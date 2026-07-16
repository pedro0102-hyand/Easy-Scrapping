import requests
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
            "tags": tags,
            "link_autor": link_autor
        })

    return citacoes

# retorna a URL da próxima página, se existir
def proxima_pagina(html):
  
    soup = BeautifulSoup(html, "html.parser")
    next_button = soup.find("li", class_="next")

    if next_button is None:
        return None
    
    href = next_button.find("a")["href"]
    return urljoin(URL, href)

def main():

    todas_as_citacoes = [] 
    url_atual = URL

    while url_atual is not None:

        html = obter_html(url_atual)
        citacoes = extrair_citacoes(html)
        todas_as_citacoes.extend(citacoes)
        url_atual = proxima_pagina(html)
    
    print("\n" + "=" * 60)
    print(f"Total de citações coletadas: {len(todas_as_citacoes)}")
    print("=" * 60)

    for i, citacao in enumerate(todas_as_citacoes, start=1):

        print(f"\nCitação {i}")
        print(f"Texto : {citacao['texto']}")
        print(f"Autor : {citacao['autor']}")
        print(f"Tags  : {', '.join(citacao['tags'])}")
        print(f"Link  : {citacao['link_autor']}")


if __name__ == "__main__":
    main()
