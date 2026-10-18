"""Configuration: built-in defaults, optionally overridden by a TOML file.

Location (first match): $WOWHANDY_CONFIG, then the platform config directory
(Linux: ~/.config/wowhandy/config.toml). Unknown keys are an error, so typos
do not go unnoticed.
"""

import os
import sys
import tomllib
from dataclasses import dataclass, field, fields
from importlib import resources
from pathlib import Path

from wowhandy.message import Grammar

# Channel word (after the lead word) -> WoW chat command. English and German work
# side by side; speak the channel word in the language of the sentence, because the
# recognizer picks one language per recording.
DEFAULT_TRIGGERS = {
    "party": "/p", "gruppe": "/p",
    "raid": "/raid", "schlachtzug": "/raid",
    "guild": "/g", "gilde": "/g",
    "officer": "/o", "offizier": "/o",
    "say": "/s", "sagen": "/s",
    "yell": "/y", "schreien": "/y",
    "instance": "/i", "instanz": "/i",
    "reply": "/r", "antwort": "/r",
    "alert": "/rw", "warnung": "/rw",
}


@dataclass
class ChatConfig:
    max_length: int = 255  # WoW chat limit, including the channel command
    strip_trailing_period: bool = True
    # Key sequence: [Enter] -> paste -> [Enter]. wowhandy never closes the chat.
    send_leading_enter: bool = True  # opens the chat; false if it is already open
    send_trailing_enter: bool = True  # sends the message; turn Handy's auto-submit off
    chat_open_delay: float = 0.10  # seconds between leading Enter and paste
    paste_delay: float = 0.10  # seconds between paste and trailing Enter
    restore_clipboard: bool = True  # put the previous clipboard text back
    clipboard_restore_delay: float = 0.30  # Proton/Wine reads the clipboard late
    log_text: bool = False  # write recognized text to the log file


@dataclass
class PrefixConfig:
    channel_words: list[str] = field(default_factory=lambda: ["channel", "kanal"])
    command_words: list[str] = field(default_factory=lambda: ["command"])
    slash_words: list[str] = field(default_factory=lambda: ["slash"])
    # Tolerate misheard control words (lead word and channel word only); 0 = off.
    fuzzy_threshold: float = 0.75
    # Also tolerate a misheard command lead word ("Komm an sit" -> /sit); riskier.
    fuzzy_commands: bool = False


@dataclass
class LinuxConfig:
    # Clipboard tool: "auto" (xclip if an X display is available, else wl-copy),
    # "xclip" (X11/XWayland – WoW under Proton) or "wl-copy" (native Wayland apps)
    clipboard: str = "auto"


@dataclass
class Config:
    chat: ChatConfig = field(default_factory=ChatConfig)
    prefixes: PrefixConfig = field(default_factory=PrefixConfig)
    linux: LinuxConfig = field(default_factory=LinuxConfig)
    triggers: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_TRIGGERS))

    def grammar(self) -> Grammar:
        def norm(words):
            return frozenset(w.strip().casefold() for w in words if w.strip())

        p = self.prefixes
        return Grammar(
            channel_words=norm(p.channel_words),
            command_words=norm(p.command_words),
            slash_words=norm(p.slash_words),
            triggers={k.strip().casefold(): v.strip() for k, v in self.triggers.items()},
            fuzzy_threshold=p.fuzzy_threshold if p.fuzzy_threshold > 0 else None,
            fuzzy_commands=p.fuzzy_commands,
        )


SECTIONS = ("chat", "prefixes", "linux")


def _apply(section, values: dict, name: str) -> None:
    known = {f.name for f in fields(section)}
    for key, value in values.items():
        if key not in known:
            raise ValueError(f"unknown setting [{name}] {key}")
        setattr(section, key, value)


def parse_config(text: str) -> Config:
    data = tomllib.loads(text)
    config = Config()
    for name in SECTIONS:
        _apply(getattr(config, name), data.pop(name, {}), name)
    if "triggers" in data:
        config.triggers = dict(data.pop("triggers"))  # replaces the defaults completely
    if data:
        raise ValueError(f"unknown sections: {', '.join(data)}")
    return config


def load_config(path: Path | None) -> Config:
    """Config from a file; without one, the shipped template (single source of truth)."""
    if path is None:
        return parse_config(default_config_text())
    return parse_config(path.read_text(encoding="utf-8"))


def config_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "wowhandy"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "wowhandy"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "wowhandy"


def default_config_path() -> Path:
    explicit = os.environ.get("WOWHANDY_CONFIG")
    return Path(explicit) if explicit else config_dir() / "config.toml"


def default_config_text() -> str:
    """The commented template that `wowhandy --init-config` writes."""
    return resources.files("wowhandy").joinpath("default_config.toml").read_text(encoding="utf-8")
