from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Dict, List, Any, Literal, Union, Optional
from playwright.sync_api import sync_playwright, Page, ElementHandle, Locator


class PlaywrightClient:
    def __init__(
        self,
        browser_headless: bool = True,
        slow_mo: float | None = None,
        record_trace: bool = False,
        trace_path: str | Path | None = None,
    ):
        self._browser_headless = browser_headless
        self._slow_mo = slow_mo
        self._record_trace = record_trace
        self._trace_path = trace_path if trace_path else self._set_default_trace_path()

        self._playwright = sync_playwright()
        self._browser = None
        self._context = None
        self._page = None
        self._console_logs = []
        self._network_requests = []

    def _install_dependencies_and_browser(self):
        result = subprocess.run(
            ["playwright", "install", "--with-deps", "chromium"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to install Playwright dependencies: {result.stderr}"
            )

    def _set_default_trace_path(self):
        current_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        return (
            Path(__file__).parent.parent.parent
            / "pw-traces"
            / f"trace_{current_timestamp}.zip"
        )

    def set_trace_path(self, trace_path: str | Path):
        self._trace_path = trace_path
        return self

    def get_page(self):
        return self._page

    def start(self):
        self._install_dependencies_and_browser()
        self._playwright = self._playwright.start()
        self._browser = self._playwright.chromium.launch(
            headless=self._browser_headless, slow_mo=self._slow_mo
        )
        self._context = self._browser.new_context()
        if self._record_trace:
            self._context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self._page = self._context.new_page()

        # Setup console log listener
        self._console_logs = []
        self._page.on(
            "console",
            lambda msg: self._console_logs.append(
                {
                    "type": msg.type,
                    "text": msg.text,
                    "timestamp": datetime.now(timezone.utc),
                    "location": msg.location,
                }
            ),
        )

        # Setup network request listener
        self._network_requests = []
        self._page.on(
            "request",
            lambda request: self._network_requests.append(
                {
                    "url": request.url,
                    "method": request.method,
                    "headers": request.headers,
                    "timestamp": datetime.now(timezone.utc),
                    "resourceType": request.resource_type,
                }
            ),
        )

    def stop(self):
        if self._record_trace:
            self._context.tracing.stop(path=self._trace_path)
        self._browser.close()
        self._playwright.stop()

    def explore_page_dom(self):
        """Returns the HTML structure of the current page"""
        return self._page.content()

    def explore_element_dom(self, selector: str):
        """Returns the HTML structure of the element identified by the selector."""
        element = self._page.query_selector(selector)
        return element.inner_html() if element else ""

    def wait_for_element(
        self,
        selector: str,
        state: Literal["visible", "hidden", "attached", "detached"] = None,
        timeout: int = 30000,
    ):
        """Waits for an element to be visible and interactable.

        Args:
            selector: CSS or XPath selector
            state: State of the element to wait for
            timeout: Maximum time to wait for the element in milliseconds

        Returns:
            ElementHandle of the found element
        """
        return self._page.wait_for_selector(selector, timeout=timeout, state=state)

    def find_elements(self, selector: str) -> List[ElementHandle]:
        """Finds elements on the page using the specified selector.

        Args:
            selector: CSS or XPath selector

        Returns:
            List of found elements
        """
        return self._page.query_selector_all(selector)

    def click_on_element(self, selector: str, timeout: int = 30000):
        """Clicks on an element identified by the selector.

        Args:
            selector: CSS or XPath selector
            timeout: Maximum time to wait for the element in milliseconds
        """
        self._page.click(selector, timeout=timeout)

    def get_element_text_content(self, selector: str, timeout: int = 30000) -> str:
        """Gets the text content of an element.

        Args:
            selector: CSS or XPath selector
            timeout: Maximum time to wait for the element in milliseconds

        Returns:
            Text content of the element
        """
        element = self._page.wait_for_selector(selector, timeout=timeout)
        return element.text_content() if element else ""

    def fill_input(self, selector: str, value: str, timeout: int = 30000):
        """Fills an input field with text.

        Args:
            selector: CSS or XPath selector
            value: Text to input
            timeout: Maximum time to wait for the element in milliseconds
        """
        self._page.fill(selector, value, timeout=timeout)

    def execute_js(self, script: str, arg: Any = None):
        """Executes JavaScript code and returns the result.

        Args:
            script: JavaScript code to execute
            arg: Optional argument to pass to the script

        Returns:
            Result of the JavaScript execution
        """
        return self._page.evaluate(script, arg)

    def get_console_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        time_from: datetime = None,
        time_to: datetime = None,
    ) -> List[Dict]:
        """Gets console logs with pagination and time filtering options.

        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            time_from: Filter logs from this time
            time_to: Filter logs until this time

        Returns:
            List of console log entries
        """
        filtered_logs = self._console_logs

        # Apply time filters if provided
        if time_from:
            filtered_logs = [
                log for log in filtered_logs if log["timestamp"] >= time_from
            ]
        if time_to:
            filtered_logs = [
                log for log in filtered_logs if log["timestamp"] <= time_to
            ]

        # Sort by timestamp (newest first)
        sorted_logs = sorted(filtered_logs, key=lambda x: x["timestamp"], reverse=True)

        # Apply pagination
        paginated_logs = sorted_logs[offset : offset + limit]

        return paginated_logs

    def get_network_requests(
        self,
        limit: int = 50,
        offset: int = 0,
        time_from: datetime = None,
        time_to: datetime = None,
        resource_type: str = None,
    ) -> List[Dict]:
        """Gets network requests with pagination, time filtering, and resource type options.

        Args:
            limit: Maximum number of requests to return
            offset: Number of requests to skip
            time_from: Filter requests from this time
            time_to: Filter requests until this time
            resource_type: Filter by resource type (e.g. 'document', 'stylesheet', 'image', etc.)

        Returns:
            List of network request entries
        """
        filtered_requests = self._network_requests

        # Apply time filters if provided
        if time_from:
            filtered_requests = [
                req for req in filtered_requests if req["timestamp"] >= time_from
            ]
        if time_to:
            filtered_requests = [
                req for req in filtered_requests if req["timestamp"] <= time_to
            ]

        # Apply resource type filter if provided
        if resource_type:
            filtered_requests = [
                req for req in filtered_requests if req["resourceType"] == resource_type
            ]

        # Sort by timestamp (newest first)
        sorted_requests = sorted(
            filtered_requests, key=lambda x: x["timestamp"], reverse=True
        )

        # Apply pagination
        paginated_requests = sorted_requests[offset : offset + limit]

        return paginated_requests
