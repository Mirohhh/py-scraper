# py-scraper

A Python web scraper with a Scratch-style visual command builder. You compose browser actions (`scroll`, `click`, `extract`, `wait`) and run them against one or many URLs. Playwright drives headless Chromium to execute the pipeline and return rendered HTML plus extracted values.

---

## What this project does

- Build scraping workflows visually in the browser (no frontend build step, no JS framework)
- Run the same command pipeline across multiple URLs
- Export results as:
  - single HTML files
  - bulk ZIP archives
  - CSV for extracted data
- Access the same capabilities via a public JSON API

---

## Features

- **Scratch-style command builder UI**
- **Multi-URL scraping** with concurrent execution
- **5 built-in command types**
  - `scroll`
  - `click`
  - `extract`
  - `wait_selector`
  - `wait_timeout`
- **Data extraction** by CSS selector (`text`, `html`, or attribute values)
- **Rate-limited API** (`30 req/min` per IP, in-memory)
- **Pagination support** on `/api/scrape`
- **Built-in docs page** at `/docs`

---

## Tech stack

- **Python** 3.12+
- **Flask** 3.x
- **Playwright** 1.40+ (sync API)
- **Vanilla JavaScript** + **Jinja2 templates**
- No npm, no bundler, no build pipeline

---

## Quick start

### 1) Clone and enter the repo

```bash
git clone <repo-url>
cd py-scraper
```

### 2) Install dependencies

```bash
pip install flask playwright
```

### 3) Install Chromium for Playwright

```bash
playwright install chromium
```

### 4) Run the app

```bash
python app.py
```

Open:

- `http://localhost:5000` (Web UI)
- `http://localhost:5000/docs` (Built-in docs)

---

## Running with Flask CLI (optional)

```bash
flask --app app run --debug --port 5000
```

---

## Web UI usage

1. Enter one URL per line
2. Add command blocks to the pipeline
3. Configure command parameters
4. Reorder via drag-and-drop
5. Click **Run Scraper**
6. Review result cards (HTML + extracted data)
7. Export as HTML / ZIP / CSV

### Pipeline save/load

- **Export** saves pipeline JSON
- **Import** restores pipeline JSON

---

## Command reference (quick)

| Command | Purpose | Key Params |
|---|---|---|
| `scroll` | Scroll page to bottom repeatedly | `times`, `delay_ms` |
| `click` | Click by selector or visible text | `selector`, `text`, `wait_after_ms` |
| `extract` | Extract values from matched elements | `selector`, `attr` |
| `wait_selector` | Wait until selector is visible | `selector`, `timeout` |
| `wait_timeout` | Sleep fixed duration | `ms` |

---

## API overview

All `/api/*` endpoints are rate-limited to **30 req/min per IP**.

### Endpoints

- `GET /api/health` — health check
- `GET /api/commands` — list command metadata
- `POST /api/scrape` — scrape and return JSON results
- `POST /api/scrape/zip` — scrape and return ZIP

### Minimal examples

Health check:

```bash
curl http://localhost:5000/api/health
```

Single-URL scrape:

```bash
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

ZIP export:

```bash
curl -X POST http://localhost:5000/api/scrape/zip \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://example.com","https://example.org"]}' \
  -o scraped.zip
```

For full request/response details, see `docs/API.md`.

---

## Project structure

```text
py-scraper/
├── app.py                 # Flask app (UI routes, API routes, exports, rate limiting)
├── scraper.py             # Playwright engine (execute_scrape)
├── templates/
│   ├── index.html         # Main UI
│   └── docs.html          # Built-in docs page
├── static/
│   ├── script.js          # Frontend behavior
│   └── style.css          # Styling
├── docs/
│   ├── README.md          # Docs index + architecture notes
│   ├── UI.md              # UI workflow + command guide + troubleshooting
│   └── API.md             # Detailed API reference
├── AGENTS.md              # Repo-specific engineering guidance
└── pyproject.toml         # Project metadata + dependencies
```

---

## Documentation map

- **Top-level overview:** `README.md` (this file)
- **In-app documentation:** `/docs` (`templates/docs.html`)
- **Docs index:** `docs/README.md`
- **UI guide:** `docs/UI.md`
- **API reference:** `docs/API.md`
- **Maintenance/engineering rules:** `AGENTS.md`

---

## Architecture notes

- A **fresh browser** is launched per `execute_scrape` call (avoids cross-request Playwright issues).
- Page navigation uses `wait_until="domcontentloaded"` plus a short buffer.
- Scrape engine returns a dict:
  - `{"html": str, "extracted": list[dict]}`
- Multi-URL scraping is performed concurrently with a bounded thread pool.
- Rate limiting is in-memory and resets on server restart.

---

## Maintenance notes

When extending the app:

1. Add or update command metadata in `COMMANDS` in `app.py`
2. Implement command runtime behavior in `scraper.py`
3. Update docs in:
   - `templates/docs.html` (in-app docs)
   - `docs/UI.md` and/or `docs/API.md`
   - this `README.md` for top-level changes
4. Keep input validation strict (`request.get_json(silent=True)` + `if data is None:` checks)

### Known operational caveats

- Some sites may block scraping or require additional waits/selectors.
- Dynamic pages vary; prefer `wait_selector` over fixed sleeps where possible.
- In-memory rate limiting is suitable for single-instance dev/small deployments.

---

## Development status

There are currently no configured test/lint/type-check commands in this repo by default.  
Suggested tooling conventions (when added) are documented in `AGENTS.md`.

---

## License

MIT