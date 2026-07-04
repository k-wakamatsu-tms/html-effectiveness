#!/usr/bin/env python3
"""Verify that a ja/ translation preserves the structure of its English source.

Usage: python verify_translation.py <english.html> <japanese.html>

Checks:
  1. <html lang="ja"> is set in the translation
  2. Open/close tag counts match the English source (structure preserved)
  3. href/src attribute values are identical as a multiset (links unchanged)
  4. The translation actually contains Japanese text
  5. The leading copyright comment is preserved verbatim

Exit code 0 = all checks pass, 1 = at least one failure.
"""
import re
import sys
from collections import Counter

TAGS = [
    "div", "span", "section", "header", "footer", "article", "main", "nav",
    "button", "table", "thead", "tbody", "tr", "td", "th", "ul", "ol", "li",
    "p", "a", "svg", "script", "style", "form", "label", "input", "select",
    "textarea", "h1", "h2", "h3", "h4", "h5", "h6",
]

JA_CHARS = re.compile(r"[぀-ヿ一-鿿]")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def tag_counts(html):
    counts = {}
    for t in TAGS:
        opens = len(re.findall(rf"<{t}(?=[\s>/])", html))
        closes = len(re.findall(rf"</{t}\s*>", html))
        counts[t] = (opens, closes)
    return counts


def links(html):
    return Counter(re.findall(r'(?:href|src)\s*=\s*"([^"]*)"', html))


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    en_path, ja_path = sys.argv[1], sys.argv[2]
    en, ja = read(en_path), read(ja_path)
    failures = []

    if not re.search(r'<html[^>]*\blang\s*=\s*"ja"', ja):
        failures.append('lang="ja" is not set on <html>')

    en_tags, ja_tags = tag_counts(en), tag_counts(ja)
    for t in TAGS:
        if en_tags[t] != ja_tags[t]:
            failures.append(
                f"<{t}> count mismatch: en(open={en_tags[t][0]},close={en_tags[t][1]}) "
                f"ja(open={ja_tags[t][0]},close={ja_tags[t][1]})"
            )

    en_links, ja_links = links(en), links(ja)
    if en_links != ja_links:
        missing = en_links - ja_links
        extra = ja_links - en_links
        if missing:
            failures.append(f"links missing in ja: {sorted(missing)}")
        if extra:
            failures.append(f"unexpected links in ja: {sorted(extra)}")

    ja_char_count = len(JA_CHARS.findall(ja))
    if ja_char_count < 20:
        failures.append(
            f"translation contains almost no Japanese text ({ja_char_count} JP chars)"
        )

    en_copyright = re.search(r"<!--.*?Copyright.*?-->", en)
    if en_copyright and en_copyright.group(0) not in ja:
        failures.append("leading copyright comment was altered or removed")

    if failures:
        print(f"FAIL: {ja_path}")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print(f"PASS: {ja_path} ({ja_char_count} JP chars)")


if __name__ == "__main__":
    main()
