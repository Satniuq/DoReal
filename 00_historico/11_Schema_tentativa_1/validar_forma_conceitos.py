from carregar_conceitos import carregar_conceitos


CAMPOS_TOPO = {
    "id": str,
    "nome": str,
    "nivel": (int, float),
    "dominio": str,
    "definicao": dict,
    "estatuto_ontologico": dict,
    "dependencias": dict,
    "operacoes_ontologicas": dict,
    "dinamica": dict,
    "epistemologia": dict,
    "notas_de_protecao": dict
}

SUBCAMPOS = {
    "definicao": {
        "texto": str,
        "linguagem": str,
        "nao_metaforica": bool
    },
    "dependencias": {
        "depende_de": list,
        "pressupoe": list,
        "implica": list
    },
    "operacoes_ontologicas": {
        "fundacao": list,
        "descricao": list,
        "diferenciacao": list,
        "critica": list,
        "corretiva": list
    },
    "dinamica": {
        "gera": list,
        "pode_gerar_erro": list,
        "pode_ser_afetado_por": list
    },
    "epistemologia": {
        "estado_epistemico_padrao": str,
        "criterio_de_validacao": str,
        "condicoes_de_erro": list
    },
    "notas_de_protecao": {
        "riscos_de_desvio": list,
        "leituras_a_evitar": list,
        "operacoes_de_reintegracao": list
    }
}


def validar_forma_conceito(cid, c):
    erros = []
    avisos = []

    # 1. Campos de topo
    for campo, tipo in CAMPOS_TOPO.items():
        if campo not in c:
            erros.append(f"{cid}: campo obrigatório em falta → '{campo}'")
        elif not isinstance(c[campo], tipo):
            erros.append(
                f"{cid}: campo '{campo}' tem tipo inválido "
                f"(esperado {tipo}, encontrado {type(c[campo])})"
            )

    # 2. Subcampos
    for bloco, campos in SUBCAMPOS.items():
        if bloco not in c:
            continue

        for subcampo, tipo in campos.items():
            if subcampo not in c[bloco]:
                avisos.append(f"{cid}: subcampo '{bloco}.{subcampo}' em falta")
            elif not isinstance(c[bloco][subcampo], tipo):
                erros.append(
                    f"{cid}: subcampo '{bloco}.{subcampo}' com tipo inválido "
                    f"(esperado {tipo}, encontrado {type(c[bloco][subcampo])})"
                )

    # 3. Campos vazios suspeitos
    for bloco in ["definicao", "estatuto_ontologico"]:
        if bloco in c and not c[bloco]:
            avisos.append(f"{cid}: bloco '{bloco}' está vazio")

    return erros, avisos


if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")

    erros_totais = []
    avisos_totais = []

    for cid, c in conceitos.items():
        erros, avisos = validar_forma_conceito(cid, c)
        erros_totais.extend(erros)
        avisos_totais.extend(avisos)

    print(f"Erros de forma: {len(erros_totais)}")
    for e in erros_totais:
        print("ERRO:", e)

    print(f"\nAvisos de forma: {len(avisos_totais)}")
    for a in avisos_totais[:20]:
        print("AVISO:", a)