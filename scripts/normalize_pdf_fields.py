#!/usr/bin/env python3
"""Normalize / rename form field names in a PDF (AcroForm).

This script is useful when you want to "clean" the field names in a static fillable
PDF so that your code can target stable names (e.g. remove trailing spaces,
remove weird characters, make names consistent).

Usage:
    python scripts/normalize_pdf_fields.py <input.pdf> <output.pdf> [--map map.json] [--strategy STRATEGY] [--dry-run]

Examples:
    # Normalize whitespace (trim and collapse spaces)
    python scripts/normalize_pdf_fields.py data/CharacterSheet_DnD5e.pdf data/CharacterSheet_normalized.pdf

    # Use an explicit mapping file (JSON object: {"oldName": "newName"})
    python scripts/normalize_pdf_fields.py data/CharacterSheet_DnD5e.pdf data/CharacterSheet_normalized.pdf --map scripts/field-map.json

    # Dry-run: show what would change without writing
    python scripts/normalize_pdf_fields.py data/CharacterSheet_DnD5e.pdf /tmp/out.pdf --dry-run

Supported strategies:
  trim         - strip leading/trailing whitespace only
  normalize    - strip + collapse internal whitespace to a single space
  remove-spaces- remove all whitespace (spaces/tabs/newlines)

If both --map and --strategy are provided, the map wins for names it contains.

exemples (Windows PowerShell / cmd):

# One-line (recommended):
 python scripts/utils/normalize_pdf_fields.py data/pdf/CharacterSheet_DnD5e.pdf data/pdf/CharacterSheet_normalized.pdf --map scripts/pdf-field-map.json

# Multi-line (PowerShell):
python scripts/utils/normalize_pdf_fields.py `
    data/pdf/CharacterSheet_DnD5e.pdf `
    data/pdf/CharacterSheet_normalized.pdf `
    --generate-map scripts/pdf-field-map.json

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


def normalize_name(name: str, strategy: str) -> str:
    if strategy == "trim":
        return name.strip()
    if strategy == "normalize":
        return re.sub(r"\s+", " ", name.strip())
    if strategy == "remove-spaces":
        return re.sub(r"\s+", "", name)
    raise ValueError(f"Unknown strategy: {strategy}")


def get_field_page(field_dict: dict, page_for_annot: dict[str, int]) -> int:
    # Determine the page number for a field, using /P or annotation reference.
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
    parser = argparse.ArgumentParser(description="Normalize/rename PDF form field names.")
    parser.add_argument("input_pdf", type=Path, help="Input PDF path")
    parser.add_argument("output_pdf", type=Path, help="Output PDF path")
    parser.add_argument("--generate-map", type=Path, help="Generate a JSON mapping file of all fields (oldName -> newName).")
    parser.add_argument("--map", type=Path, help="Optional JSON file mapping oldName->newName to apply when renaming fields.")
    parser.add_argument("--strategy", default="normalize", choices=["trim", "normalize", "remove-spaces"], help="Normalization strategy used for generating names when map is not provided.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output file, just print what would change")
    parser.add_argument("--fill", action="store_true", help="Fill text fields with their new names in the output PDF")
    parser.add_argument("--fill-template", default="{name}", help="Template to use when filling text fields: {name} and {new} are available")
    parser.add_argument("--verify", action="store_true", help="Verify output PDF fields match the fill values from map/template")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    args = parser.parse_args()

    if not args.input_pdf.exists():
        raise SystemExit(f"Input PDF not found: {args.input_pdf}")

    reader = PdfReader(str(args.input_pdf))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    fields = writer.get_fields() or {}

    # If requested, emit a JSON map file with current names (and optionally normalized values).
    if args.generate_map:
        mapping = {}
        seen = set()

        # Prefer the AcroForm /Fields array order (this is the safe PDF-defined order).
        acro = reader.trailer["/Root"].get("/AcroForm")
        if acro:
            fields_arr = acro.get("/Fields")
            if fields_arr:
                try:
                    fields_arr = fields_arr.get_object()
                except Exception:
                    pass
                if isinstance(fields_arr, list):
                    for f in fields_arr:
                        try:
                            obj = f.get_object()
                        except Exception:
                            continue
                        name = obj.get("/T")
                        if isinstance(name, bytes):
                            try:
                                name = name.decode("utf-8")
                            except Exception:
                                name = name.decode("latin-1", errors="ignore")
                        if not isinstance(name, str) or not name or name in seen:
                            continue
                        seen.add(name)
                        mapping[name] = normalize_name(name, args.strategy)

        # Finally, include any remaining fields not in the AcroForm field array

        args.generate_map.parent.mkdir(parents=True, exist_ok=True)
        args.generate_map.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote mapping file with {len(mapping)} entries to {args.generate_map}")
        return

    mapping = {}
    if args.map:
        if not args.map.exists():
            raise SystemExit(f"Mapping file not found: {args.map}")
        mapping = json.loads(args.map.read_text(encoding="utf-8"))
        if not isinstance(mapping, dict):
            raise SystemExit("Mapping file must contain a JSON object of oldName->newName")

    # Build reverse map to detect collisions.
    new_name_to_old = {}  # newName -> oldName
    changes = []

    # Detect field rename operations (old -> new) without mutating page structure yet.
    for old_name, field in fields.items():
        if not isinstance(old_name, str):
            continue
        new_name = mapping.get(old_name)
        if new_name is None:
            new_name = normalize_name(old_name, args.strategy)

        if new_name == old_name:
            continue

        if new_name in new_name_to_old:
            # Collision: two old names want the same new name.
            existing = new_name_to_old[new_name]
            print(f"WARNING: collision: '{old_name}' and '{existing}' both map to '{new_name}'")
            continue

        new_name_to_old[new_name] = old_name
        changes.append((old_name, new_name))

    # Apply renames to annotations (page-level widgets) and to the field dictionary entries.
    def get_str(value):
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except Exception:
                return value.decode('latin-1', errors='ignore')
        return value

    for old_name, new_name in changes:
        old_field = fields.get(old_name)
        if old_field is not None and '/T' in old_field:
            old_field[NameObject('/T')] = TextStringObject(new_name)

        for page in writer.pages:
            annots = page.get('/Annots')
            if not annots:
                continue
            for ann in annots:
                try:
                    aobj = ann.get_object()
                except Exception:
                    continue
                t = get_str(aobj.get('/T'))
                if t == old_name:
                    aobj[NameObject('/T')] = TextStringObject(new_name)

    if not changes:
        print("No field names changed.")
        # If the user asked to fill the fields, still write the output PDF.
        if not args.fill:
            return

    print(f"Will rename {len(changes)} fields:")
    for old_name, new_name in changes:
        print(f"  {old_name!r} -> {new_name!r}")

    # Optionally fill text fields (after rename) so the output PDF can be inspected.
    if args.fill:
        values = {}

        # Fill all renamed fields using their new name keys.
        for old_name, new_name in changes:
            values[new_name] = args.fill_template.format(name=old_name, new=new_name)

        # Also fill fields that were not renamed, so all text inputs get a visible placeholder.
        for old_name, field in fields.items():
            if not isinstance(old_name, str):
                continue
            new_name = mapping.get(old_name)
            if new_name is None:
                new_name = normalize_name(old_name, args.strategy)
            if new_name == old_name:
                values[new_name] = args.fill_template.format(name=old_name, new=new_name)

        # page-level update for visible form fields
        for page in writer.pages:
            try:
                writer.update_page_form_field_values(page, values)
            except Exception:
                pass

        # Directly mutate field objects and widget annotations for reliability.
        for field_name, text_value in values.items():
            field_obj = fields.get(field_name)
            if field_obj is None:
                continue

            ft = field_obj.get('/FT')
            if ft == '/Tx':
                field_obj[NameObject('/V')] = TextStringObject(text_value)
                # Also force appearance update when possible.
                if '/AP' in field_obj:
                    del field_obj['/AP']
            elif ft == '/Btn':
                # For checkbox/button fields, mark as checked and set value to Yes.
                field_obj[NameObject('/V')] = NameObject('/Yes')
                field_obj[NameObject('/AS')] = NameObject('/Yes')

        # Mutate widget annotations as well to keep visual state in page stream.
        for page in writer.pages:
            annots = page.get('/Annots') or []
            for ann in annots:
                try:
                    widget = ann.get_object()
                except Exception:
                    continue
                t = widget.get('/T')
                if not t:
                    continue
                w_ft = widget.get('/FT')
                if w_ft == '/Tx' and t in values:
                    widget[NameObject('/V')] = TextStringObject(values[t])
                    if '/AP' in widget:
                        del widget['/AP']
                elif w_ft == '/Btn':
                    widget[NameObject('/V')] = NameObject('/Yes')
                    widget[NameObject('/AS')] = NameObject('/Yes')

        # Ensure viewer rebuilds appearance streams.
        try:
            acro = writer._root_object.get('/AcroForm')
            if acro is not None:
                acro[NameObject('/NeedAppearances')] = True
        except Exception:
            pass

        # Force values into field dictionaries for /Tx fields, to avoid viewer appearance stale state.
        for field_name, value in values.items():
            fld = fields.get(field_name)
            if fld is None:
                continue
            if fld.get('/FT') == '/Tx':
                fld[NameObject('/V')] = TextStringObject(value)

        # Force NeedAppearances so viewers recompute appearance streams.
        try:
            acro = writer._root_object.get('/AcroForm')
            if acro is not None:
                acro[NameObject('/NeedAppearances')] = True
        except Exception:
            pass

    if args.dry_run:
        print("Dry run enabled; not writing output file.")
        return

    args.output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_pdf, "wb") as f:
        writer.write(f)

    if args.verify:
        out_reader = PdfReader(str(args.output_pdf))
        out_fields = out_reader.get_fields() or {}

        expected_map = {}
        for old_name, field in fields.items():
            if not isinstance(old_name, str):
                continue
            mapped = mapping.get(old_name)
            if mapped is None:
                mapped = normalize_name(old_name, args.strategy)
            expected_map[mapped] = args.fill_template.format(name=old_name, new=mapped)

        total = 0
        found = 0
        mismatch = 0
        missing = 0

        print("\nVerificação de preenchimento (verify):")
        for field_name, expected_value in expected_map.items():
            total += 1
            out_field = out_fields.get(field_name)
            if out_field is None:
                # Try to find field by old name in case rename did not apply
                old_name = new_name_to_old.get(field_name)
                if old_name and old_name in out_fields:
                    out_field = out_fields.get(old_name)
                else:
                    missing += 1
                    print(f"  MISSING field: {field_name!r} expected={expected_value!r}")
                    continue
            actual_value = out_field.get('/V')
            # PdfReader may return bytes for PDF strings in some versions
            if isinstance(actual_value, bytes):
                actual_value = actual_value.decode('utf-8', errors='ignore')

            if actual_value == expected_value:
                found += 1
            else:
                mismatch += 1
                print(f"  MISMATCH field: {field_name!r} expected={expected_value!r} actual={actual_value!r}")

        print(f"  total={total} found={found} missing={missing} mismatch={mismatch}")


if __name__ == "__main__":
    main()

