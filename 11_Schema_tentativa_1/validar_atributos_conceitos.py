from carregar_conceitos import carregar_conceitos


# conceitos a partir dos quais exigimos densidade semântica
NIVEL_CRITICO = 3


def validar_atributos(cid, c):
    avisos = []

    nivel = c["nivel"]

    # --- 1. Trivialidade perigosa ---
    if nivel >= NIVEL_CRITICO:
        for bloco in ["notas_de_protecao", "epistemologia"]:
            if bloco in c:
                for k, v in c[bloco].items():
                    if isinstance(v, list) and len(v) == 0:
                        avisos.append(
                            f"{cid}: '{bloco}.{k}' vazio em conceito de nível {nivel}"
                        )

    # --- 2. Coerência operação ↔ estatuto ---
    ops = c.get("operacoes_ontologicas", {})
    estatuto = c.get("estatuto_ontologico", {})

    if estatuto.get("afirmacao_ontologica") is False:
        for bloco in ops.values():
            if "OP_AFIRMACAO_ESTRUTURAL" in bloco:
                avisos.append(
                    f"{cid}: afirmação ontológica falsa mas usa OP_AFIRMACAO_ESTRUTURAL"
                )

    # --- 3. Epistemologia mínima ---
    if "ERRO" in cid and not c["epistemologia"].get("condicoes_de_erro"):
        avisos.append(f"{cid}: conceito de erro sem condicoes_de_erro")

    if "VERDADE" in cid and not c["notas_de_protecao"]["riscos_de_desvio"]:
        avisos.append(f"{cid}: verdade sem riscos de desvio explícitos")

    # --- 4. Ética sem protecção ---
    if c["nivel"] >= 5:
        if not c["notas_de_protecao"]["riscos_de_desvio"]:
            avisos.append(
                f"{cid}: conceito ético sem riscos de desvio"
            )

    return avisos


if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")

    avisos_totais = []

    for cid, c in conceitos.items():
        avisos = validar_atributos(cid, c)
        avisos_totais.extend(avisos)

    print(f"Avisos semânticos: {len(avisos_totais)}")
    for a in avisos_totais:
        print("AVISO:", a)