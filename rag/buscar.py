"""Busca semântica no índice vetorial, ainda sem uso de LLM."""

import argparse # Para permitir execução via linha de comando.
from rag.embeddings import carregar_modelo, gerar_embeddings
from rag.indice import DIRETORIO_INDICE, carregar_indice


TIPOS_DOCUMENTO = {"citacao", "biografia"}


def buscar(pergunta, k=5, tipo_documento=None, diretorio=DIRETORIO_INDICE):

    """Retorna os documentos semanticamente mais próximos da pergunta."""

    pergunta = pergunta.strip()

    if not pergunta:

        raise ValueError("A pergunta não pode estar vazia.")

    if k <= 0:

        raise ValueError("O número de resultados deve ser maior que zero.")

    if tipo_documento and tipo_documento not in TIPOS_DOCUMENTO:

        raise ValueError(
            f"Tipo inválido. Use um destes: {', '.join(sorted(TIPOS_DOCUMENTO))}."
        )

    indice, documentos, manifesto = carregar_indice(diretorio)
    modelo = carregar_modelo(manifesto["modelo_embeddings"])
    vetor_pergunta = gerar_embeddings([pergunta], modelo=modelo)

    # Quando há filtro, consultamos todo o pequeno índice e filtramos depois.
    # Sem filtro, o FAISS precisa devolver apenas os k melhores.
    quantidade_busca = indice.ntotal if tipo_documento else min(k, indice.ntotal)
    scores, posicoes = indice.search(vetor_pergunta, quantidade_busca)
    resultados = []

    for score, posicao in zip(scores[0], posicoes[0]):

        if posicao < 0:
            continue

        documento = documentos[int(posicao)]
        if (
            tipo_documento
            and documento["metadados"]["tipo_documento"] != tipo_documento
        ):
            continue

        resultados.append({
            **documento,
            "score": float(score),
        })

        if len(resultados) == k:
            break

    return resultados


def exibir_resultados(resultados):

    """Exibe os resultados da busca de forma legível no terminal."""

    if not resultados:
        
        print("Nenhum documento encontrado.")
        return

    for posicao, resultado in enumerate(resultados, start=1):
        metadados = resultado["metadados"]
        print("\n" + "=" * 70)
        print(
            f"{posicao}. Score: {resultado['score']:.4f} | "
            f"Tipo: {metadados['tipo_documento']} | "
            f"Autor: {metadados['autor']}"
        )
        print("-" * 70)
        print(resultado["texto_indexacao"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Busca semântica nas citações e biografias."
    )
    parser.add_argument("pergunta", help="Texto que deseja pesquisar.")
    parser.add_argument(
        "-k",
        type=int,
        default=5,
        help="Quantidade de resultados (padrão: 5).",
    )
    parser.add_argument(
        "--tipo",
        choices=sorted(TIPOS_DOCUMENTO),
        help="Filtra por citacao ou biografia.",
    )
    argumentos = parser.parse_args()

    exibir_resultados(
        buscar(
            argumentos.pergunta,
            k=argumentos.k,
            tipo_documento=argumentos.tipo,
        )
    )
