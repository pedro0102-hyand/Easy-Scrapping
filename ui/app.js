const form = document.getElementById("ask-form");
const perguntaEl = document.getElementById("pergunta");
const btn = document.getElementById("btn-perguntar");
const statusEl = document.getElementById("status");
const resultadoEl = document.getElementById("resultado");
const respostaEl = document.getElementById("resposta");
const themeToggle = document.getElementById("theme-toggle");

const K_PADRAO = 5;
const THEME_KEY = "quotes-ai-theme";

function temaAtual() {
  return document.documentElement.getAttribute("data-theme") || "light";
}

function aplicarTema(tema) {
  const proximo = tema === "dark" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", proximo);
  localStorage.setItem(THEME_KEY, proximo);
  if (themeToggle) {
    themeToggle.setAttribute(
      "aria-label",
      proximo === "dark" ? "Ativar modo claro" : "Ativar modo escuro"
    );
  }
}

function alternarTema() {
  aplicarTema(temaAtual() === "dark" ? "light" : "dark");
}

aplicarTema(temaAtual());
if (themeToggle) {
  themeToggle.addEventListener("click", alternarTema);
}

function setLoading(loading) {
  btn.disabled = loading;
  btn.classList.toggle("is-loading", loading);
  statusEl.textContent = loading ? "Consultando o acervo…" : "";
}

function limparErro() {
  const antigo = document.querySelector(".error");
  if (antigo) antigo.remove();
}

function mostrarErro(mensagem) {
  limparErro();
  const erro = document.createElement("p");
  erro.className = "error";
  erro.textContent = mensagem;
  form.insertAdjacentElement("afterend", erro);
}

async function enviarPergunta(event) {
  event.preventDefault();
  limparErro();

  const pergunta = perguntaEl.value.trim();
  if (!pergunta) {
    mostrarErro("Digite uma pergunta.");
    return;
  }

  setLoading(true);
  resultadoEl.hidden = true;

  try {
    const respostaHttp = await fetch("/api/perguntar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pergunta,
        k: K_PADRAO,
      }),
    });

    const texto = await respostaHttp.text();
    let dados;

    try {
      dados = JSON.parse(texto);
    } catch {
      throw new Error(
        "A API não devolveu JSON. Confirme que o servidor está em http://127.0.0.1:5001"
      );
    }

    if (!respostaHttp.ok) {
      throw new Error(dados.erro || "Falha ao consultar o RAG.");
    }

    if (!dados.resposta) {
      throw new Error("Resposta vazia do servidor.");
    }

    respostaEl.textContent = dados.resposta;
    resultadoEl.hidden = false;
    resultadoEl.scrollIntoView({ behavior: "smooth", block: "start" });
    statusEl.textContent = "";
  } catch (erro) {
    mostrarErro(erro.message || "Erro inesperado.");
    statusEl.textContent = "";
  } finally {
    setLoading(false);
  }
}

form.addEventListener("submit", enviarPergunta);

perguntaEl.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    form.requestSubmit();
  }
});
