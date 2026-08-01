#!/usr/bin/env python3
"""GB/T 7714 reference formatter (N6).

Never invent references: use this ONLY with metadata from an actual source
(scholar plugin result, publisher page, or the book/paper itself).

Single entry:
    python gb7714.py --type journal --authors "Torrieri D J" \
        --title "Statistical theory of passive location systems" \
        --venue "IEEE Transactions on Aerospace and Electronic Systems" \
        --year 1984 --volume "AES-20" --issue 2 --pages "183-198"

Batch (JSON list, numbered output):
    python gb7714.py --json refs.json
    # refs.json: [{"type":"book","authors":"姜启源, 谢金星, 叶俊","title":"数学模型",
    #              "place":"北京","publisher":"高等教育出版社","year":"2018"}, ...]
"""
import argparse
import json
import sys

TYPES = {"book": "M", "journal": "J", "conference": "C", "web": "EB/OL",
         "thesis": "D"}


def format_entry(d: dict) -> str:
    t = d.get("type", "journal")
    a = d.get("authors", "").rstrip(".")
    title = d.get("title", "").rstrip(".")
    year = d.get("year", "")
    if t == "book":
        return f"{a}. {title}[M]. {d.get('place', '')}: {d.get('publisher', '')}, {year}."
    if t == "journal":
        vi = d.get("volume", "") + (f"({d['issue']})" if d.get("issue") else "")
        return f"{a}. {title}[J]. {d.get('venue', '')}, {year}, {vi}: {d.get('pages', '')}."
    if t == "conference":
        return (f"{a}. {title}[C]//{d.get('venue', '')}. {d.get('place', '')}: "
                f"{d.get('publisher', '')}, {year}: {d.get('pages', '')}.")
    if t == "web":
        cited = d.get("cited", "")
        return f"{a}. {title}[EB/OL]. ({d.get('date', year)})[{cited}]. {d.get('url', '')}."
    if t == "thesis":
        return f"{a}. {title}[D]. {d.get('place', '')}: {d.get('publisher', '')}, {year}."
    raise ValueError(f"unknown type: {t}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", choices=list(TYPES), help="entry type")
    ap.add_argument("--authors")
    ap.add_argument("--title")
    ap.add_argument("--venue", help="journal/conference name")
    ap.add_argument("--place")
    ap.add_argument("--publisher")
    ap.add_argument("--year")
    ap.add_argument("--volume")
    ap.add_argument("--issue")
    ap.add_argument("--pages")
    ap.add_argument("--date", help="web: publish date YYYY-MM-DD")
    ap.add_argument("--cited", help="web: citation date YYYY-MM-DD")
    ap.add_argument("--url")
    ap.add_argument("--json", help="batch mode: JSON list of entries")
    args = ap.parse_args()

    if args.json:
        items = json.loads(open(args.json, encoding="utf-8").read())
        for i, d in enumerate(items, 1):
            print(f"[{i}] {format_entry(d)}")
        return 0
    if not args.type or not args.authors or not args.title:
        ap.error("--type/--authors/--title required (or use --json)")
    d = {k: v for k, v in vars(args).items() if v is not None and k != "json"}
    print(format_entry(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
