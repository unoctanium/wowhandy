import subprocess
import sys
import zipapp
from pathlib import Path

import pytest

import wowhandy
from wowhandy import selfmanage
from wowhandy.paste.linux import distro_family


def build_pyz(tmp_path: Path, version: str) -> Path:
    """A minimal fake wowhandy single file that reports the given version."""
    src = tmp_path / f"src-{version}"
    (src / "fake").mkdir(parents=True)
    (src / "__main__.py").write_text(f"print('wowhandy {version}')\n")
    target = tmp_path / f"wowhandy-{version}.pyz"
    zipapp.create_archive(src, target, interpreter=sys.executable)
    return target


@pytest.fixture
def single_file(tmp_path, monkeypatch):
    installed = tmp_path / "bin" / "wowhandy"
    installed.parent.mkdir()
    installed.write_text("old")
    monkeypatch.setattr(selfmanage, "detect", lambda: selfmanage.Installation("single-file", installed))
    return installed


def test_update_replaces_the_file(tmp_path, single_file, capsys):
    new = build_pyz(tmp_path, "9.9.9")
    assert selfmanage.update(new.as_uri()) == 0
    assert "Updated" in capsys.readouterr().out
    assert subprocess.run([sys.executable, str(single_file)], capture_output=True, text=True).stdout.strip() == "wowhandy 9.9.9"
    assert not list(single_file.parent.glob(".wowhandy-update-*"))  # no leftovers


def test_update_same_version_keeps_file(tmp_path, single_file, capsys):
    same = build_pyz(tmp_path, wowhandy.__version__)
    assert selfmanage.update(same.as_uri()) == 0
    assert "Already up to date" in capsys.readouterr().out
    assert single_file.read_text() == "old"


def test_update_rejects_broken_download(tmp_path, single_file, capsys):
    broken = tmp_path / "broken.pyz"
    broken.write_text("not a zipapp")
    assert selfmanage.update(broken.as_uri()) == 1
    assert single_file.read_text() == "old"  # untouched


def test_update_for_pipx_only_prints_the_command(monkeypatch, capsys):
    monkeypatch.setattr(selfmanage, "detect", lambda: selfmanage.Installation("pipx", None))
    assert selfmanage.update("file:///nowhere") == 0
    assert "pipx upgrade wowhandy" in capsys.readouterr().out


def test_uninstall_keeps_config_unless_purge(single_file, isolated_dirs):
    config = isolated_dirs / "config" / "wowhandy"
    config.mkdir(parents=True)
    (config / "config.toml").write_text("")
    assert selfmanage.uninstall(purge=False) == 0
    assert not single_file.exists() and config.exists()
    single_file.write_text("again")
    assert selfmanage.uninstall(purge=True) == 0
    assert not single_file.exists() and not config.exists()


def test_detect_outside_zipapp_is_not_single_file():
    assert selfmanage.detect().kind != "single-file"


@pytest.mark.parametrize("os_release, family", [
    ('ID=cachyos\nID_LIKE="arch"\n', "arch"),
    ("ID=ubuntu\nID_LIKE=debian\n", "debian"),
    ('ID="fedora"\n', "fedora"),
    ('ID="opensuse-tumbleweed"\nID_LIKE="opensuse suse"\n', "suse"),
    ("ID=gentoo\n", ""),
])
def test_distro_family(os_release, family):
    assert distro_family(os_release) == family
