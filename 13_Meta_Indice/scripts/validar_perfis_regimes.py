import os
import json
from collections import defaultdict

# =====================================================
# CONTEXTO DO PROJETO
# =====================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PASTA_PERCURSOS = os.path.join(BASE_DIR, "percursos")
PASTA_META = os.path.join(BASE_DIR, "meta")
PASTA_PERFIS = os.path.join(BASE_DIR, "perfis_de_regimes")

META_INDICE_FILE = os.path.join(PASTA_META, "meta_indice.json")

# =====================================================
# HELPERS
# =====================================================

def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def list_json_files(folder: str):
    return [fn for fn in os.listdir(folder) if fn.lower().endswith(".json")]

def norm_list(x):
    if not isinstance(x, list):
        return []
    return x

# =====================================================
# CARREGAMENTOS
# =====================================================

def carregar_meta_indice_regimes():
    meta = load_json(META_INDICE_FILE)["meta_indice"]["regimes"]

    op_to_regime = {}
    colisoes = defaultdict(set)

    for regime, bloco in meta.items():
        for op in bloco.get("operacoes", []) or []:
            if op in op_to_regime and op_to_regime[op] != regime:
                colisoes[op].add(op_to_regime[op])
                colisoes[op].add(regime)
            op_to_regime[op] = regime

    if colisoes:
        raise ValueError("Operações duplicadas em regimes no meta_indice.")

    return meta, op_to_regime

def carregar_percursos_por_id():
    percursos = {}
    for fname in list_json_files(PASTA_PERCURSOS):
        p = load_json(os.path.join(PASTA_PERCURSOS, fname))
        percursos[p["id"]] = p
    return percursos

def carregar_perfis():
    perfis = {}
    for fname in list_json_files(PASTA_PERFIS):
        perfis[fname] = load_json(os.path.join(PASTA_PERFIS, fname))
    return perfis

# =====================================================
# INFERÊNCIA
# =====================================================

def inferir_regimes(percurso, op_to_regime):
    ops = set(norm_list(percurso.get("operacoes_ativas")))
    ops |= set(norm_list(percurso.get("operacoes_de_correcao")))
    return sorted(set(op_to_regime[o] for o in ops if o in op_to_regime)), sorted(ops)

# =====================================================
# VALIDAÇÃO
# =====================================================

def validar_perfil(perfil, percursos, meta_regimes, op_to_regime):
    erros = []
    avisos = []

    pid = perfil.get("id")
    percurso_ref = perfil.get("percurso_ref")

    if percurso_ref not in percursos:
        erros.append(f"percurso_ref inexistente: {percurso_ref}")
        return erros, avisos

    percurso = percursos[percurso_ref]
    regimes_inferidos, ops_total = inferir_regimes(percurso, op_to_regime)
    regimes_inferidos_set = set(regimes_inferidos)

    regimes = perfil.get("regimes", {})
    ativados = set(norm_list(regimes.get("ativados")))
    pressupostos = set(norm_list(regimes.get("pressupostos")))
    excluidos = set(norm_list(regimes.get("excluidos")))
    inaplicaveis = set(norm_list(regimes.get("inaplicaveis")))

    # ----------------------------------------
    # REGRA FORTE: ativados == inferidos
    # ----------------------------------------

    if ativados != regimes_inferidos_set:
        faltam = sorted(regimes_inferidos_set - ativados)
        sobram = sorted(ativados - regimes_inferidos_set)
        erros.append(
            "regimes.ativados divergente do inferido por operações"
            + (f" | faltam: {faltam}" if faltam else "")
            + (f" | sobram: {sobram}" if sobram else "")
        )

    # ----------------------------------------
    # Conflitos estruturais
    # ----------------------------------------

    conflitos = [
        ("ativados", ativados, "pressupostos", pressupostos),
        ("ativados", ativados, "excluidos", excluidos),
        ("ativados", ativados, "inaplicaveis", inaplicaveis),
        ("pressupostos", pressupostos, "excluidos", excluidos),
        ("pressupostos", pressupostos, "inaplicaveis", inaplicaveis),
        ("excluidos", excluidos, "inaplicaveis", inaplicaveis),
    ]

    for a_name, a_set, b_name, b_set in conflitos:
        inter = a_set & b_set
        for r in sorted(inter):
            erros.append(f"regime {r} em conflito: {a_name} e {b_name}")

    # ----------------------------------------
    # Regra correta do corretivo
    # ----------------------------------------

    if "OP_REINTEGRACAO_ONTOLOGICA" in ops_total:
        if "REGIME_CORRETIVO" not in regimes_inferidos_set:
            erros.append("OP_REINTEGRACAO_ONTOLOGICA presente mas REGIME_CORRETIVO não inferido (meta_indice inconsistente)")

    # ----------------------------------------
    # Debug útil
    # ----------------------------------------

    if erros:
        avisos.append(f"percurso_ref={percurso_ref}")
        avisos.append(f"ops_total={ops_total}")
        avisos.append(f"regimes_inferidos={regimes_inferidos}")

    return erros, avisos

# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":
    print("\n=== VALIDAÇÃO DOS PERFIS DE REGIMES (v3 — estável) ===\n")

    meta_regimes, op_to_regime = carregar_meta_indice_regimes()
    percursos = carregar_percursos_por_id()
    perfis = carregar_perfis()

    total_erros = 0

    for fname, perfil in sorted(perfis.items()):
        erros, avisos = validar_perfil(perfil, percursos, meta_regimes, op_to_regime)

        if erros or avisos:
            print(f"🔎 {perfil.get('id', fname)}")

        for e in erros:
            print(f"   ❌ {e}")
            total_erros += 1

        for a in avisos:
            print(f"   ⚠️ {a}")

        if erros or avisos:
            print()

    if total_erros == 0:
        print("✅ Perfis semanticamente consistentes.")
    else:
        print(f"❗ {total_erros} erro(s) detetado(s).")