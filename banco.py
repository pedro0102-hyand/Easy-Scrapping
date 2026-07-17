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
            link_autor TEXT
        )
    """)

    conn.commit()
    conn.close()

def salvar_citacoes(citacoes):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    for citacao in citacoes:

        cursor.execute(f"""
            INSERT INTO {NOME_TABELA} (texto, autor, tags, link_autor)
            VALUES (?, ?, ?, ?)
        """, (
            citacao["texto"],
            citacao["autor"],
            ", ".join(citacao["tags"]) if isinstance(citacao["tags"], list) else citacao["tags"],
            citacao["link_autor"]
        ))

    conn.commit()
    conn.close()