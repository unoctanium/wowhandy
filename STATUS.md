# STATUS – wowhandy

_Last update: 2026-10-18_

## Current state

Project created on 2026-10-18 at `~/Projects/wowhandy` (local git repo, branch
`main`). Version 0.1.0, Linux only, MIT license. 93 tests pass.

**Tested by the user (2026-10-18): works without problems in KWrite and in WoW**
(installed and configured by the user following the README).

Since that test (not yet in the user's installed copy):
- `schlachtzug = "/raid"` added to the defaults (template and built-in list).
  The user's existing `~/.config/wowhandy/config.toml` does not get it
  automatically (`[triggers]` replaces the defaults) – add the line by hand.
- `--show-default-config` to compare the config after updates.
- README: comparison of the two install options, update and uninstall
  instructions, "Removing everything".

**Next step:** user updates the installed copy and adds the Schlachtzug line;
then backlog (see below).

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
- Packaging – **prepared locally 2026-10-18, not yet published:** version only in
  `src/wowhandy/__init__.py` (pyproject reads it), project metadata/URLs for
  `github.com/unoctanium/wowhandy`, GitHub Actions `ci.yml` (tests on Python
  3.11–3.14 + single-file smoke test) and `release.yml` (tag `v*` → PyPI via
  trusted publishing + GitHub release with `wowhandy.pyz`; manual run →
  TestPyPI rehearsal), `RELEASING.md`, README install via PyPI / release file /
  source. Local check: sdist + wheel build, wheel contains template and LICENSE,
  no dependencies, installs and runs in a fresh venv. The name `wowhandy` was
  free on PyPI and TestPyPI (2026-10-18). **AUR dropped** (the user cannot
  register an AUR account at the moment). **GitHub repo created by the user and pushed (2026-10-18):**
  `github.com/unoctanium/wowhandy` (origin via SSH). The user's initial commit
  contained a LICENSE (MIT, "Copyright (c) 2026 Odo Maletzki"); merged, its
  LICENSE kept. First CI run: success on Python 3.11, 3.12, 3.13, 3.14.
  Environments and trusted publishers set up by the user. **TestPyPI rehearsal
  (2026-10-18, run 39157911387): build + testpypi success**; wowhandy 0.1.0
  (wheel + sdist) is on test.pypi.org and installs and runs from there (checked
  in a throwaway venv). **Next:** decide the author name in pyproject
  ("unoctanium" vs. "Odo Maletzki" as in LICENSE), then tag v0.1.0 → PyPI +
  GitHub release – only after the user's explicit go.

**Medium**
- GitHub repository (license: MIT, decided 2026-10-18).

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
