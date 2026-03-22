from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader
from pydantic import BaseModel

app = FastAPI(title="PDF Form Labeler API", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
NORMALIZE_SCRIPT = SCRIPTS_DIR / "normalize_pdf_fields.py"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
OUTPUT_DIR = BASE_DIR / "data" / "out"

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ensure_local_path(path: str) -> Path:
    p = Path(path).resolve()
    if not str(p).startswith(str(BASE_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Path must be inside repository folder")
    return p


def extract_metadata_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    result = []

    def maybe_num(value):
        try:
            return float(value)
        except Exception:
            return None

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

    for page_num, page in enumerate(reader.pages, start=1):
        annots = page.get("/Annots") or []
        for annot in annots:
            try:
                widget = annot.get_object()
            except Exception:
                continue
            name = widget.get("/T")
            if not name:
                continue
            if isinstance(name, bytes):
                name = name.decode("utf-8", errors="ignore")
            typ = norm_type(widget.get("/FT"))

            rect = widget.get("/Rect") or []
            x = y = width = height = None
            if isinstance(rect, list) and len(rect) == 4:
                x0, y0, x1, y1 = [maybe_num(r) for r in rect]
                if None not in (x0, y0, x1, y1):
                    x = x0
                    y = y0
                    width = x1 - x0
                    height = y1 - y0

            value = widget.get("/V")
            appearance = widget.get("/AS")
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="ignore")
            if isinstance(appearance, bytes):
                appearance = appearance.decode("utf-8", errors="ignore")

            result.append({
                "page": page_num,
                "name": name,
                "type": typ,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "value": value,
                "appearanceState": appearance,
                "page_width": float(page.mediabox.width),
                "page_height": float(page.mediabox.height),
            })

    result.sort(key=lambda item: (item["page"], -(item.get("y") or 0), item.get("x") or 0))
    return result


class ApplyRequest(BaseModel):
    input_pdf: str
    output_pdf: str
    map: Optional[Dict[str, str]] = None
    map_path: Optional[str] = None
    strategy: Optional[str] = "normalize"
    fill: Optional[bool] = False
    fill_template: Optional[str] = "{name}"
    verify: Optional[bool] = False
    dry_run: Optional[bool] = False


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    html_path = BASE_DIR / "web" / "static" / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h1>Web UI not found</h1>", status_code=404)
    return HTMLResponse(html_path.read_text(encoding="utf-8"), status_code=200)


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)) -> Dict[str, Any]:
    destination = UPLOAD_DIR / Path(file.filename).name
    content = await file.read()
    destination.write_bytes(content)
    return {
        "input_pdf": str(destination),
        "file_url": f"/uploads/{destination.name}",
        "relative": str(destination.relative_to(BASE_DIR)),
    }


@app.get("/api/fields")
def api_fields(input_pdf: str) -> Dict[str, Any]:
    pdf_path = ensure_local_path(input_pdf)
    try:
        fields = extract_metadata_from_pdf(pdf_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"count": len(fields), "fields": fields}


@app.get("/api/download")
def api_download(path: str) -> FileResponse:
    file_path = ensure_local_path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, media_type="application/pdf", filename=file_path.name)


@app.post("/api/map")
def api_map(map: Dict[str, str], output_path: Optional[str] = None) -> Dict[str, Any]:
    if output_path:
        out = ensure_local_path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(map, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"saved": str(out), "entries": len(map)}
    return {"entries": len(map), "map": map}


@app.post("/api/apply")
def api_apply(payload: ApplyRequest) -> Dict[str, Any]:
    input_pdf = ensure_local_path(payload.input_pdf)
    output_pdf = ensure_local_path(payload.output_pdf)

    temp_map_file = None
    map_arg = []
    if payload.map is not None:
        temp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        temp.write(json.dumps(payload.map, indent=2, ensure_ascii=False))
        temp.close()
        temp_map_file = Path(temp.name)
        map_arg = ["--map", str(temp_map_file)]
    elif payload.map_path is not None:
        map_arg = ["--map", str(ensure_local_path(payload.map_path))]

    cmd = [
        "python",
        str(NORMALIZE_SCRIPT),
        str(input_pdf),
        str(output_pdf),
        "--strategy",
        payload.strategy or "normalize",
        "--fill" if payload.fill else "",
        "--fill-template",
        payload.fill_template or "{name}",
        "--verify" if payload.verify else "",
        "--dry-run" if payload.dry_run else "",
    ]
    cmd = [c for c in cmd if c]
    if map_arg:
        cmd += map_arg

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    finally:
        if temp_map_file and temp_map_file.exists():
            temp_map_file.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail={"cmd": cmd, "stderr": proc.stderr, "stdout": proc.stdout})

    if not payload.dry_run and not output_pdf.exists():
        raise HTTPException(status_code=500, detail="Output PDF not written")

    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "output_pdf": str(output_pdf) if output_pdf.exists() else None,
    }


@app.get("/api/preview/page/{page_number}")
def api_preview(page_number: int, input_pdf: str) -> Dict[str, Any]:
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise HTTPException(status_code=500, detail="pdf2image is required for preview. Install with pip install pdf2image pillow")

    pdf_path = ensure_local_path(input_pdf)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    images = convert_from_path(str(pdf_path), first_page=page_number, last_page=page_number)
    if not images:
        raise HTTPException(status_code=404, detail="Page not found")

    out_png = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    images[0].save(out_png.name, "PNG")
    out_png.close()

    return FileResponse(out_png.name, media_type="image/png")
