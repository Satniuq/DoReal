import os
import json
from collections import defaultdict

# =====================================================
# CONTEXTO
# =====================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PROPOSICOES_FILE = os.path.join(
    BASE_DIR, "dados_base", "proposicoes", "proposicoes_filtradas.json"
)

PASTA_INDICES = os.path.join(BASE_DIR, "indices_derivados")

# =====================================================
# HELPERS
# =====================================================

def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =====================================================
# CLASSIFICAÇÃO HEURÍSTICA
# =====================================================

def classificar(texto: str):

    t = texto.lower().strip()

    if len(t) < 25:
        return "fragmento"

    if t.startswith(("sim", "não,", "claro", "ah")):
        return "fragmento"

    if any(p in t for p in [
        "o real é", "o ser é", "ontologicamente",
        "não há", "só há", "o real não"
    ]):
        return "fundacional"

    if any(p in t for p in [
        "é aquilo que", "define", "significa",
        "implica que", "consiste em"
    ]):
        return "definicional"

    if any(p in t for p in [
        "erro", "relativismo", "dualismo",
        "redução", "confusão", "substituir"
    ]):
        return "critica"

    if any(p in t for p in [
        "como", "tal como", "por exemplo",
        "estrela", "átomo", "vento", "célula"
    ]):
        return "exemplo"

    if any(p in t for p in [
        "filosofia", "livro", "índice",
        "discurso", "narrativa"
    ]):
        return "meta"

    return "derivada"


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    print("\n=== CLASSIFICAÇÃO FUNCIONAL DAS PROPOSIÇÕES ===\n")

    if not os.path.exists(PROPOSICOES_FILE):
        raise FileNotFoundError(f"Ficheiro não encontrado: {PROPOSICOES_FILE}")

    os.makedirs(PASTA_INDICES, exist_ok=True)

    proposicoes = load_json(PROPOSICOES_FILE)

    classificadas = []
    indice_funcao = defaultdict(list)

    for p in proposicoes:

        pid = p.get("id_proposicao")
        texto = p.get("texto_literal", "")

        funcao = classificar(texto)

        p["funcao_ontologica"] = funcao

        classificadas.append(p)
        indice_funcao[funcao].append(pid)

    # ordenar listas
    for k in indice_funcao:
        indice_funcao[k] = sorted(set(indice_funcao[k]))

    save_json(
        os.path.join(PASTA_INDICES, "proposicoes_classificadas_funcao.json"),
        classificadas
    )

    save_json(
        os.path.join(PASTA_INDICES, "indice_por_funcao.json"),
        dict(indice_funcao)
    )

    print("✔ proposicoes_classificadas_funcao.json")
    print("✔ indice_por_funcao.json")
    print("\nResumo:")
    for k, v in indice_funcao.items():
        print(f"{k}: {len(v)}")

    print("\n---------------------------\n")