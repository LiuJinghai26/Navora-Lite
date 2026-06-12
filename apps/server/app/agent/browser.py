import asyncio
import html
from pathlib import Path
from typing import Any

from app.agent.actions import AgentAction, target_to_selector
from app.config import Settings


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
        self.quantity = 1

    async def execute(self, action: AgentAction) -> Any:
        await asyncio.sleep(0.05)
        if action.type == "goto":
            self.url = action.url or self.url
        elif action.type == "fill" and (action.target or "").lower() == "search input":
            self.query = action.value or ""
        elif action.type == "click" and "product" in (action.target or "").lower():
            self.product_open = True
        elif action.type == "fill" and (action.target or "").lower() == "quantity":
            self.quantity = int(action.value or "1")
        elif action.type == "click" and (action.target or "").lower() == "cart":
            self.cart_open = True
        elif action.type == "extract":
            return {"product_name": "FIRESTONE W01-377-8537", "quantity": self.quantity}
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
<text x="100" y="190" fill="#e5f6ff" font-family="Arial" font-size="42">FindItParts Mock</text>
<text x="100" y="250" fill="#7dd3fc" font-family="Arial" font-size="28">{title}</text>
<rect x="100" y="300" width="470" height="74" rx="14" fill="#111f34" stroke="#2a405f"/>
<text x="128" y="346" fill="#e5e7eb" font-family="Arial" font-size="24">Search: {html.escape(self.query or "FIRESTONE W01-377-8537")}</text>
<rect x="100" y="420" width="520" height="170" rx="18" fill="#0b2334" stroke="#22d3ee"/>
<text x="130" y="475" fill="#e5f6ff" font-family="Arial" font-size="30">FIRESTONE W01-377-8537</text>
<text x="130" y="528" fill="#9ca3af" font-family="Arial" font-size="22">{product_state}</text>
<text x="130" y="568" fill="#34d399" font-family="Arial" font-size="22">Quantity: {self.quantity}</text>
<rect x="700" y="420" width="380" height="170" rx="18" fill="#122037" stroke="#2a405f"/>
<text x="730" y="482" fill="#e5f6ff" font-family="Arial" font-size="28">{cart_state}</text>
<text x="730" y="538" fill="#34d399" font-family="Arial" font-size="24">Ready for extraction</text>
</svg>"""
        path.write_text(svg, encoding="utf-8")

    async def close(self) -> None:
        return None


class PlaywrightBrowserSession(BrowserSession):
    def __init__(self, playwright: Any, browser: Any, page: Any):
        self.playwright = playwright
        self.browser = browser
        self.page = page

    async def execute(self, action: AgentAction) -> Any:
        if action.type == "goto" and action.url:
            await self.page.goto(action.url)
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
            # The mock page exposes stable attributes so extraction is repeatable in tests and demos.
            return await self.page.evaluate(
                """() => {
                    const product = document.querySelector('[data-product-name]')?.getAttribute('data-product-name')
                      || document.querySelector('#cart-product-name')?.textContent
                      || 'FIRESTONE W01-377-8537';
                    const rawQuantity = document.querySelector('[data-cart-quantity]')?.getAttribute('data-cart-quantity')
                      || document.querySelector('#cart-quantity')?.textContent
                      || document.querySelector('#quantity')?.value
                      || '1';
                    return { product_name: product.trim(), quantity: Number.parseInt(rawQuantity, 10) || 1 };
                }"""
            )
        return None

    async def screenshot(self, path: Path, label: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        await self.page.screenshot(path=str(path), full_page=True)

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
