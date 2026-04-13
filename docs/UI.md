# Web UI Guide

This guide shows you how to use the web interface to build and run scraping pipelines without writing code.

## 1) Open the app

Start the server and open:

- `http://localhost:5000`

You’ll land on the main UI page.

---

## 2) Enter target URLs

In the **Target URLs** box:

- Enter **one URL per line**
- You can paste a single URL or many URLs
- If a URL is missing a scheme, the app will try to use `https://`

Example:

```/dev/null/example-urls.txt#L1-3
https://inside.fifa.com/fifa-world-ranking/men
https://example.com
https://news.ycombinator.com
```

---

## 3) Build your command pipeline

In the **Commands** section, add command blocks to define what happens on each page.

General workflow:

1. Click command buttons to add blocks
2. Fill in each block’s parameters
3. Drag blocks to reorder
4. Run top-to-bottom for every URL

Think of this as a repeatable browser macro.

---

## 4) Run the scraper

Click **Run Scraper**.

What to expect:

- Progress/status updates while processing URLs
- One result card per URL
- First card usually expanded, others collapsed
- Click a card header to expand/collapse details

---

## 5) Review and export results

Per result card you can typically:

- **Copy** HTML to clipboard
- **Download** single-page HTML
- Inspect extracted output if you used `extract`

Global exports:

- **Download All (.zip)** for all HTML pages
- **Download CSV** for extracted data across URLs

---

## 6) Save and load pipelines

Use:

- **Export** to download pipeline JSON
- **Import** to restore a saved pipeline

This is useful for repeat scrapes and sharing setups with teammates.

Pipeline JSON is an array of command objects (`type` + `params`), for example:

```/dev/null/pipeline-example.json#L1-6
[
  { "type": "click", "params": { "text": "Show full rankings" } },
  { "type": "wait_timeout", "params": { "ms": "3000" } },
  { "type": "scroll", "params": { "times": "1" } }
]
```

---

# Command Guide

## `scroll`

Scrolls to the bottom of the page repeatedly. Best for infinite scroll or lazy-loaded feeds.

Parameters:

- `times` (int, default: `1`) — number of scroll actions
- `delay_ms` (int, default: `1500`) — delay between scrolls

Use when content appears only after scrolling.

---

## `click`

Clicks a UI element using either CSS selector or visible text.

Parameters:

- `selector` (string, optional) — CSS selector target
- `text` (string, optional) — visible text target
- `wait_after_ms` (int, default: `2000`) — post-click delay

Tips:

- Provide either `selector` or `text`
- Use `wait_selector` after click when waiting for a specific section to appear

---

## `extract`

Collects values from elements matching a selector.

Parameters:

- `selector` (string, required) — CSS selector for elements to read
- `attr` (string, default: `text`) — what to return:
  - `text` for text content
  - `html` for inner HTML
  - any attribute name (e.g. `href`, `src`, `data-id`)

Output appears in each result’s `extracted` list.

---

## `wait_selector`

Waits until a selector becomes visible. Useful for dynamic pages.

Parameters:

- `selector` (string, required) — selector to wait for
- `timeout` (int, default: `10000`) — max wait time in milliseconds

Prefer this over fixed sleeps when possible.

---

## `wait_timeout`

Waits a fixed amount of time.

Parameters:

- `ms` (int, required) — sleep duration in milliseconds

Use as a fallback when event/selector-based waits are not reliable.

---

# Recommended pipeline patterns

## Pattern A: Expand + wait + extract

Good for “Show more” buttons.

```/dev/null/pattern-a.txt#L1-3
1) click         text: "Show more"
2) wait_selector selector: ".loaded-section"
3) extract       selector: ".loaded-section .item-title", attr: "text"
```

## Pattern B: Infinite scroll feed

Good for timeline or product listing pages.

```/dev/null/pattern-b.txt#L1-2
1) scroll        times: 5, delay_ms: 800
2) extract       selector: ".card a", attr: "href"
```

## Pattern C: Modal interaction

```/dev/null/pattern-c.txt#L1-4
1) click         selector: ".open-modal"
2) wait_selector selector: ".modal-content"
3) extract       selector: ".modal-content .value", attr: "text"
4) click         selector: ".modal-close"
```

---

# Troubleshooting

## No data extracted

- Verify the selector matches rendered DOM, not initial source
- Try adding `wait_selector` before `extract`
- Confirm `attr` is valid for the target element (`href`, `src`, etc.)

## Click does nothing

- Try selector-based click instead of text-based
- Add a short `wait_timeout` before click if element appears late
- Add `wait_after_ms` or `wait_selector` after click

## Some URLs fail but others succeed

This is normal for mixed URL batches. Each URL is processed independently; one failure does not block others.

## Results are too large

Set API/UI behavior to avoid unnecessary HTML when you only need extraction results, and export CSV for compact output.

---

# Quick example workflow

Goal: scrape FIFA rankings page after expanding full list.

```/dev/null/fifa-workflow.txt#L1-4
URLs:
https://inside.fifa.com/fifa-world-ranking/men

Pipeline:
1) click text="Show full rankings"
2) wait_timeout ms=3000
3) scroll times=1
```

Then run and export HTML/CSV as needed.