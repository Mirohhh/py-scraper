const COMMAND_DEFS = {
  scroll: {
    label: "Scroll",
    fields: [
      { key: "times", placeholder: "Times (default 1)", type: "number" },
      { key: "delay_ms", placeholder: "Delay ms (default 1500)", type: "number" },
    ],
  },
  click: {
    label: "Click",
    fields: [
      { key: "text", placeholder: "Button/link text (e.g. Show more)", type: "text" },
      { key: "wait_after_ms", placeholder: "Wait after click ms (default 2000)", type: "number" },
    ],
  },
  wait_selector: {
    label: "Wait for Selector",
    fields: [
      { key: "selector", placeholder: "CSS selector", type: "text" },
      { key: "timeout", placeholder: "Timeout ms (default 10000)", type: "number" },
    ],
  },
  wait_timeout: {
    label: "Wait (ms)",
    fields: [{ key: "ms", placeholder: "Milliseconds", type: "number" }],
  },
};

let commands = [];
let dragIndex = null;

// --- Init ---
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".palette-buttons button").forEach((btn) => {
    btn.addEventListener("click", () => addCommand(btn.dataset.cmd));
  });
  document.getElementById("run-btn").addEventListener("click", runScraper);
  document.getElementById("copy-btn").addEventListener("click", copyHtml);
  document.getElementById("download-btn").addEventListener("click", downloadHtml);
});

// --- Pipeline management ---
function addCommand(type) {
  commands.push({ type, params: {} });
  renderPipeline();
}

function removeCommand(index) {
  commands.splice(index, 1);
  renderPipeline();
}

function renderPipeline() {
  const list = document.getElementById("pipeline-list");
  list.innerHTML = "";

  if (commands.length === 0) {
    list.innerHTML = '<div class="pipeline-empty">Click a command to add it here</div>';
    return;
  }

  commands.forEach((cmd, i) => {
    const def = COMMAND_DEFS[cmd.type];
    const block = document.createElement("div");
    block.className = "cmd-block";
    block.draggable = true;
    block.dataset.index = i;

    // Drag handle
    const drag = document.createElement("span");
    drag.className = "cmd-drag";
    drag.textContent = "\u2630";
    drag.addEventListener("mousedown", () => { dragIndex = i; });
    block.appendChild(drag);

    // Drag events
    block.addEventListener("dragstart", (e) => {
      dragIndex = i;
      block.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
    });
    block.addEventListener("dragend", () => {
      block.classList.remove("dragging");
      dragIndex = null;
      document.querySelectorAll(".cmd-block").forEach((b) => b.classList.remove("drag-over"));
    });
    block.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      block.classList.add("drag-over");
    });
    block.addEventListener("dragleave", () => {
      block.classList.remove("drag-over");
    });
    block.addEventListener("drop", (e) => {
      e.preventDefault();
      block.classList.remove("drag-over");
      if (dragIndex !== null && dragIndex !== i) {
        const moved = commands.splice(dragIndex, 1)[0];
        commands.splice(i, 0, moved);
        renderPipeline();
      }
    });

    // Label
    const label = document.createElement("span");
    label.className = "cmd-label";
    label.textContent = def.label;
    block.appendChild(label);

    // Params
    const paramsDiv = document.createElement("div");
    paramsDiv.className = "cmd-params";
    def.fields.forEach((field) => {
      const input = document.createElement("input");
      input.type = field.type;
      input.placeholder = field.placeholder;
      input.value = cmd.params[field.key] || "";
      input.addEventListener("input", (e) => {
        commands[i].params[field.key] = e.target.value;
      });
      paramsDiv.appendChild(input);
    });
    block.appendChild(paramsDiv);

    // Remove button
    const remove = document.createElement("button");
    remove.className = "cmd-remove";
    remove.innerHTML = "&times;";
    remove.title = "Remove";
    remove.addEventListener("click", () => removeCommand(i));
    block.appendChild(remove);

    list.appendChild(block);
  });
}

// --- Scraper execution ---
async function runScraper() {
  const urlInput = document.getElementById("url-input");
  const url = urlInput.value.trim();
  const status = document.getElementById("status");
  const runBtn = document.getElementById("run-btn");

  if (!url) {
    setStatus("Enter a URL first", "error");
    return;
  }

  // Build command list with cleaned params
  const cleanedCommands = commands.map((cmd) => {
    const params = {};
    for (const [k, v] of Object.entries(cmd.params)) {
      if (v !== "" && v !== undefined) params[k] = v;
    }
    return { type: cmd.type, params };
  });

  runBtn.disabled = true;
  setStatus("Scraping...", "loading");

  try {
    const res = await fetch("/scrape", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, commands: cleanedCommands }),
    });

    const data = await res.json();

    if (!res.ok) {
      setStatus(data.error || "Scraping failed", "error");
      return;
    }

    document.getElementById("html-output").textContent = data.html;
    document.getElementById("results").classList.remove("hidden");
    setStatus("Done!", "success");
  } catch (err) {
    setStatus("Network error: " + err.message, "error");
  } finally {
    runBtn.disabled = false;
  }
}

function setStatus(msg, type) {
  const status = document.getElementById("status");
  status.textContent = msg;
  status.className = "status " + (type || "");
}

// --- Copy & download ---
function copyHtml() {
  const html = document.getElementById("html-output").textContent;
  navigator.clipboard.writeText(html).then(() => {
    const btn = document.getElementById("copy-btn");
    btn.textContent = "Copied!";
    setTimeout(() => { btn.textContent = "Copy"; }, 1500);
  });
}

function downloadHtml() {
  const html = document.getElementById("html-output").textContent;
  const blob = new Blob([html], { type: "text/html" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "scraped.html";
  a.click();
  URL.revokeObjectURL(a.href);
}
