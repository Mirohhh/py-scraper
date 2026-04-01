# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project Overview

Python web scraper with a Scratch-style command builder UI. Users compose a pipeline
of browser commands (scroll, click, extract, wait) and apply them to one or more URLs.
Playwright drives headless Chromium to execute the pipeline and return rendered HTML.

**Stack**: Python 3.12, Flask, Playwright (sync API), vanilla JS frontend, no build step.

## Architecture

```
app.py          Flask app: web UI routes, public API (/api/*), download endpoints
scraper.py      Playwright engine: execute_scrape(url, commands) -> {html, extracted}
templates/      Jinja2 templates (index.html, docs.html)
static/         JS + CSS, served directly by Flask
```

Key design decisions:
- A fresh browser is launched per `execute_scrape` call (no persistent singleton).
- Page load uses `wait_until="domcontentloaded"` with a 1s buffer — `networkidle`
  times out on many real sites because of long-lived connections.
- `execute_scrape` returns `{"html": str, "extracted": list[dict]}`, not a bare string.

## Commands

| Command        | Purpose                                      |
|----------------|----------------------------------------------|
| `scroll`       | Scroll to page bottom N times with delay     |
| `click`        | Click by CSS selector or visible text        |
| `extract`      | Extract text/html/attrs from matching elements|
| `wait_selector`| Wait until a selector is visible             |
| `wait_timeout` | Fixed-duration sleep                         |

Command metadata lives in the `COMMANDS` list in `app.py`. Add new types there too.

## Running

```bash
# Start the dev server (port 5000, debug mode)
python app.py

# Or with flask CLI
flask --app app run --debug --port 5000
```

## Build / Lint / Test

**There are no automated tests, linters, or formatters configured yet.**
When adding tooling, prefer these conventions (update this section when done):

```bash
# Linting & formatting (when added)
pip install ruff
ruff check .                    # lint
ruff format .                   # format

# Type checking (when added)
pip install mypy
mypy app.py scraper.py

# Testing (when added)
pip install pytest pytest-flask
pytest                          # all tests
pytest tests/test_scraper.py    # single file
pytest tests/test_scraper.py::test_execute_scrape -k "single_url"  # single test
```

Run `playwright install chromium` after installing dependencies to fetch the browser binary.

## Code Style — Python

- **Python 3.12+**. Use modern syntax: `dict` instead of `Dict`, `list` instead of `List`,
  `str | None` instead of `Optional[str]`.
- **Imports**: stdlib first, then third-party, then local. One import per line (no grouped
  `from X import a, b, c` unless already in the file). Avoid wildcard imports.
- **Naming**: `snake_case` for functions, variables, modules. `PascalCase` for classes.
  Prefix private helpers with `_` (e.g., `_api_error`, `_validate_commands`).
- **Type hints**: Use them on public function signatures. Keep param types and return types
  annotated. `params: list[dict]`, `-> dict`, `-> str | None`.
- **String handling**: When reading request JSON, use `request.get_json(silent=True)` and
  check `if data is None:` — **not** `if not data:` (empty dict `{}` is falsy).
- **Error handling**: Catch specific exceptions (`PlaywrightTimeout`). Use `try/finally`
  for resource cleanup (browser, context). Return error dicts, don't re-raise to callers
  unless it's a truly unexpected failure.
- **Formatting**: No formatter configured yet. Follow existing style: 4-space indent,
  ~100 char lines, blank lines between top-level definitions. Run `ruff format` once added.
- **No comments** unless the logic is non-obvious. Use section headers (`# --- Section ---`)
  to group related code in `app.py`.

## Code Style — JavaScript

- **Vanilla JS only** — no frameworks, no npm, no build step.
- **ES6+**. Use `const`/`let`, arrow functions, template literals, `async`/`await`.
- **Naming**: `camelCase` for variables and functions. `UPPER_CASE` for module-level
  constants (e.g., `COMMAND_DEFS`).
- **DOM**: Build elements with `document.createElement`. Attach events with
  `addEventListener`. Use `e.stopPropagation()` to prevent event bubbling on action buttons.
- **Fetch API**: Use `fetch()` with `async/await`. Always check `res.ok` before processing
  the body. Use `res.json().catch(() => ({}))` for error responses.
- **No semicolons required** by convention in this project (existing code has them inconsistently;
  follow the surrounding file).

## Code Style — CSS / HTML

- **No CSS frameworks**. All styles in `static/style.css`.
- **Dark theme**: Background `#0d1117`, surface `#161b22`, border `#30363d`,
  text `#c9d1d9`, accent `#58a6ff`, success `#238636`, danger `#f85149`.
- Use semantic class names: `.cmd-block`, `.result-card`, `.result-card-header`.
- **HTML**: Standard Jinja2 templates. No template inheritance — each page is standalone.

## API Endpoints

All `/api/*` endpoints are rate-limited (30 req/min per IP). The `/api/scrape`
endpoint supports pagination via `page` and `per_page` fields.

| Method | Path              | Purpose                          |
|--------|-------------------|----------------------------------|
| GET    | `/`               | Web UI                           |
| GET    | `/docs`           | Documentation page               |
| POST   | `/scrape`         | Web UI scrape handler            |
| POST   | `/download-zip`   | ZIP of scraped HTML              |
| POST   | `/download-csv`   | CSV of extracted data            |
| GET    | `/api/health`     | Health check                     |
| GET    | `/api/commands`   | List available command types     |
| POST   | `/api/scrape`     | Public API: scrape + return JSON |
| POST   | `/api/scrape/zip` | Public API: scrape + return ZIP  |

Rate limiting is in-memory (`_rate_limit_store` dict). Pagination returns a
`pagination` object with `page`, `per_page`, `total`, `total_pages`.

## Common Pitfalls

1. **`bool({})` is `False`** in Python. When validating JSON from Flask, always check
   `if data is None:` not `if not data:`.
2. **`networkidle` timeouts** — many sites keep WebSocket/analytics connections open.
   Use `domcontentloaded` + explicit `wait_for_timeout`.
3. **Playwright thread errors** — don't reuse a browser across Flask requests. Launch
   a fresh one per call.
4. **`execute_scrape` returns a dict**, not a string. Access `.html` and `.extracted`.
