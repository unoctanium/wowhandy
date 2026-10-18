from wowhandy import cli


def test_dry_run_prints_line(capsys):
    assert cli.main(["--dry-run", "Kanal", "Gruppe", "wir", "pullen", "gleich."]) == 0
    assert capsys.readouterr().out.strip() == "/p wir pullen gleich"


def test_dry_run_not_sendable(capsys):
    assert cli.main(["--dry-run", "Channel J Hilfe hier"]) == 1
    assert "channel not recognized" in capsys.readouterr().out


def test_spoken_option_words_are_text(monkeypatch):
    pasted = []
    monkeypatch.setattr(cli, "paste_line", lambda line, config: pasted.append(line))
    assert cli.main(["check"]) == 0
    assert cli.main(["--check", "this"]) == 0  # not alone -> text
    assert pasted == ["check", "--check this"]


def test_paste_error_returns_1(monkeypatch, isolated_dirs):
    def fail(line, config):
        raise cli.PasteError("ydotoold not running")

    monkeypatch.setattr(cli, "paste_line", fail)
    assert cli.main(["hallo"]) == 1
    assert "ydotoold not running" in (isolated_dirs / "state" / "wowhandy" / "wowhandy.log").read_text()


def test_invalid_config_returns_2(isolated_dirs):
    path = isolated_dirs / "config" / "wowhandy" / "config.toml"
    path.parent.mkdir(parents=True)
    path.write_text("[chat]\nsend_enter = true\n")
    assert cli.main(["hallo"]) == 2


def test_init_config(isolated_dirs, capsys):
    assert cli.main(["--init-config"]) == 0
    path = isolated_dirs / "config" / "wowhandy" / "config.toml"
    assert "[triggers]" in path.read_text()
    assert cli.main(["--init-config"]) == 1  # exists
    assert cli.main(["--init-config", "--force"]) == 0


def test_version(capsys):
    assert cli.main(["--version"]) == 0
    assert capsys.readouterr().out.startswith("wowhandy ")
