import requests
from bs4 import BeautifulSoup

# acessa o site
URL = "https://quotes.toscrape.com/"

# faz a requisição para o site
def obter_html(url):

    response = requests.get(url, timeout=10)
    response.raise_for_status()  # levanta um erro se a requisição falhar
    return response

def extrair_citacoes(html):

    soup = BeautifulSoup(html, 'html.parser')

    citacoes = []

    for quote in soup.find_all('div', class_='quote'):
        
        texto = quote.find('span', class_='text').get_text()
        autor = quote.find('small', class_='author').get_text()
        citacoes.append({'texto': texto, 'autor': autor})

    return citacoes

def main():

    html = obter_html(URL).text
    citacoes = extrair_citacoes(html)

    for c in citacoes:
        print(f"{c['texto']} - {c['autor']}")
    
if __name__ == "__main__":
    main()
 

