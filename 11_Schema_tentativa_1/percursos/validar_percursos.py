import sys
import os
import json

# =====================================================
# CONTEXTO DO PROJETO
# =====================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from carregar_conceitos import carregar_conceitos

# =====================================================
# CONFIGURAÇÃO
# =====================================================

PASTA_PERCURSOS = os.path.join(BASE_DIR, "percursos")
PASTA_OPERACOES = os.path.join(BASE_DIR, "operacoes")

# Conceitos explicitamente proibidos (legado de segurança)
CONCEITOS_INVALIDOS = {
    "D_ERRO",
    "D_INADEQUACAO",
    "D_DEGENERACAO",
    "D_REINTEGRACAO_ONTOLOGICA",
}

# =====================================================
# CARREGAMENTOS
# =====================================================

def carregar_operacoes():
    caminho = os.path.join(PASTA_OPERACOES, "operacoes.json")
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def carregar_percursos():
    percursos = {}
    for fname in os.listdir(PASTA_PERCURSOS):
        if fname.endswith(".json"):
            with open(os.path.join(PASTA_PERCURSOS, fname), encoding="utf-8") as f:
                percursos[fname] = json.load(f)
    return percursos


# =====================================================
# VALIDAÇÃO
# =====================================================

def validar_percurso(pid, p, conceitos, operacoes):
    erros = []
    avisos = []

    sequencia = p.get("sequencia", [])
    inicio = p.get("inicio")
    termino = p.get("termino")
    tipo = p.get("tipo", "")
    estatuto = p.get("estatuto_do_percurso", {})

    transversal = estatuto.get("transversal", False)
    natureza = estatuto.get("natureza", "")

    # -------------------------------------------------
    # Sequência estrutural
    # -------------------------------------------------

    if not sequencia:
        erros.append("sequência vazia")

    if sequencia and sequencia[0] != inicio:
        erros.append(f"inicio ({inicio}) não coincide com o primeiro da sequência")

    if sequencia and sequencia[-1] != termino:
        erros.append(f"termino ({termino}) não coincide com o último da sequência")

    # -------------------------------------------------
    # Conceitos
    # -------------------------------------------------

    for c in sequencia:
        if c in CONCEITOS_INVALIDOS:
            erros.append(f"conceito inválido usado: {c}")
        elif c not in conceitos:
            erros.append(f"conceito inexistente: {c}")

    # -------------------------------------------------
    # Operações ativas
    # -------------------------------------------------

    for op in p.get("operacoes_ativas", []):
        if op not in operacoes:
            erros.append(f"operação inexistente: {op}")
            continue

        tipo_op = operacoes[op].get("tipo", "")

        # Operações epistemológicas
        if tipo_op == "epistemologica":

            # Caso legítimo: percurso epistemológico
            if "epistemologico" in tipo:
                continue

            # Caso legítimo: percurso transversal (vida filosófica, ética crítica, etc.)
            if transversal:
                continue

            # Caso intermédio: ontológico com incursão epistemológica
            avisos.append(
                f"operação epistemológica usada em percurso não epistemológico nem transversal: {op}"
            )

    # -------------------------------------------------
    # Operações de correção
    # -------------------------------------------------

    for op in p.get("operacoes_de_correcao", []):
        if op not in operacoes:
            erros.append(f"operação de correção inexistente: {op}")
            continue

        criterio = operacoes[op].get("criterio_ultimo")

        if criterio != "D_REAL":
            erros.append(
                f"operação de correção sem critério último no real: {op}"
            )

    return erros, avisos


# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":
    conceitos = carregar_conceitos(os.path.join(BASE_DIR, "conceitos"))
    operacoes = carregar_operacoes()
    percursos = carregar_percursos()

    print("\n=== VALIDAÇÃO DOS PERCURSOS ===\n")

    total_erros = 0
    total_avisos = 0

    for fname, percurso in percursos.items():
        pid = percurso.get("id", fname)
        erros, avisos = validar_percurso(pid, percurso, conceitos, operacoes)

        if erros or avisos:
            print(f"🔎 {pid}")

        for e in erros:
            print(f"   ❌ {e}")
            total_erros += 1

        for a in avisos:
            print(f"   ⚠️ {a}")
            total_avisos += 1

        if erros or avisos:
            print()

    if total_erros == 0:
        print("✅ Todos os percursos estão estruturalmente válidos.")
    else:
        print(f"❗ {total_erros} erro(s) detetado(s).")

    if total_avisos:
        print(f"⚠️ {total_avisos} aviso(s).")