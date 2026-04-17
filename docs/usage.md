# Guia de Uso

Instruções completas sobre como usar o PDF Field Labeler.

## Iniciando o Servidor

### Via Script Fornecido

**Windows (PowerShell):**
```powershell
.\start_server.ps1
```

**Windows (Batch):**
```bash
start_server.bat
```

**Linux/macOS:**
```bash
./start_server.sh
```

### Manualmente com Uvicorn

```bash
# Com Conda
conda activate pdf-form-labeler
uvicorn web.app:app --reload --host 0.0.0.0 --port 8000

# Com venv (Windows)
venv\Scripts\activate
uvicorn web.app:app --reload --host 0.0.0.0 --port 8000

# Com venv (macOS/Linux)
source venv/bin/activate
uvicorn web.app:app --reload --host 0.0.0.0 --port 8000
```

Acesse: `http://localhost:8000`

## Usando a Interface Web

### 1. Upload do PDF

1. Clique em **"Escolher arquivo"** ou arraste um PDF
2. Clique em **"Enviar PDF"**
3. O sistema carregará automaticamente todos os campos

### 2. Visualizar Campos

- Use as setas **< >** ou o campo numérico para navegar entre páginas
- Todos os campos encontrados aparecem na sidebar à direita
- Cada campo mostra: página, nome atual, tipo, coordenadas

### 3. Editar Nomes dos Campos

Na sidebar, para cada campo:
1. Clique no campo de entrada "Novo nome"
2. Digite o novo nome desejado
3. O mapa é salvo em tempo real

### 4. Aplicar Normalização

1. Clique em **"Aplicar renomeações e gerar PDF"**
2. Aguarde o processamento (pode levar alguns segundos)
3. Clique em **"Baixar PDF Normalizado"** para salvar o arquivo

## Usando a Linha de Comando

Para processar PDFs programaticamente ou em lote.

### Extrair Metadata de um PDF

Analisa um PDF e extrai informações de todos os campos.

```bash
python scripts/extract_pdf_field_metadata.py \
  caminho/input.pdf \
  caminho/output_metadata.json
```

**Exemplo:**
```bash
python scripts/extract_pdf_field_metadata.py \
  data/sample/CharacterSheet_DnD5e.pdf \
  data/sample/pdf-field-metadata.json
```

**Output:** Arquivo JSON com campos estruturados.

### Aplicar Normalização via Script

Renomeia campos de acordo com um mapa e gera PDF novo.

```bash
python scripts/normalize_pdf_fields.py \
  caminho/input.pdf \
  caminho/output.pdf \
  --map caminho/field_map.json \
  --fill \
  --fill-template "{new}" \
  --verify
```

**Parâmetros:**
- `--map`: Arquivo JSON com mapeamento de nomes
- `--fill`: Preencher valores padrão
- `--fill-template`: Template para valores (ex: `{new}`, `{name}`)
- `--verify`: Validar integridade dos valores

**Exemplo Completo:**
```bash
python scripts/normalize_pdf_fields.py \
  data/sample/input.pdf \
  data/out/output_normalized.pdf \
  --map data/sample/pdf-field-map.json \
  --fill \
  --verify
```

### Gerar Numeração Automática

Cria mapeamento automático para campos de texto com índices.

```bash
python scripts/number_text_fields.py \
  caminho/input.pdf \
  --prefix "field_"
```

**Exemplo:**
```bash
python scripts/number_text_fields.py \
  data/sample/form.pdf \
  --prefix "text_field_"
```

**Output:** Gera nomes como `text_field_1`, `text_field_2`, etc.

## Fluxo Típico

### Fluxo 1: Web UI (Recomendado para Usuários)

```
1. Iniciar servidor (./start_server.ps1)
2. Abrir http://localhost:8000
3. Upload do PDF
4. Visualizar campos
5. Editar nomes
6. Aplicar e baixar
```

### Fluxo 2: CLI (Para Automação)

```bash
# Passo 1: Extrair metadata
python scripts/extract_pdf_field_metadata.py input.pdf metadata.json

# Passo 2: Editar metadata.json ou criar field_map.json

# Passo 3: Aplicar normalização
python scripts/normalize_pdf_fields.py \
  input.pdf \
  output.pdf \
  --map field_map.json \
  --verify
```

### Fluxo 3: Pipeline Automatizado (Bash/PowerShell)

```bash
# Processar múltiplos PDFs
for pdf in data/uploads/*.pdf; do
    basename=$(basename "$pdf" .pdf)
    python scripts/extract_pdf_field_metadata.py \
      "$pdf" \
      "metadata/${basename}_meta.json"
    
    python scripts/normalize_pdf_fields.py \
      "$pdf" \
      "data/out/${basename}_normalized.pdf" \
      --map field_map.json \
      --verify
done
```

## Arquivo de Mapeamento (field_map.json)

Arquivo JSON que define o mapeamento de nomes antigos → novos:

```json
{
  "fullname": "nome_completo",
  "email": "email_contato",
  "phone": "telefone",
  "accept_terms": "aceitar_termos",
  "ClassLevel": "nivel_classe",
  "Background": "historico",
  "PlayerName": "nome_jogador"
}
```

Crie manualmente ou use a Web UI para gerar automaticamente.

## Configurações Avançadas

### Mudar Porta

```bash
uvicorn web.app:app --port 8001
```

### Desabilitar Auto-reload (Produção)

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Host Remoto

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000
# Acesse de outro computador: http://<seu-ip>:8000
```

## Próximos Passos

- Consulte [API.md](API.md) para integração programática
- Veja [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para problemas comuns
- Leia [../README.md](../README.md) para visão geral do projeto
