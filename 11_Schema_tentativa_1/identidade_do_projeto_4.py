import os
from collections import defaultdict
from carregar_conceitos import carregar_conceitos

# =====================================================
# EXPOSIÇÃO DA COERÊNCIA ONTOLÓGICA DO SISTEMA
# =====================================================
#
# Este script NÃO valida, NÃO corrige, NÃO impõe regras.
#
# Ele:
#   - percorre a ontologia do núcleo à ética
#   - mostra a derivação sem rutura
#   - evidencia a ausência de arbitrariedade
#
# O sistema expõe-se a si próprio.
# =====================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


# -----------------------------------------------------
# UTILIDADES
# -----------------------------------------------------

def ordenar_por_nivel(conceitos):
    return sorted(
        conceitos.items(),
        key=lambda x: (x[1].get("nivel_ontologico", 99), x[0])
    )


def conceitos_por_classificacao(conceitos):
    grupos = defaultdict(list)
    for cid, c in conceitos.items():
        grupos[c.get("classificacao_estrutural", "DESCONHECIDO")].append(cid)
    return grupos


# -----------------------------------------------------
# EXPOSIÇÃO
# -----------------------------------------------------

def expor_fundacao(conceitos):
    print("\nI. FUNDAÇÃO SEM EXTERIORIDADE\n")
    print("O real constitui-se sem recurso a instâncias externas, subjetivas ou normativas.\n")

    for cid, c in ordenar_por_nivel(conceitos):
        if c.get("classificacao_estrutural") == "I. NUCLEO_ONTOLOGICO_MINIMO":
            deps = c.get("dependencias", {}).get("depende_de", [])
            print(f"• {cid}")
            if deps:
                print(f"  depende de: {', '.join(deps)}")
            else:
                print("  não depende de nenhum outro conceito")
            print()


def expor_derivacao(conceitos):
    print("\nII. DERIVAÇÃO SEM RUTURA ONTOLÓGICA\n")
    print("As estruturas derivadas emergem do real sem introduzir novas fundações.\n")

    for cid, c in ordenar_por_nivel(conceitos):
        if c.get("classificacao_estrutural") == "V. ESTRUTURA_ONTOLOGICA_DERIVADA":
            print(f"• {cid}")
            print(f"  tipo: {c.get('tipo_ontologico')}")
            print(f"  depende de: {', '.join(c.get('dependencias', {}).get('depende_de', []))}")
            print()


def expor_erro_e_conhecimento(conceitos):
    print("\nIII. ERRO SEM RELATIVISMO\n")
    print("O erro emerge da mediação situada, não da arbitrariedade.\n")

    for cid, c in conceitos.items():
        if c.get("dominio") == "epistemologico":
            print(f"• {cid}")
            print(f"  depende de: {', '.join(c.get('dependencias', {}).get('depende_de', []))}")
            print()


def expor_etica(conceitos):
    print("\nIV. ÉTICA SEM NORMATIVISMO AUTÓNOMO\n")
    print("A ética deriva do poder-ser, dos seus limites e dos seus efeitos reais.\n")

    for cid, c in conceitos.items():
        if c.get("dominio", "").startswith("etico"):
            print(f"• {cid}")
            print(f"  tipo: {c.get('tipo_ontologico')}")
            print(f"  depende de: {', '.join(c.get('dependencias', {}).get('depende_de', []))}")
            print()


# -----------------------------------------------------
# EXECUÇÃO
# -----------------------------------------------------

if __name__ == "__main__":
    conceitos = carregar_conceitos(os.path.join(BASE_DIR, "conceitos"))

    print("\n==============================================")
    print("EXPOSIÇÃO DA COERÊNCIA FILOSÓFICA DO SISTEMA")
    print("==============================================")

    expor_fundacao(conceitos)
    expor_derivacao(conceitos)
    expor_erro_e_conhecimento(conceitos)
    expor_etica(conceitos)

    print("\nConclusão:")
    print(
        "O sistema mostra que:\n"
        "• o real não é fundado\n"
        "• a epistemologia não é subjetiva\n"
        "• a ética não é normativa por decreto\n"
        "• e nenhuma etapa introduz arbitrariedade\n"
    )