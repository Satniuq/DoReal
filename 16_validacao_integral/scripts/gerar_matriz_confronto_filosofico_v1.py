#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gerar_matriz_confronto_filosofico_v1.py

Gera a matriz derivada de confronto filosófico a partir dos artefactos já
produzidos na fase de validação integral pós-árvore.

Fontes principais:
- proposicoes_nucleares_enriquecidas_v1.json
- matriz_pontes_entre_niveis_v1.json
- matriz_ancoragem_cientifica_v1.json
- mapa_campos_do_real_v1.json
- inventario_preliminar_de_problemas_filosoficos_v1.json
- schema_confronto_filosofico_preliminar_v1.json

Objetivos:
- converter o inventário preliminar numa matriz operacional e auditável;
- cruzar automaticamente problemas filosóficos com proposições, campos,
  pontes entre níveis e ancoragens científicas;
- preservar rastreabilidade para blocos, proposições e relações críticas;
- produzir relatório de geração e validação.

Outputs:
- 16_validacao_integral/01_dados/matriz_confronto_filosofico_v1.json
- 16_validacao_integral/02_outputs/relatorio_geracao_matriz_confronto_filosofico_v1.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


# =============================================================================
# CONFIGURAÇÃO CANÓNICA
# =============================================================================

DEFAULT_MAP_RELATIVE = Path(
    "14_mapa_dedutivo/02_fecho_canonico_mapa/outputs/versoes_finais/mapa_dedutivo_canonico_final__vfinal_corrente.json"
)
DEFAULT_TREE_RELATIVE = Path(
    "15_arvore_do_pensamento/01_dados/arvore_do_pensamento_v1_fecho_superior.json"
)
DEFAULT_IMPACT_RELATIVE = Path(
    "14_mapa_dedutivo/impacto_fragmentos_no_mapa.json"
)
DEFAULT_ARCH_RELATIVE = Path(
    "14_mapa_dedutivo/02_mapa_dedutivo_arquitetura_fragmentos.json"
)
DEFAULT_ARGUMENTOS_RELATIVE = Path(
    "13_Meta_Indice/indice/argumentos/argumentos_unificados.json"
)
DEFAULT_INDICE_PERCURSOS_RELATIVE = Path(
    "13_Meta_Indice/indice/indice_por_percurso.json"
)

DEFAULT_INPUT_PROPOSICOES_RELATIVE = Path(
    "16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json"
)
DEFAULT_INPUT_PONTES_RELATIVE = Path(
    "16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json"
)
DEFAULT_INPUT_ANCORAGEM_RELATIVE = Path(
    "16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json"
)
DEFAULT_INPUT_CAMPOS_RELATIVE = Path(
    "16_validacao_integral/01_dados/mapa_campos_do_real_v1.json"
)
DEFAULT_INPUT_INVENTARIO_RELATIVE = Path(
    "16_validacao_integral/01_dados/inventario_preliminar_de_problemas_filosoficos_v1.json"
)
DEFAULT_INPUT_SCHEMA_RELATIVE = Path(
    "16_validacao_integral/01_dados/schema_confronto_filosofico_preliminar_v1.json"
)

DEFAULT_OUTPUT_JSON_RELATIVE = Path(
    "16_validacao_integral/01_dados/matriz_confronto_filosofico_v1.json"
)
DEFAULT_REPORT_RELATIVE = Path(
    "16_validacao_integral/02_outputs/relatorio_geracao_matriz_confronto_filosofico_v1.txt"
)


# =============================================================================
# ENUMS / CONSTANTES
# =============================================================================

VALID_ESTADO_GLOBAL = {
    "em_construcao",
    "extraido",
    "enriquecido",
    "validado",
    "integrado",
}

VALID_TIPO_PROBLEMA = {
    "ontologico",
    "fenomenologico",
    "antropologico",
    "filosofia_da_mente",
    "epistemologico",
    "semantico_linguistico",
    "etico_pratico",
    "pratico_etico",
    "social_politico",
    "social_historico",
    "metaestrutural",
    "transversal",
}

VALID_NIVEL_ARQUITETONICO = {
    "fundacional",
    "estrutural",
    "regional",
    "de_articulacao",
    "de_passagem",
    "integrativo",
    "pratico_normativo",
    "metaestrutural",
    "meta_sistemico",
    "terminal",
}

VALID_GRAU_CENTRALIDADE = {"local", "medio", "alto", "nuclear", "estrutural"}
VALID_GRAU_PRIORIDADE = {"baixa", "media", "alta", "estrutural"}
VALID_GRAU_RISCO = {"baixo", "medio", "alto", "critico"}
VALID_GRAU_COBERTURA = {"incipiente", "parcial", "forte", "ampla", "estruturante", "transversal"}

VALID_TIPO_TENSAO = {
    "compatibilidade_forte",
    "compatibilidade_parcial",
    "tensao_produtiva",
    "tensao_forte",
    "incompatibilidade_restrita",
    "incompatibilidade_forte",
    "indeterminacao",
    "indeterminacao_ainda_aberta",
}

VALID_TIPO_VEREDITO = {
    "preservar",
    "reformular",
    "integrar",
    "restringir",
    "criticar",
    "deixar_em_aberto",
}

VALID_ESTADO_ITEM = {
    "por_preencher",
    "preenchido",
    "revisto",
    "validado",
    "integrado",
}

RISK_ORDER = ["baixo", "medio", "alto", "critico"]
PRIORITY_ORDER = ["baixa", "media", "alta", "estrutural"]
CENTRALITY_ORDER = ["local", "medio", "alto", "nuclear", "estrutural"]
COVERAGE_ORDER = ["incipiente", "parcial", "forte", "ampla", "estruturante", "transversal"]

STOPWORDS = {
    "a", "o", "e", "de", "do", "da", "das", "dos", "um", "uma", "que", "como", "sem", "com", "na",
    "no", "nas", "nos", "por", "para", "ou", "ao", "aos", "as", "os", "se", "sob", "entre", "toda",
    "todo", "mais", "menos", "ser", "real", "sobre", "qual", "quais", "onde", "quando", "porque", "isso",
    "isto", "num", "numa", "sua", "seu", "suas", "seus", "ha", "há", "ja", "já", "nao", "não", "mera",
    "mero", "toda", "todo", "qualquer", "algum", "alguma", "algo", "pela", "pelas", "pelo", "pelos",
}

THEME_ALIASES = {
    "vida_boa": ["vida", "boa", "vida_boa", "eudaimonia"],
    "regionalizacao_do_real": ["regionalizacao", "regionalizacao_do_real", "campo", "escala", "nivel"],
    "humano_situado": ["humano", "situado", "sujeito", "agente", "encarnado"],
    "corporeidade": ["corpo", "corporeidade", "encarnacao", "encarnado"],
    "consciencia": ["consciencia", "consciência"],
    "simbolo": ["simbolo", "simbolo", "simbólico", "simbolico"],
    "criterio": ["criterio", "critério", "correcao", "correção", "verdade", "erro"],
    "acao": ["acao", "ação", "agir", "pratica", "prática"],
    "dano": ["dano", "mal", "bem", "vulnerabilidade"],
    "normatividade": ["normatividade", "dever", "dever_ser", "obrigacao", "obrigação"],
    "dignidade": ["dignidade", "valor", "respeito"],
    "memoria": ["memoria", "memória", "tempo", "duracao", "duração", "identidade"],
    "representacao": ["representacao", "representação", "apreensao", "apreensão"],
    "linguagem": ["linguagem", "simbolo", "significado", "sentido", "mediação", "mediacao"],
    "potencialidade": ["potencialidade", "potencia", "potência", "atualizacao", "atualização", "mudanca", "mudança"],
}

PROBLEM_GROUP_HINTS = {
    "UCF01": range(1, 23),
    "UCF02": range(23, 31),
    "UCF03": range(1, 25),
    "UCF04": range(23, 38),
    "UCF05": range(23, 35),
    "UCF06": range(27, 38),
    "UCF07": range(30, 52),
    "UCF08": range(13, 38),
    "UCF09": range(36, 43),
    "UCF10": range(38, 48),
    "UCF11": range(44, 52),
    "UCF12": range(38, 52),
    "UCF13": range(48, 52),
}


# =============================================================================
# UTILITÁRIOS GERAIS
# =============================================================================


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()



def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)



def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")



def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}



def safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]



def normalize_spaces(text: str) -> str:
    return " ".join((text or "").strip().split())



def unique_preserve(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for v in values:
        if not isinstance(v, str):
            continue
        vv = v.strip()
        if not vv or vv in seen:
            continue
        seen.add(vv)
        out.append(vv)
    return out



def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()



def tokenize_text(value: str) -> Set[str]:
    text = normalize_text(value)
    tokens = set(re.findall(r"[a-z0-9_]+", text))
    out = {t for t in tokens if len(t) > 1 and t not in STOPWORDS}
    expanded: Set[str] = set(out)
    for t in list(out):
        expanded.update(THEME_ALIASES.get(t, []))
    return {normalize_text(x).replace(" ", "_") for x in expanded if x}



def max_order_value(current: str, candidate: str, order: Sequence[str], default: str) -> str:
    cur = current if current in order else default
    cand = candidate if candidate in order else default
    return order[max(order.index(cur), order.index(cand))]



def max_risco(current: str, candidate: str) -> str:
    return max_order_value(current, candidate, RISK_ORDER, "baixo")



def max_prioridade(current: str, candidate: str) -> str:
    return max_order_value(current, candidate, PRIORITY_ORDER, "baixa")



def max_centralidade(current: str, candidate: str) -> str:
    return max_order_value(current, candidate, CENTRALITY_ORDER, "local")



def max_cobertura(current: str, candidate: str) -> str:
    return max_order_value(current, candidate, COVERAGE_ORDER, "parcial")



def project_root_from_explicit_or_cwd(explicit_root: Optional[Path]) -> Path:
    if explicit_root:
        return explicit_root.resolve()

    script_path = Path(__file__).resolve()
    candidates = [
        script_path.parent.parent.parent,
        script_path.parent.parent,
        Path.cwd(),
        Path.cwd().parent,
        Path.cwd().parent.parent,
    ]

    for cand in candidates:
        if (cand / DEFAULT_INPUT_PROPOSICOES_RELATIVE).exists():
            return cand.resolve()

    return script_path.parent.parent.parent



def resolve_relative(project_root: Path, relative_path: Path) -> Path:
    path = (project_root / relative_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {path}")
    return path



def order_from_id(value: str, prefix: str) -> int:
    m = re.match(rf"^{re.escape(prefix)}(\d+)$", value or "")
    if not m:
        return 0
    return int(m.group(1))


# =============================================================================
# ÍNDICES E HEURÍSTICAS
# =============================================================================


def build_indexes(
    proposicoes: List[Dict[str, Any]],
    pontes: List[Dict[str, Any]],
    ancoragens: List[Dict[str, Any]],
    campos: List[Dict[str, Any]],
) -> Dict[str, Any]:
    prop_by_id = {str(p.get("proposicao_id")): p for p in proposicoes}

    ponte_by_prop: Dict[str, Set[str]] = defaultdict(set)
    for ponte in pontes:
        ponte_id = str(ponte.get("ponte_id", "")).strip()
        for pid in safe_list(ponte.get("proposicao_ids")):
            ponte_by_prop[str(pid)].add(ponte_id)

    anchor_by_prop: Dict[str, Set[str]] = defaultdict(set)
    for entrada in ancoragens:
        entrada_id = str(entrada.get("entrada_id", "")).strip()
        for pid in safe_list(entrada.get("proposicao_ids")):
            anchor_by_prop[str(pid)].add(entrada_id)

    campo_by_prop: Dict[str, Set[str]] = defaultdict(set)
    for campo in campos:
        campo_id = str(campo.get("campo_id", "")).strip()
        for pid in safe_list(campo.get("proposicao_ids")):
            campo_by_prop[str(pid)].add(campo_id)

    prop_tokens: Dict[str, Set[str]] = {}
    prop_domains: Dict[str, str] = {}
    for prop in proposicoes:
        pid = str(prop.get("proposicao_id"))
        tokens: Set[str] = set()
        tokens.update(tokenize_text(str(prop.get("texto", ""))))
        tokens.update(tokenize_text(str(prop.get("texto_curto", ""))))
        confronto = safe_dict(prop.get("confronto_filosofico"))
        for tema in safe_list(confronto.get("temas_de_confronto")):
            tokens.update(tokenize_text(str(tema)))
        for q in safe_list(confronto.get("questoes_abertas")):
            tokens.update(tokenize_text(str(q)))
        classificacao = safe_dict(prop.get("classificacao_filosofica_inicial"))
        dominio = str(classificacao.get("dominio_principal", "")).strip()
        prop_domains[pid] = dominio
        tokens.update(tokenize_text(dominio))
        prop_tokens[pid] = tokens

    return {
        "prop_by_id": prop_by_id,
        "ponte_by_prop": ponte_by_prop,
        "anchor_by_prop": anchor_by_prop,
        "campo_by_prop": campo_by_prop,
        "prop_tokens": prop_tokens,
        "prop_domains": prop_domains,
    }



def problem_tokens(problem: Dict[str, Any]) -> Set[str]:
    tokens: Set[str] = set()
    keys = [
        "titulo_curto",
        "pergunta_central",
        "descricao_canonica",
        "posicao_provavel_do_sistema",
        "observacoes_metodologicas",
    ]
    for key in keys:
        tokens.update(tokenize_text(str(problem.get(key, ""))))

    for key in [
        "objetos_filosoficos_principais",
        "operacoes_filosoficas_implicadas",
        "subproblemas",
        "perguntas_associadas",
        "familias_filosoficas_relevantes",
        "autores_relevantes",
        "conceitos_classicos_associados",
        "teses_classicas_em_tensao",
        "tipos_de_adversario_filosofico",
    ]:
        for item in safe_list(problem.get(key)):
            tokens.update(tokenize_text(str(item)))
    return tokens



def domain_bonus(problem: Dict[str, Any], dominio: str) -> int:
    tipo = str(problem.get("tipo_de_problema", "")).strip()
    dominio = normalize_text(dominio)
    if not dominio:
        return 0
    if dominio == "ontologia" and tipo in {"ontologico", "metaestrutural", "transversal"}:
        return 2
    if dominio in {"fenomenologia", "antropologia_filosofica"} and tipo in {"fenomenologico", "antropologico", "filosofia_da_mente"}:
        return 2
    if dominio in {"epistemologia", "logica"} and tipo == "epistemologico":
        return 2
    if dominio in {"linguagem", "filosofia_da_linguagem"} and tipo == "semantico_linguistico":
        return 2
    if dominio == "etica" and tipo in {"etico_pratico", "social_politico"}:
        return 2
    return 0



def score_proposition_for_problem(
    pid: str,
    prop: Dict[str, Any],
    problem: Dict[str, Any],
    problem_tokens_set: Set[str],
    indexes: Dict[str, Any],
) -> int:
    score = 0
    if pid in set(safe_list(problem.get("proposicao_ids_relacionadas"))):
        score += 100

    prop_tokens = indexes["prop_tokens"].get(pid, set())
    overlap = prop_tokens & problem_tokens_set
    score += min(len(overlap), 8) * 2

    prop_campos = indexes["campo_by_prop"].get(pid, set())
    problem_campos = set(safe_list(problem.get("campo_ids_relacionados")))
    if prop_campos & problem_campos:
        score += 3

    prop_pontes = indexes["ponte_by_prop"].get(pid, set())
    problem_pontes = set(safe_list(problem.get("ponte_ids_relacionadas")))
    if prop_pontes & problem_pontes:
        score += 2

    prop_anchors = indexes["anchor_by_prop"].get(pid, set())
    problem_anchors = set(safe_list(problem.get("ancoragem_ids_relacionadas")))
    if prop_anchors & problem_anchors:
        score += 2

    score += domain_bonus(problem, indexes["prop_domains"].get(pid, ""))

    ordem = int(prop.get("ordem_global") or 0)
    hint = PROBLEM_GROUP_HINTS.get(str(problem.get("problema_id")))
    if hint and ordem in hint:
        score += 2

    if str(problem.get("nivel_arquitetonico")) == "metaestrutural":
        if prop_pontes:
            score += 1
        if prop_campos:
            score += 1

    return score



def infer_best_problem_links(
    problems: List[Dict[str, Any]],
    proposicoes: List[Dict[str, Any]],
    indexes: Dict[str, Any],
) -> Dict[str, Set[str]]:
    links: Dict[str, Set[str]] = {str(p.get("problema_id")): set(safe_list(p.get("proposicao_ids_relacionadas"))) for p in problems}
    token_cache = {str(p.get("problema_id")): problem_tokens(p) for p in problems}

    for prop in proposicoes:
        pid = str(prop.get("proposicao_id"))
        validacao = safe_dict(prop.get("validacao_integral"))
        if not bool(validacao.get("precisa_confronto_filosofico", False)):
            continue

        scored: List[Tuple[int, str]] = []
        for problem in problems:
            prob_id = str(problem.get("problema_id"))
            score = score_proposition_for_problem(pid, prop, problem, token_cache[prob_id], indexes)
            if score > 0:
                scored.append((score, prob_id))
        scored.sort(key=lambda x: (-x[0], x[1]))
        if not scored:
            continue

        best_score = scored[0][0]
        links[scored[0][1]].add(pid)
        for score, prob_id in scored[1:3]:
            if score >= 4 and score >= best_score - 2:
                links[prob_id].add(pid)

    # Problemas metaestruturais sem proposições explícitas herdam cobertura das pontes/campos associados.
    ponte_to_props: Dict[str, Set[str]] = defaultdict(set)
    for pid, ponte_ids in indexes["ponte_by_prop"].items():
        for ponte_id in ponte_ids:
            ponte_to_props[ponte_id].add(pid)

    campo_to_props: Dict[str, Set[str]] = defaultdict(set)
    for pid, campo_ids in indexes["campo_by_prop"].items():
        for campo_id in campo_ids:
            campo_to_props[campo_id].add(pid)

    for problem in problems:
        prob_id = str(problem.get("problema_id"))
        if links.get(prob_id):
            continue
        if str(problem.get("nivel_arquitetonico")) != "metaestrutural":
            continue
        inherited: Set[str] = set()
        for ponte_id in safe_list(problem.get("ponte_ids_relacionadas")):
            inherited.update(ponte_to_props.get(str(ponte_id), set()))
        for campo_id in safe_list(problem.get("campo_ids_relacionados")):
            inherited.update(campo_to_props.get(str(campo_id), set()))
        if inherited:
            links[prob_id] = inherited

    return links



def build_reverse_indexes(entries: List[Dict[str, Any]], item_id_key: str, prop_key: str) -> Dict[str, Dict[str, Any]]:
    by_id = {str(item.get(item_id_key)): item for item in entries}
    by_prop: Dict[str, Set[str]] = defaultdict(set)
    for item in entries:
        item_id = str(item.get(item_id_key))
        for pid in safe_list(item.get(prop_key)):
            by_prop[str(pid)].add(item_id)
    return {"by_id": by_id, "by_prop": by_prop}



def infer_objecoes(problem: Dict[str, Any]) -> List[str]:
    base = unique_preserve(list(safe_list(problem.get("teses_classicas_em_tensao"))) + list(safe_list(problem.get("insuficiencias_tipicas_identificadas"))))
    tipo = str(problem.get("tipo_de_problema", ""))
    extras: List[str] = []
    if tipo == "ontologico":
        extras = [
            "Explicar por que razão a unidade do real não apaga diferença, relação e regionalização.",
            "Justificar a passagem entre estrutura, campo e determinação sem reificação indevida.",
        ]
    elif tipo == "fenomenologico":
        extras = [
            "Distinguir manifestação de mera aparência subjetiva ou construção linguística.",
            "Explicar o vínculo entre presença, apreensão e determinação do real.",
        ]
    elif tipo == "filosofia_da_mente":
        extras = [
            "Evitar tanto o dualismo forte como o reducionismo eliminativista sobre consciência e reflexividade.",
            "Explicar como sujeito, corpo e memória se articulam sem colapso identitário.",
        ]
    elif tipo == "semantico_linguistico":
        extras = [
            "Mostrar como linguagem e símbolo mediam o acesso ao real sem dissolver referência.",
            "Distinguir sentido, representação e critério de correção.",
        ]
    elif tipo == "epistemologico":
        extras = [
            "Fundar critério, verdade e correção sem cair em circularidade ou convencionalismo puro.",
            "Explicar erro sem anular a possibilidade de objetividade situada.",
        ]
    elif tipo in {"etico_pratico", "social_politico"}:
        extras = [
            "Justificar a passagem entre ação situada, dano, valor e normatividade sem salto ilegítimo.",
            "Articular responsabilidade, instituições e vida boa com vulnerabilidade e mediação histórica.",
        ]
    elif tipo == "metaestrutural":
        extras = [
            "Explicar como o sistema fecha sem arbitrariedade e sem circularidade viciosa.",
            "Justificar a ordem das passagens entre ontologia, vida, cognição, linguagem e normatividade.",
        ]
    return unique_preserve(base + extras)



def infer_estrategia(problem: Dict[str, Any], prop_ids: List[str], ponte_ids: List[str], anchor_ids: List[str]) -> List[str]:
    strategy: List[str] = []
    if prop_ids:
        strategy.append("Reconstruir o núcleo argumentativo a partir das proposições relacionadas.")
    if ponte_ids:
        strategy.append("Trabalhar explicitamente as passagens entre níveis implicadas nas pontes relacionadas.")
    if anchor_ids:
        strategy.append("Usar a ancoragem científica apenas como restrição e compatibilidade, não como substituição do confronto filosófico.")
    if str(problem.get("grau_de_risco")) in {"alto", "critico"}:
        strategy.append("Responder primeiro às objeções fortes e às ambiguidades terminológicas de maior risco.")
    if bool(problem.get("precisa_capitulo_proprio", False)):
        strategy.append("Reservar tratamento autónomo em capítulo ou subcapítulo dedicado.")
    if not strategy:
        strategy.append("Consolidar distinções conceptuais e explicitar a posição do sistema perante as tradições relevantes.")
    return unique_preserve(strategy)



def infer_veredito(problem: Dict[str, Any]) -> List[str]:
    veredito: List[str] = []
    tensoes = set(str(x) for x in safe_list(problem.get("tipo_de_tensao_com_o_sistema")))
    if "compatibilidade_forte" in tensoes:
        veredito.append("preservar")
    if "compatibilidade_parcial" in tensoes or "tensao_produtiva" in tensoes:
        veredito.append("integrar")
    if "tensao_forte" in tensoes:
        veredito.append("reformular")
    if "incompatibilidade_restrita" in tensoes or "incompatibilidade_forte" in tensoes:
        veredito.append("restringir")
        veredito.append("criticar")
    if not veredito:
        veredito.append("deixar_em_aberto")
    return unique_preserve(veredito)



def bool_map(problem: Dict[str, Any], bridge_ids: List[str], anchor_ids: List[str]) -> Dict[str, bool]:
    return {
        "precisa_reconstrucao_argumentativa": True,
        "precisa_distincao_conceitual": True,
        "precisa_resposta_a_objecoes": True,
        "precisa_articulacao_com_pontes": bool(bridge_ids),
        "precisa_articulacao_com_ciencia": bool(anchor_ids),
        "precisa_revisao_humana": bool(problem.get("necessita_revisao_humana", False)),
    }


# =============================================================================
# GERAÇÃO DA MATRIZ
# =============================================================================


def generate_matrix(
    proposicoes_doc: Dict[str, Any],
    pontes_doc: Dict[str, Any],
    ancoragem_doc: Dict[str, Any],
    campos_doc: Dict[str, Any],
    inventario_doc: Dict[str, Any],
    schema_doc: Dict[str, Any],
) -> Dict[str, Any]:
    proposicoes = safe_list(proposicoes_doc.get("proposicoes"))
    pontes = safe_list(pontes_doc.get("pontes"))
    ancoragens = safe_list(ancoragem_doc.get("entradas"))
    campos = safe_list(campos_doc.get("campos"))
    problems = safe_list(inventario_doc.get("problemas"))

    indexes = build_indexes(proposicoes, pontes, ancoragens, campos)
    ponte_index = build_reverse_indexes(pontes, "ponte_id", "proposicao_ids")
    anchor_index = build_reverse_indexes(ancoragens, "entrada_id", "proposicao_ids")
    campo_index = build_reverse_indexes(campos, "campo_id", "proposicao_ids")

    prop_links = infer_best_problem_links(problems, proposicoes, indexes)

    confrontos: List[Dict[str, Any]] = []
    indice_por_proposicao: Dict[str, List[str]] = defaultdict(list)

    for idx, problem in enumerate(problems, start=1):
        problema_id = str(problem.get("problema_id"))
        confronto_id = f"CF{idx:02d}"

        proposition_ids = sorted(
            prop_links.get(problema_id, set()),
            key=lambda x: order_from_id(x, "P"),
        )
        blocos = sorted(
            {str(indexes["prop_by_id"][pid].get("bloco_id")) for pid in proposition_ids if pid in indexes["prop_by_id"]},
            key=lambda x: order_from_id(x, "B"),
        )

        campo_ids = set(str(x) for x in safe_list(problem.get("campo_ids_relacionados")))
        ponte_ids = set(str(x) for x in safe_list(problem.get("ponte_ids_relacionadas")))
        ancoragem_ids = set(str(x) for x in safe_list(problem.get("ancoragem_ids_relacionadas")))

        for pid in proposition_ids:
            campo_ids.update(campo_index["by_prop"].get(pid, set()))
            ponte_ids.update(ponte_index["by_prop"].get(pid, set()))
            ancoragem_ids.update(anchor_index["by_prop"].get(pid, set()))

        campos_do_real = unique_preserve(
            problem.get("campos_do_real_relacionados", [])
            + [
                cpr
                for campo_id in sorted(campo_ids, key=lambda x: order_from_id(x, "CR"))
                for cpr in safe_list(safe_dict(campo_index["by_id"].get(campo_id, {})).get("campos_principais"))
            ]
        )

        autores = unique_preserve(
            safe_list(problem.get("autores_relevantes"))
            + [
                autor
                for pid in proposition_ids
                for autor in safe_list(safe_dict(indexes["prop_by_id"].get(pid, {})).get("confronto_filosofico", {}).get("autores_prioritarios"))
            ]
        )
        tradicoes = unique_preserve(
            safe_list(problem.get("familias_filosoficas_relevantes"))
            + [
                trad
                for pid in proposition_ids
                for trad in safe_list(safe_dict(indexes["prop_by_id"].get(pid, {})).get("confronto_filosofico", {}).get("tradicoes_prioritarias"))
            ]
        )
        temas_agregados = unique_preserve(
            list(safe_list(problem.get("objetos_filosoficos_principais")))
            + [
                tema
                for pid in proposition_ids
                for tema in safe_list(safe_dict(indexes["prop_by_id"].get(pid, {})).get("confronto_filosofico", {}).get("temas_de_confronto"))
            ]
        )

        necessita_revisao_humana = bool(problem.get("necessita_revisao_humana", False))
        motivo_revisao_humana = str(problem.get("motivo_revisao_humana", "")).strip()
        for pid in proposition_ids:
            estado = safe_dict(indexes["prop_by_id"].get(pid, {})).get("estado_trabalho", {})
            if safe_dict(estado).get("necessita_revisao_humana"):
                necessita_revisao_humana = True
                reason = str(safe_dict(estado).get("motivo_revisao_humana", "")).strip()
                if reason:
                    motivo_revisao_humana = reason
                    break

        entry = {
            "confronto_id": confronto_id,
            "problema_id": problema_id,
            "titulo_curto": str(problem.get("titulo_curto", "")).strip(),
            "tipo_de_problema": str(problem.get("tipo_de_problema", "")).strip(),
            "nivel_arquitetonico": str(problem.get("nivel_arquitetonico", "")).strip(),
            "pergunta_central": str(problem.get("pergunta_central", "")).strip(),
            "descricao_do_confronto": str(problem.get("descricao_canonica", "")).strip(),
            "subproblemas": safe_list(problem.get("subproblemas")),
            "proposicao_ids": proposition_ids,
            "blocos_relacionados": blocos,
            "campos_do_real_relacionados": campos_do_real,
            "campo_ids_relacionados": sorted(campo_ids, key=lambda x: order_from_id(x, "CR")),
            "ponte_ids_relacionadas": sorted(ponte_ids, key=lambda x: order_from_id(x, "PN")),
            "ancoragem_ids_relacionadas": sorted(ancoragem_ids, key=lambda x: order_from_id(x, "AC")),
            "autores_prioritarios": autores,
            "tradicoes_prioritarias": tradicoes,
            "temas_agregados": temas_agregados,
            "conceitos_classicos_associados": safe_list(problem.get("conceitos_classicos_associados")),
            "teses_classicas_em_tensao": safe_list(problem.get("teses_classicas_em_tensao")),
            "tipos_de_adversario_filosofico": safe_list(problem.get("tipos_de_adversario_filosofico")),
            "objecoes_fortes_a_responder": infer_objecoes(problem),
            "insuficiencias_tipicas_identificadas": safe_list(problem.get("insuficiencias_tipicas_identificadas")),
            "resposta_provavel_do_sistema": str(problem.get("posicao_provavel_do_sistema", "")).strip(),
            "linhas_de_tratamento": infer_estrategia(problem, proposition_ids, sorted(ponte_ids), sorted(ancoragem_ids)),
            "tipo_de_resposta_exigida": safe_list(problem.get("tipo_de_resposta_exigida")),
            "tipo_de_tensao_com_o_sistema": safe_list(problem.get("tipo_de_tensao_com_o_sistema")),
            "veredito_provisorio": infer_veredito(problem),
            "grau_de_centralidade": str(problem.get("grau_de_centralidade", "medio")).strip(),
            "grau_de_prioridade": str(problem.get("grau_de_prioridade", "media")).strip(),
            "grau_de_risco": str(problem.get("grau_de_risco", "medio")).strip(),
            "grau_de_cobertura_no_projeto": str(problem.get("grau_de_cobertura_no_projeto", "parcial")).strip(),
            "falta_tratamento_academico": bool(problem.get("falta_tratamento_academico", False)),
            "precisa_capitulo_proprio": bool(problem.get("precisa_capitulo_proprio", False)),
            "precisa_subcapitulo": bool(problem.get("precisa_subcapitulo", False)),
            "precisa_argumento_canonico": bool(problem.get("precisa_argumento_canonico", False)),
            "exige_resposta_canonica": bool(problem.get("exige_resposta_canonica", False)),
            "necessidades_de_trabalho": bool_map(problem, sorted(ponte_ids), sorted(ancoragem_ids)),
            "necessita_revisao_humana": necessita_revisao_humana,
            "motivo_revisao_humana": motivo_revisao_humana,
            "lacunas_identificadas": safe_list(problem.get("lacunas_identificadas")),
            "estado_item": "por_preencher",
            "observacoes": str(problem.get("observacoes_metodologicas", "")).strip(),
        }
        confrontos.append(entry)
        for pid in proposition_ids:
            indice_por_proposicao[pid].append(confronto_id)

    props_need_confronto = [
        str(p.get("proposicao_id"))
        for p in proposicoes
        if bool(safe_dict(p.get("validacao_integral")).get("precisa_confronto_filosofico", False))
    ]
    covered = {pid for pid, ids in indice_por_proposicao.items() if ids}
    uncovered = sorted(set(props_need_confronto) - covered, key=lambda x: order_from_id(x, "P"))

    estatisticas = {
        "total_confrontos": len(confrontos),
        "total_problemas_inventariados": len(problems),
        "total_proposicoes_que_precisam_confronto": len(props_need_confronto),
        "total_proposicoes_cobertas": len(covered),
        "total_proposicoes_sem_cobertura": len(uncovered),
        "proposicoes_sem_cobertura": uncovered,
        "total_confrontos_com_revisao_humana": sum(1 for c in confrontos if c["necessita_revisao_humana"]),
        "total_confrontos_com_resposta_canonica": sum(1 for c in confrontos if c["exige_resposta_canonica"]),
        "total_confrontos_com_capitulo_proprio": sum(1 for c in confrontos if c["precisa_capitulo_proprio"]),
        "total_confrontos_com_pontes": sum(1 for c in confrontos if c["ponte_ids_relacionadas"]),
        "total_confrontos_com_ancoragem": sum(1 for c in confrontos if c["ancoragem_ids_relacionadas"]),
        "total_confrontos_de_risco_alto_ou_critico": sum(1 for c in confrontos if c["grau_de_risco"] in {"alto", "critico"}),
        "total_confrontos_metaestruturais": sum(1 for c in confrontos if c["tipo_de_problema"] == "metaestrutural" or c["nivel_arquitetonico"] in {"metaestrutural", "meta_sistemico"}),
        "confrontos_por_tipo_de_problema": dict(Counter(c["tipo_de_problema"] for c in confrontos)),
    }

    enums_documentados = {
        "estado_global": sorted(VALID_ESTADO_GLOBAL),
        "tipo_de_problema": sorted(VALID_TIPO_PROBLEMA),
        "nivel_arquitetonico": sorted(VALID_NIVEL_ARQUITETONICO),
        "grau_de_centralidade": sorted(VALID_GRAU_CENTRALIDADE),
        "grau_de_prioridade": sorted(VALID_GRAU_PRIORIDADE),
        "grau_de_risco": sorted(VALID_GRAU_RISCO),
        "grau_de_cobertura_no_projeto": sorted(VALID_GRAU_COBERTURA),
        "tipo_de_tensao": sorted(VALID_TIPO_TENSAO),
        "tipo_de_veredito": sorted(VALID_TIPO_VEREDITO),
        "estado_item": sorted(VALID_ESTADO_ITEM),
    }

    regras = {
        "regras_gerais": [
            "Cada confronto deve referir exatamente um problema_id existente no inventário preliminar.",
            "Cada confronto deve manter pelo menos um de: proposicao_ids, campo_ids_relacionados, ponte_ids_relacionadas ou ancoragem_ids_relacionadas.",
            "Todos os IDs referidos devem existir nos ficheiros de origem desta fase.",
            "Confrontos de nível metaestrutural podem agregar proposições herdadas das pontes e dos campos relacionados.",
            "O confronto filosófico não substitui ancoragem científica nem ponte entre níveis; integra-as quando relevantes.",
        ]
    }

    output = {
        "metadata": {
            "schema_nome": "matriz_confronto_filosofico_v1",
            "schema_versao": "1.0",
            "data_geracao": utc_now_iso(),
            "gerado_por_script": "gerar_matriz_confronto_filosofico_v1.py",
            "descricao": "Matriz derivada de confronto filosófico gerada a partir do inventário preliminar e das matrizes auxiliares da fase de validação integral.",
            "idioma": "pt-PT",
            "projeto": "DoReal / 16_validacao_integral",
            "estado_global": "extraido",
        },
        "fontes": {
            "fonte_proposicoes_enriquecidas": "16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json",
            "fonte_matriz_pontes": "16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json",
            "fonte_matriz_ancoragem": "16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json",
            "fonte_mapa_campos": "16_validacao_integral/01_dados/mapa_campos_do_real_v1.json",
            "fonte_inventario_preliminar": "16_validacao_integral/01_dados/inventario_preliminar_de_problemas_filosoficos_v1.json",
            "fonte_schema_preliminar": "16_validacao_integral/01_dados/schema_confronto_filosofico_preliminar_v1.json",
            "finalidade": "Operacionalizar a batalha filosófica do sistema com rastreabilidade para proposições, campos, pontes e ancoragens.",
        },
        "estatisticas": estatisticas,
        "enums_documentados": enums_documentados,
        "regras_de_validacao": regras,
        "confrontos": confrontos,
        "indice_auxiliar_por_proposicao": dict(sorted(indice_por_proposicao.items(), key=lambda kv: order_from_id(kv[0], "P"))),
        "observacoes_metodologicas": {
            "criterio_de_geracao": "Cada entrada nasce do inventário preliminar, mas é enriquecida por ligação automática a proposições, campos, pontes e ancoragens desta fase.",
            "fonte_das_categorias": "As categorias de problema vêm do inventário preliminar e do schema auxiliar; os vínculos concretos são reatribuídos por heurísticas de sobreposição temática, campo, ponte e domínio filosófico.",
            "schema_auxiliar_consultado": bool(schema_doc),
        },
    }
    return output


# =============================================================================
# VALIDAÇÃO
# =============================================================================


def validate_output(
    output: Dict[str, Any],
    proposicoes_doc: Dict[str, Any],
    pontes_doc: Dict[str, Any],
    ancoragem_doc: Dict[str, Any],
    campos_doc: Dict[str, Any],
    inventario_doc: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    props = {str(p.get("proposicao_id")) for p in safe_list(proposicoes_doc.get("proposicoes"))}
    pontes = {str(p.get("ponte_id")) for p in safe_list(pontes_doc.get("pontes"))}
    anchors = {str(a.get("entrada_id")) for a in safe_list(ancoragem_doc.get("entradas"))}
    campos = {str(c.get("campo_id")) for c in safe_list(campos_doc.get("campos"))}
    problemas = {str(p.get("problema_id")) for p in safe_list(inventario_doc.get("problemas"))}

    metadata = safe_dict(output.get("metadata"))
    if metadata.get("estado_global") not in VALID_ESTADO_GLOBAL:
        errors.append("metadata.estado_global inválido")

    confrontos = safe_list(output.get("confrontos"))
    seen_ids: Set[str] = set()
    for idx, entry in enumerate(confrontos, start=1):
        cid = str(entry.get("confronto_id", "")).strip()
        if not cid:
            errors.append(f"Confronto #{idx} sem confronto_id")
        elif cid in seen_ids:
            errors.append(f"confronto_id duplicado: {cid}")
        seen_ids.add(cid)

        problema_id = str(entry.get("problema_id", "")).strip()
        if problema_id not in problemas:
            errors.append(f"{cid}: problema_id inexistente: {problema_id}")

        if str(entry.get("tipo_de_problema", "")) not in VALID_TIPO_PROBLEMA:
            errors.append(f"{cid}: tipo_de_problema inválido")
        if str(entry.get("nivel_arquitetonico", "")) not in VALID_NIVEL_ARQUITETONICO:
            errors.append(f"{cid}: nivel_arquitetonico inválido")
        if str(entry.get("grau_de_centralidade", "")) not in VALID_GRAU_CENTRALIDADE:
            errors.append(f"{cid}: grau_de_centralidade inválido")
        if str(entry.get("grau_de_prioridade", "")) not in VALID_GRAU_PRIORIDADE:
            errors.append(f"{cid}: grau_de_prioridade inválido")
        if str(entry.get("grau_de_risco", "")) not in VALID_GRAU_RISCO:
            errors.append(f"{cid}: grau_de_risco inválido")
        if str(entry.get("grau_de_cobertura_no_projeto", "")) not in VALID_GRAU_COBERTURA:
            errors.append(f"{cid}: grau_de_cobertura_no_projeto inválido")
        if str(entry.get("estado_item", "")) not in VALID_ESTADO_ITEM:
            errors.append(f"{cid}: estado_item inválido")

        if not normalize_spaces(str(entry.get("titulo_curto", ""))):
            errors.append(f"{cid}: titulo_curto vazio")
        if not normalize_spaces(str(entry.get("pergunta_central", ""))):
            errors.append(f"{cid}: pergunta_central vazia")

        prop_ids = [str(x) for x in safe_list(entry.get("proposicao_ids"))]
        campo_ids = [str(x) for x in safe_list(entry.get("campo_ids_relacionados"))]
        ponte_ids = [str(x) for x in safe_list(entry.get("ponte_ids_relacionadas"))]
        anch_ids = [str(x) for x in safe_list(entry.get("ancoragem_ids_relacionadas"))]
        if not (prop_ids or campo_ids or ponte_ids or anch_ids):
            errors.append(f"{cid}: entrada sem qualquer referência estrutural")

        for pid in prop_ids:
            if pid not in props:
                errors.append(f"{cid}: proposicao_id inexistente: {pid}")
        for crid in campo_ids:
            if crid not in campos:
                errors.append(f"{cid}: campo_id inexistente: {crid}")
        for pnid in ponte_ids:
            if pnid not in pontes:
                errors.append(f"{cid}: ponte_id inexistente: {pnid}")
        for acid in anch_ids:
            if acid not in anchors:
                errors.append(f"{cid}: ancoragem_id inexistente: {acid}")

        for tensao in safe_list(entry.get("tipo_de_tensao_com_o_sistema")):
            if str(tensao) not in VALID_TIPO_TENSAO:
                errors.append(f"{cid}: tipo_de_tensao inválido: {tensao}")
        for veredito in safe_list(entry.get("veredito_provisorio")):
            if str(veredito) not in VALID_TIPO_VEREDITO:
                errors.append(f"{cid}: veredito_provisorio inválido: {veredito}")

    indice = safe_dict(output.get("indice_auxiliar_por_proposicao"))
    for pid, confronto_ids in indice.items():
        if pid not in props:
            errors.append(f"Índice auxiliar refere proposição inexistente: {pid}")
        for cid in safe_list(confronto_ids):
            if str(cid) not in seen_ids:
                errors.append(f"Índice auxiliar refere confronto inexistente: {cid}")

    return errors


# =============================================================================
# RELATÓRIO
# =============================================================================


def generate_report(output: Dict[str, Any], errors: List[str]) -> str:
    stats = safe_dict(output.get("estatisticas"))
    lines: List[str] = []
    lines.append("RELATÓRIO — GERAÇÃO DA MATRIZ DE CONFRONTO FILOSÓFICO V1")
    lines.append("=" * 72)
    lines.append(f"Data de geração: {safe_dict(output.get('metadata')).get('data_geracao', '')}")
    lines.append(f"Estado global: {safe_dict(output.get('metadata')).get('estado_global', '')}")
    lines.append("")
    lines.append("Resumo:")
    lines.append(f"- Total de confrontos: {stats.get('total_confrontos', 0)}")
    lines.append(f"- Total de problemas inventariados: {stats.get('total_problemas_inventariados', 0)}")
    lines.append(f"- Proposições que precisam de confronto filosófico: {stats.get('total_proposicoes_que_precisam_confronto', 0)}")
    lines.append(f"- Proposições cobertas: {stats.get('total_proposicoes_cobertas', 0)}")
    lines.append(f"- Proposições sem cobertura: {stats.get('total_proposicoes_sem_cobertura', 0)}")
    lines.append(f"- Confrontos com revisão humana: {stats.get('total_confrontos_com_revisao_humana', 0)}")
    lines.append(f"- Confrontos com resposta canónica: {stats.get('total_confrontos_com_resposta_canonica', 0)}")
    lines.append(f"- Confrontos com capítulo próprio: {stats.get('total_confrontos_com_capitulo_proprio', 0)}")
    lines.append(f"- Confrontos com pontes relacionadas: {stats.get('total_confrontos_com_pontes', 0)}")
    lines.append(f"- Confrontos com ancoragem científica relacionada: {stats.get('total_confrontos_com_ancoragem', 0)}")
    lines.append(f"- Confrontos de risco alto ou crítico: {stats.get('total_confrontos_de_risco_alto_ou_critico', 0)}")
    lines.append(f"- Confrontos metaestruturais: {stats.get('total_confrontos_metaestruturais', 0)}")
    lines.append("")

    by_type = safe_dict(stats.get("confrontos_por_tipo_de_problema"))
    if by_type:
        lines.append("Confrontos por tipo de problema:")
        for key in sorted(by_type):
            lines.append(f"- {key}: {by_type[key]}")
        lines.append("")

    missing = safe_list(stats.get("proposicoes_sem_cobertura"))
    if missing:
        lines.append("Proposições sem cobertura:")
        lines.append("- " + ", ".join(missing))
        lines.append("")

    if errors:
        lines.append(f"Foram detetados {len(errors)} erro(s) de validação:")
        for err in errors:
            lines.append(f"- {err}")
    else:
        lines.append("Concluído sem erros de validação.")

    return "\n".join(lines) + "\n"


# =============================================================================
# MAIN
# =============================================================================


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Gerar a matriz de confronto filosófico v1.")
    parser.add_argument("--project-root", type=Path, default=None, help="Raiz explícita do projeto")
    args = parser.parse_args(argv)

    try:
        project_root = project_root_from_explicit_or_cwd(args.project_root)

        proposicoes_path = resolve_relative(project_root, DEFAULT_INPUT_PROPOSICOES_RELATIVE)
        pontes_path = resolve_relative(project_root, DEFAULT_INPUT_PONTES_RELATIVE)
        ancoragem_path = resolve_relative(project_root, DEFAULT_INPUT_ANCORAGEM_RELATIVE)
        campos_path = resolve_relative(project_root, DEFAULT_INPUT_CAMPOS_RELATIVE)
        inventario_path = resolve_relative(project_root, DEFAULT_INPUT_INVENTARIO_RELATIVE)
        schema_path = resolve_relative(project_root, DEFAULT_INPUT_SCHEMA_RELATIVE)

        output_json_path = (project_root / DEFAULT_OUTPUT_JSON_RELATIVE).resolve()
        report_path = (project_root / DEFAULT_REPORT_RELATIVE).resolve()

        proposicoes_doc = read_json(proposicoes_path)
        pontes_doc = read_json(pontes_path)
        ancoragem_doc = read_json(ancoragem_path)
        campos_doc = read_json(campos_path)
        inventario_doc = read_json(inventario_path)
        schema_doc = read_json(schema_path)

        output = generate_matrix(
            proposicoes_doc=proposicoes_doc,
            pontes_doc=pontes_doc,
            ancoragem_doc=ancoragem_doc,
            campos_doc=campos_doc,
            inventario_doc=inventario_doc,
            schema_doc=schema_doc,
        )
        errors = validate_output(output, proposicoes_doc, pontes_doc, ancoragem_doc, campos_doc, inventario_doc)
        report = generate_report(output, errors)

        write_json(output_json_path, output)
        write_text(report_path, report)

        print(f"JSON gerado em: {output_json_path}")
        print(f"Relatório gerado em: {report_path}")
        if errors:
            print(f"Atenção: foram detetados {len(errors)} erro(s) de validação.")
            return 1
        print("Concluído sem erros de validação.")
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"Erro fatal: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
