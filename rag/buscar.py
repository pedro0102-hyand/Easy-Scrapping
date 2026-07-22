import argparse
from rag.retriever import TIPOS_DOCUMENTO, buscar

def exibir_resultados(resultados):

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
    parser.add_argument("-k", type=int, default=5, help="Quantidade de resultados (padrão: 5).")
    parser.add_argument("--tipo", choices=sorted(TIPOS_DOCUMENTO), help="Filtra por citacao ou biografia.")
    parser.add_argument("--autor", help="Filtra por autor (correspondência parcial, sem diferenciar maiúsculas).")
    parser.add_argument("--tag", help="Filtra citações por tag exata.")
    parser.add_argument("--score-minimo", type=float,help="Descarta resultados abaixo deste score (entre -1.0 e 1.0).",
    )
    argumentos = parser.parse_args()

    exibir_resultados(
        buscar(
            argumentos.pergunta,
            k=argumentos.k,
            tipo_documento=argumentos.tipo,
            autor=argumentos.autor,
            tag=argumentos.tag,
            score_minimo=argumentos.score_minimo,
        )
    )
