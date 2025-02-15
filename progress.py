"""Utilities for progress messages."""

from types import TracebackType
from typing import Self


class Progress:
    """A utility that print a progress message and its confirmation."""

    def __init__(self, message: str) -> None:
        """Create a `Progress`."""
        self.message = message

    def __enter__(self) -> Self:
        """Print the message for a `Progress`."""
        print(f"{self.message}... ", end="", flush=True)
        return self

    def __exit__(self, exc: type[BaseException] | None, value: BaseException | None, tb: TracebackType | None) -> None:
        """Print the error that occurred during a `Progress` or print "OK"."""
        if exc:
            print("ERROR: ", end="", flush=True)
        else:
            print("OK", flush=True)
