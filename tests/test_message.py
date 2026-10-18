import pytest

from wowhandy.config import load_config
from wowhandy.message import (
    NotSendable, build_message, match_trigger, sanitize, similarity, split_first_word,
    strip_trailing_period, truncate,
)

CONFIG = load_config(None)
GRAMMAR = CONFIG.grammar()


def build(text, grammar=GRAMMAR, **kwargs):
    return build_message(text, grammar, **kwargs)


def grammar(**prefix_overrides):
    config = load_config(None)
    for key, value in prefix_overrides.items():
        setattr(config.prefixes, key, value)
    return config.grammar()


@pytest.mark.parametrize("transcript, expected", [
    ("channel party pull boss", "/p pull boss"),
    ("Channel Party, wir pullen gleich.", "/p wir pullen gleich"),
    ("Kanal Gruppe wir pullen gleich", "/p wir pullen gleich"),
    ("Kanal: Gilde, morgen Raid um acht.", "/g morgen Raid um acht"),
    ("Channel raid. Bitte alle auf Position.", "/raid Bitte alle auf Position"),
    ("CHANNEL GUILD hello", "/g hello"),
    ("Kanal Offizier wer hat Zeit?", "/o wer hat Zeit?"),
    ("channel alert Boss kommt!", "/rw Boss kommt!"),
    ("channel gilde hallo", "/g hallo"),  # languages may be mixed
    ("Kanalgruppe, wir pullen gleich.", "/p wir pullen gleich"),  # glued
    ("Kanal-Gilde, morgen Raid um acht.", "/g morgen Raid um acht"),  # hyphenated
])
def test_channel_prefix(transcript, expected):
    assert build(transcript) == expected


@pytest.mark.parametrize("transcript, expected", [
    ("Hallo zusammen.", "Hallo zusammen"),
    ("party pull boss", "party pull boss"),  # no lead word, no channel
    ("Gruppe ist voll", "Gruppe ist voll"),
    ("Sagen wir mal so.", "Sagen wir mal so"),
    ("Channelling ist wichtig", "Channelling ist wichtig"),
    ("Kanalarbeiter gesucht", "Kanalarbeiter gesucht"),
    ("Wir gehen in den Raid", "Wir gehen in den Raid"),
    ("Hm...", "Hm..."),
    ("Echt?", "Echt?"),
    ("Grüße aus Gütersloh.", "Grüße aus Gütersloh"),
])
def test_plain_text(transcript, expected):
    assert build(transcript) == expected


@pytest.mark.parametrize("transcript, expected", [
    ("command slash sit", "/sit"),
    ("command sit", "/sit"),
    ("Command, slash, sit.", "/sit"),
    ("Command: /sit.", "/sit"),
    ("Command /Dance!", "/dance"),
    ("command slash roll 100", "/roll 100"),
    ("command invite Thrall", "/invite Thrall"),
])
def test_commands(transcript, expected):
    assert build(transcript) == expected


@pytest.mark.parametrize("transcript", [
    "Channel J, Hilfe hier.", "channel j please help", "Kanal Schlachtzug morgen",
    "channel", "Command", "command slash", "command slash!", "command slash 123",
])
def test_lead_word_without_valid_target_sends_nothing(transcript):
    with pytest.raises(NotSendable):
        build(transcript)


@pytest.mark.parametrize("transcript", ["", "   ", ".", "channel party", "Kanal Gruppe."])
def test_nothing_to_send(transcript):
    assert build(transcript) is None


# --- fuzzy control words (measured on real recordings, see STATUS.md) ---

@pytest.mark.parametrize("transcript, expected", [
    ("Kanal-Gilder, Morgen-Rate-O-Macht", "/g Morgen-Rate-O-Macht"),
    ("Kanal schreihen, Hilfe hier.", "/y Hilfe hier"),
    ("Kanal gilt im Morgen-Rate um acht", "/g im Morgen-Rate um acht"),
    ("Kanal Rate, alle auf Position.", "/raid alle auf Position"),
    ("Canal Rate, Allow Position", "/raid Allow Position"),
    ("Kanal-Gülde Morgen-Rate umacht.", "/g Morgen-Rate umacht"),
    ("Kanalgilder, morgen Raid", "/g morgen Raid"),
    ("channel guilt, anyone up?", "/g anyone up?"),
])
def test_fuzzy_channels(transcript, expected):
    assert build(transcript) == expected


@pytest.mark.parametrize("transcript", [
    "General Guild, anyone up for a dungeon?",
    "Kann mal Schlachtzug morgen.",
    "Canal Street ist schön",
    "Come on, draw a 100.",
    "Komm an, sit!",
    "Command-Sit",
    "Party-Pull, Boss.",
])
def test_fuzzy_leaves_ordinary_text_alone(transcript):
    assert build(transcript) == strip_trailing_period(sanitize(transcript))


@pytest.mark.parametrize("transcript, expected", [
    ("Komm an, sit!", "/sit"),
    ("Kommand sit.", "/sit"),
    ("Command-Sit", "/sit"),
    ("Komm an, slash dance!", "/dance"),
    ("Come on, draw a 100.", "Come on, draw a 100"),
])
def test_fuzzy_commands_option(transcript, expected):
    assert build(transcript, grammar(fuzzy_commands=True)) == expected


def test_strict_mode():
    strict = grammar(fuzzy_threshold=0)
    with pytest.raises(NotSendable):
        build("Kanal schreihen, hallo", strict)
    assert build("Canal Rate, hallo", strict) == "Canal Rate, hallo"


def test_ambiguous_fuzzy_match_is_not_guessed():
    triggers = {"party": "/p", "parti": "/raid"}
    assert match_trigger("partx", triggers, 0.75) is None


def test_similarity_examples():
    assert similarity("Gilder", "gilde") > 0.75
    assert similarity("General", "channel") < 0.75


# --- helpers ---

def test_length_limit_includes_prefix():
    message = build("channel raid " + " ".join(["wort"] * 100))
    assert len(message) <= 255 and message.startswith("/raid wort") and message.endswith("wort")


def test_truncate_without_spaces():
    assert truncate("x" * 300, 255) == "x" * 255


def test_sanitize_and_split():
    assert sanitize("a\nb\tc\x07d\x7f  e") == "a b cd e"
    assert split_first_word("PARTY: Pull Boss") == ("PARTY", "Pull Boss")


def test_keep_period_when_disabled():
    assert build("Hallo.", strip_period=False) == "Hallo."
