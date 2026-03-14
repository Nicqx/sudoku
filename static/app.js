let state = null;
let activeCell = null;

const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status-message");
const difficultyEl = document.getElementById("difficulty");
const newGameBtn = document.getElementById("new-game-btn");
const resetBtn = document.getElementById("reset-btn");
const modalEl = document.getElementById("number-picker");
const pickerOptionsEl = document.getElementById("picker-options");
const pickerEmptyEl = document.getElementById("picker-empty");
const closePickerBtn = document.getElementById("close-picker");

function setStatus(message, tone = "default") {
  statusEl.textContent = message;
  statusEl.className = "status-pill";
  if (tone === "success") statusEl.classList.add("success");
  if (tone === "error") statusEl.classList.add("error");
}

function getCandidates(board, row, col) {
  const used = new Set();

  for (let c = 0; c < 9; c++) {
    if (c !== col && board[row][c] !== 0) used.add(board[row][c]);
  }

  for (let r = 0; r < 9; r++) {
    if (r !== row && board[r][col] !== 0) used.add(board[r][col]);
  }

  const startRow = Math.floor(row / 3) * 3;
  const startCol = Math.floor(col / 3) * 3;
  for (let r = startRow; r < startRow + 3; r++) {
    for (let c = startCol; c < startCol + 3; c++) {
      if ((r !== row || c !== col) && board[r][c] !== 0) {
        used.add(board[r][c]);
      }
    }
  }

  return [1, 2, 3, 4, 5, 6, 7, 8, 9].filter((n) => !used.has(n));
}

function renderBoard() {
  if (!state) return;
  boardEl.innerHTML = "";

  for (let row = 0; row < 9; row++) {
    for (let col = 0; col < 9; col++) {
      const value = state.board[row][col];
      const fixed = state.fixed[row][col];
      const cell = document.createElement("div");
      cell.className = "cell";

      if ((col + 1) % 3 === 0 && col !== 8) cell.classList.add("box-right");
      if ((row + 1) % 3 === 0 && row !== 8) cell.classList.add("box-bottom");

      if (fixed) {
        cell.classList.add("fixed");
      } else {
        cell.classList.add("editable");
        cell.addEventListener("click", () => openNumberPicker(row, col));
      }

      if (activeCell && activeCell.row === row && activeCell.col === col) {
        cell.classList.add("selected");
      }

      if (value === 0) {
        cell.classList.add("empty");
        cell.textContent = "0";
      } else {
        cell.textContent = String(value);
      }

      boardEl.appendChild(cell);
    }
  }
}

function openNumberPicker(row, col) {
  if (!state || state.fixed[row][col]) return;
  activeCell = { row, col };
  renderBoard();

  const candidates = getCandidates(state.board, row, col);
  pickerOptionsEl.innerHTML = "";
  pickerEmptyEl.classList.toggle("hidden", candidates.length !== 0);

  candidates.forEach((value) => {
    const button = document.createElement("button");
    button.className = "picker-btn";
    button.textContent = String(value);
    button.addEventListener("click", () => submitMove(row, col, value));
    pickerOptionsEl.appendChild(button);
  });

  const clearButton = document.createElement("button");
  clearButton.className = "picker-btn clear-btn";
  clearButton.textContent = "Törlés";
  clearButton.addEventListener("click", () => submitMove(row, col, 0));
  pickerOptionsEl.appendChild(clearButton);

  modalEl.classList.remove("hidden");
  modalEl.setAttribute("aria-hidden", "false");
}

function closeNumberPicker() {
  modalEl.classList.add("hidden");
  modalEl.setAttribute("aria-hidden", "true");
  activeCell = null;
  renderBoard();
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    ...options,
  });

  const payload = await response.json();
  if (!response.ok) {
    const error = new Error(payload.error || "Hiba történt.");
    error.payload = payload;
    throw error;
  }
  return payload;
}

async function loadState() {
  try {
    const payload = await fetchJson("api/state");
    state = payload.state;
    difficultyEl.value = state.difficulty;
    renderBoard();
    setStatus("Játék betöltve. Válassz egy üres mezőt.");
  } catch (error) {
    setStatus(`Betöltési hiba: ${error.message}`, "error");
  }
}

async function startNewGame() {
  try {
    const payload = await fetchJson("api/new-game", {
      method: "POST",
      body: JSON.stringify({ difficulty: difficultyEl.value }),
    });
    state = payload.state;
    activeCell = null;
    closeNumberPicker();
    setStatus(`Új ${difficultyLabel(state.difficulty)} játék indult.`);
  } catch (error) {
    setStatus(`Nem sikerült új játékot indítani: ${error.message}`, "error");
  }
}

async function resetBoard() {
  try {
    const payload = await fetchJson("api/reset", { method: "POST" });
    state = payload.state;
    activeCell = null;
    closeNumberPicker();
    setStatus("A tábla visszaállt az eredeti állapotra.");
  } catch (error) {
    setStatus(`Nem sikerült visszaállítani: ${error.message}`, "error");
  }
}

async function submitMove(row, col, value) {
  try {
    const payload = await fetchJson("api/move", {
      method: "POST",
      body: JSON.stringify({ row, col, value }),
    });
    state = payload.state;
    closeNumberPicker();

    if (state.solved) {
      setStatus("Gratulálok, kész a Sudoku!", "success");
    } else {
      setStatus("Lépés rögzítve.");
    }
  } catch (error) {
    const candidates = error?.payload?.candidates;
    if (Array.isArray(candidates)) {
      setStatus(`Ide ez írható: ${candidates.join(", ") || "nincs szabályos érték"}.`, "error");
    } else {
      setStatus(`Hiba: ${error.message}`, "error");
    }
  }
}

function difficultyLabel(value) {
  if (value === "easy") return "könnyű";
  if (value === "medium") return "közepes";
  if (value === "hard") return "nehéz";
  return value;
}

newGameBtn.addEventListener("click", startNewGame);
resetBtn.addEventListener("click", resetBoard);
closePickerBtn.addEventListener("click", closeNumberPicker);
modalEl.addEventListener("click", (event) => {
  if (event.target === modalEl) closeNumberPicker();
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeNumberPicker();
});

loadState();
