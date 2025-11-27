"""IO interfaces for Cafe Cursor."""


class IOInterface:
    """Basic IO contract for CLI or socket-based sessions."""

    def write(self, message: str) -> None:  # pragma: no cover - simple wrapper
        raise NotImplementedError

    def readline(self, prompt: str = "") -> str:  # pragma: no cover - simple wrapper
        raise NotImplementedError


class ConsoleIO(IOInterface):
    """Console implementation using input/print."""

    def write(self, message: str) -> None:
        print(message)

    def readline(self, prompt: str = "") -> str:
        return input(prompt)


class SocketIO(IOInterface):
    """Socket implementation compatible with telnet clients."""

    def __init__(self, connection):
        self.connection = connection
        self.rfile = connection.makefile("rb")
        self.wfile = connection.makefile("wb")

    def write(self, message: str) -> None:
        if not message.endswith("\n"):
            message += "\n"
        data = message.replace("\n", "\r\n").encode("utf-8")
        self.wfile.write(data)
        self.wfile.flush()

    def readline(self, prompt: str = "") -> str:
        if prompt:
            self.write(prompt)
        line = self.rfile.readline()
        if not line:
            raise EOFError
        return line.decode("utf-8").rstrip("\r\n")

    def close(self) -> None:
        try:
            self.rfile.close()
            self.wfile.close()
        finally:
            self.connection.close()

