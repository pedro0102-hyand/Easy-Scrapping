import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config import URL

def obter_html(url):

    response = requests.get(url, timeout=10) # acesso ao site com timeout de 10 segundos
    response.raise_for_status()
    return response.text


def extrair_citacoes(html):

    soup = BeautifulSoup(html, "html.parser") # cria o objeto BeautifulSoup para fazer o parsing do HTML
    citacoes = [] # lista para armazenar as citações extraídas

    # percorre todas as divs com a classe "quote" e extrai o texto, autor, tags e link do autor
    for quote in soup.find_all("div", class_="quote"):

        texto = quote.find("span", class_="text").get_text(strip=True)
        autor = quote.find("small", class_="author").get_text(strip=True)

        tags = [
            tag.get_text(strip=True)
            for tag in quote.find_all("a", class_="tag")
        ]

        link_autor = urljoin(URL, quote.find("a")["href"])

        citacoes.append({
            "texto": texto,
            "autor": autor,
            "tags": tags, 
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


def proxima_pagina(html):

    return obter_proxima_pagina(html)