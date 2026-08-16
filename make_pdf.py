#!/usr/bin/env python3
"""Render report/REPORT.md to a submission-ready PDF.

Markdown -> standalone HTML -> Chrome headless print-to-PDF. Chosen because it
needs no system packages: a LaTeX toolchain is a multi-GB install and pandoc,
weasyprint and wkhtmltopdf are all absent here, whereas Chrome ships on the
machine already. Everything else is one small pure-Python dependency.

Two things this does that a naive conversion would not:

- **Strips HTML comments.** The template's guidance text lives in comments and
  must not reach the submitted PDF.
- **Inlines images as data URIs**, so report/REPORT.html is a single portable
  file and Chrome cannot silently drop a figure over a path problem.

Usage:  python make_pdf.py [--open]
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import re
import subprocess
import sys
from pathlib import Path

import markdown

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: Letter; margin: 0.9in 0.95in; }

html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  font-family: "Charter", "Palatino", "Palatino Linotype", Georgia, serif;
  font-size: 10.5pt; line-height: 1.45; color: #111; margin: 0;
  hyphens: auto; text-align: justify;
}

h1 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 19pt; line-height: 1.2; margin: 0 0 0.6em; text-align: left;
  letter-spacing: -0.01em;
}
h2 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 13pt; margin: 1.5em 0 0.45em; text-align: left;
  border-bottom: 1px solid #ddd; padding-bottom: 0.15em;
}
h3 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 11pt; margin: 1.2em 0 0.35em; text-align: left;
}
h1, h2, h3 { break-after: avoid; }
p { margin: 0 0 0.55em; orphans: 2; widows: 2; }

/* Figures: keep the image with the caption that follows it. */
p:has(> img) { text-align: center; margin: 1em 0 0.35em; break-inside: avoid; break-after: avoid; }
img { max-width: 100%; height: auto; }
p:has(> img) + p {
  font-size: 9pt; line-height: 1.35; color: #333; text-align: left;
  margin: 0 0 1.2em; padding-left: 0.1in; border-left: 2px solid #e3e3e3;
  padding-left: 0.55em; break-before: avoid;
}

blockquote {
  margin: 0.7em 0; padding: 0.15em 0 0.15em 0.8em;
  border-left: 2.5px solid #ccc; color: #333; font-size: 9.8pt;
  break-inside: avoid; text-align: left;
}
blockquote p { margin: 0 0 0.35em; }

code {
  font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 0.86em;
  background: #f4f4f2; padding: 0.08em 0.28em; border-radius: 3px;
}
pre {
  background: #f7f7f5; border: 1px solid #e6e6e2; border-radius: 4px;
  padding: 0.6em 0.75em; overflow-x: auto; break-inside: avoid;
  font-size: 8.6pt; line-height: 1.35; white-space: pre-wrap; word-wrap: break-word;
}
pre code { background: none; padding: 0; font-size: 1em; }

table {
  border-collapse: collapse; width: 100%; margin: 0.7em 0 1em;
  font-size: 9.2pt; break-inside: avoid;
}
th, td { border: 1px solid #ddd; padding: 0.28em 0.5em; text-align: left; vertical-align: top; }
th { background: #f4f4f2; font-weight: 600; }

/* The author block: first table on the page, deliberately plain. */
body > table:first-of-type { width: auto; margin: 0 0 0.8em; font-size: 10pt; }
body > table:first-of-type th { background: none; border: none;
  border-bottom: 1px solid #ccc; padding-left: 0; }
body > table:first-of-type td { border: none; padding-left: 0; padding-right: 1.6em; }

ol, ul { margin: 0 0 0.6em; padding-left: 1.3em; }
li { margin-bottom: 0.2em; }
a { color: #14507a; text-decoration: none; }
hr { border: none; border-top: 1px solid #ddd; margin: 1.4em 0; }
"""


def inline_images(html: str, base: Path) -> str:
    """Replace <img src="..."> with data URIs so the HTML stands alone."""
    def repl(m: re.Match) -> str:
        src = m.group(1)
        if src.startswith(("data:", "http://", "https://")):
            return m.group(0)
        path = (base / src).resolve()
        if not path.exists():
            sys.exit(f"missing image referenced by the report: {path}")
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        b64 = base64.b64encode(path.read_bytes()).decode()
        return f'<img src="data:{mime};base64,{b64}"'
    return re.sub(r'<img src="([^"]+)"', repl, html)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="open the PDF when done")
    ap.add_argument("--src", type=Path, default=Path("report/REPORT.md"))
    args = ap.parse_args()

    src = args.src
    text = src.read_text()

    # Guidance text lives in HTML comments and must never reach the PDF.
    stripped = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    n_comments = len(re.findall(r"<!--.*?-->", text, flags=re.S))

    body = markdown.markdown(
        stripped,
        extensions=["tables", "fenced_code", "sane_lists", "smarty"],
    )
    body = inline_images(body, src.parent)

    title = "Out of Sight, Out of Mind"
    html = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>")

    html_path = src.with_suffix(".html")
    html_path.write_text(html)
    print(f"  wrote {html_path}  ({n_comments} guidance comments stripped)")

    pdf_path = src.with_suffix(".pdf")
    if not Path(CHROME).exists():
        sys.exit(f"Chrome not found at {CHROME}; open {html_path} and print to PDF manually")
    subprocess.run([
        CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={pdf_path.resolve()}", html_path.resolve().as_uri(),
    ], check=True, capture_output=True)
    print(f"  wrote {pdf_path}")

    if args.open:
        subprocess.run(["open", str(pdf_path)], check=False)


if __name__ == "__main__":
    main()
