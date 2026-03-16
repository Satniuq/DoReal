#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fechador canónico do mapa dedutivo.

Objetivo:
- partir da reconstrução inevitável v3;
- limpar contaminações meta-editoriais;
- testar inevitabilidade local de cada passo;
- distinguir fragilidade de formulação/mediação/justificação/ordem/objeção;
- propor subpassos mediacionais onde a cadeia ainda salta;
- gerar uma matriz de inevitabilidades e dossiês por corredor.

Saídas principais:
- matriz_inevitabilidades_v4.json
- mapa_dedutivo_precanonico_v4.json
- relatorio_fecho_canonico_v4.json
- dossiers_corredor/*.json
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parent
PASTA_MAPA = ROOT.parent
RAIZ_PROJETO = PASTA_MAPA.parent

PASTA_META_INDICE = RAIZ_PROJETO / "13_Meta_Indice"
PASTA_INDICE = PASTA_META_INDICE / "indice"
PASTA_ARGUMENTOS = PASTA_INDICE / "argumentos"
PASTA_CADENCIA = PASTA_META_INDICE / "cadência" / "04_extrator_q_faz_no_sistema"

DEFAULT_FILES = {
    "mapa_v3": ROOT / "mapa_dedutivo_reconstrucao_inevitavel_v3.json",
    "relatorio_v3": ROOT / "relatorio_reconstrucao_inevitavel_v3.json",
    "mapa_base": PASTA_MAPA / "02_mapa_dedutivo_arquitetura_fragmentos.json",
    "revisao": PASTA_MAPA / "revisao_estrutural_do_mapa.json",
    "fecho_p25_p30": ROOT / "fecho_manual_corredor_P25_P30.json",
    "fecho_p33_p37": ROOT / "fecho_manual_corredor_P33_P37.json",
    "fecho_p42_p48": ROOT / "fecho_manual_corredor_P42_P48.json",
    "fecho_p50": ROOT / "fecho_manual_corredor_P50.json",
    "impacto": PASTA_MAPA / "impacto_fragmentos_no_mapa.json",
    "impacto_relatorio": PASTA_MAPA / "impacto_fragmentos_no_mapa_relatorio_validacao.json",
    "tratamento_fragmentos": PASTA_CADENCIA / "tratamento_filosofico_fragmentos.json",
    "argumentos": PASTA_ARGUMENTOS / "argumentos_unificados.json",
    "indice_por_percurso": PASTA_INDICE / "indice_por_percurso.json",
}

CORREDORES = {
    "P25_P30": [f"P{i:02d}" for i in range(25, 31)],
    "P33_P37": [f"P{i:02d}" for i in range(33, 38)],
    "P42_P48": [f"P{i:02d}" for i in range(42, 49)],
    "P50": ["P50"],
}

META_EDITORIAL_PATTERNS = [
    re.compile(r"^Mant[eé]m-se o n[úu]cleo segundo o qual\s+", re.I),
    re.compile(r"\bO diagn[oó]stico estrutural atual [ée] .*?(?:\.|$)", re.I),
    re.compile(r"\bA justifica[cç][aã]o m[ií]nima j[aá] presente [ée]:\s*", re.I),
    re.compile(r"\bReformula-se provisoriamente[^.]*\.\s*", re.I),
    re.compile(r"\bMant[eé]m-se provisoriamente[^.]*\.\s*", re.I),
    re.compile(r"\bNo .*?, esta proposi[cç][aã]o fixa que\s+", re.I),
    re.compile(r"\bRecebe apoio imediato de .*?;\s*e prepara .*?(?:\.|$)", re.I),
    re.compile(r"\s+\."),
]

NORMALIZE_WS_RE = re.compile(r"\s+")
ARG_RE = re.compile(r"ARG_[A-Z0-9_]+")
P_RE = re.compile(r"P(\d{2})")


@dataclass
class StepBundle:
    pid: str
    passo_v3: Dict[str, Any]
    passo_base: Dict[str, Any]
    revisao: Dict[str, Any]
    fecho: Optional[Dict[str, Any]]
    impacto: Dict[str, Any]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_strip(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return NORMALIZE_WS_RE.sub(" ", value).strip()
    return NORMALIZE_WS_RE.sub(" ", str(value)).strip()


def parse_maybe_python_dict(text: Any) -> Any:
    if isinstance(text, (dict, list)):
        return text
    if not isinstance(text, str):
        return text
    t = text.strip()
    if not t:
        return text
    if (t.startswith("{") and t.endswith("}")) or (t.startswith("[") and t.endswith("]")):
        try:
            return ast.literal_eval(t)
        except Exception:
            return text
    return text


def clean_meta_editorial(text: Any) -> str:
    s = safe_strip(text)
    if not s:
        return ""
    for pattern in META_EDITORIAL_PATTERNS:
        s = pattern.sub("", s)
    s = s.replace("..", ".")
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    s = NORMALIZE_WS_RE.sub(" ", s).strip(" ;,.-")
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    return s


def sentence_like(text: str) -> str:
    s = clean_meta_editorial(text)
    if not s:
        return ""
    if not re.search(r"[.!?]$", s):
        s += "."
    return s


def unique_list(seq: Iterable[Any]) -> List[Any]:
    seen = set()
    out = []
    for item in seq:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def flatten_base_map(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for bloco in data.get("blocos", []):
        for prop in bloco.get("proposicoes", []):
            item = copy.deepcopy(prop)
            item["bloco_id"] = bloco.get("id")
            item["bloco_titulo"] = bloco.get("titulo")
            out[item["id"]] = item
    return out


def index_by_key(items: Sequence[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
    return {str(item.get(key)): item for item in items if item.get(key) is not None}


def load_fechos(paths: Dict[str, Path]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for path in paths.values():
        data = load_json(path)
        for ficha in data.get("fichas", []):
            out[ficha["proposicao_id"]] = ficha
    return out


def index_impacto(data: Any) -> Dict[str, Dict[str, Any]]:
    if isinstance(data, dict):
        if isinstance(data.get("impacto_por_proposicao"), list):
            return index_by_key(data["impacto_por_proposicao"], "proposicao_id")
        if isinstance(data.get("impacto_por_proposicao"), dict):
            return data["impacto_por_proposicao"]
    if isinstance(data, list):
        return index_by_key(data, "proposicao_id")
    return {}


def collect_argument_ids(data: Any) -> Tuple[set, set]:
    existing = set()
    referenced = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k in {"id", "argumento_id"} and isinstance(v, str) and v.startswith("ARG_"):
                    existing.add(v)
                if isinstance(v, str):
                    referenced.update(ARG_RE.findall(v))
                else:
                    walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            referenced.update(ARG_RE.findall(node))

    walk(data)
    return existing, referenced


def support_counts_from_impacto_entry(entry: Dict[str, Any]) -> Dict[str, int]:
    counts = {
        "fragmentos": 0,
        "explicita": 0,
        "densificar": 0,
        "reformular": 0,
    }
    if not entry:
        return counts
    possible = []
    for key in ["fragmentos_relacionados", "itens", "ocorrencias", "impactos", "resultados"]:
        val = entry.get(key)
        if isinstance(val, list):
            possible.extend(val)
    if possible:
        counts["fragmentos"] = len(possible)
        for item in possible:
            txt = json.dumps(item, ensure_ascii=False).lower()
            if "explicita" in txt:
                counts["explicita"] += 1
            if "densificar" in txt:
                counts["densificar"] += 1
            if "reformular" in txt:
                counts["reformular"] += 1
        return counts

    txt = json.dumps(entry, ensure_ascii=False).lower()
    m = re.search(r"tocad[ao] por (\d+) fragment", txt)
    if m:
        counts["fragmentos"] = int(m.group(1))
    counts["explicita"] = txt.count("explicita")
    counts["densificar"] = txt.count("densificar")
    counts["reformular"] = txt.count("reformular")
    return counts


def detect_textual_contamination(*texts: Any) -> bool:
    blob = " ".join(safe_strip(t) for t in texts if safe_strip(t))
    needles = [
        "mantém-se o núcleo",
        "o diagnóstico estrutural atual",
        "a justificação mínima já presente",
        "reformula-se provisoriamente",
        "mantém-se provisoriamente",
        "esta proposição fixa que",
    ]
    return any(n in blob.lower() for n in needles)


def infer_tipo_necessidade(bundle: StepBundle) -> str:
    p = bundle.pid
    n = int(P_RE.search(p).group(1))
    if n <= 24:
        return "ontologica"
    if 25 <= n <= 32:
        return "mediacional"
    if 33 <= n <= 38:
        return "epistemica"
    if 39 <= n <= 41:
        return "pratica"
    if 42 <= n <= 51:
        return "etica"
    return "mediacional"


def score_necessity(bundle: StepBundle) -> Tuple[float, Dict[str, float]]:
    step = bundle.passo_v3
    rev = bundle.revisao
    fecho = bundle.fecho or {}
    impacto_counts = support_counts_from_impacto_entry(bundle.impacto)

    breakdown: Dict[str, float] = {}
    breakdown["dependencias"] = min(len(step.get("depende_de", [])) * 0.8, 2.4)
    breakdown["prepara"] = min(len(step.get("prepara", [])) * 0.7, 2.1)

    classif = safe_strip(step.get("classificacao_funcional")).lower()
    breakdown["classificacao"] = {"nucleo": 3.0, "mediacao_necessaria": 2.0, "apoio_expositivo": 0.8}.get(classif, 1.2)

    estatuto = safe_strip(step.get("estatuto_no_mapa")).lower()
    breakdown["estatuto"] = {"manter": 1.2, "densificar": 1.8, "reformular": 1.1, "manter_provisoriamente": 0.9}.get(estatuto, 1.0)

    breakdown["impacto_fragmentario"] = min(math.log1p(impacto_counts["fragmentos"]) * 0.85, 4.0)
    breakdown["densificacao"] = min(impacto_counts["densificar"] * 0.15, 1.5)

    breakdown["promocao_mediacional"] = min(float(step.get("score_promocao_mediacional", 0) or 0) * 0.08, 2.0)

    necessidade_principal = safe_strip(parse_maybe_python_dict(fecho.get("estado_estrutural_atual", {})).get("necessidade_principal") if isinstance(parse_maybe_python_dict(fecho.get("estado_estrutural_atual", {})), dict) else "")
    breakdown["fragilidade"] = {
        "reformular": -1.0,
        "explicitar_mediacoes": -0.3,
        "densificar": -0.1,
        "": 0.0,
    }.get(necessidade_principal, 0.0)

    contamination = detect_textual_contamination(step.get("tese_minima"), step.get("nucleo"), fecho.get("nucleo_que_se_mantem"))
    breakdown["contaminacao_textual"] = -1.0 if contamination else 0.0

    total = sum(breakdown.values())
    return round(total, 3), breakdown


def estado_de_fecho(score: float, bundle: StepBundle) -> str:
    estatuto = safe_strip(bundle.passo_v3.get("estatuto_no_mapa")).lower()
    contamination = detect_textual_contamination(bundle.passo_v3.get("tese_minima"), bundle.passo_v3.get("nucleo"), (bundle.fecho or {}).get("nucleo_que_se_mantem"))
    if score >= 7.2 and estatuto in {"manter", "densificar"} and not contamination:
        return "fechado"
    if score >= 4.8:
        return "quase_fechado"
    return "aberto"


def canonical_proposition(bundle: StepBundle) -> Tuple[str, Dict[str, Any]]:
    step = bundle.passo_v3
    base = bundle.passo_base
    rev = bundle.revisao
    fecho = bundle.fecho or {}

    candidates: List[Tuple[str, str, float]] = []

    def add(src: str, text: Any, base_score: float) -> None:
        cleaned = sentence_like(text)
        if not cleaned:
            return
        score = base_score
        if detect_textual_contamination(text):
            score -= 2.0
        if len(cleaned.split()) < 5:
            score -= 0.4
        if len(cleaned.split()) > 35:
            score -= 0.4
        if bundle.pid in CORREDORES["P25_P30"] + CORREDORES["P33_P37"] + CORREDORES["P42_P48"] + CORREDORES["P50"] and src == "fecho_formulacao_v2_provisoria":
            # usar com prudência forte
            score -= 0.7
        candidates.append((src, cleaned, score))

    add("v3_proposicao_final", step.get("proposicao_final"), 4.6)
    add("revisao_nova_formulacao_provisoria", rev.get("nova_formulacao_provisoria"), 4.2)
    add("base_formulacao_academica", base.get("tratamento_academico", {}).get("formulacao_filosofico_academica"), 4.0)
    add("fecho_formulacao_v2_provisoria", fecho.get("formulacao_v2_provisoria"), 3.5)
    add("base_proposicao", base.get("proposicao"), 2.0)

    if not candidates:
        return sentence_like(step.get("proposicao_original") or base.get("proposicao") or bundle.pid), {"fonte": None, "score": 0.0, "candidatas": []}

    best = max(candidates, key=lambda x: x[2])
    return best[1], {
        "fonte": best[0],
        "score": round(best[2], 3),
        "candidatas": [{"fonte": s, "texto": t, "score": round(sc, 3)} for s, t, sc in sorted(candidates, key=lambda x: x[2], reverse=True)],
    }


def canonical_justification(bundle: StepBundle) -> str:
    sources = [
        bundle.passo_v3.get("justificacao_minima_suficiente"),
        bundle.revisao.get("base_dedutiva_existente", {}).get("justificacao_interna_do_passo"),
        (bundle.fecho or {}).get("justificacao_atual"),
        bundle.passo_base.get("justificacao", {}).get("justificacao_interna_do_passo"),
    ]
    for src in sources:
        cleaned = sentence_like(src)
        if cleaned and not detect_textual_contamination(src):
            return cleaned
    for src in sources:
        cleaned = sentence_like(src)
        if cleaned:
            return cleaned
    return "Justificação ainda a fechar canonicamente."


def canonical_nucleo(bundle: StepBundle) -> str:
    sources = [
        bundle.passo_v3.get("nucleo"),
        (bundle.fecho or {}).get("nucleo_que_se_mantem"),
        bundle.revisao.get("base_dedutiva_existente", {}).get("tese_minima"),
        bundle.passo_base.get("justificacao", {}).get("tese_minima"),
    ]
    for src in sources:
        cleaned = clean_meta_editorial(src)
        if cleaned and not detect_textual_contamination(src):
            return cleaned
    for src in sources:
        cleaned = clean_meta_editorial(src)
        if cleaned:
            return cleaned
    return clean_meta_editorial(bundle.passo_v3.get("tese_minima")) or clean_meta_editorial(bundle.passo_base.get("proposicao")) or bundle.pid


def canonical_objecao_letal(bundle: StepBundle) -> str:
    obj_lists = [
        bundle.passo_v3.get("objecoes_bloqueadas", []),
        bundle.revisao.get("base_dedutiva_existente", {}).get("objecoes_tipicas_a_bloquear", []),
        (bundle.fecho or {}).get("objecoes_a_bloquear", []),
        bundle.passo_base.get("tratamento_academico", {}).get("objecoes_tipicas_a_bloquear", []),
    ]
    flat = []
    for objs in obj_lists:
        if isinstance(objs, list):
            flat.extend(safe_strip(o) for o in objs if safe_strip(o))
        elif safe_strip(objs):
            flat.append(safe_strip(objs))
    if not flat:
        return "Objeção letal ainda não isolada canonicamente"
    counts = Counter(flat)
    return counts.most_common(1)[0][0]


def classify_fragility(bundle: StepBundle, score: float) -> List[str]:
    out = []
    step = bundle.passo_v3
    fecho = bundle.fecho or {}
    rev = bundle.revisao

    if detect_textual_contamination(step.get("tese_minima"), step.get("nucleo"), fecho.get("nucleo_que_se_mantem")):
        out.append("formulacao")

    mediacoes = []
    for src in [
        rev.get("base_dedutiva_existente", {}).get("mediacoes_em_falta_no_mapa", []),
        rev.get("materiais_de_reconstrucao", {}).get("mediacoes_a_introduzir", []),
        fecho.get("mediacoes_em_falta", []),
        step.get("mediacao_necessaria", []),
    ]:
        if isinstance(src, list):
            mediacoes.extend([safe_strip(x) for x in src if safe_strip(x)])
        elif safe_strip(src):
            mediacoes.append(safe_strip(src))
    if len(unique_list(mediacoes)) >= 2 or float(step.get("score_promocao_mediacional", 0) or 0) >= 6.0:
        out.append("mediacao")

    justificacao = canonical_justification(bundle)
    if len(justificacao.split()) < 10 or "a fechar canonicamente" in justificacao.lower():
        out.append("justificacao")

    if not step.get("depende_de") and int(P_RE.search(bundle.pid).group(1)) not in {1}:
        out.append("ordem")

    objecao = canonical_objecao_letal(bundle)
    if "ainda não" in objecao.lower() or not objecao:
        out.append("objecao")

    if score < 4.8 and "mediacao" not in out:
        out.append("justificacao")

    return unique_list(out) or ["residual"]


def because_previous_not_enough(bundle: StepBundle, canonical_prop: str) -> str:
    prevs = bundle.passo_v3.get("depende_de", [])
    if not prevs:
        return "Sem este passo, a cadeia nem sequer ganha o ponto mínimo a partir do qual pode começar a descrever, negar ou ordenar o real."
    if len(prevs) == 1:
        return f"{prevs[0]} não basta porque ainda não introduz explicitamente este ganho: {clean_meta_editorial(canonical_prop).rstrip('.')}"
    return f"Os passos {', '.join(prevs)} não bastam em conjunto porque ainda não fecham esta passagem específica: {clean_meta_editorial(canonical_prop).rstrip('.')}"


def because_not_suppressible(bundle: StepBundle, canonical_prop: str) -> str:
    nexts = bundle.passo_v3.get("prepara", [])
    if not nexts:
        return "Este passo não é suprimível porque sustenta o fecho do sistema e bloqueia a perda da articulação final do mapa."
    if len(nexts) == 1:
        return f"Se este passo for suprimido, a passagem para {nexts[0]} perde mediação e aparece como salto dedutivo."
    return f"Se este passo for suprimido, a transição para {', '.join(nexts)} fica sem mediação suficiente e o corredor correspondente abre um salto."


def infer_subpasso(bundle: StepBundle) -> Optional[str]:
    pid = bundle.pid
    n = int(P_RE.search(pid).group(1))
    if pid == "P25":
        return "Distinguir apreensão de interpretação e de representação, mostrando que a apreensão é contacto situado anterior à tematização reflexiva."
    if pid == "P28":
        return "Explicitar a passagem entre representação linguística e consciência como processo real, localizado e mediado, evitando exterioridade da consciência."
    if pid == "P33":
        return "Mostrar que um critério puramente interno só mede coerência sistémica, não adequação ao real; por isso o critério deve submeter-se ao real."
    if pid == "P36":
        return "Separar erro, ilusão, insuficiência epistémica e dano prático, fixando o erro como desadequação ao real sob critério válido."
    if pid == "P42":
        return "Explicitar por que a assimetria entre correção e dano torna inteligível uma direção ontológica sem apelo moral externo."
    if pid == "P47":
        return "Mostrar que o dever-ser deriva da estrutura direcional do poder-ser real e não de convenção ou pura decisão voluntarista."
    if pid == "P50":
        return "Fechar a derivação da dignidade a partir do estatuto do ser reflexivo real, vulnerável, situado e capaz de verdade, erro e correção."
    score = float(bundle.passo_v3.get("score_promocao_mediacional", 0) or 0)
    if score >= 6.0:
        return "Subpasso mediacional sugerido pelo défice de ponte entre o passo anterior e o seguinte."
    return None


def build_matrix_row(bundle: StepBundle) -> Dict[str, Any]:
    canonical_prop, prop_meta = canonical_proposition(bundle)
    necessity_score, breakdown = score_necessity(bundle)
    fecho_estado = estado_de_fecho(necessity_score, bundle)
    tipo = infer_tipo_necessidade(bundle)
    fragilidade = classify_fragility(bundle, necessity_score)
    subpasso = infer_subpasso(bundle)
    suporta_subpasso = bool(subpasso)
    previous_not_enough = because_previous_not_enough(bundle, canonical_prop)
    not_suppressible = because_not_suppressible(bundle, canonical_prop)
    cont_text = detect_textual_contamination(bundle.passo_v3.get("tese_minima"), bundle.passo_v3.get("nucleo"), (bundle.fecho or {}).get("nucleo_que_se_mantem"))
    fonte_prioritaria = bundle.passo_v3.get("fonte_decisao_prioritaria") or ("fecho_manual" if bundle.fecho else "revisao_estrutural")

    return {
        "id": bundle.pid,
        "numero_final": bundle.passo_v3.get("numero_final"),
        "bloco_id": bundle.passo_v3.get("bloco_id") or bundle.passo_base.get("bloco_id"),
        "bloco_titulo": bundle.passo_v3.get("bloco_titulo") or bundle.passo_base.get("bloco_titulo"),
        "depende_de": bundle.passo_v3.get("depende_de", []),
        "prepara": bundle.passo_v3.get("prepara", []),
        "proposicao_canonica_curta": canonical_prop,
        "proposicao_canonica_tecnica": sentence_like(bundle.passo_v3.get("proposicao_final") or canonical_prop),
        "tese_minima_canonica": sentence_like(canonical_nucleo(bundle)),
        "justificacao_minima_canonica": canonical_justification(bundle),
        "porque_este_passo_e_necessario": sentence_like(bundle.passo_v3.get("funcao_no_sistema") or bundle.passo_base.get("descricao_curta") or canonical_prop),
        "porque_o_anterior_nao_basta": sentence_like(previous_not_enough),
        "porque_nao_pode_ser_suprimido": sentence_like(not_suppressible),
        "objecao_letal_a_bloquear": canonical_objecao_letal(bundle),
        "tipo_de_necessidade": tipo,
        "estado_de_fecho": fecho_estado,
        "classificacao_funcional": bundle.passo_v3.get("classificacao_funcional"),
        "estatuto_no_mapa": bundle.passo_v3.get("estatuto_no_mapa"),
        "score_canonico_de_fecho": necessity_score,
        "breakdown_score_canonico": breakdown,
        "tipos_de_fragilidade": fragilidade,
        "precisa_de_subpasso": suporta_subpasso,
        "subpasso_sugerido": subpasso,
        "texto_meta_editorial_detectado": cont_text,
        "requer_arbitragem_humana": fecho_estado != "fechado" or cont_text or "mediacao" in fragilidade,
        "fonte_decisao_prioritaria": fonte_prioritaria,
        "fonte_formulacao_canonica": prop_meta["fonte"],
        "score_formulacao_canonica": prop_meta["score"],
        "candidatas_de_formulacao": prop_meta["candidatas"],
        "fragmentos_de_apoio_final": bundle.passo_v3.get("fragmentos_de_apoio_final", []),
        "objecoes_bloqueadas": bundle.passo_v3.get("objecoes_bloqueadas", []),
        "observacoes_editoriais": bundle.passo_v3.get("observacoes_editoriais", []),
    }


def build_precanonical_step(bundle: StepBundle, row: Dict[str, Any]) -> Dict[str, Any]:
    step = copy.deepcopy(bundle.passo_v3)
    step["proposicao_final"] = row["proposicao_canonica_curta"]
    step["tese_minima"] = row["tese_minima_canonica"]
    step["justificacao_minima_suficiente"] = row["justificacao_minima_canonica"]
    step["nucleo"] = row["tese_minima_canonica"]
    step["estado_de_fecho_canonico"] = row["estado_de_fecho"]
    step["score_canonico_de_fecho"] = row["score_canonico_de_fecho"]
    step["tipos_de_fragilidade"] = row["tipos_de_fragilidade"]
    step["precisa_de_subpasso"] = row["precisa_de_subpasso"]
    step["subpasso_sugerido"] = row["subpasso_sugerido"]
    step["texto_meta_editorial_detectado"] = row["texto_meta_editorial_detectado"]
    step["requer_arbitragem_humana"] = row["requer_arbitragem_humana"]
    step["porque_o_anterior_nao_basta"] = row["porque_o_anterior_nao_basta"]
    step["porque_nao_pode_ser_suprimido"] = row["porque_nao_pode_ser_suprimido"]
    step["objecao_letal_a_bloquear"] = row["objecao_letal_a_bloquear"]
    step["tipo_de_necessidade"] = row["tipo_de_necessidade"]
    return step


def corridor_name_for_pid(pid: str) -> Optional[str]:
    for name, ids in CORREDORES.items():
        if pid in ids:
            return name
    return None


def build_dossier(name: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    sorted_rows = sorted(rows, key=lambda x: x["numero_final"])
    problemas = []
    for row in sorted_rows:
        if row["estado_de_fecho"] != "fechado" or row["precisa_de_subpasso"]:
            problemas.append({
                "id": row["id"],
                "estado_de_fecho": row["estado_de_fecho"],
                "tipos_de_fragilidade": row["tipos_de_fragilidade"],
                "subpasso_sugerido": row["subpasso_sugerido"],
                "objecao_letal_a_bloquear": row["objecao_letal_a_bloquear"],
            })

    return {
        "meta": {
            "gerado_em_utc": now_utc_iso(),
            "corredor": name,
            "objetivo": "Dossiê de fecho canónico por corredor, com inevitabilidades, subpassos e pontos a arbitrar.",
        },
        "resumo": {
            "total_passos": len(sorted_rows),
            "fechados": sum(1 for r in sorted_rows if r["estado_de_fecho"] == "fechado"),
            "quase_fechados": sum(1 for r in sorted_rows if r["estado_de_fecho"] == "quase_fechado"),
            "abertos": sum(1 for r in sorted_rows if r["estado_de_fecho"] == "aberto"),
            "passos_com_subpasso": [r["id"] for r in sorted_rows if r["precisa_de_subpasso"]],
        },
        "sequencia_minima_do_corredor": [r["id"] for r in sorted_rows],
        "proposicoes_canonicas": [{"id": r["id"], "texto": r["proposicao_canonica_curta"]} for r in sorted_rows],
        "problemas_ainda_abertos": problemas,
        "passos": sorted_rows,
    }


def build_report(rows: List[Dict[str, Any]], relatorio_v3: Dict[str, Any], argumentos_data: Any) -> Dict[str, Any]:
    existing_args, referenced_args = collect_argument_ids(argumentos_data)
    missing_args = sorted(referenced_args - existing_args)
    corredores_resumo = {}
    for corridor, ids in CORREDORES.items():
        subset = [r for r in rows if r["id"] in ids]
        corredores_resumo[corridor] = {
            "total": len(subset),
            "fechados": sum(1 for r in subset if r["estado_de_fecho"] == "fechado"),
            "abertos": sum(1 for r in subset if r["estado_de_fecho"] == "aberto"),
            "quase_fechados": sum(1 for r in subset if r["estado_de_fecho"] == "quase_fechado"),
            "subpassos": [r["id"] for r in subset if r["precisa_de_subpasso"]],
        }

    abertas = [r for r in rows if r["estado_de_fecho"] == "aberto"]
    mediais = [r for r in rows if "mediacao" in r["tipos_de_fragilidade"]]

    return {
        "meta": {
            "gerado_em_utc": now_utc_iso(),
            "script": Path(__file__).name,
            "versao": "4.0.0",
            "objetivo": "Relatório do fecho canónico: estado de fecho, fragilidades, subpassos e arbitragem necessária.",
        },
        "resumo_global": {
            "total_passos": len(rows),
            "estado_de_fecho": Counter(r["estado_de_fecho"] for r in rows),
            "tipos_de_fragilidade": Counter(f for r in rows for f in r["tipos_de_fragilidade"]),
            "passos_com_subpasso": [r["id"] for r in rows if r["precisa_de_subpasso"]],
            "passos_com_texto_meta_editorial": [r["id"] for r in rows if r["texto_meta_editorial_detectado"]],
            "passos_que_requerem_arbitragem_humana": [r["id"] for r in rows if r["requer_arbitragem_humana"]],
        },
        "corredores_criticos": corredores_resumo,
        "top_passos_mais_abertos": [
            {
                "id": r["id"],
                "score_canonico_de_fecho": r["score_canonico_de_fecho"],
                "tipos_de_fragilidade": r["tipos_de_fragilidade"],
                "subpasso_sugerido": r["subpasso_sugerido"],
            }
            for r in sorted(abertas, key=lambda x: x["score_canonico_de_fecho"])[:15]
        ],
        "top_passos_com_fragilidade_mediacional": [
            {
                "id": r["id"],
                "score_canonico_de_fecho": r["score_canonico_de_fecho"],
                "subpasso_sugerido": r["subpasso_sugerido"],
            }
            for r in sorted(mediais, key=lambda x: x["score_canonico_de_fecho"])[:15]
        ],
        "argumentos_referidos_mas_ausentes": missing_args,
        "continuidade_com_v3": {
            "resumo_global_v3": relatorio_v3.get("resumo_global", {}),
            "zonas_ainda_frageis_v3": relatorio_v3.get("zonas_ainda_frageis", []),
            "mediacoes_promoviveis_v3": relatorio_v3.get("mediacoes_promoviveis_a_passo", []),
        },
    }


def build_outputs(base_dir: Path, out_dir: Path) -> Dict[str, Path]:
    file_paths = {k: Path(v).resolve() for k, v in DEFAULT_FILES.items()}
    fontes_json = {k: str(v) for k, v in file_paths.items()}
    mapa_v3 = load_json(file_paths["mapa_v3"])
    relatorio_v3 = load_json(file_paths["relatorio_v3"])
    mapa_base = flatten_base_map(load_json(file_paths["mapa_base"]))
    revisao = index_by_key(load_json(file_paths["revisao"])["revisao_por_proposicao"], "proposicao_id")
    fechos = load_fechos({
        "p25_p30": file_paths["fecho_p25_p30"],
        "p33_p37": file_paths["fecho_p33_p37"],
        "p42_p48": file_paths["fecho_p42_p48"],
        "p50": file_paths["fecho_p50"],
    })
    impacto = index_impacto(load_json(file_paths["impacto"]))
    argumentos = load_json(file_paths["argumentos"])

    rows: List[Dict[str, Any]] = []
    precanonical_steps: List[Dict[str, Any]] = []

    for passo_v3 in mapa_v3.get("passos", []):
        pid = passo_v3["id"]
        bundle = StepBundle(
            pid=pid,
            passo_v3=passo_v3,
            passo_base=mapa_base.get(pid, {}),
            revisao=revisao.get(pid, {}),
            fecho=fechos.get(pid),
            impacto=impacto.get(pid, {}),
        )
        row = build_matrix_row(bundle)
        rows.append(row)
        precanonical_steps.append(build_precanonical_step(bundle, row))

    rows = sorted(rows, key=lambda x: x["numero_final"])
    precanonical_steps = sorted(precanonical_steps, key=lambda x: x["numero_final"])

    matriz = {
        "meta": {
            "gerado_em_utc": now_utc_iso(),
            "script": Path(__file__).name,
            "versao": "4.0.0",
            "objetivo": "Matriz de inevitabilidades do fecho canónico do mapa dedutivo.",
        },
        "fontes": fontes_json,
        "linhas": rows,
    }

    mapa_precanonico = {
        "meta": {
            "gerado_em_utc": now_utc_iso(),
            "script": Path(__file__).name,
            "versao": "4.0.0",
            "objetivo": "Mapa dedutivo pré-canónico, já limpo e preparado para arbitragem filosófica final.",
        },
        "fontes": fontes_json,
        "passos": precanonical_steps,
    }

    relatorio = build_report(rows, relatorio_v3, argumentos)

    out_dir.mkdir(parents=True, exist_ok=True)
    dossiers_dir = out_dir / "dossiers_corredor"
    dossiers_dir.mkdir(parents=True, exist_ok=True)

    matriz_path = out_dir / "matriz_inevitabilidades_v4.json"
    mapa_path = out_dir / "mapa_dedutivo_precanonico_v4.json"
    rel_path = out_dir / "relatorio_fecho_canonico_v4.json"
    write_json(matriz_path, matriz)
    write_json(mapa_path, mapa_precanonico)
    write_json(rel_path, relatorio)

    for corridor, ids in CORREDORES.items():
        subset = [row for row in rows if row["id"] in ids]
        dossier = build_dossier(corridor, subset)
        write_json(dossiers_dir / f"dossier_corredor_{corridor}.json", dossier)

    return {
        "matriz": matriz_path,
        "mapa_precanonico": mapa_path,
        "relatorio": rel_path,
        "dossiers_dir": dossiers_dir,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fechador canónico do mapa dedutivo.")
    parser.add_argument("--base-dir", default=str(ROOT), help="Diretório onde estão os JSON de entrada.")
    parser.add_argument("--out-dir", default=str(ROOT), help="Diretório para escrever as saídas.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    outputs = build_outputs(base_dir, out_dir)
    print("Fecho canónico concluído.")
    for name, path in outputs.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
