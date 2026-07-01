# PDF para EPUB

Site para converter arquivos PDF em EPUB pelo navegador.

## Estrutura

- `index.html`: pagina principal do conversor.
- `styles.css`: layout responsivo.
- `app.js`: upload, fila e chamada da API.
- `api.py`: backend FastAPI que roda `ebook-convert`.
- `requirements.txt`: dependencias Python.
- `Dockerfile`: imagem de publicacao com Python e Calibre.
- `ROADMAP.md`: controle interno do projeto.
- `privacy.html`, `terms.html`, `contact.html`: paginas basicas para publicacao e revisao de anuncios.
- `ads.txt`: placeholder para o codigo do AdSense apos aprovacao.
- `DEPLOYMENT.md`: guia de publicacao barata e preparacao para anuncios.
- `MONETIZATION.md`: plano de renda passiva sem custo inicial.
- `guias.html` e artigos: conteudo inicial para SEO.

## Rodar localmente

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Inicie a aplicacao:

```bash
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Abra:

```text
http://127.0.0.1:8000
```

## API

- `GET /api/health`: verifica se a API esta online.
- `GET /api/version`: mostra a versao ativa do backend.
- `POST /api/convert`: recebe `multipart/form-data` com o campo `file` e retorna um `.epub`.

## Variaveis de ambiente

- `MAX_UPLOAD_MB`: limite de upload em MB.
- `CONVERSION_TIMEOUT_SECONDS`: timeout do Calibre.
- `MAX_CONCURRENT_CONVERSIONS`: conversoes simultaneas.
- `RATE_LIMIT_MAX_REQUESTS`: limite por IP dentro da janela.
- `RATE_LIMIT_WINDOW_SECONDS`: janela do rate limit.
- `TEMP_FILE_TTL_MINUTES`: idade maxima para limpeza de diretorios temporarios antigos.
- `ALLOWED_HOSTS`: hosts aceitos pelo backend.
- `ALLOWED_ORIGINS`: origens CORS aceitas.
- `SHOW_CONVERSION_ERRORS`: use `1` em desenvolvimento e `0` em producao.

## Conversao

A API usa o Calibre:

```bash
ebook-convert entrada.pdf saida.epub --enable-heuristics --html-unwrap-factor 0.40 --page-breaks-before /
```

Para publicar, o backend precisa de um ambiente que suporte Docker ou instalacao do Calibre.
