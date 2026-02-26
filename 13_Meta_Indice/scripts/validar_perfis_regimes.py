import os
import json

# =====================================================
# CONTEXTO DO PROJETO
# =====================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PASTA_PERCURSOS = os.path.join(BASE_DIR, "percursos")
PASTA_META = os.path.join(BASE_DIR, "meta")
PASTA_PERFIS = os.path.join(BASE_DIR, "perfis_de_regimes")

META_INDICE_FILE = os.path.join(PASTA_META, "meta_indice.json")


# =====================================================
# CARREGAMENTOS
# =====================================================

def carregar_meta_indice():
    with open(META_INDICE_FILE, encoding="utf-8") as f:
        return json.load(f)["meta_indice"]["regimes"]


def carregar_ids_percursos():
    ids = set()
    for fname in os.listdir(PASTA_PERCURSOS):
        if fname.endswith(".json"):
            with open(os.path.join(PASTA_PERCURSOS, fname), encoding="utf-8") as f:
                p = json.load(f)
                if "id" in p:
                    ids.add(p["id"])
    return ids


def carregar_perfis():
    perfis = {}
    for fname in os.listdir(PASTA_PERFIS):
        if fname.endswith(".json"):
            with open(os.path.join(PASTA_PERFIS, fname), encoding="utf-8") as f:
                perfis[fname] = json.load(f)
    return perfis


# =====================================================
# VALIDAÇÃO
# =====================================================

def validar_perfil(perfil, percursos_ids, regimes_meta):
    erros = []
    avisos = []

    pid = perfil.get("id")
    percurso_ref = perfil.get("percurso_ref")
    criterio = perfil.get("criterio_ultimo")

    regimes = perfil.get("regimes", {})
    ativados = set(regimes.get("ativados", []))
    pressupostos = set(regimes.get("pressupostos", []))
    excluidos = set(regimes.get("excluidos", []))
    retorno = set(regimes.get("retorno", []))

    # ----------------------------------------------
    # Percurso existente
    # ----------------------------------------------

    if percurso_ref not in percursos_ids:
        erros.append(f"percurso_ref inexistente: {percurso_ref}")

    # ----------------------------------------------
    # Critério último
    # ----------------------------------------------

    if criterio != "D_REAL":
        erros.append(f"critério último inválido: {criterio}")

    # ----------------------------------------------
    # Regimes existentes
    # ----------------------------------------------

    todos = ativados | pressupostos | excluidos | retorno

    for r in todos:
        if r not in regimes_meta:
            erros.append(f"regime inexistente no meta-índice: {r}")

    # ----------------------------------------------
    # Contradições estruturais
    # ----------------------------------------------

    intersecoes = [
        ("ativados", "excluidos", ativados & excluidos),
        ("ativados", "pressupostos", ativados & pressupostos),
        ("pressupostos", "excluidos", pressupostos & excluidos),
    ]

    for a, b, inter in intersecoes:
        for r in inter:
            erros.append(f"regime {r} em conflito: {a} e {b}")

    # ----------------------------------------------
    # Regime corretivo
    # ----------------------------------------------

    if "REGIME_CORRETIVO" in ativados:
        erros.append("REGIME_CORRETIVO não pode estar em 'ativados'")

    if retorno and retorno != {"REGIME_CORRETIVO"}:
        avisos.append("retorno contém regimes além do REGIME_CORRETIVO")

    return erros, avisos


# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":
    print("\n=== VALIDAÇÃO DOS PERFIS DE REGIMES ===\n")

    regimes_meta = carregar_meta_indice()
    percursos_ids = carregar_ids_percursos()
    perfis = carregar_perfis()

    total_erros = 0
    total_avisos = 0

    for fname, perfil in perfis.items():
        erros, avisos = validar_perfil(perfil, percursos_ids, regimes_meta)

        if erros or avisos:
            print(f"🔎 {perfil.get('id', fname)}")

        for e in erros:
            print(f"   ❌ {e}")
            total_erros += 1

        for a in avisos:
            print(f"   ⚠️ {a}")
            total_avisos += 1

        if erros or avisos:
            print()

    if total_erros == 0:
        print("✅ Todos os perfis de regimes estão estruturalmente válidos.")
    else:
        print(f"❗ {total_erros} erro(s) detetado(s).")

    if total_avisos:
        print(f"⚠️ {total_avisos} aviso(s).")