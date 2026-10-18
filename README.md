# wowhandy

**Talk to your World of Warcraft chat.** wowhandy is a small add-on for the
[Handy](https://github.com/cjpais/Handy) speech-to-text app: Handy records and
transcribes, wowhandy turns what you said into a proper chat line and pastes it
into the game.

```
"Kanal Gruppe, wir pullen gleich."   ->  /p wir pullen gleich
"channel guild anyone up for a dungeon"  ->  /g anyone up for a dungeon
"command roll 100"                    ->  /roll 100
"Grüße aus Gütersloh"                 ->  Grüße aus Gütersloh   (active channel)
```

No game addon, no network, no Python packages – just the standard library and
two small system tools.

## Why wowhandy

Handy pastes text. Chatting in WoW needs a bit more:

- **Channels by voice.** Say a lead word and a channel: `channel party …`,
  `Kanal Gruppe …` → `/p …`. Works for party, raid, guild, officer, say, yell,
  instance, reply and raid warning – in **English and German** side by side.
- **Slash commands by voice.** `command sit`, `command slash dance`,
  `command roll 100` → `/sit`, `/dance`, `/roll 100`.
- **Forgiving control words.** Speech recognition often mishears short words
  like "Gilde" or "guild" ("Gilder", "Guilt", "Kanal-Gülde"). wowhandy compares
  *only the control words* by similarity, so `Canal Gilder …` still goes to
  `/g`, while ordinary sentences are never altered. Measured on 48 real
  recordings: more messages reach the right channel and **none** the wrong one.
- **Safe by default.** If you clearly said a lead word but the channel was not
  understood (`channel J …`), nothing is sent – instead of landing in the wrong
  channel.
- **Opens the chat for you.** An Enter *before* pasting opens the chat input
  (Handy can only press Enter *after*). Both are configurable.
- **Correct umlauts and punctuation on every keyboard layout** – the line is
  pasted via the clipboard, not typed key by key. Your previous clipboard text
  is restored afterwards.
- **WoW-ready text:** 255-character limit including the command, trailing
  period removed, control characters stripped.

## Requirements (Linux)

- [Handy](https://github.com/cjpais/Handy) with push-to-talk working on your desktop
- Python 3.11 or newer (only the standard library is used)
- `ydotool` with the `ydotoold` daemon running, for key presses
  (works on X11 and Wayland; your user must be allowed to use `/dev/uinput`,
  usually via the `input` group)
- `xclip` (WoW under Proton/Wine runs on XWayland and uses the X11 clipboard)
  or `wl-clipboard` for native Wayland applications

Arch / CachyOS:

```sh
sudo pacman -S ydotool xclip
systemctl --user enable --now ydotool.service
```

macOS and Windows are not supported yet; the code is prepared for them (see
`src/wowhandy/paste/`).

## Installation

Two ways to install – both give you the same program:

| | **A) Single file** (`wowhandy.pyz`) | **B) pipx from PyPI** (`wowhandy` command) |
|---|---|---|
| What you get | one executable file (~13 KB) containing everything | a `wowhandy` command in its own isolated environment |
| Needs | Python ≥ 3.11 | Python ≥ 3.11 and [pipx](https://pipx.pypa.io/) |
| Install | download one file | `pipx install wowhandy` |
| Update | download the new file over the old one | `pipx upgrade wowhandy` |
| Uninstall | delete one file | `pipx uninstall wowhandy` |
| Handy path | `~/.local/bin/wowhandy.pyz` | `~/.local/bin/wowhandy` |
| Good for | simplest setup, nothing installed, easy to copy to another machine | managed updates with one command |
| Downsides | you call it by its file name; updates are manual downloads | needs pipx |

### A) Single file

```sh
curl -fLo ~/.local/bin/wowhandy.pyz --create-dirs \
  https://github.com/unoctanium/wowhandy/releases/latest/download/wowhandy.pyz
chmod +x ~/.local/bin/wowhandy.pyz
```

- **Update:** run the same two commands again (Handy keeps using the same path).
- **Uninstall:** `rm ~/.local/bin/wowhandy.pyz`

### B) pipx from PyPI

```sh
pipx install wowhandy
```

- **Update:** `pipx upgrade wowhandy`
- **Uninstall:** `pipx uninstall wowhandy`

### From source (development version)

```sh
pipx install git+https://github.com/unoctanium/wowhandy        # as a command
# or build the single file yourself:
git clone https://github.com/unoctanium/wowhandy && cd wowhandy
python3 scripts/build_zipapp.py                                 # -> dist/wowhandy.pyz
```

### After installing

Check the setup and create your config file:

```sh
wowhandy --check          # config, ydotool, ydotoold, clipboard tool
wowhandy --init-config    # writes ~/.config/wowhandy/config.toml (commented)
```

With option A call `~/.local/bin/wowhandy.pyz` instead of `wowhandy`.

### Updates and your config file

Updating never touches `~/.config/wowhandy/config.toml`. New defaults (for
example new channel words) therefore do not appear in your file automatically –
your `[triggers]` list replaces the built-in one. Compare after an update:

```sh
wowhandy --show-default-config | diff ~/.config/wowhandy/config.toml -
```

…and copy over what you want, or start fresh with
`wowhandy --init-config --force` (overwrites your file).

### Removing everything

Uninstall as above, then delete the config and the log, and switch Handy's
paste method back to its default:

```sh
rm -r ~/.config/wowhandy ~/.local/state/wowhandy
```

## Configure Handy

In Handy's settings:

1. **Paste method:** `External Script`
2. **Script path:** the full path, e.g. `/home/you/.local/bin/wowhandy`
   (pipx) or `/home/you/.local/bin/wowhandy.pyz` (single file)
3. **Auto-submit (Enter after paste): off** – wowhandy presses Enter itself
   (`send_trailing_enter`). Otherwise Enter is pressed twice.
4. **Language:** `auto`, and **translate to English: off** – otherwise German
   speech comes out translated.
5. **Model:** one with automatic language detection if you mix languages.
   In our tests Qwen3-ASR and Parakeet TDT 0.6B v3 worked well on the GPU with
   no noticeable frame drops.
6. Optional – **custom words:** adding your lead and channel words
   (`Kanal, channel, Gruppe, party, Gilde, guild, Raid, Offizier, officer,
   command, slash`) helps the recognizer; wowhandy's fuzzy matching covers the
   rest.

In WoW the chat must open with **Enter** (default key binding).

## Configure wowhandy

The config file is `~/.config/wowhandy/config.toml` (or the path in
`$WOWHANDY_CONFIG`). Without a file, the shipped defaults apply; every value is
optional. The file is read on every call, so changes apply immediately.

### `[chat]`

| Option | Default | Meaning |
|---|---|---|
| `send_leading_enter` | `true` | Press Enter before pasting to open the chat. Set `false` if your chat input is already open when you speak (see below). |
| `send_trailing_enter` | `true` | Press Enter after pasting to send. Keep Handy's auto-submit off. |
| `max_length` | `255` | WoW's chat limit, including the channel command. |
| `strip_trailing_period` | `true` | Remove a single trailing period. |
| `chat_open_delay` | `0.10` | Seconds between the leading Enter and the paste. Increase if the first characters get lost. |
| `paste_delay` | `0.10` | Seconds between paste and the trailing Enter. |
| `restore_clipboard` | `true` | Put your previous clipboard text back afterwards. |
| `clipboard_restore_delay` | `0.30` | Wait before restoring (Proton reads the clipboard late). |
| `log_text` | `false` | Also write the recognized text to the log file. |

### `[prefixes]`

| Option | Default | Meaning |
|---|---|---|
| `channel_words` | `["channel", "kanal"]` | Lead words before a channel word. |
| `command_words` | `["command"]` | Lead words before a slash command. |
| `slash_words` | `["slash"]` | Optional filler after the command lead word. |
| `fuzzy_threshold` | `0.75` | Similarity (0–1) for misheard control words; `0` = exact only. |
| `fuzzy_commands` | `false` | Also accept a misheard command lead word ("Komm an sit" → `/sit`). More hits, slightly more risk. |

### `[triggers]`

Channel word → WoW command. The list in your file **replaces** the built-in
one. Add spellings your recognizer produces as extra keys:

```toml
[triggers]
party = "/p"
gruppe = "/p"
raid = "/raid"
rate = "/raid"   # mishearing of "Raid" in German sentences
schlachtzug = "/raid"
guild = "/g"
gilde = "/g"
# ...
```

### `[linux]`

| Option | Default | Meaning |
|---|---|---|
| `clipboard` | `"auto"` | `xclip` when an X display exists (WoW under Proton), else `wl-copy`. Force with `"xclip"` or `"wl-copy"`. |

## Test without the game

```sh
wowhandy --dry-run "Kanal Gruppe, wir pullen gleich."   # -> /p wir pullen gleich
wowhandy --dry-run "channel J please help"              # -> not sent: channel not recognized: 'J'
```

To test the full paste, focus a text editor, set `send_leading_enter = false`
and say something with Handy.

## Troubleshooting

- **Nothing happens:** run `wowhandy --check`, then look at the log:
  `~/.local/state/wowhandy/wowhandy.log` (Handy hides the script's output).
- **"ydotoold not running":** `systemctl --user enable --now ydotool.service`.
- **Chat opens and closes again / text lost:** your chat input was already
  open. Without WoW's gamepad mode the leading Enter then sends or closes the
  empty input. Set `send_leading_enter = false` and open the chat yourself, or
  make sure it is closed before you speak.
- **First characters missing:** increase `chat_open_delay` (e.g. `0.25`).
- **German speech comes out in English:** turn off Handy's translation.
- **Enter pressed twice:** turn off Handy's auto-submit.

## Exit codes

`0` pasted (or nothing to paste), `1` not sent (reason in the log), `2`
invalid configuration.

## Development

```sh
python3 -m venv .venv && .venv/bin/pip install -e '.[test]'
.venv/bin/pytest
```

Releases are built and published by GitHub Actions – see [RELEASING.md](https://github.com/unoctanium/wowhandy/blob/main/RELEASING.md).

Layout: `message.py` (chat line), `config.py` (settings), `paste/` (platform
backends: `base.py` interface, `linux.py`), `cli.py` (what Handy calls).

## Credits

wowhandy grew out of *woxation*, a standalone push-to-talk prototype, and was
inspired by [Decktation](https://github.com/silverfoxy/decktation) (MIT), which
brought dictation to WoW on the Steam Deck. Thanks to the
[Handy](https://github.com/cjpais/Handy) project for the external-script hook.

License: [MIT](https://github.com/unoctanium/wowhandy/blob/main/LICENSE).
