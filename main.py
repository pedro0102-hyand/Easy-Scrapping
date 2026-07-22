from config import URL, DATABASE
from scraper import enriquecer_citacoes_com_autores,extrair_citacoes,obter_html, obter_proxima_pagina
from banco import criar_tabela, salvar_citacoes, salvar_csv
from limpeza import deduplicar_citacoes


def main():

    # 1. Inicializa o Banco de Dados
    criar_tabela()

    todas_as_citacoes = []
    url_atual = URL

    # 2. Executa a raspagem de todas as páginas
    while url_atual is not None:
        print(f"Coletando: {url_atual}")
        html = obter_html(url_atual)
        citacoes = extrair_citacoes(html, url_origem=url_atual)
        todas_as_citacoes.extend(citacoes)
        url_atual = obter_proxima_pagina(html)

    todas_as_citacoes = deduplicar_citacoes(todas_as_citacoes)

    print("\n" + "=" * 60)
    print(f"Total de citações coletadas: {len(todas_as_citacoes)}")
    print("=" * 60)

    # 3. Coleta os detalhes de cada autor uma única vez.
    enriquecer_citacoes_com_autores(todas_as_citacoes)

    # 4. Salva no Banco de Dados e gera o CSV
    salvar_citacoes(todas_as_citacoes)
    print(f"\nCitações salvas com sucesso no banco de dados '{DATABASE}'!")
    
    salvar_csv(todas_as_citacoes)

    # 5. Exibe os dados formatados no terminal (comportamento do visualizador)
    for i, citacao in enumerate(todas_as_citacoes, start=1):
        print(f"\nCitação {i}")
        print(f"Texto : {citacao['texto']}")
        print(f"Autor : {citacao['autor']}")
        # Une as tags para exibição no print
        tags_str = ", ".join(citacao["tags"]) if isinstance(citacao["tags"], list) else citacao["tags"]
        print(f"Tags  : {tags_str}")
        print(f"Link  : {citacao['link_autor']}")
        print(f"Nascimento: {citacao['data_nascimento']}")
        print(f"Local: {citacao['local_nascimento']}")


if __name__ == "__main__":
    
    main()