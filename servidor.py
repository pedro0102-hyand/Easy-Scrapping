from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from rag.gerar import perguntar
from rag.retriever import Retriever

UI_DIR = Path(__file__).resolve().parent / "ui"

app = Flask(__name__, static_folder=str(UI_DIR), static_url_path="/static")

_retriever = None


def obter_retriever():
    """Carrega o retriever uma única vez (modelo + índice em memória)."""

    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


@app.get("/")
def home():
    return send_from_directory(UI_DIR, "index.html")


@app.post("/api/perguntar")
def api_perguntar():
    dados = request.get_json(silent=True) or {}
    pergunta = (dados.get("pergunta") or "").strip()

    if not pergunta:
        return jsonify({"erro": "A pergunta não pode estar vazia."}), 400

    try:
        k = int(dados.get("k") or 5)
    except (TypeError, ValueError):
        return jsonify({"erro": "O valor de k é inválido."}), 400

    tipo = dados.get("tipo_documento") or None
    autor = (dados.get("autor") or "").strip() or None

    try:
        resultado = perguntar(
            pergunta,
            k=k,
            tipo_documento=tipo,
            autor=autor,
            retriever=obter_retriever(),
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except Exception as erro:  # noqa: BLE001 - devolve erro legível à UI
        return jsonify({"erro": f"Falha ao gerar resposta: {erro}"}), 500

    return jsonify({
        "pergunta": resultado["pergunta"],
        "resposta": resultado["resposta"],
        "fontes": resultado["fontes"],
        "documentos": [
            {
                "id": doc["id"],
                "score": doc["score"],
                "texto_indexacao": doc["texto_indexacao"],
                "metadados": doc["metadados"],
            }
            for doc in resultado["documentos"]
        ],
    })


if __name__ == "__main__":
    print("Quotes AI em http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
