"""
Brand voice: presets, user rules and an enforcement pass that rewrites what
it safely can (term swaps, contractions, punctuation, emoji policy) and flags
what needs a human (banned words with no replacement, hype, long sentences).
"""
from __future__ import annotations

import re

from .text import split_sentences, words

HYPE_WORDS = [
    "game-changer", "game changer", "revolutionary", "revolutionize", "unlock", "unleash", "skyrocket",
    "synergy", "cutting-edge", "world-class", "best-in-class", "disrupt", "next-level", "supercharge",
    "seamless", "seamlessly", "leverage", "paradigm", "rockstar", "ninja", "guru", "delve", "elevate",
]

CONTRACTIONS = [
    (r"\bdo not\b", "don't"), (r"\bdoes not\b", "doesn't"), (r"\bdid not\b", "didn't"), (r"\bis not\b", "isn't"),
    (r"\bare not\b", "aren't"), (r"\bcannot\b", "can't"), (r"\bwill not\b", "won't"), (r"\bit is\b", "it's"),
    (r"\bthat is\b", "that's"), (r"\bwe are\b", "we're"), (r"\byou are\b", "you're"), (r"\bthey are\b", "they're"),
    (r"\bwe have\b", "we've"), (r"\byou will\b", "you'll"), (r"\bwe will\b", "we'll"), (r"\bthere is\b", "there's"),
]

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U0001F900-\U0001F9FF\u2B50\u2B06\u2194-\u21FF]",
)

PRESETS = {
    "expert": {
        "id": "expert",
        "label": "Expert and calm",
        "description": "Measured, specific, no hype. Reads like a senior practitioner.",
        "emoji": "none",
        "contractions": False,
        "exclamations": False,
        "bullet": "•",
        "max_sentence_words": 26,
        "target_flesch": 50,
    },
    "friendly": {
        "id": "friendly",
        "label": "Friendly and warm",
        "description": "Conversational and human. Contractions, light emoji, plain words.",
        "emoji": "light",
        "contractions": True,
        "exclamations": True,
        "bullet": "→",
        "max_sentence_words": 22,
        "target_flesch": 60,
    },
    "bold": {
        "id": "bold",
        "label": "Bold and direct",
        "description": "Short lines, strong verbs, gets to the point fast.",
        "emoji": "none",
        "contractions": True,
        "exclamations": False,
        "bullet": "▸",
        "max_sentence_words": 18,
        "target_flesch": 60,
    },
}

PLATFORM_EMOJI = {"linkedin": "📌", "instagram": "✨", "video": "🎬"}


def build_voice(raw: dict | None) -> dict:
    raw = raw or {}
    preset = PRESETS.get(raw.get("preset") or "expert", PRESETS["expert"])
    voice = dict(preset)

    def as_list(value):
        if isinstance(value, str):
            value = re.split(r"[,\n]", value)
        return [v.strip() for v in (value or []) if v and v.strip()]

    terms = []
    raw_terms = raw.get("preferred_terms") or []
    if isinstance(raw_terms, str):
        raw_terms = [ln for ln in raw_terms.split("\n") if ln.strip()]
    for item in raw_terms:
        if isinstance(item, dict):
            src, dst = item.get("from", ""), item.get("to", "")
        else:
            parts = re.split(r"\s*(?:->|→|=>|=|:)\s*", str(item), maxsplit=1)
            if len(parts) != 2:
                continue
            src, dst = parts
        if src.strip() and dst.strip():
            terms.append({"from": src.strip(), "to": dst.strip()})

    voice.update({
        "brand_name": (raw.get("brand_name") or "").strip(),
        "banned_words": as_list(raw.get("banned_words")),
        "preferred_terms": terms,
        "hashtags": [("#" + h.lstrip("#")) for h in re.split(r"[\s,]+", raw.get("hashtags") if isinstance(raw.get("hashtags"), str) else " ".join(raw.get("hashtags") or [])) if h.strip("#")][:3],
        "cta": (raw.get("cta") or "").strip(),
        "emoji": raw.get("emoji") or preset["emoji"],
        "avoid_hype": raw.get("avoid_hype", True) is not False,
    })
    if voice["emoji"] not in ("none", "light"):
        voice["emoji"] = preset["emoji"]
    return voice


def _match_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


URL_RE = re.compile(r"(https?://\S+|#\w+)")


def enforce(text: str, voice: dict, *, block_id: str = "", platform: str = "") -> tuple[str, list[dict]]:
    """Apply safe rewrites outside links and hashtags. Returns new text and a change log."""
    changes: list[dict] = []
    parts = URL_RE.split(text)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
        else:
            new, log = _enforce_plain(part, voice, block_id, platform)
            out.append(new)
            changes.extend(log)
    text = re.sub(r"[ ]+\n", "\n", "".join(out))
    return text, changes


def _enforce_plain(text: str, voice: dict, block_id: str, platform: str) -> tuple[str, list[dict]]:
    changes: list[dict] = []

    def log(rule, before, after):
        changes.append({"rule": rule, "before": before, "after": after, "block": block_id, "platform": platform})

    for term in voice["preferred_terms"]:
        pattern = re.compile(r"\b" + re.escape(term["from"]) + r"\b", flags=re.I)
        for m in list(pattern.finditer(text)):
            log("Preferred term", m.group(0), _match_case(m.group(0), term["to"]))
        text = pattern.sub(lambda m: _match_case(m.group(0), term["to"]), text)

    if voice["contractions"]:
        for pat, rep in CONTRACTIONS:
            rx = re.compile(pat, flags=re.I)
            for m in list(rx.finditer(text)):
                log("Contraction", m.group(0), _match_case(m.group(0), rep))
            text = rx.sub(lambda m, rep=rep: _match_case(m.group(0), rep), text)

    if not voice["exclamations"] and "!" in text:
        before = text
        text = re.sub(r"!+", ".", text)
        if before != text:
            log("No exclamation marks", "!", ".")

    if voice["emoji"] == "none":
        found = EMOJI_RE.findall(text)
        if found:
            text = EMOJI_RE.sub("", text)
            text = re.sub(r"[ ]{2,}", " ", text)
            log("No emoji", "".join(found), "")

    return text, changes


def check(text: str, voice: dict) -> list[dict]:
    """Issues a person should look at. Nothing here is auto-fixed."""
    issues = []
    lower = text.lower()
    for word in voice["banned_words"]:
        if re.search(r"\b" + re.escape(word.lower()) + r"\b", lower):
            issues.append({"type": "banned", "severity": "high", "message": f"Uses a banned word: “{word}”."})
    if voice["avoid_hype"]:
        for word in HYPE_WORDS:
            if re.search(r"\b" + re.escape(word) + r"\b", lower):
                issues.append({"type": "hype", "severity": "medium", "message": f"Hype word: “{word}”. Say what it does instead."})
    for sentence in split_sentences(text.replace("\n", " ")):
        n = len(words(sentence))
        if n > voice["max_sentence_words"] + 6:
            issues.append({
                "type": "long",
                "severity": "low",
                "message": f"A {n}-word sentence runs long for this voice (aim for under {voice['max_sentence_words']}).",
                "excerpt": sentence[:80] + ("…" if len(sentence) > 80 else ""),
            })
    if voice["emoji"] == "light" and len(EMOJI_RE.findall(text)) > 2:
        issues.append({"type": "emoji", "severity": "low", "message": "More than two emoji. Keep it light."})
    return issues
