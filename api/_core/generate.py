"""
Generators for LinkedIn, Instagram and short-video scripts.

Every output is built from blocks. A block carries its text and the source
segment ids it came from, so each line of each post can be traced back to the
approved source. Framing lines (lead-ins, calls to action) carry no source ids
and never contain figures, so they cannot introduce new facts.
"""
from __future__ import annotations

import re

from .analyze import ROLE_ORDER, pick
from .text import (
    STOPWORDS,
    content_words,
    ensure_period,
    figure_phrase,
    find_numbers,
    find_proper_nouns,
    lead_fragment,
    number_core,
    readability,
    trim_connector,
    word_count,
)
from .voice import check as voice_check
from .voice import enforce

WORDS_PER_SECOND = 2.5
LIMITS = {
    "linkedin": {"chars": 3000, "fold": 210, "hashtags": 5},
    "instagram": {"chars": 2200, "fold": 125, "hashtags": 5},
    "video": {"seconds": 60, "ideal": (25, 50)},
}
GENERIC_NAMES = {
    "linkedin", "instagram", "link", "bio", "swipe", "save", "follow", "comment", "share", "read", "watch",
    "here", "what", "the", "full", "see", "bottom", "line", "takeaway", "voiceover", "cut", "case", "study",
}

LEAD_INS = {
    "case_study": {"expert": "What changed:", "friendly": "Here's what happened:", "bold": "What happened:"},
    "blog": {"expert": "The points worth keeping:", "friendly": "A few things worth knowing:", "bold": "What matters:"},
    "product_page": {"expert": "What it does:", "friendly": "Here's what you get:", "bold": "What you get:"},
}
TAKEAWAY = {"expert": "The takeaway: ", "friendly": "The big takeaway? ", "bold": "Bottom line: "}
DEFAULT_CTA = {
    "case_study": "Read the full case study",
    "blog": "Read the full article",
    "product_page": "See how it works",
}
VISUALS = {
    "case_study": ["Customer on camera or a photo of their team", "Screen recording of the before workflow",
                   "Screen recording of the product in use", "Simple chart animating the result"],
    "product_page": ["Close-up of the product screen", "Screen recording of the feature",
                     "Hands using the product on a phone", "Before and after split screen"],
    "blog": ["Talking head, presenter to camera", "Text on a plain brand-colour background",
             "Relevant B-roll from the article", "Presenter pointing to on-screen text"],
}


def _block(text: str, sources: list[str], kind: str) -> dict:
    return {"text": text, "sources": sources, "kind": kind}


def _clean(seg: dict) -> str:
    return ensure_period(trim_connector(seg["text"]))


def _key_phrase(seg: dict, keywords: list[str] | None = None, max_words: int = 6) -> str:
    """Headline for a slide or on-screen text, taken verbatim from the segment."""
    return figure_phrase(seg["text"]) or lead_fragment(trim_connector(seg["text"]), max_words)


GENERIC_TAG_WORDS = {
    "days", "day", "hours", "hour", "weeks", "week", "months", "month", "years", "year", "time", "paid", "late",
    "small", "big", "large", "average", "around", "under", "more", "less", "every", "single", "now", "team",
    "people", "things", "thing", "work", "start", "started", "using", "makes", "made", "part", "close",
}


def _hashtags(analysis: dict, voice: dict, limit: int) -> list[str]:
    tags = list(voice["hashtags"])
    seen = {t.lower() for t in tags}

    def add(tag):
        if len(tags) < limit and tag.lower() not in seen and len(tag) > 3:
            tags.append(tag)
            seen.add(tag.lower())

    for name in find_proper_nouns(analysis["title"]):
        name = " ".join(w for w in name.split() if w.lower() not in STOPWORDS)
        if 1 < len(name.split()) <= 3:
            add("#" + re.sub(r"[^A-Za-z0-9]", "", name.title().replace(" ", "")))
    for kw in analysis["keywords"]:
        if kw in GENERIC_TAG_WORDS or len(kw) < 5:
            continue
        add("#" + re.sub(r"[^A-Za-z0-9]", "", kw).capitalize())
    return tags[:limit]


def _ordered(segments: list[dict]) -> list[dict]:
    order = {s["id"]: i for i, s in enumerate(segments)}
    return sorted(segments, key=lambda s: order[s["id"]])


def _structured_points(analysis: dict, used: set[str], count: int, max_words: int = 40) -> list[dict]:
    segs = analysis["segments"]
    roles = ROLE_ORDER[analysis["source_type"]]
    chosen: list[dict] = []
    for role in roles:
        if len(chosen) >= count:
            break
        chosen += pick(segs, roles=[role], used=used, limit=1, max_words=max_words)
    if len(chosen) < count:
        chosen += pick(segs, used=used, limit=count - len(chosen), max_words=max_words)
    by_id = {s["id"]: i for i, s in enumerate(segs)}
    return sorted(chosen, key=lambda s: by_id[s["id"]])


def _cta(analysis: dict, voice: dict, platform: str) -> str:
    base = voice["cta"] or DEFAULT_CTA[analysis["source_type"]]
    base = base.rstrip(".")
    if platform == "instagram":
        text = f"{base} at the link in bio."
    elif analysis["url"]:
        text = f"{base}: {analysis['url']}"
    else:
        text = f"{base}."
    if voice["emoji"] == "light" and platform != "video":
        text = "👉 " + text
    return text


# --------------------------------------------------------------------------- #
def linkedin(analysis: dict, voice: dict) -> dict:
    segs = analysis["segments"]
    used: set[str] = set()
    hook = (pick(segs, roles=["result", "benefit"], used=used, limit=1, need_number=True, max_words=30)
            or pick(segs, used=used, limit=1, need_number=True, max_words=30)
            or pick(segs, used=used, limit=1, max_words=34))
    blocks = []
    if hook:
        blocks.append(_block(_clean(hook[0]), [hook[0]["id"]], "hook"))
    else:
        blocks.append(_block(ensure_period(analysis["title"]), ["T"], "hook"))

    points = _structured_points(analysis, used, 4)
    blocks.append(_block(LEAD_INS[analysis["source_type"]][voice["id"]], [], "framing"))
    for p in points:
        blocks.append(_block(f"{voice['bullet']} {_clean(p)}", [p["id"]], "point"))

    takeaway = pick(segs, roles=["insight", "benefit", "result", "quote"], used=used, limit=1, max_words=34)
    if takeaway:
        sentence = _clean(takeaway[0])
        lead = TAKEAWAY[voice["id"]]
        first_word = sentence.split()[0].strip(",.;:")
        source_lower = " ".join(s["text"] for s in segs)
        common = first_word.lower() in STOPWORDS or re.search(r"\b" + re.escape(first_word.lower()) + r"\b", source_lower)
        lowercase = common and not first_word.isupper() and lead.rstrip().endswith(":")
        first = sentence[:1].lower() + sentence[1:] if lowercase else sentence
        blocks.append(_block(lead + first, [takeaway[0]["id"]], "takeaway"))

    blocks.append(_block(_cta(analysis, voice, "linkedin"), [], "cta"))
    blocks.append(_block(" ".join(_hashtags(analysis, voice, 4)), [], "hashtags"))
    return {"platform": "linkedin", "blocks": blocks}


def instagram(analysis: dict, voice: dict) -> dict:
    segs = analysis["segments"]
    used: set[str] = set()
    fold = LIMITS["instagram"]["fold"]
    hook_seg = sorted(
        [s for s in segs if s["kind"] != "heading" and len(_clean(s)) <= fold and s["words"] >= 5],
        key=lambda s: (s["score"] + (2 if {"result", "benefit"} & set(s["roles"]) and s["numbers"] else 0)),
        reverse=True,
    )
    caption = []
    if hook_seg:
        used.add(hook_seg[0]["id"])
        caption.append(_block(_clean(hook_seg[0]), [hook_seg[0]["id"]], "hook"))
    elif len(analysis["title"]) <= fold:
        caption.append(_block(ensure_period(analysis["title"]), ["T"], "hook"))

    for s in _ordered(pick(segs, used=used, limit=2, max_words=28)):
        caption.append(_block(_clean(s), [s["id"]], "body"))
    caption.append(_block(_cta(analysis, voice, "instagram"), [], "cta"))
    caption.append(_block(" ".join(_hashtags(analysis, voice, LIMITS["instagram"]["hashtags"])), [], "hashtags"))

    slides = [{
        "headline": analysis["title"],
        "body": "Swipe through for the key points." if voice["id"] != "bold" else "Swipe for the key points.",
        "sources": ["T"],
        "kind": "cover",
    }]
    slide_used: set[str] = set()
    for s in _structured_points(analysis, slide_used, 5, max_words=32):
        slides.append({"headline": _key_phrase(s, analysis["keywords"]), "body": _clean(s), "sources": [s["id"]], "kind": "point"})
    slides.append({"headline": voice["brand_name"] or "Read the full story", "body": _cta(analysis, voice, "instagram"), "sources": [], "kind": "cta"})

    alt = f"Carousel cover with the title “{analysis['title']}”, followed by {len(slides) - 2} slides of key points and a closing call to action."
    return {"platform": "instagram", "blocks": caption, "slides": slides, "alt_text": alt}


def video(analysis: dict, voice: dict) -> dict:
    segs = analysis["segments"]
    st = analysis["source_type"]
    used: set[str] = set()
    plan = {
        "case_study": [("Hook", ["result"], True), ("The problem", ["challenge"], False), ("What they did", ["solution"], False), ("The result", ["result"], False)],
        "product_page": [("Hook", ["benefit", "result"], True), ("Feature", ["feature"], False), ("Feature", ["feature"], False), ("Why it matters", ["benefit"], False)],
        "blog": [("Hook", ["insight", "result"], True), ("Point", ["insight"], False), ("Point", None, False), ("Point", None, False)],
    }[st]
    scenes = []
    visuals = VISUALS[st]
    for i, (label, roles, need_num) in enumerate(plan):
        found = pick(segs, roles=roles, used=used, limit=1, need_number=need_num, max_words=26)
        if not found:
            found = pick(segs, roles=roles, used=used, limit=1, max_words=26) or pick(segs, used=used, limit=1, max_words=26)
        if not found:
            continue
        s = found[0]
        scenes.append({
            "label": label,
            "voiceover": _clean(s),
            "on_screen": _key_phrase(s, analysis["keywords"], 4),
            "visual": visuals[i % len(visuals)],
            "sources": [s["id"]],
        })
    cta_line = _cta(analysis, voice, "video")
    scenes.append({"label": "Call to action", "voiceover": cta_line, "on_screen": voice["brand_name"] or "Link below",
                   "visual": "Logo end card with the link", "sources": []})

    # keep it inside the ideal range by dropping middle scenes if needed
    def total_seconds():
        return sum(max(2.5, word_count(s["voiceover"]) / WORDS_PER_SECOND) for s in scenes)

    while total_seconds() > LIMITS["video"]["ideal"][1] and len(scenes) > 3:
        scenes.pop(len(scenes) - 3)

    t = 0.0
    for s in scenes:
        dur = max(2.5, word_count(s["voiceover"]) / WORDS_PER_SECOND)
        s["start"] = round(t, 1)
        t += dur
        s["end"] = round(t, 1)
    return {"platform": "video", "scenes": scenes, "duration": round(t, 1), "hashtags": _hashtags(analysis, voice, 3)}


# --------------------------------------------------------------------------- #
def verify_text(text: str, cited: list[str], analysis: dict, brand: str = "") -> list[dict]:
    """Check that figures and names in text come from the source."""
    issues = []
    seg_by_id = {s["id"]: s for s in analysis["segments"]}
    source_text = " ".join(s["text"] for s in analysis["segments"]) + " " + analysis["title"]
    source_cores = {f["core"] for f in analysis["facts"] if f["kind"] == "figure"}
    cited_numbers = [n for sid in cited for n in seg_by_id.get(sid, {}).get("numbers", [])]
    cited_cores = {number_core(n) for n in cited_numbers}
    body = re.sub(r"(?:^|\s)#\w+", " ", text)
    body = re.sub(r"https?://\S+", " ", body)

    found_cores = set()
    for n in find_numbers(body):
        core = number_core(n)
        found_cores.add(core)
        if core not in source_cores:
            issues.append({"type": "figure", "severity": "high", "message": f"“{n}” isn’t in the approved source."})
        elif cited and core not in cited_cores:
            issues.append({"type": "figure", "severity": "low", "message": f"“{n}” is in the source, but not in the line this was drawn from."})
    for n in cited_numbers:
        core = number_core(n)
        if core not in found_cores and found_cores - source_cores:
            issues.append({"type": "figure", "severity": "high", "message": f"The source says “{n}”. Check the figure wasn’t changed."})

    lower_source = source_text.lower()
    for name in find_proper_nouns(body):
        if name.lower() in GENERIC_NAMES or (brand and name.lower() in brand.lower()):
            continue
        if all(part.lower() in GENERIC_NAMES for part in name.split()):
            continue
        if name.lower() not in lower_source:
            issues.append({"type": "name", "severity": "medium", "message": f"“{name}” doesn’t appear in the source."})
    return issues


def _finish_blocks(blocks: list[dict], voice: dict, analysis: dict, platform: str, changes: list[dict], prefix: str):
    for i, b in enumerate(blocks):
        b["id"] = f"{prefix}{i + 1}"
        if b["kind"] != "hashtags":
            b["text"], log = enforce(b["text"], voice, block_id=b["id"], platform=platform)
            changes.extend(log)
        b["issues"] = verify_text(b["text"], [s for s in b["sources"] if s != "T"], analysis, voice["brand_name"]) + (
            voice_check(b["text"], voice) if b["kind"] not in ("hashtags",) else []
        )


def render_linkedin(blocks: list[dict]) -> str:
    out, prev = [], None
    for b in blocks:
        if prev and not (prev == "point" and b["kind"] == "point") and not (prev == "framing" and b["kind"] == "point"):
            out.append("")
        out.append(b["text"])
        prev = b["kind"]
    return "\n".join(out)


def render_caption(blocks: list[dict]) -> str:
    return "\n\n".join(b["text"] for b in blocks)


def summarise(platform: str, text: str, extra: dict | None = None) -> dict:
    limits = LIMITS[platform]
    info = {"chars": len(text), "words": word_count(text), "readability": readability(text)}
    if "chars" in limits:
        info["limit"] = limits["chars"]
        info["over_limit"] = len(text) > limits["chars"]
        first = text.split("\n")[0]
        info["fold_chars"] = len(first)
        info["fold_ok"] = len(first) <= limits["fold"]
        info["fold_limit"] = limits["fold"]
        info["hashtag_count"] = len(re.findall(r"(?:^|\s)#\w+", text))
        info["hashtag_limit"] = limits["hashtags"]
    if extra:
        info.update(extra)
    return info


def coverage(analysis: dict, outputs: dict) -> list[dict]:
    texts = {
        "linkedin": outputs["linkedin"]["text"],
        "instagram": outputs["instagram"]["text"] + " " + " ".join(s["body"] + " " + s["headline"] for s in outputs["instagram"]["slides"]),
        "video": " ".join(s["voiceover"] + " " + s["on_screen"] for s in outputs["video"]["scenes"]),
    }
    ledger = []
    for f in analysis["facts"]:
        used_in = []
        for platform, text in texts.items():
            if f["kind"] == "figure":
                hit = f["core"] in {number_core(n) for n in find_numbers(text)}
            else:
                hit = f["value"].lower() in text.lower()
            if hit:
                used_in.append(platform)
        ledger.append({**f, "used_in": used_in})
    return ledger


def build_all(analysis: dict, voice: dict) -> dict:
    changes: list[dict] = []
    li = linkedin(analysis, voice)
    _finish_blocks(li["blocks"], voice, analysis, "linkedin", changes, "L")
    li["text"] = render_linkedin(li["blocks"])
    li["meta"] = summarise("linkedin", li["text"])

    ig = instagram(analysis, voice)
    _finish_blocks(ig["blocks"], voice, analysis, "instagram", changes, "I")
    for i, s in enumerate(ig["slides"]):
        s["id"] = f"C{i + 1}"
        for field in ("headline", "body"):
            s[field], log = enforce(s[field], voice, block_id=s["id"], platform="instagram")
            changes.extend(log)
        s["issues"] = verify_text(s["headline"] + ". " + s["body"], [x for x in s["sources"] if x != "T"], analysis, voice["brand_name"])
        s["body_words"] = word_count(s["body"])
    ig["text"] = render_caption(ig["blocks"])
    ig["meta"] = summarise("instagram", ig["text"], {"slides": len(ig["slides"])})

    vd = video(analysis, voice)
    for i, s in enumerate(vd["scenes"]):
        s["id"] = f"V{i + 1}"
        s["voiceover"], log = enforce(s["voiceover"], voice, block_id=s["id"], platform="video")
        changes.extend(log)
        s["on_screen"], _ = enforce(s["on_screen"], voice)
        s["issues"] = verify_text(s["on_screen"] + ". " + s["voiceover"], s["sources"], analysis, voice["brand_name"]) + voice_check(s["voiceover"], voice)
    script_text = "\n".join(s["voiceover"] for s in vd["scenes"])
    vd["text"] = script_text
    vd["meta"] = {
        "words": word_count(script_text),
        "duration": vd["duration"],
        "limit": LIMITS["video"]["seconds"],
        "ideal": LIMITS["video"]["ideal"],
        "in_range": LIMITS["video"]["ideal"][0] <= vd["duration"] <= LIMITS["video"]["ideal"][1],
        "readability": readability(script_text),
    }

    outputs = {"linkedin": li, "instagram": ig, "video": vd}
    ledger = coverage(analysis, outputs)
    traced_ids = {sid for o in (li["blocks"], ig["blocks"], ig["slides"], vd["scenes"]) for b in o for sid in b["sources"]}
    total_issues = sum(len(b["issues"]) for o in (li["blocks"], ig["blocks"], ig["slides"], vd["scenes"]) for b in o)
    high = sum(1 for o in (li["blocks"], ig["blocks"], ig["slides"], vd["scenes"]) for b in o for x in b["issues"] if x["severity"] == "high")
    return {
        "outputs": outputs,
        "voice_changes": changes,
        "ledger": ledger,
        "summary": {
            "segments_used": len(traced_ids - {"T"}),
            "segments_total": len(analysis["segments"]),
            "figures_used": sum(1 for f in ledger if f["kind"] == "figure" and f["used_in"]),
            "figures_total": sum(1 for f in ledger if f["kind"] == "figure"),
            "issues": total_issues,
            "high_issues": high,
            "voice_fixes": len(changes),
        },
    }


def verify_edit(analysis: dict, voice: dict, platform: str, text: str, sources: list[str]) -> dict:
    """Re-check a block, caption or scene after a person edits it."""
    issues = verify_text(text, [s for s in sources if s != "T"], analysis, voice["brand_name"]) + voice_check(text, voice)
    meta = summarise(platform, text) if platform in ("linkedin", "instagram") else {
        "words": word_count(text), "seconds": round(word_count(text) / WORDS_PER_SECOND, 1), "readability": readability(text)
    }
    return {"issues": issues, "meta": meta}


__all__ = ["build_all", "verify_edit", "content_words"]
