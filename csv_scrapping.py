import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# URL inicial
URL = "https://quotes.toscrape.com/"


def obter_html(url):
 
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def extrair_citacoes(html):
  
    soup = BeautifulSoup(html, "html.parser")

    citacoes = []

    for quote in soup.find_all("div", class_="quote"):

        texto = quote.find("span", class_="text").get_text(strip=True)

        autor = quote.find("small", class_="author").get_text(strip=True)

        tags = [
            tag.get_text(strip=True)
            for tag in quote.find_all("a", class_="tag")
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


def salvar_csv(citacoes, nome_arquivo="citacoes.csv"):
    
    df = pd.DataFrame(citacoes)

    df.to_csv(
        nome_arquivo,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nArquivo '{nome_arquivo}' salvo com sucesso!")


def main():

    todas_citacoes = []

    url_atual = URL

    while url_atual:

        print(f"Coletando: {url_atual}")

        html = obter_html(url_atual)

        citacoes = extrair_citacoes(html)

        todas_citacoes.extend(citacoes)

        url_atual = obter_proxima_pagina(html)

    print(f"\nTotal de citações coletadas: {len(todas_citacoes)}")

    salvar_csv(todas_citacoes)


if __name__ == "__main__":
    main()