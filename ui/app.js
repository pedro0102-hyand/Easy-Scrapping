const form = document.getElementById("ask-form");
const perguntaEl = document.getElementById("pergunta");
const tipoEl = document.getElementById("tipo");
const kEl = document.getElementById("k");
const autorEl = document.getElementById("autor");
const btn = document.getElementById("btn-perguntar");
const statusEl = document.getElementById("status");
const resultadoEl = document.getElementById("resultado");
const respostaEl = document.getElementById("resposta");
const fontesEl = document.getElementById("fontes");

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

function renderizarFontes(documentos) {
  fontesEl.innerHTML = "";

  if (!documentos || documentos.length === 0) {
    const vazio = document.createElement("li");
    vazio.textContent = "Nenhum documento recuperado.";
    fontesEl.appendChild(vazio);
    return;
  }

  documentos.forEach((doc, indice) => {
    const meta = doc.metadados || {};
    const item = document.createElement("li");
    item.style.animationDelay = `${indice * 0.05}s`;

    const cabecalho = document.createElement("div");
    cabecalho.className = "source__meta";
    cabecalho.innerHTML = `
      <span>${meta.tipo_documento || "documento"}</span>
      <span>score ${Number(doc.score || 0).toFixed(3)}</span>
    `;

    const autor = document.createElement("p");
    autor.className = "source__autor";
    autor.textContent = meta.autor || "Autor desconhecido";

    item.appendChild(cabecalho);
    item.appendChild(autor);

    if (meta.url_origem) {
      const link = document.createElement("a");
      link.className = "source__link";
      link.href = meta.url_origem;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = meta.url_origem;
      item.appendChild(link);
    }

    fontesEl.appendChild(item);
  });
}

async function enviarPergunta(event) {
  event.preventDefault();
  limparErro();

  const pergunta = perguntaEl.value.trim();
  if (!pergunta) {
    mostrarErro("Digite uma pergunta.");
    return;
  }

  const payload = {
    pergunta,
    k: Number(kEl.value) || 5,
    tipo_documento: tipoEl.value || null,
    autor: autorEl.value.trim() || null,
  };

  setLoading(true);
  resultadoEl.hidden = true;

  try {
    const resposta = await fetch("/api/perguntar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const dados = await resposta.json();

    if (!resposta.ok) {
      throw new Error(dados.erro || "Falha ao consultar o RAG.");
    }

    respostaEl.textContent = dados.resposta;
    renderizarFontes(dados.documentos);
    resultadoEl.hidden = false;
    resultadoEl.scrollIntoView({ behavior: "smooth", block: "start" });
    statusEl.textContent = `${dados.documentos.length} documento(s) usados.`;
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
