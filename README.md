# PDF Field Labeler

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.112%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Descrição do Projeto

**PDF Field Labeler** é uma ferramenta poderosa e profissional para identificação, mapeamento, normalização e renomeação de campos AcroForm em documentos PDF. Funciona com diversos tipos de campos incluindo texto, checkboxes, campos de seleção (choice) e assinaturas digitais.

O projeto oferece uma solução completa que combina:
- **Scripts CLI** para processamento em lote
- **Web UI interativa** (FastAPI + React) para gerenciamento visual
- **API REST** para integração em pipelines automatizados

Ideal para processar formulários PDF em volume, padronizar nomenclaturas de campos e gerar PDFs normalizados para processamento automatizado.

---

## 🖼️ Screenshots

### Interface Principal em Ação

<img src="docs/assets/screenshot-main-interface.png" alt="Interface principal do PDF Field Labeler com formulário D&D 5e carregado" width="100%">

**Exemplo:** Processando um formulário D&D 5e com 333 campos
- **À esquerda:** Visualização do PDF com campos destacados em vermelho
- **À direita:** Lista de campos extraídos com opção de editar nomes
- Mostra campos como `ClassLevel`, `Background`, `PlayerName`, `CharacterName`, `Race`
- Botão azul para aplicar normalização e gerar PDF

### Interface (Mockup SVG)

<img src="docs/assets/interface-mockup.svg" alt="Mockup da interface do PDF Field Labeler" width="100%">

A interface oferece:
- **Painel de upload** no topo para carregar PDFs
- **Visualizador de PDF** no centro com navegação entre páginas
- **Sidebar de campos** à direita listando todos os campos encontrados
- **Edição em tempo real** de nomes de campos
- **Botão de ação** para aplicar normalização e gerar PDF

---

## ✨ Funcionalidades Principais

### 🔍 Extração e Análise
- Extrai metadata completa de campos PDF (tipo, posição, tamanho, valores)
- Suporte para todos os tipos AcroForm: texto, checkbox, choice, signature
- Calcula dimensões e coordenadas de cada campo
- Exporta dados em JSON estruturado

### 🏷️ Mapeamento e Renomeação
- Interface visual para mapear nomes antigos → novos
- Estratégias automáticas: `trim`, `normalize`, `remove-spaces`
- Validação em tempo real
- Suporte a mapeamento customizado via JSON

### ⚙️ Processamento e Normalização
- Renomeia campos de acordo com mapa
- Preenche valores padrão em campos
- Verifica integridade dos valores (`/V`)
- Exporta PDF normalizado

### 🎨 Interface Web
- Upload de PDFs com drag-and-drop
- Visualização interativa de campos
- Preview de páginas em tempo real
- Aplicação de mapeamentos com feedback visual
- Download de PDFs processados

---

## 📦 Dependências e Requisitos

### Requisitos do Sistema
- **Python**: 3.8 ou superior
- **Sistema Operacional**: Windows, macOS ou Linux
- **Espaço em disco**: ~500MB (incluindo ambiente virtuais)

### Dependências do Projeto

| Pacote | Versão | Propósito |
|--------|--------|----------|
| `pypdf` | ≥3.14.0 | Leitura/escrita de PDFs |
| `fastapi` | ≥0.112.0 | Framework web API |
| `uvicorn` | ≥0.23.0 | Servidor ASGI |
| `pdf2image` | ≥1.16.0 | Conversão PDF → imagem |
| `Pillow` | ≥10.0.0 | Processamento de imagens |
| `python-multipart` | ≥0.0.6 | Upload de formulários |

---

## 🚀 Instalação e Configuração

### Opção 1: Com Conda (Recomendado)

#### Passo 1: Clonar o Repositório
```bash
git clone https://github.com/andre12burger/PDF-Field-Labeler.git
cd PDF-Field-Labeler
```

#### Passo 2: Criar Ambiente Conda
```bash
conda env create -f environment.yml
```

#### Passo 3: Ativar Ambiente
```bash
# Windows (PowerShell)
conda init powershell
# Fechar e reabrir o terminal

conda activate pdf-form-labeler

# Alternativa (se conda activate falhar)
conda run -n pdf-form-labeler python -c "import multipart, fastapi, uvicorn, pypdf; print('✓ Ambiente OK')"
```

### Opção 2: Com venv (Alternativa)

```bash
# Clonar repositório
git clone https://github.com/andre12burger/PDF-Field-Labeler.git
cd PDF-Field-Labeler

# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (macOS/Linux)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

---

## 💻 Como Executar

### Iniciar o Servidor Web

#### Com Conda:
```bash
conda activate pdf-form-labeler
uvicorn web.app:app --reload --host 0.0.0.0 --port 8000
```

#### Com venv:
```bash
# Windows
venv\Scripts\activate

# Depois:
uvicorn web.app:app --reload --host 0.0.0.0 --port 8000
```

#### Usando Scripts Fornecidos:

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

Após iniciar, abra no navegador:
```
http://localhost:8000
```

---

## 🎯 Guia de Uso

### Fluxo Básico na Web UI

1. **Upload do PDF**
   - Clique em "Escolher arquivo" ou arraste um PDF
   - Clique em "Enviar PDF"

2. **Visualizar Campos**
   - Os campos do PDF serão carregados automaticamente
   - Navegue entre páginas usando < e >

3. **Editar Mapeamento**
   - Para cada campo, edite o novo nome desejado
   - O mapa é salvo em tempo real

4. **Aplicar Normalização**
   - Clique em "Aplicar renomeações e gerar PDF"
   - Aguarde o processamento
   - Download do PDF normalizado

### Uso via Linha de Comando

#### 1. Extrair Metadata
```bash
python scripts/extract_pdf_field_metadata.py \
  data/sample/form.pdf \
  output/form_metadata.json
```

#### 2. Criar Mapeamento
Edite `output/field_map.json`:
```json
{
  "field_old_name": "field_new_name",
  "checkbox_1": "aceitar_termos",
  "text_address": "endereco_completo"
}
```

#### 3. Aplicar Normalização
```bash
python scripts/normalize_pdf_fields.py \
  data/sample/form.pdf \
  data/out/form_normalized.pdf \
  --map output/field_map.json \
  --fill \
  --fill-template "{new}" \
  --verify
```

#### 4. Gerar Numeração Automática
```bash
python scripts/number_text_fields.py \
  data/sample/form.pdf \
  --prefix "field_"
```

---

## 🏗️ Estrutura do Projeto

```
PDF-Field-Labeler/
├── web/                          # Aplicação web (FastAPI)
│   ├── app.py                   # API endpoints principal
│   └── static/                  # Arquivos frontend
│       ├── index.html           # Interface HTML
│       ├── app.js               # Lógica JavaScript
│       └── styles.css           # Estilos CSS
├── scripts/                      # Scripts Python CLI
│   ├── extract_pdf_field_metadata.py    # Extração de metadata
│   ├── normalize_pdf_fields.py          # Normalização de campos
│   ├── number_text_fields.py            # Geração de numeração
│   └── ...
├── data/
│   ├── sample/                  # Arquivos de exemplo
│   │   ├── pdf-field-metadata.json
│   │   └── pdf-field-map.json
│   ├── uploads/                 # PDFs enviados temporariamente
│   └── out/                     # PDFs processados gerados
├── requirements.txt              # Dependências pip
├── environment.yml               # Configuração Conda
├── README.md                     # Este arquivo
└── start_server.*               # Scripts para iniciar servidor

```

---

## 🔌 API REST

### Endpoints Principais

#### 1. Upload de PDF
```http
POST /api/upload
Content-Type: multipart/form-data

Response:
{
  "input_pdf": "/absolute/path/to/file.pdf",
  "file_url": "/uploads/file.pdf",
  "relative": "data/uploads/file.pdf"
}
```

#### 2. Extrair Campos
```http
GET /api/fields?input_pdf=data/sample/form.pdf

Response:
{
  "fields": [
    {
      "page": 1,
      "name": "fullname",
      "type": "text",
      "x": 100,
      "y": 200,
      "width": 150,
      "height": 20,
      "value": null,
      "page_width": 612,
      "page_height": 792
    },
    ...
  ]
}
```

#### 3. Aplicar Mapeamento
```http
POST /api/apply
Content-Type: application/json

{
  "input_pdf": "data/sample/form.pdf",
  "output_pdf": "data/out/form_normalized.pdf",
  "map": {
    "fullname": "nome_completo",
    "email": "email_contato"
  },
  "fill": true,
  "verify": true
}

Response:
{
  "output": "data/out/form_normalized.pdf",
  "status": "success",
  "message": "PDF normalizado com sucesso"
}
```

---

## 📊 Exemplos de Uso

### Exemplo 1: Processamento Simples
```bash
# Extrair campos
python scripts/extract_pdf_field_metadata.py \
  input.pdf metadata.json

# Editar map.json manualmente ou via UI
# Aplicar normalização
python scripts/normalize_pdf_fields.py \
  input.pdf output.pdf \
  --map map.json
```

### Exemplo 2: Pipeline Automatizado
```bash
# Script para processar múltiplos PDFs
for pdf in data/uploads/*.pdf; do
  python scripts/extract_pdf_field_metadata.py "$pdf" "metadata.json"
  python scripts/normalize_pdf_fields.py "$pdf" "data/out/$(basename $pdf)" \
    --map "map.json" --fill --verify
done
```

---

## ⚙️ Configuração Avançada

### Variáveis de Ambiente (Futuro)
Tenha um arquivo `.env`:
```env
API_HOST=0.0.0.0
API_PORT=8000
UPLOAD_DIR=data/uploads
OUTPUT_DIR=data/out
LOG_LEVEL=INFO
```

### Executar sem Reload
Para produção:
```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🐛 Troubleshooting

### Problema: Conda activate não funciona
**Solução:**
```bash
conda run -n pdf-form-labeler uvicorn web.app:app --port 8000
```

### Problema: Porta 8000 em uso
**Solução:**
```bash
uvicorn web.app:app --port 8001  # Use outra porta
```

### Problema: PyPDF não consegue ler PDF
**Solução:** 
- Verifique se o PDF não está corrompido
- Alguns PDFs com criptografia podem não ser suportados
- Tente converter com outro software primeiro

### Problema: Campos não aparecem
**Solução:**
- PDFs com campos em AcroForm precisam ter `/Fields` definido
- Formulários em PDF de imagem não funcionam
- Verifique se os campos estão marcados como interativos no Adobe

---

## 📝 Pré-requisitos de Sistema

Para a funcionalidade de preview de página (pdf2image), pode ser necessário:

**Windows:**
- Poppler para Windows: baixe de [aqui](https://github.com/oschwartz10612/poppler-windows/releases/)

**macOS:**
```bash
brew install poppler
```

**Linux:**
```bash
sudo apt-get install poppler-utils
```

---

## 🛠️ Desenvolvimento

Para contribuir ao projeto:

```bash
# Fork e clone seu fork
git clone https://github.com/seu-usuario/PDF-Field-Labeler.git
cd PDF-Field-Labeler

# Criar branch para feature
git checkout -b feature/sua-feature

# Fazer alterações
# ...

# Commit e push
git add .
git commit -m "Add: descrição da feature"
git push origin feature/sua-feature

# Abrir Pull Request
```

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 👤 Autor

**André Burger**
- GitHub: [@andre12burger](https://github.com/andre12burger)
- Projeto: [PDF-Field-Labeler](https://github.com/andre12burger/PDF-Field-Labeler)

---

## 📞 Suporte e Contato

Para reportar bugs, sugerir features ou fazer perguntas:
- Abra uma [Issue](https://github.com/andre12burger/PDF-Field-Labeler/issues)
- Crie uma [Discussion](https://github.com/andre12burger/PDF-Field-Labeler/discussions)

---

## 🙏 Agradecimentos

- [PyPDF](https://github.com/py-pdf/pypdf) - Manipulação de PDFs
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web
- [Uvicorn](https://www.uvicorn.org/) - Servidor ASGI

---

**Última atualização:** 17 de Abril de 2026 | **Versão:** v0.1.0

