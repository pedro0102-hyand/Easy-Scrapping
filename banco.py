import sqlite3
import pandas as pd
from config import DATABASE, NOME_TABELA
from limpeza import limpar_citacao, normalizar_tags

def salvar_csv(citacoes, nome_arquivo="citacoes.csv"):

    citacoes_formatadas = []
    
    for citacao in citacoes:

        copia = limpar_citacao(citacao)

        if isinstance(copia["tags"], list):

            copia["tags"] = ", ".join(copia["tags"])

        citacoes_formatadas.append(copia)

    df = pd.DataFrame(citacoes_formatadas)
    df.to_csv(nome_arquivo, index=False, encoding="utf-8")
    print(f"Arquivo CSV '{nome_arquivo}' salvo com sucesso.")

def criar_tabela():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {NOME_TABELA} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            texto_normalizado TEXT NOT NULL,
            autor TEXT NOT NULL,
            tags TEXT,
            link_autor TEXT,
            data_nascimento TEXT,
            local_nascimento TEXT,
            biografia TEXT,
            coletado_em TEXT,
            url_origem TEXT,
            hash_texto TEXT
        )
    """)

    # Atualiza bancos criados por versões anteriores do projeto.
    cursor.execute(f"PRAGMA table_info({NOME_TABELA})")
    colunas_existentes = {coluna[1] for coluna in cursor.fetchall()}
    novas_colunas = {
        "texto_normalizado": "TEXT",
        "data_nascimento": "TEXT",
        "local_nascimento": "TEXT",
        "biografia": "TEXT",
        "coletado_em": "TEXT",
        "url_origem": "TEXT",
        "hash_texto": "TEXT"
    }

    for nome_coluna, tipo_coluna in novas_colunas.items():
        if nome_coluna not in colunas_existentes:
            cursor.execute(
                f"ALTER TABLE {NOME_TABELA} "
                f"ADD COLUMN {nome_coluna} {tipo_coluna}"
            )

    # Migra também os registros já existentes para a forma normalizada.
    cursor.execute("DROP INDEX IF EXISTS idx_citacao_unica")
    cursor.execute("DROP INDEX IF EXISTS idx_hash_texto")
    cursor.execute(
        f"SELECT id, texto, autor, tags FROM {NOME_TABELA}"
    )

    for id_citacao, texto, autor, tags in cursor.fetchall():
        citacao_limpa = limpar_citacao({
            "texto": texto,
            "autor": autor,
            "tags": normalizar_tags(tags),
        })
        cursor.execute(f"""
            UPDATE {NOME_TABELA}
            SET texto = ?,
                texto_normalizado = ?,
                autor = ?,
                tags = ?,
                hash_texto = ?
            WHERE id = ?
        """, (
            citacao_limpa["texto"],
            citacao_limpa["texto_normalizado"],
            citacao_limpa["autor"],
            ", ".join(citacao_limpa["tags"]),
            citacao_limpa["hash_texto"],
            id_citacao,
        ))

    # O hash canônico identifica a mesma citação mesmo quando espaços,
    # aspas ou capitalização são diferentes.
    cursor.execute(f"""
        DELETE FROM {NOME_TABELA}
        WHERE id NOT IN (
            SELECT MAX(id) FROM {NOME_TABELA} GROUP BY hash_texto
        )
    """)
    cursor.execute(f"""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_hash_texto
        ON {NOME_TABELA} (hash_texto)
    """)

    conn.commit()
    conn.close()

def salvar_citacoes(citacoes):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    for citacao in citacoes:
        citacao = limpar_citacao(citacao)

        # Upsert pelo hash: variações de espaços, aspas e capitalização
        # atualizam a mesma citação em vez de duplicá-la.
        cursor.execute(f"""
            INSERT INTO {NOME_TABELA} (
                texto,
                texto_normalizado,
                autor,
                tags,
                link_autor,
                data_nascimento,
                local_nascimento,
                biografia,
                coletado_em,
                url_origem,
                hash_texto
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (hash_texto) DO UPDATE SET
                texto = excluded.texto,
                texto_normalizado = excluded.texto_normalizado,
                autor = excluded.autor,
                tags = excluded.tags,
                link_autor = excluded.link_autor,
                data_nascimento = excluded.data_nascimento,
                local_nascimento = excluded.local_nascimento,
                biografia = excluded.biografia,
                coletado_em = excluded.coletado_em,
                url_origem = excluded.url_origem,
                hash_texto = excluded.hash_texto
        """, (
            citacao["texto"],
            citacao["texto_normalizado"],
            citacao["autor"],
            ", ".join(citacao["tags"]) if isinstance(citacao["tags"], list) else citacao["tags"],
            citacao["link_autor"],
            citacao.get("data_nascimento"),
            citacao.get("local_nascimento"),
            citacao.get("biografia"),
            citacao.get("coletado_em"),
            citacao.get("url_origem"),
            citacao.get("hash_texto")
        ))

    conn.commit()
    conn.close()