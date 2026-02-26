import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PASTA_PERCURSOS = os.path.join(BASE_DIR, "percursos")
PASTA_PERFIS = os.path.join(BASE_DIR, "perfis_de_regimes")
META_INDICE_FILE = os.path.join(BASE_DIR, "meta", "meta_indice.json")

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def carregar_meta_indice():
    return load_json(META_INDICE_FILE)["meta_indice"]["regimes"]

def carregar_percursos():
    percursos = {}
    for fn in os.listdir(PASTA_PERCURSOS):
        if fn.endswith(".json"):
            p = load_json(os.path.join(PASTA_PERCURSOS, fn))
            percursos[p["id"]] = p
    return percursos

def carregar_perfis():
    perfis = {}
    for fn in os.listdir(PASTA_PERFIS):
        if fn.endswith(".json"):
            perfis[fn] = load_json(os.path.join(PASTA_PERFIS, fn))
    return perfis

def inferir_regimes(ops, meta_regimes):
    regimes = set()
    for r, bloco in meta_regimes.items():
        if set(bloco.get("operacoes", [])) & ops:
            regimes.add(r)
    return regimes

if __name__ == "__main__":

    print("\n=== ALINHAMENTO AUTOMÁTICO DE PERFIS (v2) ===\n")

    meta_regimes = carregar_meta_indice()
    percursos = carregar_percursos()
    perfis = carregar_perfis()

    total = 0

    for fname, perfil in perfis.items():

        percurso_id = perfil.get("percurso_ref")
        if percurso_id not in percursos:
            continue

        percurso = percursos[percurso_id]

        ops = set(percurso.get("operacoes_ativas", []))
        ops |= set(percurso.get("operacoes_de_correcao", []))

        regimes_inferidos = inferir_regimes(ops, meta_regimes)

        regimes = perfil.get("regimes", {})

        antigos = set(regimes.get("ativados", []))

        regimes["ativados"] = sorted(regimes_inferidos)

        # remover ativados de pressupostos e excluidos
        regimes["pressupostos"] = sorted(
            set(regimes.get("pressupostos", [])) - regimes_inferidos
        )

        regimes["excluidos"] = sorted(
            set(regimes.get("excluidos", [])) - regimes_inferidos
        )

        regimes.pop("retorno", None)

        perfil["regimes"] = regimes

        with open(os.path.join(PASTA_PERFIS, fname), "w", encoding="utf-8") as f:
            json.dump(perfil, f, ensure_ascii=False, indent=2)

        if antigos != regimes_inferidos:
            print(f"✔ Atualizado: {perfil['id']}")
            total += 1

    print("\n---------------------------------")
    print(f"Perfis ajustados: {total}")
    print("---------------------------------\n")