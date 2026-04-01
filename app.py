import csv
import io
import re
import zipfile
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify, Response
from scraper import execute_scrape

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Web UI routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/docs")
def docs():
    return render_template("docs.html")


@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    urls = data.get("urls", [])
    commands = data.get("commands", [])

    if not urls:
        return jsonify({"error": "At least one URL is required"}), 400

    results = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            scraped = execute_scrape(url, commands)
            results.append(
                {
                    "url": url,
                    "html": scraped["html"],
                    "extracted": scraped["extracted"],
                    "error": None,
                }
            )
        except Exception as e:
            results.append({"url": url, "html": None, "extracted": [], "error": str(e)})

    return jsonify({"results": results})


@app.route("/download-zip", methods=["POST"])
def download_zip():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400
    results = data.get("results", [])

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, r in enumerate(results):
            if not r.get("html"):
                continue
            filename = _url_to_filename(r["url"], i)
            zf.writestr(filename, r["html"])

    buf.seek(0)
    return Response(
        buf.read(),
        mimetype="application/zip",
        headers={"Content-Disposition": "attachment; filename=scraped.zip"},
    )


@app.route("/download-csv", methods=["POST"])
def download_csv():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400
    results = data.get("results", [])

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["url", "selector", "index", "value"])

    for r in results:
        url = r.get("url", "")
        for ext in r.get("extracted", []):
            selector = ext.get("selector", "")
            for j, val in enumerate(ext.get("values", [])):
                writer.writerow([url, selector, j, val])

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=extracted.csv"},
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

COMMANDS = [
    {
        "type": "scroll",
        "description": "Scroll to the bottom of the page",
        "params": {
            "times": {
                "type": "int",
                "default": 1,
                "description": "Number of times to scroll",
            },
            "delay_ms": {
                "type": "int",
                "default": 1500,
                "description": "Delay between scrolls in ms",
            },
        },
    },
    {
        "type": "click",
        "description": "Click an element by CSS selector or visible text",
        "params": {
            "selector": {
                "type": "string",
                "description": "CSS selector (alternative to text)",
            },
            "text": {
                "type": "string",
                "description": "Visible text of the element to click",
            },
            "wait_after_ms": {
                "type": "int",
                "default": 2000,
                "description": "Wait after click in ms",
            },
        },
    },
    {
        "type": "extract",
        "description": "Extract data from elements matching a CSS selector",
        "params": {
            "selector": {
                "type": "string",
                "required": True,
                "description": "CSS selector for elements to extract",
            },
            "attr": {
                "type": "string",
                "default": "text",
                "description": "What to extract: 'text', 'html', or an attribute name like 'href'",
            },
        },
    },
    {
        "type": "wait_selector",
        "description": "Wait for a CSS selector to become visible",
        "params": {
            "selector": {
                "type": "string",
                "required": True,
                "description": "CSS selector to wait for",
            },
            "timeout": {
                "type": "int",
                "default": 10000,
                "description": "Timeout in ms",
            },
        },
    },
    {
        "type": "wait_timeout",
        "description": "Wait for a fixed duration",
        "params": {
            "ms": {
                "type": "int",
                "required": True,
                "description": "Duration in milliseconds",
            },
        },
    },
]


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok"})


@app.route("/api/commands", methods=["GET"])
def api_commands():
    return jsonify({"commands": COMMANDS})


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    data = request.get_json(silent=True)
    if data is None:
        return _api_error(400, "Request body must be valid JSON")

    if "urls" in data:
        urls = data["urls"]
    elif "url" in data:
        urls = [data["url"]]
    else:
        urls = []

    if not urls or not isinstance(urls, list):
        return _api_error(400, "Provide 'url' (string) or 'urls' (list of strings)")

    commands = data.get("commands", [])
    if not isinstance(commands, list):
        return _api_error(400, "'commands' must be a list")

    validation_error = _validate_commands(commands)
    if validation_error:
        return _api_error(400, validation_error)

    return_html = data.get("html", True)

    results = []
    for raw_url in urls:
        if not isinstance(raw_url, str) or not raw_url.strip():
            continue
        url = raw_url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            scraped = execute_scrape(url, commands)
            entry = {"url": url, "status": "ok", "html_length": len(scraped["html"])}
            if return_html:
                entry["html"] = scraped["html"]
            if scraped["extracted"]:
                entry["extracted"] = scraped["extracted"]
            results.append(entry)
        except Exception as e:
            results.append({"url": url, "status": "error", "error": str(e)})

    return jsonify({"results": results})


@app.route("/api/scrape/zip", methods=["POST"])
def api_scrape_zip():
    data = request.get_json(silent=True)
    if data is None:
        return _api_error(400, "Request body must be valid JSON")

    if "urls" in data:
        urls = data["urls"]
    elif "url" in data:
        urls = [data["url"]]
    else:
        urls = []

    if not urls or not isinstance(urls, list):
        return _api_error(400, "Provide 'url' (string) or 'urls' (list of strings)")

    commands = data.get("commands", [])
    if not isinstance(commands, list):
        return _api_error(400, "'commands' must be a list")

    validation_error = _validate_commands(commands)
    if validation_error:
        return _api_error(400, validation_error)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, raw_url in enumerate(urls):
            if not isinstance(raw_url, str) or not raw_url.strip():
                continue
            url = raw_url.strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            try:
                scraped = execute_scrape(url, commands)
                filename = _url_to_filename(url, i)
                zf.writestr(filename, scraped["html"])
            except Exception:
                continue

    buf.seek(0)
    return Response(
        buf.read(),
        mimetype="application/zip",
        headers={"Content-Disposition": "attachment; filename=scraped.zip"},
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _api_error(status, message):
    return jsonify({"error": message}), status


def _validate_commands(commands):
    valid_types = {c["type"] for c in COMMANDS}
    for i, cmd in enumerate(commands):
        if not isinstance(cmd, dict):
            return f"commands[{i}] must be an object"
        cmd_type = cmd.get("type")
        if cmd_type not in valid_types:
            return f"commands[{i}].type '{cmd_type}' is invalid. Must be one of: {', '.join(sorted(valid_types))}"
    return None


def _url_to_filename(url: str, index: int) -> str:
    parsed = urlparse(url)
    name = parsed.netloc + parsed.path.rstrip("/")
    name = re.sub(r"[^\w\-.]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = f"page_{index}"
    return f"{name}.html"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
