# Troubleshooting

Soluções para problemas comuns ao usar o PDF Field Labeler.

## Instalação

### Problema: "ModuleNotFoundError: No module named 'fastapi'"

**Solução:**
Certifique-se que o ambiente está ativado e dependências instaladas.

```bash
# Com Conda
conda activate pdf-form-labeler
python -c "import fastapi"

# Com venv
venv\Scripts\activate
pip install -r requirements.txt
```

Se persistir, reinstale tudo:
```bash
pip install --upgrade --force-reinstall -r requirements.txt
```

### Problema: "conda activate não funciona"

**Solução:**
```bash
# Inicializar conda para PowerShell
conda init powershell

# Fechar e reabrir o terminal

# Se ainda não funcionar, use:
conda run -n pdf-form-labeler python -c "print('OK')"
```

---

## Execução do Servidor

### Problema: "Porta 8000 já está em uso"

**Solução:**
```bash
# Usar outra porta
uvicorn web.app:app --port 8001

# Ou encerrar o processo que usa a porta
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8000
kill -9 <PID>
```

### Problema: "Address already in use"

**Solução:**
```bash
# Port já em uso de execução anterior
uvicorn web.app:app --port 8001

# Ou aguarde 30 segundos e tente novamente
```

### Problema: "Connection refused" ao acessar localhost:8000

**Solução:**
1. Verifique se o servidor está realmente rodando
2. Tente `http://127.0.0.1:8000` em vez de `localhost`
3. Verifique firewall
4. Tente outra porta: `--port 8001`

---

## PDF não carrega / Campos não aparecem

### Problema: "FileNotFoundError: PDF not found"

**Solução:**
- Verifique se o caminho está correto
- Use caminhos relativos a partir da pasta raiz do repositório
- Para uploads, use a path retornada pelo `/api/upload`

### Problema: PDF carrega mas não há campos

**Possíveis causas:**

1. **PDF sem campos AcroForm**
   - O PDF é apenas um documento de imagem
   - Solução: Use PDF com formulários interativos

2. **Campos não estão marcados como interativos**
   - Solução: Abra em Adobe Acrobat → Tools → Prepare Form → Se não mostrar formulário, não há campos interativos

3. **PDF corrompido**
   - Solução: Tente converter com outro software e fazer upload novamente

### Problema: Alguns campos não aparecem

**Solução:**
- Alguns campos podem estar ocultos ou desabilitados
- Use `scripts/extract_pdf_field_metadata.py` diretamente para debug
- Verifique se a PDF tem `/Fields` definido

---

## Normalização e Saída

### Problema: "PDF normalizado não mostra as mudanças"

**Solução:**
1. Certifique-se de que o mapeamento foi salvo
2. Use `--verify` para checar integridade
3. Abra o PDF em Adobe Acrobat (não apenas preview)
4. Use `Ctrl+Shift+R` no navegador para limpar cache

### Problema: "Erro ao aplicar normalização: Permission denied"

**Solução:**
```bash
# A pasta data/out/ precisa existir
mkdir data/out

# Ou use um caminho diferente com permissões
python scripts/normalize_pdf_fields.py \
  input.pdf \
  C:\Users\seu_usuario\Documents\output.pdf \
  --map map.json
```

### Problema: Arquivo PDF gerado fica corrompido

**Solução:**
1. Tente sem `--fill`:
   ```bash
   python scripts/normalize_pdf_fields.py \
     input.pdf \
     output.pdf \
     --map map.json
   ```

2. Se não for reproduzível, pode ser a PyPDF
   - Atualize: `pip install --upgrade pypdf`

3. Tente PDF simpler sem criptografia

---

## Web UI

### Problema: Preview do PDF não renderiza

**Solução:**
Poppler não está instalado:

```bash
# Windows (choco)
choco install poppler

# macOS
brew install poppler

# Linux (Debian/Ubuntu)
sudo apt-get install poppler-utils
```

Se não quiser usar preview, desabilite em `web/app.py`.

### Problema: Campos não sincronizam com o input

**Solução:**
- Feche e reabra o navegador
- Use `Ctrl+Shift+R` para hard reload
- Limpe cookies: DevTools → Application → Clear Storage
- Se persistir, verifique `web/static/app.js`

### Problema: Dropdown não carrega campos

**Solução:**
```bash
# Verifique se /api/fields funciona
curl "http://localhost:8000/api/fields?input_pdf=data/uploads/form.pdf"

# Se houver erro, o servidor pode estar com problema
# Reinicie com verbosity:
uvicorn web.app:app --log-level debug
```

---

## Performance

### Problema: Processamento muito lento para PDFs grandes

**Solução:**
1. PDFs com muitos campos (300+) demoram naturalmente
2. Use processamento em lote com script CLI
3. Considere usar workers do Uvicorn:
   ```bash
   uvicorn web.app:app --workers 4
   ```

### Problema: Out of Memory com PDFs muito grandes

**Solução:**
1. Processe PDFs menores em separado
2. Use linha de comando em vez de Web UI
3. Aumente memória do Python:
   ```bash
   python -u scripts/normalize_pdf_fields.py ...
   ```

---

## Issues de Integração

### Problema: Como integrar com minha aplicação?

**Solução:**
1. Use a API REST (veja [API.md](API.md))
2. Ou importe os scripts Python diretamente:
   ```python
   from scripts.extract_pdf_field_metadata import extract_metadata_from_pdf
   ```

### Problema: Preciso processar 1000 PDFs

**Solução:**
Use um script batch:
```bash
for pdf in *.pdf; do
    python scripts/extract_pdf_field_metadata.py "$pdf" "${pdf%.pdf}_meta.json"
    python scripts/normalize_pdf_fields.py "$pdf" "out/${pdf}" --map map.json --verify
done
```

---

## Windows Específico

### Problema: `.ps1` não executa: "not digitally signed"

**Solução:**
```powershell
# Permitir execução apenas desta sessão
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Depois execute
.\start_server.ps1
```

### Problema: "python command not found"

**Solução:**
```powershell
# Python não está no PATH
# Options:

# 1. Use conda ativado
conda activate pdf-form-labeler

# 2. Use path completo
C:\Python39\python.exe script.py

# 3. Reinstale Python com "Add to PATH" ativado
```

---

## Debugging

### Ativar Logs Detalhados

```bash
# Com verbosity
uvicorn web.app:app --log-level debug
```

### Testar Endpoints Diretamente

```bash
# Teste /api/fields
curl -v "http://localhost:8000/api/fields?input_pdf=data/sample/pdf-field-metadata.json"

# Teste /api/upload
curl -F "file=@test.pdf" http://localhost:8000/api/upload
```

### Inspecionar Código Python

Adicione debug prints:
```python
# Em web/app.py
print(f"DEBUG: pdf_path = {pdf_path}")
print(f"DEBUG: fields count = {len(fields)}")
```

---

## Contato e Reportar Issues

Se o problema persiste:

1. Abra uma [Issue](https://github.com/andre12burger/PDF-Field-Labeler/issues) no GitHub
2. Inclua:
   - Seu SO (Windows/Mac/Linux)
   - Versão do Python
   - Stacktrace do erro
   - Arquivo de exemplo se possível

---

## Recursos Adicionais

- [INSTALLATION.md](INSTALLATION.md) - Guia de instalação
- [USAGE.md](USAGE.md) - Guia de uso
- [API.md](API.md) - Documentação da API
- [../README.md](../README.md) - Visão geral do projeto
