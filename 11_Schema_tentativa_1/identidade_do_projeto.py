from carregar_conceitos import carregar_conceitos
from collections import defaultdict


# -----------------------------
# Construção do grafo ontológico
# -----------------------------

def construir_grafo(conceitos):
    grafo = defaultdict(list)
    inverso = defaultdict(list)

    for cid, c in conceitos.items():
        for dep in c.get("dependencias", {}).get("depende_de", []):
            grafo[dep].append(cid)
            inverso[cid].append(dep)

    return grafo, inverso


# ------------------------------------
# Profundidade ontológica (fundacional)
# ------------------------------------

def profundidade(cid, inverso, validos, memo):
    if cid in memo:
        return memo[cid]

    pais = [p for p in inverso.get(cid, []) if p in validos]
    if not pais:
        memo[cid] = 0
    else:
        memo[cid] = 1 + max(profundidade(p, inverso, validos, memo) for p in pais)

    return memo[cid]


# ------------------------------------
# Critério ontológico fundacional (PRECISO)
# ------------------------------------

TIPOS_NAO_FUNDACIONAIS = {
    # já confirmados no teu sistema
    "configuracao_funcional_localizada",  # D_CIRCULO
    "forma_dinamica",                     # D_CONTINUO
    "manifestacao_dinamica",              # D_MOVIMENTO

    # reservas para evolução futura (se vierem a existir)
    "forma_de_manifestacao",
    "manifestacao_fenomenologica",
    "descricao_dinamica",
}


def e_fundacional(c):
    est = c.get("estatuto_ontologico", {})

    # tem de afirmar ontologia
    if est.get("afirmacao_ontologica") is not True:
        return False

    tipo = est.get("tipo", "").strip()
    if tipo in TIPOS_NAO_FUNDACIONAIS:
        return False

    return True


# ------------------------------------
# Núcleo ontológico do real
# ------------------------------------

def extrair_nucleo_ontologico(conceitos, inverso, nivel_max=2):
    nucleares = {
        cid for cid, c in conceitos.items()
        if c["nivel"] <= nivel_max and e_fundacional(c)
    }

    memo = {}
    profundidades = {
        cid: profundidade(cid, inverso, nucleares, memo)
        for cid in nucleares
    }

    fim = max(profundidades, key=lambda k: profundidades[k])

    eixo = []
    atual = fim
    while True:
        eixo.append(atual)
        pais = [p for p in inverso.get(atual, []) if p in nucleares]
        if not pais:
            break
        atual = max(pais, key=lambda k: profundidades[k])

    return list(reversed(eixo))


# ------------------------------------
# Transição para antropologia ontológica
# ------------------------------------

def extrair_transicao_antropologica(conceitos, inverso):
    if "D_SER_HUMANO" not in conceitos:
        return []

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

    return list(reversed(caminho))


# ------------------------------------
# Eixo epistemológico
# ------------------------------------

def extrair_eixo_epistemologico(conceitos):
    return sorted(
        cid for cid, c in conceitos.items()
        if "epistemologico" in c["dominio"]
    )


# ------------------------------------
# Eixo ético
# ------------------------------------

def extrair_eixo_etico(conceitos):
    return sorted(
        cid for cid, c in conceitos.items()
        if "etico" in c["dominio"]
    )


# ------------------------------------
# Execução principal
# ------------------------------------

if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")
    grafo, inverso = construir_grafo(conceitos)

    nucleo = extrair_nucleo_ontologico(conceitos, inverso, nivel_max=2)
    transicao = extrair_transicao_antropologica(conceitos, inverso)
    eixo_ep = extrair_eixo_epistemologico(conceitos)
    eixo_et = extrair_eixo_etico(conceitos)

    print("\n=== I. NÚCLEO ONTOLÓGICO DO REAL ===\n")
    for c in nucleo:
        print(c)

    print("\n=== II. TRANSIÇÃO PARA ANTROPOLOGIA ONTOLÓGICA ===\n")
    for c in transicao:
        print(c)

    print("\n=== III. EIXO EPISTEMOLÓGICO ===\n")
    for c in eixo_ep:
        print(c)

    print("\n=== IV. EIXO ÉTICO ===\n")
    for c in eixo_et:
        print(c)