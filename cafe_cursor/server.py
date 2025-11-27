"""TCP server for Cafe Cursor."""

import socketserver

from .backend import CafeBackendApp
from .frontend import CafeOrderApp
from .io import SocketIO
from .order_system import CafeOrderSystem


class ThreadedCafeServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def serve_app_over_tcp(
    app_cls, system: CafeOrderSystem, host: str, port: int, label: str
) -> None:
    """Start a telnet-friendly TCP server for the provided app."""

    class CafeRequestHandler(socketserver.BaseRequestHandler):
        def handle(self_inner) -> None:
            io = SocketIO(self_inner.request)
            app = app_cls(system=system, io=io)
            try:
                app.run()
            finally:
                io.close()

    with ThreadedCafeServer((host, port), CafeRequestHandler) as server:
        print(f"{label} listening on {host}:{port}")
        server.serve_forever()


def serve_frontend_over_tcp(system: CafeOrderSystem, host: str, port: int) -> None:
    serve_app_over_tcp(CafeOrderApp, system, host, port, "Cafe Cursor frontend server")


def serve_backend_over_tcp(system: CafeOrderSystem, host: str, port: int) -> None:
    serve_app_over_tcp(CafeBackendApp, system, host, port, "Cafe Cursor backend server")

