"""Shared types for the platform paste backends."""

from typing import Protocol


class PasteError(RuntimeError):
    """Pasting is not possible or failed; no final Enter is sent."""


class PasteBackend(Protocol):
    def check(self) -> list[str]:
        """Problems that prevent pasting (empty list = ready)."""

    def read_clipboard(self) -> bytes | None:
        """Current clipboard text, or None if there is none or it is not text."""

    def write_clipboard(self, data: bytes) -> None:
        """Replace the clipboard text; raises PasteError on failure."""

    def press_enter(self) -> None:
        """Press and release Enter; raises PasteError on failure."""

    def press_paste(self) -> None:
        """Press the paste shortcut (Ctrl+V; Cmd+V on macOS); raises PasteError on failure."""
