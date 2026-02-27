import os
import json
from collections import defaultdict

# =====================================================
# CONTEXTO
# =====================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PROPOSICOES_FILE = os.path.join(
    BASE_DIR, "indices_derivados", "proposicoes_classificadas_funcao.json"
)

MAPA_CAPITULOS_FILE = os.path.join(
    BASE_DIR, "meta", "mapa_capitulos.json"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR, "indices_derivados", "manuscrito_nuclear.txt"
)

# =====================================================
# HELPERS
# =====================================================

def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def ordenar_por_id(lista):
    return sorted(lista, key=lambda x: x.get("id_proposicao", ""))

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    print("\n=== GERAÇÃO DO MANUSCRITO NUCLEAR ===\n")

    if not os.path.exists(PROPOSICOES_FILE):
        raise FileNotFoundError("proposicoes_classificadas_funcao.json não encontrado.")

    if not os.path.exists(MAPA_CAPITULOS_FILE):
        raise FileNotFoundError("mapa_capitulos.json não encontrado.")

    proposicoes = load_json(PROPOSICOES_FILE)
    mapa_capitulos = load_json(MAPA_CAPITULOS_FILE)

    # apenas funções nucleares
    FUNCOES_NUCLEARES = {"fundacional", "definicional", "critica"}

    # organizar por capítulo
    por_capitulo = defaultdict(list)

    for p in proposicoes:

        funcao = p.get("funcao_ontologica")

        if funcao not in FUNCOES_NUCLEARES:
            continue

        loc = p.get("localizacao_vertical", {}) or {}
        nivel = loc.get("nivel")
        campo = loc.get("campo_principal")

        for capitulo, info in mapa_capitulos.items():

            if (
                info.get("nivel") == nivel and
                campo in info.get("campos", [])
            ):
                por_capitulo[capitulo].append(p)

    # escrever ficheiro
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        partes = sorted(
            set(info["parte"] for info in mapa_capitulos.values())
        )

        for parte in partes:

            f.write("=" * 80 + "\n")
            f.write(parte + "\n")
            f.write("=" * 80 + "\n\n")

            capitulos_da_parte = [
                c for c, info in mapa_capitulos.items()
                if info["parte"] == parte
            ]

            for capitulo in sorted(capitulos_da_parte):

                f.write("-" * 60 + "\n")
                f.write(capitulo + "\n")
                f.write("-" * 60 + "\n\n")

                props = ordenar_por_id(por_capitulo.get(capitulo, []))

                for p in props:
                    pid = p.get("id_proposicao")
                    texto = p.get("texto_literal", "").strip()
                    funcao = p.get("funcao_ontologica")

                    f.write(f"{pid} [{funcao}] — {texto}\n")

                f.write("\n")

    print("✔ manuscrito_nuclear.txt gerado com sucesso.\n")