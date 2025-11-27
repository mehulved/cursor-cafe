"""Tests for IO interfaces."""

import unittest
from unittest.mock import patch

from cafe_cursor.io import ConsoleIO


class TestIOInterfaces(unittest.TestCase):
    """Test IO interface classes."""

    def test_console_io_write(self):
        io = ConsoleIO()
        with patch("builtins.print") as mock_print:
            io.write("test message")
            mock_print.assert_called_once_with("test message")

    def test_console_io_readline(self):
        io = ConsoleIO()
        with patch("builtins.input", return_value="test input"):
            result = io.readline("prompt> ")
            self.assertEqual(result, "test input")

