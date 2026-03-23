#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
restringir_adjudicacao_confrontos_filosoficos_v1.py

Objetivo:
- Ler a adjudicação filosófica gerada em adjudicacao_confrontos_filosoficos_v1.json
- Produzir uma versão redacionalmente restringida
- Limitar amplitude temática e excesso de agregação
- Preservar rastreabilidade estrutural mínima
- Gerar JSON + relatório textual

Input:
- 16_validacao_integral/01_dados/adjudicacao_confrontos_filosoficos_v1.json

Outputs:
- 16_validacao_integral/01_dados/adjudicacao_confrontos_filosoficos_restrita_v1.json
- 16_validacao_integral/02_outputs/relatorio_restricao_adjudicacao_confrontos_filosoficos_v1.txt
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


FASE_DIRNAME = "16_validacao_integral"


# ============================================================
# Utilitários gerais
# ============================================================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)


def ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def unique_preserve_order(items: List[Any]) -> List[Any]:
    seen = set()
    out = []
    for x in items:
        key = json.dumps(x, ensure_ascii=False, sort_keys=True) if isinstance(x, (dict, list)) else str(x)
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


def truncate_list(items: List[Any], max_items: int) -> List[Any]:
    return items[:max_items] if len(items) > max_items else items


def first_non_empty_string(*values: Any) -> str:
    for v in values:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def to_text_list(value: Any) -> List[str]:
    out: List[str] = []
    for item in ensure_list(value):
        if item is None:
            continue
        s = str(item).strip()
        if s:
            out.append(s)
    return unique_preserve_order(out)


# ============================================================
# Caminhos / resolução da raiz do projeto
# ============================================================

def infer_project_root(cli_project_root: str | None = None) -> Path:
    """
    Resolve a raiz da fase 16_validacao_integral de forma robusta.

    Casos suportados:
    - --project-root apontado diretamente
    - script corrido dentro de .../16_validacao_integral/scripts
    - script corrido dentro de .../16_validacao_integral
    - fallback por procura ascendente a partir de cwd e __file__
    """
    if cli_project_root:
        p = Path(cli_project_root).expanduser().resolve()
        if p.name == FASE_DIRNAME:
            return p
        candidate = p / FASE_DIRNAME
        if candidate.exists():
            return candidate
        return p

    cwd = Path.cwd().resolve()

    if cwd.name == "scripts" and cwd.parent.name == FASE_DIRNAME:
        return cwd.parent

    if cwd.name == FASE_DIRNAME:
        return cwd

    for parent in [cwd] + list(cwd.parents):
        if parent.name == FASE_DIRNAME:
            return parent

    here = Path(__file__).resolve()

    if here.parent.name == "scripts" and here.parent.parent.name == FASE_DIRNAME:
        return here.parent.parent

    for parent in [here.parent] + list(here.parents):
        if parent.name == FASE_DIRNAME:
            return parent

    return cwd


def build_paths(project_root: Path) -> Dict[str, Path]:
    dados = project_root / "01_dados"
    outputs = project_root / "02_outputs"

    return {
        "project_root": project_root,
        "dados": dados,
        "outputs": outputs,
        "input_json": dados / "adjudicacao_confrontos_filosoficos_v1.json",
        "output_json": dados / "adjudicacao_confrontos_filosoficos_restrita_v1.json",
        "output_report": outputs / "relatorio_restricao_adjudicacao_confrontos_filosoficos_v1.txt",
    }


# ============================================================
# Parâmetros de restrição
# ============================================================

MAX_AUTORES = 5
MAX_TRADICOES = 4
MAX_CONCEITOS = 6
MAX_TEMAS = 8
MAX_TESES_CLASSICAS = 4
MAX_ADVERSARIOS = 3
MAX_OBJECOES_FORTES = 4
MAX_INSUFICIENCIAS = 3
MAX_LINHAS_TRATAMENTO = 3
MAX_TIPO_RESPOSTA = 3
MAX_TIPO_TENSAO = 2
MAX_VEREDITO = 2
MAX_CAMPOS = 3
MAX_PONTES = 3
MAX_ANCORAGENS = 2

MAX_TESES_SUSTENTACAO = 4
MAX_DISTINCOES_MINIMAS = 4
MAX_OBJECOES_PRIORIZADAS = 3
MAX_CHECKLIST = 4
MAX_SEQUENCIA_REDACAO = 3


ONTOLOGY_CORE_HINTS = {
    "ser", "real", "unidade", "diferença", "diferenca", "relação", "relacao",
    "estrutura", "limite", "potência", "potencia", "atualização", "atualizacao",
    "regionalização", "regionalizacao", "multiplicidade"
}

NORMATIVE_HINTS = {
    "dano", "bem", "mal", "normatividade", "dever", "responsabilidade",
    "dignidade", "vida boa", "ético", "etico", "moral", "justiça", "justica"
}

SEMANTIC_HINTS = {
    "linguagem", "símbolo", "simbolo", "sentido", "representação", "representacao",
    "mediação", "mediacao", "significado", "expressão", "expressao"
}

EPISTEMIC_HINTS = {
    "verdade", "erro", "critério", "criterio", "objetividade", "correção", "correcao",
    "justificação", "justificacao", "conhecimento"
}

METASTRUCTURAL_HINTS = {
    "critério último", "criterio ultimo", "fecho", "arquitetura", "percurso",
    "passagem entre regimes", "inteligibilidade do sistema", "metaarquitetonico",
    "metaestrutural", "sistema"
}


# ============================================================
# Heurísticas de foco
# ============================================================

def derive_focus_tags(entry: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    title = first_non_empty_string(
        entry.get("titulo_curto"),
        entry.get("pergunta_central"),
        entry.get("descricao_do_confronto"),
    ).lower()

    if any(k in title for k in ["ser", "real", "unidade", "diferença", "diferenca", "relação", "relacao"]):
        tags.append("ontologia_fundacional")
    if any(k in title for k in ["consciência", "consciencia", "reflex", "sujeito", "subjetividade"]):
        tags.append("subjetividade_reflexividade")
    if any(k in title for k in ["linguagem", "símbolo", "simbolo", "sentido", "representação", "representacao"]):
        tags.append("mediação_semântica")
    if any(k in title for k in ["verdade", "erro", "critério", "criterio", "objetividade"]):
        tags.append("epistemologia_criterial")
    if any(k in title for k in ["dano", "bem", "mal", "normatividade", "responsabilidade", "dignidade"]):
        tags.append("normatividade_prática")
    if any(k in title for k in ["emergência", "emergencia", "níveis", "niveis", "regimes"]):
        tags.append("passagem_entre_niveis")
    if any(k in title for k in ["critério último", "criterio ultimo", "fecho", "arquitetura", "sistema"]):
        tags.append("metaarquitetura")

    if not tags:
        tags.append("confronto_regional")

    return unique_preserve_order(tags)


def pick_core_items(problem_id: str, title: str, items: List[str], max_items: int) -> List[str]:
    """
    Restringe listas com leve sensibilidade temática.
    """
    title_low = (title or "").lower()
    normalized = [x for x in items if isinstance(x, str) and x.strip()]
    if not normalized:
        return []

    if problem_id == "CF01" or "ser" in title_low or "real" in title_low:
        preferred = []
        secondary = []
        for x in normalized:
            xl = x.lower()
            if any(h in xl for h in ONTOLOGY_CORE_HINTS):
                preferred.append(x)
            elif any(h in xl for h in NORMATIVE_HINTS):
                continue
            else:
                secondary.append(x)
        chosen = preferred + secondary
        return truncate_list(unique_preserve_order(chosen), max_items)

    if any(h in title_low for h in ["dano", "bem", "mal", "normatividade", "responsabilidade", "dignidade"]):
        preferred = []
        secondary = []
        for x in normalized:
            xl = x.lower()
            if any(h in xl for h in NORMATIVE_HINTS):
                preferred.append(x)
            elif any(h in xl for h in ONTOLOGY_CORE_HINTS):
                secondary.append(x)
            else:
                secondary.append(x)
        chosen = preferred + secondary
        return truncate_list(unique_preserve_order(chosen), max_items)

    if any(h in title_low for h in ["linguagem", "símbolo", "simbolo", "sentido", "representação", "representacao"]):
        preferred = []
        secondary = []
        for x in normalized:
            xl = x.lower()
            if any(h in xl for h in SEMANTIC_HINTS):
                preferred.append(x)
            else:
                secondary.append(x)
        chosen = preferred + secondary
        return truncate_list(unique_preserve_order(chosen), max_items)

    if any(h in title_low for h in ["verdade", "erro", "critério", "criterio", "objetividade"]):
        preferred = []
        secondary = []
        for x in normalized:
            xl = x.lower()
            if any(h in xl for h in EPISTEMIC_HINTS):
                preferred.append(x)
            else:
                secondary.append(x)
        chosen = preferred + secondary
        return truncate_list(unique_preserve_order(chosen), max_items)

    if any(h in title_low for h in ["critério", "criterio", "fecho", "arquitetura", "regimes", "sistema"]):
        preferred = []
        secondary = []
        for x in normalized:
            xl = x.lower()
            if any(h in xl for h in METASTRUCTURAL_HINTS):
                preferred.append(x)
            else:
                secondary.append(x)
        chosen = preferred + secondary
        return truncate_list(unique_preserve_order(chosen), max_items)

    return truncate_list(unique_preserve_order(normalized), max_items)


# ============================================================
# Restrição de um confronto
# ============================================================

def restrict_single_confronto(item: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Produz uma versão restringida de um confronto adjudicado.
    """
    out = copy.deepcopy(item)
    cf_id = str(item.get("confronto_id", "")).strip() or "CF?"
    title = first_non_empty_string(
        item.get("titulo_curto"),
        item.get("pergunta_central"),
        item.get("descricao_do_confronto"),
    )

    counters = {
        "autores_before": 0, "autores_after": 0,
        "tradicoes_before": 0, "tradicoes_after": 0,
        "conceitos_before": 0, "conceitos_after": 0,
        "temas_before": 0, "temas_after": 0,
        "teses_classicas_before": 0, "teses_classicas_after": 0,
        "adversarios_before": 0, "adversarios_after": 0,
        "obj_fortes_before": 0, "obj_fortes_after": 0,
        "insuf_before": 0, "insuf_after": 0,
        "linhas_before": 0, "linhas_after": 0,
        "resp_before": 0, "resp_after": 0,
        "tensao_before": 0, "tensao_after": 0,
        "veredito_before": 0, "veredito_after": 0,
        "campos_before": 0, "campos_after": 0,
        "pontes_before": 0, "pontes_after": 0,
        "anc_before": 0, "anc_after": 0,
        "teses_sust_before": 0, "teses_sust_after": 0,
        "dist_before": 0, "dist_after": 0,
        "obj_prio_before": 0, "obj_prio_after": 0,
        "check_before": 0, "check_after": 0,
        "seq_before": 0, "seq_after": 0,
    }

    # --- nível geral do confronto
    autores = to_text_list(item.get("autores_prioritarios"))
    counters["autores_before"] = len(autores)
    autores = truncate_list(unique_preserve_order(autores), MAX_AUTORES)
    counters["autores_after"] = len(autores)

    tradicoes = to_text_list(item.get("tradicoes_prioritarias"))
    counters["tradicoes_before"] = len(tradicoes)
    tradicoes = truncate_list(unique_preserve_order(tradicoes), MAX_TRADICOES)
    counters["tradicoes_after"] = len(tradicoes)

    conceitos = to_text_list(item.get("conceitos_classicos_associados"))
    counters["conceitos_before"] = len(conceitos)
    conceitos = pick_core_items(cf_id, title, conceitos, MAX_CONCEITOS)
    counters["conceitos_after"] = len(conceitos)

    temas = to_text_list(item.get("temas_agregados"))
    counters["temas_before"] = len(temas)
    temas = pick_core_items(cf_id, title, temas, MAX_TEMAS)
    counters["temas_after"] = len(temas)

    teses_classicas = to_text_list(item.get("teses_classicas_em_tensao"))
    counters["teses_classicas_before"] = len(teses_classicas)
    teses_classicas = pick_core_items(cf_id, title, teses_classicas, MAX_TESES_CLASSICAS)
    counters["teses_classicas_after"] = len(teses_classicas)

    adversarios = to_text_list(item.get("tipos_de_adversario_filosofico"))
    counters["adversarios_before"] = len(adversarios)
    adversarios = truncate_list(unique_preserve_order(adversarios), MAX_ADVERSARIOS)
    counters["adversarios_after"] = len(adversarios)

    obj_fortes = to_text_list(item.get("objecoes_fortes_a_responder"))
    counters["obj_fortes_before"] = len(obj_fortes)
    obj_fortes = pick_core_items(cf_id, title, obj_fortes, MAX_OBJECOES_FORTES)
    counters["obj_fortes_after"] = len(obj_fortes)

    insuf = to_text_list(item.get("insuficiencias_tipicas_identificadas"))
    counters["insuf_before"] = len(insuf)
    insuf = truncate_list(unique_preserve_order(insuf), MAX_INSUFICIENCIAS)
    counters["insuf_after"] = len(insuf)

    linhas = to_text_list(item.get("linhas_de_tratamento"))
    counters["linhas_before"] = len(linhas)
    linhas = truncate_list(unique_preserve_order(linhas), MAX_LINHAS_TRATAMENTO)
    counters["linhas_after"] = len(linhas)

    tipo_resp = to_text_list(item.get("tipo_de_resposta_exigida"))
    counters["resp_before"] = len(tipo_resp)
    tipo_resp = truncate_list(unique_preserve_order(tipo_resp), MAX_TIPO_RESPOSTA)
    counters["resp_after"] = len(tipo_resp)

    tipo_tensao = to_text_list(item.get("tipo_de_tensao_com_o_sistema"))
    counters["tensao_before"] = len(tipo_tensao)
    tipo_tensao = truncate_list(unique_preserve_order(tipo_tensao), MAX_TIPO_TENSAO)
    counters["tensao_after"] = len(tipo_tensao)

    veredito = to_text_list(item.get("veredito_provisorio"))
    counters["veredito_before"] = len(veredito)
    veredito = truncate_list(unique_preserve_order(veredito), MAX_VEREDITO)
    counters["veredito_after"] = len(veredito)

    campos = to_text_list(item.get("campo_ids_relacionados"))
    counters["campos_before"] = len(campos)
    campos = truncate_list(unique_preserve_order(campos), MAX_CAMPOS)
    counters["campos_after"] = len(campos)

    pontes = to_text_list(item.get("ponte_ids_relacionadas"))
    counters["pontes_before"] = len(pontes)
    pontes = truncate_list(unique_preserve_order(pontes), MAX_PONTES)
    counters["pontes_after"] = len(pontes)

    ancoragens = to_text_list(item.get("ancoragem_ids_relacionadas"))
    counters["anc_before"] = len(ancoragens)
    ancoragens = truncate_list(unique_preserve_order(ancoragens), MAX_ANCORAGENS)
    counters["anc_after"] = len(ancoragens)

    # --- nível do bloco adjudicacao_filosofica
    adj = item.get("adjudicacao_filosofica", {})
    if not isinstance(adj, dict):
        adj = {}

    sintese = first_non_empty_string(
        adj.get("sintese_adjudicada"),
        item.get("descricao_do_confronto"),
    )

    tese_central = first_non_empty_string(
        adj.get("tese_central_adjudicada"),
        adj.get("sintese_adjudicada"),
        item.get("resposta_provavel_do_sistema"),
    )

    teses_sust = to_text_list(adj.get("teses_de_sustentacao"))
    counters["teses_sust_before"] = len(teses_sust)
    teses_sust = pick_core_items(cf_id, title, teses_sust, MAX_TESES_SUSTENTACAO)
    counters["teses_sust_after"] = len(teses_sust)

    dist = to_text_list(adj.get("distincoes_conceituais_minimas"))
    counters["dist_before"] = len(dist)
    dist = pick_core_items(cf_id, title, dist, MAX_DISTINCOES_MINIMAS)
    counters["dist_after"] = len(dist)

    obj_prio = to_text_list(adj.get("objecoes_priorizadas"))
    counters["obj_prio_before"] = len(obj_prio)
    obj_prio = pick_core_items(cf_id, title, obj_prio, MAX_OBJECOES_PRIORIZADAS)
    counters["obj_prio_after"] = len(obj_prio)

    articulacao = adj.get("articulacao_estrutural", {})
    if not isinstance(articulacao, dict):
        articulacao = {}

    articulacao_restrita = {
        "proposicoes_nucleares": truncate_list(
            unique_preserve_order(to_text_list(articulacao.get("proposicoes_nucleares"))),
            6
        ),
        "pontes_entre_niveis": truncate_list(
            unique_preserve_order(to_text_list(articulacao.get("pontes_entre_niveis"))),
            MAX_PONTES
        ),
        "ancoragens_cientificas": truncate_list(
            unique_preserve_order(to_text_list(articulacao.get("ancoragens_cientificas"))),
            MAX_ANCORAGENS
        ),
        "campos_do_real": truncate_list(
            unique_preserve_order(to_text_list(articulacao.get("campos_do_real"))),
            MAX_CAMPOS
        ),
    }

    decisao = adj.get("decisao_de_adjudicacao", {})
    if not isinstance(decisao, dict):
        decisao = {}

    plano_red = adj.get("plano_de_redacao_canonica", {})
    if not isinstance(plano_red, dict):
        plano_red = {}

    sequencia = to_text_list(plano_red.get("sequencia_minima"))
    counters["seq_before"] = len(sequencia)
    if not sequencia:
        sequencia = [
            "Delimitar o núcleo do confronto.",
            "Formulação da objeção mais forte.",
            "Resposta canónica disciplinada.",
        ]
    sequencia = truncate_list(unique_preserve_order(sequencia), MAX_SEQUENCIA_REDACAO)
    counters["seq_after"] = len(sequencia)

    checklist = to_text_list(adj.get("checklist_de_fecho"))
    counters["check_before"] = len(checklist)
    if not checklist:
        checklist = [
            "O confronto ficou limitado ao seu núcleo temático.",
            "As objeções foram reduzidas ao mínimo decisivo.",
            "A articulação estrutural não excede o necessário.",
        ]
    checklist = truncate_list(unique_preserve_order(checklist), MAX_CHECKLIST)
    counters["check_after"] = len(checklist)

    notas = [
        "Versão restringida para disciplina redacional.",
        f"Máximos aplicados: {MAX_TESES_SUSTENTACAO} teses, {MAX_DISTINCOES_MINIMAS} distinções, {MAX_OBJECOES_PRIORIZADAS} objeções priorizadas.",
        "Temas, autores, campos, pontes e ancoragens secundários foram reduzidos para preservar foco.",
    ]

    out["autores_prioritarios_restritos"] = autores
    out["tradicoes_prioritarias_restritas"] = tradicoes
    out["conceitos_classicos_associados_restritos"] = conceitos
    out["temas_agregados_restritos"] = temas
    out["teses_classicas_em_tensao_restritas"] = teses_classicas
    out["tipos_de_adversario_filosofico_restritos"] = adversarios
    out["objecoes_fortes_a_responder_restritas"] = obj_fortes
    out["insuficiencias_tipicas_identificadas_restritas"] = insuf
    out["linhas_de_tratamento_restritas"] = linhas
    out["tipo_de_resposta_exigida_restrita"] = tipo_resp
    out["tipo_de_tensao_com_o_sistema_restrita"] = tipo_tensao
    out["veredito_provisorio_restrito"] = veredito
    out["campo_ids_relacionados_restritos"] = campos
    out["ponte_ids_relacionadas_restritas"] = pontes
    out["ancoragem_ids_relacionadas_restritas"] = ancoragens
    out["focos_restritos"] = derive_focus_tags(item)

    out["adjudicacao_filosofica_restrita"] = {
        "estado_restricao": "restringido",
        "sintese_adjudicada_restrita": sintese,
        "tese_central_restrita": tese_central,
        "teses_de_sustentacao_restritas": teses_sust,
        "distincoes_conceituais_minimas_restritas": dist,
        "objecoes_priorizadas_restritas": obj_prio,
        "articulacao_estrutural_restrita": articulacao_restrita,
        "decisao_de_adjudicacao_restrita": {
            "decisao_principal": first_non_empty_string(
                decisao.get("decisao_principal"),
                "manter_com_restricao"
            ),
            "justificacao": first_non_empty_string(
                decisao.get("justificacao"),
                "A adjudicação foi preservada, mas restringida para disciplina redacional."
            ),
            "veredito_herdado_da_matriz": truncate_list(
                unique_preserve_order(to_text_list(decisao.get("veredito_herdado_da_matriz"))),
                MAX_VEREDITO
            ),
        },
        "plano_de_redacao_restrito": {
            "unidade_de_redacao_recomendada": first_non_empty_string(
                plano_red.get("unidade_de_redacao_recomendada"),
                "subsecção disciplinada"
            ),
            "prioridade_redacional": first_non_empty_string(
                plano_red.get("prioridade_redacional"),
                item.get("grau_de_prioridade"),
                "media"
            ),
            "sequencia_minima_restrita": sequencia,
        },
        "checklist_de_fecho_restrito": checklist,
        "confianca_heuristica_herdada": adj.get("confianca_heuristica"),
        "notas_de_restricao": notas,
        "gerado_em": utc_now_iso(),
    }

    return out, counters


# ============================================================
# Transformação principal
# ============================================================

def transform(input_data: Dict[str, Any]) -> Dict[str, Any]:
    confrontos = input_data.get("confrontos")
    if not isinstance(confrontos, list):
        raise ValueError("Estrutura inesperada: não foi encontrada a lista 'confrontos'.")

    out_confrontos: List[Dict[str, Any]] = []

    totals = {
        "autores_before": 0, "autores_after": 0,
        "tradicoes_before": 0, "tradicoes_after": 0,
        "conceitos_before": 0, "conceitos_after": 0,
        "temas_before": 0, "temas_after": 0,
        "teses_classicas_before": 0, "teses_classicas_after": 0,
        "adversarios_before": 0, "adversarios_after": 0,
        "obj_fortes_before": 0, "obj_fortes_after": 0,
        "insuf_before": 0, "insuf_after": 0,
        "linhas_before": 0, "linhas_after": 0,
        "resp_before": 0, "resp_after": 0,
        "tensao_before": 0, "tensao_after": 0,
        "veredito_before": 0, "veredito_after": 0,
        "campos_before": 0, "campos_after": 0,
        "pontes_before": 0, "pontes_after": 0,
        "anc_before": 0, "anc_after": 0,
        "teses_sust_before": 0, "teses_sust_after": 0,
        "dist_before": 0, "dist_after": 0,
        "obj_prio_before": 0, "obj_prio_after": 0,
        "check_before": 0, "check_after": 0,
        "seq_before": 0, "seq_after": 0,
    }

    ids_restritos: List[str] = []

    for item in confrontos:
        restricted, counters = restrict_single_confronto(item)
        out_confrontos.append(restricted)

        cf_id = str(restricted.get("confronto_id", "")).strip()
        if cf_id:
            ids_restritos.append(cf_id)

        for k in totals:
            totals[k] += counters[k]

    metadata_in = input_data.get("metadata", {})
    fontes_in = input_data.get("fontes", {})
    estat_in = input_data.get("estatisticas", {})

    result = {
        "metadata": {
            "schema_nome": "adjudicacao_confrontos_filosoficos_restrita",
            "schema_versao": "v1",
            "data_geracao": utc_now_iso(),
            "gerado_por_script": "restringir_adjudicacao_confrontos_filosoficos_v1.py",
            "descricao": (
                "Versão redacionalmente restringida da adjudicação dos confrontos filosóficos, "
                "com redução de amplitude temática e preservação de rastreabilidade mínima."
            ),
            "idioma": metadata_in.get("idioma", "pt-PT"),
            "projeto": metadata_in.get("projeto", "DoReal"),
            "estado_global": "restringido",
        },
        "fontes": {
            "fonte_adjudicacao_original": "16_validacao_integral/01_dados/adjudicacao_confrontos_filosoficos_v1.json",
            "fonte_matriz_confronto": fontes_in.get("fonte_matriz_confronto", ""),
            "fonte_proposicoes_enriquecidas": fontes_in.get("fonte_proposicoes_enriquecidas", ""),
            "fonte_matriz_pontes": fontes_in.get("fonte_matriz_pontes", ""),
            "fonte_matriz_ancoragem": fontes_in.get("fonte_matriz_ancoragem", ""),
            "fonte_mapa_campos": fontes_in.get("fonte_mapa_campos", ""),
            "finalidade": "Restrição redacional disciplinada da adjudicação filosófica.",
        },
        "estatisticas": {
            "total_confrontos_restritos": len(out_confrontos),
            "ids_confrontos_restritos": ids_restritos,
            "total_revistos_herdados": estat_in.get("total_revistos"),
            "total_preenchidos_herdados": estat_in.get("total_preenchidos"),
            "total_com_revisao_humana_herdados": estat_in.get("total_com_revisao_humana"),
            "media_confianca_heuristica_herdada": estat_in.get("media_confianca_heuristica"),

            "autores_antes": totals["autores_before"],
            "autores_depois": totals["autores_after"],
            "tradicoes_antes": totals["tradicoes_before"],
            "tradicoes_depois": totals["tradicoes_after"],
            "conceitos_antes": totals["conceitos_before"],
            "conceitos_depois": totals["conceitos_after"],
            "temas_antes": totals["temas_before"],
            "temas_depois": totals["temas_after"],
            "teses_classicas_antes": totals["teses_classicas_before"],
            "teses_classicas_depois": totals["teses_classicas_after"],
            "adversarios_antes": totals["adversarios_before"],
            "adversarios_depois": totals["adversarios_after"],
            "objecoes_fortes_antes": totals["obj_fortes_before"],
            "objecoes_fortes_depois": totals["obj_fortes_after"],
            "insuficiencias_antes": totals["insuf_before"],
            "insuficiencias_depois": totals["insuf_after"],
            "linhas_tratamento_antes": totals["linhas_before"],
            "linhas_tratamento_depois": totals["linhas_after"],
            "tipos_resposta_antes": totals["resp_before"],
            "tipos_resposta_depois": totals["resp_after"],
            "tipos_tensao_antes": totals["tensao_before"],
            "tipos_tensao_depois": totals["tensao_after"],
            "vereditos_antes": totals["veredito_before"],
            "vereditos_depois": totals["veredito_after"],
            "campos_antes": totals["campos_before"],
            "campos_depois": totals["campos_after"],
            "pontes_antes": totals["pontes_before"],
            "pontes_depois": totals["pontes_after"],
            "ancoragens_antes": totals["anc_before"],
            "ancoragens_depois": totals["anc_after"],
            "teses_sustentacao_antes": totals["teses_sust_before"],
            "teses_sustentacao_depois": totals["teses_sust_after"],
            "distincoes_minimas_antes": totals["dist_before"],
            "distincoes_minimas_depois": totals["dist_after"],
            "objecoes_priorizadas_antes": totals["obj_prio_before"],
            "objecoes_priorizadas_depois": totals["obj_prio_after"],
            "checklist_antes": totals["check_before"],
            "checklist_depois": totals["check_after"],
            "sequencia_redacao_antes": totals["seq_before"],
            "sequencia_redacao_depois": totals["seq_after"],
        },
        "enums_documentados": {
            "estado_global": ["restringido"],
            "estado_restricao": ["restringido"],
        },
        "regras_de_validacao": {
            "regras_gerais": [
                "Cada confronto deve manter 'confronto_id'.",
                "Cada confronto deve conter 'adjudicacao_filosofica_restrita'.",
                "As listas restringidas não podem ultrapassar os máximos definidos.",
                "A versão restringida deve preservar foco temático e rastreabilidade mínima.",
            ]
        },
        "confrontos": out_confrontos,
        "observacoes_metodologicas": [
            "A restrição não substitui revisão filosófica humana.",
            "O objetivo desta versão é disciplinar amplitude e preparar redação canónica.",
        ],
    }

    return result


# ============================================================
# Validação
# ============================================================

def validate_output(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    if not isinstance(data, dict):
        return ["O documento final não é um objeto JSON."]

    if "metadata" not in data or not isinstance(data["metadata"], dict):
        errors.append("Falta 'metadata'.")

    if "confrontos" not in data or not isinstance(data["confrontos"], list):
        errors.append("Falta lista 'confrontos'.")
        return errors

    seen_ids = set()

    for idx, item in enumerate(data["confrontos"], start=1):
        if not isinstance(item, dict):
            errors.append(f"Entrada #{idx} não é objeto.")
            continue

        cf_id = item.get("confronto_id")
        if not isinstance(cf_id, str) or not cf_id.strip():
            errors.append(f"Entrada #{idx} sem 'confronto_id'.")
            continue

        if cf_id in seen_ids:
            errors.append(f"ID duplicado: {cf_id}")
        seen_ids.add(cf_id)

        adjr = item.get("adjudicacao_filosofica_restrita")
        if not isinstance(adjr, dict):
            errors.append(f"{cf_id}: falta 'adjudicacao_filosofica_restrita'.")
            continue

        required_adjr = [
            "estado_restricao",
            "sintese_adjudicada_restrita",
            "tese_central_restrita",
            "teses_de_sustentacao_restritas",
            "distincoes_conceituais_minimas_restritas",
            "objecoes_priorizadas_restritas",
            "articulacao_estrutural_restrita",
            "decisao_de_adjudicacao_restrita",
            "plano_de_redacao_restrito",
            "checklist_de_fecho_restrito",
        ]
        for key in required_adjr:
            if key not in adjr:
                errors.append(f"{cf_id}: falta '{key}' em adjudicacao_filosofica_restrita.")

        if len(ensure_list(item.get("autores_prioritarios_restritos"))) > MAX_AUTORES:
            errors.append(f"{cf_id}: excede máximo de autores_prioritarios_restritos.")
        if len(ensure_list(item.get("tradicoes_prioritarias_restritas"))) > MAX_TRADICOES:
            errors.append(f"{cf_id}: excede máximo de tradicoes_prioritarias_restritas.")
        if len(ensure_list(item.get("conceitos_classicos_associados_restritos"))) > MAX_CONCEITOS:
            errors.append(f"{cf_id}: excede máximo de conceitos_classicos_associados_restritos.")
        if len(ensure_list(item.get("temas_agregados_restritos"))) > MAX_TEMAS:
            errors.append(f"{cf_id}: excede máximo de temas_agregados_restritos.")
        if len(ensure_list(item.get("teses_classicas_em_tensao_restritas"))) > MAX_TESES_CLASSICAS:
            errors.append(f"{cf_id}: excede máximo de teses_classicas_em_tensao_restritas.")
        if len(ensure_list(item.get("tipos_de_adversario_filosofico_restritos"))) > MAX_ADVERSARIOS:
            errors.append(f"{cf_id}: excede máximo de tipos_de_adversario_filosofico_restritos.")
        if len(ensure_list(item.get("objecoes_fortes_a_responder_restritas"))) > MAX_OBJECOES_FORTES:
            errors.append(f"{cf_id}: excede máximo de objecoes_fortes_a_responder_restritas.")
        if len(ensure_list(item.get("insuficiencias_tipicas_identificadas_restritas"))) > MAX_INSUFICIENCIAS:
            errors.append(f"{cf_id}: excede máximo de insuficiencias_tipicas_identificadas_restritas.")
        if len(ensure_list(item.get("linhas_de_tratamento_restritas"))) > MAX_LINHAS_TRATAMENTO:
            errors.append(f"{cf_id}: excede máximo de linhas_de_tratamento_restritas.")
        if len(ensure_list(item.get("tipo_de_resposta_exigida_restrita"))) > MAX_TIPO_RESPOSTA:
            errors.append(f"{cf_id}: excede máximo de tipo_de_resposta_exigida_restrita.")
        if len(ensure_list(item.get("tipo_de_tensao_com_o_sistema_restrita"))) > MAX_TIPO_TENSAO:
            errors.append(f"{cf_id}: excede máximo de tipo_de_tensao_com_o_sistema_restrita.")
        if len(ensure_list(item.get("veredito_provisorio_restrito"))) > MAX_VEREDITO:
            errors.append(f"{cf_id}: excede máximo de veredito_provisorio_restrito.")
        if len(ensure_list(item.get("campo_ids_relacionados_restritos"))) > MAX_CAMPOS:
            errors.append(f"{cf_id}: excede máximo de campo_ids_relacionados_restritos.")
        if len(ensure_list(item.get("ponte_ids_relacionadas_restritas"))) > MAX_PONTES:
            errors.append(f"{cf_id}: excede máximo de ponte_ids_relacionadas_restritas.")
        if len(ensure_list(item.get("ancoragem_ids_relacionadas_restritas"))) > MAX_ANCORAGENS:
            errors.append(f"{cf_id}: excede máximo de ancoragem_ids_relacionadas_restritas.")

        if len(ensure_list(adjr.get("teses_de_sustentacao_restritas"))) > MAX_TESES_SUSTENTACAO:
            errors.append(f"{cf_id}: excede máximo de teses_de_sustentacao_restritas.")
        if len(ensure_list(adjr.get("distincoes_conceituais_minimas_restritas"))) > MAX_DISTINCOES_MINIMAS:
            errors.append(f"{cf_id}: excede máximo de distincoes_conceituais_minimas_restritas.")
        if len(ensure_list(adjr.get("objecoes_priorizadas_restritas"))) > MAX_OBJECOES_PRIORIZADAS:
            errors.append(f"{cf_id}: excede máximo de objecoes_priorizadas_restritas.")
        if len(ensure_list(adjr.get("checklist_de_fecho_restrito"))) > MAX_CHECKLIST:
            errors.append(f"{cf_id}: excede máximo de checklist_de_fecho_restrito.")

        art = adjr.get("articulacao_estrutural_restrita", {})
        if isinstance(art, dict):
            if len(ensure_list(art.get("campos_do_real"))) > MAX_CAMPOS:
                errors.append(f"{cf_id}: articulacao_estrutural_restrita.campos_do_real excede máximo.")
            if len(ensure_list(art.get("pontes_entre_niveis"))) > MAX_PONTES:
                errors.append(f"{cf_id}: articulacao_estrutural_restrita.pontes_entre_niveis excede máximo.")
            if len(ensure_list(art.get("ancoragens_cientificas"))) > MAX_ANCORAGENS:
                errors.append(f"{cf_id}: articulacao_estrutural_restrita.ancoragens_cientificas excede máximo.")

    return errors


# ============================================================
# Relatório
# ============================================================

def build_report(data: Dict[str, Any], validation_errors: List[str]) -> str:
    meta = data.get("metadata", {})
    stats = data.get("estatisticas", {})

    lines: List[str] = []
    lines.append("RELATÓRIO — RESTRIÇÃO DA ADJUDICAÇÃO DOS CONFRONTOS FILOSÓFICOS")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"Data de geração: {meta.get('data_geracao', '')}")
    lines.append(f"Schema: {meta.get('schema_nome', '')} {meta.get('schema_versao', '')}")
    lines.append(f"Estado global: {meta.get('estado_global', '')}")
    lines.append("")

    lines.append("ESTATÍSTICAS")
    lines.append("-" * 78)
    for key, value in stats.items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("LIMITES APLICADOS")
    lines.append("-" * 78)
    lines.append(f"- autores_prioritarios: máximo {MAX_AUTORES}")
    lines.append(f"- tradicoes_prioritarias: máximo {MAX_TRADICOES}")
    lines.append(f"- conceitos_classicos_associados: máximo {MAX_CONCEITOS}")
    lines.append(f"- temas_agregados: máximo {MAX_TEMAS}")
    lines.append(f"- teses_classicas_em_tensao: máximo {MAX_TESES_CLASSICAS}")
    lines.append(f"- tipos_de_adversario_filosofico: máximo {MAX_ADVERSARIOS}")
    lines.append(f"- objecoes_fortes_a_responder: máximo {MAX_OBJECOES_FORTES}")
    lines.append(f"- insuficiencias_tipicas_identificadas: máximo {MAX_INSUFICIENCIAS}")
    lines.append(f"- linhas_de_tratamento: máximo {MAX_LINHAS_TRATAMENTO}")
    lines.append(f"- tipo_de_resposta_exigida: máximo {MAX_TIPO_RESPOSTA}")
    lines.append(f"- tipo_de_tensao_com_o_sistema: máximo {MAX_TIPO_TENSAO}")
    lines.append(f"- veredito_provisorio: máximo {MAX_VEREDITO}")
    lines.append(f"- campo_ids_relacionados: máximo {MAX_CAMPOS}")
    lines.append(f"- ponte_ids_relacionadas: máximo {MAX_PONTES}")
    lines.append(f"- ancoragem_ids_relacionadas: máximo {MAX_ANCORAGENS}")
    lines.append(f"- teses_de_sustentacao: máximo {MAX_TESES_SUSTENTACAO}")
    lines.append(f"- distincoes_conceituais_minimas: máximo {MAX_DISTINCOES_MINIMAS}")
    lines.append(f"- objecoes_priorizadas: máximo {MAX_OBJECOES_PRIORIZADAS}")
    lines.append(f"- checklist_de_fecho: máximo {MAX_CHECKLIST}")
    lines.append("")

    lines.append("RESUMO POR CONFRONTO")
    lines.append("-" * 78)
    for item in data.get("confrontos", []):
        cf_id = item.get("confronto_id", "?")
        titulo = first_non_empty_string(item.get("titulo_curto"), item.get("pergunta_central"))
        adjr = item.get("adjudicacao_filosofica_restrita", {})

        n_teses = len(ensure_list(adjr.get("teses_de_sustentacao_restritas")))
        n_dist = len(ensure_list(adjr.get("distincoes_conceituais_minimas_restritas")))
        n_obj = len(ensure_list(adjr.get("objecoes_priorizadas_restritas")))
        n_campos = len(ensure_list(item.get("campo_ids_relacionados_restritos")))
        n_pontes = len(ensure_list(item.get("ponte_ids_relacionadas_restritas")))
        n_anc = len(ensure_list(item.get("ancoragem_ids_relacionadas_restritas")))

        lines.append(f"* {cf_id} — {titulo}")
        lines.append(
            f"  teses={n_teses}; distinções={n_dist}; objeções={n_obj}; "
            f"campos={n_campos}; pontes={n_pontes}; ancoragens={n_anc}"
        )

    lines.append("")
    if validation_errors:
        lines.append("ERROS DE VALIDAÇÃO")
        lines.append("-" * 78)
        for err in validation_errors:
            lines.append(f"- {err}")
    else:
        lines.append("VALIDAÇÃO")
        lines.append("-" * 78)
        lines.append("Concluído sem erros de validação.")

    lines.append("")
    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restringe redacionalmente a adjudicação dos confrontos filosóficos."
    )
    parser.add_argument(
        "--project-root",
        dest="project_root",
        default=None,
        help="Caminho para a pasta 16_validacao_integral.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = infer_project_root(args.project_root)
    paths = build_paths(project_root)

    input_json = paths["input_json"]
    output_json = paths["output_json"]
    output_report = paths["output_report"]

    if not input_json.exists():
        print(f"Erro: ficheiro de entrada não encontrado: {input_json}", file=sys.stderr)
        return 1

    try:
        input_data = load_json(input_json)
        result = transform(input_data)
        validation_errors = validate_output(result)
        report = build_report(result, validation_errors)

        save_json(output_json, result)
        save_text(output_report, report)

        print(f"JSON gerado em: {output_json}")
        print(f"Relatório gerado em: {output_report}")
        if validation_errors:
            print(f"Atenção: foram detetados {len(validation_errors)} erro(s) de validação.")
            return 2

        print("Concluído sem erros de validação.")
        return 0

    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())