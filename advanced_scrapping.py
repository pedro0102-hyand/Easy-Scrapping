import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://quotes.toscrape.com/"


def obter_html(url):

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response


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


def main():

    html = obter_html(URL).text

    citacoes = extrair_citacoes(html)

    for c in citacoes:

        print("=" * 80)
        print(f"Texto : {c['texto']}")
        print(f"Autor : {c['autor']}")
        print(f"Tags  : {', '.join(c['tags'])}")
        print(f"Link  : {c['link_autor']}")


if __name__ == "__main__":
    main()