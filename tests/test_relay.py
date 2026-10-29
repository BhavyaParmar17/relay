import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from _core.analyze import SourceError, analyse  # noqa: E402
from _core.generate import build_all, verify_edit  # noqa: E402
from _core.samples import SAMPLES  # noqa: E402
from _core.text import find_numbers, segment  # noqa: E402
from _core.voice import build_voice, enforce  # noqa: E402
from index import app  # noqa: E402

APPROVED = {"approved": True, "approver": "Test Reviewer"}


def run(sample):
    a = analyse({**sample, "approval": APPROVED})
    v = build_voice(sample["brand"])
    return a, v, build_all(a, v)


def all_items(out):
    o = out["outputs"]
    return o["linkedin"]["blocks"] + o["instagram"]["blocks"] + o["instagram"]["slides"] + o["video"]["scenes"]


def test_segmentation_numbers_every_line():
    segs = segment("## Heading\nFirst sentence here. Second one, with 3.5% growth.\n\n- A bullet point")
    assert [s["id"] for s in segs] == ["S1", "S2", "S3", "S4"]
    assert segs[0]["kind"] == "heading" and segs[3]["kind"] == "bullet"
    assert "3.5%" in find_numbers(segs[2]["text"])


@pytest.mark.parametrize("sample", SAMPLES, ids=[s["id"] for s in SAMPLES])
def test_samples_produce_three_platforms_with_no_fact_flags(sample):
    a, v, out = run(sample)
    o = out["outputs"]
    assert o["linkedin"]["meta"]["chars"] <= 3000
    assert o["instagram"]["meta"]["hashtag_count"] <= 5
    assert o["instagram"]["meta"]["fold_ok"]
    assert o["video"]["duration"] <= 60
    assert out["summary"]["high_issues"] == 0


@pytest.mark.parametrize("sample", SAMPLES, ids=[s["id"] for s in SAMPLES])
def test_every_sourced_line_traces_to_real_segments(sample):
    a, v, out = run(sample)
    ids = {s["id"] for s in a["segments"]} | {"T"}
    for item in all_items(out):
        assert set(item["sources"]) <= ids


@pytest.mark.parametrize("sample", SAMPLES, ids=[s["id"] for s in SAMPLES])
def test_no_invented_figures(sample):
    a, v, out = run(sample)
    source_numbers = {n.replace(",", "") for s in a["segments"] for n in find_numbers(s["text"])}
    source_digits = {"".join(ch for ch in n if ch.isdigit() or ch == ".") for n in source_numbers}
    o = out["outputs"]
    text = o["linkedin"]["text"] + o["instagram"]["text"] + o["video"]["text"]
    text = " ".join(w for w in text.split() if not w.startswith(("http", "#")))
    for n in find_numbers(text):
        digits = "".join(ch for ch in n.replace(",", "") if ch.isdigit() or ch == ".")
        assert digits in source_digits, n


def test_approval_is_required():
    with pytest.raises(SourceError) as err:
        analyse({**SAMPLES[0], "approval": {"approved": False}})
    assert err.value.field == "approval"


def test_short_source_rejected():
    with pytest.raises(SourceError):
        analyse({"source_text": "Too short.", "approval": APPROVED})


def test_preferred_terms_skip_links_and_hashtags():
    v = build_voice({"preferred_terms": "customers -> clients"})
    text, log = enforce("Our customers love it https://x.com/customers #customers", v)
    assert text == "Our clients love it https://x.com/customers #customers"
    assert len(log) == 1


def test_contractions_and_exclamations_follow_voice():
    friendly = build_voice({"preset": "friendly"})
    expert = build_voice({"preset": "expert"})
    assert enforce("It is not hard!", friendly)[0] == "It isn't hard!"
    assert enforce("It is not hard!", expert)[0] == "It is not hard."


def test_verify_catches_changed_figure_and_new_name():
    a, v, out = run(SAMPLES[0])
    hook = out["outputs"]["linkedin"]["blocks"][0]
    res = verify_edit(a, v, "linkedin", "Late payments fell by 45% at Acme Corp.", hook["sources"])
    messages = " ".join(i["message"] for i in res["issues"])
    assert "45%" in messages and "Acme Corp" in messages


def test_banned_words_flagged():
    a, v, out = run(SAMPLES[0])
    res = verify_edit(a, v, "linkedin", "A cheap fix that will unlock growth.", [])
    types = {i["type"] for i in res["issues"]}
    assert {"banned", "hype"} <= types


def test_api_flow_and_exports():
    c = app.test_client()
    cfg = c.get("/api/config").get_json()
    assert len(cfg["presets"]) == 3 and len(cfg["samples"]) == 3
    body = {**cfg["samples"][1], "approval": APPROVED}
    r = c.post("/api/repurpose", json=body)
    assert r.status_code == 200
    data = r.get_json()
    for fmt, marker in (("md", "## Traceability"), ("csv", "source_ids"), ("json", "fact_ledger")):
        e = c.post("/api/export", json={**body, "format": fmt, "outputs": data["outputs"]})
        assert e.status_code == 200 and marker in e.data.decode("utf-8")
    v = c.post("/api/verify", json={**body, "items": [{"id": "x", "platform": "linkedin", "text": "Up 99%.", "sources": []}]})
    assert v.get_json()["items"][0]["issues"][0]["severity"] == "high"
    assert c.post("/api/repurpose", json={**body, "approval": {}}).status_code == 400
    assert c.post("/api/import", json={"url": "http://localhost/admin"}).status_code == 400
