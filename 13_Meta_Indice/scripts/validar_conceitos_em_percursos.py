# validar_conceitos_em_percursos.py

import os
import json
import sys
from functools import lru_cache

BASE = os.path.dirname(os.path.dirname(__file__))

PASTA_PERCURSOS = os.path.join(BASE, "percursos")
FICHEIRO_CONCEITOS = os.path.join(BASE, "dados_base", "todos_os_conceitos.json")
FICHEIRO_META_REF = os.path.join(BASE, "meta", "meta_referencia_do_percurso.json")

# --------------------------------------------------
# carregar dados
# --------------------------------------------------

with open(FICHEIRO_CONCEITOS, encoding="utf-8") as f:
    CONCEITOS = json.load(f)

with open(FICHEIRO_META_REF, encoding="utf-8") as f:
    META_REF = json.load(f)

# índice rápido dos percursos
PERCURSOS = {}
for fname in os.listdir(PASTA_PERCURSOS):
    if fname.startswith("P_") and fname.endswith(".json"):
        with open(os.path.join(PASTA_PERCURSOS, fname), encoding="utf-8") as f:
            p = json.load(f)
            PERCURSOS[p["id"]] = p


# --------------------------------------------------
# utilitário: fecho ontológico dos pressupostos
# --------------------------------------------------

@lru_cache(None)
def percursos_pressupostos(pid):
    """
    Retorna o conjunto de percursos pressupostos direta ou indiretamente.
    """
    if pid not in META_REF:
        return set()

    diretos = set(META_REF[pid].get("pressupoe_percursos", []))
    todos = set(diretos)

    for p in diretos:
        todos |= percursos_pressupostos(p)

    return todos


def conceitos_disponiveis_por_pressuposto(pid):
    """
    Constrói o conjunto de conceitos já ontologicamente disponíveis
    antes do percurso começar, por via dos pressupostos.
    """
    disponiveis = set()

    for p in percursos_pressupostos(pid):
        percurso = PERCURSOS.get(p)
        if not percurso:
            continue
        disponiveis.update(percurso.get("sequencia", []))

    return disponiveis


# --------------------------------------------------
# validação de um percurso
# --------------------------------------------------

def validar_percurso(percurso):
    erros = []

    pid = percurso.get("id", "<sem id>")
    sequencia = percurso.get("sequencia", [])

    # conceitos já disponíveis por pressuposição ontológica
    vistos = set(conceitos_disponiveis_por_pressuposto(pid))

    for idx, cid in enumerate(sequencia):
        if cid not in CONCEITOS:
            erros.append(
                f"[{pid}] conceito inexistente: {cid} (posição {idx})"
            )
            continue

        deps = CONCEITOS[cid].get("dependencias", {}).get("depende_de", [])
        faltam = [d for d in deps if d not in vistos]

        if faltam:
            erros.append(
                f"[{pid}] {cid} usado sem pressupor dependências ontológicas: {', '.join(faltam)}"
            )

        vistos.add(cid)

    return erros


# --------------------------------------------------
# main
# --------------------------------------------------

def main():
    print("\n=== VALIDAÇÃO DE CONCEITOS NOS PERCURSOS (COM META-REFERÊNCIA) ===")

    erros_totais = 0

    for pid in sorted(PERCURSOS.keys()):
        percurso = PERCURSOS[pid]
        erros = validar_percurso(percurso)

        if erros:
            print(f"\n🔎 {pid}")
            for e in erros:
                print("   ❌", e)
            erros_totais += len(erros)

    if erros_totais == 0:
        print("\n✅ Todos os percursos respeitam as dependências ontológicas (com pressupostos).")
    else:
        print(f"\n❗ {erros_totais} erro(s) de dependência ontológica detetado(s).")
        sys.exit(1)


if __name__ == "__main__":
    main()