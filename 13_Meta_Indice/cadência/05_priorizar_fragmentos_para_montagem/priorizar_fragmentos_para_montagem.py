import json
from pathlib import Path


NOME_FICHEIRO_ENTRADA = "tratamento_filosofico_fragmentos.json"
NOME_FICHEIRO_SAIDA_PRIORIDADE_A = "fragmentos_prioridade_A.json"
NOME_FICHEIRO_SAIDA_MAPA_CAPITULO = "mapa_por_capitulo.json"
NOME_FICHEIRO_SAIDA_TOP_CAPITULOS = "top_capitulos_para_montagem.json"


def carregar_json(caminho: Path):
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def guardar_json(caminho: Path, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
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


def extrair_bloco(item):
    return item.get("tratamento_filosofico_fragmento", {}) or {}


def extrair_posicao(bloco):
    return bloco.get("posicao_no_indice", {}) or {}


def extrair_potencial(bloco):
    return bloco.get("potencial_argumentativo", {}) or {}


def extrair_destino(bloco):
    return bloco.get("destino_editorial", {}) or {}


def extrair_avaliacao(bloco):
    return bloco.get("avaliacao_global", {}) or {}


def e_prioridade_a(item):
    bloco = extrair_bloco(item)
    pos = extrair_posicao(bloco)
    pot = extrair_potencial(bloco)

    grau = normalizar_texto(pos.get("grau_de_pertenca_ao_indice"))
    reconstruivel = bool(pot.get("argumento_reconstruivel"))

    if grau == "forte":
        return True

    if grau == "provavel" and reconstruivel:
        return True

    return False


def calcular_score_prioridade_capitulo(item):
    bloco = extrair_bloco(item)
    pos = extrair_posicao(bloco)
    pot = extrair_potencial(bloco)

    score = 0

    grau = normalizar_texto(pos.get("grau_de_pertenca_ao_indice"))
    estado_argumentativo = normalizar_texto(pot.get("estado_argumentativo"))
    argumento_reconstruivel = bool(pot.get("argumento_reconstruivel"))

    if grau == "forte":
        score += 4
    elif grau == "provavel":
        score += 2

    if argumento_reconstruivel:
        score += 2

    if estado_argumentativo == "argumento_em_esboco":
        score += 1

    return score


def resumo_fragmento(item):
    bloco = extrair_bloco(item)
    pos = extrair_posicao(bloco)
    pot = extrair_potencial(bloco)
    destino = extrair_destino(bloco)
    avaliacao = extrair_avaliacao(bloco)

    return {
        "fragment_id": item.get("fragment_id"),
        "origem_id": item.get("origem_id"),
        "ordem_no_ficheiro": item.get("ordem_no_ficheiro"),
        "trabalho_no_sistema": bloco.get("trabalho_no_sistema"),
        "trabalho_no_sistema_secundario": bloco.get("trabalho_no_sistema_secundario"),
        "descricao_funcional_curta": bloco.get("descricao_funcional_curta"),
        "explicacao_textual_do_que_o_fragmento_tenta_fazer": bloco.get(
            "explicacao_textual_do_que_o_fragmento_tenta_fazer"
        ),
        "problema_filosofico_central": bloco.get("problema_filosofico_central"),
        "problemas_filosoficos_associados": normalizar_lista(
            bloco.get("problemas_filosoficos_associados")
        ),
        "parte_id": pos.get("parte_id"),
        "capitulo_id": pos.get("capitulo_id"),
        "capitulo_titulo": pos.get("capitulo_titulo"),
        "subcapitulo_ou_zona_interna": pos.get("subcapitulo_ou_zona_interna"),
        "argumento_canonico_relacionado": pos.get("argumento_canonico_relacionado"),
        "argumentos_canonicos_associados": normalizar_lista(
            pos.get("argumentos_canonicos_associados")
        ),
        "grau_de_pertenca_ao_indice": pos.get("grau_de_pertenca_ao_indice"),
        "modo_de_pertenca": pos.get("modo_de_pertenca"),
        "justificacao_de_posicao_no_indice": pos.get("justificacao_de_posicao_no_indice"),
        "estado_argumentativo": pot.get("estado_argumentativo"),
        "argumento_reconstruivel": pot.get("argumento_reconstruivel"),
        "necessita_reconstrucao_forte": pot.get("necessita_reconstrucao_forte"),
        "forca_logica_estimada": pot.get("forca_logica_estimada"),
        "premissa_central_reconstruida": pot.get("premissa_central_reconstruida"),
        "conclusao_visada": pot.get("conclusao_visada"),
        "destino_editorial_fino": destino.get("destino_editorial_fino"),
        "papel_editorial_primario": destino.get("papel_editorial_primario"),
        "papel_editorial_secundario": destino.get("papel_editorial_secundario"),
        "prioridade_de_revisao": destino.get("prioridade_de_revisao"),
        "prioridade_de_aproveitamento": destino.get("prioridade_de_aproveitamento"),
        "requer_reescrita": destino.get("requer_reescrita"),
        "requer_densificacao": destino.get("requer_densificacao"),
        "requer_formalizacao_logica": destino.get("requer_formalizacao_logica"),
        "densidade_filosofica": avaliacao.get("densidade_filosofica"),
        "clareza_atual": avaliacao.get("clareza_atual"),
        "grau_de_estabilizacao": avaliacao.get("grau_de_estabilizacao"),
        "risco_de_ma_interpretacao": avaliacao.get("risco_de_ma_interpretacao"),
        "confianca_tratamento_filosofico": avaliacao.get("confianca_tratamento_filosofico"),
    }


def construir_fragmentos_prioridade_a(fragmentos):
    prioridade = [resumo_fragmento(item) for item in fragmentos if e_prioridade_a(item)]

    prioridade.sort(
        key=lambda x: (
            0 if x.get("grau_de_pertenca_ao_indice") == "forte" else 1,
            0 if x.get("argumento_reconstruivel") else 1,
            0 if x.get("estado_argumentativo") == "argumento_em_esboco" else 1,
            x.get("capitulo_id") or "ZZZ",
            x.get("ordem_no_ficheiro") or 999999,
        )
    )
    return prioridade


def construir_mapa_por_capitulo(fragmentos):
    grupos = {}

    for item in fragmentos:
        bloco = extrair_bloco(item)
        pos = extrair_posicao(bloco)
        pot = extrair_potencial(bloco)

        parte_id = normalizar_texto(pos.get("parte_id"), "SEM_PARTE")
        capitulo_id = normalizar_texto(pos.get("capitulo_id"), "SEM_CAPITULO")
        capitulo_titulo = normalizar_texto(pos.get("capitulo_titulo"), "Sem capítulo atribuído")
        argumento = normalizar_texto(
            pos.get("argumento_canonico_relacionado"), "SEM_ARGUMENTO_CANONICO"
        )

        chave = (parte_id, capitulo_id, capitulo_titulo, argumento)

        if chave not in grupos:
            grupos[chave] = {
                "parte_id": parte_id,
                "capitulo_id": capitulo_id,
                "capitulo_titulo": capitulo_titulo,
                "argumento_canonico_relacionado": argumento,
                "total_fragmentos": 0,
                "fortes": 0,
                "provaveis": 0,
                "fracos": 0,
                "indefinidos": 0,
                "reconstruiveis": 0,
                "argumentos_em_esboco": 0,
                "formulacoes_pre_argumentativas": 0,
                "score_editorial_do_grupo": 0,
                "fragmentos": [],
            }

        grupo = grupos[chave]
        resumo = resumo_fragmento(item)
        grau = normalizar_texto(pos.get("grau_de_pertenca_ao_indice"))
        estado = normalizar_texto(pot.get("estado_argumentativo"))

        grupo["total_fragmentos"] += 1
        grupo["score_editorial_do_grupo"] += calcular_score_prioridade_capitulo(item)

        if grau == "forte":
            grupo["fortes"] += 1
        elif grau == "provavel":
            grupo["provaveis"] += 1
        elif grau == "fraca":
            grupo["fracos"] += 1
        elif grau == "indefinida":
            grupo["indefinidos"] += 1

        if resumo.get("argumento_reconstruivel"):
            grupo["reconstruiveis"] += 1

        if estado == "argumento_em_esboco":
            grupo["argumentos_em_esboco"] += 1
        elif estado == "formulacao_pre_argumentativa":
            grupo["formulacoes_pre_argumentativas"] += 1

        grupo["fragmentos"].append(
            {
                "fragment_id": resumo["fragment_id"],
                "origem_id": resumo["origem_id"],
                "ordem_no_ficheiro": resumo["ordem_no_ficheiro"],
                "grau_de_pertenca_ao_indice": resumo["grau_de_pertenca_ao_indice"],
                "estado_argumentativo": resumo["estado_argumentativo"],
                "argumento_reconstruivel": resumo["argumento_reconstruivel"],
                "necessita_reconstrucao_forte": resumo["necessita_reconstrucao_forte"],
                "trabalho_no_sistema": resumo["trabalho_no_sistema"],
                "descricao_funcional_curta": resumo["descricao_funcional_curta"],
                "explicacao_textual_do_que_o_fragmento_tenta_fazer": resumo[
                    "explicacao_textual_do_que_o_fragmento_tenta_fazer"
                ],
                "prioridade_de_revisao": resumo["prioridade_de_revisao"],
                "prioridade_de_aproveitamento": resumo["prioridade_de_aproveitamento"],
                "destino_editorial_fino": resumo["destino_editorial_fino"],
            }
        )

    resultado = []
    for grupo in grupos.values():
        grupo["fragmentos"].sort(
            key=lambda x: (
                0 if x.get("grau_de_pertenca_ao_indice") == "forte" else
                1 if x.get("grau_de_pertenca_ao_indice") == "provavel" else
                2 if x.get("grau_de_pertenca_ao_indice") == "fraca" else
                3,
                0 if x.get("argumento_reconstruivel") else 1,
                x.get("ordem_no_ficheiro") or 999999,
            )
        )
        resultado.append(grupo)

    resultado.sort(
        key=lambda g: (
            -g["score_editorial_do_grupo"],
            -g["fortes"],
            -g["provaveis"],
            g["capitulo_id"],
            g["argumento_canonico_relacionado"],
        )
    )

    return resultado


def construir_top_capitulos(fragmentos):
    capitulos = {}

    for item in fragmentos:
        bloco = extrair_bloco(item)
        pos = extrair_posicao(bloco)
        pot = extrair_potencial(bloco)

        parte_id = normalizar_texto(pos.get("parte_id"), "SEM_PARTE")
        capitulo_id = normalizar_texto(pos.get("capitulo_id"), "SEM_CAPITULO")
        capitulo_titulo = normalizar_texto(pos.get("capitulo_titulo"), "Sem capítulo atribuído")
        chave = (parte_id, capitulo_id, capitulo_titulo)

        if chave not in capitulos:
            capitulos[chave] = {
                "parte_id": parte_id,
                "capitulo_id": capitulo_id,
                "capitulo_titulo": capitulo_titulo,
                "score_total": 0,
                "total_fragmentos": 0,
                "fortes": 0,
                "provaveis": 0,
                "fracos": 0,
                "indefinidos": 0,
                "reconstruiveis": 0,
                "argumentos_em_esboco": 0,
                "formulacoes_pre_argumentativas": 0,
                "argumentos_canonicos_presentes": set(),
                "trabalhos_no_sistema_presentes": set(),
                "fragmentos_exemplo": [],
            }

        cap = capitulos[chave]
        grau = normalizar_texto(pos.get("grau_de_pertenca_ao_indice"))
        estado = normalizar_texto(pot.get("estado_argumentativo"))
        score = calcular_score_prioridade_capitulo(item)

        cap["score_total"] += score
        cap["total_fragmentos"] += 1

        if grau == "forte":
            cap["fortes"] += 1
        elif grau == "provavel":
            cap["provaveis"] += 1
        elif grau == "fraca":
            cap["fracos"] += 1
        elif grau == "indefinida":
            cap["indefinidos"] += 1

        if pot.get("argumento_reconstruivel"):
            cap["reconstruiveis"] += 1

        if estado == "argumento_em_esboco":
            cap["argumentos_em_esboco"] += 1
        elif estado == "formulacao_pre_argumentativa":
            cap["formulacoes_pre_argumentativas"] += 1

        argumento = normalizar_texto(pos.get("argumento_canonico_relacionado"))
        if argumento:
            cap["argumentos_canonicos_presentes"].add(argumento)

        trabalho = normalizar_texto(bloco.get("trabalho_no_sistema"))
        if trabalho:
            cap["trabalhos_no_sistema_presentes"].add(trabalho)

        cap["fragmentos_exemplo"].append(
            {
                "fragment_id": item.get("fragment_id"),
                "grau_de_pertenca_ao_indice": grau,
                "estado_argumentativo": estado,
                "argumento_reconstruivel": bool(pot.get("argumento_reconstruivel")),
                "descricao_funcional_curta": bloco.get("descricao_funcional_curta"),
                "score_individual": score,
            }
        )

    resultado = []
    for cap in capitulos.values():
        cap["argumentos_canonicos_presentes"] = sorted(cap["argumentos_canonicos_presentes"])
        cap["trabalhos_no_sistema_presentes"] = sorted(cap["trabalhos_no_sistema_presentes"])

        cap["fragmentos_exemplo"].sort(
            key=lambda x: (
                -x["score_individual"],
                0 if x["grau_de_pertenca_ao_indice"] == "forte" else
                1 if x["grau_de_pertenca_ao_indice"] == "provavel" else
                2,
                0 if x["argumento_reconstruivel"] else 1,
            )
        )
        cap["fragmentos_exemplo"] = cap["fragmentos_exemplo"][:10]
        resultado.append(cap)

    resultado.sort(
        key=lambda x: (
            -x["score_total"],
            -x["fortes"],
            -x["provaveis"],
            x["capitulo_id"],
        )
    )

    return resultado


def imprimir_resumo(fragmentos, prioridade_a, top_capitulos):
    print("=" * 90)
    print("PRIORIZAÇÃO DE FRAGMENTOS PARA MONTAGEM")
    print("=" * 90)
    print(f"Total de fragmentos lidos: {len(fragmentos)}")
    print(f"Fragmentos de prioridade A: {len(prioridade_a)}")
    print(f"Capítulos no ranking: {len(top_capitulos)}")
    print("-" * 90)

    print("Top 10 capítulos para montagem:")
    for i, cap in enumerate(top_capitulos[:10], start=1):
        print(
            f"{i:02d}. {cap['capitulo_id']} | "
            f"{cap['capitulo_titulo']} | "
            f"score={cap['score_total']} | "
            f"fortes={cap['fortes']} | "
            f"prováveis={cap['provaveis']} | "
            f"reconstruíveis={cap['reconstruiveis']} | "
            f"total={cap['total_fragmentos']}"
        )

    print("-" * 90)
    print("Ficheiros gerados:")
    print(f"- {NOME_FICHEIRO_SAIDA_PRIORIDADE_A}")
    print(f"- {NOME_FICHEIRO_SAIDA_MAPA_CAPITULO}")
    print(f"- {NOME_FICHEIRO_SAIDA_TOP_CAPITULOS}")
    print("=" * 90)


def main():
    pasta_script = Path(__file__).resolve().parent
    pasta_cadencia = pasta_script.parent
    pasta_entrada = pasta_cadencia / "04_extrator_q_faz_no_sistema"
    pasta_saida = pasta_script

    caminho_entrada = pasta_entrada / NOME_FICHEIRO_ENTRADA
    caminho_saida_prioridade_a = pasta_saida / NOME_FICHEIRO_SAIDA_PRIORIDADE_A
    caminho_saida_mapa_capitulo = pasta_saida / NOME_FICHEIRO_SAIDA_MAPA_CAPITULO
    caminho_saida_top_capitulos = pasta_saida / NOME_FICHEIRO_SAIDA_TOP_CAPITULOS

    if not caminho_entrada.exists():
        raise FileNotFoundError(
            f"Não encontrei o ficheiro de entrada: {caminho_entrada}"
        )

    fragmentos = carregar_json(caminho_entrada)

    if not isinstance(fragmentos, list):
        raise ValueError("O ficheiro de entrada tem de conter uma lista de fragmentos.")

    prioridade_a = construir_fragmentos_prioridade_a(fragmentos)
    mapa_por_capitulo = construir_mapa_por_capitulo(fragmentos)
    top_capitulos = construir_top_capitulos(fragmentos)

    guardar_json(caminho_saida_prioridade_a, prioridade_a)
    guardar_json(caminho_saida_mapa_capitulo, mapa_por_capitulo)
    guardar_json(caminho_saida_top_capitulos, top_capitulos)

    imprimir_resumo(fragmentos, prioridade_a, top_capitulos)


if __name__ == "__main__":
    main()