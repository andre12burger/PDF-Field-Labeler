#!/usr/bin/env python3
"""Extract PDF form field metadata with page/position/type for mapping. """

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypdf import PdfReader

TYPE_LABELS = {
    "/Tx": "text",
    "/Btn": "checkbox",
    "/Ch": "choice",
    "/Sig": "signature",
}


def norm_type(ft):
    if isinstance(ft, str):
        return TYPE_LABELS.get(ft, ft.strip("/"))
    return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Extract PDF form field metadata.")
    parser.add_argument("input_pdf", type=Path, help="Input PDF")
    parser.add_argument("output_json", type=Path, help="Output JSON")
    args = parser.parse_args()

    if not args.input_pdf.exists():
        raise SystemExit("Input PDF not found")

    pdf = PdfReader(str(args.input_pdf))
    result = []

    def maybe_num(v):
        try:
            return float(v)
        except Exception:
            return None

    for page_num, page in enumerate(pdf.pages, start=1):
        annots = page.get("/Annots") or []
        for ann in annots:
            try:
                w = ann.get_object()
            except Exception:
                continue
            name = w.get("/T")
            if not name:
                continue
            typ = norm_type(w.get("/FT"))
            rect = w.get("/Rect") or []
            x = None
            y = None
            wdt = None
            hgt = None
            if isinstance(rect, list) and len(rect) == 4:
                x, y, x2, y2 = [maybe_num(rc) for rc in rect]
                if x is not None and y is not None and x2 is not None and y2 is not None:
                    wdt = x2 - x
                    hgt = y2 - y
            v = w.get("/V")
            asv = w.get("/AS")
            # normalize bytes
            if isinstance(name, bytes):
                name = name.decode("utf-8", errors="ignore")
            if isinstance(v, bytes):
                v = v.decode("utf-8", errors="ignore")
            if isinstance(asv, bytes):
                asv = asv.decode("utf-8", errors="ignore")

            result.append({
                "page": page_num,
                "name": name,
                "type": typ,
                "x": x,
                "y": y,
                "width": wdt,
                "height": hgt,
                "value": v,
                "appearanceState": asv,
            })

    # Sort by page desc y??, by page and y desc to match visual top-down
    def sort_key(item):
        return (item["page"], -(item["y"] or 0), item["x"] or 0)

    result.sort(key=sort_key)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(result)} fields to {args.output_json}")


if __name__ == "__main__":
    main()
