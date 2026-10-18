# Research: macOS and Windows support (2026-10-18)

Question: can wowhandy work as Handy's external paste script on macOS and Windows,
and what would the platform backends look like?

## 1. Handy side (checked in Handy's source, commit 9e57a0d)

- **The backend runs the external script on every platform.** In
  `src-tauri/src/clipboard.rs` the `PasteMethod::ExternalScript` arm and
  `paste_via_external_script()` have no `cfg(target_os)` gate:
  `Command::new(script_path).arg(text)` with stdin/stdout/stderr set to null.
- **The settings UI only offers it on Linux.** `src/components/settings/PasteMethod.tsx`:
  "External script is only available on Linux" (`if (osType === "linux")`).
- Consequences:
  - Workaround: set `"paste_method": "external_script"` and
    `"external_script_path"` by hand in Handy's `settings_store.json`. Unofficial;
    needs testing whether the UI keeps or resets the value.
  - Clean fix: a one-line change in Handy's UI to show the option on all
    platforms. Handy is in a feature freeze (see `~/Projects/Handy/CONTRIBUTING.md`);
    this would need a GitHub Discussion first, possibly framed as making the UI
    consistent with the backend.
- **Windows: no `CREATE_NO_WINDOW` for the script** (Handy sets it only for its
  engine supervisor). A console program started by Handy would open a console
  window – which can steal focus from the game and make the paste land in the
  console. → wowhandy must be a **GUI-subsystem executable** on Windows
  (`pythonw`, a `[project.gui-scripts]` launcher, or a windowed PyInstaller build).
- Windows argument passing: Rust quotes arguments correctly for `.exe` targets;
  `.bat`/`.cmd` wrappers go through `cmd.exe` quoting and are unsafe for
  arbitrary spoken text. → use an `.exe`, never a batch file.

## 2. Paste backends (standard library only, via `ctypes`)

### macOS

- Clipboard: `pbcopy` / `pbpaste` (built into macOS), or `NSPasteboard` via
  `ctypes`/Objective-C runtime.
- Keys: `CGEventCreateKeyboardEvent` + `CGEventPost` from the ApplicationServices
  framework via `ctypes` (Return = virtual key 36, V = 9, Command flag), or
  `osascript` with System Events (slower, needs Automation permission too).
- **Permissions (main risk):** posting keyboard events requires the
  Accessibility / PostEvent permission (TCC). Whether a child process started by
  Handy inherits Handy's grant is unclear: an Apple forum thread reports that a
  parent's grants were *not* inherited by a Python child
  ([thread 805245](https://developer.apple.com/forums/thread/805245)); posting
  events is a separate TCC service shown under "Accessibility"
  ([thread 820594](https://developer.apple.com/forums/thread/820594)); launch
  context matters ([thread 724603](https://developer.apple.com/forums/thread/724603)).
  Likely outcome: the user has to grant Accessibility to the wowhandy executable
  (or to the Python interpreter, which is too broad). A signed standalone binary
  would be the clean target.
- WoW on macOS is a native client; Enter opens the chat, Cmd+V pastes into edit
  boxes (to be verified in-game).

### Windows

- Clipboard: `OpenClipboard` / `EmptyClipboard` / `SetClipboardData(CF_UNICODETEXT)`
  / `GetClipboardData` via `ctypes` (user32/kernel32).
- Keys: `SendInput` with `VK_RETURN`, `VK_CONTROL` + `'V'` via `ctypes`. Injected
  input reaches WoW like real input (key-macro tools rely on that); to be
  verified.
- No extra permissions; UIPI only blocks injection into elevated windows (WoW
  normally does not run elevated).

## 3. Python availability

- Windows has no Python by default; the macOS system/CLT Python is 3.9 (wowhandy
  needs 3.11 for `tomllib`).
- Options:
  1. Require a recent Python (python.org / Homebrew) and install with pipx – easy
     for developers, not for players.
  2. **Ship standalone binaries** built with PyInstaller in GitHub Actions
     (Windows `wowhandy.exe` windowed, macOS universal binary). Still no runtime
     dependencies for the user; build-time tool only.
  3. Lower the requirement to 3.9 with a tiny TOML subset parser – more code to
     maintain; not recommended.

## 4. Testing

- Unit tests for clipboard/key code paths can run on GitHub Actions macOS and
  Windows runners (clipboard round trip; key sending only with mocks).
- Real verification needs a Mac and a Windows PC with Handy and WoW.

## Assessment

- **Feasible:** both backends fit the existing `PasteBackend` interface with
  `ctypes`, no Python dependencies.
- **Blockers outside our code:** Handy hides the option on macOS/Windows (UI);
  macOS permissions for the child process; packaging without a system Python.
- Suggested order: (1) ask in Handy's Discussions to show External Script on all
  platforms; (2) Windows backend + windowed PyInstaller build (fewer unknowns);
  (3) macOS backend once a test machine and the permission question are settled.
