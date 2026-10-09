# Publicação

O projeto tem duas partes, publicadas em lugares diferentes:

| Parte | Onde | Por quê |
|---|---|---|
| Páginas (HTML, CSS, JS) | GitHub Pages | grátis e rápido para arquivos estáticos |
| API de conversão | Render (plano gratuito, Docker) | o Calibre precisa de um servidor com binários do sistema |

## 1. Front-end no GitHub Pages

Já configurado: em **Settings → Pages**, branch `master`, pasta `/ (root)`. Cada push na `master` publica em
https://alex-m-silva.github.io/pdf-para-epub/.

Os links entre as páginas são relativos, porque o site fica na subpasta `/pdf-para-epub/`.

## 2. API no Render

1. Entre em https://render.com com a conta do GitHub.
2. **New → Blueprint** e escolha o repositório `pdf-para-epub`. O Render lê o [`render.yaml`](render.yaml) e cria o serviço `pdf-para-epub` com as variáveis de ambiente.
3. Quando o deploy terminar, teste: `https://pdf-para-epub.onrender.com/api/health` deve responder `{"status":"ok"}`.
4. Se o Render der outro endereço ao serviço (por exemplo, se o nome já estiver em uso), troque a URL em [`config.js`](config.js) e faça push.

O plano gratuito "dorme" após uns 15 minutos sem uso. Ao abrir o site, o `app.js` já manda um ping para acordar o servidor e mostra o status ("Acordando o servidor…" → "Servidor online"). A primeira conversão depois disso pode levar até um minuto.

## Domínio próprio (opcional)

Para usar um subdomínio (ex.: `epub.seudominio.com`):

1. Em **Settings → Pages → Custom domain**, informe o subdomínio e crie no DNS um `CNAME` apontando para `alex-m-silva.github.io`.
2. Acrescente o novo endereço em `ALLOWED_ORIGINS` no Render.
3. Atualize os links `canonical`, `sitemap.xml` e `robots.txt`.
