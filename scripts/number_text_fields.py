#!/usr/bin/env python3
"""Generate a numbered mapping for PDF text fields (and report field types).

This script reads the form fields from a PDF and produces a JSON report that:
- groups fields by their AcroForm type (Text/Button/Choice/etc)
- assigns a sequential number to each Text field (1,2,3...)
- optionally writes a mapping file (oldName -> newName) that can be used with
  normalize_pdf_fields.py to rename the fields inside the PDF.

Usage:
    python scripts/utils/number_text_fields.py <input.pdf> <out.json>

Example:
    python scripts/utils/number_text_fields.py \
        data/pdf/CharacterSheet_DnD5e.pdf \
        scripts/pdf-field-report.json

Optional:
    --prefix <prefix>        Prefix for the generated text-field name (default: "")
    --sep <sep>              Separator between name and number (default: "_")
    --start <n>              Starting index for numbering (default: 1)
    --map <out.json>         Output a mapping file (oldName -> newName) for text fields.
    --apply <out.pdf>        Write a new PDF with names renamed using the generated mapping.
    --dry-run                Do not write output PDF, just print what would change.

The report JSON format is:
{
  "fields": [ {"name": ..., "type": ..., "newName": ...?}, ... ],
  "counts": {"Text": 123, "Button": 45, ...}
}


Example:

python scripts/utils/number_text_fields.py  `
  data/pdf/CharacterSheet_DnD5e.pdf  `
  scripts/pdf-field-report.json  `
  --map scripts/pdf-field-map.json  `
  --apply data/pdf/CharacterSheet_numbered.pdf  `
  --fill

"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject, TextStringObject
except ImportError as e:
    raise SystemExit("pypdf is required. Install with: pip install pypdf") from e


FIELD_TYPE_MAP = {
    "/Btn": "Button",
    "/Tx": "Text",
    "/Ch": "Choice",
    "/Sig": "Signature",
    "/Sb": "Button",
}


def get_field_type(field_dict: dict) -> str:
    ft = field_dict.get("/FT")
    if not ft:
        return "Unknown"
    return FIELD_TYPE_MAP.get(ft, str(ft))


def get_field_page(field_dict: dict, page_for_annot: dict[str, int]) -> int:
    # Try /P then annotation reference
    page_num = None
    if "/P" in field_dict:
        try:
            page_num = field_dict["/P"].indirect_reference
        except Exception:
            page_num = None
    if page_num is None:
        ref = getattr(field_dict, "indirect_reference", None)
        if ref is not None:
            page_num = page_for_annot.get(ref)
    return page_num or 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Number text fields and report PDF form field types.")
    parser.add_argument("input_pdf", type=Path, help="Input PDF path")
    parser.add_argument("out_json", type=Path, help="Output JSON report path")
    parser.add_argument("--prefix", default="", help="Prefix for generated text-field names")
    parser.add_argument("--sep", default="_", help="Separator between name and number")
    parser.add_argument("--start", type=int, default=1, help="Starting index for numbering")
    parser.add_argument("--map", type=Path, help="Optional output mapping JSON (oldName->newName) for text fields")
    parser.add_argument("--apply", type=Path, help="Optional output PDF path to apply the mapping")
    parser.add_argument("--fill", action="store_true", help="Fill text fields with their assigned value (by default, the field name) in the output PDF")
    parser.add_argument("--fill-template", default="{name}", help="Template used to fill text fields: {name} and {num} are available.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output PDF, just print what would change")
    args = parser.parse_args()

    if not args.input_pdf.exists():
        raise SystemExit(f"Input PDF not found: {args.input_pdf}")

    reader = PdfReader(str(args.input_pdf))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    fields = writer.get_fields() or {}

    # Build a map from annotation -> page number so we can sort by page.
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

    report = {"fields": [], "counts": {}}
    mapping = {}

    # Number the Text fields in page order, and capture the rectangle for all fields.
    def get_rect(field_dict: dict):
        rect = field_dict.get("/Rect")
        if not rect or len(rect) != 4:
            return None
        try:
            return [float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])]
        except Exception:
            return None

    # Build a list of (page, y, x, name, field) for ordering by page and position.
    sortable = []
    for old_name, field in fields.items():
        if not isinstance(old_name, str):
            continue
        page_num = get_field_page(field, page_for_annot)
        rect = get_rect(field)
        # sort by page, then top->bottom (descending y), then left->right (ascending x)
        if rect:
            x0, y0, x1, y1 = rect
            y = max(y0, y1)
            x = min(x0, x1)
        else:
            y = 0
            x = 0
        sortable.append((page_num, -y, x, old_name, field, rect))

    sortable.sort(key=lambda x: (x[0], x[1], x[2], x[3]))

    text_counter = args.start

    for page_num, _, _, old_name, field, rect in sortable:
        field_type = get_field_type(field)
        report["counts"][field_type] = report["counts"].get(field_type, 0) + 1

        entry = {"name": old_name, "type": field_type, "page": page_num}
        if rect is not None:
            entry["rect"] = rect

        if field_type == "Text":
            new_name = f"{args.prefix}{old_name}{args.sep}{text_counter}"
            entry["newName"] = new_name
            mapping[old_name] = new_name
            text_counter += 1

        report["fields"].append(entry)

    # Write report JSON
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote report to {args.out_json} ({len(report['fields'])} fields)")

    if args.map:
        args.map.parent.mkdir(parents=True, exist_ok=True)
        args.map.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote mapping to {args.map} ({len(mapping)} text fields)")

    if args.apply:
        if args.dry_run:
            print(f"Dry run: would write PDF to {args.apply} (not writing)")
            return

        # Optionally fill text fields with their assigned number (and name)
        if args.fill:
            values = {}
            for old_name, field in fields.items():
                if not isinstance(old_name, str):
                    continue
                field_type = get_field_type(field)
                if field_type != "Text":
                    continue
                new_name = mapping.get(old_name)
                if not new_name:
                    continue
                m = re.search(r"(\d+)$", new_name)
                if not m:
                    continue
                num = m.group(1)
                values[old_name] = args.fill_template.format(name=old_name, num=num)

            # Update all pages with the values dict
            for page in writer.pages:
                try:
                    writer.update_page_form_field_values(page, values)
                except Exception:
                    pass

        # Apply mapping to create a new PDF (rename fields)
        for old_name, new_name in mapping.items():
            field = fields.get(old_name)
            if not field:
                continue
            if "/T" in field:
                field[NameObject("/T")] = TextStringObject(new_name)

        args.apply.parent.mkdir(parents=True, exist_ok=True)
        with open(args.apply, "wb") as f:
            writer.write(f)
        print(f"Wrote PDF with updated field names to {args.apply}")


if __name__ == "__main__":
    main()
