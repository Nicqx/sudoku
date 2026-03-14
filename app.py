from __future__ import annotations

import json
import os
import random
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, make_response, render_template, request

from storage import BaseStore, MemoryStore, RedisStore, StorageError
from sudoku import board_has_no_conflicts, clone_board, get_candidates, is_solved, is_valid_move

BASE_DIR = Path(__file__).resolve().parent
PUZZLES_FILE = BASE_DIR / "puzzles.json"
SESSION_PREFIX = "sudoku:"
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "86400"))

with PUZZLES_FILE.open("r", encoding="utf-8") as f:
    PUZZLES: dict[str, list[list[list[int]]]] = json.load(f)


def create_store() -> BaseStore:
    backend = os.getenv("SESSION_BACKEND", "memory").strip().lower()
    if backend == "redis":
        host = os.getenv("REDIS_HOST", "sudoku-redis")
        port = int(os.getenv("REDIS_PORT", "6379"))
        return RedisStore(host=host, port=port)
    return MemoryStore()


def create_app(store: BaseStore | None = None) -> Flask:
    app = Flask(__name__)
    session_store = store or create_store()

    def get_session_id() -> str:
        sid = request.cookies.get("sudoku_sid")
        return sid if sid else str(uuid.uuid4())

    def session_key(sid: str) -> str:
        return f"{SESSION_PREFIX}{sid}"

    def load_state(sid: str) -> dict[str, Any] | None:
        return session_store.get(session_key(sid))

    def save_state(sid: str, state: dict[str, Any]) -> None:
        session_store.set(session_key(sid), state, ttl_seconds=SESSION_TTL_SECONDS)

    def build_state(difficulty: str) -> dict[str, Any]:
        if difficulty not in PUZZLES:
            difficulty = "easy"
        puzzle = clone_board(random.choice(PUZZLES[difficulty]))
        fixed = [[cell != 0 for cell in row] for row in puzzle]
        return {
            "difficulty": difficulty,
            "puzzle": clone_board(puzzle),
            "board": clone_board(puzzle),
            "fixed": fixed,
            "solved": False,
            "has_conflicts": False,
        }

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True})

    @app.post("/api/new-game")
    def new_game():
        sid = get_session_id()
        body = request.get_json(silent=True) or {}
        difficulty = str(body.get("difficulty", "easy"))
        state = build_state(difficulty)
        save_state(sid, state)
        response = make_response(jsonify({"ok": True, "state": state}))
        response.set_cookie("sudoku_sid", sid, httponly=True, samesite="Lax")
        return response

    @app.get("/api/state")
    def get_state():
        sid = get_session_id()
        state = load_state(sid)
        if state is None:
            state = build_state("easy")
            save_state(sid, state)
        response = make_response(jsonify({"ok": True, "state": state}))
        response.set_cookie("sudoku_sid", sid, httponly=True, samesite="Lax")
        return response

    @app.get("/api/candidates/<int:row>/<int:col>")
    def candidates(row: int, col: int):
        sid = get_session_id()
        state = load_state(sid)
        if state is None:
            return jsonify({"ok": False, "error": "no active game"}), 404

        if state["fixed"][row][col]:
            return jsonify({"ok": True, "candidates": []})

        values = get_candidates(state["board"], row, col)
        return jsonify({"ok": True, "candidates": values})

    @app.post("/api/move")
    def move():
        sid = get_session_id()
        state = load_state(sid)
        if state is None:
            return jsonify({"ok": False, "error": "no active game"}), 404

        body = request.get_json(force=True)
        row = int(body["row"])
        col = int(body["col"])
        value = int(body["value"])

        board = state["board"]
        fixed = state["fixed"]

        if not is_valid_move(board, fixed, row, col, value):
            return jsonify(
                {
                    "ok": False,
                    "error": "invalid move",
                    "candidates": get_candidates(board, row, col),
                }
            ), 400

        board[row][col] = value
        state["board"] = board
        state["has_conflicts"] = not board_has_no_conflicts(board)
        state["solved"] = is_solved(board)
        save_state(sid, state)
        return jsonify({"ok": True, "state": state})

    @app.post("/api/reset")
    def reset():
        sid = get_session_id()
        state = load_state(sid)
        if state is None:
            return jsonify({"ok": False, "error": "no active game"}), 404

        state["board"] = clone_board(state["puzzle"])
        state["solved"] = False
        state["has_conflicts"] = False
        save_state(sid, state)
        return jsonify({"ok": True, "state": state})

    @app.get("/api/ping-store")
    def ping_store():
        return jsonify({"ok": True, "backend": os.getenv("SESSION_BACKEND", "memory")})

    return app


try:
    app = create_app()
except StorageError as exc:
    failing_app = Flask(__name__)

    @failing_app.get("/healthz")
    def failed_healthz():
        return jsonify({"ok": False, "error": str(exc)}), 500

    @failing_app.get("/")
    def failed_index():
        return f"Sudoku storage error: {exc}", 500

    app = failing_app


if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", "9097"))
    app.run(host="0.0.0.0", port=port, debug=False)
