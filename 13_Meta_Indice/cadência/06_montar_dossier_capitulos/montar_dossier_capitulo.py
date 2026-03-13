import json
from pathlib import Path
from collections import defaultdict


CAPITULO_ID_ALVO = "CAP_15_CONSCIENCIA"

BASE_DIR = Path(__file__).resolve().parent
PASTA_FONTE = BASE_DIR.parent / "05_priorizar_fragmentos_para_montagem"

FICHEIRO_ENTRADA = PASTA_FONTE / "fragmentos_prioridade_A.json"
FICHEIRO_SAIDA = BASE_DIR / f"dossier_{CAPITULO_ID_ALVO}.json"


def carregar_json(caminho: Path):
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def guardar_json(caminho: Path, dados):
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def normalizar_texto(valor, default=None):
    if valor is None:
        return default
    if isinstance(valor, str):
        valor = valor.strip()
        return valor if valor else default
    return valor


def normalizar_lista(valor):
    if isinstance(valor, list):
        return valor
    if valor is None:
        return []
    return [valor]


def score_fragmento(frag):
    score = 0

    grau = normalizar_texto(frag.get("grau_de_pertenca_ao_indice"))
    estado = normalizar_texto(frag.get("estado_argumentativo"))
    reconstruivel = bool(frag.get("argumento_reconstruivel"))
    reconstrucao_forte = bool(frag.get("necessita_reconstrucao_forte"))
    prioridade_aproveitamento = normalizar_texto(frag.get("prioridade_de_aproveitamento"))
    clareza = normalizar_texto(frag.get("clareza_atual"))
    estabilizacao = normalizar_texto(frag.get("grau_de_estabilizacao"))
    densidade = normalizar_texto(frag.get("densidade_filosofica"))

    if grau == "forte":
        score += 5
    elif grau == "provavel":
        score += 3

    if reconstruivel:
        score += 2

    if estado == "argumento_em_esboco":
        score += 2
    elif estado == "formulacao_pre_argumentativa":
        score += 1

    if prioridade_aproveitamento == "alta":
        score += 2
    elif prioridade_aproveitamento == "media":
        score += 1

    if clareza == "alta":
        score += 2
    elif clareza == "media":
        score += 1

    if estabilizacao == "alta":
        score += 2
    elif estabilizacao == "media":
        score += 1

    if densidade == "alta":
        score += 2
    elif densidade == "media":
        score += 1

    if reconstrucao_forte:
        score -= 2

    return score


def classificar_funcao_editorial(fragmento):
    texto = " ".join(
        [
            str(fragmento.get("trabalho_no_sistema") or ""),
            str(fragmento.get("trabalho_no_sistema_secundario") or ""),
            str(fragmento.get("descricao_funcional_curta") or ""),
            str(fragmento.get("explicacao_textual_do_que_o_fragmento_tenta_fazer") or ""),
            str(fragmento.get("problema_filosofico_central") or ""),
        ]
    ).lower()

    if any(x in texto for x in ["reinscrev", "situar", "localiz", "emerge", "corpo", "corporal"]):
        return "abertura_e_tese_base"

    if any(x in texto for x in ["criticar", "critica", "erro", "ilus", "autonom", "separ"]):
        return "critica_e_correcao"

    if any(x in texto for x in ["distingu", "diferen", "não é", "nao é", "limita", "delimita"]):
        return "distincao_e_delimitacao"

    if any(x in texto for x in ["transi", "ponte", "passagem", "prepara"]):
        return "ponte_de_transicao"

    if any(x in texto for x in ["aplica", "caso", "exemplo"]):
        return "aplicacao_ou_exemplo"

    estado = normalizar_texto(fragmento.get("estado_argumentativo"))
    if estado == "argumento_em_esboco":
        return "nucleo_argumentativo"

    return "material_de_apoio"


def classificar_aproveitamento(fragmento):
    score = score_fragmento(fragmento)
    reconstrucao_forte = bool(fragmento.get("necessita_reconstrucao_forte"))
    clareza = normalizar_texto(fragmento.get("clareza_atual"))
    estabilizacao = normalizar_texto(fragmento.get("grau_de_estabilizacao"))

    if score >= 12 and not reconstrucao_forte and clareza in ("alta", "media") and estabilizacao in ("alta", "media"):
        return "aproveitamento_quase_direto"

    if score >= 8:
        return "reconstrucao_leve"

    if score >= 5:
        return "reconstrucao_forte"

    return "apenas_apoio_lateral"


def filtrar_capitulo(fragmentos, capitulo_id):
    return [
        f for f in fragmentos
        if normalizar_texto(f.get("capitulo_id")) == capitulo_id
    ]


def construir_resumo_capitulo(fragmentos_capitulo, capitulo_id):
    capitulo_titulo = None
    parte_id = None

    for f in fragmentos_capitulo:
        if not capitulo_titulo and f.get("capitulo_titulo"):
            capitulo_titulo = f.get("capitulo_titulo")
        if not parte_id and f.get("parte_id"):
            parte_id = f.get("parte_id")

    return {
        "capitulo_id": capitulo_id,
        "capitulo_titulo": capitulo_titulo,
        "parte_id": parte_id,
        "total_fragmentos": len(fragmentos_capitulo),
        "fortes": sum(1 for f in fragmentos_capitulo if f.get("grau_de_pertenca_ao_indice") == "forte"),
        "provaveis": sum(1 for f in fragmentos_capitulo if f.get("grau_de_pertenca_ao_indice") == "provavel"),
        "reconstruiveis": sum(1 for f in fragmentos_capitulo if f.get("argumento_reconstruivel")),
        "argumentos_em_esboco": sum(1 for f in fragmentos_capitulo if f.get("estado_argumentativo") == "argumento_em_esboco"),
        "formulacoes_pre_argumentativas": sum(1 for f in fragmentos_capitulo if f.get("estado_argumentativo") == "formulacao_pre_argumentativa"),
    }


def construir_por_argumento(fragmentos_capitulo):
    grupos = defaultdict(list)

    for f in fragmentos_capitulo:
        argumento = normalizar_texto(
            f.get("argumento_canonico_relacionado"),
            "SEM_ARGUMENTO_CANONICO"
        )
        grupos[argumento].append(f)

    resultado = []

    for argumento, frags in grupos.items():
        lista = []
        for f in frags:
            item = {
                "fragment_id": f.get("fragment_id"),
                "origem_id": f.get("origem_id"),
                "ordem_no_ficheiro": f.get("ordem_no_ficheiro"),
                "grau_de_pertenca_ao_indice": f.get("grau_de_pertenca_ao_indice"),
                "estado_argumentativo": f.get("estado_argumentativo"),
                "argumento_reconstruivel": f.get("argumento_reconstruivel"),
                "necessita_reconstrucao_forte": f.get("necessita_reconstrucao_forte"),
                "descricao_funcional_curta": f.get("descricao_funcional_curta"),
                "explicacao_textual_do_que_o_fragmento_tenta_fazer": f.get("explicacao_textual_do_que_o_fragmento_tenta_fazer"),
                "premissa_central_reconstruida": f.get("premissa_central_reconstruida"),
                "conclusao_visada": f.get("conclusao_visada"),
                "aproveitamento_editorial": classificar_aproveitamento(f),
                "funcao_editorial_sugerida": classificar_funcao_editorial(f),
                "score_editorial": score_fragmento(f),
            }
            lista.append(item)

        lista.sort(
            key=lambda x: (
                -x["score_editorial"],
                0 if x["grau_de_pertenca_ao_indice"] == "forte" else 1,
                0 if x["argumento_reconstruivel"] else 1,
                x["ordem_no_ficheiro"] or 999999,
            )
        )

        resultado.append(
            {
                "argumento_canonico_relacionado": argumento,
                "total_fragmentos": len(lista),
                "score_total_argumento": sum(x["score_editorial"] for x in lista),
                "fragmentos": lista,
            }
        )

    resultado.sort(
        key=lambda x: (-x["score_total_argumento"], -x["total_fragmentos"], x["argumento_canonico_relacionado"])
    )

    return resultado


def construir_por_funcao_editorial(fragmentos_capitulo):
    grupos = defaultdict(list)

    for f in fragmentos_capitulo:
        funcao = classificar_funcao_editorial(f)
        grupos[funcao].append(f)

    ordem_funcoes = [
        "abertura_e_tese_base",
        "nucleo_argumentativo",
        "distincao_e_delimitacao",
        "critica_e_correcao",
        "aplicacao_ou_exemplo",
        "ponte_de_transicao",
        "material_de_apoio",
    ]

    resultado = []

    for funcao in ordem_funcoes:
        frags = grupos.get(funcao, [])
        lista = []

        for f in frags:
            item = {
                "fragment_id": f.get("fragment_id"),
                "origem_id": f.get("origem_id"),
                "ordem_no_ficheiro": f.get("ordem_no_ficheiro"),
                "argumento_canonico_relacionado": f.get("argumento_canonico_relacionado"),
                "grau_de_pertenca_ao_indice": f.get("grau_de_pertenca_ao_indice"),
                "estado_argumentativo": f.get("estado_argumentativo"),
                "descricao_funcional_curta": f.get("descricao_funcional_curta"),
                "explicacao_textual_do_que_o_fragmento_tenta_fazer": f.get("explicacao_textual_do_que_o_fragmento_tenta_fazer"),
                "aproveitamento_editorial": classificar_aproveitamento(f),
                "score_editorial": score_fragmento(f),
            }
            lista.append(item)

        lista.sort(
            key=lambda x: (
                -x["score_editorial"],
                0 if x["grau_de_pertenca_ao_indice"] == "forte" else 1,
                x["ordem_no_ficheiro"] or 999999,
            )
        )

        resultado.append(
            {
                "funcao_editorial": funcao,
                "total_fragmentos": len(lista),
                "fragmentos": lista,
            }
        )

    return resultado


def construir_fragmentos_ordenados(fragmentos_capitulo):
    lista = []

    for f in fragmentos_capitulo:
        item = {
            "fragment_id": f.get("fragment_id"),
            "origem_id": f.get("origem_id"),
            "ordem_no_ficheiro": f.get("ordem_no_ficheiro"),
            "argumento_canonico_relacionado": f.get("argumento_canonico_relacionado"),
            "funcao_editorial_sugerida": classificar_funcao_editorial(f),
            "aproveitamento_editorial": classificar_aproveitamento(f),
            "grau_de_pertenca_ao_indice": f.get("grau_de_pertenca_ao_indice"),
            "estado_argumentativo": f.get("estado_argumentativo"),
            "descricao_funcional_curta": f.get("descricao_funcional_curta"),
            "explicacao_textual_do_que_o_fragmento_tenta_fazer": f.get("explicacao_textual_do_que_o_fragmento_tenta_fazer"),
            "premissa_central_reconstruida": f.get("premissa_central_reconstruida"),
            "conclusao_visada": f.get("conclusao_visada"),
            "score_editorial": score_fragmento(f),
        }
        lista.append(item)

    lista.sort(
        key=lambda x: (
            0 if x["aproveitamento_editorial"] == "aproveitamento_quase_direto" else
            1 if x["aproveitamento_editorial"] == "reconstrucao_leve" else
            2 if x["aproveitamento_editorial"] == "reconstrucao_forte" else
            3,
            -x["score_editorial"],
            0 if x["grau_de_pertenca_ao_indice"] == "forte" else 1,
            x["ordem_no_ficheiro"] or 999999,
        )
    )

    return lista


def construir_sugestao_estrutura(fragmentos_capitulo):
    por_funcao = defaultdict(list)

    for f in fragmentos_capitulo:
        funcao = classificar_funcao_editorial(f)
        por_funcao[funcao].append(
            {
                "fragment_id": f.get("fragment_id"),
                "descricao_funcional_curta": f.get("descricao_funcional_curta"),
                "score_editorial": score_fragmento(f),
                "argumento_canonico_relacionado": f.get("argumento_canonico_relacionado"),
            }
        )

    for funcao in por_funcao:
        por_funcao[funcao].sort(key=lambda x: -x["score_editorial"])

    return {
        "abertura_sugerida": por_funcao.get("abertura_e_tese_base", [])[:3],
        "nucleo_argumentativo_sugerido": por_funcao.get("nucleo_argumentativo", [])[:6],
        "distincoes_e_delimitacoes": por_funcao.get("distincao_e_delimitacao", [])[:5],
        "criticas_e_correcoes": por_funcao.get("critica_e_correcao", [])[:5],
        "aplicacoes_ou_exemplos": por_funcao.get("aplicacao_ou_exemplo", [])[:4],
        "pontes_de_transicao": por_funcao.get("ponte_de_transicao", [])[:4],
    }


def construir_diagnostico_editorial(fragmentos_capitulo):
    diag = defaultdict(int)

    for f in fragmentos_capitulo:
        diag[classificar_aproveitamento(f)] += 1

    return {
        "aproveitamento_quase_direto": diag["aproveitamento_quase_direto"],
        "reconstrucao_leve": diag["reconstrucao_leve"],
        "reconstrucao_forte": diag["reconstrucao_forte"],
        "apenas_apoio_lateral": diag["apenas_apoio_lateral"],
    }


def imprimir_resumo(dossier):
    resumo = dossier["resumo_capitulo"]
    print("=" * 90)
    print("DOSSIER DE CAPÍTULO")
    print("=" * 90)
    print(f"Capítulo: {resumo['capitulo_id']} | {resumo['capitulo_titulo']}")
    print(f"Parte: {resumo['parte_id']}")
    print(f"Total de fragmentos: {resumo['total_fragmentos']}")
    print(f"Fortes: {resumo['fortes']} | Prováveis: {resumo['provaveis']} | Reconstruíveis: {resumo['reconstruiveis']}")
    print("-" * 90)

    print("Diagnóstico editorial:")
    for k, v in dossier["diagnostico_editorial"].items():
        print(f"- {k}: {v}")

    print("-" * 90)
    print("Argumentos canónicos presentes:")
    for item in dossier["por_argumento_canonico"][:10]:
        print(
            f"- {item['argumento_canonico_relacionado']}: "
            f"{item['total_fragmentos']} fragmentos | score={item['score_total_argumento']}"
        )

    print("-" * 90)
    print("Ficheiro gerado:")
    print(f"- {FICHEIRO_SAIDA}")
    print("=" * 90)


def main():
    if not FICHEIRO_ENTRADA.exists():
        raise FileNotFoundError(f"Não encontrei o ficheiro de entrada: {FICHEIRO_ENTRADA}")

    fragmentos = carregar_json(FICHEIRO_ENTRADA)

    if not isinstance(fragmentos, list):
        raise ValueError("O ficheiro de entrada tem de conter uma lista.")

    fragmentos_capitulo = filtrar_capitulo(fragmentos, CAPITULO_ID_ALVO)

    if not fragmentos_capitulo:
        raise ValueError(f"Não encontrei fragmentos para o capítulo {CAPITULO_ID_ALVO}.")

    dossier = {
        "resumo_capitulo": construir_resumo_capitulo(fragmentos_capitulo, CAPITULO_ID_ALVO),
        "diagnostico_editorial": construir_diagnostico_editorial(fragmentos_capitulo),
        "sugestao_de_estrutura_interna": construir_sugestao_estrutura(fragmentos_capitulo),
        "por_argumento_canonico": construir_por_argumento(fragmentos_capitulo),
        "por_funcao_editorial": construir_por_funcao_editorial(fragmentos_capitulo),
        "fragmentos_ordenados_para_trabalho": construir_fragmentos_ordenados(fragmentos_capitulo),
    }

    guardar_json(FICHEIRO_SAIDA, dossier)
    imprimir_resumo(dossier)


if __name__ == "__main__":
    main()