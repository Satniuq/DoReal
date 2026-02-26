import os
import json
import difflib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PASTA_META = os.path.join(BASE_DIR, "meta")
PASTA_PERFIS = os.path.join(BASE_DIR, "perfis_de_regimes")

META_INDICE_FILE = os.path.join(PASTA_META, "meta_indice.json")

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def list_json_files(folder):
    return [f for f in os.listdir(folder) if f.endswith(".json")]

def sugerir(nome, universo):
    return difflib.get_close_matches(nome, universo, n=3, cutoff=0.75)

if __name__ == "__main__":

    print("\n=== VALIDAÇÃO DE REGIMES NOS PERFIS ===\n")

    meta = load_json(META_INDICE_FILE)["meta_indice"]["regimes"]
    regimes_validos = set(meta.keys())

    total_erros = 0

    for fname in sorted(list_json_files(PASTA_PERFIS)):
        path = os.path.join(PASTA_PERFIS, fname)
        perfil = load_json(path)

        pid = perfil.get("id", fname)

        regimes = perfil.get("regimes", {})

        todos = set()
        for lista in regimes.values():
            if isinstance(lista, list):
                todos.update(lista)

        erros_local = []

        for r in sorted(todos):
            if r not in regimes_validos:
                sugestoes = sugerir(r, regimes_validos)
                erros_local.append((r, sugestoes))

        if erros_local:
            print(f"🔎 {pid}")
            for r, sugestoes in erros_local:
                print(f"   ❌ Regime inválido: {r}")
                if sugestoes:
                    print(f"      ➜ Sugestões: {sugestoes}")
                else:
                    print("      ➜ Sem sugestão automática")
                total_erros += 1
            print()

    if total_erros == 0:
        print("✅ Todos os regimes nos perfis são válidos.")
    else:
        print("=========================================")
        print(f"❗ Total de regimes inválidos: {total_erros}")
        print("=========================================")

    print()