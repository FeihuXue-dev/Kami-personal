#!/usr/bin/env python3
"""Build a static-Shiki HTML/PDF variant without overwriting reviewed PDFs.

Usage:
  python3 scripts/rebuild_shiki_pdf.py source.html out.html out.pdf \
    --input-pdf reviewed.pdf

Language-tagged code blocks are highlighted with the configured Shiki theme.
Previously static Shiki blocks from a non-current theme can be re-highlighted
when their plain text strongly identifies as Python, Bash, SQL, JSON, or JS.
Any non-Link / non-Widget PDF annotation is treated as a review record: the
script refuses an in-place PDF output so the caller must write a variant.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from highlight import highlight_code_blocks  # noqa: E402
from math_render import render_latex_in_html  # noqa: E402
from render import render_pdf  # noqa: E402

LEGACY_SHIKI_RE = re.compile(
    r'<pre\b(?P<attrs>[^>]*\bclass="[^"]*\bshiki-rendered\b[^"]*"[^>]*)>'
    r'\s*<code\b[^>]*>(?P<code>.*?)</code>\s*</pre>',
    re.IGNORECASE | re.DOTALL,
)
REVIEW_ANNOTATION_SUBTYPES = {"/Text", "/FreeText", "/Highlight", "/Underline", "/Squiggly", "/StrikeOut", "/Ink", "/Square", "/Circle", "/Stamp", "/FileAttachment"}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def visible_text(fragment: str) -> str:
    parser = _TextExtractor()
    parser.feed(fragment)
    return html.unescape("".join(parser.parts)).strip("\n")


def guess_language(code: str) -> str | None:
    stripped = code.strip()
    if re.search(r"(?m)^\s*(from\s+\w+\s+import|import\s+\w+|def\s+\w+\(|class\s+\w+|for\s+\w+\s+in\s+|while\s+|return\b)", stripped):
        return "python"
    if re.search(r"(?im)^\s*(SELECT|WITH|INSERT|UPDATE|DELETE)\b", stripped):
        return "sql"
    if re.search(r"(?m)^\s*(#!/bin/(ba)?sh|set -[a-z]+|export\s+\w+=|pip\s+install|python3?\s)", stripped):
        return "bash"
    if stripped.startswith(("{", "[")):
        return "json"
    if re.search(r"(?m)^\s*(const|let|function|import\s+.*from)\b", stripped):
        return "javascript"
    return None


def rehighlight_legacy_shiki(raw: str) -> tuple[str, int]:
    """Turn confidently recognized old static Shiki blocks back into source blocks."""
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        code = visible_text(match.group("code"))
        language = guess_language(code)
        if language is None:
            return match.group(0)
        changed += 1
        return f'<pre><code class="language-{language}">{html.escape(code)}</code></pre>'

    return LEGACY_SHIKI_RE.sub(replace, raw), changed


def review_annotations(pdf: Path) -> dict[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf))
    found: dict[str, int] = {}
    for page in reader.pages:
        for ref in page.get("/Annots", []) or []:
            annotation = ref.get_object()
            subtype = str(annotation.get("/Subtype", "/Unknown"))
            found[subtype] = found.get(subtype, 0) + 1
    return found


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_html", type=Path)
    parser.add_argument("output_html", type=Path)
    parser.add_argument("output_pdf", type=Path)
    parser.add_argument("--input-pdf", type=Path, help="Existing PDF to inspect for review annotations")
    parser.add_argument("--rehighlight-legacy", action="store_true", help="Re-highlight recognized non-current Shiki blocks")
    args = parser.parse_args(argv)

    source, out_html, out_pdf = args.source_html, args.output_html, args.output_pdf
    if not source.is_file():
        print(f"ERROR: source HTML not found: {source}")
        return 2
    if out_html.resolve() == source.resolve():
        print("ERROR: output_html must be a distinct build artifact; preserve the source HTML")
        return 2
    if args.input_pdf:
        if not args.input_pdf.is_file():
            print(f"ERROR: input PDF not found: {args.input_pdf}")
            return 2
        annotations = review_annotations(args.input_pdf)
        review = {k: v for k, v in annotations.items() if k in REVIEW_ANNOTATION_SUBTYPES or k not in {"/Link", "/Widget"}}
        if review and out_pdf.resolve() == args.input_pdf.resolve():
            print(f"ERROR: reviewed PDF has annotations {review}; output_pdf must be a new variant")
            return 2
        if review:
            print(f"INFO: preserving reviewed PDF; writing Shiki variant because of {review}")

    raw = source.read_text(encoding="utf-8")
    legacy_count = 0
    if args.rehighlight_legacy:
        raw, legacy_count = rehighlight_legacy_shiki(raw)
    rendered = highlight_code_blocks(render_latex_in_html(raw))
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(rendered, encoding="utf-8")
    pages = render_pdf(out_html, out_pdf)
    shiki_blocks = rendered.count('<pre class="shiki shiki-rendered')
    print(f"OK: {out_html}: {shiki_blocks} Shiki block(s), {legacy_count} legacy block(s) re-highlighted")
    print(f"OK: {out_pdf}: {pages} page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
