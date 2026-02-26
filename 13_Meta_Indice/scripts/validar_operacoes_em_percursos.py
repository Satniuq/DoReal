import os
import json
import difflib

# =====================================================
# CONTEXTO DO PROJETO
# =====================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PASTA_PERCURSOS = os.path.join(BASE_DIR, "percursos")
PASTA_DADOS = os.path.join(BASE_DIR, "dados_base")

OPERACOES_FILE = os.path.join(PASTA_DADOS, "operacoes.json")

# =====================================================
# HELPERS
# =====================================================

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def list_json_files(folder):
    return [f for f in os.listdir(folder) if f.endswith(".json")]

def sugerir_correcao(nome, universo):
    sugestoes = difflib.get_close_matches(nome, universo, n=3, cutoff=0.75)
    return sugestoes

# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":

    print("\n=== VALIDAÇÃO DE OPERAÇÕES NOS PERCURSOS ===\n")

    operacoes_validas = set(load_json(OPERACOES_FILE).keys())

    total_erros = 0

    for fname in sorted(list_json_files(PASTA_PERCURSOS)):
        path = os.path.join(PASTA_PERCURSOS, fname)
        percurso = load_json(path)

        pid = percurso.get("id", fname)

        ops_ativas = percurso.get("operacoes_ativas", []) or []
        ops_correcao = percurso.get("operacoes_de_correcao", []) or []

        todas_ops = sorted(set(ops_ativas + ops_correcao))

        erros_local = []

        for op in todas_ops:
            if op not in operacoes_validas:
                sugestoes = sugerir_correcao(op, operacoes_validas)
                erros_local.append((op, sugestoes))

        if erros_local:
            print(f"🔎 {pid}")
            for op, sugestoes in erros_local:
                print(f"   ❌ Operação inválida: {op}")
                if sugestoes:
                    print(f"      ➜ Sugestões: {sugestoes}")
                else:
                    print("      ➜ Sem sugestão automática")
                total_erros += 1
            print()

    if total_erros == 0:
        print("✅ Todas as operações nos percursos são válidas.")
    else:
        print("===================================================")
        print(f"❗ Total de operações inválidas: {total_erros}")
        print("===================================================")

    print()