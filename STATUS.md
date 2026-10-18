# STATUS – wowhandy

_Last update: 2026-10-18_

## Current state

**wowhandy 0.2.0 is released (2026-10-18)** – "one command" install.
PyPI https://pypi.org/project/wowhandy/0.2.0/ (wheel + sdist; author Odo
Maletzki, MIT) and GitHub release v0.2.0 with `wowhandy.pyz`, `install.sh`,
wheel, sdist. Release run 39160497195: build, pypi, github-release success.
Verified like a user in a throwaway HOME: the README curl one-liner installs
0.2.0 to `~/.local/bin/wowhandy`, creates the config, prints check + Handy
settings; `--update` → "Already up to date"; dry-run "Kanal Schlachtzug …" →
`/raid …`. CI green on Python 3.11–3.14 (includes an installer test). 105 tests.
Linux only. Repo: github.com/unoctanium/wowhandy (branch `main`, tags v0.1.0, v0.2.0).

What 0.2.0 added (research: `docs/research/install-ux.md`; pattern of uv, ruff,
poetry, yt-dlp):
- `install.sh` (POSIX sh, no sudo, refuses to overwrite a pipx/uv link).
- `wowhandy --update` (single file replaces itself atomically after checking
  the download runs; pipx/uv: prints their command), `--uninstall [--purge]`
  (`src/wowhandy/selfmanage.py`), `--show-default-config`.
- `--check` names the install command for the detected distribution and prints
  the Handy settings with the right script path.
- `schlachtzug = "/raid"` in the defaults.
- README: one command at the top with a "Not `pip install`" note.

**Tested by the user (0.1.0, 2026-10-18): works in KWrite and in WoW.**

**Next step (user):** switch the own install to 0.2.0. If installed with pipx:
`pipx uninstall wowhandy`, then the curl one-liner (or stay on pipx with
`pipx upgrade wowhandy`). Script path in Handy stays `~/.local/bin/wowhandy`.
The existing `~/.config/wowhandy/config.toml` is kept; add
`schlachtzug = "/raid"` by hand (compare with `--show-default-config`).
Then backlog (see below).

## What exists

- `src/wowhandy/message.py` – chat line: lead words + channel words (EN/DE),
  slash commands, fuzzy matching of control words only (difflib, threshold 0.75,
  ambiguity margin 0.05), hyphen/glued forms, NotSendable for a clear lead word
  with an unknown target, 255-character limit, trailing period.
- `src/wowhandy/config.py` – TOML (`tomllib`), sections `[chat]`, `[prefixes]`,
  `[linux]`, `[triggers]`; unknown keys are errors; without a file the shipped
  `default_config.toml` is used (single source of truth). Config path per
  platform, `$WOWHANDY_CONFIG` overrides.
- `src/wowhandy/paste/` – `base.py` (PasteError, PasteBackend protocol),
  `__init__.py` (`paste_line`: clipboard first, [Enter], Ctrl+V, [Enter],
  restore clipboard only if it still holds our line), `linux.py` (ydotool keys
  with daemon liveness check via the datagram socket; clipboard via xclip or
  wl-copy, `auto` = xclip when DISPLAY is set).
- `src/wowhandy/cli.py` – `wowhandy "<text>"`, `--dry-run`, `--check`,
  `--init-config [--force]`, `--version`, `--help`. Options only as the first
  argument and in their exact form; everything else is text. Logs to
  `~/.local/state/wowhandy/wowhandy.log`. Exit codes 0/1/2.
- `scripts/build_zipapp.py` – builds `dist/wowhandy.pyz` (13 KB, single
  executable file). Verified: dry-run, check, init-config from the zipapp.

## Verified facts

- Handy calls the external script with the transcript as the **first argument**,
  stdin/stdout/stderr set to null; Handy's own auto-submit Enter runs after the
  script if enabled (`~/Projects/Handy/src-tauri/src/clipboard.rs`).
- User test with the predecessor (woxation's `woxation-handy-paste`, same logic):
  chat closed + leading Enter → chat opens, text arrives, is sent ✅.
  Qwen3-ASR and Parakeet TDT 0.6B v3 in Handy work well on the GPU without
  noticeable frame drops; Whisper in Handy translated German to English while
  translation was enabled.
- Fuzzy control words, measured on 48 recorded base-model transcripts (correct
  target channel/command/nothing): strict 31/48, fuzzy 34/48, fuzzy + commands
  41/48, 0 wrong targets in every variant.
- System of the user: CachyOS, KDE Plasma (Wayland), WoW Forever beta via
  Steam/Proton on XWayland, ydotool 1.0.4 with `ydotool.service` running,
  xclip installed, Python 3.14.

## Decisions

- Handy is the UI and recognizer; wowhandy is only the chat layer (2026-10-18).
- Standard library only; external tools per platform.
- Fuzzy matching on by default; **fuzzy commands stay off** (user, 2026-10-18:
  "works without it").
- Lead word with unknown target → send nothing.
- Everything in the repo in English.

## Relation to woxation

`~/Projects/woxation` is the standalone prototype (own recording, faster-whisper
with CUDA, hotkey via evdev, sounds, overlay, systemd service). It stays as an
independent variant. wowhandy replaces its `woxation-handy-paste` entry point.
When the user uses Handy daily, the woxation service must be disabled
(`systemctl --user disable --now woxation.service`) so both do not react to the
same key.

## Backlog

**High**
- Push-to-talk listener for a double tap → Escape (close the chat): needs a
  small own listener service that watches the push-to-talk key, forwards it to
  Handy and sends Escape on a double tap. Later (user, 2026-10-18).
- ~~Packaging~~ – done: PyPI + GitHub release v0.1.0 (2026-10-18), see "Current state".

**Medium**

**Low**
- macOS and Windows backends – **researched 2026-10-18**, see
  `docs/research/macos-windows.md`. Feasible with `ctypes` (no dependencies).
  Blockers outside our code: Handy's UI offers "External Script" only on Linux
  (the backend runs it everywhere); Windows needs a GUI-subsystem `.exe` (no
  console window stealing focus); macOS posting keys needs Accessibility for the
  child process (inheritance unclear); no suitable system Python on Windows/macOS
  → standalone binaries (PyInstaller in CI). Priority set to low by
  the user (2026-10-18); open questions: test hardware (Mac / Windows PC),
  draft a Handy Discussion post asking to show External Script on all platforms.
- Configurable key for opening the chat (games where it is not Enter).
- `--check` could also verify Handy's settings file (paste method, auto-submit).

## Open questions

- none
