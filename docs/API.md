# Documentação da API REST

Referência completa dos endpoints disponíveis.

## Base URL

```
http://localhost:8000
```

## Endpoints

### 1. Upload de PDF

Envia um arquivo PDF para processamento.

```http
POST /api/upload
Content-Type: multipart/form-data
```

**Parâmetros:**
- `file` (file, required): Arquivo PDF

**Response:**
```json
{
  "input_pdf": "/absolute/path/to/file.pdf",
  "file_url": "/uploads/file.pdf",
  "relative": "data/uploads/file.pdf"
}
```

**Status Codes:**
- `200`: Upload bem-sucedido
- `400`: Arquivo inválido
- `413`: Arquivo muito grande

---

### 2. Extrair Campos

Extrai metadata de todos os campos de um PDF.

```http
GET /api/fields?input_pdf=data/sample/form.pdf
```

**Parâmetros Query:**
- `input_pdf` (string, required): Caminho do PDF relativo ao repositório

**Response:**
```json
{
  "fields": [
    {
      "page": 1,
      "name": "fullname",
      "type": "text",
      "x": 100.5,
      "y": 200.3,
      "width": 150.0,
      "height": 20.0,
      "value": null,
      "appearanceState": null,
      "page_width": 612.0,
      "page_height": 792.0
    },
    {
      "page": 1,
      "name": "email",
      "type": "text",
      "x": 100.5,
      "y": 230.3,
      "width": 150.0,
      "height": 20.0,
      "value": null,
      "appearanceState": null,
      "page_width": 612.0,
      "page_height": 792.0
    }
  ]
}
```

**Status Codes:**
- `200`: Campos extraídos com sucesso
- `404`: PDF não encontrado
- `400`: Caminho fora do diretório permitido

---

### 3. Aplicar Mapeamento e Normalizar

Renomeia campos e gera novo PDF.

```http
POST /api/apply
Content-Type: application/json
```

**Body:**
```json
{
  "input_pdf": "data/sample/form.pdf",
  "output_pdf": "data/out/form_normalized.pdf",
  "map": {
    "fullname": "nome_completo",
    "email": "email_contato"
  },
  "strategy": "normalize",
  "fill": true,
  "fill_template": "{new}",
  "verify": true,
  "dry_run": false
}
```

**Parâmetros:**
- `input_pdf` (string, required): Caminho do PDF original
- `output_pdf` (string, required): Caminho do PDF de saída
- `map` (object, optional): Mapeamento de nomes antigos → novos
- `map_path` (string, optional): Caminho do arquivo JSON com mapeamento
- `strategy` (string, optional): Estratégia de normalização (`normalize`, `trim`, `remove-spaces`)
- `fill` (boolean, optional): Preencher valores padrão
- `fill_template` (string, optional): Template para valores (ex: `{new}`, `{name}`)
- `verify` (boolean, optional): Validar integridade
- `dry_run` (boolean, optional): Simular sem gerar arquivo

**Response:**
```json
{
  "output": "data/out/form_normalized.pdf",
  "status": "success",
  "message": "PDF normalizado com sucesso",
  "fields_processed": 15,
  "timestamp": "2025-04-17T10:30:45Z"
}
```

**Status Codes:**
- `200`: Normalização bem-sucedida
- `400`: Dados inválidos
- `404`: Arquivo não encontrado
- `500`: Erro ao processar PDF

---

### 4. Visualizar Página do PDF (Opcional)

Retorna uma imagem renderizada de uma página específica.

```http
GET /api/preview/page/1?input_pdf=data/sample/form.pdf
```

**Parâmetros Query:**
- `input_pdf` (string, required): Caminho do PDF
- Page number: `1`, `2`, `3`, etc.

**Response:**
```
Content-Type: image/png
(Imagem PNG da página)
```

**Requisitos:**
- `pdf2image` instalado
- `poppler` instalado no sistema

**Status Codes:**
- `200`: Imagem gerada
- `404`: Página não encontrada
- `500`: Erro ao renderizar

---

## Exemplos de Uso

### JavaScript/Fetch

#### Upload

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/upload', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log('PDF salvo em:', data.input_pdf);
```

#### Extrair Campos

```javascript
const response = await fetch('/api/fields?input_pdf=data/uploads/form.pdf');
const data = await response.json();

data.fields.forEach(field => {
  console.log(`${field.name} (${field.type}) na página ${field.page}`);
});
```

#### Aplicar Mapeamento

```javascript
const payload = {
  input_pdf: 'data/uploads/form.pdf',
  output_pdf: 'data/out/form_normalized.pdf',
  map: {
    'fullname': 'nome_completo',
    'email': 'email_contato'
  },
  fill: true,
  verify: true
};

const response = await fetch('/api/apply', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});

const result = await response.json();
console.log(result.message);
```

### Python/Requests

```python
import requests

# Upload
with open('form.pdf', 'rb') as f:
    files = {'file': f}
    resp = requests.post('http://localhost:8000/api/upload', files=files)
    print(resp.json())

# Extrair campos
resp = requests.get('http://localhost:8000/api/fields', 
    params={'input_pdf': 'data/uploads/form.pdf'})
fields = resp.json()['fields']
print(f"Encontrados {len(fields)} campos")

# Aplicar mapeamento
payload = {
    'input_pdf': 'data/uploads/form.pdf',
    'output_pdf': 'data/out/form_normalized.pdf',
    'map': {
        'fullname': 'nome_completo',
        'email': 'email_contato'
    },
    'verify': True
}
resp = requests.post('http://localhost:8000/api/apply', json=payload)
print(resp.json())
```

### cURL

```bash
# Upload
curl -F "file=@form.pdf" http://localhost:8000/api/upload

# Extrair campos
curl "http://localhost:8000/api/fields?input_pdf=data/uploads/form.pdf"

# Aplicar mapeamento
curl -X POST http://localhost:8000/api/apply \
  -H "Content-Type: application/json" \
  -d '{
    "input_pdf": "data/uploads/form.pdf",
    "output_pdf": "data/out/form_normalized.pdf",
    "map": {"fullname": "nome_completo"}
  }'
```

---

## Documentação Interativa

A API também oferece documentação automática via Swagger UI:

```
http://localhost:8000/docs
```

E versão ReDoc:

```
http://localhost:8000/redoc
```

---

## Limitações e Considerações

- PDFs com criptografia podem não ser suportados
- Campos sem `/Fields` definido não serão detectados
- Alguns formulários em imagem (não interativos) não funcionam
- Arquivos muito grandes podem levar tempo para processar

Consulte [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para mais problemas e soluções.
