import pytest

from wowhandy.config import DEFAULT_TRIGGERS, Config, default_config_text, load_config, parse_config


def test_template_is_valid_and_contains_defaults():
    config = load_config(None)
    assert set(config.triggers) >= set(DEFAULT_TRIGGERS)
    assert config.chat.send_leading_enter and config.chat.send_trailing_enter
    assert config.prefixes.fuzzy_threshold == 0.75 and not config.prefixes.fuzzy_commands


def test_template_matches_dataclass_defaults():
    template = load_config(None)
    plain = Config()
    assert template.chat == plain.chat
    assert template.prefixes == plain.prefixes
    assert template.linux == plain.linux


def test_unknown_key_and_section_are_errors():
    with pytest.raises(ValueError, match="unknown setting"):
        parse_config("[chat]\nsend_enter = true\n")
    with pytest.raises(ValueError, match="unknown sections"):
        parse_config("[audio]\nx = 1\n")


def test_triggers_replace_defaults_and_are_normalized():
    config = parse_config('[triggers]\n"Party" = " /p "\n')
    assert config.grammar().triggers == {"party": "/p"}


def test_fuzzy_zero_means_off():
    config = parse_config("[prefixes]\nfuzzy_threshold = 0\n")
    assert config.grammar().fuzzy_threshold is None


def test_default_template_text_is_english_ascii_safe():
    text = default_config_text()
    assert "[triggers]" in text and "wowhandy --dry-run" in text
