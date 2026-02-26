# gerar_indices_derivados.py
# Gera automaticamente indices derivados a partir de:
# - dados_base/todos_os_conceitos.json
# - dados_base/operacoes.json
# - meta/meta_indice.json
# - meta/meta_referencia_do_percurso.json
# - percursos/*.json
#
# Saídas (indices_derivados/):
# - indice_conceito_operacoes.json
# - indice_por_regime.json
# - indice_de_percursos.json
# - indice_de_patologias.json
#
# Regras:
# - índices derivados são regeneráveis (não contêm informação primária manual)
# - ordenação determinística
# - validações leves para apanhar deriva estrutural

import json
import os
from collections import defaultdict

# ------------------------------------------------------
# Base dir = pasta 13_Meta_Indice (pai de scripts/)
# ------------------------------------------------------

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPTS_DIR)

PATH_CONCEITOS = os.path.join(BASE_DIR, "dados_base", "todos_os_conceitos.json")
PATH_OPERACOES = os.path.join(BASE_DIR, "dados_base", "operacoes.json")
PATH_META_INDICE = os.path.join(BASE_DIR, "meta", "meta_indice.json")
PATH_META_REF_PERCURSO = os.path.join(BASE_DIR, "meta", "meta_referencia_do_percurso.json")

DIR_PERCURSOS = os.path.join(BASE_DIR, "percursos")
DIR_OUT = os.path.join(BASE_DIR, "indices_derivados")

OUT_CONCEITO_OPERACOES = os.path.join(DIR_OUT, "indice_conceito_operacoes.json")
OUT_POR_REGIME = os.path.join(DIR_OUT, "indice_por_regime.json")
OUT_DE_PERCURSOS = os.path.join(DIR_OUT, "indice_de_percursos.json")
OUT_PATOLOGIAS = os.path.join(DIR_OUT, "indice_de_patologias.json")

# ------------------------------------------------------

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def flatten_ops(operacoes_ontologicas) -> list[str]:
    """
    Espera um dict {categoria: [OP_..., OP_...], ...}
    Devolve lista única sem duplicados, ordenada.
    """
    if not isinstance(operacoes_ontologicas, dict):
        return []
    out = []
    for v in operacoes_ontologicas.values():
        if isinstance(v, list):
            out.extend(v)
    return sorted(set(out))

def build_op_to_regime(meta_regimes: dict) -> dict[str, str]:
    """
    Mapa operação -> regime (1:1 esperado).
    Se uma operação aparecer em mais de um regime, lança erro.
    """
    op_to_regime = {}
    collisions = defaultdict(list)

    for regime, bloco in meta_regimes.items():
        for op in bloco.get("operacoes", []) or []:
            if op in op_to_regime and op_to_regime[op] != regime:
                collisions[op].append(op_to_regime[op])
                collisions[op].append(regime)
            op_to_regime[op] = regime

    if collisions:
        msgs = []
        for op, regs in collisions.items():
            regs_u = sorted(set(regs))
            msgs.append(f"{op}: {regs_u}")
        raise ValueError("Operações presentes em múltiplos regimes (meta_indice inconsistente):\n" + "\n".join(msgs))

    return op_to_regime

def regimes_from_ops(ops: list[str], op_to_regime: dict[str, str]) -> list[str]:
    regimes = set()
    for op in ops:
        r = op_to_regime.get(op)
        if r:
            regimes.add(r)
    return sorted(regimes)

def read_percurso_files(dir_percursos: str) -> dict[str, dict]:
    """
    Lê todos os *.json em percursos/ (ignora ficheiros que não sejam JSON).
    Exige campo "id" em cada ficheiro.
    """
    percursos = {}
    for fn in os.listdir(dir_percursos):
        if not fn.lower().endswith(".json"):
            continue
        path = os.path.join(dir_percursos, fn)
        try:
            obj = load_json(path)
        except Exception:
            continue  # se houver algum json inválido, ignora (podes tornar isto erro se quiseres)

        pid = obj.get("id")
        if not pid:
            raise ValueError(f"Percurso sem 'id': {path}")
        percursos[pid] = obj
    return percursos

def tipo_normalizado(tipo: str) -> str:
    return (tipo or "").strip().lower()

def main():
    ensure_dir(DIR_OUT)

    conceitos = load_json(PATH_CONCEITOS)
    operacoes = load_json(PATH_OPERACOES)
    meta = load_json(PATH_META_INDICE)
    meta_ref = load_json(PATH_META_REF_PERCURSO)

    meta_regimes = meta["meta_indice"]["regimes"]
    op_to_regime = build_op_to_regime(meta_regimes)
    operacoes_validas = set(operacoes.keys())

    # --------------------------------------------------
    # 1) indice_conceito_operacoes.json
    # --------------------------------------------------
    indice_conceito_operacoes = {}

    for cid, c in conceitos.items():
        ops = flatten_ops(c.get("operacoes_ontologicas", {}))

        # valida operações
        invalidas = sorted([o for o in ops if o not in operacoes_validas])
        if invalidas:
            raise ValueError(f"Conceito {cid} tem operações inválidas: {invalidas}")

        regimes = regimes_from_ops(ops, op_to_regime)

        indice_conceito_operacoes[cid] = {
            "operacoes": ops,
            "regimes_ativados": regimes
        }

    # --------------------------------------------------
    # 2) indice_de_percursos.json (por tipo_instancia)
    # --------------------------------------------------
    indice_de_percursos = defaultdict(list)

    for pid, info in meta_ref.items():
        t = info.get("tipo_instancia")
        if not t:
            raise ValueError(f"meta_referencia_do_percurso: {pid} sem tipo_instancia")
        indice_de_percursos[t].append(pid)

    # ordenação determinística
    indice_de_percursos = {k: sorted(v) for k, v in sorted(indice_de_percursos.items(), key=lambda x: x[0])}

    # --------------------------------------------------
    # 3) ler percursos reais + inferir regimes por percurso
    # --------------------------------------------------
    percursos = read_percurso_files(DIR_PERCURSOS)

    # por regime: regime -> [percursos]
    indice_por_regime = defaultdict(set)

    # também guardamos um mapa auxiliar percurso->regimes para patologias/consistência
    percurso_regimes = {}

    for pid, p in percursos.items():
        ops_ativas = p.get("operacoes_ativas", []) or []
        ops_correcao = p.get("operacoes_de_correcao", []) or []

        if not isinstance(ops_ativas, list) or not isinstance(ops_correcao, list):
            raise ValueError(f"Percurso {pid}: operacoes_ativas/operacoes_de_correcao devem ser listas")

        ops = sorted(set(ops_ativas + ops_correcao))

        # valida operações do percurso
        invalidas = sorted([o for o in ops if o not in operacoes_validas])
        if invalidas:
            raise ValueError(f"Percurso {pid} tem operações inválidas: {invalidas}")

        regs = regimes_from_ops(ops, op_to_regime)
        percurso_regimes[pid] = regs

        for r in regs:
            indice_por_regime[r].add(pid)

    indice_por_regime = {k: sorted(list(v)) for k, v in sorted(indice_por_regime.items(), key=lambda x: x[0])}

    # --------------------------------------------------
    # 4) indice_de_patologias.json (derivado de tipo_instancia)
    # --------------------------------------------------
    patologias = {
        "percursos_esteris": [],
        "percursos_degenerativos": [],
        "percursos_criticos": []
    }

    for pid, info in meta_ref.items():
        t = tipo_normalizado(info.get("tipo_instancia", ""))

        # regras automáticas (podes refinar depois)
        if "esteril" in t:
            patologias["percursos_esteris"].append(pid)
        if "degeneracao" in t or "degenerativo" in t:
            patologias["percursos_degenerativos"].append(pid)
        if "critico" in t:
            patologias["percursos_criticos"].append(pid)

    # ordenação determinística
    for k in list(patologias.keys()):
        patologias[k] = sorted(set(patologias[k]))

    # --------------------------------------------------
    # Guardar tudo
    # --------------------------------------------------
    save_json(OUT_CONCEITO_OPERACOES, indice_conceito_operacoes)
    save_json(OUT_DE_PERCURSOS, indice_de_percursos)
    save_json(OUT_POR_REGIME, indice_por_regime)
    save_json(OUT_PATOLOGIAS, patologias)

    print("\n================ GERACAO INDICES DERIVADOS ================\n")
    print(f"✔ indice_conceito_operacoes.json  -> {OUT_CONCEITO_OPERACOES}")
    print(f"✔ indice_de_percursos.json        -> {OUT_DE_PERCURSOS}")
    print(f"✔ indice_por_regime.json          -> {OUT_POR_REGIME}")
    print(f"✔ indice_de_patologias.json       -> {OUT_PATOLOGIAS}")
    print("\n===========================================================\n")

if __name__ == "__main__":
    main()