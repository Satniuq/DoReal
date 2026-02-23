# expor_estrutura_do_real.py

from carregar_conceitos import carregar_conceitos
from identidade_do_projeto_2 import (
    extrair_nucleo_minimo,
    extrair_transicao_antropologica,
    extrair_eixo_epistemologico,
    extrair_eixo_etico,
    construir_inverso,
)
import os
import json

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PASTA_PERCURSOS = os.path.join(BASE_DIR, "percursos")
FICHEIRO_SAIDA = os.path.join(BASE_DIR, "exposicao_estrutural_do_real.txt")


# =====================================================
# UTILIDADES
# =====================================================

def carregar_percursos():
    percursos = []
    for fname in os.listdir(PASTA_PERCURSOS):
        if fname.endswith(".json"):
            with open(os.path.join(PASTA_PERCURSOS, fname), encoding="utf-8") as f:
                percursos.append(json.load(f))
    return percursos


def percursos_do_conceito(cid, percursos):
    usados = []
    for p in percursos:
        if cid in p.get("sequencia", []):
            usados.append(p["id"])
    return usados


# =====================================================
# EXPOSIÇÃO FILOSÓFICA
# =====================================================

def expor_conceito(cid, c, classificacao, inverso, percursos, write):
    write("\n" + "=" * 72)
    write(f"CONCEITO: {cid}")
    write("-" * 72)

    write(f"• Classificação estrutural: {classificacao}")
    write(f"• Nível ontológico: {c['nivel']}")
    write(f"• Domínio: {c['dominio']}")

    est = c.get("estatuto_ontologico", {})
    write(f"• Afirmação ontológica: {est.get('afirmacao_ontologica')}")
    write(f"• Tipo ontológico: {est.get('tipo')}")

    pais = inverso.get(cid, [])
    if pais:
        write(f"• Depende estruturalmente de: {', '.join(pais)}")
    else:
        write("• Não depende estruturalmente de nenhum outro conceito")

    usados = percursos_do_conceito(cid, percursos)
    if usados:
        write("• Integra os seguintes percursos:")
        for p in usados:
            write(f"   - {p}")
    else:
        write("• Não é utilizado diretamente em nenhum percurso")

    # Síntese filosófica mínima
    write("\nSíntese filosófica:")
    if classificacao.startswith("I."):
        write("→ Conceito fundacional: condição estrutural do real.")
    elif classificacao.startswith("II."):
        write("→ Conceito de transição: abre o domínio antropológico sem fundar o real.")
    elif classificacao.startswith("III."):
        write("→ Conceito epistemológico: regula a relação mediada com o real.")
    elif classificacao.startswith("IV."):
        write("→ Conceito ético: deriva do poder-ser e dos seus efeitos reais.")
    elif classificacao.startswith("V."):
        write("→ Estrutura ontológica derivada: real, mas não fundacional.")
    else:
        write("→ Forma de manifestação ou mediação: não fundacional.")


# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":
    conceitos = carregar_conceitos(os.path.join(BASE_DIR, "conceitos"))
    percursos = carregar_percursos()
    inverso = construir_inverso(conceitos)

    nucleo = extrair_nucleo_minimo(conceitos, inverso)
    transicao = extrair_transicao_antropologica(conceitos, inverso)
    eixo_ep = extrair_eixo_epistemologico(conceitos)
    eixo_et = extrair_eixo_etico(conceitos)

    from identidade_do_projeto_2 import classificar

    classificacoes = {
        cid: classificar(cid, c, nucleo, transicao, eixo_ep, eixo_et)
        for cid, c in conceitos.items()
    }

    with open(FICHEIRO_SAIDA, "w", encoding="utf-8") as f:

        def write(text=""):
            f.write(text + "\n")

        write("EXPOSIÇÃO ESTRUTURAL DO REAL")
        write("O sistema ontológico mostra-se a si próprio.\n")

        for cid in sorted(conceitos):
            expor_conceito(
                cid,
                conceitos[cid],
                classificacoes[cid],
                inverso,
                percursos,
                write
            )