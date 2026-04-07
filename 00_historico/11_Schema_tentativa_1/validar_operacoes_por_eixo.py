from carregar_conceitos import carregar_conceitos
import json


# ==== EIXOS ====

EIXOS = {
    "ontologico_nuclear": {
        "D_DISTINCAO", "D_RELACIONALIDADE_MINIMA", "D_ESTRUTURA",
        "D_DETERMINACAO", "D_NAO_SER", "D_LIMITE",
        "D_PODER_SER", "D_REAL", "D_SER",
        "D_POTENCIALIDADE", "D_ATUALIZACAO",
        "D_CONTINUIDADE", "D_REGULARIDADE",
        "D_ESCALA_ONTOLOGICA"
    },

    "transicao_antropologica": {
        "D_SER_HUMANO", "D_LOCALIDADE", "D_CAMPO_DE_POTENCIALIDADES"
    },

    "epistemologico": {
        "D_APREENSAO", "D_REPRESENTACAO",
        "D_ADEQUACAO", "D_VERDADE",
        "D_ERRO", "D_CRITERIO"
    },

    "etico": {
        "D_RESPONSABILIDADE_ONTOLOGICA",
        "D_BEM", "D_MAL", "D_DEVER_SER"
    },

    "sistemico": {
        "D_SISTEMA", "D_SISTEMA_SIMBOLICO",
        "D_CULTURA", "D_INSTITUICAO",
        "D_DIREITO_COMO_DESCRICAO",
        "D_TECNOLOGIA", "D_IMAGINACAO"
    }
}


OPERACOES_PERMITIDAS_POR_EIXO = {
    "ontologico_nuclear": {
        "inscricao_no_real",
        "descricao_estrutural",
        "diferenciacao_ontologica"
    },

    "transicao_antropologica": {
        "inscricao_no_real",
        "descricao_estrutural",
        "diferenciacao_ontologica",
        "critica_reflexividade"
    },

    "epistemologico": {
        "descricao_estrutural",
        "diferenciacao_ontologica",
        "critica_reflexividade",
        "epistemologica",
        "critica_sistemica"
    },

    "etico": {
        "descricao_estrutural",
        "epistemologica",
        "etico_ontologica",
        "corretiva"
    },

    "sistemico": {
        "descricao_estrutural",
        "diferenciacao_ontologica",
        "critica_reflexividade",
        "epistemologica",
        "critica_sistemica",
        "corretiva"
    }
}


def identificar_eixo(conceito_id):
    for eixo, conceitos in EIXOS.items():
        if conceito_id in conceitos:
            return eixo
    return "eixo_desconhecido"


def validar_operacoes_por_eixo(conceitos, operacoes):
    erros = []
    avisos = []

    for cid, c in conceitos.items():
        eixo = identificar_eixo(cid)
        ops = c.get("operacoes_ontologicas", {})

        if eixo == "eixo_desconhecido":
            avisos.append(f"{cid}: eixo não identificado")
            continue

        tipos_permitidos = OPERACOES_PERMITIDAS_POR_EIXO[eixo]

        for bloco in ops.values():
            for op in bloco:
                tipo = operacoes[op]["tipo"]
                if tipo not in tipos_permitidos:
                    erros.append(
                        f"{cid} ({eixo}) usa operação '{op}' "
                        f"do tipo '{tipo}' não permitido neste eixo"
                    )

    return erros, avisos


if __name__ == "__main__":
    conceitos = carregar_conceitos("conceitos")

    with open("operacoes/operacoes.json", encoding="utf-8") as f:
        operacoes = json.load(f)

    erros, avisos = validar_operacoes_por_eixo(conceitos, operacoes)

    print(f"Erros por eixo: {len(erros)}")
    for e in erros:
        print("ERRO:", e)

    print(f"\nAvisos por eixo: {len(avisos)}")
    for a in avisos:
        print("AVISO:", a)
