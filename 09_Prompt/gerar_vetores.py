# gerar_vetores.py
# Gera embeddings das definições e guarda em config/vetores_definicoes.json
#
# Requisitos:
#   pip install python-dotenv numpy
#
# Nota:
# - Lê config/definicoes.json
# - Produz config/vetores_definicoes.json

from google import genai
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY não encontrado. Cria um .env com GOOGLE_API_KEY=...")

client = genai.Client(api_key=API_KEY)

MODELO_EMBEDDING = "gemini-embedding-001"
FICHEIRO_DEFINICOES = "config/definicoes.json"
FICHEIRO_SAIDA_VETORES = "config/vetores_definicoes.json"

def criar_base_vetorial():
    with open(FICHEIRO_DEFINICOES, "r", encoding="utf-8") as f:
        definicoes = json.load(f)

    base_vetorial = []

    for d in definicoes:
        # texto rico (campo + definição + nota)
        campo = d.get("campo", "")
        definicao = d.get("definicao", "")
        nota = d.get("nota", "")

        texto_para_vetor = f"{campo}: {definicao} {nota}".strip()

        res = client.models.embed_content(
            model=MODELO_EMBEDDING,
            contents=texto_para_vetor
        )

        base_vetorial.append({
            "id": d["id"],
            "vetor": res.embeddings[0].values
        })

        print(f"Vetor gerado para: {d['id']}")

    with open(FICHEIRO_SAIDA_VETORES, "w", encoding="utf-8") as f:
        json.dump(base_vetorial, f, ensure_ascii=False, indent=2)

    print(f"\nConcluído. Vetores guardados em: {FICHEIRO_SAIDA_VETORES}")

if __name__ == "__main__":
    criar_base_vetorial()
