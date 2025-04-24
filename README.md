# browser-mcp

## Overview

**browser-mcp** is an MCP server for browser automation, built on [Playwright](https://playwright.dev/), providing a robust set of tools for DOM exploration, interaction, and automation via the Model Context Protocol (MCP). It is designed for scriptable, reliable browser automation in both local and production environments.

## Features

- Navigate to URLs and explore the DOM structure
- Interact with elements (click, fill, wait, etc.)
- Execute JavaScript in the browser context
- Retrieve console logs and network requests
- Designed for robust, scriptable automation via MCP tools
- Easily extensible and production-ready (Docker support)

## Technology Stack

- **Python** 3.11+
- **Playwright** (browser automation)
- **MCP** (Model Context Protocol)
- **Dependency management:** [uv](https://github.com/astral-sh/uv)
- **Testing:** pytest, pytest-cov
- **Linting:** ruff
- **Type checking:** mypy

## Local Development Setup

1. **Install Python 3.11+** and [uv](https://github.com/astral-sh/uv)

2. **Install dependencies:**

    ```sh
    uv sync
    ```

3. **Install Playwright browsers:**

    ```sh
    playwright install --with-deps chromium
    ```

4. **Run the MCP server:**

   Use the following configuration in your MCP client:

   ```json
   {
     "mcpServers": {
       "browser": {
         "command": "uv",
         "args": [
           "--directory", "full/path/to/browser-mcp/app",
           "run",
           "main.py"
         ]
       }
     }
   }
   ```

## Production Setup (Docker)

- Use the provided Dockerfile or pull the prebuilt image:

  ```json
  {
    "mcpServers": {
      "browser-mcp": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "ghcr.io/l0kifs/browser-mcp:main"
        ]
      }
    }
  }
  ```

- Or build and run locally:

  ```sh
  docker build -t browser-mcp .
  docker run -i --rm browser-mcp
  ```

## Usage

The server exposes a set of MCP tools for browser automation, including:

- `restart_browser`: Restart the browser instance
- `navigate_to_url`: Navigate to a specific URL
- `explore_page_dom`: Retrieve a hierarchical representation of the page's DOM
- `explore_element_dom`: Explore a specific element's DOM subtree
- `wait_for_element`: Wait for an element to reach a specified state
- `find_elements`: Find all elements matching a selector
- `click_on_element`: Click on an element
- `get_element_text_content`: Get the text content of an element
- `fill_input`: Fill a form input field
- `reload_page`: Reload the current page
- `execute_js`: Execute JavaScript in the page context
- `get_console_logs`: Retrieve browser console logs
- `get_network_requests`: Retrieve network requests made by the page
- `press_key`: Simulate keyboard key press events

See the source code in `app/main.py` for full tool signatures and details.

## Best Practices & Troubleshooting

- **Follow the [Browser Automation Best Practices](docs/browser-usage-rules.md)** for robust and reliable automation.
- Tips include: thorough DOM exploration, robust selector strategies, error handling, and step-by-step verification.

## License

This project is licensed under the terms of the [MIT License](LICENSE).
