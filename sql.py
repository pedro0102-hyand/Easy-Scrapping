import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://quotes.toscrape.com/"
DATABASE = "quotes.db"


def obter_html(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def extrair_citacoes(html):

    soup = BeautifulSoup(html, "html.parser")

    citacoes = []

    for quote in soup.find_all("div", class_="quote"):

        texto = quote.find(
            "span",
            class_="text"
        ).get_text(strip=True)

        autor = quote.find(
            "small",
            class_="author"
        ).get_text(strip=True)

        tags = [
            tag.get_text(strip=True)
            for tag in quote.find_all(
                "a",
                class_="tag"
            )
        ]

        link_autor = urljoin(
            URL,
            quote.find("a")["href"]
        )

        citacoes.append({

            "texto": texto,
            "autor": autor,
            "tags": ", ".join(tags),
            "link_autor": link_autor

        })

    return citacoes


def obter_proxima_pagina(html):

    soup = BeautifulSoup(html, "html.parser")

    next_button = soup.find("li", class_="next")

    if next_button is None:
        return None

    href = next_button.find("a")["href"]

    return urljoin(URL, href)

def criar_tabela():

    conn = sqlite3.connect(DATABASE) # Conecta ao banco de dados (ou cria se não existir)
    cursor = conn.cursor() # Cria um cursor para executar comandos SQL

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS citacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT,
            autor TEXT,
            tags TEXT,
            link_autor TEXT
        )
    ''')

    conn.commit() # Salva as alterações no banco de dados
    conn.close() # Fecha a conexão com o banco de dados

def salvar_citacoes(citacoes):

    conn = sqlite3.connect(DATABASE) # Conecta ao banco de dados
    cursor = conn.cursor() # Cria um cursor para executar comandos SQL

    for citacao in citacoes:
        cursor.execute('''
            INSERT INTO citacoes (texto, autor, tags, link_autor)
            VALUES (?, ?, ?, ?)
        ''', (citacao["texto"], citacao["autor"], citacao["tags"], citacao["link_autor"]))

    conn.commit() # Salva as alterações no banco de dados
    conn.close() # Fecha a conexão com o banco de dados

def main(): 
    
    criar_tabela() # Cria a tabela no banco de dados, se não existir

    todas_citacoes = [] # Lista para armazenar todas as citações coletadas

    url_atual = URL 

    while url_atual is not None:

        print(f"Coletando: {url_atual}")

        html = obter_html(url_atual) 
        citacoes = extrair_citacoes(html) 
        todas_citacoes.extend(citacoes) # Adiciona as citações à lista principal
        url_atual = obter_proxima_pagina(html) 

    print(f"\nTotal de citações coletadas: {len(todas_citacoes)}")

    salvar_citacoes(todas_citacoes) # Salva todas as citações no banco de dados
    print(f"\nCitações salvas com sucesso no banco de dados '{DATABASE}'!")

if __name__ == "__main__":
    main()