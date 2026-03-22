# PDF-Field-Labeler

Ferramenta em Python para identificação, mapeamento e renomeação de campos AcroForm em PDFs (text, checkbox, choice, signature etc.).

## Funcionalidades existentes

- `scripts/extract_pdf_field_metadata.py`: extrai metadados PDF -> JSON (page, name, type, posição, tamanho, value, appearanceState)
- `scripts/normalize_pdf_fields.py`: renomeia campos por map ou estratégia (`trim`, `normalize`, `remove-spaces`), preenche e verifica `/V`.
- `scripts/number_text_fields.py`: utilitário de ajuda para gerar mapeamento com índice.

## Nova UI Web (FastAPI)

- `web/app.py` com endpoints:
  - `GET /api/fields?input_pdf=<path>`
  - `POST /api/map` (JSON mapping + salva arquivo)
  - `POST /api/apply` (executa normalize via script com params)
  - `GET /api/preview/page/{n}?input_pdf=<path>` (opcional, via `pdf2image`)
- `web/static/index.html`, `app.js`, `styles.css` para fluxo minimalista.

## Quickstart

1. `pip install -r requirements.txt`
2. `python scripts/extract_pdf_field_metadata.py data/sample/CharacterSheet_DnD5e.pdf data/sample/pdf-field-metadata.json`
3. Ajuste `data/sample/pdf-field-map.json` com `{"oldName":"newName"}`.
4. `python scripts/normalize_pdf_fields.py data/sample/CharacterSheet_DnD5e.pdf data/out/CharacterSheet_normalized.pdf --map data/sample/pdf-field-map.json --fill --fill-template "{new}" --verify`
5. Iniciar web:
   - `uvicorn web.app:app --reload --host 0.0.0.0 --port 8000`
   - Abrir `http://localhost:8000`

## Usando com conda (recomendado)

1. `conda init powershell` (apenas 1 vez por shell completo)
2. Fechar e reabrir o terminal
3. `conda activate pdf-form-labeler`
4. `uvicorn web.app:app --reload --host 0.0.0.0 --port 8000`

### Fallback (se `conda activate` falhar)

- `conda run -n pdf-form-labeler uvicorn web.app:app --reload --host 127.0.0.1 --port 8000`

### Verificação do ambiente

- `conda run -n pdf-form-labeler python -c "import multipart, fastapi, uvicorn, pypdf; print('env ok')"`

## Fluxo recomendado

- Extrair metadata
- Enriquecer JSON / CSV / YAML
- Gerar/editar map
- Aplicar normalização
- Validar resultado PDF

## Atualização do README e ações do repositório

1. O frontend agora renderiza o PDF com ajuste para o tamanho do container, mantendo `fit-to-container`.
2. A visualização de campos (hover) usa `renderState.scale` calculado a partir de `displayWidth / page_width` (unidades pontos → pixels).
3. A extração de metadata agora inclui `page_width` e `page_height` em `api_fields`, suporte obrigatório para métricas de posicionamento.
4. O `openPdf` carrega `fields` antes de chamar `renderPage` para garantir que `pageMetrics` esteja presença.

### Passo a passo para validar a correção

- `git checkout main`
- `git pull`
- `git status` para confirmar alterações locais
- `git add README.md web/app.py web/static/app.js web/static/styles.css`
- `git commit -m "Fix pdf preview scaling + field hover alignment + readme update"`
- `git push`

### Dica para o desenvolvedor

- Use `Ctrl+Shift+R` (hard reload) no navegador para limpar cache JS e garantir que a versão nova seja usada.
- Se quiser, abra um PR com descrição: "Correcção: fit-to-container + escala de campo + sequência openPdf/loadFields".

