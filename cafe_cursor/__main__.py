"""Main entry point for Cafe Cursor."""

import argparse

from .backend import CafeBackendApp
from .frontend import CafeOrderApp
from .order_system import CafeOrderSystem
from .server import serve_backend_over_tcp, serve_frontend_over_tcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Cafe Cursor ordering app")
    parser.add_argument(
        "--serve",
        "--serve-frontend",
        action="store_true",
        dest="serve_frontend",
        help="Start the guest (frontend) TCP server",
        default=False,
    )
    parser.add_argument("--serve-backend", action="store_true", help="Start the staff/backend TCP server")
    parser.add_argument("--backend", action="store_true", help="Run the backend console locally")
    parser.add_argument("--frontend-host", default="0.0.0.0", help="Bind address for the frontend TCP server")
    parser.add_argument("--frontend-port", type=int, default=5555, help="Port for the frontend TCP server")
    parser.add_argument("--backend-host", default="127.0.0.1", help="Bind address for the backend TCP server")
    parser.add_argument("--backend-port", type=int, default=6000, help="Port for the backend TCP server")
    parser.add_argument("--db-path", default="cafe_cursor.db", help="SQLite database path")
    args = parser.parse_args()

    system = CafeOrderSystem(db_path=args.db_path)

    if args.serve_frontend and args.serve_backend:
        parser.error("Choose either --serve/--serve-frontend or --serve-backend per process.")

    if args.serve_frontend:
        serve_frontend_over_tcp(system, args.frontend_host, args.frontend_port)
    elif args.serve_backend:
        serve_backend_over_tcp(system, args.backend_host, args.backend_port)
    else:
        app_cls = CafeBackendApp if args.backend else CafeOrderApp
        app = app_cls(system=system)
        app.run()


if __name__ == "__main__":
    main()

