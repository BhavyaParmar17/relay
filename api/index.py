"""Flask API for Relay. Deployed on Vercel as a Python serverless function."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, Response, jsonify, request  # noqa: E402

from _core.analyze import SourceError, analyse  # noqa: E402
from _core.export import to_csv, to_json, to_markdown  # noqa: E402
from _core.fetch import FetchError, import_url  # noqa: E402
from _core.generate import build_all, coverage, verify_edit  # noqa: E402
from _core.samples import SAMPLES  # noqa: E402
from _core.voice import PRESETS, build_voice  # noqa: E402

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1_000_000


@app.after_request
def add_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


class BadRequest(ValueError):
    def __init__(self, field, message):
        super().__init__(message)
        self.field, self.message = field, message


def _payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest("body", "Send a JSON object.")
    return data


@app.errorhandler(SourceError)
@app.errorhandler(FetchError)
@app.errorhandler(BadRequest)
def handle_error(exc):
    return jsonify({"error": exc.message, "field": exc.field}), 400


@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": "That request is too large."}), 413


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "relay"})


@app.route("/api/config")
def config():
    return jsonify({
        "presets": list(PRESETS.values()),
        "samples": [{k: s[k] for k in ("id", "label", "source_type", "title", "url", "source_text", "brand")} for s in SAMPLES],
    })


@app.route("/api/repurpose", methods=["POST", "OPTIONS"])
def repurpose():
    if request.method == "OPTIONS":
        return "", 204
    data = _payload()
    analysis = analyse(data)
    voice = build_voice(data.get("brand"))
    result = build_all(analysis, voice)
    return jsonify({"analysis": analysis, "voice": voice, **result})


@app.route("/api/verify", methods=["POST", "OPTIONS"])
def verify():
    """Re-check edited text. Body: the repurpose payload plus `items`."""
    if request.method == "OPTIONS":
        return "", 204
    data = _payload()
    analysis = analyse(data)
    voice = build_voice(data.get("brand"))
    items = data.get("items") or []
    if not isinstance(items, list) or len(items) > 80:
        raise BadRequest("items", "Send a list of up to 80 items to check.")
    checked = []
    for item in items:
        platform = item.get("platform")
        if platform not in ("linkedin", "instagram", "video"):
            raise BadRequest("platform", "Unknown platform.")
        text = str(item.get("text", ""))[:5000]
        res = verify_edit(analysis, voice, platform, text, item.get("sources") or [])
        checked.append({"id": item.get("id"), **res})
    return jsonify({"items": checked})


@app.route("/api/import", methods=["POST", "OPTIONS"])
def import_page():
    if request.method == "OPTIONS":
        return "", 204
    return jsonify(import_url(_payload().get("url", "")))


@app.route("/api/export", methods=["POST", "OPTIONS"])
def export():
    if request.method == "OPTIONS":
        return "", 204
    data = _payload()
    fmt = data.get("format", "md")
    analysis = analyse(data)
    outputs = data.get("outputs")
    if not isinstance(outputs, dict) or not {"linkedin", "instagram", "video"} <= set(outputs):
        voice = build_voice(data.get("brand"))
        outputs = build_all(analysis, voice)["outputs"]
    slug = re.sub(r"[^a-z0-9]+", "-", analysis["title"].lower()).strip("-")[:50] or "relay"
    if fmt == "csv":
        body, mime, ext = to_csv(analysis, outputs), "text/csv; charset=utf-8", "csv"
    elif fmt == "json":
        body, mime, ext = to_json(analysis, outputs, coverage(analysis, outputs)), "application/json", "json"
    elif fmt == "md":
        body, mime, ext = to_markdown(analysis, outputs), "text/markdown; charset=utf-8", "md"
    else:
        raise BadRequest("format", "Choose md, csv or json.")
    return Response(body, mimetype=mime, headers={"Content-Disposition": f'attachment; filename="{slug}-relay.{ext}"'})


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
