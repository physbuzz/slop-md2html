#!/usr/bin/env python3
"""Enforce transfer-size and static-MathJax budgets on the stress page."""

from __future__ import annotations

import argparse
import gzip
from pathlib import Path
import re


def size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    return len(data), len(gzip.compress(data, compresslevel=9))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    page = args.root / "2026/05/18/gaussianintegral.html"
    css = args.root / "assets/md2html/mathjax-chtml.css"
    site_css = (args.root / "css/main.css").read_text(encoding="utf-8")
    md2html_css = (args.root / "css/md2html.css").read_text(encoding="utf-8")
    fonts = sorted((args.root / "assets/md2html/mathjax/woff2").glob("*.woff2"))
    page_raw, page_gzip = size(page)
    css_raw, css_gzip = size(css)
    font_bytes = sum(path.stat().st_size for path in fonts)
    text = page.read_text(encoding="utf-8")
    styles = css.read_text(encoding="utf-8")
    glyph_rules = len(re.findall(r"mjx-c\.mjx-c", styles))
    preload_names = re.findall(r'rel="preload"[^>]+/([^/"?]+\.woff2)', text)
    preload_bytes = sum((args.root / "assets/md2html/mathjax/woff2" / name).stat().st_size for name in preload_names)
    initial_math_bytes = page_gzip + css_gzip + preload_bytes
    checks = {
        "HTML raw <= 560 KB": page_raw <= 560_000,
        "HTML gzip <= 38 KB": page_gzip <= 38_000,
        "CHTML CSS gzip <= 10 KB": css_gzip <= 10_000,
        "initial math payload <= 255 KB": initial_math_bytes <= 255_000,
        "complete shared fonts <= 350 KB": 20 <= len(fonts) <= 30 and font_bytes <= 350_000,
        "page font preloads <= 10": len(preload_names) <= 10,
        "glyph metrics present": glyph_rules >= 100,
        "fonts are local": "cdn.jsdelivr.net/npm/@mathjax/mathjax-tex-font" not in styles,
        "hash guard precedes styles": text.find("data-hash-pending") < text.find('rel="stylesheet"'),
        "CHTML styles precede site script": text.find("mathjax-chtml.css") < text.find("site.js"),
        "site script is deferred": '<script defer src="/js/site.js"></script>' in text,
        "reader :has() selectors stay bounded": site_css.count(":has(") == 8 and site_css.count("html:has(#reader-") == 8,
        "Directory keeps the compact shared rhythm": all(rule in md2html_css for rule in (
            ".post-content h2#directory {\n  margin: 1rem 0 0.5rem;\n  font-size: 1.8rem;",
            ".post-content h2#directory + ul {\n  margin: 0;\n  padding-left: 20px;\n  font-size: 0.9rem;\n  line-height: 1;",
            ".post-content h2#directory + ul li,",
            "margin-bottom: 2px;",
        )),
        "text-size control present": text.count('name="reader-text"') == 3,
        "reader widget is native HTML": '<details class="reader-widget">' in text and '<form aria-label="Reader controls">' in text,
        "content visible without JavaScript": not re.search(r"<html\b[^>]*(?:data-hash-pending|class=[\"'][^\"']*js)", text),
    }
    print(f"HTML       {page_raw:>7} raw  {page_gzip:>6} gzip")
    print(f"CHTML CSS  {css_raw:>7} raw  {css_gzip:>6} gzip  {glyph_rules} glyph rules")
    print(f"fonts      {font_bytes:>7} bytes  {len(fonts)} files  {len(preload_names)} page preloads ({preload_bytes} bytes)")
    print(f"math load  {initial_math_bytes:>7} bytes before content images")
    failed = [label for label, passed in checks.items() if not passed]
    for label, passed in checks.items():
        print(f"{'ok' if passed else 'FAIL':>4}  {label}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
