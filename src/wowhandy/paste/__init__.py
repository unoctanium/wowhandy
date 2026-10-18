"""Pasting a chat line into the focused game window.

The sequence is the same on every platform:

    put text on the clipboard -> [Enter] -> Ctrl+V -> [Enter] -> restore clipboard

Pasting instead of typing keeps umlauts and punctuation correct on any keyboard
layout. Only the clipboard and key backends differ per platform; each platform
module provides a `Backend` with the methods of `PasteBackend`.
"""

import logging
import sys
import time

from wowhandy.config import Config
from wowhandy.paste.base import PasteBackend, PasteError

__all__ = ["PasteBackend", "PasteError", "get_backend", "paste_line"]

log = logging.getLogger(__name__)


def get_backend(config: Config) -> PasteBackend:
    if sys.platform.startswith("linux"):
        from wowhandy.paste.linux import Backend

        return Backend(config.linux)
    raise PasteError(f"platform {sys.platform!r} is not supported yet (Linux only for now)")


def paste_line(line: str, config: Config, backend: PasteBackend | None = None) -> None:
    """Paste one chat line according to [chat]. Raises PasteError on failure."""
    chat = config.chat
    backend = backend or get_backend(config)
    problems = backend.check()
    if problems:
        raise PasteError("; ".join(problems))
    payload = line.encode("utf-8")
    previous = backend.read_clipboard() if chat.restore_clipboard else None
    # Clipboard first: if that fails, no key has been pressed yet.
    backend.write_clipboard(payload)
    try:
        if chat.send_leading_enter:
            backend.press_enter()
            time.sleep(chat.chat_open_delay)
        backend.press_paste()
        time.sleep(chat.paste_delay)
        if chat.send_trailing_enter:
            backend.press_enter()
    finally:
        if previous is not None:
            _restore(backend, previous, payload, chat.clipboard_restore_delay - chat.paste_delay)


def _restore(backend: PasteBackend, previous: bytes, payload: bytes, delay: float) -> None:
    """Put the previous text back – but only if the clipboard still holds our line."""
    time.sleep(max(0.0, delay))
    try:
        if backend.read_clipboard() == payload:
            backend.write_clipboard(previous)
    except PasteError as exc:
        log.warning("Clipboard not restored: %s", exc)
