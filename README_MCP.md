# Cafe Cursor MCP Server

This MCP (Model Context Protocol) server allows AI assistants to interact with the Cafe Cursor ordering system.

## Installation

```bash
pip install -r requirements.txt
```

## Running the MCP Server

The server uses stdio for communication, which is the standard way MCP servers work with AI assistants.

```bash
python mcp_server.py
```

## Environment Variables (Optional)

- `CAFE_CURSOR_DB_PATH`: Path to the SQLite database (default: `cafe_cursor.db` in the same directory as the script)

## Available Tools

### Customer Tools

1. **get_menu** - Get the current menu with all available items and their IDs
   - No parameters required

2. **place_order** - Place an order with specified menu items
   - Parameters:
     - `items`: Dictionary mapping menu item IDs to quantities (e.g., `{"1": 2, "3": 1}`)

3. **get_order_status** - Get the status of a specific order
   - Parameters:
     - `order_id`: The order ID to check (integer)

### Backend Tools

4. **list_orders** - List all orders with their status, timestamps, and items
   - No parameters required

5. **mark_order_ready** - Mark an order as ready for pickup
   - Parameters:
     - `order_id`: The order ID to mark as ready (integer)

6. **add_menu_item** - Add a new item to the menu
   - Parameters:
     - `item_id`: Unique ID for the menu item (integer)
     - `name`: Name of the menu item (string)

7. **remove_menu_item** - Remove an item from the menu
   - Parameters:
     - `item_id`: ID of the menu item to remove (integer)

## Available Resources

1. **cafe://menu** - The current menu with all available items
2. **cafe://orders** - List of all orders in the system

## Example Usage

### With Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "cafe-cursor": {
      "command": "python3",
      "args": ["/path/to/cafe_cursor/mcp_server.py"]
    }
  }
}
```

**Note:** The server automatically uses `cafe_cursor.db` in the same directory as the script. You can optionally override this with the `CAFE_CURSOR_DB_PATH` environment variable if needed.

### Example Tool Calls

**Get the menu:**
```json
{
  "tool": "get_menu"
}
```

**Place an order:**
```json
{
  "tool": "place_order",
  "arguments": {
    "items": {
      "1": 2,
      "3": 1
    }
  }
}
```

**Check order status:**
```json
{
  "tool": "get_order_status",
  "arguments": {
    "order_id": 1
  }
}
```

**List all orders:**
```json
{
  "tool": "list_orders"
}
```

**Mark order as ready:**
```json
{
  "tool": "mark_order_ready",
  "arguments": {
    "order_id": 1
  }
}
```

## Integration

The MCP server can be integrated with any MCP-compatible client, including:
- Claude Desktop
- Custom MCP clients
- AI assistants that support MCP

The server uses stdio for communication, making it compatible with standard MCP client implementations.

