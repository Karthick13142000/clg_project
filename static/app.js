/* EduGenie frontend: one function per feature, shared helpers below. */

const ENDPOINTS = {
  ask: { url: "/ask", field: "question", out: "answer" },
  summarize: { url: "/summarize", field: "notes", out: "summary" },
  quiz: { url: "/quiz", field: "topic", out: "quiz" }
};

const MAX_INPUT_CHARS = 8000;

/* ---------- setup ---------- */

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".tab").forEach(initTab);
  document.querySelectorAll("button[data-action]").forEach(initAction);
  document.querySelectorAll("button[data-clear]").forEach(initClear);

  const notes = document.getElementById("notes");
  notes.addEventListener("input", () => {
    document.getElementById("notes-count").textContent =
      notes.value.length.toLocaleString();
  });

  document.querySelectorAll("button[data-copy]").forEach(initCopy);
});

function initCopy(button) {
  button.addEventListener("click", async () => {
    const text = document.getElementById(button.dataset.copy).textContent.trim();
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      flashLabel(button, "Copied!");
    } catch (clipboardError) {
      flashLabel(button, "Press Ctrl+C");
    }
    setTimeout(() => { button.textContent = "Copy"; }, 1600);
  });
}

function flashLabel(button, label) {
  button.textContent = label;
}

function initTab(tab) {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => {
      t.classList.remove("active");
      t.setAttribute("aria-selected", "false");
    });
    document.querySelectorAll(".panel").forEach((p) => p.classList.add("hidden"));

    tab.classList.add("active");
    tab.setAttribute("aria-selected", "true");
    document.getElementById(tab.dataset.panel).classList.remove("hidden");
  });
}

function initAction(button) {
  button.addEventListener("click", () => run(button.dataset.action, button));
}

function initClear(button) {
  button.addEventListener("click", () => {
    const input = document.getElementById(button.dataset.clear);
    input.value = "";
    if (input.id === "notes") {
      document.getElementById("notes-count").textContent = "0";
    }
    input.focus();
  });
}

/* ---------- API calls ---------- */

async function run(feature, button) {
  const { url, field, out } = ENDPOINTS[feature];
  const input = document.getElementById(field);
  const output = document.getElementById(out);
  const value = input.value.trim();

  if (!value) {
    showError(output, "Please enter some text first.");
    input.focus();
    return;
  }
  if (value.length > MAX_INPUT_CHARS) {
    showError(output, `Input is too long (${value.length} characters). Keep it under ${MAX_INPUT_CHARS}.`);
    return;
  }

  setBusy(button, true);
  setLoading(output);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input: value })
    });

    let data = {};
    try {
      data = await response.json();
    } catch (parseError) {
      throw new Error(`Server returned an unexpected response (${response.status}).`);
    }

    if (!response.ok) {
      throw new Error(data.error || `Request failed with status ${response.status}.`);
    }

    // textContent, never innerHTML: the text came from an AI model.
    output.textContent = data.result ? Object.values(data.result)[0] : "";
    output.classList.remove("loading", "error");
    syncResult(output, false);
  } catch (error) {
    showError(output, error.message);
  } finally {
    setBusy(button, false);
  }
}

/* ---------- rendering helpers ---------- */

function syncResult(output, errored) {
  const box = output.closest("[data-result]");
  if (box) {
    box.hidden = output.textContent.trim() === "";
    box.classList.toggle("error", errored);
  }
}

function setBusy(button, busy) {
  button.disabled = busy;
  const panel = button.closest(".panel");
  panel.querySelectorAll("textarea, input").forEach((el) => {
    el.disabled = busy;
  });
  if (busy) {
    button.textContent = "Working...";
  } else {
    button.textContent = button.dataset.action === "quiz"
      ? "Generate Quiz"
      : button.dataset.action === "summarize"
        ? "Summarize"
        : "Ask";
  }
}

function setLoading(output) {
  const spinner = document.createElement("span");
  spinner.className = "spinner";
  output.replaceChildren(spinner, document.createTextNode(" Asking Gemini..."));
  output.classList.add("loading");
  output.classList.remove("error");
  syncResult(output, false);
}

function showError(output, message) {
  output.textContent = message;
  output.classList.add("error");
  output.classList.remove("loading");
  syncResult(output, true);
}
