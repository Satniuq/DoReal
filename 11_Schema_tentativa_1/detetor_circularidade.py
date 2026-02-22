from carregar_conceitos import carregar_conceitos
from collections import defaultdict

# =====================================================
# Ordem estrutural ontológica
# (quanto maior, mais derivado)
# Eixos ético e epistemológico ficam FORA da hierarquia
# =====================================================

ORDEM_ESTRUTURAL = {
    "I. NUCLEO_ONTOLOGICO_MINIMO": 1,
    "I.5 ESTRUTURA_FUNDACIONAL": 2,
    "II. TRANSICAO_ANTROPOLOGICA": 3,
    "V. ESTRUTURA_ONTOLOGICA_DERIVADA": 4,
    "VI. MANIFESTACAO_OU_MEDIACAO": 5,

    # eixos laterais (não entram na lógica de circularidade)
    "III. EIXO_EPISTEMOLOGICO": 99,
    "IV. EIXO_ETICO": 99,
}


# =====================================================
# Classificação ontológica (versão corrigida – OPÇÃO A)
# =====================================================

def classificar(cid, c, nucleo, transicao, eixo_ep, eixo_et):
    if cid in nucleo:
        return "I. NUCLEO_ONTOLOGICO_MINIMO"

    if cid in transicao:
        return "II. TRANSICAO_ANTROPOLOGICA"

    if cid in eixo_ep:
        return "III. EIXO_EPISTEMOLOGICO"

    if cid in eixo_et:
        return "IV. EIXO_ETICO"

    est = c.get("estatuto_ontologico", {})

    if est.get("afirmacao_ontologica"):
        tipo = est.get("tipo", "")

        # 🔹 estruturas ontológicas fundacionais (pré-atualização)
        if tipo in {
            "conjunto_admissivel",
            "dimensao_estrutural",
            "condicao_minima",
            "exclusao_estrutural",
            "implicacao_ontologica",
        }:
            return "I.5 ESTRUTURA_FUNDACIONAL"

        # 🔹 restantes ontológicos reais derivados
        return "V. ESTRUTURA_ONTOLOGICA_DERIVADA"

    return "VI. MANIFESTACAO_OU_MEDIACAO"


# =====================================================
# Construção do grafo direto (depende_de)
# =====================================================

def construir_grafo(conceitos):
    grafo = defaultdict(list)
    for cid, c in conceitos.items():
        for dep in c.get("dependencias", {}).get("depende_de", []):
            grafo[cid].append(dep)
    return grafo


# =====================================================
# Detetor de circularidade ontológica ilegítima
# =====================================================

def detetar_circularidade(conceitos, classificacoes):
    grafo = construir_grafo(conceitos)
    inconsistencias = []

    for origem, deps in grafo.items():
        classe_origem = classificacoes.get(origem)
        if not classe_origem:
            continue

        nivel_origem = ORDEM_ESTRUTURAL.get(classe_origem, 99)

        for dep in deps:
            classe_dep = classificacoes.get(dep)
            if not classe_dep:
                continue

            nivel_dep = ORDEM_ESTRUTURAL.get(classe_dep, 99)

            # ignora eixos laterais
            if nivel_origem >= 99 or nivel_dep >= 99:
                continue

            # ✅ EXCEÇÃO FUNDACIONAL (OPÇÃO A)
            # Núcleo pode depender de Estrutura Fundacional
            if (
                classe_origem == "I. NUCLEO_ONTOLOGICO_MINIMO"
                and classe_dep == "I.5 ESTRUTURA_FUNDACIONAL"
            ):
                continue

            # ❌ regra geral
            if nivel_dep > nivel_origem:
                inconsistencias.append(
                    (origem, classe_origem, dep, classe_dep)
                )

    return inconsistencias


# =====================================================
# Execução
# =====================================================

if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")

    from identidade_do_projeto_2 import (
        extrair_nucleo_minimo,
        extrair_transicao_antropologica,
        extrair_eixo_epistemologico,
        extrair_eixo_etico,
        construir_inverso,
    )

    inverso = construir_inverso(conceitos)

    nucleo = extrair_nucleo_minimo(conceitos, inverso)
    transicao = extrair_transicao_antropologica(conceitos, inverso)
    eixo_ep = extrair_eixo_epistemologico(conceitos)
    eixo_et = extrair_eixo_etico(conceitos)

    classificacoes = {
        cid: classificar(cid, c, nucleo, transicao, eixo_ep, eixo_et)
        for cid, c in conceitos.items()
    }

    erros = detetar_circularidade(conceitos, classificacoes)

    print("\n=== DETETOR DE CIRCULARIDADE ONTOLÓGICA (OPÇÃO A) ===\n")

    if not erros:
        print("✅ Nenhuma circularidade ontológica ilegítima detetada.")
    else:
        for o, co, d, cd in erros:
            print(f"❗ {o} ({co}) depende de {d} ({cd})")
        print(f"\n⚠️ Total de circularidades ilegítimas: {len(erros)}")