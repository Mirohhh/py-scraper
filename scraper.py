import re

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright


def execute_scrape(url: str, commands: list[dict]) -> dict:
    """Execute a scraping pipeline for a single URL using a fresh Playwright browser.

    Args:
        url: Target page URL.
        commands: Ordered list of command objects. Each command should include a
            `type` and optional `params` dict.

    Returns:
        A dict with:
            - "html": Rendered page HTML after all commands are applied.
            - "extracted": List of extraction result objects produced by `extract`
              commands.

    Notes:
        - Uses `domcontentloaded` for initial navigation and then waits briefly to
          allow additional dynamic rendering.
        - Always closes page context and browser resources in `finally`.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        extracted = []

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1000)

            for cmd in commands:
                result = _execute_command(page, cmd)
                if result is not None:
                    extracted.append(result)

            return {"html": page.content(), "extracted": extracted}
        finally:
            context.close()
            browser.close()


def _execute_command(page, cmd: dict):
    """Execute a single command against the current Playwright page.

    Supported command types:
        - scroll: Scroll to page bottom repeatedly.
        - click: Click by CSS selector or visible text.
        - extract: Collect text/html/attribute values from matching elements.
        - wait_selector: Wait for a selector to become visible.
        - wait_timeout: Sleep for a fixed duration (ms).

    Args:
        page: Playwright page instance.
        cmd: Command object with `type` and optional `params`.

    Returns:
        For `extract`, returns a dict:
            {"selector": str, "attr": str, "values": list[str]}
        For all other commands, returns None.

    Behavior:
        - Timeout-related click/wait failures are swallowed to keep pipeline
          execution resilient across varied pages.
        - Unknown command types are ignored and return None.
    """
    cmd_type = cmd.get("type", "")
    params = cmd.get("params", {})

    if cmd_type == "scroll":
        times = int(params.get("times", 1))
        delay = int(params.get("delay_ms", 1500))
        for _ in range(times):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(delay)

    elif cmd_type == "click":
        selector = params.get("selector", "").strip()
        text = params.get("text", "").strip()
        wait_after = int(params.get("wait_after_ms", 2000))

        if selector:
            try:
                loc = page.locator(selector).first
                loc.scroll_into_view_if_needed(timeout=5000)
                loc.click(timeout=10000)
                page.wait_for_timeout(wait_after)
            except PlaywrightTimeout:
                pass
        elif text:
            locator = page.get_by_text(re.compile(re.escape(text), re.IGNORECASE)).first
            try:
                locator.scroll_into_view_if_needed(timeout=5000)
                locator.click(timeout=10000)
                page.wait_for_timeout(wait_after)
            except PlaywrightTimeout:
                try:
                    role_loc = page.get_by_role(
                        "button", name=re.compile(re.escape(text), re.IGNORECASE)
                    ).first
                    role_loc.scroll_into_view_if_needed(timeout=3000)
                    role_loc.click(timeout=10000)
                    page.wait_for_timeout(wait_after)
                except PlaywrightTimeout:
                    pass

    elif cmd_type == "extract":
        selector = params.get("selector", "").strip()
        attr = params.get("attr", "text").strip().lower()
        if selector:
            elements = page.query_selector_all(selector)
            values = []
            for el in elements:
                if attr == "text":
                    values.append(el.text_content() or "")
                elif attr == "html":
                    values.append(el.inner_html() or "")
                else:
                    values.append(el.get_attribute(attr) or "")
            return {"selector": selector, "attr": attr, "values": values}

    elif cmd_type == "wait_selector":
        selector = params.get("selector", "")
        timeout = int(params.get("timeout", 10000))
        if selector:
            try:
                page.wait_for_selector(selector, state="visible", timeout=timeout)
            except PlaywrightTimeout:
                pass

    elif cmd_type == "wait_timeout":
        ms = int(params.get("ms", 1000))
        page.wait_for_timeout(ms)

    return None
