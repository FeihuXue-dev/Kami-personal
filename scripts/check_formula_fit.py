#!/usr/bin/env python3
"""Formula-fit gate: no rendered content may cross the text column.

A display formula wider than the column is not wrapped and not scaled — the
renderer clips it, so the reader sees the left half of an equation and no
warning anywhere. This gate reads the delivered PDF's own geometry: it derives
the text column from the body-text bbox on each page, then fails on any drawing
(formula glyph runs, rules, tables, images) whose ink leaves that column.

Usage:
    python3 scripts/check_formula_fit.py doc.pdf [more.pdf ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

TOLERANCE_PT = 1.5
# Margin bands (running header / page number) legitimately sit outside the
# body column, so they are excluded from both the column estimate and the scan.
HEADER_BAND_PT = 70.0
FOOTER_BAND_PT = 775.0


def require_pymupdf():
    try:
        import pymupdf  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(f"ERROR: pymupdf is required for this check: {exc}")
    return pymupdf


def body_column(pymupdf, doc) -> tuple[float, float] | None:
    """Derive the body text column once for the whole document.

    A per-page estimate is too tight: a page whose last line is short would make
    the column look narrower than it is and flag every full-width rule on it.
    The column is a property of the page template, so it is measured across all
    pages and reused.
    """
    left, right = None, None
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if not span.get("text", "").strip():
                        continue
                    x0, y0, x1, y1 = span["bbox"]
                    if y0 < HEADER_BAND_PT or y1 > FOOTER_BAND_PT:
                        continue
                    left = x0 if left is None else min(left, x0)
                    right = x1 if right is None else max(right, x1)
    if left is None or right is None or right - left < 200:
        return None
    return left, right


def check(pdf: Path) -> list[str]:
    pymupdf = require_pymupdf()
    issues: list[str] = []
    doc = pymupdf.open(str(pdf))
    column = body_column(pymupdf, doc)
    if column is None:
        doc.close()
        return issues
    left, right = column
    for pno in range(doc.page_count):
        page = doc[pno]
        worst = None
        for dr in page.get_drawings():
            r = dr["rect"]
            if r.is_empty:
                continue
            if r.width > 400 and r.height > 700:      # page background
                continue
            if r.y1 < HEADER_BAND_PT or r.y0 > FOOTER_BAND_PT:
                continue
            overflow = max(r.x1 - right, left - r.x0)
            if overflow > TOLERANCE_PT and (worst is None or overflow > worst[0]):
                worst = (overflow, r)
        if worst:
            overflow, r = worst
            issues.append(
                f"p{pno + 1}: content crosses the text column by {overflow:.1f}pt "
                f"(ink x=[{r.x0:.1f}, {r.x1:.1f}] vs column [{left:.1f}, {right:.1f}])"
            )
    doc.close()
    return issues


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv if not a.startswith("-")]
    if not paths:
        print("ERROR: usage: check_formula_fit.py doc.pdf [more.pdf ...]")
        return 2
    failures = 0
    for pdf in paths:
        if not pdf.is_file():
            print(f"ERROR: {pdf}: file not found")
            failures += 1
            continue
        issues = check(pdf)
        if issues:
            failures += 1
            print(f"ERROR: {pdf}: {len(issues)} page(s) with content outside the text column")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"OK: {pdf}: every page keeps its ink inside the text column")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
