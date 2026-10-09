// Endereço da API de conversão.
// - Rodando localmente (uvicorn), a API está no mesmo servidor das páginas.
// - Publicado no GitHub Pages, as páginas são estáticas e a API roda no Render.
//   Se o serviço no Render tiver outro nome, troque a URL abaixo.
window.API_BASE_URL = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname)
  ? ""
  : "https://pdf-para-epub.onrender.com";
