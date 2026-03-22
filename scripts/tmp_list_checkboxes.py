from pypdf import PdfReader
pdf = PdfReader('data/pdf/CharacterSheet_DnD5e.pdf')
rows = []
for pi, page in enumerate(pdf.pages, start=1):
    ann = page.get('/Annots') or []
    for a in ann:
        w = a.get_object()
        ft = w.get('/FT')
        if ft == '/Btn':
            t = w.get('/T')
            rect = w.get('/Rect')
            v = w.get('/V')
            asv = w.get('/AS')
            if isinstance(rect, list) and len(rect) == 4:
                x1, y1, x2, y2 = rect
            else:
                x1 = y1 = x2 = y2 = 0
            rows.append((pi, -y2, x1, t, v, asv))
rows.sort()
for pi, ny, x, t, v, asv in rows:
    print(f"page={pi:02d} y={-ny:.1f} x={x:.1f} name={t!r} V={v!r} AS={asv!r}")
