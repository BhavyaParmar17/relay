"""
Turns raw source text into a traceable source model:
numbered segments, a role for each (challenge, solution, result, feature,
benefit, insight...), an importance score and a ledger of hard facts.
"""
from __future__ import annotations

import re

from .text import (
    content_words,
    find_numbers,
    find_proper_nouns,
    keywords,
    number_core,
    readability,
    segment,
    word_count,
)

SOURCE_TYPES = ("blog", "case_study", "product_page")

ROLE_CUES = {
    "challenge": r"\b(problem|challenge|struggl\w*|pain|manual\w*|slow|delay\w*|late|chas\w*|bottleneck|before|spent|losing|lost|frustrat\w*|hard to|difficult|risk)\b",
    "solution": r"\b(implemented|introduced|built|switched|adopted|set up|rolled out|started using|solution|automat\w*|integrat\w*|moved to|chose|deployed)\b",
    "result": r"\b(increas\w*|reduc\w*|cut|saved|grew|growth|improv\w*|dropped|fell|rose|faster|result\w*|now|within|doubled|halved|recovered)\b",
    "feature": r"\b(feature\w*|includes?|comes with|built-in|supports?|lets you|dashboard|template\w*|integrat\w*|schedul\w*|track\w*|export\w*)\b",
    "benefit": r"\b(so you|helps?|save\w*|without|never|less time|more time|peace of mind|easier|simpler|faster|fewer|no more)\b",
    "insight": r"\b(why|how|because|means|lesson|truth|most|common|mistake|should|key|matters|the reason|instead)\b",
    "quote": r"[\"“].{12,}[\"”]",
}
ROLE_ORDER = {
    "case_study": ["challenge", "solution", "result", "quote"],
    "product_page": ["feature", "benefit", "result"],
    "blog": ["insight", "challenge", "result", "benefit"],
}


class SourceError(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


def detect_roles(text: str) -> list[str]:
    return [role for role, pattern in ROLE_CUES.items() if re.search(pattern, text, flags=re.I)]


def analyse(payload: dict) -> dict:
    title = (payload.get("title") or "").strip()
    raw = payload.get("source_text") or ""
    source_type = payload.get("source_type") or "blog"
    if source_type not in SOURCE_TYPES:
        raise SourceError("source_type", "Choose blog, case study or product page.")
    if word_count(raw) < 60:
        raise SourceError("source_text", "Paste at least 60 words of approved source text.")
    if len(raw) > 60000:
        raise SourceError("source_text", "Keep the source under 60,000 characters.")
    approval = payload.get("approval") or {}
    if not approval.get("approved"):
        raise SourceError("approval", "Confirm the source is approved before repurposing it.")
    if not (approval.get("approver") or "").strip():
        raise SourceError("approval", "Add who approved the source.")

    segments = segment(raw)
    if not title:
        first_heading = next((s for s in segments if s["kind"] == "heading"), None)
        title = first_heading["text"] if first_heading else segments[0]["text"][:90]

    kw = keywords(segments, title)
    kw_weight = {w: c for w, c in kw}
    title_words = set(content_words(title))
    total = len(segments)

    facts: list[dict] = []
    for idx, seg in enumerate(segments):
        text = seg["text"]
        cw = content_words(text)
        nums = find_numbers(text)
        names = find_proper_nouns(text)
        roles = detect_roles(text)
        n_words = word_count(text)

        score = sum(kw_weight.get(w, 0) for w in set(cw)) / (len(set(cw)) ** 0.5 + 1)
        score += 2.2 * min(len(nums), 2)
        score += 0.8 * len(title_words.intersection(cw))
        if idx < max(2, total // 8):
            score += 0.8
        if "result" in roles:
            score += 1.2
        if "quote" in roles:
            score += 1.0
        if seg["kind"] == "heading":
            score *= 0.35
        if n_words < 6 and seg["kind"] != "bullet":
            score *= 0.5
        if n_words > 42:
            score *= 0.7

        seg.update({
            "numbers": nums,
            "names": names,
            "roles": roles,
            "score": round(score, 3),
            "words": n_words,
        })
        for n in nums:
            facts.append({"id": f"F{len(facts) + 1}", "kind": "figure", "value": n, "core": number_core(n), "source": seg["id"]})
        for name in names:
            if not any(f["value"] == name for f in facts):
                facts.append({"id": f"F{len(facts) + 1}", "kind": "name", "value": name, "core": name.lower(), "source": seg["id"]})
        quote = re.search(r"[\"“](.{12,}?)[\"”]", text)
        if quote:
            facts.append({"id": f"F{len(facts) + 1}", "kind": "quote", "value": quote.group(1), "core": quote.group(1).lower(), "source": seg["id"]})

    return {
        "title": title,
        "source_type": source_type,
        "url": (payload.get("url") or "").strip(),
        "approval": {
            "approved": True,
            "approver": approval.get("approver", "").strip(),
            "date": (approval.get("date") or "").strip(),
        },
        "segments": segments,
        "keywords": [w for w, _ in kw],
        "facts": facts,
        "stats": {
            "segments": total,
            "words": word_count(raw),
            "figures": sum(1 for f in facts if f["kind"] == "figure"),
            "names": sum(1 for f in facts if f["kind"] == "name"),
            "readability": readability(raw),
        },
    }


def pick(segments: list[dict], *, roles: list[str] | None = None, used: set[str] | None = None,
         limit: int = 3, need_number: bool = False, max_words: int | None = None) -> list[dict]:
    used = used if used is not None else set()
    pool = [
        s for s in segments
        if s["id"] not in used and s["kind"] != "heading"
        and (not roles or set(roles).intersection(s["roles"]))
        and (not need_number or s["numbers"])
        and (max_words is None or s["words"] <= max_words)
        and s["words"] >= 5
    ]
    pool.sort(key=lambda s: s["score"], reverse=True)
    chosen = pool[:limit]
    for s in chosen:
        used.add(s["id"])
    return chosen
