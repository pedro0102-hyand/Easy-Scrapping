"""gera respostas com LLM a partir do contexto recuperado.

Fluxo:
1. Retriever busca os documentos mais próximos da pergunta.
2. O contexto é montado e enviado ao Groq (Llama 3.3 70B).
3. O modelo responde só com base nesse contexto, citando fontes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from rag.retriever import Retriever, buscar

MODELO_GROQ = "llama-3.3-70b-versatile"
TEMPERATURA = 0.5

PROMPT_SISTEMA = """Você é um assistente de perguntas e respostas sobre citações e biografias.

Regras obrigatórias:
1. Responda APENAS com base no contexto fornecido.
2. Se o contexto não tiver informação suficiente, diga claramente que não encontrou a resposta nos dados.
3. NÃO invente citações, autores, datas ou fatos.
4. Quando usar uma citação, reproduza o texto com fidelidade e cite o autor.
5. Ao final, liste as fontes usadas no formato:
   Fontes:
   - Autor | tipo | url
6. Responda em português, de forma clara e objetiva.
"""


def carregar_chave_groq():

    raiz = Path(__file__).resolve().parent.parent
    load_dotenv(raiz / ".env")

    chave = os.getenv("GROQ_API_KEY", "").strip()
    if not chave:

        raise EnvironmentError(
            "GROQ_API_KEY não encontrada. "
            "Cadastre a chave no arquivo .env do projeto."
        )

    return chave


def montar_contexto(documentos):


    if not documentos:

        return "Nenhum documento relevante foi encontrado."

    blocos = []

    for i, documento in enumerate(documentos, start=1):

        metadados = documento["metadados"]
        blocos.append(
            f"[Documento {i}]\n"
            f"Tipo: {metadados.get('tipo_documento')}\n"
            f"Autor: {metadados.get('autor')}\n"
            f"Score: {documento['score']:.4f}\n"
            f"Fonte: {metadados.get('url_origem')}\n"
            f"Conteúdo:\n{documento['texto_indexacao']}"
        )

    return "\n\n".join(blocos)


def extrair_fontes(documentos):

    fontes = []
    vistas = set()

    for documento in documentos:

        metadados = documento["metadados"]
        chave = (
            metadados.get("autor"),
            metadados.get("tipo_documento"),
            metadados.get("url_origem"),
        )

        if chave in vistas:

            continue

        vistas.add(chave)
        fontes.append({
            "autor": metadados.get("autor"),
            "tipo_documento": metadados.get("tipo_documento"),
            "url_origem": metadados.get("url_origem"),
            "score": documento["score"],
        })

    return fontes


def chamar_llm(pergunta, contexto, modelo=MODELO_GROQ):

    cliente = Groq(api_key=carregar_chave_groq())
    prompt_usuario = (
        f"Contexto:\n{contexto}\n\n"
        f"Pergunta: {pergunta}\n\n"
        "Responda com base apenas no contexto acima."
    )

    resposta = cliente.chat.completions.create(
        model=modelo,
        temperature=TEMPERATURA,
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": prompt_usuario},
        ],
    )

    return resposta.choices[0].message.content.strip()


def perguntar(
    pergunta,
    k=5,
    tipo_documento=None,
    autor=None,
    tag=None,
    score_minimo=None,
    retriever=None,
):
    

    pergunta = (pergunta or "").strip()

    if not pergunta:

        raise ValueError("A pergunta não pode estar vazia.")

    if retriever is None:

        documentos = buscar(
            pergunta,
            k=k,
            tipo_documento=tipo_documento,
            autor=autor,
            tag=tag,
            score_minimo=score_minimo,
        )

    else:

        documentos = retriever.buscar(
            pergunta,
            k=k,
            tipo_documento=tipo_documento,
            autor=autor,
            tag=tag,
            score_minimo=score_minimo,
        )

    contexto = montar_contexto(documentos)
    resposta = chamar_llm(pergunta, contexto)

    return {
        "pergunta": pergunta,
        "resposta": resposta,
        "documentos": documentos,
        "fontes": extrair_fontes(documentos),
    }


def exibir_resposta(resultado):


    print("\n" + "=" * 70)
    print(f"Pergunta: {resultado['pergunta']}")
    print("=" * 70)
    print(resultado["resposta"])
    print("\n" + "-" * 70)
    print(f"Documentos usados: {len(resultado['documentos'])}")
    for i, documento in enumerate(resultado["documentos"], start=1):
        metadados = documento["metadados"]
        print(
            f"  {i}. [{metadados['tipo_documento']}] "
            f"{metadados['autor']} | score={documento['score']:.4f}"
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Pergunta ao RAG (retriever + Groq Llama 3.3 70B)."
    )
    parser.add_argument("pergunta", help="Pergunta em português ou inglês.")
    parser.add_argument("-k", type=int, default=5, help="Quantidade de documentos.")
    parser.add_argument(
        "--tipo",
        choices=["citacao", "biografia"],
        help="Filtra por tipo de documento.",
    )
    parser.add_argument("--autor", help="Filtra por autor.")
    parser.add_argument("--tag", help="Filtra por tag.")
    parser.add_argument(
        "--score-minimo",
        type=float,
        help="Score mínimo de similaridade.",
    )
    argumentos = parser.parse_args()

    resultado = perguntar(
        argumentos.pergunta,
        k=argumentos.k,
        tipo_documento=argumentos.tipo,
        autor=argumentos.autor,
        tag=argumentos.tag,
        score_minimo=argumentos.score_minimo,
    )
    exibir_resposta(resultado)
