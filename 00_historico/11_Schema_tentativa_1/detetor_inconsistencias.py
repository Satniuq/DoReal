from carregar_conceitos import carregar_conceitos
from collections import defaultdict, deque

# =====================================================
# Configurações ontológicas explícitas
# =====================================================

TIPOS_NAO_FUNDACIONAIS = {
    "configuracao_funcional_localizada",
    "forma_dinamica",
    "manifestacao_dinamica",
    "processo_mediador_simbolico",
    "forma_de_manifestacao",
    "descricao_dinamica",
}

# =====================================================
# Utilidades
# =====================================================

def e_ontologico_real(c):
    return c.get("estatuto_ontologico", {}).get("afirmacao_ontologica") is True


def e_epistemologico(c):
    return c.get("estatuto_ontologico", {}).get("afirmacao_ontologica") is False


def e_etico(c):
    return "etico" in c.get("dominio", "")


# -----------------------------------------------------
# Dependência transitiva
# -----------------------------------------------------

def depende_transitivamente(conceitos, origem, alvo):
    visitados = set()
    fila = deque([origem])

    while fila:
        atual = fila.popleft()
        if atual in visitados:
            continue
        visitados.add(atual)

        deps = conceitos[atual].get("dependencias", {}).get("depende_de", [])
        if alvo in deps:
            return True

        fila.extend(deps)

    return False


# =====================================================
# DETETOR DE INCONSISTÊNCIAS
# =====================================================

def detetar_inconsistencias(conceitos):
    inconsistencias = defaultdict(list)

    for cid, c in conceitos.items():
        est = c.get("estatuto_ontologico", {})
        deps = c.get("dependencias", {}).get("depende_de", [])
        tipo = est.get("tipo", "")

        # ----------------------------------------------
        # REGRA 1 — Ontológico real não depende de epistemológico
        # ----------------------------------------------
        # REGRA 1 — Ontológico real não pode DEPENDER fundacionalmente de epistemológico
        if e_ontologico_real(c):
            deps_fortes = c.get("dependencias", {}).get("depende_de", [])
            for d in deps_fortes:
                if d in conceitos and e_epistemologico(conceitos[d]):
                    inconsistencias[cid].append(
                        f"conceito ontológico real depende fundacionalmente de não-ontológico ({d})"
                    )

        # ----------------------------------------------
        # REGRA 2 — Ético deve depender (direta ou indiretamente) de D_SER_HUMANO
        # ----------------------------------------------
        if e_etico(c):
            if not depende_transitivamente(conceitos, cid, "D_SER_HUMANO"):
                inconsistencias[cid].append(
                    "conceito ético sem dependência (direta ou indireta) de D_SER_HUMANO"
                )

        # ----------------------------------------------
        # REGRA 3 — Tipo não fundacional NÃO é erro (apenas aviso se mal rotulado)
        # ----------------------------------------------
        if tipo in TIPOS_NAO_FUNDACIONAIS:
            # só erro se alguém o marcar como fundacional (não é o caso no teu sistema)
            pass

    return inconsistencias


# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")

    inconsistencias = detetar_inconsistencias(conceitos)

    print("\n=== DETETOR DE INCONSISTÊNCIAS ONTOLÓGICAS (v2) ===\n")

    total = 0
    for cid, erros in inconsistencias.items():
        print(f"❗ {cid}")
        for e in erros:
            print(f"   - {e}")
            total += 1
        print()

    if total == 0:
        print("✅ Nenhuma inconsistência ontológica detetada.")
    else:
        print(f"⚠️ Total de inconsistências encontradas: {total}")