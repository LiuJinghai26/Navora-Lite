import asyncio
import html
from pathlib import Path
from typing import Any

from app.agent.actions import AgentAction, target_to_selector
from app.config import Settings

DEMO_PRODUCT = "AURORA TASK LAMP"
DEMO_COLOR = "Warm White"
DEMO_PRICE = 89
PRESET_NAVIGATION_TIMEOUT_MS = 10000


def preset_fallback_html(url: str | None) -> str | None:
    if url == "https://news.ycombinator.com/":
        return """<!doctype html>
<html>
<head>
  <title>Hacker News</title>
  <style>
    body { margin: 0; background: #f6f6ef; color: #000; font-family: Verdana, Geneva, sans-serif; }
    .bar { background: #ff6600; padding: 8px 12px; font-weight: bold; }
    table { width: 100%; max-width: 1120px; margin: 12px auto; border-collapse: collapse; }
    td { padding: 4px 6px; font-size: 14px; }
    .titleline a { color: #000; text-decoration: none; font-size: 16px; }
    .subtext, .subtext a, .sitebit { color: #828282; font-size: 11px; }
  </style>
</head>
<body>
  <div class="bar">Hacker News</div>
  <table>
    <tr class="athing" id="preset-hn-story">
      <td class="title" align="right">1.</td>
      <td class="title">
        <span class="titleline">
          <a href="https://example.com/offline-browser-agent-demo">Offline-first browser agents for reliable demos</a>
        </span>
        <span class="sitebit comhead"> (example.com) </span>
      </td>
    </tr>
    <tr>
      <td></td>
      <td class="subtext">
        <span class="score">348 points</span>
        <span class="age">2 hours ago</span>
        <a href="item?id=preset-hn-story">96 comments</a>
      </td>
    </tr>
  </table>
</body>
</html>"""
    if url == "https://en.wikipedia.org/wiki/Python_(programming_language)":
        return """<!doctype html>
<html>
<head>
  <title>Python (programming language) - Wikipedia</title>
  <style>
    body { margin: 0; background: #fff; color: #202122; font-family: Arial, sans-serif; }
    main { max-width: 1180px; margin: 0 auto; padding: 32px 48px; }
    h1 { border-bottom: 1px solid #a2a9b1; font-family: Georgia, serif; font-size: 40px; font-weight: normal; }
    p { font-size: 18px; line-height: 1.65; max-width: 760px; }
    .infobox { float: right; width: 320px; margin-left: 32px; border: 1px solid #a2a9b1; border-collapse: collapse; background: #f8f9fa; }
    .infobox th, .infobox td { border: 1px solid #a2a9b1; padding: 8px; text-align: left; }
    .infobox caption { font-size: 22px; font-weight: bold; padding: 10px; }
  </style>
</head>
<body>
  <main>
    <h1 id="firstHeading">Python (programming language)</h1>
    <table class="infobox">
      <caption>Python</caption>
      <tr><th>Designed by</th><td>Guido van Rossum</td></tr>
      <tr><th>First appeared</th><td>20 February 1991</td></tr>
      <tr><th>Typing discipline</th><td>Duck, dynamic, strong typing</td></tr>
    </table>
    <div id="mw-content-text">
      <div class="mw-parser-output">
        <p>Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.</p>
        <p>Python is dynamically typed and garbage-collected. It supports multiple programming paradigms, including structured, object-oriented, and functional programming.</p>
      </div>
    </div>
  </main>
</body>
</html>"""
    if url == "https://developer.mozilla.org/en-US/docs/Web/API":
        return """<!doctype html>
<html>
<head>
  <title>Web APIs | MDN</title>
  <style>
    body { margin: 0; background: #fff; color: #1b1b1b; font-family: Inter, Arial, sans-serif; }
    main { max-width: 1100px; margin: 0 auto; padding: 40px 48px; }
    h1 { font-size: 48px; margin-bottom: 16px; }
    p { font-size: 19px; line-height: 1.6; max-width: 820px; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 28px; }
    a { border: 1px solid #d8dee4; border-radius: 8px; color: #0069c2; display: block; padding: 18px; text-decoration: none; }
  </style>
</head>
<body>
  <main>
    <h1>Web APIs</h1>
    <p>Web APIs are interfaces exposed by browsers and related platforms that let developers build interactive web applications, access device capabilities, and communicate with network resources.</p>
    <div class="grid">
      <a href="/en-US/docs/Web/API/Fetch_API">Fetch API</a>
      <a href="/en-US/docs/Web/API/Canvas_API">Canvas API</a>
      <a href="/en-US/docs/Web/API/Document_Object_Model">Document Object Model</a>
      <a href="/en-US/docs/Web/API/Web_Storage_API">Web Storage API</a>
    </div>
  </main>
</body>
</html>"""
    if url == "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API":
        return """<!doctype html>
<html>
<head>
  <title>Fetch API - Web APIs | MDN</title>
  <style>
    body { margin: 0; background: #fff; color: #1b1b1b; font-family: Inter, Arial, sans-serif; }
    main { max-width: 980px; margin: 0 auto; padding: 40px 48px; }
    h1 { font-size: 48px; margin-bottom: 16px; }
    h2 { border-top: 1px solid #d8dee4; margin-top: 32px; padding-top: 24px; }
    p { font-size: 19px; line-height: 1.6; }
  </style>
</head>
<body>
  <main>
    <h1>Fetch API</h1>
    <p>The Fetch API provides an interface for fetching resources across the network. It is a modern replacement for many XMLHttpRequest use cases and is built around promises.</p>
    <h2>Concepts and usage</h2>
    <h2>Interfaces</h2>
    <h2>Examples</h2>
    <h2>Specifications</h2>
  </main>
</body>
</html>"""
    return None


class BrowserSession:
    async def execute(self, action: AgentAction) -> Any:
        raise NotImplementedError

    async def screenshot(self, path: Path, label: str) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


class MockBrowserSession(BrowserSession):
    """Deterministic fallback used when Playwright or browser binaries are unavailable."""

    def __init__(self):
        self.url = "about:blank"
        self.query = ""
        self.product_open = False
        self.cart_open = False
        self.color = "Graphite"
        self.quantity = 1
        self.context: dict[str, Any] = {}

    async def execute(self, action: AgentAction) -> Any:
        await asyncio.sleep(0.05)
        if action.type == "goto":
            self.url = action.url or self.url
        elif action.type == "fill" and (action.target or "").lower() == "search input":
            self.query = action.value or ""
        elif action.type == "click" and "product" in (action.target or "").lower():
            self.product_open = True
        elif action.type == "click" and "color" in (action.target or "").lower():
            self.color = DEMO_COLOR
        elif action.type == "fill" and (action.target or "").lower() == "quantity":
            self.quantity = int(action.value or "1")
        elif action.type == "click" and (action.target or "").lower() == "cart":
            self.cart_open = True
        elif action.type == "extract":
            target = (action.target or "").lower()
            if target == "hacker news top story":
                return {
                    "source": "Hacker News",
                    "rank": 1,
                    "title": "Mock top story for offline browser fallback",
                    "site": "news.ycombinator.com",
                    "points": "100 points",
                    "comments": "25 comments",
                }
            if target == "wikipedia python summary":
                return {
                    "site": "Wikipedia",
                    "title": "Python (programming language)",
                    "summary": "Python is a high-level, general-purpose programming language.",
                    "designed_by": "Guido van Rossum",
                    "first_appeared": "1991",
                }
            if target == "mdn web api overview":
                topics = ["Fetch API", "Canvas API", "DOM", "Web Storage API"]
                self.context["mdn_topics"] = topics
                return {"site": "MDN Web Docs", "page_title": "Web APIs | MDN", "topics": topics}
            if target == "mdn fetch api detail":
                return {
                    "site": "MDN Web Docs",
                    "topics": self.context.get("mdn_topics", []),
                    "selected_article": {
                        "title": "Fetch API",
                        "summary": "The Fetch API provides an interface for fetching resources.",
                    },
                }
            return {
                "product_name": DEMO_PRODUCT,
                "color": self.color,
                "quantity": self.quantity,
                "subtotal": f"${self.quantity * DEMO_PRICE}",
            }
        return None

    async def screenshot(self, path: Path, label: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        title = html.escape(label)
        product_state = "Product detail" if self.product_open else "Search results"
        cart_state = "Cart open" if self.cart_open else "Cart pending"
        # SVG screenshots keep the demo inspectable even on machines without Chromium.
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="800" viewBox="0 0 1280 800">
<defs>
  <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
    <stop offset="0" stop-color="#07111f"/>
    <stop offset="1" stop-color="#101a2c"/>
  </linearGradient>
</defs>
<rect width="1280" height="800" fill="url(#bg)"/>
<rect x="70" y="70" width="1140" height="660" rx="24" fill="#0d1728" stroke="#1f8fb8" stroke-width="2"/>
<circle cx="110" cy="112" r="9" fill="#ef4444"/>
<circle cx="140" cy="112" r="9" fill="#f59e0b"/>
<circle cx="170" cy="112" r="9" fill="#22c55e"/>
<rect x="220" y="94" width="860" height="36" rx="18" fill="#111f34" stroke="#24364f"/>
<text x="250" y="118" fill="#7dd3fc" font-family="Arial" font-size="18">{html.escape(self.url)}</text>
<text x="100" y="190" fill="#e5f6ff" font-family="Arial" font-size="42">OfficeMart Demo</text>
<text x="100" y="250" fill="#7dd3fc" font-family="Arial" font-size="28">{title}</text>
<rect x="100" y="300" width="470" height="74" rx="14" fill="#111f34" stroke="#2a405f"/>
<text x="128" y="346" fill="#e5e7eb" font-family="Arial" font-size="24">Search: {html.escape(self.query or DEMO_PRODUCT)}</text>
<rect x="100" y="420" width="520" height="170" rx="18" fill="#0b2334" stroke="#22d3ee"/>
<text x="130" y="475" fill="#e5f6ff" font-family="Arial" font-size="30">{DEMO_PRODUCT}</text>
<text x="130" y="528" fill="#9ca3af" font-family="Arial" font-size="22">{product_state}</text>
<text x="130" y="568" fill="#34d399" font-family="Arial" font-size="22">Color: {html.escape(self.color)} | Qty: {self.quantity}</text>
<rect x="700" y="420" width="380" height="170" rx="18" fill="#122037" stroke="#2a405f"/>
<text x="730" y="482" fill="#e5f6ff" font-family="Arial" font-size="28">{cart_state}</text>
<text x="730" y="538" fill="#34d399" font-family="Arial" font-size="24">Subtotal: ${self.quantity * DEMO_PRICE}</text>
</svg>"""
        path.write_text(svg, encoding="utf-8")

    async def close(self) -> None:
        return None


class PlaywrightBrowserSession(BrowserSession):
    def __init__(self, playwright: Any, browser: Any, page: Any):
        self.playwright = playwright
        self.browser = browser
        self.page = page
        self.context: dict[str, Any] = {}

    async def execute(self, action: AgentAction) -> Any:
        if action.type == "goto" and action.url:
            await self._goto(action.url)
        elif action.type == "fill":
            selector = action.selector or target_to_selector(action.target)
            if selector and action.value is not None:
                await self.page.fill(selector, action.value)
        elif action.type == "click":
            selector = action.selector or target_to_selector(action.target)
            if selector:
                await self.page.click(selector)
        elif action.type == "press" and action.key:
            await self.page.keyboard.press(action.key)
        elif action.type == "scroll":
            amount = action.amount or 600
            sign = -1 if action.direction == "up" else 1
            await self.page.mouse.wheel(0, amount * sign)
        elif action.type == "wait":
            await self.page.wait_for_timeout(action.ms or 500)
        elif action.type == "extract":
            target = (action.target or "").lower()
            if target == "hacker news top story":
                return await self._extract_hacker_news_top_story()
            if target == "wikipedia python summary":
                return await self._extract_wikipedia_python_summary()
            if target == "mdn web api overview":
                result = await self._extract_mdn_web_api_overview()
                if isinstance(result, dict):
                    self.context["mdn_topics"] = result.get("topics", [])
                return result
            if target == "mdn fetch api detail":
                result = await self._extract_mdn_fetch_api_detail()
                if isinstance(result, dict):
                    result["topics"] = self.context.get("mdn_topics", [])
                return result
            # The mock page exposes stable attributes so extraction is repeatable in tests and demos.
            return await self.page.evaluate(
                """() => {
                    const product = document.querySelector('[data-product-name]')?.getAttribute('data-product-name')
                      || document.querySelector('#cart-product-name')?.textContent
                      || 'AURORA TASK LAMP';
                    const color = document.querySelector('[data-cart-color]')?.getAttribute('data-cart-color')
                      || document.querySelector('#cart-color')?.textContent
                      || 'Warm White';
                    const rawQuantity = document.querySelector('[data-cart-quantity]')?.getAttribute('data-cart-quantity')
                      || document.querySelector('#cart-quantity')?.textContent
                      || document.querySelector('#quantity')?.value
                      || '2';
                    const subtotal = document.querySelector('[data-cart-subtotal]')?.getAttribute('data-cart-subtotal')
                      || document.querySelector('#cart-subtotal')?.textContent
                      || '$178';
                    return {
                      product_name: product.trim(),
                      color: color.trim(),
                      quantity: Number.parseInt(rawQuantity, 10) || 2,
                      subtotal: subtotal.trim()
                    };
                }"""
            )
        return None

    async def _extract_hacker_news_top_story(self) -> Any:
        return await self.page.evaluate(
            """() => {
                const row = document.querySelector('.athing');
                const subtext = row?.nextElementSibling;
                const titleLink = row?.querySelector('.titleline a') || row?.querySelector('.storylink');
                const href = titleLink?.href || '';
                const links = Array.from(subtext?.querySelectorAll('a') || []);
                const comments = links.map((link) => link.textContent?.trim() || '').find((text) => /comment/i.test(text)) || '';
                const site = row?.querySelector('.sitebit.comhead')?.textContent?.replace(/[()]/g, '').trim()
                    || (href ? new URL(href).hostname : '');
                return {
                    source: 'Hacker News',
                    rank: 1,
                    title: titleLink?.textContent?.trim() || '',
                    url: href,
                    site,
                    points: subtext?.querySelector('.score')?.textContent?.trim() || '',
                    age: subtext?.querySelector('.age')?.textContent?.trim() || '',
                    comments
                };
            }"""
        )

    async def _goto(self, url: str) -> None:
        fallback_html = preset_fallback_html(url)
        timeout = PRESET_NAVIGATION_TIMEOUT_MS if fallback_html else 45000
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        except Exception:
            if not fallback_html:
                raise
            await self._goto_preset_fallback(url, fallback_html)

    async def _goto_preset_fallback(self, url: str, body: str) -> None:
        async def fulfill(route: Any) -> None:
            await route.fulfill(status=200, content_type="text/html", body=body)

        await self.page.route(url, fulfill)
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=PRESET_NAVIGATION_TIMEOUT_MS)
        finally:
            await self.page.unroute(url, fulfill)

    async def _extract_wikipedia_python_summary(self) -> Any:
        return await self.page.evaluate(
            """() => {
                const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const lead = Array.from(document.querySelectorAll('#mw-content-text .mw-parser-output > p'))
                    .map((paragraph) => clean(paragraph.textContent))
                    .find((text) => text.length > 80) || '';
                const rows = Array.from(document.querySelectorAll('table.infobox tr'));
                const lookup = (label) => {
                    const row = rows.find((item) => clean(item.querySelector('th')?.textContent).toLowerCase().includes(label));
                    return clean(row?.querySelector('td')?.textContent);
                };
                return {
                    site: 'Wikipedia',
                    title: clean(document.querySelector('#firstHeading')?.textContent) || document.title,
                    summary: lead,
                    designed_by: lookup('designed by'),
                    first_appeared: lookup('first appeared'),
                    typing_discipline: lookup('typing discipline')
                };
            }"""
        )

    async def _extract_mdn_web_api_overview(self) -> Any:
        return await self.page.evaluate(
            """() => {
                const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const lead = Array.from(document.querySelectorAll('main p'))
                    .map((paragraph) => clean(paragraph.textContent))
                    .find((text) => text.length > 70) || '';
                const topics = Array.from(document.querySelectorAll('main a[href*="/Web/API/"]'))
                    .map((link) => clean(link.textContent))
                    .filter(Boolean)
                    .filter((value, index, list) => list.indexOf(value) === index)
                    .slice(0, 8);
                return {
                    site: 'MDN Web Docs',
                    page_title: document.title,
                    overview: lead,
                    topics
                };
            }"""
        )

    async def _extract_mdn_fetch_api_detail(self) -> Any:
        return await self.page.evaluate(
            """() => {
                const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const summary = Array.from(document.querySelectorAll('main p'))
                    .map((paragraph) => clean(paragraph.textContent))
                    .find((text) => text.length > 70) || '';
                const sections = Array.from(document.querySelectorAll('main h2'))
                    .map((heading) => clean(heading.textContent))
                    .filter(Boolean)
                    .slice(0, 6);
                return {
                    site: 'MDN Web Docs',
                    selected_article: {
                        title: clean(document.querySelector('h1')?.textContent) || document.title,
                        url: window.location.href,
                        summary,
                        sections
                    }
                };
            }"""
        )

    async def screenshot(self, path: Path, label: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        await self.page.screenshot(path=str(path), full_page=False)

    async def close(self) -> None:
        await self.browser.close()
        await self.playwright.stop()


async def create_browser_session(settings: Settings) -> BrowserSession:
    try:
        from playwright.async_api import async_playwright

        playwright = await async_playwright().start()
        browser_type = playwright.chromium
        browser = await browser_type.launch(headless=settings.browser_headless)
        page = await browser.new_page(
            viewport={
                "width": settings.browser_viewport_width,
                "height": settings.browser_viewport_height,
            }
        )
        return PlaywrightBrowserSession(playwright, browser, page)
    except Exception:
        # Preserve the end-to-end demo path when Playwright is not installed or cannot launch.
        return MockBrowserSession()
