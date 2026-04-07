# gerar_vetores.py
# Gera embeddings das definições e guarda em config/vetores_definicoes.json

from google import genai
import json
import os
from dotenv import load_dotenv

# =========================
# CONFIG
# =========================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY não encontrado no .env")

client = genai.Client(api_key=API_KEY)

MODELO_EMBEDDING = "models/gemini-embedding-001"
FICHEIRO_DEFINICOES = "config/definicoes.json"
FICHEIRO_SAIDA = "config/vetores_definicoes.json"


# =========================
# PROCESSAMENTO
# =========================
def criar_base_vetorial():
    with open(FICHEIRO_DEFINICOES, "r", encoding="utf-8") as f:
        definicoes = json.load(f)

    base_vetorial = []

    for d in definicoes:
        campo = d.get("campo", "")
        nivel = d.get("nivel", "")
        definicao = d.get("definicao", "")
        nota = d.get("nota", "")
        depende = ", ".join(d.get("depende_de", []))
        exclui = ", ".join(d.get("exclui", []))

        texto = "\n".join([
            f"CONCEITO: {campo}",
            f"NÍVEL ONTOLÓGICO: {nivel}",
            f"DEFINIÇÃO: {definicao}",
            f"DEPENDE DE: {depende}",
            f"EXCLUI: {exclui}",
            f"NOTA: {nota}",
        ])

        response = client.models.embed_content(
            model=MODELO_EMBEDDING,
            contents=texto
        )

        base_vetorial.append({
            "id": d["id"],
            "vetor": response.embeddings[0].values
        })

        print(f"✓ Vetor gerado: {d['id']}")

    with open(FICHEIRO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(base_vetorial, f, ensure_ascii=False, indent=2)

    print(f"\n✔ Base vetorial criada em {FICHEIRO_SAIDA}")


if __name__ == "__main__":
    criar_base_vetorial()
