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


def extrair_dados_autor(html):

    soup = BeautifulSoup(html, "html.parser")

    data_nascimento = soup.find("span", class_="author-born-date")
    local_nascimento = soup.find("span", class_="author-born-location")
    biografia = soup.find("div", class_="author-description")

    local = local_nascimento.get_text(strip=True) if local_nascimento else None

    if local and local.lower().startswith("in "): # remove o i " in " do início da string

        local = local[3:]

    return {

        "data_nascimento": data_nascimento.get_text(strip=True) if data_nascimento else None,
        "local_nascimento": local,
        "biografia": biografia.get_text(" ", strip=True) if biografia else None
        
    }


def enriquecer_citacoes_com_autores(citacoes):

    autores_por_link = {}

    for citacao in citacoes:

        link_autor = citacao["link_autor"]

        if link_autor not in autores_por_link:

            print(f"Coletando autor: {link_autor}")
            html = obter_html(link_autor)
            autores_por_link[link_autor] = extrair_dados_autor(html)

        citacao.update(autores_por_link[link_autor])

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