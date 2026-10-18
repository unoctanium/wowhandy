import pytest

from wowhandy.config import load_config
from wowhandy.paste import PasteError, paste_line
from wowhandy.paste.linux import Backend, daemon_listening


class FakeBackend:
    def __init__(self, clipboard=b"previous", problems=(), fail_on=None):
        self.clipboard = clipboard
        self.problems = list(problems)
        self.fail_on = fail_on
        self.events = []

    def check(self):
        return self.problems

    def read_clipboard(self):
        return self.clipboard

    def write_clipboard(self, data):
        self.events.append(("clip", data))
        self.clipboard = data

    def press_enter(self):
        if self.fail_on == "enter":
            raise PasteError("enter failed")
        self.events.append("enter")

    def press_paste(self):
        self.events.append("paste")


def config(**chat):
    cfg = load_config(None)
    cfg.chat.chat_open_delay = cfg.chat.paste_delay = cfg.chat.clipboard_restore_delay = 0
    for key, value in chat.items():
        setattr(cfg.chat, key, value)
    return cfg


@pytest.mark.parametrize("leading, trailing, keys", [
    (True, True, ["enter", "paste", "enter"]),
    (False, True, ["paste", "enter"]),
    (True, False, ["enter", "paste"]),
    (False, False, ["paste"]),
])
def test_key_sequence(leading, trailing, keys):
    backend = FakeBackend()
    paste_line("/p Grüße", config(send_leading_enter=leading, send_trailing_enter=trailing), backend)
    assert backend.events[0] == ("clip", "/p Grüße".encode())
    assert [e for e in backend.events if isinstance(e, str)] == keys
    assert backend.events[-1] == ("clip", b"previous")  # restored


def test_clipboard_not_restored_if_changed_meanwhile():
    backend = FakeBackend()
    original_paste = backend.press_paste

    def paste_and_copy_elsewhere():
        original_paste()
        backend.clipboard = b"user copied something new"

    backend.press_paste = paste_and_copy_elsewhere
    paste_line("hi", config(), backend)
    assert backend.clipboard == b"user copied something new"


def test_problems_prevent_any_action():
    backend = FakeBackend(problems=["ydotoold not running"])
    with pytest.raises(PasteError, match="ydotoold"):
        paste_line("hi", config(), backend)
    assert backend.events == []


def test_failure_stops_before_final_enter():
    backend = FakeBackend(fail_on="enter")
    with pytest.raises(PasteError):
        paste_line("hi", config(), backend)
    assert "paste" not in backend.events


def test_stale_ydotool_socket_is_detected(tmp_path):
    import socket

    path = tmp_path / "stale.sock"
    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind(str(path))
    assert daemon_listening(path)
    server.close()
    assert path.is_socket() and not daemon_listening(path)


def test_linux_clipboard_setting_validated():
    from wowhandy.config import LinuxConfig

    with pytest.raises(ValueError):
        Backend(LinuxConfig(clipboard="pbcopy"))
