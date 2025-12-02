# Setting Up MCP Server in Cursor

This guide will help you configure the Cafe Cursor MCP server to work with Cursor IDE.

## Prerequisites

1. Install the MCP SDK:
```bash
pip install mcp
```

If that doesn't work, try:
```bash
pip install model-context-protocol
```

2. Verify the installation:
```bash
python3 -c "import mcp; print('MCP installed successfully')"
```

## Configuration Steps

### Option 1: Using mcp.json (Recommended)

1. **Locate Cursor's MCP configuration file:**
   - On macOS: `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
   - On Linux: `~/.config/Cursor/User/globalStorage/mcp.json`
   - On Windows: `%APPDATA%\Cursor\User\globalStorage\mcp.json`

2. **Add the Cafe Cursor server configuration:**
   
   Open the MCP configuration file and add this entry (or merge with existing `mcpServers`):

```json
{
  "mcpServers": {
    "cafe-cursor": {
      "command": "python3",
      "args": ["/Users/Admin/Projects/cafe_cursor/mcp_server.py"]
    }
  }
}
```

**Note:** The server automatically finds `cafe_cursor.db` in the same directory as the script, so no environment variables are needed!

**Important:** Replace `/Users/Admin/Projects/cafe_cursor/` with your actual project path.

3. **Restart Cursor** for the changes to take effect.

### Option 2: Using Cursor Settings UI

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Search for "MCP" or "Model Context Protocol"
3. Add a new MCP server with:
   - **Name:** `cafe-cursor`
   - **Command:** `python3`
   - **Args:** `/Users/Admin/Projects/cafe_cursor/mcp_server.py`
   - **Environment Variables:** (optional - server handles DB path automatically)

## Verifying the Setup

1. **Check MCP server status:**
   - Look for MCP indicators in Cursor's status bar
   - Check Cursor's developer console for MCP connection logs

2. **Test the connection:**
   - Try asking Cursor to "get the cafe menu" or "list all orders"
   - The AI should be able to use the MCP tools

## Troubleshooting

### Issue: MCP server not connecting

**Solution:**
- Verify Python path: `which python3`
- Check file permissions: `chmod +x mcp_server.py`
- Test the server manually:
  ```bash
  python3 mcp_server.py
  ```
  (It should start and wait for stdio input - this is normal)

### Issue: "Module not found: mcp"

**Solution:**
```bash
pip3 install mcp
# or
pip3 install model-context-protocol
```

### Issue: Database path errors

**Solution:**
- Use absolute paths in the configuration
- Ensure the database file exists or will be created
- Check file permissions on the database directory

### Issue: Import errors

**Solution:**
- Make sure you're in the project directory or Python can find the `cafe_cursor` package
- Try installing in development mode:
  ```bash
  pip3 install -e .
  ```

## Using the MCP Tools

Once configured, you can interact with Cafe Cursor through natural language:

- "What's on the menu?"
- "Place an order for 2 Black (Hot) coffees"
- "Check the status of order 1"
- "List all orders"
- "Mark order 1 as ready"
- "Add a new menu item with ID 14 called 'Iced Matcha'"

The AI assistant will automatically use the appropriate MCP tools to fulfill these requests.

## Configuration File Location

The `mcp.json` file in this repository is a template. You need to copy its contents to Cursor's actual MCP configuration file location (see Option 1 above).

