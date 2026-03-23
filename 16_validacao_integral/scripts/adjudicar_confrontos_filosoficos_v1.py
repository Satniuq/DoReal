#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
adjudicar_confrontos_filosoficos_v1.py

Adjudica e enriquece a matriz de confronto filosófico já gerada na fase de
validação integral pós-árvore.

Objetivos:
- preencher cada confronto com núcleo argumentativo canónico, distinções
  conceptuais mínimas, objeções priorizadas e plano de redação;
- preservar a rastreabilidade para proposições, campos, pontes e ancoragens;
- localizar confrontos que ainda exigem revisão humana forte;
- produzir um artefacto autónomo, auditável e pronto para redação académica.

Inputs esperados:
- 16_validacao_integral/01_dados/matriz_confronto_filosofico_v1.json
- 16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json
- 16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json
- 16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json
- 16_validacao_integral/01_dados/mapa_campos_do_real_v1.json

Outputs:
- 16_validacao_integral/01_dados/adjudicacao_confrontos_filosoficos_v1.json
- 16_validacao_integral/02_outputs/relatorio_adjudicacao_confrontos_filosoficos_v1.txt
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


# =============================================================================
# CONFIGURAÇÃO CANÓNICA
# =============================================================================

DEFAULT_INPUT_CONFRONTOS_RELATIVE = Path(
    "16_validacao_integral/01_dados/matriz_confronto_filosofico_v1.json"
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
DEFAULT_OUTPUT_JSON_RELATIVE = Path(
    "16_validacao_integral/01_dados/adjudicacao_confrontos_filosoficos_v1.json"
)
DEFAULT_REPORT_RELATIVE = Path(
    "16_validacao_integral/02_outputs/relatorio_adjudicacao_confrontos_filosoficos_v1.txt"
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

VALID_ESTADO_ITEM = {
    "por_preencher",
    "preenchido",
    "revisto",
    "validado",
    "integrado",
}

VALID_DECISAO_ADJUDICADA = {
    "preservar_com_restricoes",
    "preservar_e_explicitar",
    "integrar_com_hierarquia",
    "reformular_em_passos",
    "restringir_o_escopo",
    "manter_em_aberto_sob_criterio",
    "revisao_humana_necessaria",
}

VALID_PRIORIDADE_REDACTIONAL = {
    "baixa",
    "media",
    "alta",
    "estrutural",
    "critica",
}

RISK_ORDER = ["baixo", "medio", "alto", "critico"]
PRIORITY_ORDER = ["baixa", "media", "alta", "estrutural", "critica"]
STATE_ORDER = ["por_preencher", "preenchido", "revisto", "validado", "integrado"]


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



def unique_preserve(values: Iterable[Any]) -> List[Any]:
    out: List[Any] = []
    seen: Set[str] = set()
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out



def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    out = []
    prev_sep = False
    for ch in text:
        if ch.isalnum():
            out.append(ch)
            prev_sep = False
        else:
            if not prev_sep:
                out.append("_")
                prev_sep = True
    return "".join(out).strip("_")



def cut(text: str, limit: int = 220) -> str:
    text = normalize_spaces(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"



def max_by_order(current: str, candidate: str, order: Sequence[str]) -> str:
    cur = current if current in order else order[0]
    cand = candidate if candidate in order else order[0]
    return order[max(order.index(cur), order.index(cand))]



def relpath_str(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve())).replace("\\", "/")
    except Exception:
        return str(path.resolve())



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
        if (cand / DEFAULT_INPUT_CONFRONTOS_RELATIVE).exists():
            return cand.resolve()

    return script_path.parent.parent.parent



def resolve_relative(project_root: Path, relative_path: Path) -> Path:
    path = (project_root / relative_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {path}")
    return path


# =============================================================================
# LOOKUPS
# =============================================================================


def build_proposicao_lookup(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("proposicao_id", "")).strip(): item
        for item in safe_list(data.get("proposicoes"))
        if isinstance(item, dict) and str(item.get("proposicao_id", "")).strip()
    }



def build_ponte_lookup(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("ponte_id", "")).strip(): item
        for item in safe_list(data.get("pontes"))
        if isinstance(item, dict) and str(item.get("ponte_id", "")).strip()
    }



def build_ancoragem_lookup(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("entrada_id", "")).strip(): item
        for item in safe_list(data.get("entradas"))
        if isinstance(item, dict) and str(item.get("entrada_id", "")).strip()
    }



def build_campo_lookup(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("campo_id", "")).strip(): item
        for item in safe_list(data.get("campos"))
        if isinstance(item, dict) and str(item.get("campo_id", "")).strip()
    }


# =============================================================================
# HEURÍSTICAS DE ADJUDICAÇÃO
# =============================================================================


def build_proposition_digest(prop_ids: Sequence[str], proposicoes_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for pid in prop_ids:
        p = safe_dict(proposicoes_lookup.get(pid))
        if not p:
            continue
        out.append(
            {
                "proposicao_id": pid,
                "texto_curto": p.get("texto_curto") or cut(str(p.get("texto", "")), 160),
                "bloco_id": p.get("bloco_id", ""),
                "ordem_global": p.get("ordem_global"),
                "funcao_no_mapa": safe_dict(p.get("classificacao_filosofica_inicial")).get("funcao_no_mapa", ""),
            }
        )
    return out



def build_bridge_digest(ponte_ids: Sequence[str], ponte_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for bridge_id in ponte_ids:
        p = safe_dict(ponte_lookup.get(bridge_id))
        if not p:
            continue
        out.append(
            {
                "ponte_id": bridge_id,
                "nivel_origem": p.get("nivel_origem", ""),
                "nivel_destino": p.get("nivel_destino", ""),
                "tipo_ponte": p.get("tipo_ponte", ""),
                "grau_risco": p.get("grau_risco", "baixo"),
                "problema_da_transicao": p.get("problema_da_transicao", ""),
                "justificacao_provisoria": p.get("justificacao_provisoria", ""),
            }
        )
    return out



def build_science_digest(anc_ids: Sequence[str], anc_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for anc_id in anc_ids:
        a = safe_dict(anc_lookup.get(anc_id))
        if not a:
            continue
        out.append(
            {
                "entrada_id": anc_id,
                "tema_cientifico": a.get("tema_cientifico", ""),
                "dominios_cientificos": safe_list(a.get("dominios_cientificos")),
                "tipo_dependencia_cientifica": a.get("tipo_dependencia_cientifica", ""),
                "estado_atual_da_ancoragem": a.get("estado_atual_da_ancoragem", ""),
                "restricoes_ou_alertas": safe_list(a.get("restricoes_ou_alertas")),
            }
        )
    return out



def build_field_digest(field_ids: Sequence[str], campo_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for field_id in field_ids:
        c = safe_dict(campo_lookup.get(field_id))
        if not c:
            continue
        out.append(
            {
                "campo_id": field_id,
                "nome_campo": c.get("nome_campo", ""),
                "tipo_campo": c.get("tipo_campo", ""),
                "grau_risco": c.get("grau_risco", "baixo"),
                "propriedades_em_foco": safe_list(c.get("propriedades_em_foco"))[:5],
                "dinamicas_relevantes": safe_list(c.get("dinamicas_relevantes"))[:4],
            }
        )
    return out



def build_canonical_claim(confronto: Dict[str, Any]) -> str:
    title = confronto.get("titulo_curto", "Problema filosófico")
    answer = normalize_spaces(confronto.get("resposta_provavel_do_sistema", ""))
    if not answer:
        answer = "O sistema ainda precisa de formulação canónica suficiente para este confronto."
    return f"Quanto a {title.lower()}, a tese canónica provisória é a seguinte: {answer}"



def build_synthesis(confronto: Dict[str, Any], prop_digest: List[Dict[str, Any]], bridge_digest: List[Dict[str, Any]]) -> str:
    title = confronto.get("titulo_curto", "Problema")
    pergunta = normalize_spaces(confronto.get("pergunta_central", ""))
    textos = [item.get("texto_curto", "") for item in prop_digest[:3] if item.get("texto_curto")]
    bridge_ref = ""
    if bridge_digest:
        first_bridge = bridge_digest[0]
        bridge_ref = (
            f" A articulação exige especial cuidado na passagem {first_bridge.get('nivel_origem','?')} → "
            f"{first_bridge.get('nivel_destino','?')} ({first_bridge.get('ponte_id','')})."
        )
    trecho = " ".join(textos)
    if trecho:
        trecho = f" As proposições relacionadas sugerem este núcleo: {trecho}."
    return f"{title} é adjudicado como confronto estrutural em torno da pergunta ‘{pergunta}’.{trecho}{bridge_ref}".strip()



def build_supporting_theses(confronto: Dict[str, Any], prop_digest: List[Dict[str, Any]], field_digest: List[Dict[str, Any]], bridge_digest: List[Dict[str, Any]], science_digest: List[Dict[str, Any]]) -> List[str]:
    theses: List[str] = []
    principal = normalize_spaces(confronto.get("resposta_provavel_do_sistema", ""))
    if principal:
        theses.append(principal)

    if prop_digest:
        theses.append(
            "A formulação deve ser reconstruída a partir das proposições nucleares relacionadas, evitando importar teses externas sem mediação textual suficiente."
        )

    if field_digest:
        nomes = ", ".join(item.get("nome_campo", item.get("campo_id", "")) for item in field_digest[:2] if item.get("nome_campo") or item.get("campo_id"))
        if nomes:
            theses.append(f"A adjudicação deve respeitar a regionalização do problema nos campos {nomes}, evitando generalizações indevidas para todo o real.")

    if bridge_digest:
        theses.append(
            "As passagens entre níveis só são aceitáveis quando mostram mediação real, continuidade inteligível e limites explícitos de derivação."
        )

    if science_digest:
        theses.append(
            "A ancoragem científica funciona aqui como restrição externa de compatibilidade e não como substituição da prova filosófica principal."
        )

    if confronto.get("necessita_revisao_humana"):
        theses.append(
            "A formulação final deve manter prudência terminológica e deixar explícito o ponto exato em que a revisão humana é necessária."
        )

    return unique_preserve(theses)[:5]



def build_distinctions(confronto: Dict[str, Any]) -> List[str]:
    tipo = confronto.get("tipo_de_problema", "")
    title_slug = slugify(confronto.get("titulo_curto", ""))
    base: List[str] = []
    if tipo == "ontologico":
        base += [
            "Distinguir ser, ente, estrutura e campo regional.",
            "Distinguir unidade do real de monismo nivelador.",
            "Distinguir diferença real de mera dispersão pluralista.",
        ]
    elif tipo == "fenomenologico":
        base += [
            "Distinguir aparecer, presença, apreensão e representação.",
            "Distinguir manifestação do real de produção subjetiva do real.",
            "Distinguir imediatidade fenomenal de mediação posterior.",
        ]
    elif tipo in {"antropologico", "filosofia_da_mente"}:
        base += [
            "Distinguir vida, organismo, corpo próprio e sujeito reflexivo.",
            "Distinguir consciência de autoconsciência.",
            "Distinguir identidade pessoal de mera continuidade factual.",
        ]
    elif tipo == "semantico_linguistico":
        base += [
            "Distinguir linguagem, símbolo, sentido e representação.",
            "Distinguir mediação linguística de constituição integral do real.",
            "Distinguir correção semântica de verdade ontológica.",
        ]
    elif tipo == "epistemologico":
        base += [
            "Distinguir verdade, correção, critério e objetividade.",
            "Distinguir erro categorial de erro factual local.",
            "Distinguir adequação ao real de simples coerência interna.",
        ]
    elif tipo in {"pratico_etico", "etico_pratico", "social_politico", "social_historico"}:
        base += [
            "Distinguir descrição do que ocorre de justificação do que deve ser feito.",
            "Distinguir dano real de mera desaprovação subjetiva.",
            "Distinguir normatividade básica de institucionalização histórica.",
        ]
    elif tipo == "metaestrutural":
        base += [
            "Distinguir ordem de exposição de ordem de fundamentação.",
            "Distinguir fecho legítimo de circularidade viciosa.",
            "Distinguir mediação arquitetónica de justaposição temática.",
        ]
    else:
        base += [
            "Distinguir núcleo do problema de extensões regionais secundárias.",
            "Distinguir formulação descritiva de decisão arquitetónica.",
        ]

    if "passagem" in title_slug or "regime" in title_slug:
        base.append("Distinguir passagem mediada entre regimes de simples transposição verbal entre blocos.")
    if "criterio" in title_slug:
        base.append("Distinguir critério último de critério apenas operativo ou convencional.")
    if "dignidade" in title_slug:
        base.append("Distinguir dignidade ontológico-normativa de valor meramente atribuído externamente.")

    return unique_preserve(base)[:6]



def build_prioritized_objections(confronto: Dict[str, Any]) -> List[Dict[str, Any]]:
    objections = []
    resposta = normalize_spaces(confronto.get("resposta_provavel_do_sistema", ""))
    for idx, obj in enumerate(safe_list(confronto.get("objecoes_fortes_a_responder"))[:6], start=1):
        obj_text = normalize_spaces(str(obj))
        if not obj_text:
            continue
        estrategia = "resposta_distintiva"
        if "passagem" in obj_text.lower() or "salto" in obj_text.lower() or "media" in obj_text.lower():
            estrategia = "resposta_de_passagem"
        elif "critério" in obj_text.lower() or "criterio" in obj_text.lower() or "verdade" in obj_text.lower():
            estrategia = "resposta_fundacional"
        elif "norma" in obj_text.lower() or "dever" in obj_text.lower() or "dano" in obj_text.lower():
            estrategia = "resposta_pratico_normativa"
        objections.append(
            {
                "ordem": idx,
                "objecao": obj_text,
                "resposta_curta": cut(
                    resposta
                    or "A resposta do sistema deve mostrar a distinção pertinente, identificar a mediação necessária e restringir o alcance da objeção."
                ),
                "estrategia": estrategia,
            }
        )
    return objections



def choose_decision(confronto: Dict[str, Any]) -> Tuple[str, str]:
    verdicts = safe_list(confronto.get("veredito_provisorio"))
    review = bool(confronto.get("necessita_revisao_humana"))
    risk = confronto.get("grau_de_risco", "baixo")
    tipo = confronto.get("tipo_de_problema", "")

    if review and risk == "critico":
        return (
            "revisao_humana_necessaria",
            "A estrutura do confronto já é suficiente para orientar a redação, mas a decisão final deve ficar suspensa até revisão humana por causa do risco crítico e da indeterminação restante.",
        )
    if "reformular" in verdicts and tipo == "metaestrutural":
        return (
            "reformular_em_passos",
            "A adjudicação recomenda decompor o problema em passagens argumentativas explícitas, porque a forma atual ainda agrega demasiado material heterogéneo.",
        )
    if "reformular" in verdicts:
        return (
            "preservar_com_restricoes",
            "A tese de base pode ser preservada, mas precisa de restrições conceptuais e de melhor explicitação das passagens fortes.",
        )
    if "restringir" in verdicts:
        return (
            "restringir_o_escopo",
            "O confronto deve ser mantido, mas com escopo mais delimitado para evitar inflação temática e derivação excessiva.",
        )
    if "integrar" in verdicts and len(safe_list(confronto.get("tipo_de_tensao_com_o_sistema"))) > 1:
        return (
            "integrar_com_hierarquia",
            "Há compatibilidades reais a integrar, mas com hierarquia interna clara entre ontologia, mediação e eventual fecho normativo.",
        )
    if "integrar" in verdicts:
        return (
            "preservar_e_explicitar",
            "A linha do sistema parece filosoficamente defensável; o trabalho principal é explicitá-la melhor e responder às objeções mais fortes.",
        )
    if "deixar_em_aberto" in verdicts:
        return (
            "manter_em_aberto_sob_criterio",
            "Abertura aqui não significa suspensão vaga: significa manter o problema em aberto sob critérios de fecho e de inteligibilidade explicitados.",
        )
    return (
        "preservar_e_explicitar",
        "A adjudicação sugere preservar a formulação de base, reforçando distinções, objeções e encadeamento argumentativo.",
    )



def build_redaction_plan(confronto: Dict[str, Any], decision: str) -> Dict[str, Any]:
    chapter = "capitulo_proprio" if confronto.get("precisa_capitulo_proprio") else "subcapitulo" if confronto.get("precisa_subcapitulo") else "secao_integrada"
    prioridade = "media"
    if confronto.get("grau_de_risco") == "critico" or confronto.get("necessita_revisao_humana"):
        prioridade = "critica"
    elif confronto.get("grau_de_prioridade") == "estrutural":
        prioridade = "estrutural"
    elif confronto.get("grau_de_prioridade") == "alta":
        prioridade = "alta"

    passos = [
        "abrir com formulação explícita da pergunta central e do ponto de tensão",
        "fixar distinções conceptuais mínimas antes de entrar na disputa autoral",
        "reconstruir o núcleo do sistema a partir das proposições relacionadas",
        "responder às objeções em ordem de risco, começando pelas de salto ilegítimo ou indeterminação forte",
    ]
    if confronto.get("ponte_ids_relacionadas"):
        passos.append("mostrar as passagens entre níveis com remissão explícita para as pontes relacionadas")
    if confronto.get("ancoragem_ids_relacionadas"):
        passos.append("usar a ciência como teste de compatibilidade, sem a converter em fundamento filosófico substitutivo")
    if decision == "revisao_humana_necessaria":
        passos.append("fechar com reserva metodológica clara e ponto exato que exige revisão humana")

    return {
        "unidade_de_redacao_recomendada": chapter,
        "prioridade_redacional": prioridade,
        "sequencia_minima": unique_preserve(passos),
    }



def build_checklist(confronto: Dict[str, Any], decision: str) -> List[str]:
    checks = [
        "A pergunta central aparece logo no início da redação.",
        "As distinções conceptuais mínimas são tratadas antes da resposta final.",
        "Há ligação explícita às proposições nucleares relacionadas.",
        "As objeções fortes recebem resposta determinada e não apenas menção lateral.",
    ]
    if confronto.get("ponte_ids_relacionadas"):
        checks.append("As pontes relacionadas são usadas para justificar passagens entre níveis.")
    if confronto.get("ancoragem_ids_relacionadas"):
        checks.append("As ancoragens científicas aparecem como restrição e compatibilidade, não como substituição do argumento filosófico.")
    if decision == "revisao_humana_necessaria":
        checks.append("A parte em aberto fica marcada com fronteira clara de revisão humana.")
    return checks



def confidence_score(confronto: Dict[str, Any], prop_digest: List[Dict[str, Any]], bridge_digest: List[Dict[str, Any]], science_digest: List[Dict[str, Any]]) -> float:
    score = 0.45
    score += min(len(prop_digest), 5) * 0.06
    score += min(len(bridge_digest), 3) * 0.04
    score += min(len(science_digest), 2) * 0.03
    if confronto.get("grau_de_risco") == "critico":
        score -= 0.15
    elif confronto.get("grau_de_risco") == "alto":
        score -= 0.08
    if confronto.get("necessita_revisao_humana"):
        score -= 0.12
    if confronto.get("falta_tratamento_academico"):
        score -= 0.04
    return round(max(0.2, min(score, 0.95)), 2)



def adjudicate_confronto(
    confronto: Dict[str, Any],
    proposicoes_lookup: Dict[str, Dict[str, Any]],
    ponte_lookup: Dict[str, Dict[str, Any]],
    anc_lookup: Dict[str, Dict[str, Any]],
    campo_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    novo = json.loads(json.dumps(confronto, ensure_ascii=False))

    prop_digest = build_proposition_digest(safe_list(confronto.get("proposicao_ids")), proposicoes_lookup)
    bridge_digest = build_bridge_digest(safe_list(confronto.get("ponte_ids_relacionadas")), ponte_lookup)
    science_digest = build_science_digest(safe_list(confronto.get("ancoragem_ids_relacionadas")), anc_lookup)
    field_digest = build_field_digest(safe_list(confronto.get("campo_ids_relacionados")), campo_lookup)

    decision, decision_just = choose_decision(confronto)
    synthesis = build_synthesis(confronto, prop_digest, bridge_digest)
    canonical_claim = build_canonical_claim(confronto)
    supporting = build_supporting_theses(confronto, prop_digest, field_digest, bridge_digest, science_digest)
    distinctions = build_distinctions(confronto)
    objections = build_prioritized_objections(confronto)
    redaction_plan = build_redaction_plan(confronto, decision)
    checklist = build_checklist(confronto, decision)
    confidence = confidence_score(confronto, prop_digest, bridge_digest, science_digest)

    novo["adjudicacao_filosofica"] = {
        "sintese_adjudicada": synthesis,
        "tese_central_adjudicada": canonical_claim,
        "teses_de_sustentacao": supporting,
        "distincoes_conceituais_minimas": distinctions,
        "objecoes_priorizadas": objections,
        "articulacao_estrutural": {
            "proposicoes_nucleares": prop_digest,
            "pontes_entre_niveis": bridge_digest,
            "ancoragens_cientificas": science_digest,
            "campos_do_real": field_digest,
        },
        "decisao_de_adjudicacao": {
            "decisao_principal": decision,
            "justificacao": decision_just,
            "veredito_herdado_da_matriz": safe_list(confronto.get("veredito_provisorio")),
        },
        "plano_de_redacao_canonica": redaction_plan,
        "checklist_de_fecho": checklist,
        "confianca_heuristica": confidence,
        "gerado_em": utc_now_iso(),
    }

    novo["estado_item"] = "revisto" if confronto.get("necessita_revisao_humana") else "preenchido"
    novo["observacoes"] = normalize_spaces(
        (confronto.get("observacoes", "") + " " + decision_just).strip()
    )
    return novo


# =============================================================================
# VALIDAÇÃO
# =============================================================================


def validate_output(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    metadata = safe_dict(data.get("metadata"))
    estado_global = metadata.get("estado_global", "")
    if estado_global not in VALID_ESTADO_GLOBAL:
        errors.append(f"metadata.estado_global inválido: {estado_global}")

    confrontos = safe_list(data.get("confrontos"))
    if not confrontos:
        errors.append("Não existem confrontos adjudicados.")
        return errors

    seen_ids: Set[str] = set()
    for idx, conf in enumerate(confrontos, start=1):
        cid = str(conf.get("confronto_id", "")).strip()
        if not cid:
            errors.append(f"confrontos[{idx}] sem confronto_id")
        elif cid in seen_ids:
            errors.append(f"confronto_id duplicado: {cid}")
        else:
            seen_ids.add(cid)

        estado_item = conf.get("estado_item", "")
        if estado_item not in VALID_ESTADO_ITEM:
            errors.append(f"{cid}: estado_item inválido: {estado_item}")

        adj = safe_dict(conf.get("adjudicacao_filosofica"))
        if not adj:
            errors.append(f"{cid}: falta bloco adjudicacao_filosofica")
            continue

        decisao = safe_dict(adj.get("decisao_de_adjudicacao")).get("decisao_principal", "")
        if decisao not in VALID_DECISAO_ADJUDICADA:
            errors.append(f"{cid}: decisão adjudicada inválida: {decisao}")

        prioridade = safe_dict(adj.get("plano_de_redacao_canonica")).get("prioridade_redacional", "")
        if prioridade not in VALID_PRIORIDADE_REDACTIONAL:
            errors.append(f"{cid}: prioridade_redacional inválida: {prioridade}")

        confidence = adj.get("confianca_heuristica")
        if not isinstance(confidence, (int, float)):
            errors.append(f"{cid}: confianca_heuristica não numérica")
        else:
            if confidence < 0 or confidence > 1:
                errors.append(f"{cid}: confianca_heuristica fora de [0,1]")

        if not normalize_spaces(adj.get("sintese_adjudicada", "")):
            errors.append(f"{cid}: sintese_adjudicada vazia")
        if not normalize_spaces(adj.get("tese_central_adjudicada", "")):
            errors.append(f"{cid}: tese_central_adjudicada vazia")
        if not safe_list(adj.get("teses_de_sustentacao")):
            errors.append(f"{cid}: teses_de_sustentacao vazias")
        if not safe_list(adj.get("distincoes_conceituais_minimas")):
            errors.append(f"{cid}: distincoes_conceituais_minimas vazias")
        if not safe_list(adj.get("checklist_de_fecho")):
            errors.append(f"{cid}: checklist_de_fecho vazio")

        articulacao = safe_dict(adj.get("articulacao_estrutural"))
        if not any(safe_list(articulacao.get(key)) for key in [
            "proposicoes_nucleares", "pontes_entre_niveis", "ancoragens_cientificas", "campos_do_real"
        ]):
            errors.append(f"{cid}: adjudicação sem articulação estrutural útil")

    return errors


# =============================================================================
# RELATÓRIO
# =============================================================================


def build_report(
    project_root: Path,
    input_paths: Dict[str, Path],
    output_json_path: Path,
    output_report_path: Path,
    data: Dict[str, Any],
    validation_errors: List[str],
) -> str:
    metadata = safe_dict(data.get("metadata"))
    stats = safe_dict(data.get("estatisticas"))
    confrontos = safe_list(data.get("confrontos"))

    lines: List[str] = []
    lines.append("RELATÓRIO — ADJUDICAÇÃO DOS CONFRONTOS FILOSÓFICOS V1")
    lines.append("=" * 72)
    lines.append(f"Data de geração: {metadata.get('data_geracao', '')}")
    lines.append(f"Estado global: {metadata.get('estado_global', '')}")
    lines.append("")
    lines.append("Ficheiros lidos:")
    lines.append("-" * 72)
    for key, path in input_paths.items():
        lines.append(f"- {key}: {relpath_str(path, project_root)}")
    lines.append("")
    lines.append("Ficheiros escritos:")
    lines.append("-" * 72)
    lines.append(f"- json_principal: {relpath_str(output_json_path, project_root)}")
    lines.append(f"- relatorio_txt: {relpath_str(output_report_path, project_root)}")
    lines.append("")
    lines.append("Resumo quantitativo:")
    lines.append("-" * 72)
    for key in [
        "total_confrontos_adjudicados",
        "total_revistos",
        "total_preenchidos",
        "total_com_revisao_humana",
        "total_decisao_revisao_humana",
        "total_prioridade_critica",
        "total_com_ciencia_articulada",
        "total_com_pontes_articuladas",
        "media_confianca_heuristica",
    ]:
        lines.append(f"- {key}: {stats.get(key)}")
    lines.append("")
    lines.append("Decisões de adjudicação:")
    lines.append("-" * 72)
    decisao_counts = safe_dict(stats.get("confrontos_por_decisao"))
    for key in sorted(decisao_counts.keys()):
        lines.append(f"- {key}: {decisao_counts[key]}")
    lines.append("")
    lines.append("Listagem por confronto:")
    lines.append("-" * 72)
    for conf in confrontos:
        cid = conf.get("confronto_id", "")
        titulo = conf.get("titulo_curto", "")
        risk = conf.get("grau_de_risco", "")
        review = "sim" if conf.get("necessita_revisao_humana") else "não"
        adj = safe_dict(conf.get("adjudicacao_filosofica"))
        decisao = safe_dict(adj.get("decisao_de_adjudicacao")).get("decisao_principal", "")
        prioridade = safe_dict(adj.get("plano_de_redacao_canonica")).get("prioridade_redacional", "")
        confianca = adj.get("confianca_heuristica", "")
        lines.append(
            f"{cid} | risco={risk} | revisão_humana={review} | decisão={decisao} | prioridade={prioridade} | confiança={confianca} | {titulo}"
        )
        lines.append(f"  síntese: {adj.get('sintese_adjudicada', '')}")
        lines.append(f"  tese_central: {adj.get('tese_central_adjudicada', '')}")
    lines.append("")
    if validation_errors:
        lines.append("Erros de validação:")
        lines.append("-" * 72)
        for error in validation_errors:
            lines.append(f"- {error}")
    else:
        lines.append("Concluído sem erros de validação.")
    return "\n".join(lines) + "\n"


# =============================================================================
# MAIN
# =============================================================================


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Adjudica a matriz de confronto filosófico.")
    parser.add_argument("--project-root", type=Path, default=None, help="Raiz explícita do projeto DoReal.")
    args = parser.parse_args(argv)

    try:
        project_root = project_root_from_explicit_or_cwd(args.project_root)
        input_confrontos_path = resolve_relative(project_root, DEFAULT_INPUT_CONFRONTOS_RELATIVE)
        input_proposicoes_path = resolve_relative(project_root, DEFAULT_INPUT_PROPOSICOES_RELATIVE)
        input_pontes_path = resolve_relative(project_root, DEFAULT_INPUT_PONTES_RELATIVE)
        input_ancoragem_path = resolve_relative(project_root, DEFAULT_INPUT_ANCORAGEM_RELATIVE)
        input_campos_path = resolve_relative(project_root, DEFAULT_INPUT_CAMPOS_RELATIVE)

        output_json_path = (project_root / DEFAULT_OUTPUT_JSON_RELATIVE).resolve()
        output_report_path = (project_root / DEFAULT_REPORT_RELATIVE).resolve()

        matriz = safe_dict(read_json(input_confrontos_path))
        proposicoes = safe_dict(read_json(input_proposicoes_path))
        pontes = safe_dict(read_json(input_pontes_path))
        ancoragem = safe_dict(read_json(input_ancoragem_path))
        campos = safe_dict(read_json(input_campos_path))

        proposicoes_lookup = build_proposicao_lookup(proposicoes)
        ponte_lookup = build_ponte_lookup(pontes)
        anc_lookup = build_ancoragem_lookup(ancoragem)
        campo_lookup = build_campo_lookup(campos)

        confrontos_origem = safe_list(matriz.get("confrontos"))
        confrontos_adjudicados = [
            adjudicate_confronto(conf, proposicoes_lookup, ponte_lookup, anc_lookup, campo_lookup)
            for conf in confrontos_origem
        ]

        decisao_counter = Counter()
        priority_counter = Counter()
        state_counter = Counter()
        confidences: List[float] = []
        with_review = 0
        with_science = 0
        with_bridges = 0
        total_decision_review = 0

        for conf in confrontos_adjudicados:
            state_counter[conf.get("estado_item", "")] += 1
            adj = safe_dict(conf.get("adjudicacao_filosofica"))
            decisao = safe_dict(adj.get("decisao_de_adjudicacao")).get("decisao_principal", "")
            decisao_counter[decisao] += 1
            prioridade = safe_dict(adj.get("plano_de_redacao_canonica")).get("prioridade_redacional", "")
            priority_counter[prioridade] += 1
            conf_score = adj.get("confianca_heuristica")
            if isinstance(conf_score, (int, float)):
                confidences.append(float(conf_score))
            art = safe_dict(adj.get("articulacao_estrutural"))
            if safe_list(art.get("ancoragens_cientificas")):
                with_science += 1
            if safe_list(art.get("pontes_entre_niveis")):
                with_bridges += 1
            if conf.get("necessita_revisao_humana"):
                with_review += 1
            if decisao == "revisao_humana_necessaria":
                total_decision_review += 1

        media_conf = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

        output_data = {
            "metadata": {
                "schema_nome": "adjudicacao_confrontos_filosoficos_v1",
                "schema_versao": "1.0",
                "data_geracao": utc_now_iso(),
                "gerado_por_script": "adjudicar_confrontos_filosoficos_v1.py",
                "descricao": "Adjudicação heurística e auditável da matriz de confronto filosófico, pronta para redação académica assistida.",
                "idioma": "pt-PT",
                "projeto": "DoReal / 16_validacao_integral",
                "estado_global": "enriquecido",
            },
            "fontes": {
                "fonte_matriz_confronto": relpath_str(input_confrontos_path, project_root),
                "fonte_proposicoes_enriquecidas": relpath_str(input_proposicoes_path, project_root),
                "fonte_matriz_pontes": relpath_str(input_pontes_path, project_root),
                "fonte_matriz_ancoragem": relpath_str(input_ancoragem_path, project_root),
                "fonte_mapa_campos": relpath_str(input_campos_path, project_root),
                "finalidade": "Transformar confrontos por preencher em unidades adjudicadas e redacionalmente operáveis.",
            },
            "estatisticas": {
                "total_confrontos_adjudicados": len(confrontos_adjudicados),
                "total_revistos": state_counter.get("revisto", 0),
                "total_preenchidos": state_counter.get("preenchido", 0),
                "total_com_revisao_humana": with_review,
                "total_decisao_revisao_humana": total_decision_review,
                "total_prioridade_critica": priority_counter.get("critica", 0),
                "total_com_ciencia_articulada": with_science,
                "total_com_pontes_articuladas": with_bridges,
                "media_confianca_heuristica": media_conf,
                "confrontos_por_decisao": dict(sorted(decisao_counter.items())),
                "confrontos_por_prioridade_redacional": dict(sorted(priority_counter.items())),
            },
            "enums_documentados": {
                "estado_global": sorted(VALID_ESTADO_GLOBAL),
                "estado_item": sorted(VALID_ESTADO_ITEM),
                "decisao_adjudicada": sorted(VALID_DECISAO_ADJUDICADA),
                "prioridade_redacional": sorted(VALID_PRIORIDADE_REDACTIONAL),
            },
            "regras_de_validacao": {
                "regras_gerais": [
                    "Cada confronto adjudicado deve preservar o confronto_id e o problema_id da matriz de origem.",
                    "Cada confronto adjudicado deve conter adjudicacao_filosofica com tese central, distinções mínimas e decisão principal.",
                    "A adjudicação não substitui revisão humana quando a própria matriz assinala risco crítico ou indeterminação forte.",
                    "A ciência entra como restrição de compatibilidade; não substitui o fundamento filosófico principal.",
                ]
            },
            "confrontos": confrontos_adjudicados,
            "observacoes_metodologicas": [
                "Esta adjudicação é heurística e textual: organiza o trabalho filosófico e reduz dispersão, mas não fecha por si só a redação académica final.",
                "Confrontos com decisão revisao_humana_necessaria devem ser tratados manualmente antes de qualquer fecho canónico final.",
            ],
        }

        validation_errors = validate_output(output_data)
        write_json(output_json_path, output_data)

        report_text = build_report(
            project_root=project_root,
            input_paths={
                "matriz_confronto": input_confrontos_path,
                "proposicoes": input_proposicoes_path,
                "pontes": input_pontes_path,
                "ancoragem": input_ancoragem_path,
                "campos": input_campos_path,
            },
            output_json_path=output_json_path,
            output_report_path=output_report_path,
            data=output_data,
            validation_errors=validation_errors,
        )
        write_text(output_report_path, report_text)

        print(f"JSON gerado em: {output_json_path}")
        print(f"Relatório gerado em: {output_report_path}")
        if validation_errors:
            print(f"Atenção: foram detetados {len(validation_errors)} erro(s) de validação.")
            return 1
        print("Concluído sem erros de validação.")
        return 0

    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
