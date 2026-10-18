# Research: how CLI projects on PyPI present installation (2026-10-18)

Problem: PyPI shows `pip install wowhandy` at the top of every project page (not
configurable). On Arch/CachyOS and current Debian/Ubuntu/Fedora, `pip install`
into the system Python is refused (PEP 668, `EXTERNALLY-MANAGED`), so a
non-technical user following PyPI's line gets an error. How do others handle it?

Method: read the README (= PyPI project page) of 15 well-known command-line
tools via the PyPI JSON API and extract their install instructions.

## Patterns found

| Pattern | Projects | Example |
|---|---|---|
| **One-line standalone installer first**, package managers as alternatives | uv, ruff (Astral), poetry | `curl -LsSf https://astral.sh/uv/install.sh \| sh`; poetry: `install.python-poetry.org` script |
| **Standalone binaries from GitHub Releases first** | yt-dlp (main method; one file per OS), black (as alternative, PyInstaller builds) | `releases/latest/download/yt-dlp_linux` |
| **Self-update built in** | uv (`uv self update` when installed by the installer), yt-dlp (`yt-dlp -U`) | |
| **Bootstrap package** | aider | `python -m pip install aider-install` then `aider-install` (sets up an isolated environment) |
| **Install a tool manager, then the tool** | posting, harlequin | install uv via its curl installer, then `uv tool install posting` |
| **pipx / uv tool listed as alternatives** | ruff, uv, tldr, posting, harlequin | `pipx install ruff`, `uv tool install ruff` |
| **Plain `pip install` only** (older style, ignores PEP 668) | black, glances, thefuck, beets | `pip install black` |
| **Distribution packages listed** | tldr (`pacman -S tldr`), thefuck (`brew`, `apt`) | |
| **Points to a docs website** | httpie, poetry, streamlink | |

No project can remove PyPI's `pip install` line; the user-friendly ones put
their recommended method at the very top of the README, which PyPI shows right
below that line.

## Conclusion for wowhandy

The proposal matches the most user-friendly projects (Astral's uv/ruff, poetry,
yt-dlp):

1. One command at the top of the README:
   `curl -fsSL https://github.com/unoctanium/wowhandy/releases/latest/download/install.sh | sh`
   – downloads the single file to `~/.local/bin/wowhandy`, checks the
   requirements, creates the config, prints what to enter in Handy.
2. Built-in `wowhandy --update` and `wowhandy --uninstall` (like `yt-dlp -U`).
3. pipx / `uv tool install` and building from source as alternatives further
   down; both also end up at `~/.local/bin/wowhandy`.
4. A clear note: "Not `pip install` – use the command below."
5. Offer "download, inspect, then run" for users who do not want `curl | sh`.
