"""Command line.

Handy calls `wowhandy "<transcript>"` after every recording (paste method
"External Script"). Handy discards the script's output, so everything goes to a
log file. Any argument that is not one of the options below is treated as text
– a spoken word such as "check" must never turn into a command.

    wowhandy "<text>"                   build the chat line and paste it
    wowhandy --dry-run "<text>"         show the chat line, paste nothing
    wowhandy --check                    check config, tools and ydotoold
    wowhandy --init-config [--force]    write the commented default config
    wowhandy --show-default-config      print the default config (compare after updates)
    wowhandy --version | --help

Exit codes: 0 = pasted or nothing to do, 1 = not sent (reason in the log),
2 = configuration error.
"""

import logging
import os
import sys
from pathlib import Path

from wowhandy import __version__
from wowhandy.config import default_config_path, default_config_text, load_config
from wowhandy.message import NotSendable, build_message
from wowhandy.paste import PasteError, get_backend, paste_line

log = logging.getLogger("wowhandy")


def log_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Logs"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "wowhandy" / "wowhandy.log"


def setup_logging() -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


def load() -> tuple:
    """(config, path) – the built-in defaults if no config file exists."""
    path = default_config_path()
    return load_config(path if path.is_file() else None), path


def cmd_paste(text: str, dry_run: bool) -> int:
    try:
        config, path = load()
    except (OSError, ValueError) as exc:
        log.error("Invalid configuration %s: %s", default_config_path(), exc)
        return 2
    try:
        line = build_message(text, config.grammar(), config.chat.max_length, config.chat.strip_trailing_period)
    except NotSendable as exc:
        log.info("Not sent: %s", exc)
        if dry_run:
            print(f"not sent: {exc}")
        return 1
    if not line:
        log.info("Nothing to paste")
        if dry_run:
            print("nothing to paste")
        return 0
    if dry_run:
        print(line)
        return 0
    if config.chat.log_text:
        log.info("Text: %r -> %r", text, line)
    try:
        paste_line(line, config)
    except PasteError as exc:
        log.error("Paste failed, nothing sent: %s", exc)
        return 1
    log.info("Pasted")
    return 0


def cmd_check() -> int:
    path = default_config_path()
    print(f"config: {path} ({'found' if path.is_file() else 'not found – using defaults'})")
    try:
        config, _ = load()
    except (OSError, ValueError) as exc:
        print(f"  ✗ invalid configuration: {exc}")
        return 2
    try:
        problems = get_backend(config).check()
    except (PasteError, ValueError) as exc:
        problems = [str(exc)]
    for problem in problems:
        print(f"  ✗ {problem}")
    if not problems:
        print("  ✓ ready to paste")
    print(f"log: {log_path()}")
    return 1 if problems else 0


def cmd_init_config(force: bool) -> int:
    path = default_config_path()
    if path.exists() and not force:
        print(f"{path} already exists (use --init-config --force to overwrite)")
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(default_config_text(), encoding="utf-8")
    print(f"written: {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    first = argv[0] if argv else ""
    if first in ("--help", "-h") and len(argv) == 1:
        print(__doc__.strip())
        return 0
    if first == "--version" and len(argv) == 1:
        print(f"wowhandy {__version__}")
        return 0
    if first == "--init-config" and len(argv) <= 2 and argv[1:] in ([], ["--force"]):
        return cmd_init_config(force=len(argv) == 2)
    if first == "--show-default-config" and len(argv) == 1:
        print(default_config_text(), end="")
        return 0
    if first == "--check" and len(argv) == 1:
        setup_logging()
        return cmd_check()
    dry_run = first == "--dry-run" and len(argv) >= 2
    setup_logging()
    text = " ".join(argv[1:] if dry_run else argv)
    return cmd_paste(text, dry_run)


if __name__ == "__main__":
    sys.exit(main())
