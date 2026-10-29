"""Export the repurposed set with source-to-post traceability."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone


def _seg_lookup(analysis: dict) -> dict:
    lookup = {s["id"]: s["text"] for s in analysis["segments"]}
    lookup["T"] = analysis["title"]
    return lookup


def rows(analysis: dict, outputs: dict) -> list[dict]:
    look = _seg_lookup(analysis)
    out = []

    def add(platform, part, item_id, text, sources):
        out.append({
            "platform": platform,
            "part": part,
            "id": item_id,
            "text": text,
            "source_ids": " ".join(sources),
            "source_text": " | ".join(look.get(s, "") for s in sources),
        })

    for b in outputs["linkedin"]["blocks"]:
        add("LinkedIn", b["kind"], b["id"], b["text"], b["sources"])
    for b in outputs["instagram"]["blocks"]:
        add("Instagram caption", b["kind"], b["id"], b["text"], b["sources"])
    for s in outputs["instagram"]["slides"]:
        add("Instagram carousel", s["kind"], s["id"], f"{s['headline']} — {s['body']}", s["sources"])
    for s in outputs["video"]["scenes"]:
        add("Short video", s["label"], s["id"], f"[{s['start']}–{s['end']}s] VO: {s['voiceover']} | On screen: {s['on_screen']} | Visual: {s['visual']}", s["sources"])
    return out


def to_csv(analysis: dict, outputs: dict) -> str:
    buf = io.StringIO()
    fields = ["platform", "part", "id", "text", "source_ids", "source_text"]
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows(analysis, outputs))
    return "\ufeff" + buf.getvalue()


def to_markdown(analysis: dict, outputs: dict) -> str:
    look = _seg_lookup(analysis)
    ap = analysis["approval"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = [
        f"# {analysis['title']}",
        "",
        f"Source type: {analysis['source_type'].replace('_', ' ')}  ",
        f"Approved by: {ap['approver']}{' on ' + ap['date'] if ap.get('date') else ''}  ",
        f"Source link: {analysis['url'] or '—'}  ",
        f"Exported: {stamp}",
        "",
        "## LinkedIn",
        "",
        outputs["linkedin"]["text"],
        "",
        "## Instagram caption",
        "",
        outputs["instagram"]["text"],
        "",
        "## Instagram carousel",
        "",
    ]
    for i, s in enumerate(outputs["instagram"]["slides"], start=1):
        md.append(f"{i}. **{s['headline']}** — {s['body']}")
    md += ["", f"Alt text: {outputs['instagram']['alt_text']}", "", "## Short video script", "",
           "| Time | Scene | Voiceover | On screen | Visual |", "|---|---|---|---|---|"]
    for s in outputs["video"]["scenes"]:
        md.append(f"| {s['start']}–{s['end']}s | {s['label']} | {s['voiceover']} | {s['on_screen']} | {s['visual']} |")
    md += ["", "## Traceability", "", "| Post part | Source line | Source text |", "|---|---|---|"]
    for r in rows(analysis, outputs):
        if r["source_ids"]:
            md.append(f"| {r['platform']} {r['id']} | {r['source_ids']} | {r['source_text'].replace('|', '/')} |")
    md += ["", "## Approved source, numbered", ""]
    for sid, text in look.items():
        if sid != "T":
            md.append(f"- **{sid}** {text}")
    return "\n".join(md) + "\n"


def to_json(analysis: dict, outputs: dict, ledger: list) -> str:
    return json.dumps({"source": analysis, "outputs": outputs, "fact_ledger": ledger}, indent=2, ensure_ascii=False)
