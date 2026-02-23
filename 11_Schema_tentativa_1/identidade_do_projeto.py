from carregar_conceitos import carregar_conceitos
from collections import defaultdict

# ============================================================
# IDENTIDADE DO PROJETO
# ------------------------------------------------------------
# Este script NÃO descreve o real nem os seus percursos.
#
# Ele extrai a ESPINHA ESTRUTURAL que identifica o projeto:
#   - núcleo ontológico fundacional
#   - eixo emergente (dinâmico)
#   - transição ontológica para a antropologia
#   - eixos epistemológico e ético
#
# Tudo o que aqui sai é estrutural, não narrativo.
# ============================================================


# ------------------------------------------------------------
# Construção do grafo ontológico
# ------------------------------------------------------------
# grafo   : pai -> filhos
# inverso : filho -> pais
# ------------------------------------------------------------

def construir_grafo(conceitos):
    grafo = defaultdict(list)
    inverso = defaultdict(list)

    for cid, c in conceitos.items():
        for dep in c.get("dependencias", {}).get("depende_de", []):
            grafo[dep].append(cid)
            inverso[cid].append(dep)

    return grafo, inverso


# ------------------------------------------------------------
# Profundidade ontológica fundacional
# ------------------------------------------------------------
# Mede "quão fundacional" é um conceito relativamente
# a outros considerados válidos.
# ------------------------------------------------------------

def profundidade(cid, inverso, validos, memo):
    if cid in memo:
        return memo[cid]

    pais = [p for p in inverso.get(cid, []) if p in validos]

    if not pais:
        memo[cid] = 0
    else:
        memo[cid] = 1 + max(
            profundidade(p, inverso, validos, memo)
            for p in pais
        )

    return memo[cid]


# ------------------------------------------------------------
# Critério ontológico de fundacionalidade
# ------------------------------------------------------------
# Um conceito é fundacional se:
#   - afirma ontologia
#   - NÃO é mera manifestação ou forma dinâmica
# ------------------------------------------------------------

TIPOS_NAO_FUNDACIONAIS = {
    "configuracao_funcional_localizada",  # D_CIRCULO
    "forma_dinamica",                     # D_CONTINUO
    "manifestacao_dinamica",              # D_MOVIMENTO
    "forma_de_manifestacao",
    "manifestacao_fenomenologica",
    "descricao_dinamica",
}


def e_fundacional(c):
    est = c.get("estatuto_ontologico", {})

    if est.get("afirmacao_ontologica") is not True:
        return False

    tipo = est.get("tipo", "").strip()
    if tipo in TIPOS_NAO_FUNDACIONAIS:
        return False

    return True


# ------------------------------------------------------------
# Núcleo ontológico do real (fundacional)
# ------------------------------------------------------------
# Extrai a cadeia estrutural mais profunda
# até um certo nível ontológico.
# ------------------------------------------------------------

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
        atual = max(pais, key=lambda p: profundidades[p])

    return list(reversed(eixo))


# ------------------------------------------------------------
# Eixo emergente (processual / dinâmico)
# ------------------------------------------------------------
# NÃO é fundacional.
# Capta processos, condições dinâmicas e emergências.
# ------------------------------------------------------------

TIPOS_EMERGENTES = {
    "processo_real",
    "condicao_dinamica",
    "manifestacao_dinamica",
    "forma_dinamica",
    "configuracao_relacional",
    "capacidade_reflexiva_localizada",
    "processo_mediador_simbolico",
    "relacao_reflexiva_localizada",
}


def extrair_eixo_emergente(conceitos):
    return sorted(
        cid for cid, c in conceitos.items()
        if c.get("estatuto_ontologico", {}).get("tipo") in TIPOS_EMERGENTES
    )


# ------------------------------------------------------------
# Transição ontológica para a antropologia
# ------------------------------------------------------------
# Reconstrói a transição até D_REAL,
# escolhendo SEMPRE o pai ontologicamente mais profundo.
# ------------------------------------------------------------

def extrair_transicao_antropologica(conceitos, inverso):
    if "D_SER_HUMANO" not in conceitos:
        return []

    caminho = ["D_SER_HUMANO"]
    atual = "D_SER_HUMANO"

    while atual != "D_REAL":
        pais = inverso.get(atual, [])
        if not pais:
            break

        # escolhe o pai mais fundacional:
        atual = min(
            pais,
            key=lambda p: (
                conceitos[p]["nivel"],
                p
            )
        )

        caminho.append(atual)

    return list(reversed(caminho))


# ------------------------------------------------------------
# Eixo epistemológico
# ------------------------------------------------------------

def extrair_eixo_epistemologico(conceitos):
    return sorted(
        cid for cid, c in conceitos.items()
        if "epistemologico" in c["dominio"]
    )


# ------------------------------------------------------------
# Eixo ético
# ------------------------------------------------------------

def extrair_eixo_etico(conceitos):
    return sorted(
        cid for cid, c in conceitos.items()
        if "etico" in c["dominio"]
    )


# ============================================================
# Execução principal
# ============================================================

if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")
    grafo, inverso = construir_grafo(conceitos)

    nucleo = extrair_nucleo_ontologico(conceitos, inverso, nivel_max=2)
    emergente = extrair_eixo_emergente(conceitos)
    transicao = extrair_transicao_antropologica(conceitos, inverso)
    eixo_ep = extrair_eixo_epistemologico(conceitos)
    eixo_et = extrair_eixo_etico(conceitos)

    print("\n=== I. NÚCLEO ONTOLÓGICO DO REAL (FUNDACIONAL) ===\n")
    for c in nucleo:
        print(c)

    print("\n=== II. EIXO EMERGENTE (DINÂMICO) ===\n")
    for c in emergente:
        print(c)

    print("\n=== III. TRANSIÇÃO PARA ANTROPOLOGIA ONTOLÓGICA ===\n")
    for c in transicao:
        print(c)

    print("\n=== IV. EIXO EPISTEMOLÓGICO ===\n")
    for c in eixo_ep:
        print(c)

    print("\n=== V. EIXO ÉTICO ===\n")
    for c in eixo_et:
        print(c)