"""Linux backend: clipboard via xclip or wl-copy, keys via ydotool.

- Keys: `ydotool` talks to the `ydotoold` daemon, which injects keys through
  /dev/uinput. That works for X11, XWayland and Wayland windows alike.
- Clipboard: WoW runs under Proton/Wine on XWayland and reads the X11 clipboard,
  so `xclip` is the default when an X display exists; `wl-copy`/`wl-paste`
  serve native Wayland applications.
All tools are called with argument lists (never through a shell); the text is
passed as data on stdin, never as a command-line argument.
"""

import os
import shutil
import socket
import subprocess
from pathlib import Path

from wowhandy.config import LinuxConfig
from wowhandy.paste.base import PasteError

# Linux input event codes (linux/input-event-codes.h)
KEY_ENTER = 28
KEY_LEFTCTRL = 29
KEY_V = 47

_TEXT_TARGETS = {b"UTF8_STRING", b"STRING", b"TEXT", b"text/plain", b"text/plain;charset=utf-8"}


def ydotool_socket() -> Path:
    explicit = os.environ.get("YDOTOOL_SOCKET")
    if explicit:
        return Path(explicit)
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    return Path(runtime, ".ydotool_socket") if runtime else Path("/tmp/.ydotool_socket")


def daemon_listening(path: Path) -> bool:
    """Is ydotoold listening? (A stale socket file remains after the daemon stopped.)"""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        sock.connect(str(path))
        return True
    except OSError:
        return False
    finally:
        sock.close()


class Backend:
    def __init__(self, cfg: LinuxConfig):
        self.ydotool = shutil.which("ydotool")
        self.clipboard = self._choose_clipboard(cfg.clipboard)

    @staticmethod
    def _choose_clipboard(setting: str) -> str:
        if setting not in ("auto", "xclip", "wl-copy"):
            raise ValueError(f"[linux] clipboard must be auto, xclip or wl-copy, not {setting!r}")
        if setting == "auto":
            return "xclip" if os.environ.get("DISPLAY") and shutil.which("xclip") else "wl-copy"
        return setting

    # --- checks -----------------------------------------------------------

    def check(self) -> list[str]:
        problems = []
        if not self.ydotool:
            problems.append("ydotool not found (install the ydotool package)")
        socket_path = ydotool_socket()
        if not socket_path.is_socket() or not daemon_listening(socket_path):
            problems.append(f"ydotoold not running (no daemon at {socket_path}; "
                            "systemctl --user enable --now ydotool.service)")
        if self.clipboard == "xclip":
            if not shutil.which("xclip"):
                problems.append("xclip not found (install the xclip package)")
            if not os.environ.get("DISPLAY"):
                problems.append("DISPLAY not set: no X11 clipboard (use clipboard = \"wl-copy\")")
        elif not (shutil.which("wl-copy") and shutil.which("wl-paste")):
            problems.append("wl-copy/wl-paste not found (install the wl-clipboard package)")
        return problems

    # --- clipboard ----------------------------------------------------------

    def read_clipboard(self) -> bytes | None:
        try:
            if self.clipboard == "xclip":
                targets = subprocess.run(["xclip", "-selection", "clipboard", "-out", "-target", "TARGETS"],
                                         capture_output=True, timeout=3)
                if targets.returncode != 0 or not _TEXT_TARGETS & set(targets.stdout.split()):
                    return None
                result = subprocess.run(["xclip", "-selection", "clipboard", "-out"], capture_output=True, timeout=3)
            else:
                types = subprocess.run(["wl-paste", "--list-types"], capture_output=True, timeout=3)
                if types.returncode != 0 or b"text/plain" not in types.stdout:
                    return None
                result = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout if result.returncode == 0 else None

    def write_clipboard(self, data: bytes) -> None:
        if self.clipboard == "xclip":
            cmd = ["xclip", "-selection", "clipboard", "-in"]
        else:
            cmd = ["wl-copy", "--type", "text/plain;charset=utf-8"]
        # Both tools stay in the background to serve the selection. stdout/stderr
        # must not be pipes, or subprocess.run would wait until they exit.
        try:
            result = subprocess.run(cmd, input=data, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=3)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PasteError(f"{cmd[0]} failed: {exc}") from exc
        if result.returncode != 0:
            raise PasteError(f"{cmd[0]} could not set the clipboard (exit {result.returncode})")

    # --- keys -------------------------------------------------------------------

    def _keys(self, *events: str) -> None:
        result = subprocess.run([self.ydotool, "key", *events], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            raise PasteError(f"ydotool key failed (exit {result.returncode}): {result.stderr.strip()}")

    def press_enter(self) -> None:
        self._keys(f"{KEY_ENTER}:1", f"{KEY_ENTER}:0")

    def press_paste(self) -> None:
        self._keys(f"{KEY_LEFTCTRL}:1", f"{KEY_V}:1", f"{KEY_V}:0", f"{KEY_LEFTCTRL}:0")
