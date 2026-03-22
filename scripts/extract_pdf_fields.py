#!/usr/bin/env python3
"""Extract editable form field names from a PDF and write them to a text file.

Usage:
    python scripts/extract_pdf_fields.py path/to/file.pdf [output.txt]

If output is omitted, prints to stdout.

This is useful for generating a list like `form_fields_pdf.txt` which lists the
interactive form fields in a PDF (AcroForm fields).

The output format is:
    Page <n>:
      <field name> (<field type>)

The script tries to match fields to the page where they are referenced.
"""

import argparse
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    raise SystemExit(
        "pypdf is required. Install with: pip install pypdf"
    )


FIELD_TYPE_MAP = {
    "/Btn": "Button",
    "/Tx": "Text",
    "/Ch": "Choice",
    "/Sig": "Signature",
    "/Sb": "Button (checkbox/radio)",
}


def get_field_type(field_dict):
    ft = field_dict.get("/FT")
    if not ft:
        return "Unknown"
    return FIELD_TYPE_MAP.get(ft, ft)


def main():
    parser = argparse.ArgumentParser(description="Extract PDF form field names into a TXT list")
    parser.add_argument("pdf", type=Path, help="Path to the PDF file")
    parser.add_argument("out", type=Path, nargs="?", help="Optional output text file")
    args = parser.parse_args()

    if not args.pdf.exists():
        raise SystemExit(f"PDF not found: {args.pdf}")

    reader = PdfReader(str(args.pdf))

    # Map /Annots object ids to page numbers
    page_for_annot = {}
    for pi, page in enumerate(reader.pages, start=1):
        annots = page.get("/Annots")
        if not annots:
            continue
        for a in annots:
            try:
                key = a.get_object().indirect_reference
            except Exception:
                key = getattr(a, "idnum", None)
            if key is not None:
                page_for_annot[key] = pi

    # Get form fields
    fields = reader.get_fields() or {}

    # Build output per page (ordered)
    per_page = {}
    for name, f in fields.items():
        if not isinstance(f, dict):
            continue
        field_name = name
        field_type = get_field_type(f)

        # Try to find page if possible
        page_num = None
        # Some field dictionaries may include /P (page reference)
        if "/P" in f:
            try:
                page_num = reader.get_object(f["/P"]).indirect_reference
            except Exception:
                page_num = None
        # Fallback: try match via annotation id
        if page_num is None:
            ref = getattr(f, "indirect_reference", None)
            if ref is not None:
                page_num = page_for_annot.get(ref)

        if page_num is None:
            page_num = 0

        per_page.setdefault(page_num, []).append((field_name, field_type))

    out_lines = []
    for page in sorted(per_page.keys()):
        heading = f"Page {page}:" if page != 0 else "Page (unknown):"
        out_lines.append(heading)
        for field_name, field_type in sorted(per_page[page], key=lambda x: x[0].lower()):
            # Use repr() so trailing spaces (and other whitespace) are visible in the output.
            out_lines.append(f"  {repr(field_name)} ({field_type})")
        out_lines.append("")

    out_txt = "\n".join(out_lines).rstrip() + "\n"

    if args.out:
        args.out.write_text(out_txt, encoding="utf-8")
    else:
        print(out_txt)


if __name__ == "__main__":
    main()
