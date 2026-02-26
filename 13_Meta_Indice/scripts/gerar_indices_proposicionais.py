import os
import json
from collections import defaultdict

# =====================================================
# CONTEXTO
# =====================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PASTA_META = os.path.join(BASE_DIR, "meta")
PASTA_PERFIS = os.path.join(BASE_DIR, "perfis_de_regimes")
PASTA_INDICES = os.path.join(BASE_DIR, "indices_derivados")

PROPOSICOES_FILE = os.path.join(
    BASE_DIR, "dados_base", "proposicoes", "proposicoes_normalizadas.json"
)
META_FILE = os.path.join(PASTA_META, "meta_indice.json")

# =====================================================
# HELPERS
# =====================================================

def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def list_json_files(folder: str):
    return [fn for fn in os.listdir(folder) if fn.lower().endswith(".json")]

def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def as_list(x):
    return x if isinstance(x, list) else []

# =====================================================
# LOADERS
# =====================================================

def carregar_proposicoes():
    data = load_json(PROPOSICOES_FILE)
    if isinstance(data, list):
        return data
    # segurança: se vier num dict {"proposicoes":[...]}
    if isinstance(data, dict) and "proposicoes" in data and isinstance(data["proposicoes"], list):
        return data["proposicoes"]
    return []

def carregar_meta_regimes():
    return load_json(META_FILE)["meta_indice"]["regimes"]

def carregar_perfis():
    perfis = {}
    for fname in list_json_files(PASTA_PERFIS):
        path = os.path.join(PASTA_PERFIS, fname)
        perfis[fname] = load_json(path)
    return perfis

# =====================================================
# GERAÇÃO
# =====================================================

if __name__ == "__main__":

    print("\n=== GERAÇÃO DE ÍNDICES PROPOSICIONAIS ===\n")

    if not os.path.exists(PROPOSICOES_FILE):
        raise FileNotFoundError(f"Ficheiro não encontrado: {PROPOSICOES_FILE}")

    os.makedirs(PASTA_INDICES, exist_ok=True)

    proposicoes = carregar_proposicoes()
    meta_regimes = carregar_meta_regimes()  # aqui só para garantir que os regimes existem
    perfis = carregar_perfis()

    # --------------------------------------------
    # Estruturas
    # --------------------------------------------

    por_regime = defaultdict(list)
    por_regime_principal = defaultdict(list)
    por_nivel = defaultdict(list)
    por_campo = defaultdict(list)
    por_regime_nivel = defaultdict(lambda: defaultdict(list))
    por_percurso = defaultdict(list)

    # mapa regime -> percursos (a partir dos perfis)
    regime_para_percursos = defaultdict(set)
    for perfil in perfis.values():
        percurso = perfil.get("percurso_ref")
        ativados = as_list(perfil.get("regimes", {}).get("ativados", []))
        for r in ativados:
            regime_para_percursos[r].add(percurso)

    # --------------------------------------------
    # Processar proposições
    # --------------------------------------------

    total_sem_id = 0
    total_sem_nivel = 0
    total_sem_regimes = 0

    for p in proposicoes:

        pid = p.get("id_proposicao")
        if not pid:
            total_sem_id += 1
            continue

        loc = p.get("localizacao_vertical", {}) or {}
        nivel = loc.get("nivel")
        campo = loc.get("campo_principal")

        regimes = as_list(p.get("regimes_detectados", []))
        regime_principal = p.get("regime_principal")

        if nivel is None:
            total_sem_nivel += 1
        else:
            por_nivel[f"nivel_{nivel}"].append(pid)

        if campo:
            por_campo[campo].append(pid)

        if not regimes:
            total_sem_regimes += 1
        else:
            for r in regimes:
                por_regime[r].append(pid)
                if nivel is not None:
                    por_regime_nivel[r][f"nivel_{nivel}"].append(pid)

                # Por percurso (via regime -> percursos)
                for percurso in regime_para_percursos.get(r, set()):
                    por_percurso[percurso].append(pid)

        if regime_principal:
            por_regime_principal[regime_principal].append(pid)

    # --------------------------------------------
    # Ordenações e limpeza
    # --------------------------------------------

    def sort_lists(d):
        for k, v in d.items():
            if isinstance(v, list):
                d[k] = sorted(set(v))
            elif isinstance(v, dict):
                sort_lists(v)

    sort_lists(por_regime)
    sort_lists(por_regime_principal)
    sort_lists(por_nivel)
    sort_lists(por_campo)
    sort_lists(por_regime_nivel)
    sort_lists(por_percurso)

    # --------------------------------------------
    # Guardar
    # --------------------------------------------

    save_json(os.path.join(PASTA_INDICES, "indice_proposicoes_por_regime.json"), por_regime)
    print("✔ indice_proposicoes_por_regime.json")

    save_json(os.path.join(PASTA_INDICES, "indice_proposicoes_por_regime_principal.json"), por_regime_principal)
    print("✔ indice_proposicoes_por_regime_principal.json")

    save_json(os.path.join(PASTA_INDICES, "indice_proposicoes_por_nivel.json"), por_nivel)
    print("✔ indice_proposicoes_por_nivel.json")

    save_json(os.path.join(PASTA_INDICES, "indice_proposicoes_por_campo.json"), por_campo)
    print("✔ indice_proposicoes_por_campo.json")

    save_json(os.path.join(PASTA_INDICES, "indice_proposicoes_por_regime_e_nivel.json"), por_regime_nivel)
    print("✔ indice_proposicoes_por_regime_e_nivel.json")

    save_json(os.path.join(PASTA_INDICES, "indice_proposicoes_por_percurso.json"), por_percurso)
    print("✔ indice_proposicoes_por_percurso.json")

    # --------------------------------------------
    # Resumo
    # --------------------------------------------

    print("\n---------------------------")
    print(f"Total proposições lidas: {len(proposicoes)}")
    print(f"Sem id_proposicao: {total_sem_id}")
    print(f"Sem nivel: {total_sem_nivel}")
    print(f"Sem regimes_detectados: {total_sem_regimes}")
    print("---------------------------\n")