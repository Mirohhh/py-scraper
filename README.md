# py-scraper

A Python web scraper with a Scratch-style visual command builder. Compose browser automation pipelines (scroll, click, extract, wait) and run them against one or more URLs. Playwright drives headless Chromium to execute the pipeline and return the fully rendered HTML.

## Features

- **Visual pipeline builder** — drag-and-drop command blocks, no code required
- **Multi-URL support** — scrape multiple pages in one run
- **5 command types** — scroll, click (by selector or text), extract (text/html/attributes), wait for selector, wait for duration
- **Data extraction** — pull structured data from pages using CSS selectors, export as CSV
- **Export options** — single HTML download, bulk ZIP, CSV of extracted data
- **Pipeline save/load** — export your command pipeline as JSON, import it later
- **Public REST API** — programmatic access with rate limiting and pagination
- **Collapsible results** — expandable result cards with HTML preview

## Quick Start

```bash
# Clone and enter the project
git clone <repo-url>
cd py-scraper

# Install dependencies
pip install flask playwright

# Download Chromium binary
playwright install chromium

# Run the server
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Usage

### Web UI

1. Enter one or more URLs in the textarea (one per line)
2. Click command buttons to build your pipeline (scroll, click, extract, etc.)
3. Edit parameters directly in the pipeline blocks
4. Drag blocks to reorder
5. Click **Run Scraper**
6. Expand/collapse result cards, copy HTML, or download results

### Commands

| Command | Purpose | Key Parameters |
|---------|---------|----------------|
| **Scroll** | Scroll to page bottom N times | `times`, `delay_ms` |
| **Click** | Click element by CSS selector or visible text | `selector`, `text`, `wait_after_ms` |
| **Extract** | Extract data from matching elements | `selector`, `attr` (text/html/href) |
| **Wait for Selector** | Wait until an element is visible | `selector`, `timeout` |
| **Wait (ms)** | Fixed-duration sleep | `ms` |

## API

All `/api/*` endpoints return JSON and are rate-limited to **30 requests per minute** per IP.

### Health Check

```bash
curl http://localhost:5000/api/health
```

```json
{"status": "ok"}
```

### List Commands

```bash
curl http://localhost:5000/api/commands
```

Returns the full list of available command types with their parameters and defaults.

### Scrape

```bash
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "commands": [
      {"type": "click", "params": {"text": "Show more"}},
      {"type": "scroll", "params": {"times": 3}},
      {"type": "extract", "params": {"selector": "h1", "attr": "text"}}
    ]
  }'
```

**Request fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | one of url/urls | Single URL to scrape |
| `urls` | string[] | one of url/urls | Multiple URLs to scrape |
| `commands` | object[] | no | Command pipeline |
| `html` | bool | no | Include HTML in response (default `true`) |
| `page` | int | no | Page number for pagination (default `1`) |
| `per_page` | int | no | URLs per page, max 100 (default `10`) |

**Response:**

```json
{
  "results": [
    {
      "url": "https://example.com",
      "status": "ok",
      "html_length": 528,
      "html": "<!DOCTYPE html>...",
      "extracted": [
        {"selector": "h1", "attr": "text", "values": ["Example Domain"]}
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

### Scrape to ZIP

Same input as `/api/scrape`, returns a `.zip` file with one HTML file per URL.

```bash
curl -X POST http://localhost:5000/api/scrape/zip \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com", "https://example.org"]}' \
  -o scraped.zip
```

### Error Handling

- **400** — invalid input (missing URLs, bad command types, invalid pagination params)
- **429** — rate limit exceeded
- Per-URL scrape failures return `"status": "error"` in the results array, other URLs still succeed

```json
{
  "results": [
    {"url": "https://example.com", "status": "ok", "html_length": 528},
    {"url": "https://bad.invalid", "status": "error", "error": "net::ERR_NAME_NOT_RESOLVED"}
  ],
  "pagination": {"page": 1, "per_page": 10, "total": 2, "total_pages": 1}
}
```

## Project Structure

```
app.py              Flask app: web UI routes, public API, download endpoints
scraper.py          Playwright engine: execute_scrape(url, commands) -> {html, extracted}
pyproject.toml      Project metadata and dependencies
templates/
  index.html        Web UI — pipeline builder, URL input, results display
  docs.html         Built-in documentation page with sidebar navigation
static/
  script.js         Frontend logic — pipeline management, fetch calls, DOM rendering
  style.css         Dark-themed styles — layout, cards, sidebar, syntax blocks
```

## Architecture

- **A fresh browser is launched per `execute_scrape` call** — no persistent singleton. This avoids Playwright thread-safety issues with Flask's threaded dev server.
- **`domcontentloaded` + 1s buffer** — page load uses `wait_until="domcontentloaded"` instead of `networkidle`, because many sites keep WebSocket/analytics connections open that cause 15-second timeouts.
- **`execute_scrape` returns a dict** — `{"html": str, "extracted": list[dict]}`, not a bare string.
- **Rate limiting is in-memory** — uses a per-IP fixed-window counter (`_rate_limit_store` dict). Stale IPs are cleaned up lazily. This resets when the server restarts.
- **No build step** — the frontend is vanilla JS with no bundler, framework, or npm dependencies.

## Development

```bash
# Start the dev server with auto-reload
python app.py

# Or use the Flask CLI
flask --app app run --debug --port 5000
```

The server runs on port 5000 in debug mode. Templates and static files are served directly by Flask.

### Dependencies

- Python 3.12+
- Flask 3.0+
- Playwright 1.40+ (with Chromium)

```bash
pip install flask playwright
playwright install chromium
```

## License

MIT
