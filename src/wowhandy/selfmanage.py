"""How wowhandy was installed, and updating / uninstalling itself.

The recommended install is the single file `~/.local/bin/wowhandy` (a Python
zipapp) put there by install.sh. That file can replace or remove itself. Other
installs (pipx, uv tool, a development checkout) are managed by their own tools;
for those we only print the right command.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import wowhandy
from wowhandy.config import config_dir

RELEASE_URL = "https://github.com/unoctanium/wowhandy/releases/latest/download/wowhandy.pyz"


@dataclass(frozen=True)
class Installation:
    kind: str  # "single-file", "pipx", "uv", "other"
    executable: Path | None  # what Handy should run


def detect() -> Installation:
    archive = getattr(getattr(wowhandy, "__loader__", None), "archive", None)
    if archive:  # running from the zipapp
        return Installation("single-file", Path(archive).resolve())
    prefix = Path(sys.prefix).as_posix()
    command = shutil.which("wowhandy")
    executable = Path(command) if command else None
    if "/pipx/venvs/" in prefix:
        return Installation("pipx", executable)
    if "/uv/tools/" in prefix:
        return Installation("uv", executable)
    return Installation("other", executable)


def _download(url: str, target: Path) -> None:
    with urllib.request.urlopen(url, timeout=30) as response, open(target, "wb") as out:
        shutil.copyfileobj(response, out)


def _version_of(path: Path) -> str:
    result = subprocess.run([sys.executable, str(path), "--version"], capture_output=True, text=True, timeout=30)
    if result.returncode != 0 or not result.stdout.startswith("wowhandy "):
        raise RuntimeError("the downloaded file is not a working wowhandy")
    return result.stdout.split()[1]


def update(url: str | None = None) -> int:
    url = url or os.environ.get("WOWHANDY_URL", RELEASE_URL)  # override for testing
    install = detect()
    if install.kind == "pipx":
        print("Installed with pipx – update with:  pipx upgrade wowhandy")
        return 0
    if install.kind == "uv":
        print("Installed with uv – update with:  uv tool upgrade wowhandy")
        return 0
    if install.kind != "single-file":
        print("This copy is not a single-file install (development checkout?) – update it with git.")
        return 1
    target = install.executable
    # Download next to the target so the final rename is atomic (same file system).
    fd, tmp_name = tempfile.mkstemp(prefix=".wowhandy-update-", dir=target.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        print(f"Downloading {url} …")
        _download(url, tmp)
        new_version = _version_of(tmp)
        if new_version == wowhandy.__version__:
            print(f"Already up to date ({new_version}).")
            return 0
        tmp.chmod(0o755)
        os.replace(tmp, target)
        print(f"Updated {wowhandy.__version__} → {new_version}: {target}")
        print("Compare your config with the new defaults:  wowhandy --show-default-config")
        return 0
    except Exception as exc:  # network, permissions, broken download
        print(f"Update failed: {exc}")
        return 1
    finally:
        tmp.unlink(missing_ok=True)


def state_dir() -> Path:
    from wowhandy.cli import log_path

    return log_path().parent


def uninstall(purge: bool) -> int:
    install = detect()
    removed = []
    if purge:
        for folder in (config_dir(), state_dir()):
            if folder.exists():
                shutil.rmtree(folder)
                removed.append(str(folder))
    if install.kind == "single-file":
        install.executable.unlink(missing_ok=True)
        removed.append(str(install.executable))
    elif install.kind == "pipx":
        print("Installed with pipx – remove the program with:  pipx uninstall wowhandy")
    elif install.kind == "uv":
        print("Installed with uv – remove the program with:  uv tool uninstall wowhandy")
    else:
        print("Not a single-file install – remove it with the tool you installed it with.")
    for path in removed:
        print(f"removed: {path}")
    if not purge:
        print(f"Your config was kept ({config_dir()}); `--uninstall --purge` removes it too.")
    print("In Handy, set the paste method back to its default.")
    return 0
