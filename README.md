# browser-mcp

Local setup:

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

General setup for production:

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
