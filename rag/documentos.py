import hashlib
import sqlite3
from config import DATABASE, NOME_TABELA

TAMANHO_CHUNK_BIOGRAFIA = 120
SOBREPOSICAO_CHUNK_BIOGRAFIA = 25


def dividir_em_chunks(texto, tamanho = TAMANHO_CHUNK_BIOGRAFIA, sobreposicao = SOBREPOSICAO_CHUNK_BIOGRAFIA,):

    if not texto:

        return []

    if tamanho <= 0:

        raise ValueError("O tamanho do chunk deve ser maior que zero.")

    if sobreposicao < 0 or sobreposicao >= tamanho:

        raise ValueError( "A sobreposição deve ser zero ou maior e menor que o tamanho.")

    palavras = texto.split()
    chunks = []
    inicio = 0

    while inicio < len(palavras):

        fim = min(inicio + tamanho, len(palavras))
        chunks.append(" ".join(palavras[inicio:fim]))

        if fim == len(palavras):

            break

        inicio = fim - sobreposicao

    return chunks


def carregar_citacoes(caminho_db=DATABASE):

    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row

    try:

        linhas = conn.execute(f"SELECT * FROM {NOME_TABELA}").fetchall()
    finally:

        conn.close()

    return [dict(linha) for linha in linhas]


def montar_documento_citacao(citacao):

    tags = citacao.get("tags") or ""
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

    partes = [
        f"Citação: {citacao['texto']}",
        f"Autor: {citacao['autor']}",
    ]

    if tags:
        partes.append(f"Tags: {', '.join(tags)}")

    if citacao.get("data_nascimento") and citacao.get("local_nascimento"):
        partes.append(
            f"Nascimento: {citacao['data_nascimento']} "
            f"em {citacao['local_nascimento']}"
        )

    if citacao.get("url_origem"):
        partes.append(f"Fonte: {citacao['url_origem']}")

    return {
        "id": citacao["hash_texto"],
        "texto_indexacao": "\n".join(partes),
        "metadados": {
            "tipo_documento": "citacao",
            "hash_texto": citacao["hash_texto"],
            "texto": citacao["texto"],
            "autor": citacao["autor"],
            "tags": tags,
            "url_origem": citacao.get("url_origem"),
            "link_autor": citacao.get("link_autor"),
        },
    }


def montar_documentos_biografia(autor):

    chunks = dividir_em_chunks(autor.get("biografia"))
    total_chunks = len(chunks)
    documentos = []

    for indice, chunk in enumerate(chunks):
        partes = [f"Biografia de: {autor['autor']}"]

        if autor.get("data_nascimento") and autor.get("local_nascimento"):
            partes.append(
                f"Nascimento: {autor['data_nascimento']} "
                f"em {autor['local_nascimento']}"
            )

        partes.append(
            f"Trecho biográfico {indice + 1}/{total_chunks}: {chunk}"
        )

        if autor.get("link_autor"):
            partes.append(f"Fonte: {autor['link_autor']}")

        conteudo_id = (
            f"{autor.get('link_autor')}:{indice}:{chunk}"
        ).encode("utf-8")
        id_documento = hashlib.sha256(conteudo_id).hexdigest()

        documentos.append({
            "id": id_documento,
            "texto_indexacao": "\n".join(partes),
            "metadados": {
                "tipo_documento": "biografia",
                "autor": autor["autor"],
                "data_nascimento": autor.get("data_nascimento"),
                "local_nascimento": autor.get("local_nascimento"),
                "url_origem": autor.get("link_autor"),
                "link_autor": autor.get("link_autor"),
                "indice_chunk": indice,
                "total_chunks": total_chunks,
            },
        })

    return documentos


def selecionar_autores_unicos(citacoes):

    autores_por_chave = {}

    for citacao in citacoes:
        chave = citacao.get("link_autor") or citacao["autor"]
        if chave not in autores_por_chave:
            autores_por_chave[chave] = citacao

    return list(autores_por_chave.values())


def montar_documento(citacao):

    return montar_documento_citacao(citacao)


def gerar_documentos(caminho_db=DATABASE):

    citacoes = carregar_citacoes(caminho_db)
    documentos_citacoes = [
        montar_documento_citacao(citacao) for citacao in citacoes
    ]
    documentos_biografias = []

    for autor in selecionar_autores_unicos(citacoes):
        documentos_biografias.extend(montar_documentos_biografia(autor))

    return documentos_citacoes + documentos_biografias


if __name__ == "__main__":
    
    documentos = gerar_documentos()
    total_citacoes = sum(
        doc["metadados"]["tipo_documento"] == "citacao"
        for doc in documentos
    )
    total_biografias = len(documentos) - total_citacoes

    print(f"Documentos gerados: {len(documentos)}\n")
    print(f"  Citações: {total_citacoes}")
    print(f"  Chunks de biografias: {total_biografias}\n")
    print("Exemplo de documento:")
    print("=" * 60)
    print(documentos[0]["texto_indexacao"])
    print("=" * 60)
    print("\nMetadados:")
    for chave, valor in documentos[0]["metadados"].items():
        print(f"  {chave}: {valor}")
