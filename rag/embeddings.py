"""Geração de embeddings multilíngues para os documentos do RAG."""

from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer

NOME_MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1) # Mantém o modelo carregado em cache para evitar recarregamentos desnecessários.

def carregar_modelo(nome_modelo=NOME_MODELO):

    """Carrega o modelo uma única vez durante a execução."""

    try:

        return SentenceTransformer(nome_modelo, local_files_only=True)
    
    except OSError:

        return SentenceTransformer(nome_modelo)


def gerar_embeddings(textos, modelo=None, mostrar_progresso=False):

    """Converte textos em vetores normalizados para similaridade de cosseno."""

    if not textos:

        raise ValueError("É necessário informar pelo menos um texto.")

    modelo = modelo or carregar_modelo()

    embeddings = modelo.encode(
        textos,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=mostrar_progresso,
    )

    return np.asarray(embeddings, dtype=np.float32) # Garante que o tipo de dado seja float32 para compatibilidade com FAISS.
