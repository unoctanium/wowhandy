"""Turn a transcript into a WoW chat line.

Spoken forms (case-insensitive; separators: space, ':', ',', '.'):

- ``<lead word> <channel word> <text>``
  "channel party pull boss" -> "/p pull boss", "Kanal Gruppe wir pullen" -> "/p wir pullen"
- ``<command lead word> [slash] <command> [arguments]``
  "command slash sit" or "command sit" -> "/sit", "command roll 100" -> "/roll 100"
- anything else: the text as it is (goes to the currently active chat channel)

Speech recognition often mishears the short control words ("Kanal Gilder",
"Guilt", "Kanal-Gülde"). With a fuzzy threshold, *only the control positions*
(lead word and channel word) are compared by similarity; the message itself is
never changed. A merely similar lead word counts only if a channel word follows,
so ordinary sentences stay untouched.
"""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

# First word and the rest. Separators: whitespace, colon, comma, period.
_FIRST_WORD = re.compile(r"\s*([^\s:,.]+)[\s:,.]+(.*)", re.DOTALL)
# Leftovers at the start of the message after a prefix ("channel raid - pull").
_LEADING_JUNK = " :,.-–—"
# WoW slash command name: ASCII, as WoW parses it (sit, dance, roll, readycheck, ...)
_COMMAND = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)(?:\s+(.*))?", re.DOTALL)
# Two candidates closer than this are ambiguous and are not guessed.
_AMBIGUITY_MARGIN = 0.05


class NotSendable(ValueError):
    """A lead word was recognized but the channel or command was not: send nothing."""


@dataclass(frozen=True)
class Grammar:
    """Everything the parser needs (built from the [prefixes] and [triggers] config)."""

    channel_words: frozenset[str]  # lead words for channels, e.g. channel, kanal
    command_words: frozenset[str]  # lead words for slash commands, e.g. command
    slash_words: frozenset[str]  # optional filler after the command lead word, e.g. slash
    triggers: dict[str, str]  # channel word -> chat command, e.g. gruppe -> /p
    fuzzy_threshold: float | None = None  # None = exact control words only
    fuzzy_commands: bool = False  # also tolerate a misheard command lead word


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def sanitize(text: str) -> str:
    """Remove control characters; line breaks and tabs become spaces."""
    text = re.sub(r"[\t\r\n]+", " ", text)
    text = "".join(ch for ch in text if ord(ch) >= 32 and ord(ch) != 127)
    return re.sub(r" {2,}", " ", text).strip()


def strip_trailing_period(text: str) -> str:
    """Remove exactly one trailing period; an ellipsis stays."""
    if text.endswith(".") and not text.endswith(".."):
        return text[:-1].rstrip()
    return text


def split_first_word(text: str) -> tuple[str, str]:
    """(first word, rest)."""
    text = text.strip()
    match = _FIRST_WORD.fullmatch(text)
    if match:
        return match.group(1), match.group(2).strip().lstrip(_LEADING_JUNK).strip()
    return text.strip(_LEADING_JUNK), ""


def split_hyphen(head: str, rest: str) -> tuple[str, str]:
    """"Kanal-Gilde, ..." -> ("Kanal", "Gilde, ...") so control words can be found."""
    parts = re.split(r"[-–]", head, maxsplit=1)
    if len(parts) == 2 and parts[0] and parts[1]:
        return parts[0], f"{parts[1]} {rest}".strip()
    return head, rest


def truncate(text: str, max_length: int) -> str:
    """Shorten to max_length, at a word boundary if possible."""
    if len(text) <= max_length:
        return text
    cut = text[:max_length]
    space = cut.rfind(" ")
    if space > max_length // 2:
        cut = cut[:space]
    return cut.rstrip()


# ---------------------------------------------------------------------------
# Matching control words
# ---------------------------------------------------------------------------


def _norm(word: str) -> str:
    """For similarity: lower case, simplified umlauts, letters and digits only."""
    word = word.casefold().replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")
    return "".join(ch for ch in word if ch.isalnum())


def similarity(a: str, b: str) -> float:
    """0.0 (unrelated) .. 1.0 (equal)."""
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def match_word(word: str, candidates: frozenset[str], threshold: float | None) -> str | None:
    """Exact candidate, otherwise (with a threshold) the most similar one."""
    if word.casefold() in candidates:
        return word.casefold()
    if threshold is None or not _norm(word) or not candidates:
        return None
    best = max(candidates, key=lambda c: similarity(word, c))
    return best if similarity(word, best) >= threshold else None


def match_trigger(word: str, triggers: dict[str, str], threshold: float | None) -> str | None:
    """Chat command for a channel word: exact, otherwise (with a threshold) fuzzy.

    Fuzzy only if unambiguous: if another channel word is almost as close and
    leads to a different command, nothing is guessed.
    """
    exact = triggers.get(word.casefold())
    if exact is not None or threshold is None or not _norm(word):
        return exact
    scored = sorted(((similarity(word, key), command) for key, command in triggers.items()), reverse=True)
    if not scored or scored[0][0] < threshold:
        return None
    best_score, best_command = scored[0]
    for score, command in scored[1:]:
        if score < best_score - _AMBIGUITY_MARGIN:
            break
        if command != best_command:
            return None
    return best_command


# ---------------------------------------------------------------------------
# Building the chat line
# ---------------------------------------------------------------------------


def build_command(rest: str, slash_words: frozenset[str]) -> str:
    """Text after the command lead word -> "/name arguments"."""
    head, tail = split_first_word(rest)
    if head.strip("!?.,:;").casefold() in slash_words:
        rest = tail
    # Recognizers sometimes write "/sit" themselves and add punctuation at the end.
    rest = rest.lstrip("/ ").rstrip(".!? ").strip()
    match = _COMMAND.fullmatch(rest)
    if not match:
        raise NotSendable(f"command not recognized: {rest!r}")
    name, arguments = match.groups()
    arguments = (arguments or "").strip()
    return "/" + name.lower() + (" " + arguments if arguments else "")


def _channel_line(command: str, body: str, strip_period: bool) -> str | None:
    if strip_period:
        body = strip_trailing_period(body)
    return f"{command} {body}" if body else None


def _split_glued_channel(head: str, rest: str, grammar: Grammar) -> tuple[str, str] | None:
    """Lead word and channel word written as one word ("Kanalgruppe").

    Only if the remainder is a (possibly fuzzy) channel word; otherwise it is an
    ordinary word ("Channelling", "Kanalarbeiter"). Returns (command, message).
    """
    lowered = head.casefold()
    for lead in grammar.channel_words:
        if lowered.startswith(lead) and len(lowered) > len(lead):
            command = match_trigger(head[len(lead):].lstrip("-–"), grammar.triggers, grammar.fuzzy_threshold)
            if command is not None:
                return command, rest
    return None


def build_message(transcript: str, grammar: Grammar, max_length: int = 255,
                  strip_period: bool = True) -> str | None:
    """The finished chat line, or None if nothing is left to send.

    Raises NotSendable if a lead word was clearly recognized but the channel or
    command after it was not – otherwise the message could end up in the wrong
    channel.
    """
    text = sanitize(transcript)
    threshold = grammar.fuzzy_threshold
    raw_head, raw_rest = split_first_word(text)
    head, rest = split_hyphen(raw_head, raw_rest)

    if raw_head.casefold() in grammar.command_words:
        line = build_command(raw_rest, grammar.slash_words)
    elif head.casefold() in grammar.command_words and grammar.fuzzy_commands:
        # "Command-Sit": hyphenated commands only with fuzzy_commands
        line = build_command(rest, grammar.slash_words)
    elif head.casefold() in grammar.channel_words:
        channel_word, body = split_first_word(rest)
        command = match_trigger(channel_word, grammar.triggers, threshold)
        if command is None:
            raise NotSendable(f"channel not recognized: {channel_word!r}")
        line = _channel_line(command, body, strip_period)
    else:
        line = _fuzzy_prefixed_line(head, rest, grammar, strip_period)
        if line is _NO_PREFIX:
            line = strip_trailing_period(text) if strip_period else text
    if not line:
        return None
    return truncate(line, max_length) or None


_NO_PREFIX = object()  # marker: no prefix found, send the text as it is


def _fuzzy_prefixed_line(head: str, rest: str, grammar: Grammar, strip_period: bool):
    """Glued or misheard prefixes. Returns the line, None (prefix without text) or _NO_PREFIX."""
    threshold = grammar.fuzzy_threshold
    glued = _split_glued_channel(head, rest, grammar)
    if glued:
        return _channel_line(*glued, strip_period)
    if threshold is None:
        return _NO_PREFIX
    if match_word(head, grammar.channel_words, threshold):
        channel_word, body = split_first_word(rest)
        command = match_trigger(channel_word, grammar.triggers, threshold)
        if command is not None:  # a merely similar lead word needs a channel word
            return _channel_line(command, body, strip_period)
        return _NO_PREFIX
    if grammar.fuzzy_commands:
        # "Kommand sit", also across two words: "Komm an, slash sit"
        next_word, after = split_first_word(rest)
        if match_word(head, grammar.command_words, threshold):
            return build_command(rest, grammar.slash_words)
        if next_word and match_word(head + next_word, grammar.command_words, threshold):
            return build_command(after, grammar.slash_words)
    return _NO_PREFIX
