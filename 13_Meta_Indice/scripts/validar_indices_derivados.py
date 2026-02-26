# validar_indices_derivados.py

import json
import os
from collections import defaultdict

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPTS_DIR)

PATH_CONCEITOS = os.path.join(BASE_DIR, "dados_base", "todos_os_conceitos.json")
PATH_OPERACOES = os.path.join(BASE_DIR, "dados_base", "operacoes.json")
PATH_META = os.path.join(BASE_DIR, "meta", "meta_indice.json")
PATH_META_REF = os.path.join(BASE_DIR, "meta", "meta_referencia_do_percurso.json")

DIR_PERCURSOS = os.path.join(BASE_DIR, "percursos")
DIR_DERIVADOS = os.path.join(BASE_DIR, "indices_derivados")

def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def flatten_ops(d):
    ops = []
    for v in d.values():
        if isinstance(v, list):
            ops += v
    return sorted(set(ops))

def main():

    conceitos = load(PATH_CONCEITOS)
    operacoes = load(PATH_OPERACOES)
    meta = load(PATH_META)["meta_indice"]["regimes"]
    meta_ref = load(PATH_META_REF)

    idx_conc_ops = load(os.path.join(DIR_DERIVADOS, "indice_conceito_operacoes.json"))
    idx_por_regime = load(os.path.join(DIR_DERIVADOS, "indice_por_regime.json"))
    idx_perc = load(os.path.join(DIR_DERIVADOS, "indice_de_percursos.json"))
    idx_pat = load(os.path.join(DIR_DERIVADOS, "indice_de_patologias.json"))

    erros = 0

    print("\n============= VALIDACAO INDICES DERIVADOS =============\n")

    # ----------------------------------------------------
    # 1) Conceito -> Operações -> Regimes
    # ----------------------------------------------------

    op_to_regime = {}
    for r, bloco in meta.items():
        for op in bloco.get("operacoes", []):
            op_to_regime[op] = r

    for cid, c in conceitos.items():

        ops_reais = flatten_ops(c.get("operacoes_ontologicas", {}))
        ops_idx = sorted(idx_conc_ops[cid]["operacoes"])

        if ops_reais != ops_idx:
            print(f"❌ Operações divergentes no conceito {cid}")
            erros += 1

        regimes_esperados = sorted(set(op_to_regime[o] for o in ops_reais if o in op_to_regime))
        regimes_idx = sorted(idx_conc_ops[cid]["regimes_ativados"])

        if regimes_esperados != regimes_idx:
            print(f"❌ Regimes divergentes no conceito {cid}")
            erros += 1

    # ----------------------------------------------------
    # 2) Percursos -> Regimes
    # ----------------------------------------------------

    percursos = {}
    for f in os.listdir(DIR_PERCURSOS):
        if f.endswith(".json"):
            p = load(os.path.join(DIR_PERCURSOS, f))
            percursos[p["id"]] = p

    for pid, p in percursos.items():
        ops = sorted(set(p.get("operacoes_ativas", []) + p.get("operacoes_de_correcao", [])))
        regimes_esperados = sorted(set(op_to_regime[o] for o in ops if o in op_to_regime))

        for r in regimes_esperados:
            if pid not in idx_por_regime.get(r, []):
                print(f"❌ Percurso {pid} deveria estar em {r}")
                erros += 1

    # ----------------------------------------------------
    # 3) Percursos por tipo_instancia
    # ----------------------------------------------------

    for tipo, lista in idx_perc.items():
        for pid in lista:
            if meta_ref[pid]["tipo_instancia"] != tipo:
                print(f"❌ Percurso {pid} mal classificado em indice_de_percursos")
                erros += 1

    # ----------------------------------------------------
    # 4) Patologias
    # ----------------------------------------------------

    for pid, info in meta_ref.items():
        t = info["tipo_instancia"].lower()

        if "esteril" in t and pid not in idx_pat["percursos_esteris"]:
            print(f"❌ {pid} deveria estar em percursos_esteris")
            erros += 1

        if "degeneracao" in t and pid not in idx_pat["percursos_degenerativos"]:
            print(f"❌ {pid} deveria estar em percursos_degenerativos")
            erros += 1

        if "critico" in t and pid not in idx_pat["percursos_criticos"]:
            print(f"❌ {pid} deveria estar em percursos_criticos")
            erros += 1

    print("\n======================================================")
    print(f"Erros encontrados: {erros}")
    print("======================================================\n")

if __name__ == "__main__":
    main()