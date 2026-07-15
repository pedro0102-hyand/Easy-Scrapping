import requests
from bs4 import BeautifulSoup

# acessa o site
site = "https://quotes.toscrape.com/"

# faz a requisição para o site
response = requests.get(site)

# cria o objeto BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# encontra todas as citações na página
todas_as_citacoes = soup.find_all('span', itemprop='text')

# imprime todas as citações
for citacao in todas_as_citacoes:
    print(citacao.get_text())
 

