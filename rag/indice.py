"""Criação, persistência e carregamento do índice vetorial FAISS."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import faiss
from config import DATABASE
from rag.documentos import gerar_documentos
from rag.embeddings import NOME_MODELO, gerar_embeddings


DIRETORIO_INDICE = Path(__file__).parent / "store"
ARQUIVO_INDICE = "indice.faiss"
ARQUIVO_DOCUMENTOS = "documentos.json"
ARQUIVO_MANIFESTO = "manifesto.json"


def calcular_assinatura(documentos):

    """Identifica exatamente o conjunto e a ordem dos documentos indexados."""

    ids = "\n".join(documento["id"] for documento in documentos)
    return hashlib.sha256(ids.encode("utf-8")).hexdigest()


def criar_indice(caminho_db=DATABASE, diretorio=DIRETORIO_INDICE):

    """Gera embeddings e salva o índice, documentos e manifesto em disco."""

    documentos = gerar_documentos(caminho_db)
    textos = [documento["texto_indexacao"] for documento in documentos]
    embeddings = gerar_embeddings(textos, mostrar_progresso=True)

    # Cria o índice

    indice = faiss.IndexFlatIP(embeddings.shape[1]) # Índice plano de produto interno (IP)
    indice.add(embeddings) # Adiciona os embeddings ao índice

    diretorio = Path(diretorio)
    diretorio.mkdir(parents=True, exist_ok=True) # Cria o diretório se não existir

    faiss.write_index(indice, str(diretorio / ARQUIVO_INDICE)) # Salva o índice no disco

    with (diretorio / ARQUIVO_DOCUMENTOS).open("w", encoding="utf-8") as arquivo:
        json.dump(documentos, arquivo, ensure_ascii=False) # Salva os documentos no disco

    manifesto = {
        "modelo_embeddings": NOME_MODELO,
        "dimensoes": embeddings.shape[1],
        "total_documentos": len(documentos),
        "assinatura_documentos": calcular_assinatura(documentos),
        "indexado_em": datetime.now(timezone.utc).isoformat(),
    }

    with (diretorio / ARQUIVO_MANIFESTO).open("w", encoding="utf-8") as arquivo:
        json.dump(manifesto, arquivo, ensure_ascii=False, indent=2)

    return manifesto


def carregar_indice(diretorio=DIRETORIO_INDICE):
    """Carrega o índice, seus documentos e o manifesto."""

    diretorio = Path(diretorio)
    caminhos = {
        "índice": diretorio / ARQUIVO_INDICE,
        "documentos": diretorio / ARQUIVO_DOCUMENTOS,
        "manifesto": diretorio / ARQUIVO_MANIFESTO,
    }
    ausentes = [nome for nome, caminho in caminhos.items() if not caminho.exists()]

    if ausentes:
        raise FileNotFoundError(
            "Índice ainda não criado. Execute `python -m rag.indice`. "
            f"Arquivos ausentes: {', '.join(ausentes)}."
        )

    indice = faiss.read_index(str(caminhos["índice"]))

    with caminhos["documentos"].open(encoding="utf-8") as arquivo:
        documentos = json.load(arquivo)

    with caminhos["manifesto"].open(encoding="utf-8") as arquivo:
        manifesto = json.load(arquivo)

    if indice.ntotal != len(documentos):
        raise ValueError(
            "Índice inconsistente: a quantidade de vetores difere dos documentos."
        )

    return indice, documentos, manifesto


if __name__ == "__main__":
    
    resultado = criar_indice()

    print("\nÍndice criado com sucesso:")
    print(f"  Documentos: {resultado['total_documentos']}")
    print(f"  Dimensões: {resultado['dimensoes']}")
    print(f"  Modelo: {resultado['modelo_embeddings']}")
    print(f"  Diretório: {DIRETORIO_INDICE}")
