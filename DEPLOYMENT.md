# Publicacao com baixo custo

## Recomendacao para o MVP

Use um unico backend Docker no Render Free para testar o produto publicado.

Motivo: o conversor depende do Calibre, e o Calibre precisa rodar em um ambiente com binarios do sistema. Um site puramente estatico no Cloudflare Pages nao consegue executar `ebook-convert`.

## Caminho 1: custo zero para validar

1. Criar conta no Render.
2. Criar um Web Service a partir do repositorio.
3. Usar deploy via Dockerfile.
4. Configurar variaveis:

```text
MAX_UPLOAD_MB=50
CONVERSION_TIMEOUT_SECONDS=180
MAX_CONCURRENT_CONVERSIONS=1
RATE_LIMIT_MAX_REQUESTS=30
RATE_LIMIT_WINDOW_SECONDS=60
TEMP_FILE_TTL_MINUTES=30
SHOW_CONVERSION_ERRORS=0
ALLOWED_HOSTS=seu-servico.onrender.com
ALLOWED_ORIGINS=https://seu-servico.onrender.com
```

5. Testar:

```text
https://seu-servico.onrender.com/api/version
https://seu-servico.onrender.com/privacy.html
https://seu-servico.onrender.com/terms.html
https://seu-servico.onrender.com/contact.html
```

Ponto fraco: Render Free hiberna com inatividade e o primeiro acesso pode demorar.

## Caminho 2: melhor para producao barata

Use Cloudflare Pages para o front e um backend Docker pago barato para a API.

Vantagens:

- Front rapido e gratuito.
- Backend separado pode escalar ou ser trocado depois.
- Mais facil adicionar Cloudflare WAF, cache e dominio.

Variavel importante no front quando separar:

```javascript
const API_BASE_URL = "https://api.seudominio.com";
```

Hoje o front usa `/api/convert` porque front e backend estao no mesmo servidor.

## AdSense

Antes de pedir revisao:

- Substituir `SEU-DOMINIO.com` em `sitemap.xml` e `robots.txt`.
- Trocar os textos placeholder das paginas `privacy.html` e `contact.html`.
- Publicar com dominio real.
- Garantir que `ads.txt` esteja acessivel em `/ads.txt`.
- Criar conteudo original suficiente alem da ferramenta, por exemplo:
  - Como converter PDF para EPUB
  - Como enviar EPUB para Kindle
  - Por que alguns PDFs nao convertem bem
  - PDF escaneado vs PDF com texto selecionavel
- Nao clicar nos proprios anuncios.

Nao conte com anuncios aparecendo no primeiro dia. O site precisa passar por revisao, e a aprovacao depende de conteudo, navegacao, politicas e conformidade.
