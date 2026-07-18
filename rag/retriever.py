"""Camada de retriever: busca semântica reutilizável sobre o índice vetorial.

Diferente de chamar `buscar` avulso, a classe `Retriever` carrega o índice,
os documentos e o modelo de embeddings uma única vez e reaproveita tudo entre
consultas. Isso evita reler o disco e recarregar o modelo a cada pergunta.
"""

from functools import lru_cache

from rag.embeddings import carregar_modelo, gerar_embeddings
from rag.indice import DIRETORIO_INDICE, carregar_indice


TIPOS_DOCUMENTO = {"citacao", "biografia"}


def _corresponde_filtros(documento, tipo_documento, autor, tag):
    """Verifica se um documento satisfaz todos os filtros informados."""

    metadados = documento["metadados"]

    if tipo_documento and metadados.get("tipo_documento") != tipo_documento:

        return False

    if autor:

        autor_documento = (metadados.get("autor") or "").casefold()

        if autor.casefold() not in autor_documento:

            return False

    if tag:

        tags = [t.casefold() for t in (metadados.get("tags") or [])]
        if tag.casefold() not in tags:
            return False

    return True


class Retriever:
    
    """Encapsula o índice vetorial e expõe uma API de busca com filtros."""

    def __init__(self, diretorio=DIRETORIO_INDICE):
        self.indice, self.documentos, self.manifesto = carregar_indice(diretorio)
        self.modelo = carregar_modelo(self.manifesto["modelo_embeddings"])

    def buscar(
        self,
        pergunta,
        k=5,
        tipo_documento=None,
        autor=None,
        tag=None,
        score_minimo=None,
    ):
        """Retorna os `k` documentos mais próximos que satisfazem os filtros."""

        pergunta = (pergunta or "").strip()
        if not pergunta:
            raise ValueError("A pergunta não pode estar vazia.")

        if k <= 0:
            raise ValueError("O número de resultados deve ser maior que zero.")

        if tipo_documento and tipo_documento not in TIPOS_DOCUMENTO:
            raise ValueError(
                f"Tipo inválido. Use um destes: {', '.join(sorted(TIPOS_DOCUMENTO))}."
            )

        if score_minimo is not None and not -1.0 <= score_minimo <= 1.0:
            raise ValueError("O score mínimo deve estar entre -1.0 e 1.0.")

        tem_filtro = any((tipo_documento, autor, tag, score_minimo is not None))

        # Com filtros, varremos todo o índice (pequeno) e filtramos depois.
        # Sem filtros, basta pedir os k melhores diretamente ao FAISS.
        quantidade_busca = self.indice.ntotal if tem_filtro else min(k, self.indice.ntotal)

        vetor_pergunta = gerar_embeddings([pergunta], modelo=self.modelo)
        scores, posicoes = self.indice.search(vetor_pergunta, quantidade_busca)

        resultados = []
        for score, posicao in zip(scores[0], posicoes[0]):
            if posicao < 0:
                continue

            score = float(score)
            if score_minimo is not None and score < score_minimo:
                continue

            documento = self.documentos[int(posicao)]
            if not _corresponde_filtros(documento, tipo_documento, autor, tag):
                continue

            resultados.append({**documento, "score": score})

            if len(resultados) == k:
                break

        return resultados


@lru_cache(maxsize=1)
def _retriever_padrao(diretorio=DIRETORIO_INDICE):
    """Reaproveita uma única instância de `Retriever` entre chamadas."""

    return Retriever(diretorio)


def buscar(pergunta, k=5, diretorio=DIRETORIO_INDICE, **filtros):
    """Atalho de módulo: usa um `Retriever` compartilhado (carregado uma vez)."""

    return _retriever_padrao(diretorio).buscar(pergunta, k=k, **filtros)
