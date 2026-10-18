# CLAUDE.md – working rules for wowhandy

wowhandy is the World of Warcraft chat layer for the Handy speech-to-text app:
Handy calls `wowhandy "<transcript>"` (paste method "External Script"); wowhandy
builds the chat line (channel prefixes, slash commands, fuzzy control words,
length limit) and pastes it (clipboard + Enter / Ctrl+V / Enter).

## Start of every session

- **Read `STATUS.md` completely before doing anything.** It holds the current
  state, decisions, open questions and next steps. Earlier chats are not
  available; only `STATUS.md` and this repo count.
- Keep `STATUS.md` up to date after every step and decision. It is a state, not
  a log: remove what is outdated.

## Changes to this file

- **Change CLAUDE.md only after explicit confirmation by the user.** Show the
  proposed change first.

## Language

- Everything in the repository is **English**: code, comments, docstrings,
  README, STATUS.md, commit messages.
- Chat replies to the user: German (as in the woxation project), unless the
  user asks otherwise.

## Scope and design rules

- Only what the Handy integration needs. No audio, speech recognition, hotkeys,
  sounds or overlays here (those live in the separate `woxation` project).
- **No runtime dependencies** beyond the Python standard library (Python ≥ 3.11).
  External tools only per platform (Linux: ydotool, xclip / wl-copy).
- Platform-specific code only under `src/wowhandy/paste/` behind the
  `PasteBackend` interface, so macOS and Windows can be added later.
- Call external tools with argument lists, never through a shell; pass the text
  as data (stdin), never as an argument.
- Every spoken word must stay text: CLI options only when they are the first and
  only recognized option form (see `cli.py`).
- Before commands with side effects (`sudo`, `pacman`, `systemctl`, installing
  into the user's home) explain what they do.
- Work only inside `~/Projects/wowhandy/`; anything else only after asking.

## Git

- Local repo, branch `main`. Commit only when the user asks or agrees; no push
  without being asked.
