# PDF para EPUB

Conversor online de **PDF para EPUB**, para ler livros e apostilas em Kindle, Kobo e aplicativos de leitura. Sem login: escolha o PDF, converta e baixe o EPUB.

**Site:** https://alex-m-silva.github.io/pdf-para-epub/

## Como funciona

```
Navegador (GitHub Pages)  ──PDF──▶  API FastAPI (Render, Docker)  ──▶  Calibre (ebook-convert)
        ▲                                                                     │
        └──────────────────────────────── EPUB ◀──────────────────────────────┘
```

- **Front-end:** HTML, CSS e JavaScript puros, publicados no GitHub Pages. Fila de arquivos, arrastar e soltar, e indicador de status do servidor.
- **Back-end:** Python com FastAPI, empacotado em Docker com o Calibre instalado. Recebe o PDF, roda o `ebook-convert` e devolve o EPUB.
- **Conteúdo:** guias sobre leitura digital (enviar EPUB para o Kindle, PDF escaneado vs. PDF com texto etc.).

## Segurança e limites da API

- Limite de tamanho do upload (verificado no `Content-Length` e durante o recebimento)
- Rate limit por IP e limite de conversões simultâneas
- Timeout na conversão e nova tentativa sem as opções heurísticas quando a primeira falha
- Arquivos em pasta temporária com nome aleatório, apagados após a resposta e numa limpeza periódica
- `TrustedHostMiddleware`, CORS restrito e cabeçalhos de segurança

## Estrutura

| Arquivo | O que é |
|---|---|
| `index.html`, `styles.css`, `app.js` | página do conversor |
| `config.js` | endereço da API (local ou Render) |
| `api.py` | API FastAPI que roda o Calibre |
| `Dockerfile`, `requirements.txt` | imagem com Python e Calibre |
| `render.yaml` | blueprint para publicar a API no Render |
| `guias.html` e artigos | conteúdo sobre leitura digital |
| `privacy.html`, `terms.html`, `contact.html` | páginas institucionais |

## Rodar localmente

Precisa do [Calibre](https://calibre-ebook.com/download) instalado (comando `ebook-convert` no PATH).

```bash
pip install -r requirements.txt
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000. Localmente, as páginas e a API rodam no mesmo servidor.

Ou com Docker:

```bash
docker build -t pdf-para-epub .
docker run -p 8000:8000 pdf-para-epub
```

## API

- `GET /api/health`: verifica se a API está online.
- `GET /api/version`: versão ativa do back-end.
- `POST /api/convert`: recebe `multipart/form-data` com o campo `file` e retorna o `.epub`.

## Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `MAX_UPLOAD_MB` | `50` | tamanho máximo do PDF |
| `CONVERSION_TIMEOUT_SECONDS` | `180` | tempo máximo do Calibre |
| `MAX_CONCURRENT_CONVERSIONS` | `2` | conversões ao mesmo tempo |
| `RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | `30` / `60` | limite por IP |
| `TEMP_FILE_TTL_MINUTES` | `30` | idade máxima dos temporários |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost,*.onrender.com` | hosts aceitos |
| `ALLOWED_ORIGINS` | `http://127.0.0.1:8000,http://localhost:8000` | origens CORS |
| `SHOW_CONVERSION_ERRORS` | `1` | `1` mostra o erro do Calibre (dev); `0` em produção |

Publicação: veja [`DEPLOYMENT.md`](DEPLOYMENT.md).
