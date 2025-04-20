from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Literal, Any
from mcp.server.fastmcp import FastMCP, Context

from clients.playwright_client import PlaywrightClient


@dataclass
class AppContext:
    playwright_client: PlaywrightClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    playwright_client = PlaywrightClient(browser_headless=False)
    await playwright_client.start()
    try:
        yield AppContext(playwright_client=playwright_client)
    finally:
        # Cleanup on shutdown
        await playwright_client.stop()


mcp = FastMCP("Browser MCP", lifespan=app_lifespan)
# mcp = FastMCP("Browser MCP")


@mcp.tool()
async def navigate_to_url(ctx: Context, url: str) -> str:
    """Navigate to a specific URL in the browser.
    
    Used to load web pages for interaction or analysis.
    
    Args:
        url (str): The complete URL to navigate to, including protocol.
            Example: "https://www.example.com" or "https://github.com/search?q=playwright"
    
    Returns:
        str: A confirmation message that navigation was successful.
            Example: "Navigated to https://www.example.com"
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    await playwright_client.get_page().goto(url)
    return f"Navigated to {url}"


@mcp.tool()
async def explore_page_dom(ctx: Context) -> str:
    """Retrieve the complete HTML structure of the current page.
    
    Used for analyzing page structure, debugging, or extracting information not easily accessible 
    through selectors.
    
    Args:
        No arguments required.
    
    Returns:
        str: The full HTML content of the current page.
            Example: "<!DOCTYPE html><html><head>...</head><body>...</body></html>"
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    return await playwright_client.explore_page_dom()


@mcp.tool()
async def explore_element_dom(ctx: Context, selector: str) -> str:
    """Retrieve the HTML structure of a specific element on the page.
    
    Useful for examining a particular component or section of a page without the surrounding HTML.
    
    Args:
        selector (str): CSS or XPath selector identifying the element.
            Example: "#main-content", "//div[@class='header']", ".product-container"
    
    Returns:
        str: The inner HTML content of the selected element, or empty string if not found.
            Example: "<div class='item'>Product details</div><button>Add to cart</button>"
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    return await playwright_client.explore_element_dom(selector)


@mcp.tool()
async def wait_for_element(
    ctx: Context,
    selector: str,
    state: Literal["visible", "hidden", "attached", "detached"] = None,
    timeout: int = 30000
) -> bool:
    """Wait for an element to reach a specified state before proceeding.
    
    Useful for handling dynamic content that appears after page load, 
    or waiting for elements to be ready for interaction.
    
    Args:
        selector (str): CSS or XPath selector identifying the element.
            Example: "#login-button", "//table[@id='results']", ".notification"
        
        state (Literal["visible", "hidden", "attached", "detached"]): The state to wait for.
            - "visible": Wait for element to be visible (default if None)
            - "hidden": Wait for element to be hidden
            - "attached": Wait for element to be present in DOM
            - "detached": Wait for element to be removed from DOM
        
        timeout (int): Maximum time to wait in milliseconds before giving up.
            Default: 30000 (30 seconds).
            Example: 5000 (5 seconds), 60000 (1 minute)
    
    Returns:
        bool: True if the element reached the desired state within the timeout period, False otherwise.
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    element = await playwright_client.wait_for_element(selector, state, timeout)
    return element is not None


@mcp.tool()
async def find_elements(ctx: Context, selector: str) -> List[Dict]:
    """Find all elements on the page matching a selector and return their content.
    
    Useful for collecting multiple items, like products in a list, table rows, or menu items.
    
    Args:
        selector (str): CSS or XPath selector identifying the elements.
            Example: ".product-item", "//li[contains(@class, 'result')]", "ul.menu > li"
    
    Returns:
        List[Dict]: A list of dictionaries with the following keys for each found element:
            - "text": The text content of the element
            - "html": The inner HTML of the element
            
            Example: [
                {"text": "Product 1", "html": "<span>Product 1</span><span>$19.99</span>"},
                {"text": "Product 2", "html": "<span>Product 2</span><span>$24.99</span>"}
            ]
            Returns an empty list if no elements are found.
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    elements = await playwright_client.find_elements(selector)
    # Convert ElementHandles to serializable dictionaries
    result = []
    for el in elements:
        text = await el.text_content()
        html = await el.inner_html()
        result.append({"text": text, "html": html})
    return result


@mcp.tool()
async def click_on_element(ctx: Context, selector: str, timeout: int = 30000) -> bool:
    """Click on an element on the page.
    
    Used for interacting with buttons, links, checkboxes, radio buttons, 
    or any other clickable element.
    
    Args:
        selector (str): CSS or XPath selector identifying the element to click.
            Example: "#submit-button", "//button[contains(text(), 'Accept')]", ".menu-toggle"
        
        timeout (int): Maximum time to wait for the element in milliseconds before giving up.
            Default: 30000 (30 seconds).
            Example: 5000 (5 seconds), 60000 (1 minute)
    
    Returns:
        bool: True if the click was successful, False if it failed (element not found or other error).
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    try:
        await playwright_client.click_on_element(selector, timeout)
        return True
    except Exception as e:
        return False


@mcp.tool()
async def get_element_text_content(ctx: Context, selector: str, timeout: int = 30000) -> str:
    """Get the text content of a specific element on the page.
    
    Useful for extracting visible text from headings, paragraphs, labels, or any other elements.
    
    Args:
        selector (str): CSS or XPath selector identifying the element.
            Example: "h1.title", "//div[@id='price']", ".error-message"
        
        timeout (int): Maximum time to wait for the element in milliseconds before giving up.
            Default: 30000 (30 seconds).
            Example: 5000 (5 seconds), 60000 (1 minute)
    
    Returns:
        str: The text content of the element, or empty string if not found.
            Example: "Welcome to our website", "Error: Invalid credentials"
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    return await playwright_client.get_element_text_content(selector, timeout)


@mcp.tool()
async def fill_input(ctx: Context, selector: str, value: str, timeout: int = 30000) -> bool:
    """Fill a form input field with text.
    
    Used for entering text into input fields, textareas, or any editable element.
    This will replace any existing content in the field.
    
    Args:
        selector (str): CSS or XPath selector identifying the input element.
            Example: "#username", "//input[@name='email']", ".search-box"
        
        value (str): The text to enter into the input field.
            Example: "john.doe@example.com", "password123", "search term"
        
        timeout (int): Maximum time to wait for the element in milliseconds before giving up.
            Default: 30000 (30 seconds).
            Example: 5000 (5 seconds), 60000 (1 minute)
    
    Returns:
        bool: True if the input was successfully filled, False if it failed (element not found or other error).
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    try:
        await playwright_client.fill_input(selector, value, timeout)
        return True
    except Exception as e:
        return False


@mcp.tool()
async def execute_js(ctx: Context, script: str, arg: Any = None) -> Any:
    """Execute JavaScript code on the page and return the result.
    
    Used for advanced interactions, data extraction, or manipulations not possible with standard tools.
    
    Args:
        script (str): JavaScript code to execute in the page context.
            Example: "return document.title", 
                     "return Array.from(document.querySelectorAll('.price')).map(el => el.textContent)",
                     "return window.localStorage.getItem('token')"
        
        arg (Any, optional): Optional argument to pass to the script.
            This value will be serialized and can be accessed in the script as the first function parameter.
            Example: {"id": 123}, "search-term", 42
    
    Returns:
        Any: The return value from the JavaScript execution, serialized to Python types.
            - JavaScript objects become Python dictionaries
            - Arrays become lists
            - Numbers, strings, booleans are converted to their Python equivalents
            - null/undefined become None
            
            Example: "Page Title", ["$10.99", "$24.99"], {"userId": 123, "name": "John"}
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    return await playwright_client.execute_js(script, arg)


@mcp.tool()
async def get_console_logs(
    ctx: Context,
    limit: int = 50,
    offset: int = 0,
    time_from: datetime = None,
    time_to: datetime = None
) -> List[Dict]:
    """Retrieve browser console logs with filtering and pagination options.
    
    Useful for debugging JavaScript issues, monitoring API calls, or capturing application logs.
    
    Args:
        limit (int): Maximum number of log entries to return.
            Default: 50
            Example: 10, 100
        
        offset (int): Number of log entries to skip (for pagination).
            Default: 0
            Example: 50 (to get the second page when limit is 50)
        
        time_from (datetime, optional): Filter logs from this time onwards.
            Example: datetime(2023, 5, 10, 14, 30, 0)
        
        time_to (datetime, optional): Filter logs up to this time.
            Example: datetime(2023, 5, 10, 15, 0, 0)
    
    Returns:
        List[Dict]: A list of dictionaries representing console log entries, sorted newest first.
            Each dictionary has the following keys:
            - "type": The type of log (e.g., "log", "error", "warning")
            - "text": The log message text
            - "timestamp": When the log entry was created (UTC)
            - "location": Information about where the log originated (URL, line number)
            
            Example: [
                {
                    "type": "error",
                    "text": "Uncaught TypeError: Cannot read property 'length' of undefined",
                    "timestamp": "2023-05-10T14:35:23.123Z",
                    "location": {"url": "https://example.com/script.js", "lineNumber": 42}
                },
                {
                    "type": "log",
                    "text": "User logged in successfully",
                    "timestamp": "2023-05-10T14:35:20.456Z",
                    "location": {"url": "https://example.com/script.js", "lineNumber": 100}
                }
            ]
            Returns an empty list if no logs match the criteria.
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    return await playwright_client.get_console_logs(limit, offset, time_from, time_to)


@mcp.tool()
async def get_network_requests(
    ctx: Context,
    limit: int = 50,
    offset: int = 0,
    time_from: datetime = None,
    time_to: datetime = None,
    resource_type: str = None
) -> List[Dict]:
    """Retrieve network requests made by the page with filtering and pagination options.
    
    Used for monitoring API calls, tracking resource loading, debugging network issues,
    or analyzing the application's communication with servers.
    
    Args:
        limit (int): Maximum number of network requests to return.
            Default: 50
            Example: 10, 100
        
        offset (int): Number of requests to skip (for pagination).
            Default: 0
            Example: 50 (to get the second page when limit is 50)
        
        time_from (datetime, optional): Filter requests from this time onwards.
            Example: datetime(2023, 5, 10, 14, 30, 0)
        
        time_to (datetime, optional): Filter requests up to this time.
            Example: datetime(2023, 5, 10, 15, 0, 0)
        
        resource_type (str, optional): Filter by resource type.
            Possible values: "document", "stylesheet", "image", "media", "font", 
                            "script", "texttrack", "xhr", "fetch", "websocket", 
                            "manifest", "other"
            Example: "xhr", "image"
    
    Returns:
        List[Dict]: A list of dictionaries representing network requests, sorted newest first.
            Each dictionary has the following keys:
            - "url": The URL that was requested
            - "method": The HTTP method used (GET, POST, etc.)
            - "headers": The HTTP headers sent with the request
            - "timestamp": When the request was made (UTC)
            - "resourceType": The type of resource requested
            
            Example: [
                {
                    "url": "https://api.example.com/users/123",
                    "method": "GET",
                    "headers": {"Authorization": "Bearer token123", "Content-Type": "application/json"},
                    "timestamp": "2023-05-10T14:35:23.123Z",
                    "resourceType": "xhr"
                },
                {
                    "url": "https://example.com/images/logo.png",
                    "method": "GET",
                    "headers": {"Accept": "image/webp,image/png"},
                    "timestamp": "2023-05-10T14:35:20.456Z",
                    "resourceType": "image"
                }
            ]
            Returns an empty list if no requests match the criteria.
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    return await playwright_client.get_network_requests(
        limit, offset, time_from, time_to, resource_type
    )


@mcp.tool()
async def press_key(ctx: Context, key: str) -> bool:
    """Send a keyboard key press event to the current page.
    
    Used for simulating keyboard interactions like pressing Enter, arrow keys,
    or keyboard shortcuts such as Ctrl+C.
    
    Args:
        key (str): The key or key combination to press.
            For single keys: "Enter", "Tab", "a", "1", "ArrowLeft", "Escape", etc.
            For key combinations: "Control+c", "Shift+ArrowRight", "Alt+Enter", etc.
            
            Example: "Enter" (press Enter key)
                     "Control+a" (select all text)
                     "Escape" (press Escape key)
    
    Returns:
        bool: True if the key press was successful, False otherwise.
    """
    playwright_client = ctx.request_context.lifespan_context.playwright_client
    try:
        await playwright_client.press_key(key)
        return True
    except Exception as e:
        return False


if __name__ == "__main__":
    mcp.run()
