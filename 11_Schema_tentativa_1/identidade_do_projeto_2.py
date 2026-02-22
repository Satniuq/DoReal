from carregar_conceitos import carregar_conceitos
from collections import defaultdict


# =====================================================
# Regras ontológicas já assumidas no sistema
# =====================================================

TIPOS_NAO_FUNDACIONAIS = {
    "configuracao_funcional_localizada",
    "forma_dinamica",
    "manifestacao_dinamica",
    "forma_de_manifestacao",
    "manifestacao_fenomenologica",
    "descricao_dinamica",
}


def e_fundacional(c):
    est = c.get("estatuto_ontologico", {})
    if est.get("afirmacao_ontologica") is not True:
        return False, "afirmação ontológica falsa"

    tipo = est.get("tipo", "").strip()
    if tipo in TIPOS_NAO_FUNDACIONAIS:
        return False, f"tipo ontológico não fundacional ({tipo})"

    return True, "fundacional"


# =====================================================
# Grafo de dependências
# =====================================================

def construir_inverso(conceitos):
    inverso = defaultdict(list)
    for cid, c in conceitos.items():
        for dep in c.get("dependencias", {}).get("depende_de", []):
            inverso[cid].append(dep)
    return inverso


# =====================================================
# Profundidade ontológica
# =====================================================

def profundidade(cid, inverso, validos, memo):
    if cid in memo:
        return memo[cid]

    pais = [p for p in inverso.get(cid, []) if p in validos]
    if not pais:
        memo[cid] = 0
    else:
        memo[cid] = 1 + max(profundidade(p, inverso, validos, memo) for p in pais)

    return memo[cid]


# =====================================================
# Núcleo ontológico mínimo (cadeia axial máxima)
# =====================================================

def extrair_nucleo_minimo(conceitos, inverso, nivel_max=2):
    candidatos = {
        cid for cid, c in conceitos.items()
        if c["nivel"] <= nivel_max and e_fundacional(c)[0]
    }

    memo = {}
    profs = {cid: profundidade(cid, inverso, candidatos, memo) for cid in candidatos}

    fim = max(profs, key=lambda k: profs[k])

    eixo = []
    atual = fim
    while True:
        eixo.append(atual)
        pais = [p for p in inverso.get(atual, []) if p in candidatos]
        if not pais:
            break
        atual = max(pais, key=lambda k: profs[k])

    return set(reversed(eixo))


# =====================================================
# Eixos derivados
# =====================================================

def extrair_transicao_antropologica(conceitos, inverso):
    if "D_SER_HUMANO" not in conceitos:
        return set()

    caminho = ["D_SER_HUMANO"]
    atual = "D_SER_HUMANO"

    while True:
        pais = inverso.get(atual, [])
        if not pais:
            break
        atual = pais[0]
        caminho.append(atual)
        if atual == "D_REAL":
            break

    return set(caminho)


def extrair_eixo_epistemologico(conceitos):
    return {
        cid for cid, c in conceitos.items()
        if "epistemologico" in c["dominio"]
    }


def extrair_eixo_etico(conceitos):
    return {
        cid for cid, c in conceitos.items()
        if "etico" in c["dominio"]
    }


# =====================================================
# Classificação final (5 estratos)
# =====================================================

def classificar(cid, c, nucleo, transicao, eixo_ep, eixo_et):
    fund, _ = e_fundacional(c)

    if cid in nucleo:
        return "I. NUCLEO_ONTOLOGICO_MINIMO"

    if cid in transicao:
        return "II. TRANSICAO_ANTROPOLOGICA"

    if cid in eixo_ep:
        return "III. EIXO_EPISTEMOLOGICO"

    if cid in eixo_et:
        return "IV. EIXO_ETICO"

    if fund:
        return "V. ESTRUTURA_ONTOLOGICA_DERIVADA"

    return "VI. MANIFESTACAO_OU_MEDIACAO"


# =====================================================
# Explicação detalhada
# =====================================================

def explicar(cid, c, classificacao):
    print(f"\n{cid}")
    print(f"  → posição estrutural: {classificacao}")
    print(f"  - nível: {c['nivel']}")
    print(f"  - domínio: {c['dominio']}")

    est = c.get("estatuto_ontologico", {})
    print(f"  - afirmação ontológica: {est.get('afirmacao_ontologica')}")
    print(f"  - tipo ontológico: {est.get('tipo')}")

    deps = c.get("dependencias", {}).get("depende_de", [])
    if deps:
        print(f"  - depende de: {', '.join(deps)}")
    else:
        print("  - não depende de outros conceitos")

    fund, razao = e_fundacional(c)
    if fund:
        print("  ✅ estatuto ontológico real")
    else:
        print(f"  ❌ não fundacional: {razao}")

    if classificacao.startswith("V. ESTRUTURA_ONTOLOGICA_DERIVADA"):
        print("  ℹ️ ontologicamente real, mas estruturalmente derivado do núcleo")

    if classificacao.startswith("VI"):
        print("  ℹ️ não pertence ao núcleo nem a eixos normativos; é forma de manifestação ou mediação")

# =====================================================
# Execução
# =====================================================

if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")
    inverso = construir_inverso(conceitos)

    nucleo = extrair_nucleo_minimo(conceitos, inverso)
    transicao = extrair_transicao_antropologica(conceitos, inverso)
    eixo_ep = extrair_eixo_epistemologico(conceitos)
    eixo_et = extrair_eixo_etico(conceitos)

    print("\n=== EXPLICAÇÃO ESTRUTURAL COMPLETA DO SISTEMA ===")

    for cid, c in sorted(conceitos.items()):
        classificacao = classificar(
            cid, c, nucleo, transicao, eixo_ep, eixo_et
        )
        explicar(cid, c, classificacao)