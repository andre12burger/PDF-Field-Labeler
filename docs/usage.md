# Uso do PDF Form Labeler

## 1. Extração de metadados

```bash
python scripts/extract_pdf_field_metadata.py data/sample/CharacterSheet_DnD5e.pdf data/sample/pdf-field-metadata.json
```

## 2. Validar e editar metadados

- `data/sample/pdf-field-metadata.json` contém uma lista de campos.
- Atualize nomes, tipos e/ou transformação desejada.

## 3. Gerar/editar map

```json
{
  "Race ": "Race",
  "Check Box 12": "Check Box ST Strength"
}
```

en `data/sample/pdf-field-map.json`.

## 4. Aplicar normalização

```bash
python scripts/normalize_pdf_fields.py \
  data/sample/CharacterSheet_DnD5e.pdf \
  data/out/CharacterSheet_normalized.pdf \
  --map data/sample/pdf-field-map.json \
  --fill --fill-template "{new}" --verify
```

## 5. Interface Web

```bash
uvicorn web.app:app --reload --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000`.

- `GET /api/fields?input_pdf=...`
- `POST /api/map` `{ "map": {...} }`
- `POST /api/apply` payload JSON
- `GET /api/preview/page/1?input_pdf=...` (requer `pdf2image` + `poppler`)
