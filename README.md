# Cafe Cursor

A terminal-based ordering system for Cafe Cursor, featuring separate frontend (customer) and backend (staff) interfaces with SQLite persistence.

## Features

- 🛒 **Customer Ordering**: Browse menu, add items to cart, and place orders
- 👨‍🍳 **Staff Management**: View all orders, check status, and mark orders as ready
- 💾 **SQLite Persistence**: All orders persist across restarts
- 🌐 **Telnet Support**: Access via telnet for both frontend and backend
- ⏱️ **Timestamp Tracking**: Automatic tracking of order placement and ready times for analytics

## Installation

No external dependencies required! Uses only Python standard library.

```bash
# Clone or download the repository
cd cafe_cursor

# Make sure Python 3 is installed
python3 --version

# The app is ready to run!
```

## Running the App

### Local Console Mode

**Frontend (Customer Interface):**
```bash
python cafe_cursor.py
```

**Backend (Staff Interface):**
```bash
python cafe_cursor.py --backend
```

### TCP Server Mode

**Start Frontend Server (for customers):**
```bash
python cafe_cursor.py --serve --frontend-port 5555
```

**Start Backend Server (for staff):**
```bash
python cafe_cursor.py --serve-backend --backend-port 6000
```

**Connect via Telnet:**
```bash
# For customers
telnet localhost 5555

# For staff
telnet localhost 6000
```

### Advanced Options

```bash
# Custom database path
python cafe_cursor.py --db-path /path/to/cafe.db

# Custom frontend host/port
python cafe_cursor.py --serve --frontend-host 0.0.0.0 --frontend-port 8080

# Custom backend host/port (defaults to 127.0.0.1:6000 for security)
python cafe_cursor.py --serve-backend --backend-host 127.0.0.1 --backend-port 7000
```

## Available Modes

### 1. Frontend Mode (Customer)
- **Purpose**: For customers to browse menu and place orders
- **Access**: Default mode or `--serve` flag
- **Port**: 5555 (default)
- **Commands**: `menu`, `add`, `cart`, `order`, `status`, `help`, `exit`

### 2. Backend Mode (Staff)
- **Purpose**: For baristas to manage orders and mark them ready
- **Access**: `--backend` flag or `--serve-backend` flag
- **Port**: 6000 (default, bound to localhost for security)
- **Commands**: `list`, `status`, `ready`, `help`, `exit`

## Commands Reference

### Frontend Commands (Customer Interface)

#### `menu`
Display the full menu with item numbers.

**Example:**
```
cmd> menu

================================================
            CAFE CURSOR MENU
================================================
  1. Black (Hot)
  2. Black (Cold)
  3. White (Hot)
  4. White (Cold)
  5. Mocha (Hot)
  6. Mocha (Cold)
  7. Hot Chocolate
  8. Cold Chocolate
  9. Espresso Tonic
 10. Strawberry Latte
 11. Vanilla Latte
 12. Chocolate Cookies
 13. Strawberry Cookies
```

#### `add <item #> [quantity]`
Add items to your cart. Quantity defaults to 1 if not specified.

**Examples:**
```
cmd> add 1
Added 1 Black (Hot) to cart.

cmd> add 5 2
Added 2 Mocha (Hot)s to cart.
```

#### `cart`
View your current cart contents.

**Example:**
```
cmd> cart

--- Cart ---
Black (Hot) x1
Mocha (Hot) x2
------------
```

#### `order`
Place your current cart as an order. Returns an order ID.

**Example:**
```
cmd> order

================================================
ORDER CONFIRMED
Order ID: 42
Use `status 42` anytime to check progress.
We'll ping you when everything is ready!
================================================
```

#### `status <order id>`
Check the status of a specific order.
Note: Third part tools should query order status every 15-30 seconds. Ideal interval is 20 seconds.

**Example:**
```
cmd> status 42
42: Barista received your order.
```

**Possible statuses:**
- "Barista received your order." (placed < 2 minutes ago)
- "Drinks are being prepared." (placed 2-5 minutes ago)
- "Almost ready..." (placed > 5 minutes ago)
- "Ready for pickup!" (marked ready by staff)

#### `help` or `?`
Display available commands.

#### `exit` or `quit`
Exit the application.

---

### Backend Commands (Staff Interface)

#### `list`
Display all orders with their status, timestamps, and items.

**Example:**
```
bknd> list

Current Orders:
- #042 [PREP] placed 2024-01-15 14:30:00 ready -
    Black (Hot) x1, Mocha (Hot) x2
- #041 [READY] placed 2024-01-15 14:25:00 ready 2024-01-15 14:28:00
    Vanilla Latte x1
```

#### `status <order id>`
Show detailed information for a specific order.

**Example:**
```
bknd> status 42
Order 42: Barista received your order.
  Placed: 2024-01-15 14:30:00
  Ready:  -
  Items:  Black (Hot) x1, Mocha (Hot) x2
```

#### `ready <order id>`
Mark an order as ready for pickup. Records the ready timestamp.

**Example:**
```
bknd> ready 42
Order 42 marked ready at 2024-01-15 14:35:00.
```

#### `help` or `?`
Display available backend commands.

#### `exit` or `quit`
Exit the backend console.

---

## Menu Items

| # | Item |
|---|------|
| 1 | Black (Hot) |
| 2 | Black (Cold) |
| 3 | White (Hot) |
| 4 | White (Cold) |
| 5 | Mocha (Hot) |
| 6 | Mocha (Cold) |
| 7 | Hot Chocolate |
| 8 | Cold Chocolate |
| 9 | Espresso Tonic |
| 10 | Strawberry Latte |
| 11 | Vanilla Latte |
| 12 | Chocolate Cookies |
| 13 | Strawberry Cookies |

## Database

The app uses SQLite to persist all orders. By default, the database file is `cafe_cursor.db` in the current directory.

**Database Schema:**
- `orders` table with columns: `id`, `items` (JSON), `placed_at`, `ready_at`

**Note:** The database file is automatically created on first run and is excluded from git (see `.gitignore`).

## Example Workflow

### Customer Workflow
```bash
# 1. Start frontend server
python cafe_cursor.py --serve

# 2. Customer connects via telnet
telnet localhost 5555

# 3. Customer places order
cmd> menu
cmd> add 1
cmd> add 11 2
cmd> cart
cmd> order
# Returns: Order ID: 1

# 4. Customer checks status later
cmd> status 1
```

### Staff Workflow
```bash
# 1. Start backend server
python cafe_cursor.py --serve-backend

# 2. Staff connects via telnet
telnet localhost 6000

# 3. Staff views all orders
bknd> list

# 4. Staff marks order ready
bknd> ready 1
```

## Security Notes

- Backend server defaults to `127.0.0.1` (localhost only) for security
- Frontend server defaults to `0.0.0.0` (all interfaces) for accessibility
- Both servers share the same database, so orders are immediately visible across interfaces

## Development

The app is written in Python 3 using only standard library modules:
- `sqlite3` for database persistence
- `socketserver` for TCP server functionality
- `argparse` for command-line argument parsing
- `threading` for concurrent request handling

## License

This is a demo project for Cafe Cursor.

