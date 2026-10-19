#!/usr/bin/env python3
"""Formula symbol-completeness gate for Kami documents.

Rule (see ``SKILL.md`` › "LaTeX mathematics gate"): every letter, Greek letter
and named symbol (``\\mathrm{MSE}``, ``\\text{Params}``, ``IoU``) that appears in
a display formula must be explained in a per-formula legend rendered right
after it::

    <div class="latex-display" data-latex="..."></div>
    <div class="sym-list">
      <div class="sym-list-label">式中符号</div>
      <ul>
        <li><span class="sym-key"><span class="latex-inline" data-latex="x"></span></span>
            <span class="sym-def">…</span></li>
      </ul>
    </div>

A display formula that repeats an earlier formula verbatim (appendix recap)
inherits the earlier legend and is not asked for a second one.

``parse_symbols`` is also the library used by project-side build scripts, so the
extractor has exactly one implementation.

CLI:
  python3 scripts/check_symbols.py --check filled-source.html
  python3 scripts/check_symbols.py --dump  filled-source.html
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

GREEK = {"alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta", "eta",
         "theta", "vartheta", "iota", "kappa", "lambda", "mu", "nu", "xi", "pi",
         "rho", "sigma", "tau", "upsilon", "phi", "varphi", "chi", "psi", "omega",
         "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon",
         "Phi", "Psi", "Omega"}

# Symbol-like commands that are not letters but must be explained.
NAMED = {"top", "infty", "partial", "nabla", "ell"}

# Multi-letter sub/superscripts explained as one word; also used for prose runs.
WORDS = {"in", "out", "eff", "cls", "reg", "det", "box", "gt", "pred", "target",
         "param", "params", "flops", "macs", "var", "bias", "top", "obj", "pix",
         "anc", "bg", "fg", "pos", "neg", "loc", "conf", "seg", "mask",
         "model", "dim", "iter", "head", "new", "per", "avg", "std"}

# Units that follow a number (``4pt``, ``8px``, ``16ms``) are not symbols.
UNITS = {"pt", "px", "ms", "us", "ns", "db", "kb", "mb", "gb", "mm", "cm", "km",
         "kg", "fps", "hz", "kb", "gflops"}

DISPLAY_RE = re.compile(
    r'<(?P<tag>span|div)\s+class="latex-display"\s+data-latex="(?P<tex>[^"]*)"\s*>.*?</(?P=tag)>',
    re.S)
INLINE_RE = re.compile(
    r'<(?P<tag>span|div)\s+class="latex-inline"\s+data-latex="(?P<tex>[^"]*)"\s*>.*?</(?P=tag)>',
    re.S)
ITEM_RE = re.compile(r'<li\s*>(.*?)</li>', re.S)
KEY_RE = re.compile(r'class="sym-key"\s*>(.*?)</span>\s*<span\s+class="sym-def"', re.S)
# greedy: an item is already <li>-bounded, and a meaning may contain inline spans
DEF_RE = re.compile(r'<span\s+class="sym-def"\s*>(.*)</span>', re.S)


def _brace(s: str, i: int) -> tuple[str, int]:
    """s[i] == '{' → (content, index after the closing brace)."""
    depth, j = 1, i + 1
    while j < len(s) and depth:
        if s[j] == "\\":
            j += 2
            continue
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
        j += 1
    return s[i + 1:j - 1], j


def _wordlike(arg: str) -> bool:
    """Only real named symbols (MSE, Params, IoU) count; skip prose/pseudocode."""
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9 _\-]*", arg.strip()))


def parse_symbols(tex: str) -> list[str]:
    """Symbols of ``tex`` that a reader must be able to decode, in source order."""
    out: list[str] = []

    def walk(s: str) -> None:
        def add(key: str) -> None:
            if key and key not in out:
                out.append(key)

        i = 0
        while i < len(s):
            c = s[i]
            if c == "\\":
                m = re.match(r"\\([A-Za-z]+)", s[i:])
                if not m:
                    i += 2
                    continue
                cmd = m.group(1)
                i += 1 + len(cmd)
                if cmd in GREEK or cmd in NAMED:
                    add("\\" + cmd)
                    continue
                if cmd in ("begin", "end"):
                    _arg, i = _brace(s, i) if i < len(s) and s[i] == "{" else ("", i)
                    continue                       # \begin{cases} 的环境名不是符号
                if cmd in ("mathrm", "mathcal", "mathbf", "mathit", "mathsf",
                           "boldsymbol", "bm", "operatorname", "text",
                           "textnormal", "textup", "textbf", "textrm"):
                    arg, i = _brace(s, i) if i < len(s) and s[i] == "{" else ("", i)
                    if _wordlike(arg):
                        add(arg.strip())
                    continue
                continue  # structural / spacing command
            if c in "_^" and i + 1 < len(s) and s[i + 1] == "{":
                arg, i = _brace(s, i + 1)
                if len(arg) > 2 and re.fullmatch(r"[A-Za-z]+", arg):
                    add(arg)                       # _{anchor} / _{coord} / ^{LS}：整词
                elif len(arg) > 1 and re.fullmatch(r"[A-Za-z]+", arg) and \
                        (arg.upper() == arg or arg.lower() in WORDS):
                    add(arg)
                else:
                    walk(arg)                      # _{ij}：两个索引，分开解释
                continue
            if c == "{":
                arg, i = _brace(s, i)
                walk(arg)
                continue
            if c.isascii() and c.isalpha():
                run = re.match(r"[A-Za-z]+", s[i:]).group(0)
                if run.lower() in UNITS:
                    i += len(run)                  # 4pt / 8px：单位不是符号
                    continue
                if len(run) > 1 and (run.upper() == run or run.lower() in WORDS):
                    add(run)
                    i += len(run)
                else:
                    add(c)
                    i += 1
                continue
            i += 1

    walk(tex)
    return out


def _visible(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def parse_legend(block: str) -> tuple[set[str], list[str]]:
    """Return (covered symbols, keys whose meaning is empty)."""
    covered: set[str] = set()
    empty: list[str] = []
    for item in ITEM_RE.findall(block):
        key_html = KEY_RE.search(item)
        def_html = DEF_RE.search(item)
        if not key_html or not def_html:
            continue
        keys: set[str] = set()
        for m in INLINE_RE.finditer(key_html.group(1)):
            tex = html.unescape(m.group("tex")).strip()
            # 键本身也算覆盖：`MaxPool` 这类混合大小写名字按字母拆开会失配，
            # 键写成裸词或 \text{MaxPool} 都应当成立。
            keys |= {tex} | set(parse_symbols(tex))
        covered |= keys
        if len(_visible(def_html.group(1))) < 2:
            empty.append(sorted(keys)[0] if keys else "?")
    return covered, empty


def check_html(path: Path, require_legend: bool = True) -> list[str]:
    text = path.read_text(encoding="utf-8")
    token_re = re.compile(
        r'(?P<display><(?P<dtag>span|div)\s+class="latex-display"\s+data-latex="(?P<tex>[^"]*)"\s*>.*?</(?P=dtag)>)'
        r'|(?P<legend><div\s+class="sym-list[^"]*"\s*>.*?</ul>\s*</div>)', re.S)
    failures: list[str] = []
    pending: list[tuple[str, str]] = []          # (normalized tex, label)
    seen: dict[str, set[str]] = {}               # tex → covered symbols
    explained: set[str] = set()
    n_display = n_legend = 0
    for m in token_re.finditer(text):
        if m.group("display"):
            n_display += 1
            tex = html.unescape(m.group("tex"))
            if not parse_symbols(tex):
                continue            # 纯数值 / 文字公式：没有字母需要解释
            pending.append((re.sub(r"\s+", "", tex), tex[:70]))
        else:
            n_legend += 1
            covered, empty = parse_legend(m.group("legend"))
            explained |= covered
            for key in empty:
                failures.append(f"图例符号 {key} 的说明为空")
            if pending:
                norm, _ = pending.pop()
                seen[norm] = covered
    for norm, label in pending:
        if not require_legend:
            continue
        if norm in seen:
            continue                              # appendix recap of an explained formula
        failures.append(f"显示公式缺少逐符号图例：{label}")
    # inline formulas must be explained somewhere in the document
    if require_legend:
        inline: set[str] = set()
        for m in INLINE_RE.finditer(text):
            inline |= set(parse_symbols(html.unescape(m.group("tex"))))
        orphan = sorted(inline - explained)
    else:
        orphan = []
    if orphan:
        failures.append("内联公式符号未在任何图例中解释：" + " ".join(orphan))
    return failures, n_display, n_legend, len(explained)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="filled-source HTML (LaTeX placeholders, before MathJax)")
    ap.add_argument("--check", action="store_true", help="gate mode (default)")
    ap.add_argument("--dump", action="store_true", help="print every display formula with its required symbols")
    ap.add_argument("--no-legend-required", action="store_true")
    ap.add_argument("--allow-no-formulas", action="store_true",
                    help="pass even when no LaTeX placeholder is found (documents without math)")
    args = ap.parse_args()
    path = Path(args.path)
    if args.dump:
        text = path.read_text(encoding="utf-8")
        for m in DISPLAY_RE.finditer(text):
            tex = html.unescape(m.group("tex"))
            print(f"--- {tex}")
            print("    " + "  ".join(f'("{s}", "")' for s in parse_symbols(tex)))
        return 0
    failures, n_display, n_legend, n_sym = check_html(path, not args.no_legend_required)
    if n_display == 0 and not args.allow_no_formulas:
        print("符号门禁无法判定：没有找到 LaTeX 占位符。请在 MathJax 转换前的 filled-source.html 上运行，"
              "或加 --allow-no-formulas 显式跳过。")
        return 1
    if failures:
        print(f"符号门禁失败：{len(failures)} 处")
        for f in failures[:60]:
            print("  " + f)
        if len(failures) > 60:
            print(f"  … 另有 {len(failures) - 60} 处")
        return 1
    print(f"OK: 符号门禁通过 —— {n_display} 条显示公式 / {n_legend} 份图例 / {n_sym} 个已解释符号")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
