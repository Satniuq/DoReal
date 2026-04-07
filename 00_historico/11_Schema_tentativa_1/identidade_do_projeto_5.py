# =====================================================
# IDENTIDADE DO PROJETO — EXPOSIÇÃO DA COERÊNCIA FILOSÓFICA
# Versão 5 — com transições ontológicas explícitas
# =====================================================

import os
import sys

# -----------------------------------------------------
# CONTEXTO DO PROJETO
# -----------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from carregar_conceitos import carregar_conceitos


# -----------------------------------------------------
# UTILIDADES DE IMPRESSÃO FILOSÓFICA
# -----------------------------------------------------

def titulo(texto):
    print("\n" + "=" * 60)
    print(texto)
    print("=" * 60 + "\n")


def secao(texto):
    print("\n" + texto + "\n")


def transicao(texto):
    print("\n" + "-" * 60)
    print(texto)
    print("-" * 60 + "\n")


def listar_dependencias(cid, c):
    deps = c.get("dependencias", {}).get("depende_de", [])
    if deps:
        print(f"• {cid}")
        print(f"  depende de: {', '.join(deps)}\n")


# -----------------------------------------------------
# EXECUÇÃO PRINCIPAL
# -----------------------------------------------------

if __name__ == "__main__":

    conceitos = carregar_conceitos(os.path.join(BASE_DIR, "conceitos"))

    titulo("EXPOSIÇÃO DA COERÊNCIA FILOSÓFICA DO SISTEMA")

    # =================================================
    # I. FUNDAÇÃO SEM EXTERIORIDADE
    # =================================================

    secao("I. FUNDAÇÃO SEM EXTERIORIDADE")

    print(
        "O sistema ontológico constitui o real sem recurso a instâncias externas,\n"
        "subjetivas, normativas ou transcendentais.\n"
        "Nenhum conceito funda o real: o real é condição estrutural irredutível."
    )

    transicao(
        "Se o real não é fundado,\n"
        "então tudo o que emerge deve fazê-lo\n"
        "sem introduzir novas instâncias fundacionais."
    )

    # =================================================
    # II. DERIVAÇÃO SEM RUTURA ONTOLÓGICA
    # =================================================

    secao("II. DERIVAÇÃO SEM RUTURA ONTOLÓGICA")

    print(
        "As estruturas ontológicas derivadas emergem do real\n"
        "como diferenciações internas, não como níveis exteriores.\n"
        "Não há salto ontológico, criação ex nihilo ou autonomização estrutural."
    )

    transicao(
        "Se toda a derivação permanece interna ao real,\n"
        "então a mediação não suspende a ontologia,\n"
        "apenas a diferencia."
    )

    # =================================================
    # III. ERRO SEM RELATIVISMO
    # =================================================

    secao("III. ERRO SEM RELATIVISMO")

    print(
        "O erro não emerge da arbitrariedade, nem da pluralidade de perspetivas,\n"
        "mas da mediação situada entre representação e real.\n"
        "A possibilidade do erro é estrutural porque há resistência ontológica."
    )

    transicao(
        "Se o acesso ao real é sempre mediado e situado,\n"
        "então o erro não é acidente psicológico,\n"
        "mas possibilidade estrutural da relação com o real."
    )

    for cid, c in conceitos.items():
        if c.get("dominio") == "epistemologico":
            listar_dependencias(cid, c)

    transicao(
        "A epistemologia não funda o real,\n"
        "mas responde à sua resistência.\n"
        "Por isso, o erro informa — não relativiza."
    )

    # =================================================
    # IV. ÉTICA SEM NORMATIVISMO AUTÓNOMO
    # =================================================

    secao("IV. ÉTICA SEM NORMATIVISMO AUTÓNOMO")

    print(
        "A ética emerge da atualização situada do poder-ser,\n"
        "dos seus limites e dos seus efeitos reais.\n"
        "Não há valores externos, nem normatividade autónoma."
    )

    transicao(
        "Se toda a ação atualiza o real e produz efeitos irreversíveis,\n"
        "então responsabilidade, bem e mal\n"
        "não são convenções, mas determinações ontológicas derivadas."
    )

    for cid, c in conceitos.items():
        if c.get("dominio") in {"etico", "etico-ontologico"}:
            print(f"• {cid}")
            tipo = c.get("estatuto_ontologico", {}).get("tipo")
            if tipo:
                print(f"  tipo: {tipo}")
            deps = c.get("dependencias", {}).get("depende_de", [])
            if deps:
                print(f"  depende de: {', '.join(deps)}")
            print()

    transicao(
        "O dever-ser não impõe o real:\n"
        "projeta temporalmente modos de atualização\n"
        "já inscritos no poder-ser."
    )

    # =================================================
    # CONCLUSÃO
    # =================================================

    secao("CONCLUSÃO")

    print(
        "O sistema mostra que:\n"
        "• o real não é fundado\n"
        "• a epistemologia não é subjetiva\n"
        "• a ética não é normativa por decreto\n"
        "• e nenhuma etapa introduz arbitrariedade\n\n"
        "Cada domínio emerge como diferenciação interna do real,\n"
        "mantendo continuidade ontológica, critério último e possibilidade de correção."
    )