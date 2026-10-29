# Relay — Social Content Repurposing Pipeline

Turn an **approved** blog post, case study or product page into platform-specific **LinkedIn**, **Instagram** and **short-video** content. Relay preserves the source facts, enforces your brand voice and shows **source-to-post traceability** for every line.

**Tech stack:** Python · Flask (API) · React 18 (Vite) · Framer Motion · deployed on Vercel. No paid AI API or key is needed: the pipeline is deterministic, so every output can be traced and tested.

---

## Features

### 1. Approved source in
- Paste text (use `##` for headings and `-` for bullets), **import from a public URL**, or load one of three samples (case study, blog post, product page).
- **Approval gate:** posts are only written once the source is marked approved and an approver is named. The approval record is included in every export.

### 2. Fact extraction
- Every heading, bullet and sentence gets an id (`S1`, `S2`, …).
- A **fact ledger** collects figures (percentages, money, durations, counts), names and quotes, with the line each came from.
- Each line is scored (keywords, figures, position, title overlap) and tagged with a role: challenge, solution, result, feature, benefit, insight or quote.

### 3. Brand voice
- Presets: **Expert and calm**, **Friendly and warm**, **Bold and direct**.
- **Preferred terms** (`customers -> clients`) are swapped everywhere except links and hashtags.
- **Banned words** and **hype words** ("game-changer", "unlock", …) are flagged for a person to rewrite.
- Contractions, exclamation marks, emoji and sentence length follow the chosen voice.
- Every automatic change is logged in **Voice fixes**.

### 4. Platform outputs
| Platform | What Relay writes | Rules applied |
|---|---|---|
| LinkedIn | Hook, structured points, takeaway, call to action, hashtags | 3,000 characters; strongest figure in the first ~210 characters; 3–5 hashtags |
| Instagram | Caption plus a carousel (cover, key-point slides, call-to-action slide) and alt text | 2,200 characters; hook fits the first 125; maximum 5 hashtags (Instagram's limit since December 2025) |
| Short video | Timed scenes with voiceover, on-screen text and shot suggestion | 25–50 s target at 2.5 words per second; hook in the first 3 s |

Case studies follow challenge → solution → result; product pages follow feature → benefit; blogs follow insight → points.

### 5. Traceability and checking
- Every post line shows the source ids it came from. Framing lines, calls to action and hashtags are marked as added and never contain figures.
- **Hover** a post line to highlight its source sentence; **select** a source sentence to highlight every post line built from it.
- **Edit any line** and it is re-checked as you type: changed or invented figures, names not in the source, banned and hype words, over-long sentences, character and hashtag limits.
- **Export** to Markdown, CSV or JSON, including your edits, the approval record and a line-by-line source map.

---

## Project structure

```
relay/
├── api/
│   ├── index.py               # Flask app (Vercel serverless function)
│   └── _core/
│       ├── text.py            # Segmentation, numbers, names, readability
│       ├── analyze.py         # Source model, roles, scoring, fact ledger, approval gate
│       ├── voice.py           # Voice presets, enforcement and checks
│       ├── generate.py        # LinkedIn, Instagram and video builders, verification
│       ├── fetch.py           # Safe import from a public URL
│       ├── export.py          # Markdown, CSV and JSON exports
│       └── samples.py         # Sample approved sources
├── tests/test_relay.py        # Pytest suite
├── src/                       # React app (components/, lib/, styles.css)
├── index.html, package.json, vite.config.js
├── requirements.txt
└── vercel.json
```

---

## Run locally

Requirements: **Python 3.9+** and **Node.js 18+**.

```bash
pip install -r requirements.txt
npm install

# terminal 1 — Flask API on http://127.0.0.1:5000
python api/index.py

# terminal 2 — frontend on http://localhost:5173
npm run dev
```

Vite proxies `/api/*` to Flask during development.

- **Tests:** `pip install pytest` then `python -m pytest tests -q`
- **Production build:** `npm run build`

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/config` | Voice presets and sample sources |
| POST | `/api/repurpose` | Analyse the source and write all three formats |
| POST | `/api/verify` | Re-check edited lines against the source and voice |
| POST | `/api/import` | Pull readable text from a public web page |
| POST | `/api/export` | Download Markdown, CSV or JSON (`format`: `md`, `csv`, `json`) |

Example body for `/api/repurpose`:

```json
{
  "title": "How Kavya Interiors cut late payments by 41% in one quarter",
  "source_type": "case_study",
  "url": "https://example.com/case-study",
  "source_text": "…at least 60 words…",
  "approval": { "approved": true, "approver": "Riya Shah", "date": "2026-10-28" },
  "brand": {
    "brand_name": "Ledgerly",
    "preset": "expert",
    "preferred_terms": "customers -> clients",
    "banned_words": "cheap, guarantee",
    "hashtags": "#Ledgerly",
    "cta": "Read the full case study",
    "avoid_hype": true
  }
}
```

Errors return HTTP 400 with `{"error": "...", "field": "..."}`.

---

## Deploy to Vercel

`vercel.json` builds the Vite frontend into `dist/` and routes `/api/*` to `api/index.py`, which Vercel runs as a Python function using `requirements.txt`.

1. Push this folder to its own GitHub repository.
2. On vercel.com: **Add New → Project**, import the repository, click **Deploy**.

Or with the CLI: `npm i -g vercel && vercel --prod`.

---

## Author

_Your name, course and university here._
