import asyncio
import json
from pathlib import Path
import socket
import subprocess
import time
from typing import Any
import urllib.request
from uuid import uuid4

from app.agent.actions import AgentAction, target_to_selector
from app.config import Settings


def _unique_selectors(selectors: list[str | None]) -> list[str]:
    # Keep selector retries deterministic while removing empty and duplicate entries.
    seen: set[str] = set()
    unique: list[str] = []
    for selector in selectors:
        if selector and selector not in seen:
            unique.append(selector)
            seen.add(selector)
    return unique


class BrowserSession:
    # Small protocol used by the runner; concrete sessions can swap browser implementations.
    async def execute(self, action: AgentAction) -> Any:
        raise NotImplementedError

    async def screenshot(self, path: Path, label: str) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError

    async def keep_open(self) -> None:
        raise NotImplementedError


class PlaywrightBrowserSession(BrowserSession):
    def __init__(self, playwright: Any, browser: Any, page: Any, external_process: subprocess.Popen | None = None):
        self.playwright = playwright
        self.browser = browser
        self.page = page
        self.external_process = external_process
        self.context: dict[str, Any] = {}
        self._released = False

    async def execute(self, action: AgentAction) -> Any:
        # Dispatch stays centralized so screenshots, timing, and safety checks remain runner-owned.
        if action.type == "goto" and action.url:
            await self._goto(action.url)
        elif action.type == "fill":
            await self._fill(action)
        elif action.type == "click":
            await self._click(action)
        elif action.type == "press":
            await self._press(action)
        elif action.type == "scroll":
            amount = action.amount or 600
            sign = -1 if action.direction == "up" else 1
            await self.page.mouse.wheel(0, amount * sign)
        elif action.type == "wait":
            await self.page.wait_for_timeout(action.ms or 500)
        elif action.type == "extract":
            await self._wait_for_page_settle()
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
            if target == "wikipedia article summary":
                return await self._extract_wikipedia_article_summary()
            if target == "httpbin form echo":
                return await self._extract_httpbin_form_echo()
            if target == "page summary":
                return await self._extract_page_summary()
            if "news.ycombinator.com" in self.page.url:
                return await self._extract_hacker_news_stories()
            if "github.com/trending" in self.page.url:
                return await self._extract_github_trending()
            if "wikipedia.org" in self.page.url:
                return await self._extract_wikipedia_article_summary()
            if "httpbin.org/post" in self.page.url:
                return await self._extract_httpbin_form_echo()
            return await self._extract_page_summary()
        return None

    async def _fill(self, action: AgentAction) -> None:
        if action.value is None:
            return
        target = (action.target or "").lower()
        candidates = [action.selector]
        # Search fields vary widely across public sites, so try semantic fallbacks before failing.
        if "search" in target:
            candidates.extend(
                [
                    '[role="searchbox"]',
                    'input[name="search"]',
                    'input[name="q"]',
                    'input[name="query"]',
                    'input[name*="search" i]',
                    'input[type="search"]',
                    'input[aria-label*="search" i]',
                    'input[placeholder*="search" i]',
                    'input[id*="search" i]',
                    'input[class*="search" i]',
                    'textarea[aria-label*="search" i]',
                    "#searchInput",
                    "#search-input input",
                    "form[role='search'] input",
                    "form input[type='text']",
                ]
            )
        candidates.append(target_to_selector(action.target))
        await self._try_fill(candidates, action.value)

    async def _click(self, action: AgentAction) -> None:
        target = action.target or ""
        target_key = target.lower()
        candidates = [action.selector]
        if "search" in target_key and ("button" in target_key or "submit" in target_key):
            candidates.extend(
                [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button[aria-label*="search" i]',
                    'button[class*="search" i]',
                    'button:has-text("Search")',
                    'input[value*="Search" i]',
                ]
            )
        if "submit" in target_key:
            candidates.extend(['button:has-text("Submit")', 'input[type="submit"]', "button"])
        candidates.append(target_to_selector(action.target))
        selector_error: Exception | None = None
        try:
            await self._try_click(candidates)
            await self._wait_for_page_settle()
            return
        except Exception as exc:
            selector_error = exc
            if not target:
                raise
        # Role locators handle links/buttons whose accessible name matches the planner target.
        for locator in [self.page.get_by_role("link", name=target), self.page.get_by_role("button", name=target)]:
            try:
                await locator.first.click(timeout=2000)
                await self._wait_for_page_settle()
                return
            except Exception:
                continue
        if selector_error:
            raise selector_error
        raise ValueError(f"Could not click {target}")

    async def _press(self, action: AgentAction) -> None:
        key = action.key or action.target
        if not key:
            return
        aliases = {"return": "Enter", "enter": "Enter", "esc": "Escape"}
        await self.page.keyboard.press(aliases.get(key.lower(), key))

    async def _wait_for_page_settle(self) -> None:
        # Public pages can keep network requests open, so each load-state wait is best effort.
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        try:
            await self.page.wait_for_load_state("load", timeout=8000)
        except Exception:
            pass
        try:
            await self.page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass
        await self.page.wait_for_timeout(800)

    async def _try_fill(self, selectors: list[str | None], value: str) -> None:
        last_error: Exception | None = None
        candidates = _unique_selectors(selectors)
        if not candidates:
            raise ValueError("No fill selector candidates.")
        for selector in candidates:
            try:
                await self.page.locator(selector).first.fill(value, timeout=2000)
                return
            except Exception as exc:
                last_error = exc
        if last_error:
            raise last_error

    async def _try_click(self, selectors: list[str | None]) -> None:
        last_error: Exception | None = None
        candidates = _unique_selectors(selectors)
        if not candidates:
            raise ValueError("No click selector candidates.")
        for selector in candidates:
            try:
                await self.page.locator(selector).first.click(timeout=2000)
                return
            except Exception as exc:
                last_error = exc
        if last_error:
            raise last_error

    async def _evaluate(self, script: str) -> Any:
        last_error: Exception | None = None
        for _ in range(3):
            try:
                return await self.page.evaluate(script)
            except Exception as exc:
                last_error = exc
                message = str(exc)
                if "Execution context was destroyed" not in message and "Cannot find context" not in message:
                    raise
                # Navigation during extraction can destroy the JS context; wait and retry.
                try:
                    await self.page.wait_for_load_state("load", timeout=8000)
                except Exception:
                    pass
                await self.page.wait_for_timeout(1000)
        if last_error:
            raise last_error
        return None

    async def _extract_hacker_news_top_story(self) -> Any:
        # Site-specific extractors keep common demos more reliable than a generic page summary.
        return await self._evaluate(
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

    async def _extract_hacker_news_stories(self) -> Any:
        return await self._evaluate(
            """() => {
                const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                return {
                    source: 'Hacker News',
                    url: window.location.href,
                    stories: Array.from(document.querySelectorAll('.athing')).slice(0, 10).map((row) => {
                        const subtext = row.nextElementSibling;
                        const titleLink = row.querySelector('.titleline a') || row.querySelector('.storylink');
                        const href = titleLink?.href || '';
                        const links = Array.from(subtext?.querySelectorAll('a') || []);
                        const comments = links.map((link) => clean(link.textContent)).find((text) => /comment/i.test(text)) || '';
                        return {
                            rank: Number.parseInt(clean(row.querySelector('.rank')?.textContent), 10) || null,
                            title: clean(titleLink?.textContent),
                            url: href,
                            site: clean(row.querySelector('.sitebit.comhead')?.textContent).replace(/[()]/g, '') || (href ? new URL(href).hostname : ''),
                            points: clean(subtext?.querySelector('.score')?.textContent),
                            age: clean(subtext?.querySelector('.age')?.textContent),
                            comments
                        };
                    })
                };
            }"""
        )

    async def _extract_github_trending(self) -> Any:
        return await self._evaluate(
            """() => {
                const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                return {
                    source: 'GitHub Trending',
                    url: window.location.href,
                    repositories: Array.from(document.querySelectorAll('article.Box-row')).slice(0, 10).map((row) => {
                        const link = row.querySelector('h2 a');
                        const href = link?.href || '';
                        const repo = clean(link?.textContent).replace(/\\s+/g, '');
                        const starsLink = Array.from(row.querySelectorAll('a')).find((item) => /stargazers/.test(item.href));
                        const forkLink = Array.from(row.querySelectorAll('a')).find((item) => /forks/.test(item.href));
                        const today = Array.from(row.querySelectorAll('span')).map((item) => clean(item.textContent)).find((text) => /stars today/i.test(text)) || '';
                        return {
                            name: repo,
                            url: href,
                            description: clean(row.querySelector('p')?.textContent),
                            language: clean(row.querySelector('[itemprop="programmingLanguage"]')?.textContent),
                            stars: clean(starsLink?.textContent),
                            forks: clean(forkLink?.textContent),
                            stars_today: today
                        };
                    })
                };
            }"""
        )

    async def _goto(self, url: str) -> None:
        await self.page.goto(url, wait_until="domcontentloaded", timeout=45000)

    async def _extract_wikipedia_python_summary(self) -> Any:
        return await self._evaluate(
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

    async def _extract_wikipedia_article_summary(self) -> Any:
        return await self._evaluate(
            """() => {
                const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const lead = Array.from(document.querySelectorAll('#mw-content-text .mw-parser-output > p'))
                    .map((paragraph) => clean(paragraph.textContent))
                    .find((text) => text.length > 80) || '';
                const rows = Array.from(document.querySelectorAll('table.infobox tr'));
                const infobox = {};
                for (const row of rows) {
                    const key = clean(row.querySelector('th')?.textContent);
                    const value = clean(row.querySelector('td')?.textContent);
                    if (key && value) infobox[key] = value;
                }
                const lookup = (label) => {
                    const key = Object.keys(infobox).find((item) => item.toLowerCase().includes(label));
                    return key ? infobox[key] : '';
                };
                return {
                    site: 'Wikipedia',
                    title: clean(document.querySelector('#firstHeading')?.textContent) || document.title,
                    url: window.location.href,
                    summary: lead,
                    birth_date: lookup('born'),
                    known_for: lookup('known for'),
                    infobox
                };
            }"""
        )

    async def _extract_mdn_web_api_overview(self) -> Any:
        return await self._evaluate(
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
        return await self._evaluate(
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

    async def _extract_httpbin_form_echo(self) -> Any:
        return await self._evaluate(
            """() => {
                const text = document.body?.innerText || '';
                try {
                    const payload = JSON.parse(text);
                    return {
                        site: 'httpbin',
                        url: window.location.href,
                        form: payload.form || {},
                        headers: payload.headers || {}
                    };
                } catch {
                    return {
                        site: 'httpbin',
                        url: window.location.href,
                        raw: text.slice(0, 2000)
                    };
                }
            }"""
        )

    async def _extract_page_summary(self) -> Any:
        return await self._evaluate(
            """() => {
                const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const paragraphs = Array.from(document.querySelectorAll('main p, article p, p'))
                    .map((paragraph) => clean(paragraph.textContent))
                    .filter((text) => text.length > 40)
                    .slice(0, 5);
                const headings = Array.from(document.querySelectorAll('h1, h2'))
                    .map((heading) => clean(heading.textContent))
                    .filter(Boolean)
                    .slice(0, 8);
                const links = Array.from(document.querySelectorAll('a[href]'))
                    .map((link) => ({ text: clean(link.textContent), href: link.href }))
                    .filter((link) => link.text)
                    .slice(0, 10);
                return {
                    page_title: document.title,
                    url: window.location.href,
                    heading: clean(document.querySelector('h1')?.textContent),
                    paragraphs,
                    headings,
                    links
                };
            }"""
        )

    async def screenshot(self, path: Path, label: str) -> None:
        # The label is stored by the runner; Playwright only needs the artifact path.
        path.parent.mkdir(parents=True, exist_ok=True)
        await self.page.screenshot(path=str(path), full_page=False)

    async def close(self) -> None:
        if self._released:
            return
        await self.browser.close()
        await self.playwright.stop()
        self._released = True

    async def keep_open(self) -> None:
        if self._released:
            return
        if self.external_process is None:
            await self.close()
            return
        # For CDP-launched visible browsers, stopping Playwright only detaches control.
        await self.playwright.stop()
        self._released = True


async def create_browser_session(settings: Settings) -> BrowserSession:
    playwright = None
    try:
        # Import lazily so the server can still start before Playwright is installed.
        from playwright.async_api import async_playwright

        playwright = await async_playwright().start()
        browser_type = playwright.chromium
        if not settings.browser_headless:
            return await _create_visible_browser_session(playwright, browser_type, settings)
        browser = await browser_type.launch(headless=settings.browser_headless)
        page = await browser.new_page(
            viewport={
                "width": settings.browser_viewport_width,
                "height": settings.browser_viewport_height,
            }
        )
        return PlaywrightBrowserSession(playwright, browser, page)
    except Exception as exc:
        if playwright:
            await playwright.stop()
        detail = str(exc) or exc.__class__.__name__
        raise RuntimeError(f"Could not launch Playwright browser: {detail}") from exc


async def _create_visible_browser_session(playwright: Any, browser_type: Any, settings: Settings) -> BrowserSession:
    port = _free_port()
    profile_dir = settings.artifacts_dir.parent / "browser-profiles" / f"profile_{uuid4().hex[:12]}"
    profile_dir.mkdir(parents=True, exist_ok=True)
    process = _launch_visible_chromium(browser_type.executable_path, profile_dir, port, settings)
    try:
        await _wait_for_cdp(port)
        browser = await browser_type.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        await page.set_viewport_size(
            {
                "width": settings.browser_viewport_width,
                "height": settings.browser_viewport_height,
            }
        )
        return PlaywrightBrowserSession(playwright, browser, page, external_process=process)
    except Exception:
        process.terminate()
        raise


def _launch_visible_chromium(executable_path: str, profile_dir: Path, port: int, settings: Settings) -> subprocess.Popen:
    command = [
        executable_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-crashed-bubble",
        f"--window-size={settings.browser_viewport_width},{settings.browser_viewport_height}",
        "about:blank",
    ]
    creationflags = 0
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP
    if hasattr(subprocess, "DETACHED_PROCESS"):
        creationflags |= subprocess.DETACHED_PROCESS
    return subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def _wait_for_cdp(port: int) -> None:
    url = f"http://127.0.0.1:{port}/json/version"
    deadline = time.time() + 10
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            await asyncio.to_thread(_read_json_url, url)
            return
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.2)
    raise RuntimeError(f"Visible Chromium did not expose CDP: {last_error}")


def _read_json_url(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=0.5) as response:
        return json.loads(response.read().decode("utf-8"))
