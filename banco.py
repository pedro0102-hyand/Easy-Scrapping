import sqlite3
import pandas as pd
from config import DATABASE, NOME_TABELA

def salvar_csv(citacoes, nome_arquivo="citacoes.csv"):

    citacoes_formatadas = []
    
    for citacao in citacoes:

        copia = citacao.copy()

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

    # Remove duplicatas de execuções antigas, mantendo o registro mais
    # recente (que contém os dados do autor), e garante unicidade.
    cursor.execute(f"""
        DELETE FROM {NOME_TABELA}
        WHERE id NOT IN (
            SELECT MAX(id) FROM {NOME_TABELA} GROUP BY texto, autor
        )
    """)
    cursor.execute(f"""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_citacao_unica
        ON {NOME_TABELA} (texto, autor)
    """)

    conn.commit()
    conn.close()

def salvar_citacoes(citacoes):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    for citacao in citacoes:

        # Upsert: se a citação já existir, atualiza os campos em vez de
        # duplicar a linha.
        cursor.execute(f"""
            INSERT INTO {NOME_TABELA} (
                texto,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (texto, autor) DO UPDATE SET
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