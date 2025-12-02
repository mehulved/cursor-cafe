#!/usr/bin/env python3
"""
MCP Server for Cafe Cursor

This server exposes Cafe Cursor functionality through the Model Context Protocol,
allowing AI assistants to interact with the cafe ordering system.
"""

import asyncio
import os
from typing import Any, Sequence

# MCP SDK imports - adjust based on your installed version
# Common package names: mcp, model-context-protocol, mcp-python
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError:
    try:
        # Alternative import path
        from mcp import Server
        from mcp.stdio import stdio_server
        from mcp import (
            Resource,
            Tool,
            TextContent,
            ImageContent,
            EmbeddedResource,
        )
    except ImportError:
        raise ImportError(
            "MCP SDK not found. Install it with: pip install mcp\n"
            "Or try: pip install model-context-protocol"
        )

from cafe_cursor import CafeOrderSystem, summarize_order_items


# Global system instance
_system: CafeOrderSystem | None = None


def get_system() -> CafeOrderSystem:
    """Get or create the Cafe Order System instance."""
    global _system
    if _system is None:
        # Default to cafe_cursor.db in the same directory as the script
        # Allow override via environment variable if needed
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_db_path = os.path.join(script_dir, "cafe_cursor.db")
        db_path = os.getenv("CAFE_CURSOR_DB_PATH", default_db_path)
        _system = CafeOrderSystem(db_path=db_path)
    return _system


# Create MCP server
app = Server("cafe-cursor")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for interacting with Cafe Cursor."""
    return [
        Tool(
            name="get_menu",
            description="Get the current menu with all available items and their IDs",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="place_order",
            description="Place an order with specified menu items. Provide a dictionary mapping item IDs to quantities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "object",
                        "description": "Dictionary mapping menu item IDs to quantities (e.g., {'1': 2, '3': 1})",
                        "additionalProperties": {"type": "integer"},
                    },
                },
                "required": ["items"],
            },
        ),
        Tool(
            name="get_order_status",
            description="Get the status of a specific order by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The order ID to check",
                    },
                },
                "required": ["order_id"],
            },
        ),
        Tool(
            name="list_orders",
            description="List all orders with their status, timestamps, and items (backend operation)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="mark_order_ready",
            description="Mark an order as ready for pickup (backend operation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The order ID to mark as ready",
                    },
                },
                "required": ["order_id"],
            },
        ),
        Tool(
            name="add_menu_item",
            description="Add a new item to the menu (backend operation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "integer",
                        "description": "Unique ID for the menu item",
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the menu item",
                    },
                },
                "required": ["item_id", "name"],
            },
        ),
        Tool(
            name="remove_menu_item",
            description="Remove an item from the menu (backend operation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "integer",
                        "description": "ID of the menu item to remove",
                    },
                },
                "required": ["item_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""
    system = get_system()
    
    if name == "get_menu":
        menu_items = system.menu.all_items()
        if not menu_items:
            return [TextContent(type="text", text="No menu items available.")]
        
        lines = ["Cafe Cursor Menu:\n"]
        for item in menu_items:
            lines.append(f"  {item.identifier:2d}. {item.name}")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "place_order":
        if not arguments or "items" not in arguments:
            return [TextContent(type="text", text="Error: 'items' parameter is required.")]
        
        items_dict = arguments["items"]
        # Convert string keys to integers if needed
        items = {int(k): int(v) for k, v in items_dict.items()}
        
        # Validate items exist in menu
        for item_id in items:
            if not system.menu.get_item(item_id):
                return [TextContent(
                    type="text",
                    text=f"Error: Menu item {item_id} does not exist."
                )]
        
        order = system.create_order(items)
        summary = summarize_order_items(system.menu, items)
        
        return [TextContent(
            type="text",
            text=f"Order placed successfully!\nOrder ID: {order.order_id}\nItems: {summary}\nStatus: {order.status()}"
        )]
    
    elif name == "get_order_status":
        if not arguments or "order_id" not in arguments:
            return [TextContent(type="text", text="Error: 'order_id' parameter is required.")]
        
        order_id = int(arguments["order_id"])
        order = system.get_order(order_id)
        
        if not order:
            return [TextContent(type="text", text=f"Order {order_id} not found.")]
        
        summary = summarize_order_items(system.menu, order.items)
        placed = order.placed_at.strftime("%Y-%m-%d %H:%M:%S")
        ready = order.ready_at.strftime("%Y-%m-%d %H:%M:%S") if order.ready_at else "Not ready yet"
        
        return [TextContent(
            type="text",
            text=f"Order {order_id}:\n"
                 f"  Status: {order.status()}\n"
                 f"  Placed: {placed}\n"
                 f"  Ready: {ready}\n"
                 f"  Items: {summary}"
        )]
    
    elif name == "list_orders":
        orders = system.list_orders()
        
        if not orders:
            return [TextContent(type="text", text="No orders found.")]
        
        lines = ["Current Orders:\n"]
        for order in orders:
            status = "READY" if order.ready_at else "PREP"
            placed = order.placed_at.strftime("%Y-%m-%d %H:%M:%S")
            ready = order.ready_at.strftime("%Y-%m-%d %H:%M:%S") if order.ready_at else "-"
            summary = summarize_order_items(system.menu, order.items)
            lines.append(f"  #{order.order_id} [{status}] placed {placed} ready {ready}")
            lines.append(f"    {summary}")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "mark_order_ready":
        if not arguments or "order_id" not in arguments:
            return [TextContent(type="text", text="Error: 'order_id' parameter is required.")]
        
        order_id = int(arguments["order_id"])
        order = system.mark_ready(order_id)
        
        if not order:
            return [TextContent(type="text", text=f"Order {order_id} not found.")]
        
        ready_at = order.ready_at.strftime("%Y-%m-%d %H:%M:%S") if order.ready_at else "unknown"
        return [TextContent(
            type="text",
            text=f"Order {order_id} marked as ready at {ready_at}."
        )]
    
    elif name == "add_menu_item":
        if not arguments or "item_id" not in arguments or "name" not in arguments:
            return [TextContent(type="text", text="Error: 'item_id' and 'name' parameters are required.")]
        
        item_id = int(arguments["item_id"])
        name = str(arguments["name"])
        
        success = system.add_menu_item(item_id, name)
        
        if success:
            return [TextContent(
                type="text",
                text=f"Menu item {item_id} '{name}' added successfully."
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to add menu item. Item ID {item_id} may already exist."
            )]
    
    elif name == "remove_menu_item":
        if not arguments or "item_id" not in arguments:
            return [TextContent(type="text", text="Error: 'item_id' parameter is required.")]
        
        item_id = int(arguments["item_id"])
        item = system.menu.get_item(item_id)
        
        if not item:
            return [TextContent(type="text", text=f"Menu item {item_id} not found.")]
        
        success = system.remove_menu_item(item_id)
        
        if success:
            return [TextContent(
                type="text",
                text=f"Menu item {item_id} '{item.name}' removed successfully."
            )]
        else:
            return [TextContent(type="text", text=f"Failed to remove menu item {item_id}.")]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="cafe://menu",
            name="Cafe Menu",
            description="The current menu with all available items",
            mimeType="text/plain",
        ),
        Resource(
            uri="cafe://orders",
            name="All Orders",
            description="List of all orders in the system",
            mimeType="text/plain",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource."""
    system = get_system()
    
    if uri == "cafe://menu":
        menu_items = system.menu.all_items()
        if not menu_items:
            return "No menu items available."
        
        lines = ["Cafe Cursor Menu:\n"]
        for item in menu_items:
            lines.append(f"  {item.identifier:2d}. {item.name}")
        return "\n".join(lines)
    
    elif uri == "cafe://orders":
        orders = system.list_orders()
        if not orders:
            return "No orders found."
        
        lines = ["Current Orders:\n"]
        for order in orders:
            status = "READY" if order.ready_at else "PREP"
            placed = order.placed_at.strftime("%Y-%m-%d %H:%M:%S")
            ready = order.ready_at.strftime("%Y-%m-%d %H:%M:%S") if order.ready_at else "-"
            summary = summarize_order_items(system.menu, order.items)
            lines.append(f"  #{order.order_id} [{status}] placed {placed} ready {ready}")
            lines.append(f"    {summary}")
        return "\n".join(lines)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())

