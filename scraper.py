import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def execute_scrape(url: str, commands: list[dict]) -> str:
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

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1000)

            for cmd in commands:
                _execute_command(page, cmd)

            return page.content()
        finally:
            context.close()
            browser.close()


def _execute_command(page, cmd: dict):
    cmd_type = cmd.get("type", "")
    params = cmd.get("params", {})

    if cmd_type == "scroll":
        times = int(params.get("times", 1))
        delay = int(params.get("delay_ms", 1500))
        for _ in range(times):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(delay)

    elif cmd_type == "click":
        text = params.get("text", "")
        wait_after = int(params.get("wait_after_ms", 2000))
        if text:
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
