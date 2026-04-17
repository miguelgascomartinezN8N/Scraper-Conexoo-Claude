import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)

BLOCKED_TYPES = {"image", "font", "media", "stylesheet"}


class BrowserManager:
    def __init__(self):
        self._pw = None
        self._browser = None
        self._semaphore: Optional[threading.Semaphore] = None
        self._available = False

    def start(self, max_concurrent: int = 3) -> None:
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True)
            self._semaphore = threading.Semaphore(max_concurrent)
            self._available = True
            logger.info("Playwright browser initialized")
        except Exception as e:
            logger.warning(f"Playwright unavailable: {e}. Falling back to HTTP-only mode.")
            self._available = False

    def stop(self) -> None:
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")

    @property
    def available(self) -> bool:
        return self._available

    def get_html(self, url: str, timeout: int = 15) -> Optional[str]:
        if not self._available or not self._browser:
            return None

        def _block_resource(route):
            if route.request.resource_type in BLOCKED_TYPES:
                route.abort()
            else:
                route.continue_()

        with self._semaphore:
            page = self._browser.new_page()
            try:
                page.route("**/*", _block_resource)
                page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
                return page.content()
            except Exception as e:
                logger.warning(f"Playwright failed for {url}: {e}")
                return None
            finally:
                page.close()


browser_manager = BrowserManager()
