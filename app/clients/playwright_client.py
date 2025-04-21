from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Dict, List, Any, Literal, Union, Optional
from playwright.async_api import async_playwright, Page, ElementHandle, Locator


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

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._console_logs = []
        self._network_requests = []

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

    async def start(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._browser_headless, slow_mo=self._slow_mo
        )
        self._context = await self._browser.new_context()
        if self._record_trace:
            await self._context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self._page = await self._context.new_page()

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

    async def stop(self):
        """Properly clean up all Playwright resources"""
        try:
            if self._record_trace and self._context:
                await self._context.tracing.stop(path=self._trace_path)
            
            # Close page first if it exists
            if self._page:
                await self._page.close()
                self._page = None
                
            # Close context if it exists
            if self._context:
                await self._context.close()
                self._context = None
                
            # Close browser if it exists
            if self._browser:
                await self._browser.close()
                self._browser = None
                
            # Stop Playwright if it exists
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
                
            # Clear collected data
            self._console_logs = []
            self._network_requests = []
        except Exception as e:
            print(f"Error during Playwright cleanup: {e}")
            # Continue with cleanup despite errors
    
    async def _get_css_selector(self, element: ElementHandle) -> str:
        return await element.evaluate("""
            (el) => {
                // Check if this is an element node
                if (el.nodeType !== Node.ELEMENT_NODE) {
                    return "[non-element-node]";
                }
                
                if (el.id) return `#${el.id}`;
                const path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let selector = el.nodeName.toLowerCase();
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/).join(".");
                        selector += "." + classes;
                    }
                    const siblingIndex = Array.from(el.parentNode?.children || []).indexOf(el) + 1;
                    selector += `:nth-child(${siblingIndex})`;
                    path.unshift(selector);
                    el = el.parentElement;
                }
                return path.join(" > ");
            }
        """)
    
    async def _summarize_element(
        self, 
        element: ElementHandle, 
        depth: int = 0, 
        visible_only: bool = True, 
        max_depth: int = 10, 
        max_children: int = 10
    ) -> Optional[Dict]:
        if depth > max_depth:
            return None

        if visible_only:
            is_visible = await element.is_visible()
            if not is_visible:
                return None

        # Check if element is a valid HTML element before using inner_text
        is_html_element = await element.evaluate("""
            (el) => {
                return el.nodeType === Node.ELEMENT_NODE;
            }
        """)
        
        tag = await element.evaluate("el => el.tagName ? el.tagName.toLowerCase() : el.nodeName.toLowerCase()")
        
        # Only get inner_text for HTML elements
        text = ""
        if is_html_element:
            try:
                text = await element.inner_text()
                text = text.strip()
                if len(text) > 80:
                    text = text[:77] + "..."
            except Exception:
                # Fallback to textContent if inner_text fails
                text_content = await element.evaluate("el => el.textContent || ''")
                text = text_content.strip()
                if len(text) > 80:
                    text = text[:77] + "..."
        
        attrs = await element.evaluate("""
            (el) => {
                if (el.nodeType !== Node.ELEMENT_NODE) return { id: '', class: '', type: undefined };
                return { id: el.id || '', class: el.className || '', type: el.type || undefined };
            }
        """)
        selector = await self._get_css_selector(element)

        summary = {
            "tag": tag,
            "text": text,
            "id": attrs.get("id"),
            "class": attrs.get("class"),
            "type": attrs.get("type"),
            "selector": selector,
            "children": []
        }

        children = await element.query_selector_all(":scope > *")
        for child in children[:max_children]:
            child_summary = await self._summarize_element(child, depth + 1, visible_only=visible_only, max_depth=max_depth, max_children=max_children)
            if child_summary:
                summary["children"].append(child_summary)

        return summary
    
    async def navigate_to_url(self, url: str):
        """Navigates to the specified URL"""
        await self._page.goto(url)
    
    async def explore_page_dom(
        self, 
        depth: int = 0, 
        visible_only: bool = True, 
        max_depth: int = 10, 
        max_children: int = 10
    ) -> Optional[Dict]:
        """Returns the HTML structure of the current page"""
        body = await self._page.query_selector("body")
        return await self._summarize_element(body, depth=depth, visible_only=visible_only, max_depth=max_depth, max_children=max_children)

    async def explore_element_dom(
        self, 
        selector: str, 
        depth: int = 0, 
        visible_only: bool = True, 
        max_depth: int = 10, 
        max_children: int = 10
    ) -> Optional[Dict]:
        """Returns the HTML structure of the element identified by the selector."""
        element = await self._page.query_selector(selector)
        return await self._summarize_element(element, depth=depth, visible_only=visible_only, max_depth=max_depth, max_children=max_children)

    async def wait_for_element(
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
        return await self._page.wait_for_selector(selector, timeout=timeout, state=state)

    async def find_elements(
        self, 
        selector: str,
        max_depth: int = 10,
        max_children: int = 10,
        visible_only: bool = True
    ) -> List[Dict]:
        """Finds elements on the page using the specified selector.

        Args:
            selector: CSS or XPath selector
            max_depth: Maximum depth of the element tree to explore
            max_children: Maximum number of children to explore per element
            visible_only: Whether to only include visible elements

        Returns:
            List of found elements
        """
        elements = await self._page.query_selector_all(selector)
        return [await self._summarize_element(element, max_depth=max_depth, max_children=max_children, visible_only=visible_only) for element in elements]

    async def click_on_element(self, selector: str, timeout: int = 30000):
        """Clicks on an element identified by the selector.

        Args:
            selector: CSS or XPath selector
            timeout: Maximum time to wait for the element in milliseconds
        """
        await self._page.click(selector, timeout=timeout)

    async def get_element_text_content(self, selector: str, timeout: int = 30000) -> str:
        """Gets the text content of an element.

        Args:
            selector: CSS or XPath selector
            timeout: Maximum time to wait for the element in milliseconds

        Returns:
            Text content of the element
        """
        element = await self._page.wait_for_selector(selector, timeout=timeout)
        return await element.text_content() if element else ""

    async def fill_input(self, selector: str, value: str, timeout: int = 30000):
        """Fills an input field with text.

        Args:
            selector: CSS or XPath selector
            value: Text to input
            timeout: Maximum time to wait for the element in milliseconds
        """
        await self._page.fill(selector, value, timeout=timeout)

    async def reload_page(self):
        """Reloads the current page."""
        await self._page.reload()

    async def execute_js(self, script: str, arg: Any = None):
        """Executes JavaScript code and returns the result.

        Args:
            script: JavaScript code to execute
            arg: Optional argument to pass to the script

        Returns:
            Result of the JavaScript execution
        """
        return await self._page.evaluate(script, arg)

    async def get_console_logs(
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

    async def get_network_requests(
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

    async def press_key(self, key: str):
        """Sends a keyboard key press event to the page.
        
        Args:
            key: Key to press, such as 'Enter', 'a', 'ArrowLeft', etc.
               For modifier keys, use format like 'Control+c', 'Shift+ArrowRight', 'Alt+Enter'
        """
        if '+' in key:
            # Handle key combinations like 'Control+c' or 'Shift+ArrowRight'
            parts = key.split('+')
            modifier = parts[0]
            key_to_press = parts[1]
            await self._page.keyboard.press(key_to_press, modifiers=[modifier])
        else:
            # Handle single key press
            await self._page.keyboard.press(key)




# import asyncio
# import json

# async def example():
#     client = PlaywrightClient(browser_headless=False)
#     await client.start()
#     await client.navigate_to_url("https://docs.astral.sh/uv/")
#     page_dom = await client.explore_page_dom()
#     print(json.dumps(page_dom, indent=4))
#     await client.stop()

# asyncio.run(example())
    