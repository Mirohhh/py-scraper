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
let lastResults = [];

// --- Init ---
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".palette-buttons button").forEach((btn) => {
    btn.addEventListener("click", () => addCommand(btn.dataset.cmd));
  });
  document.getElementById("run-btn").addEventListener("click", runScraper);
  document.getElementById("download-zip-btn").addEventListener("click", downloadZip);
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

    const drag = document.createElement("span");
    drag.className = "cmd-drag";
    drag.textContent = "\u2630";
    drag.addEventListener("mousedown", () => { dragIndex = i; });
    block.appendChild(drag);

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

    const label = document.createElement("span");
    label.className = "cmd-label";
    label.textContent = def.label;
    block.appendChild(label);

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
  const urlText = document.getElementById("url-input").value.trim();
  const urls = urlText.split("\n").map((u) => u.trim()).filter(Boolean);
  const runBtn = document.getElementById("run-btn");

  if (urls.length === 0) {
    setStatus("Enter at least one URL", "error");
    return;
  }

  const cleanedCommands = commands.map((cmd) => {
    const params = {};
    for (const [k, v] of Object.entries(cmd.params)) {
      if (v !== "" && v !== undefined) params[k] = v;
    }
    return { type: cmd.type, params };
  });

  runBtn.disabled = true;
  setStatus(`Scraping ${urls.length} URL${urls.length > 1 ? "s" : ""}...`, "loading");

  try {
    const res = await fetch("/scrape", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ urls, commands: cleanedCommands }),
    });

    const data = await res.json();

    if (!res.ok) {
      setStatus(data.error || "Scraping failed", "error");
      return;
    }

    lastResults = data.results;
    renderResults(data.results);

    const ok = data.results.filter((r) => !r.error).length;
    const fail = data.results.filter((r) => r.error).length;
    let msg = `${ok} succeeded`;
    if (fail > 0) msg += `, ${fail} failed`;
    setStatus(msg, fail > 0 ? "error" : "success");
  } catch (err) {
    setStatus("Network error: " + err.message, "error");
  } finally {
    runBtn.disabled = false;
  }
}

function renderResults(results) {
  const container = document.getElementById("results-list");
  container.innerHTML = "";
  document.getElementById("results").classList.remove("hidden");

  results.forEach((r, i) => {
    const card = document.createElement("div");
    card.className = "result-card";

    const header = document.createElement("div");
    header.className = "result-card-header";

    const urlSpan = document.createElement("span");
    urlSpan.className = "result-url";
    urlSpan.textContent = r.url;
    urlSpan.title = r.url;
    header.appendChild(urlSpan);

    const actions = document.createElement("div");
    actions.className = "result-card-actions";

    if (r.html) {
      const copyBtn = document.createElement("button");
      copyBtn.className = "secondary-btn";
      copyBtn.textContent = "Copy";
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(r.html).then(() => {
          copyBtn.textContent = "Copied!";
          setTimeout(() => { copyBtn.textContent = "Copy"; }, 1500);
        });
      });
      actions.appendChild(copyBtn);

      const dlBtn = document.createElement("button");
      dlBtn.className = "secondary-btn";
      dlBtn.textContent = "Download";
      dlBtn.addEventListener("click", () => downloadSingle(r.url, r.html, i));
      actions.appendChild(dlBtn);

      const toggleBtn = document.createElement("button");
      toggleBtn.className = "secondary-btn";
      toggleBtn.textContent = "Show HTML";
      actions.appendChild(toggleBtn);
    }

    header.appendChild(actions);
    card.appendChild(header);

    if (r.error) {
      const errDiv = document.createElement("div");
      errDiv.className = "result-error";
      errDiv.textContent = r.error;
      card.appendChild(errDiv);
    }

    if (r.html) {
      const pre = document.createElement("pre");
      pre.className = "html-output hidden";
      pre.textContent = r.html;
      card.appendChild(pre);

      const toggleBtn = actions.querySelector(".secondary-btn:last-child");
      toggleBtn.addEventListener("click", () => {
        const isHidden = pre.classList.contains("hidden");
        pre.classList.toggle("hidden");
        toggleBtn.textContent = isHidden ? "Hide HTML" : "Show HTML";
      });
    }

    container.appendChild(card);
  });
}

function setStatus(msg, type) {
  const status = document.getElementById("status");
  status.textContent = msg;
  status.className = "status " + (type || "");
}

// --- Downloads ---
function downloadSingle(url, html, index) {
  const parsed = new URL(url);
  let name = (parsed.host + parsed.pathname).replace(/\/$/, "");
  name = name.replace(/[^\w\-.]/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, "");
  if (!name) name = "page_" + index;

  const blob = new Blob([html], { type: "text/html" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name + ".html";
  a.click();
  URL.revokeObjectURL(a.href);
}

async function downloadZip() {
  const okResults = lastResults.filter((r) => r.html);
  if (okResults.length === 0) return;

  const res = await fetch("/download-zip", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ results: okResults }),
  });

  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "scraped.zip";
  a.click();
  URL.revokeObjectURL(a.href);
}
