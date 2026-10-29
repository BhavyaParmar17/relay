"""Import readable text from a public web page (blog, case study, product page)."""
from __future__ import annotations

import ipaddress
import re
import socket
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse

MAX_BYTES = 2_000_000
SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "aside", "button", "iframe"}
BLOCK = {"p", "h1", "h2", "h3", "h4", "li", "blockquote"}


class FetchError(ValueError):
    def __init__(self, message: str):
        super().__init__(message)
        self.field = "url"
        self.message = message


class _Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.stack: list[str] = []
        self.blocks: list[tuple[str, str]] = []
        self.buf: list[str] = []
        self.title = ""
        self.og_title = ""
        self.in_title = False
        self.in_main = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in SKIP:
            self.skip += 1
        if tag == "title":
            self.in_title = True
        if tag == "meta" and a.get("property") == "og:title":
            self.og_title = a.get("content", "")
        if tag in ("article", "main"):
            self.in_main += 1
        if tag in BLOCK:
            self.stack.append(tag)
            self.buf = []
        if tag == "br":
            self.buf.append(" ")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1
        if tag == "title":
            self.in_title = False
        if tag in ("article", "main") and self.in_main:
            self.in_main -= 1
        if tag in BLOCK and self.stack:
            self.stack.pop()
            text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if text and not self.skip:
                self.blocks.append((tag, text, bool(self.in_main)))
            self.buf = []

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.stack and not self.skip:
            self.buf.append(data)


def _check_host(host: str):
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise FetchError("That address could not be found.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise FetchError("Only public web pages can be imported.")


def import_url(url: str) -> dict:
    url = (url or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FetchError("Enter a full link starting with https://")
    _check_host(parsed.hostname)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; RelayImporter/1.0)",
        "Accept": "text/html,application/xhtml+xml",
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            ctype = res.headers.get("Content-Type", "")
            if "html" not in ctype:
                raise FetchError("That link isn’t a web page.")
            raw = res.read(MAX_BYTES + 1)
            charset = res.headers.get_content_charset() or "utf-8"
    except FetchError:
        raise
    except Exception:
        raise FetchError("The page couldn’t be loaded. Paste the text instead.")
    if len(raw) > MAX_BYTES:
        raise FetchError("That page is too large to import.")
    parser = _Extractor()
    parser.feed(raw.decode(charset, errors="replace"))
    blocks = parser.blocks
    main = [b for b in blocks if b[2]]
    chosen = main if sum(len(b[1]) for b in main) > 400 else blocks
    lines = []
    for tag, text, _ in chosen:
        if tag.startswith("h"):
            lines.append(f"\n## {text}")
        elif tag == "li":
            lines.append(f"- {text}")
        elif len(text.split()) >= 6:
            lines.append(text + "\n")
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    if len(body.split()) < 60:
        raise FetchError("Not enough readable text on that page. Paste the text instead.")
    title = (parser.og_title or parser.title or "").strip()
    title = re.split(r"\s[|–—-]\s", title)[0].strip()
    return {"title": title, "source_text": body[:60000], "url": url}
