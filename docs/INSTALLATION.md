# Instalação

Guia detalhado para instalar o PDF Field Labeler no seu sistema.

## Requisitos do Sistema

- **Python**: 3.8 ou superior
- **Git**: Para clonar o repositório
- **Espaço em disco**: ~500MB (incluindo ambientes virtuais)
- **SO**: Windows, macOS ou Linux

## Opção 1: Com Conda (Recomendado)

Conda gerencia automaticamente as dependências e cria um ambiente isolado.

### Passo 1: Clonar o Repositório

```bash
git clone https://github.com/andre12burger/PDF-Field-Labeler.git
cd PDF-Field-Labeler
```

### Passo 2: Criar Ambiente Conda

```bash
conda env create -f environment.yml
```

### Passo 3: Ativar Ambiente

```bash
# Windows (PowerShell)
conda init powershell
# Fechar e reabrir o terminal

conda activate pdf-form-labeler
```

### Validar Instalação

```bash
python -c "import fastapi, uvicorn, pypdf; print('✓ Tudo OK')"
```

## Opção 2: Com venv (Alternativa Leve)

Usa apenas pip, sem dependências externas.

### Passo 1: Clonar e Navegar

```bash
git clone https://github.com/andre12burger/PDF-Field-Labeler.git
cd PDF-Field-Labeler
```

### Passo 2: Criar Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Validar Instalação

```bash
python -c "import fastapi, uvicorn, pypdf; print('✓ Tudo OK')"
```

## Opção 3: Com Poetry (Alternativa Profissional)

Se você usa Poetry para gerenciamento de dependências:

```bash
git clone https://github.com/andre12burger/PDF-Field-Labeler.git
cd PDF-Field-Labeler

poetry install
poetry shell
```

## Dependências Principais

| Pacote | Versão | Função |
|--------|--------|--------|
| `pypdf` | ≥3.14.0 | Leitura e escrita de PDFs |
| `fastapi` | ≥0.112.0 | Framework web para API |
| `uvicorn` | ≥0.23.0 | Servidor ASGI |
| `pdf2image` | ≥1.16.0 | Conversão PDF → imagem |
| `Pillow` | ≥10.0.0 | Processamento de imagens |

Veja [requirements.txt](../requirements.txt) para a lista completa.

## Requisitos Adicionais por Sistema

### Windows

Para preview de páginas (opcional):

```powershell
# Instalar Poppler
choco install poppler
# ou baixe de: https://github.com/oschwartz10612/poppler-windows/releases/
```

### macOS

```bash
brew install poppler
```

### Linux (Debian/Ubuntu)

```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

## Verificação de Ambiente

Para confirmar que tudo está instalado corretamente:

```bash
# Windows (PowerShell)
conda activate pdf-form-labeler
python -c "import multipart, fastapi, uvicorn, pypdf, pdf2image, PIL; print('✓ Todas as dependências OK')"

# macOS / Linux
source venv/bin/activate
python -c "import multipart, fastapi, uvicorn, pypdf, pdf2image, PIL; print('✓ Todas as dependências OK')"
```

Se receber erro, revise os passos ou consulte [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Próximos Passos

Depois de instalar, consulte:
- [USAGE.md](USAGE.md) - Como executar e usar o programa
- [API.md](API.md) - Documentação dos endpoints
