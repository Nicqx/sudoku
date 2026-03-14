from __future__ import annotations

from typing import Iterable, List

Board = List[List[int]]


def clone_board(board: Board) -> Board:
    return [row[:] for row in board]


def get_candidates(board: Board, row: int, col: int) -> list[int]:
    if not (0 <= row < 9 and 0 <= col < 9):
        return []

    used: set[int] = set()

    for c in range(9):
        if c != col and board[row][c] != 0:
            used.add(board[row][c])

    for r in range(9):
        if r != row and board[r][col] != 0:
            used.add(board[r][col])

    start_row = (row // 3) * 3
    start_col = (col // 3) * 3
    for r in range(start_row, start_row + 3):
        for c in range(start_col, start_col + 3):
            if (r != row or c != col) and board[r][c] != 0:
                used.add(board[r][c])

    return [n for n in range(1, 10) if n not in used]


def is_valid_move(board: Board, fixed: list[list[bool]], row: int, col: int, value: int) -> bool:
    if not (0 <= row < 9 and 0 <= col < 9):
        return False

    if not (0 <= value <= 9):
        return False

    if fixed[row][col]:
        return False

    if value == 0:
        return True

    return value in get_candidates(board, row, col)


def _valid_group(values: Iterable[int]) -> bool:
    nums = [v for v in values if v != 0]
    return len(nums) == len(set(nums))


def board_has_no_conflicts(board: Board) -> bool:
    for row in board:
        if not _valid_group(row):
            return False

    for col in range(9):
        if not _valid_group(board[row][col] for row in range(9)):
            return False

    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            box = []
            for r in range(box_row, box_row + 3):
                for c in range(box_col, box_col + 3):
                    box.append(board[r][c])
            if not _valid_group(box):
                return False

    return True


def is_solved(board: Board) -> bool:
    for row in board:
        if any(cell == 0 for cell in row):
            return False

    expected = set(range(1, 10))

    for row in board:
        if set(row) != expected:
            return False

    for col in range(9):
        if {board[row][col] for row in range(9)} != expected:
            return False

    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            box = set()
            for r in range(box_row, box_row + 3):
                for c in range(box_col, box_col + 3):
                    box.add(board[r][c])
            if box != expected:
                return False

    return True
