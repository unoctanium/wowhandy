#!/bin/sh
# wowhandy installer – puts the single-file program at ~/.local/bin/wowhandy.
#
#   curl -fsSL https://github.com/unoctanium/wowhandy/releases/latest/download/install.sh | sh
#
# No sudo, nothing outside ~/.local/bin and ~/.config/wowhandy is changed.
# Environment overrides (mainly for testing): WOWHANDY_BIN_DIR, WOWHANDY_URL.
set -eu

BIN_DIR="${WOWHANDY_BIN_DIR:-$HOME/.local/bin}"
URL="${WOWHANDY_URL:-https://github.com/unoctanium/wowhandy/releases/latest/download/wowhandy.pyz}"
TARGET="$BIN_DIR/wowhandy"

say() { printf '%s\n' "$*"; }
fail() { printf 'wowhandy installer: %s\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = "Linux" ] || fail "only Linux is supported for now."

# Python 3.11+ is the only requirement of the program itself.
command -v python3 >/dev/null 2>&1 || fail "python3 not found – install Python 3.11 or newer first."
python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' \
  || fail "Python 3.11 or newer is needed (found $(python3 --version 2>&1))."

# An existing pipx/uv install is a link into its own environment – do not overwrite it.
if [ -L "$TARGET" ]; then
  fail "$TARGET is managed by pipx or uv. Remove it first (pipx uninstall wowhandy / uv tool uninstall wowhandy)."
fi

mkdir -p "$BIN_DIR"
TMP="$(mktemp "$BIN_DIR/.wowhandy-install.XXXXXX")"
trap 'rm -f "$TMP"' EXIT

say "Downloading wowhandy …"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$URL" -o "$TMP" || fail "download failed: $URL"
elif command -v wget >/dev/null 2>&1; then
  wget -q "$URL" -O "$TMP" || fail "download failed: $URL"
else
  fail "neither curl nor wget found."
fi

VERSION="$(python3 "$TMP" --version 2>/dev/null)" || fail "the downloaded file does not run."
chmod 755 "$TMP"
mv -f "$TMP" "$TARGET"
trap - EXIT
say "Installed $VERSION → $TARGET"

# Config: create the commented default once, never overwrite an existing one.
"$TARGET" --init-config >/dev/null 2>&1 && say "Created your config: ~/.config/wowhandy/config.toml" \
  || say "Keeping your existing config."

say ""
"$TARGET" --check || true

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) say ""; say "Note: $BIN_DIR is not on your PATH. Handy uses the full path above, so this is fine;"
     say "to type 'wowhandy' in a terminal, add $BIN_DIR to your PATH." ;;
esac

say ""
say "Done. Update later with:   wowhandy --update"
say "Remove with:               wowhandy --uninstall"
