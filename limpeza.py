import hashlib
import unicodedata


PARES_DE_ASPAS = {
    ('"', '"'),
    ("'", "'"),
    ("“", "”"),
    ("‘", "’"),
    ("«", "»"),
}

TRADUCAO_ASPAS = str.maketrans({
    "“": '"',
    "”": '"',
    "„": '"',
    "‟": '"',
    "‘": "'",
    "’": "'",
})


def normalizar_espacos(valor):
    """Remove espaços extras, quebras de linha e tabulações."""

    if valor is None:
        return None

    return " ".join(str(valor).split())


def normalizar_texto(texto, lowercase=False, remover_aspas_externas=True):
    """Cria texto consistente sem destruir a capitalização por padrão."""

    if texto is None:
        return None

    texto = unicodedata.normalize("NFKC", str(texto))
    texto = normalizar_espacos(texto)

    if remover_aspas_externas:
        while len(texto) >= 2 and (texto[0], texto[-1]) in PARES_DE_ASPAS:
            texto = normalizar_espacos(texto[1:-1])

    texto = texto.translate(TRADUCAO_ASPAS)
    texto = normalizar_espacos(texto)

    return texto.casefold() if lowercase else texto


def normalizar_tags(tags):
    """Normaliza tags em minúsculas e remove repetições."""

    if not tags:
        return []

    if isinstance(tags, str):
        tags = tags.split(",")

    tags_normalizadas = []
    tags_vistas = set()

    for tag in tags:
        tag_normalizada = normalizar_texto(tag, lowercase=True)
        if tag_normalizada and tag_normalizada not in tags_vistas:
            tags_vistas.add(tag_normalizada)
            tags_normalizadas.append(tag_normalizada)

    return tags_normalizadas


def gerar_hash_texto(texto):
    """Gera SHA-256 usando a versão canônica do texto."""

    texto_canonico = normalizar_texto(texto, lowercase=True)
    return hashlib.sha256(texto_canonico.encode("utf-8")).hexdigest()


def limpar_citacao(citacao):
    """Normaliza os campos de uma citação sem alterar o dicionário original."""

    citacao_limpa = citacao.copy()
    texto = normalizar_texto(citacao_limpa["texto"])

    citacao_limpa.update({
        "texto": texto,
        "texto_normalizado": normalizar_texto(texto, lowercase=True),
        "hash_texto": gerar_hash_texto(texto),
        "autor": normalizar_texto(
            citacao_limpa["autor"],
            remover_aspas_externas=False
        ),
        "tags": normalizar_tags(citacao_limpa.get("tags")),
    })

    for campo in ("data_nascimento", "local_nascimento", "biografia"):
        if campo in citacao_limpa:
            citacao_limpa[campo] = normalizar_texto(
                citacao_limpa[campo],
                remover_aspas_externas=False
            )

    return citacao_limpa


def deduplicar_citacoes(citacoes):
    """Remove duplicatas pelo hash e preserva a ordem da coleta."""

    citacoes_por_hash = {}

    for citacao in citacoes:
        citacao_limpa = limpar_citacao(citacao)
        citacoes_por_hash[citacao_limpa["hash_texto"]] = citacao_limpa

    return list(citacoes_por_hash.values())
