# API Documentation

Base URL (local development): `http://localhost:5000`  
Content type for POST endpoints: `application/json`

All `/api/*` endpoints are rate-limited to **30 requests per minute per IP**.

---

## Authentication

No authentication is required by default.

---

## Error Format

Most API validation failures return this shape:

```/dev/null/error.json#L1-3
{
  "error": "Human-readable error message"
}
```

Common status codes:

- `200` — Success
- `400` — Invalid request payload or parameters
- `429` — Rate limit exceeded

---

## GET `/api/health`

Health check endpoint.

### Request

No request body.

### Example

```/dev/null/curl.sh#L1-1
curl http://localhost:5000/api/health
```

### Response `200`

```/dev/null/health-response.json#L1-3
{
  "status": "ok"
}
```

---

## GET `/api/commands`

Returns all available command types and their parameter metadata.

### Request

No request body.

### Example

```/dev/null/curl.sh#L1-1
curl http://localhost:5000/api/commands
```

### Response `200` (example)

```/dev/null/commands-response.json#L1-40
{
  "commands": [
    {
      "type": "scroll",
      "description": "Scroll to the bottom of the page",
      "params": {
        "times": { "type": "int", "default": 1, "description": "Number of times to scroll" },
        "delay_ms": { "type": "int", "default": 1500, "description": "Delay between scrolls in ms" }
      }
    },
    {
      "type": "click",
      "description": "Click an element by CSS selector or visible text",
      "params": {
        "selector": { "type": "string", "description": "CSS selector (alternative to text)" },
        "text": { "type": "string", "description": "Visible text of the element to click" },
        "wait_after_ms": { "type": "int", "default": 2000, "description": "Wait after click in ms" }
      }
    }
  ]
}
```

---

## POST `/api/scrape`

Scrapes one or more URLs and returns structured results with optional HTML and extracted data.

### Request Body

You must provide exactly one of:

- `url` (string), or
- `urls` (array of strings)

Optional fields:

- `commands` (array, default `[]`)
- `html` (boolean, default `true`)
- `page` (integer, default `1`, min `1`)
- `per_page` (integer, default `10`, max `100`)

### Example: Single URL

```/dev/null/curl.sh#L1-8
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "commands": [
      { "type": "extract", "params": { "selector": "h1", "attr": "text" } }
    ]
  }'
```

### Example: Multiple URLs with pagination

```/dev/null/curl.sh#L1-10
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://a.com", "https://b.com", "https://c.com"],
    "commands": [{ "type": "scroll", "params": { "times": 2 } }],
    "html": false,
    "page": 1,
    "per_page": 2
  }'
```

### Response `200` (example)

```/dev/null/scrape-response.json#L1-24
{
  "results": [
    {
      "url": "https://example.com",
      "status": "ok",
      "html_length": 528,
      "html": "<!DOCTYPE html>...",
      "extracted": [
        {
          "selector": "h1",
          "attr": "text",
          "values": ["Example Domain"]
        }
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

### Response `400` (examples)

Invalid JSON body:

```/dev/null/error.json#L1-3
{
  "error": "Request body must be valid JSON"
}
```

Missing `url`/`urls`:

```/dev/null/error.json#L1-3
{
  "error": "Provide 'url' (string) or 'urls' (list of strings)"
}
```

Invalid `commands` type:

```/dev/null/error.json#L1-3
{
  "error": "'commands' must be a list"
}
```

Invalid command type:

```/dev/null/error.json#L1-3
{
  "error": "commands[0].type 'bad' is invalid. Must be one of: click, extract, scroll, wait_selector, wait_timeout"
}
```

Invalid pagination values:

```/dev/null/error.json#L1-3
{
  "error": "'page' and 'per_page' must be integers"
}
```

### Response `429`

```/dev/null/error.json#L1-3
{
  "error": "Rate limit exceeded. Try again later."
}
```

---

## POST `/api/scrape/zip`

Runs a scrape for one or more URLs and returns a ZIP file containing rendered HTML documents.

### Request Body

Same body schema as `POST /api/scrape`:

- `url` or `urls` required
- `commands` optional (must be array if provided)

### Example

```/dev/null/curl.sh#L1-6
curl -X POST http://localhost:5000/api/scrape/zip \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com", "https://example.org"]}' \
  -o scraped.zip
```

### Response `200`

- `Content-Type: application/zip`
- `Content-Disposition: attachment; filename=scraped.zip`

### Response `400` / `429`

Uses the same error format as other API endpoints.

---

## Command Types (for `commands[]`)

Each command item should be an object with:

- `type` (string)
- `params` (object, optional but recommended)

Supported `type` values:

### `scroll`

Parameters:

- `times` (int, default `1`)
- `delay_ms` (int, default `1500`)

Example:

```/dev/null/command.json#L1-1
{ "type": "scroll", "params": { "times": 3, "delay_ms": 1000 } }
```

### `click`

Parameters:

- `selector` (string, optional)
- `text` (string, optional)
- `wait_after_ms` (int, default `2000`)

Example:

```/dev/null/command.json#L1-1
{ "type": "click", "params": { "text": "Show more", "wait_after_ms": 1500 } }
```

### `extract`

Parameters:

- `selector` (string, required)
- `attr` (string, default `text`; can be `text`, `html`, or attribute like `href`)

Example:

```/dev/null/command.json#L1-1
{ "type": "extract", "params": { "selector": "a.article-link", "attr": "href" } }
```

### `wait_selector`

Parameters:

- `selector` (string, required)
- `timeout` (int, default `10000`)

Example:

```/dev/null/command.json#L1-1
{ "type": "wait_selector", "params": { "selector": ".results", "timeout": 12000 } }
```

### `wait_timeout`

Parameters:

- `ms` (int, required)

Example:

```/dev/null/command.json#L1-1
{ "type": "wait_timeout", "params": { "ms": 3000 } }
```

---

## Notes

- URLs without protocol are normalized to `https://` internally.
- Multi-URL responses include pagination metadata even when only one page is returned.
- Per-URL scrape errors do not fail the entire request; each result item reports `status: "ok"` or `status: "error"`.