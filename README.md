# Quotes AI — Web Scraping + RAG

Projeto educacional de **web scraping**, limpeza de dados e **RAG** (Retrieval-Augmented Generation) sobre citações e biografias do site [quotes.toscrape.com](https://quotes.toscrape.com).

O fluxo coleta citações e dados de autores, normaliza e persiste em SQLite/CSV, indexa semanticamente com embeddings + FAISS e responde perguntas em português com **GPT-OSS 20B** (Groq), citando fontes. A interface web **Quotes AI** consome essa API.

---

## Funcionalidades

- Scraping paginado de citações (texto, autor, tags, link do autor)
- Enriquecimento com páginas de autor (nascimento, local, biografia)
- Limpeza de texto (Unicode NFKC, aspas, espaços, tags)
- Deduplicação e upsert por hash SHA-256 do texto canônico
- Metadados de coleta (`coletado_em`, `url_origem`, `hash_texto`)
- Documentos de indexação: citações inteiras + chunks de biografia
- Embeddings multilíngues + busca por similaridade de cosseno (FAISS)
- RAG com prompt restritivo (só responde com base no contexto)
- UI web simples (pergunta → resposta)
- CLIs para indexar, buscar e perguntar no terminal

---

## Arquitetura

```text
quotes.toscrape.com
        │
        ▼
  scraper + limpeza  →  SQLite (quotes.db) + CSV
        │
        ▼
  documentos (citações + chunks de biografia)
        │
        ▼
  embeddings (MiniLM) + FAISS (rag/store/)
        │
        ▼
      retriever (top-k) → Groq GPT-OSS 20B → resposta
        │
        ▼
  Flask (servidor.py) + UI (ui/)
```

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Linguagem | Python 3.12+ |
| Scraping | `requests`, `beautifulsoup4` |
| Dados | `sqlite3`, `pandas` |
| Embeddings | `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`) |
| Índice vetorial | `faiss-cpu` (`IndexFlatIP`) |
| LLM | Groq API — `openai/gpt-oss-20b` |
| API / UI | `flask`, HTML, CSS, JS |
| Segredos | `.env` + `python-dotenv` |

---

## Estrutura do projeto

```text
Web Scrapping/
├── main.py              # Orquestra a coleta
├── scraper.py           # HTTP + parsing HTML
├── limpeza.py           # Normalização, hash, dedup
├── banco.py             # SQLite + CSV
├── config.py            # URL, banco, tabela
├── servidor.py          # Flask (UI + API)
├── requirements.txt
├── .env.example
├── quotes.db            # Gerado pela coleta
├── citacoes.csv         # Export gerado
├── rag/
│   ├── documentos.py    # Docs de indexação + chunking
│   ├── embeddings.py    # MiniLM
│   ├── indice.py        # Cria/carrega FAISS
│   ├── retriever.py     # Busca semântica + filtros
│   ├── buscar.py        # CLI de busca
│   ├── gerar.py         # CLI / pipeline RAG + LLM
│   └── store/           # Índice (gitignore)
└── ui/
    ├── index.html
    ├── styles.css
    └── app.js
```

---

## Setup

### 1. Dependências

```bash
pip install -r requirements.txt
```

### 2. Chave da Groq

1. Crie uma conta em [console.groq.com](https://console.groq.com) (há free tier).
2. Gere uma API key (`gsk_...`).
3. Copie o exemplo e preencha:

```bash
cp .env.example .env
```

```env
GROQ_API_KEY=gsk_sua_chave_aqui
```

O arquivo `.env` está no `.gitignore` — não faça commit da chave.

---

## Como usar

### Coletar dados

```bash
python main.py
```

Gera/atualiza `quotes.db` e `citacoes.csv` (upsert por hash — reexecutar não duplica).

### Criar / atualizar o índice vetorial

```bash
python -m rag.indice
```

Gera `rag/store/` (FAISS + documentos + manifesto).  
**Rode de novo** sempre que a base de citações mudar.

### Perguntar no terminal (RAG completo)

```bash
python -m rag.gerar "Quem falou sobre coragem e amizade?"
python -m rag.gerar "Onde Einstein nasceu?" --tipo biografia
```

### Só busca semântica (sem LLM)

```bash
python -m rag.buscar "sucesso e valor" -k 5
python -m rag.buscar "onde Einstein nasceu?" --tipo biografia
```

### Interface web (Quotes AI)

```bash
python servidor.py
```

Abra: [http://127.0.0.1:5001](http://127.0.0.1:5001)

> A porta **5001** evita conflito comum no macOS com o AirPlay na porta 5000.

Atalho no formulário: `Cmd+Enter` (Mac) ou `Ctrl+Enter` envia a pergunta.

---

## RAG em resumo

1. **Documentos** — cada citação vira um doc; biografias são divididas em chunks (120 palavras, overlap 25).
2. **Embeddings** — MiniLM multilíngue (12 camadas, vetor 384-d, normalizado).
3. **Índice** — FAISS `IndexFlatIP`; com vetores normalizados, produto interno = **similaridade de cosseno**.
4. **Retriever** — devolve os top-k trechos mais próximos da pergunta.
5. **Geração** — GPT-OSS 20B (Groq) responde em português **somente** com base no contexto, listando fontes.

### Parâmetros principais

| Componente | Parâmetro | Valor |
|------------|-----------|--------|
| Embeddings | Modelo | `paraphrase-multilingual-MiniLM-L12-v2` |
| Embeddings | Dimensões | 384 |
| Chunk biografia | Tamanho / overlap | 120 / 25 palavras |
| LLM | Modelo | `openai/gpt-oss-20b` |
| LLM | Temperatura | `0.5` |
| UI | `k` (docs no contexto) | `5` (fixo) |

---

## API local

`POST /api/perguntar`

```json
{
  "pergunta": "Quem falou sobre coragem e amizade?",
  "k": 5,
  "tipo_documento": null,
  "autor": null
}
```

Resposta inclui `resposta`, `documentos` e `fontes`.

---

## Conceitos úteis

- **Unicode / NFKC** — padronizam caracteres equivalentes antes do hash e da indexação.
- **Hash SHA-256** — identidade estável da citação (dedup + upsert + id do documento).
- **Similaridade de cosseno** — quanto menor o ângulo entre vetores, maior o score (~0 a 1).
- **Transformer** — MiniLM (local) gera embeddings; GPT-OSS (Groq) gera o texto da resposta.

---

## Observações

- Site de treino: [quotes.toscrape.com](https://quotes.toscrape.com) — uso educacional.
- Artefatos gerados (`rag/store/`, `.env`) não devem ir para o repositório.
- Na primeira execução de embeddings/RAG, o modelo MiniLM pode ser baixado do Hugging Face (precisa de rede).

---

## Licença

Projeto educacional — use e adapte livremente para estudo.
