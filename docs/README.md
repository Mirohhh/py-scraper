# py-scraper Documentation

Welcome to the documentation index for the `py-scraper` app.

This project is a Python + Flask web scraper with a Scratch-style command builder UI. You can compose browser actions (`scroll`, `click`, `extract`, `wait`) and run them against one or many URLs using Playwright.

## Documentation Map

- **Main project overview**: `../README.md`
- **Agent/project rules**: `../AGENTS.md`
- **In-app docs page**: `/docs` route (`templates/docs.html`)
- **Server/API implementation**: `../app.py`
- **Scraping engine**: `../scraper.py`
- **Frontend UI logic**: `../static/script.js`
- **Frontend styles**: `../static/style.css`

## Quick Start

1. Install dependencies:
   - `flask`
   - `playwright`
2. Install browser binary:
   - `playwright install chromium`
3. Run the app:
   - `python app.py`
4. Open:
   - `http://localhost:5000`

## App Usage

### Web UI Flow

1. Open `/`
2. Enter one URL per line
3. Build a command pipeline
4. Run scraper
5. Inspect results
6. Export HTML/ZIP/CSV as needed

### Supported Commands

- `scroll` — Scroll page bottom repeatedly (`times`, `delay_ms`)
- `click` — Click by CSS selector or visible text (`selector`, `text`, `wait_after_ms`)
- `extract` — Extract `text`, `html`, or attribute values (`selector`, `attr`)
- `wait_selector` — Wait for selector to be visible (`selector`, `timeout`)
- `wait_timeout` — Fixed sleep in milliseconds (`ms`)

## Architecture

## High-Level Components

- **`app.py`**
  - Flask app setup
  - Web UI routes (`/`, `/docs`, `/scrape`)
  - Download routes (`/download-zip`, `/download-csv`)
  - Public API routes (`/api/*`)
  - Command metadata (`COMMANDS`)
  - Request validation and rate limiting
- **`scraper.py`**
  - Playwright-driven execution
  - Applies command pipeline to each URL
  - Returns structured scrape result
- **`templates/`**
  - `index.html` for UI
  - `docs.html` for built-in documentation
- **`static/`**
  - Vanilla JS interactions and API calls
  - Dark-theme CSS styling

## Execution Model

- A **fresh browser** is launched per scrape execution to avoid threading issues.
- Page load strategy uses `domcontentloaded` + short wait buffer.
- Scrape returns a dict:
  - `{"html": str, "extracted": list[dict]}`

## API Summary

- `GET /api/health` — health check
- `GET /api/commands` — command metadata
- `POST /api/scrape` — JSON scrape response (+ pagination support)
- `POST /api/scrape/zip` — ZIP of scraped HTML

### Rate Limiting

- In-memory, per-IP fixed window
- Default: `30` requests per minute
- Applied to `/api/*` and UI scrape endpoint

## Data and Export Model

- Each result is URL-scoped and can include:
  - status
  - html/html_length
  - extracted values
  - per-URL error
- Export options:
  - Single HTML
  - Bulk ZIP
  - CSV for extracted records

## Development Notes

- Python 3.12+ conventions
- Vanilla JS frontend (no build step)
- No automated tests/linting configured yet in-repo
- If you add tooling, align with conventions in `AGENTS.md`

## Suggested Reading Order

1. `../README.md` (product + API basics)
2. `../app.py` (routes, validation, response shapes)
3. `../scraper.py` (runtime command behavior)
4. `templates/docs.html` (UI-facing docs content)

---

If you’re extending the app, start by updating `COMMANDS` in `app.py`, then implement behavior in `scraper.py`, and finally document changes in both `templates/docs.html` and `../README.md`.