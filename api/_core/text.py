"""
Text analysis: segmentation into traceable sentences, keyword and fact
extraction, readability. Pure Python, no external NLP dependencies.
"""
from __future__ import annotations

import re
from collections import Counter

STOPWORDS = set("""
a about above after again against all also am an and any are aren't as at be because been before being below between
both but by can can't cannot could couldn't did didn't do does doesn't doing don't down during each even every few for
from further get gets got had hadn't has hasn't have haven't having he her here hers herself him himself his how i if
in into is isn't it it's its itself just let's like made make makes many may me might more most much must my myself
need new no nor not now of off on once one only or other our ours ourselves out over own per really same say says she
should shouldn't so some such than that that's the their theirs them themselves then there there's these they this
those through to too under until up us use used using very via was wasn't way we we're were weren't what when where
which while who whom why will with within without won't would wouldn't yet you you're your yours yourself yourselves
across around back still well first two three four five six seven eight nine ten every each many much lot lots
also every than them they're it's here's what's don't
""".split())

ABBREVIATIONS = ("e.g.", "i.e.", "etc.", "vs.", "Dr.", "Mr.", "Mrs.", "Ms.", "Inc.", "Ltd.", "Co.", "No.", "approx.", "Rs.", "St.")

UNIT = (
    r"(?:\s?(?:%|percent\b|x\b|X\b|k\b|K\b|lakh\b|crore\b|million\b|billion\b|cr\b|"
    r"hours?\b|hrs?\b|days?\b|weeks?\b|months?\b|years?\b|minutes?\b|mins?\b))?"
)
NUMBER_RE = re.compile(r"(?:₹|\$|€|£|Rs\.?\s?|INR\s?|USD\s?)?\d(?:[\d,]*\d)?(?:\.\d+)?" + UNIT + r"(?:-[a-z]+)?")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’\-]*")
PROPER_RE = re.compile(r"\b([A-Z][a-zA-Z0-9&'’\-]+(?:\s+(?:of\s+|and\s+|&\s+|the\s+)?[A-Z][a-zA-Z0-9&'’\-]+)*)")

CONNECTORS = (
    "In addition, ", "Additionally, ", "Moreover, ", "Furthermore, ", "However, ", "Also, ", "So, ", "And ",
    "But ", "Plus, ", "On top of that, ", "As a result, ", "That said, ", "Meanwhile, ",
    "First, ", "Second, ", "Third, ", "Fourth, ", "Finally, ", "Lastly, ",
)


def clean_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\u00a0", " ").replace("\t", " ")
    text = re.sub(r"[ ]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _protect(text: str) -> str:
    for abbr in ABBREVIATIONS:
        text = text.replace(abbr, abbr.replace(".", "§"))
    return re.sub(r"(\d)\.(\d)", r"\1§\2", text)


def _restore(text: str) -> str:
    return text.replace("§", ".")


def split_sentences(paragraph: str) -> list[str]:
    protected = _protect(paragraph)
    parts = re.split(r"(?:(?<=[.!?])|(?<=[.!?][\"”’)]))\s+(?=[\"“(]?[A-Z0-9₹$€£])", protected)
    return [_restore(p).strip() for p in parts if p.strip()]


def segment(text: str) -> list[dict]:
    """Split source text into numbered segments (headings, bullets, sentences)."""
    text = clean_whitespace(text)
    segments: list[dict] = []
    para = 0
    for block in re.split(r"\n\s*\n", text):
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        para += 1
        buffer: list[str] = []

        def flush():
            if buffer:
                for sentence in split_sentences(" ".join(buffer)):
                    segments.append({"kind": "sentence", "text": sentence, "paragraph": para})
                buffer.clear()

        for idx, line in enumerate(lines):
            heading = re.match(r"^#{1,6}\s+(.*)$", line)
            bullet = re.match(r"^(?:[-*•▪◦]|\d+[.)])\s+(.*)$", line)
            if heading:
                flush()
                segments.append({"kind": "heading", "text": heading.group(1).strip(), "paragraph": para})
            elif bullet:
                flush()
                segments.append({"kind": "bullet", "text": bullet.group(1).strip(), "paragraph": para})
            elif idx == 0 and len(line) < 90 and not re.search(r"[.!?:,;\"”]$", line) and len(line.split()) <= 14:
                flush()
                segments.append({"kind": "heading", "text": line, "paragraph": para})
            else:
                buffer.append(line)
        flush()
    for i, seg in enumerate(segments, start=1):
        seg["id"] = f"S{i}"
    return segments


def words(text: str) -> list[str]:
    return [w.lower().strip("'’-") for w in WORD_RE.findall(text)]


def content_words(text: str) -> list[str]:
    return [w for w in words(text) if w not in STOPWORDS and len(w) > 2]


def number_core(token: str) -> str:
    """Just the digits of a number token, used to spot changed figures."""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", token)
    return m.group(0).replace(",", "") if m else ""


def find_numbers(text: str) -> list[str]:
    return [m.group(0).strip() for m in NUMBER_RE.finditer(text) if re.search(r"\d", m.group(0))]


CALENDAR_WORDS = {
    "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november",
    "december", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
}


def find_proper_nouns(text: str) -> list[str]:
    """Capitalised names that are not just the first word of a sentence."""
    nouns = []
    for m in PROPER_RE.finditer(text):
        phrase = m.group(1).strip()
        parts = phrase.split()
        lead_trimmed = False
        while parts and (parts[0].lower() in STOPWORDS or parts[0].lower() in CALENDAR_WORDS):
            parts.pop(0)
            lead_trimmed = True
        while parts and parts[-1].lower() in CALENDAR_WORDS:
            parts.pop()
        if not parts:
            continue
        if lead_trimmed and len(parts) == 1:
            continue
        phrase = " ".join(parts)
        before = text[: m.start(1)].rstrip()
        at_start = before == "" or before.endswith((".", "!", "?", ":", "\n", "•", "—", "-", "→", "▸", '"', "“"))
        if at_start and " " not in phrase:
            continue
        if phrase.lower() in STOPWORDS or len(phrase) < 2:
            continue
        nouns.append(phrase)
    return nouns


def keywords(segments: list[dict], title: str = "", limit: int = 12) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for seg in segments:
        weight = 2 if seg["kind"] == "heading" else 1
        for w in content_words(seg["text"]):
            counts[w] += weight
    for w in content_words(title):
        counts[w] += 3
    return [(w, c) for w, c in counts.most_common(limit * 2) if not w.isdigit()][:limit]


def syllables(word: str) -> int:
    word = word.lower()
    count = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e") and count > 1 and not word.endswith(("le", "ee")):
        count -= 1
    return max(count, 1)


def readability(text: str) -> dict:
    flat = re.sub(r"#\S+", "", text).replace("\n", " ")
    sentences = [s for s in split_sentences(flat) if words(s)]
    ws = words(flat)
    if not ws or not sentences:
        return {"flesch": None, "avg_sentence_words": 0, "label": "—"}
    syl = sum(syllables(w) for w in ws)
    asl = len(ws) / len(sentences)
    flesch = max(0.0, min(100.0, 206.835 - 1.015 * asl - 84.6 * (syl / len(ws))))
    label = (
        "Very easy" if flesch >= 80 else "Easy" if flesch >= 70 else "Plain" if flesch >= 60 else
        "Fairly hard" if flesch >= 50 else "Hard" if flesch >= 30 else "Very hard"
    )
    return {"flesch": round(flesch, 1), "avg_sentence_words": round(asl, 1), "label": label}


def trim_connector(sentence: str) -> str:
    for c in CONNECTORS:
        if sentence.startswith(c):
            rest = sentence[len(c):]
            return rest[:1].upper() + rest[1:]
    return sentence


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def ensure_period(sentence: str) -> str:
    s = sentence.rstrip()
    return s if re.search(r"[.!?…:\"”)]$", s) else s + "."


def figure_phrase(text: str, max_extra: int = 2) -> str:
    """A number plus the one or two words that follow it, e.g. '5 tone templates'."""
    m = NUMBER_RE.search(text)
    if not m:
        return ""
    phrase = m.group(0).strip()
    rest = text[m.end():]
    if phrase.endswith("%") or re.match(r"^[.,;:!?)]", rest):
        return phrase
    extra = []
    for w in re.findall(r"^\s*([A-Za-z][A-Za-z\-]*)(?=[\s.,;:!?]|$)", rest)[:1] + re.findall(r"\s([A-Za-z][A-Za-z\-]*)", rest)[1:]:
        if w.lower() in STOPWORDS or len(extra) >= max_extra:
            break
        extra.append(w)
    return " ".join([phrase] + extra)


def lead_fragment(text: str, max_words: int = 7) -> str:
    """The opening words of a sentence, cut at the first comma, as a headline."""
    first = re.split(r"[,;:—]", text, maxsplit=1)[0].strip().rstrip(".")
    ws = first.split()
    if len(ws) <= max_words:
        return first
    return " ".join(ws[:max_words]) + "…"
