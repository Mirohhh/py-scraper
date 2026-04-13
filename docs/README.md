# py-scraper Documentation

This is the central docs index for the `py-scraper` repository.

Use this page as your entry point to:
- understand the app quickly,
- find detailed API/UI guides,
- and navigate in-code documentation.

## Start here

- **Project overview**: `../README.md`
- **In-app documentation page**: `http://localhost:5000/docs` (source: `../templates/docs.html`)
- **API guide**: `./API.md`
- **UI guide**: `./UI.md`
- **Repo engineering rules**: `../AGENTS.md`

## Documentation map

### Product + usage docs

1. `../README.md`  
   High-level overview, setup, architecture notes, and quick API examples.

2. `./UI.md`  
   End-to-end web UI workflow:
   - entering URLs
   - building command pipelines
   - export/import pipeline JSON
   - troubleshooting common scraping issues

3. `./API.md`  
   Complete API reference:
   - endpoint list and request/response shapes
   - validation and error formats
   - pagination behavior
   - cURL examples for scrape and ZIP export

4. `../templates/docs.html`  
   Built-in docs rendered at `/docs` for browser-based usage.

### In-code documentation

The codebase includes docstrings on core backend functions and route handlers.

- `../app.py`
  - route-level docs for web and API endpoints
  - helper docs for rate limiting, validation, scraping orchestration, and exports
  - typed helper signatures for clearer maintenance

- `../scraper.py`
  - docs for `execute_scrape(...)` lifecycle and return shape
  - docs for command execution behavior in `_execute_command(...)`

## Recommended reading order

If you are new to the project:

1. `../README.md`
2. `./UI.md`
3. `./API.md`
4. `../app.py`
5. `../scraper.py`

## Quick operational summary

- Stack: Python 3.12+, Flask, Playwright (sync API), vanilla JS frontend.
- No build step for frontend assets.
- Scraping model:
  - fresh browser per scrape execution
  - `domcontentloaded` navigation + short wait buffer
  - returns `{"html": str, "extracted": list[dict]}`

## When you add or change features

Update docs in this order to keep everything aligned:

1. Update command metadata in `../app.py` (`COMMANDS`) if command-related.
2. Implement runtime behavior in `../scraper.py`.
3. Update user-facing docs:
   - `../templates/docs.html`
   - `./UI.md` and/or `./API.md`
   - `../README.md` for top-level changes
4. Verify examples still match actual request/response behavior.

## Notes on scope and reliability

- Rate limiting is in-memory (resets on restart).
- Multi-URL scraping is concurrent but bounded.
- Dynamic sites may require wait commands (`wait_selector` preferred over fixed waits).
- Per-URL failures are isolated; one failed URL should not fail all results.

---

If this index feels out of sync with behavior in code, treat `../app.py` and `../scraper.py` as the source of truth, then update this file and linked guides accordingly.