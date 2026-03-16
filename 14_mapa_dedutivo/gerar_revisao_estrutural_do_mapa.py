import json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# PATHS
# ============================================================

PASTA_BASE = Path(__file__).resolve().parent

FICHEIRO_MAPA = PASTA_BASE / "02_mapa_dedutivo_arquitetura_fragmentos.json"
FICHEIRO_IMPACTO = PASTA_BASE / "impacto_fragmentos_no_mapa.json"
FICHEIRO_RELATORIO = PASTA_BASE / "impacto_fragmentos_no_mapa_relatorio_validacao.json"

FICHEIRO_SAIDA = PASTA_BASE / "revisao_estrutural_do_mapa.json"


# ============================================================
# UTILITÁRIOS
# ============================================================

def carregar_json(caminho: Path) -> Any:
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def guardar_json(caminho: Path, dados: Any) -> None:
    with caminho.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def normalizar_dict(valor: Any) -> Dict[str, Any]:
    return valor if isinstance(valor, dict) else {}


def normalizar_lista(valor: Any) -> List[Any]:
    return valor if isinstance(valor, list) else []


def limpar_texto(valor: Any) -> Optional[str]:
    if valor is None:
        return None
    if not isinstance(valor, str):
        valor = str(valor)
    valor = " ".join(valor.split()).strip()
    return valor or None


def limpar_lista_textos(valores: Any) -> List[str]:
    saida: List[str] = []
    for v in normalizar_lista(valores):
        txt = limpar_texto(v)
        if txt:
            saida.append(txt)
    return saida


def adicionar_unico(lista: List[str], valor: Optional[str]) -> None:
    if valor and valor not in lista:
        lista.append(valor)


def adicionar_varios_unicos(destino: List[str], origem: List[str]) -> None:
    for item in origem:
        adicionar_unico(destino, item)


def top_itens(contador: Counter, limite: int = 10) -> List[Dict[str, Any]]:
    return [{"valor": k, "contagem": v} for k, v in contador.most_common(limite)]


def escolher_valor_dominante(contador: Counter) -> Optional[str]:
    if not contador:
        return None
    return contador.most_common(1)[0][0]


def numero_de_proposicao(prop_id: str) -> int:
    if not isinstance(prop_id, str):
        return 999999
    digitos = "".join(ch for ch in prop_id if ch.isdigit())
    if not digitos:
        return 999999
    return int(digitos)


# ============================================================
# LEITURA DO MAPA
# ============================================================

def extrair_proposicoes_do_mapa(mapa: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    proposicoes: List[Dict[str, Any]] = []
    indice: Dict[str, Dict[str, Any]] = {}

    for bloco in normalizar_lista(mapa.get("blocos")):
        bloco = normalizar_dict(bloco)
        bloco_id = bloco.get("id")
        bloco_titulo = bloco.get("titulo")

        for prop in normalizar_lista(bloco.get("proposicoes")):
            prop = normalizar_dict(prop)
            prop_id = prop.get("id")
            if not prop_id:
                continue

            enriquecida = {
                **prop,
                "_bloco_id": bloco_id,
                "_bloco_titulo": bloco_titulo,
            }
            proposicoes.append(enriquecida)
            indice[prop_id] = enriquecida

    proposicoes.sort(key=lambda p: p.get("numero", numero_de_proposicao(p.get("id", ""))))
    return proposicoes, indice


# ============================================================
# AGREGAÇÃO DO IMPACTO POR PROPOSIÇÃO
# ============================================================

def criar_agregador_vazio() -> Dict[str, Any]:
    return {
        "fragmentos_tocam": [],
        "origens_tocam": [],
        "zonas_filosoficas": Counter(),
        "efeitos_principais": Counter(),
        "acoes_recomendadas": Counter(),
        "tipos_utilidade": Counter(),
        "prioridades_editoriais": Counter(),
        "graus_relevancia": Counter(),
        "tipos_relacao": Counter(),
        "necessita_revisao_humana": 0,
        "obriga_reescrever": 0,
        "obriga_dividir": 0,
        "obriga_criar_intermedio": 0,
        "resumos_fragmento": [],
        "teses_fragmento": [],
        "justificacoes_associacao": [],
        "o_que_acrescenta": [],
        "justificacoes_novas": [],
        "objecoes_bloqueadas": [],
        "mediacoes_fornecidas": [],
        "conceitos_novos": [],
        "propostas_nova_formulacao": [],
        "propostas_novo_passo": [],
        "entre_que_passos": [],
        "observacoes_finais": [],
    }


def agregar_impacto_por_proposicao(impactos: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    agregado: Dict[str, Dict[str, Any]] = defaultdict(criar_agregador_vazio)

    for item in impactos:
        item = normalizar_dict(item)
        fragment_id = item.get("fragment_id")
        origem_id = item.get("origem_id")

        raiz = normalizar_dict(item.get("impacto_no_mapa_fragmento"))
        resumo_fragmento = limpar_texto(raiz.get("resumo_do_fragmento_para_o_mapa"))
        tese_fragmento = limpar_texto(raiz.get("tese_principal_relevante"))
        zona_filosofica = limpar_texto(raiz.get("zona_filosofica_dominante"))
        efeito_principal = limpar_texto(raiz.get("efeito_principal_no_mapa"))
        tipo_utilidade = limpar_texto(raiz.get("tipo_de_utilidade_principal"))

        impacto_editorial = normalizar_dict(raiz.get("impacto_editorial_e_dedutivo"))
        decisao_final = normalizar_dict(raiz.get("decisao_final"))

        acao_recomendada = limpar_texto(decisao_final.get("acao_recomendada_sobre_o_mapa"))
        prioridade_editorial = limpar_texto(decisao_final.get("prioridade_editorial"))
        observacao_final = limpar_texto(decisao_final.get("observacao_final"))
        necessita_revisao_humana = bool(decisao_final.get("necessita_revisao_humana"))

        for prop_ref in normalizar_lista(raiz.get("proposicoes_do_mapa_tocadas")):
            prop_ref = normalizar_dict(prop_ref)
            prop_id = prop_ref.get("proposicao_id")
            if not prop_id:
                continue

            bucket = agregado[prop_id]

            if fragment_id and fragment_id not in bucket["fragmentos_tocam"]:
                bucket["fragmentos_tocam"].append(fragment_id)

            if origem_id and origem_id not in bucket["origens_tocam"]:
                bucket["origens_tocam"].append(origem_id)

            if zona_filosofica:
                bucket["zonas_filosoficas"][zona_filosofica] += 1

            if efeito_principal:
                bucket["efeitos_principais"][efeito_principal] += 1

            if acao_recomendada:
                bucket["acoes_recomendadas"][acao_recomendada] += 1

            if tipo_utilidade:
                bucket["tipos_utilidade"][tipo_utilidade] += 1

            if prioridade_editorial:
                bucket["prioridades_editoriais"][prioridade_editorial] += 1

            grau_relevancia = limpar_texto(prop_ref.get("grau_de_relevancia"))
            tipo_relacao = limpar_texto(prop_ref.get("tipo_de_relacao"))
            justificacao_associacao = limpar_texto(prop_ref.get("justificacao_da_associacao"))

            if grau_relevancia:
                bucket["graus_relevancia"][grau_relevancia] += 1

            if tipo_relacao:
                bucket["tipos_relacao"][tipo_relacao] += 1

            if necessita_revisao_humana:
                bucket["necessita_revisao_humana"] += 1

            if impacto_editorial.get("obriga_a_reescrever_o_passo") is True:
                bucket["obriga_reescrever"] += 1

            if impacto_editorial.get("obriga_a_dividir_o_passo") is True:
                bucket["obriga_dividir"] += 1

            if impacto_editorial.get("obriga_a_criar_passo_intermedio") is True:
                bucket["obriga_criar_intermedio"] += 1

            adicionar_unico(bucket["resumos_fragmento"], resumo_fragmento)
            adicionar_unico(bucket["teses_fragmento"], tese_fragmento)
            adicionar_unico(bucket["justificacoes_associacao"], justificacao_associacao)

            adicionar_unico(
                bucket["o_que_acrescenta"],
                limpar_texto(impacto_editorial.get("o_que_o_fragmento_acrescenta_ao_mapa"))
            )
            adicionar_unico(
                bucket["justificacoes_novas"],
                limpar_texto(impacto_editorial.get("justificacao_nova_que_fornece"))
            )
            adicionar_varios_unicos(
                bucket["objecoes_bloqueadas"],
                limpar_lista_textos(impacto_editorial.get("objecoes_que_ajuda_a_bloquear"))
            )

            mediacao = limpar_texto(impacto_editorial.get("mediacao_que_fornece"))
            if mediacao and mediacao != "nao fornece mediacao estrutural":
                adicionar_unico(bucket["mediacoes_fornecidas"], mediacao)

            adicionar_varios_unicos(
                bucket["conceitos_novos"],
                limpar_lista_textos(impacto_editorial.get("conceitos_ou_distincoes_novas"))
            )

            adicionar_unico(
                bucket["propostas_nova_formulacao"],
                limpar_texto(impacto_editorial.get("proposta_de_nova_formulacao"))
            )
            adicionar_unico(
                bucket["propostas_novo_passo"],
                limpar_texto(impacto_editorial.get("proposta_de_novo_passo"))
            )

            for par in normalizar_lista(impacto_editorial.get("entre_que_passos_deveria_entrar")):
                par = limpar_texto(par)
                adicionar_unico(bucket["entre_que_passos"], par)

            adicionar_unico(bucket["observacoes_finais"], observacao_final)

    return agregado


# ============================================================
# DIAGNÓSTICO E DECISÃO
# ============================================================

def classificar_estabilidade(
    total_fragmentos: int,
    efeitos: Counter,
    acoes: Counter,
    obriga_reescrever: int,
    obriga_dividir: int,
    obriga_criar_intermedio: int
) -> str:
    if total_fragmentos == 0:
        return "nao_testado_pelos_fragmentos"

    reformular = acoes.get("reformular", 0)
    densificar = acoes.get("densificar", 0)
    medeia = efeitos.get("medeia", 0)

    if obriga_dividir > 0 or obriga_criar_intermedio > 0:
        return "instavel_por_falta_de_mediação"

    if reformular >= 2 or obriga_reescrever >= 2:
        return "instavel_por_reformulacao"

    if densificar >= 8 or medeia >= 3:
        return "estavel_mas_a_densificar"

    return "globalmente_estavel"


def decidir_necessidade_principal(
    estabilidade: str,
    acoes: Counter,
    efeitos: Counter,
    obriga_dividir: int,
    obriga_criar_intermedio: int
) -> Optional[str]:
    if estabilidade == "nao_testado_pelos_fragmentos":
        return "verificar_manual"

    if obriga_dividir > 0:
        return "avaliar_divisao_do_passo"

    if obriga_criar_intermedio > 0:
        return "avaliar_passo_intermedio"

    if acoes.get("reformular", 0) > 0:
        return "reformular"

    if efeitos.get("medeia", 0) > 0:
        return "explicitar_mediacoes"

    if acoes.get("densificar", 0) > 0:
        return "densificar"

    return "manter"


def decidir_acao_estrutural(
    estabilidade: str,
    acoes: Counter,
    obriga_dividir: int,
    obriga_criar_intermedio: int
) -> str:
    if estabilidade == "nao_testado_pelos_fragmentos":
        return "manter_provisoriamente"

    if obriga_dividir > 0:
        return "avaliar_dividir"

    if obriga_criar_intermedio > 0:
        return "avaliar_criar_intermedio"

    if acoes.get("reformular", 0) > 0:
        return "reformular"

    if acoes.get("densificar", 0) > 0:
        return "densificar"

    return "manter"


def construir_diagnostico_textual(
    prop: Dict[str, Any],
    total_fragmentos: int,
    zona_dominante: Optional[str],
    efeito_dominante: Optional[str],
    acao_dominante: Optional[str],
    estabilidade: str,
    objecoes_bloqueadas: List[str],
    mediacoes_fornecidas: List[str]
) -> str:
    partes: List[str] = []

    partes.append(
        f"A proposição {prop.get('id')} foi tocada por {total_fragmentos} fragmento(s)."
    )

    if zona_dominante:
        partes.append(f"A pressão dominante vem da zona {zona_dominante}.")

    if efeito_dominante:
        partes.append(f"O efeito dominante é '{efeito_dominante}'.")

    if acao_dominante:
        partes.append(f"A ação editorial dominante é '{acao_dominante}'.")

    partes.append(f"O estado estrutural estimado é '{estabilidade}'.")

    if mediacoes_fornecidas:
        partes.append("Há material para explicitar mediações intermédias.")

    if objecoes_bloqueadas:
        partes.append("Há também apoio para bloqueio de objeções recorrentes.")

    return " ".join(partes)


def escolher_melhor_formulacao_provisoria(
    mapa_existente: Dict[str, Any],
    propostas_fragmentos: List[str]
) -> Optional[str]:
    decisao_editorial = normalizar_dict(mapa_existente.get("decisao_editorial"))
    existente = limpar_texto(decisao_editorial.get("nova_formulacao_provisoria"))
    if existente:
        return existente
    if propostas_fragmentos:
        return propostas_fragmentos[0]
    return None


# ============================================================
# CONSTRUÇÃO DA REVISÃO ESTRUTURAL
# ============================================================

def construir_revisao_estrutural(
    mapa: Dict[str, Any],
    impactos: List[Dict[str, Any]],
    relatorio: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    proposicoes, indice_props = extrair_proposicoes_do_mapa(mapa)
    agregado = agregar_impacto_por_proposicao(impactos)

    revisoes: List[Dict[str, Any]] = []

    resumo_estabilidade = Counter()
    resumo_necessidades = Counter()
    resumo_acoes = Counter()
    resumo_zonas = Counter()

    for prop in proposicoes:
        prop_id = prop.get("id")
        dados = agregado.get(prop_id, criar_agregador_vazio())

        total_fragmentos = len(dados["fragmentos_tocam"])
        total_origens = len(dados["origens_tocam"])

        zona_dominante = escolher_valor_dominante(dados["zonas_filosoficas"])
        efeito_dominante = escolher_valor_dominante(dados["efeitos_principais"])
        acao_dominante = escolher_valor_dominante(dados["acoes_recomendadas"])
        utilidade_dominante = escolher_valor_dominante(dados["tipos_utilidade"])
        prioridade_dominante = escolher_valor_dominante(dados["prioridades_editoriais"])

        estabilidade = classificar_estabilidade(
            total_fragmentos=total_fragmentos,
            efeitos=dados["efeitos_principais"],
            acoes=dados["acoes_recomendadas"],
            obriga_reescrever=dados["obriga_reescrever"],
            obriga_dividir=dados["obriga_dividir"],
            obriga_criar_intermedio=dados["obriga_criar_intermedio"],
        )

        necessidade_principal = decidir_necessidade_principal(
            estabilidade=estabilidade,
            acoes=dados["acoes_recomendadas"],
            efeitos=dados["efeitos_principais"],
            obriga_dividir=dados["obriga_dividir"],
            obriga_criar_intermedio=dados["obriga_criar_intermedio"],
        )

        acao_estrutural = decidir_acao_estrutural(
            estabilidade=estabilidade,
            acoes=dados["acoes_recomendadas"],
            obriga_dividir=dados["obriga_dividir"],
            obriga_criar_intermedio=dados["obriga_criar_intermedio"],
        )

        justificacao = normalizar_dict(prop.get("justificacao"))
        tratamento = normalizar_dict(prop.get("tratamento_academico"))
        decisao_editorial = normalizar_dict(prop.get("decisao_editorial"))

        revisao = {
            "proposicao_id": prop_id,
            "numero": prop.get("numero"),
            "bloco_id": prop.get("_bloco_id"),
            "bloco_titulo": prop.get("_bloco_titulo"),
            "proposicao": prop.get("proposicao"),
            "descricao_curta": prop.get("descricao_curta"),
            "depende_de": normalizar_lista(prop.get("depende_de")),
            "prepara": normalizar_lista(prop.get("prepara")),
            "estado_anterior_no_mapa": {
                "estado_atual": decisao_editorial.get("estado_atual"),
                "necessidade_de_tratamento": decisao_editorial.get("necessidade_de_tratamento"),
                "acao_sobre_o_mapa": decisao_editorial.get("acao_sobre_o_mapa"),
                "prioridade_editorial": decisao_editorial.get("prioridade_editorial"),
            },
            "base_dedutiva_existente": {
                "tese_minima": justificacao.get("tese_minima"),
                "justificacao_interna_do_passo": justificacao.get("justificacao_interna_do_passo"),
                "tipo_de_necessidade": justificacao.get("tipo_de_necessidade"),
                "estatuto_inferencial": justificacao.get("estatuto_inferencial"),
                "formulacao_filosofico_academica": tratamento.get("formulacao_filosofico_academica"),
                "o_que_falta_provar_ou_explicitar": tratamento.get("o_que_falta_provar_ou_explicitar"),
                "objecoes_tipicas_a_bloquear": limpar_lista_textos(tratamento.get("objecoes_tipicas_a_bloquear")),
                "mediacoes_em_falta_no_mapa": limpar_lista_textos(tratamento.get("mediacoes_em_falta")),
            },
            "pressao_dos_fragmentos": {
                "total_fragmentos_que_tocam": total_fragmentos,
                "total_origens_que_tocam": total_origens,
                "zona_filosofica_dominante": zona_dominante,
                "efeito_principal_dominante": efeito_dominante,
                "acao_recomendada_dominante": acao_dominante,
                "tipo_de_utilidade_dominante": utilidade_dominante,
                "prioridade_editorial_dominante": prioridade_dominante,
                "distribuicao_efeitos": dict(dados["efeitos_principais"]),
                "distribuicao_acoes": dict(dados["acoes_recomendadas"]),
                "distribuicao_tipos_relacao": dict(dados["tipos_relacao"]),
                "distribuicao_graus_relevancia": dict(dados["graus_relevancia"]),
                "distribuicao_tipos_utilidade": dict(dados["tipos_utilidade"]),
                "distribuicao_prioridades": dict(dados["prioridades_editoriais"]),
            },
            "materiais_de_reconstrucao": {
                "fragmentos_relacionados": dados["fragmentos_tocam"],
                "origens_relacionadas": dados["origens_tocam"],
                "resumos_de_fragmento": dados["resumos_fragmento"][:20],
                "teses_principais_dos_fragmentos": dados["teses_fragmento"][:20],
                "justificacoes_da_associacao": dados["justificacoes_associacao"][:20],
                "o_que_os_fragmentos_acrescentam": dados["o_que_acrescenta"][:20],
                "justificacoes_novas_que_fornecem": dados["justificacoes_novas"][:20],
                "objecoes_que_ajudam_a_bloquear": dados["objecoes_bloqueadas"][:20],
                "mediacoes_que_fornecem": dados["mediacoes_fornecidas"][:20],
                "conceitos_ou_distincoes_novas": dados["conceitos_novos"][:20],
                "propostas_de_nova_formulacao": dados["propostas_nova_formulacao"][:10],
                "propostas_de_novo_passo": dados["propostas_novo_passo"][:10],
                "entre_que_passos_deveria_entrar": dados["entre_que_passos"][:10],
                "observacoes_finais": dados["observacoes_finais"][:20],
            },
            "diagnostico_estrutural": {
                "estabilidade": estabilidade,
                "necessidade_principal": necessidade_principal,
                "acao_estrutural_recomendada": acao_estrutural,
                "indicios_de_reescrita": dados["obriga_reescrever"],
                "indicios_de_divisao": dados["obriga_dividir"],
                "indicios_de_passo_intermedio": dados["obriga_criar_intermedio"],
                "necessita_revisao_humana_em": dados["necessita_revisao_humana"],
                "diagnostico_textual": construir_diagnostico_textual(
                    prop=prop,
                    total_fragmentos=total_fragmentos,
                    zona_dominante=zona_dominante,
                    efeito_dominante=efeito_dominante,
                    acao_dominante=acao_dominante,
                    estabilidade=estabilidade,
                    objecoes_bloqueadas=dados["objecoes_bloqueadas"],
                    mediacoes_fornecidas=dados["mediacoes_fornecidas"],
                ),
            },
            "nova_formulacao_provisoria": escolher_melhor_formulacao_provisoria(
                mapa_existente=prop,
                propostas_fragmentos=dados["propostas_nova_formulacao"],
            ),
        }

        revisoes.append(revisao)

        resumo_estabilidade[estabilidade] += 1
        if necessidade_principal:
            resumo_necessidades[necessidade_principal] += 1
        resumo_acoes[acao_estrutural] += 1
        if zona_dominante:
            resumo_zonas[zona_dominante] += 1

    top_proposicoes_pressao = sorted(
        revisoes,
        key=lambda r: (
            r["pressao_dos_fragmentos"]["total_fragmentos_que_tocam"],
            r["diagnostico_estrutural"]["indicios_de_passo_intermedio"],
            r["diagnostico_estrutural"]["indicios_de_divisao"],
            r["diagnostico_estrutural"]["indicios_de_reescrita"],
        ),
        reverse=True
    )[:15]

    saida = {
        "meta": {
            "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
            "ficheiro_mapa_origem": FICHEIRO_MAPA.name,
            "ficheiro_impacto_origem": FICHEIRO_IMPACTO.name,
            "ficheiro_relatorio_origem": FICHEIRO_RELATORIO.name if FICHEIRO_RELATORIO.exists() else None,
            "total_proposicoes_no_mapa": len(proposicoes),
            "total_fragmentos_no_impacto": len(impactos),
            "objetivo": (
                "Converter o impacto dos fragmentos sobre o mapa dedutivo numa "
                "revisão estrutural por proposição, pronta para reconstrução do mapa."
            ),
        },
        "resumo_global": {
            "distribuicao_estabilidade": dict(resumo_estabilidade),
            "distribuicao_necessidade_principal": dict(resumo_necessidades),
            "distribuicao_acao_estrutural_recomendada": dict(resumo_acoes),
            "zonas_filosoficas_dominantes_nas_proposicoes": dict(resumo_zonas),
            "top_proposicoes_por_pressao": [
                {
                    "proposicao_id": r["proposicao_id"],
                    "numero": r["numero"],
                    "proposicao": r["proposicao"],
                    "total_fragmentos_que_tocam": r["pressao_dos_fragmentos"]["total_fragmentos_que_tocam"],
                    "estabilidade": r["diagnostico_estrutural"]["estabilidade"],
                    "acao_estrutural_recomendada": r["diagnostico_estrutural"]["acao_estrutural_recomendada"],
                }
                for r in top_proposicoes_pressao
            ],
        },
        "macro_relatorio_original": relatorio if isinstance(relatorio, dict) else None,
        "revisao_por_proposicao": revisoes,
    }

    return saida


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    if not FICHEIRO_MAPA.exists():
        raise FileNotFoundError(f"Não encontrei o ficheiro do mapa: {FICHEIRO_MAPA}")

    if not FICHEIRO_IMPACTO.exists():
        raise FileNotFoundError(f"Não encontrei o ficheiro do impacto: {FICHEIRO_IMPACTO}")

    mapa = carregar_json(FICHEIRO_MAPA)
    impactos = carregar_json(FICHEIRO_IMPACTO)
    relatorio = carregar_json(FICHEIRO_RELATORIO) if FICHEIRO_RELATORIO.exists() else None

    if not isinstance(mapa, dict):
        raise TypeError("O ficheiro do mapa tem de ser um JSON objeto.")

    if not isinstance(impactos, list):
        raise TypeError("O ficheiro de impacto tem de ser uma lista JSON.")

    revisao = construir_revisao_estrutural(
        mapa=mapa,
        impactos=impactos,
        relatorio=relatorio,
    )

    guardar_json(FICHEIRO_SAIDA, revisao)

    total_props = revisao["meta"]["total_proposicoes_no_mapa"]
    top_pressao = revisao["resumo_global"]["top_proposicoes_por_pressao"][:10]

    print(f"Ficheiro gerado: {FICHEIRO_SAIDA}")
    print(f"Total de proposições revistas: {total_props}")
    print("Top 10 proposições por pressão dos fragmentos:")
    for item in top_pressao:
        print(
            f"  - {item['proposicao_id']} | "
            f"{item['total_fragmentos_que_tocam']} fragmentos | "
            f"{item['acao_estrutural_recomendada']}"
        )


if __name__ == "__main__":
    main()