#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
reabrir_base_fragmentaria_confronto_v1.py

Reabre a base fragmentária real de um dossier de confronto já gerado,
reconstituindo os fragmentos, microlinhas, ramos, percursos e argumentos
herdados pelas proposições envolvidas.

Objetivos:
- impedir que o dossier de confronto fique apenas como compressão formal;
- devolver ao confronto a sua base viva de fragmentos tratados;
- preservar rastreabilidade total para a árvore e para o mapa dedutivo;
- gerar artefactos utilizáveis para revisão filosófica substantiva.

Inputs esperados:
- 16_validacao_integral/03_cadernos_confrontos/CFxx_dossier_confronto.md
- 16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json
- 15_arvore_do_pensamento/01_dados/arvore_do_pensamento_v1.json
- 14_mapa_dedutivo/impacto_fragmentos_no_mapa.json
- 14_mapa_dedutivo/02_mapa_dedutivo_arquitetura_fragmentos.json

Outputs:
- 16_validacao_integral/04_bases_fragmentarias_confrontos/CFxx_base_fragmentaria.json
- 16_validacao_integral/04_bases_fragmentarias_confrontos/CFxx_base_fragmentaria.md
- 16_validacao_integral/04_bases_fragmentarias_confrontos/indice_bases_fragmentarias_confrontos.json
- 16_validacao_integral/02_outputs/relatorio_reabertura_fragmentaria_CFxx_v1.txt
  (ou relatorio_reabertura_fragmentaria_all_v1.txt para execução em lote)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


# =============================================================================
# CONFIGURAÇÃO CANÓNICA
# =============================================================================

DEFAULT_INPUT_DOSSIER_DIR_RELATIVE = Path(
    "16_validacao_integral/03_cadernos_confrontos"
)
DEFAULT_INPUT_PROPOSICOES_RELATIVE = Path(
    "16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json"
)
DEFAULT_INPUT_TREE_RELATIVE = Path(
    "15_arvore_do_pensamento/01_dados/arvore_do_pensamento_v1.json"
)
DEFAULT_INPUT_IMPACT_RELATIVE = Path(
    "14_mapa_dedutivo/impacto_fragmentos_no_mapa.json"
)
DEFAULT_INPUT_ARCH_RELATIVE = Path(
    "14_mapa_dedutivo/02_mapa_dedutivo_arquitetura_fragmentos.json"
)

DEFAULT_OUTPUT_DIR_RELATIVE = Path(
    "16_validacao_integral/04_bases_fragmentarias_confrontos"
)
DEFAULT_OUTPUT_INDEX_RELATIVE = Path(
    "16_validacao_integral/04_bases_fragmentarias_confrontos/indice_bases_fragmentarias_confrontos.json"
)
DEFAULT_REPORT_ALL_RELATIVE = Path(
    "16_validacao_integral/02_outputs/relatorio_reabertura_fragmentaria_all_v1.txt"
)


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
    path.write_text(text, encoding="utf-8", newline="\n")


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
        script_path.parent.parent.parent,  # .../DoReal
        script_path.parent.parent,         # .../16_validacao_integral
        Path.cwd(),
        Path.cwd().parent,
        Path.cwd().parent.parent,
    ]

    for cand in candidates:
        cand = cand.resolve()
        if (cand / DEFAULT_INPUT_PROPOSICOES_RELATIVE).exists():
            return cand
        # caso raro: execução a partir de 16_validacao_integral
        if (cand / "01_dados" / "proposicoes_nucleares_enriquecidas_v1.json").exists():
            return cand.parent.resolve()

    return script_path.parent.parent.parent.resolve()


def resolve_relative(project_root: Path, relative_path: Path) -> Path:
    path = (project_root / relative_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {path}")
    return path


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


def order_from_prefixed_id(value: str, prefix: str) -> int:
    if not isinstance(value, str):
        return 10**9
    m = re.search(rf"^{re.escape(prefix)}[_\-]?0*(\d+)$", value.strip())
    if m:
        return int(m.group(1))
    m2 = re.search(r"(\d+)", value)
    return int(m2.group(1)) if m2 else 10**9


def parse_markdown_sections(text: str) -> Dict[str, str]:
    """
    Divide markdown por secções do tipo:
    ## 1. Identificação
    ## 20. Articulação estrutural
    """
    pattern = re.compile(r"^##\s+(\d+\.\s+.+?)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: Dict[str, str] = {}
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections[title] = body
    return sections


def extract_ids_from_text(text: str, prefix: str) -> List[str]:
    patt = re.compile(rf"\b{re.escape(prefix)}\d{{2,4}}\b")
    return unique_preserve(patt.findall(text or ""))


def extract_propositions_from_dossier_text(text: str) -> List[str]:
    sections = parse_markdown_sections(text)

    # Preferência 1: secção 20
    for sec_title in ("20. Articulação estrutural", "7. Proposições envolvidas"):
        body = sections.get(sec_title, "")
        ids = extract_ids_from_text(body, "P")
        if ids:
            return sorted(ids, key=lambda x: order_from_prefixed_id(x, "P"))

    # fallback: documento inteiro
    ids = extract_ids_from_text(text, "P")
    return sorted(ids, key=lambda x: order_from_prefixed_id(x, "P"))


def shorten(text: str, max_len: int = 280) -> str:
    text = normalize_spaces(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


# =============================================================================
# INDEXAÇÃO DE DADOS
# =============================================================================


def index_by_id(items: Sequence[Dict[str, Any]], key: str = "id") -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for item in items:
        item_id = safe_dict(item).get(key)
        if isinstance(item_id, str) and item_id:
            out[item_id] = item
    return out


def build_impact_index(impact_data: Any) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]:
    by_fragment: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_proposition: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for row in safe_list(impact_data):
        rowd = safe_dict(row)
        frag_id = rowd.get("fragmento_id") or rowd.get("id_fragmento") or rowd.get("fragment_id")
        prop_id = rowd.get("proposicao_id") or rowd.get("passo_id") or rowd.get("id_proposicao")
        if isinstance(frag_id, str) and frag_id:
            by_fragment[frag_id].append(rowd)
        if isinstance(prop_id, str) and prop_id:
            by_proposition[prop_id].append(rowd)

    return dict(by_fragment), dict(by_proposition)


def infer_proposition_text(prop: Dict[str, Any]) -> str:
    for key in ("texto", "texto_proposicao", "proposicao_texto", "descricao", "enunciado"):
        value = prop.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def infer_argument_summary(arg: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("conceito_alvo", "natureza", "criterio_ultimo"):
        val = arg.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(f"{key}: {val.strip()}")
    if not parts:
        estrutura = safe_dict(arg.get("estrutura_logica"))
        if estrutura:
            prem = estrutura.get("premissas")
            concl = estrutura.get("conclusao")
            if isinstance(concl, str) and concl.strip():
                parts.append(f"conclusao: {concl.strip()}")
            elif isinstance(prem, list) and prem:
                parts.append(f"premissas: {len(prem)}")
    return " | ".join(parts)


# =============================================================================
# RECOLHA DA BASE FRAGMENTÁRIA
# =============================================================================


def collect_from_propositions(
    proposition_ids: List[str],
    propositions_index: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    proposition_entries: List[Dict[str, Any]] = []
    missing: List[str] = []

    fragment_ids: List[str] = []
    microlinha_ids: List[str] = []
    ramo_ids: List[str] = []
    percurso_ids: List[str] = []
    argumento_ids: List[str] = []
    convergencia_ids: List[str] = []
    relacao_ids: List[str] = []

    for pid in proposition_ids:
        prop = propositions_index.get(pid)
        if not prop:
            missing.append(pid)
            continue

        arq = safe_dict(prop.get("arquitetura_origem"))
        entry = {
            "proposicao_id": pid,
            "texto": infer_proposition_text(prop),
            "texto_curto": prop.get("texto_curto"),
            "bloco_id": prop.get("bloco_id"),
            "bloco_titulo": prop.get("bloco_titulo"),
            "ordem_global": prop.get("ordem_global"),
            "arquitetura_origem": {
                "fragmento_ids": safe_list(arq.get("fragmento_ids")),
                "microlinha_ids": safe_list(arq.get("microlinha_ids")),
                "ramo_ids": safe_list(arq.get("ramo_ids")),
                "percurso_ids": safe_list(arq.get("percurso_ids")),
                "argumento_ids": safe_list(arq.get("argumento_ids")),
                "convergencia_ids": safe_list(arq.get("convergencia_ids")),
                "relacao_ids": safe_list(arq.get("relacao_ids")),
            },
        }
        proposition_entries.append(entry)

        fragment_ids.extend(entry["arquitetura_origem"]["fragmento_ids"])
        microlinha_ids.extend(entry["arquitetura_origem"]["microlinha_ids"])
        ramo_ids.extend(entry["arquitetura_origem"]["ramo_ids"])
        percurso_ids.extend(entry["arquitetura_origem"]["percurso_ids"])
        argumento_ids.extend(entry["arquitetura_origem"]["argumento_ids"])
        convergencia_ids.extend(entry["arquitetura_origem"]["convergencia_ids"])
        relacao_ids.extend(entry["arquitetura_origem"]["relacao_ids"])

    return {
        "propositions": proposition_entries,
        "missing_propositions": sorted(missing, key=lambda x: order_from_prefixed_id(x, "P")),
        "fragment_ids": sorted(unique_preserve(fragment_ids)),
        "microlinha_ids": sorted(unique_preserve(microlinha_ids), key=lambda x: order_from_prefixed_id(x, "ML")),
        "ramo_ids": sorted(unique_preserve(ramo_ids)),
        "percurso_ids": sorted(unique_preserve(percurso_ids)),
        "argumento_ids": sorted(unique_preserve(argumento_ids)),
        "convergencia_ids": sorted(unique_preserve(convergencia_ids)),
        "relacao_ids": sorted(unique_preserve(relacao_ids)),
    }


def collect_tree_entities(
    ids: List[str],
    index: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    out: List[Dict[str, Any]] = []
    missing: List[str] = []
    for item_id in ids:
        item = index.get(item_id)
        if item is None:
            missing.append(item_id)
            continue
        out.append(item)
    return out, missing


def summarize_fragment(fragment: Dict[str, Any], impacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    base = safe_dict(fragment.get("base_empirica"))
    cad = safe_dict(fragment.get("cadencia"))
    trat = safe_dict(fragment.get("tratamento_filosofico"))
    imp = safe_dict(fragment.get("impacto_mapa"))
    lig = safe_dict(fragment.get("ligacoes_arvore"))

    impacto_sintetico = []
    for row in impacts:
        rowd = safe_dict(row)
        small = {}
        for key in (
            "proposicao_id",
            "passo_id",
            "tipo_relacao",
            "grau_impacto",
            "funcao_no_mapa",
            "papel_no_corredor",
            "observacoes",
        ):
            val = rowd.get(key)
            if val not in (None, "", []):
                small[key] = val
        if small:
            impacto_sintetico.append(small)

    return {
        "id": fragment.get("id"),
        "origem_id": fragment.get("origem_id"),
        "ordem_no_ficheiro": fragment.get("ordem_no_ficheiro"),
        "texto_fragmento": base.get("texto_fragmento"),
        "texto_curto": shorten(base.get("texto_fragmento", "")),
        "ficheiro_origem": base.get("ficheiro_origem"),
        "tipo_unidade": safe_dict(base.get("segmentacao")).get("tipo_unidade"),
        "funcao_textual_dominante": base.get("funcao_textual_dominante"),
        "cadencia": {
            "funcao_cadencia_principal": cad.get("funcao_cadencia_principal"),
            "direcao_movimento": cad.get("direcao_movimento"),
            "centralidade": cad.get("centralidade"),
            "estatuto_no_percurso": cad.get("estatuto_no_percurso"),
            "zona_provavel_percurso": cad.get("zona_provavel_percurso"),
        },
        "tratamento_filosofico": trat if trat else None,
        "impacto_mapa_arvore": imp if imp else None,
        "impacto_no_mapa_registos": impacto_sintetico,
        "ligacoes_arvore": {
            "microlinha_ids": safe_list(lig.get("microlinha_ids")),
            "ramo_ids": safe_list(lig.get("ramo_ids")),
            "percurso_ids": safe_list(lig.get("percurso_ids")),
            "argumento_ids": safe_list(lig.get("argumento_ids")),
            "convergencia_ids": safe_list(lig.get("convergencia_ids")),
        },
        "estado_validacao": fragment.get("estado_validacao"),
        "estado_excecao": fragment.get("estado_excecao"),
        "excecao_ids": safe_list(fragment.get("excecao_ids")),
    }


def summarize_microlinha(item: Dict[str, Any]) -> Dict[str, Any]:
    crit = safe_dict(item.get("criterio_de_agregacao"))
    return {
        "id": item.get("id"),
        "titulo": item.get("titulo"),
        "descricao_funcional": item.get("descricao_funcional"),
        "fragmento_ids": safe_list(item.get("fragmento_ids")),
        "percurso_ids_sugeridos": safe_list(item.get("percurso_ids_sugeridos")),
        "argumento_ids_sugeridos": safe_list(item.get("argumento_ids_sugeridos")),
        "criterio_de_agregacao": crit if crit else None,
        "prioridade_de_consolidacao": item.get("prioridade_de_consolidacao"),
        "estado_validacao": item.get("estado_validacao"),
    }


def summarize_ramo(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id"),
        "titulo": item.get("titulo"),
        "descricao_funcional": item.get("descricao_funcional"),
        "criterio_de_unidade": item.get("criterio_de_unidade"),
        "microlinha_ids": safe_list(item.get("microlinha_ids")),
        "percurso_ids_associados": safe_list(item.get("percurso_ids_associados")),
        "argumento_ids_associados": safe_list(item.get("argumento_ids_associados")),
        "passo_ids_alvo": safe_list(item.get("passo_ids_alvo")),
        "prioridade_de_consolidacao": item.get("prioridade_de_consolidacao"),
        "estado_validacao": item.get("estado_validacao"),
    }


def summarize_percurso(item: Dict[str, Any]) -> Dict[str, Any]:
    meta = safe_dict(item.get("meta"))
    return {
        "id": item.get("id"),
        "titulo": meta.get("titulo") or item.get("titulo"),
        "regime": meta.get("regime"),
        "descricao": meta.get("descricao"),
        "ramo_ids": safe_list(item.get("ramo_ids")),
        "pressupostos_fecho_ids": safe_list(item.get("pressupostos_fecho_ids")),
        "directo": safe_list(item.get("directo")),
        "com_pressupostos": safe_list(item.get("com_pressupostos")),
        "estado_validacao": item.get("estado_validacao"),
    }


def summarize_argumento(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id"),
        "capitulo": item.get("capitulo"),
        "parte": item.get("parte"),
        "nivel": item.get("nivel"),
        "conceito_alvo": item.get("conceito_alvo"),
        "natureza": item.get("natureza"),
        "tipo_de_necessidade": item.get("tipo_de_necessidade"),
        "nivel_de_operacao": item.get("nivel_de_operacao"),
        "fundamenta": safe_list(item.get("fundamenta")),
        "outputs_instalados": safe_list(item.get("outputs_instalados")),
        "operacoes_chave": safe_list(item.get("operacoes_chave")),
        "ramo_ids": safe_list(item.get("ramo_ids")),
        "resumo": infer_argument_summary(item),
        "estado_validacao": item.get("estado_validacao"),
    }


def infer_fragment_coverage(
    proposition_ids: List[str],
    proposition_entries: List[Dict[str, Any]],
    impacts_by_prop: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    coverage: List[Dict[str, Any]] = []
    without_fragments: List[str] = []
    sem_impacto_explicito: List[str] = []

    for entry in proposition_entries:
        pid = entry["proposicao_id"]
        fragment_ids = safe_list(safe_dict(entry.get("arquitetura_origem")).get("fragmento_ids"))
        impact_rows = impacts_by_prop.get(pid, [])
        if not fragment_ids:
            without_fragments.append(pid)
        if not impact_rows:
            sem_impacto_explicito.append(pid)
        coverage.append(
            {
                "proposicao_id": pid,
                "n_fragmentos": len(fragment_ids),
                "n_registos_impacto": len(impact_rows),
            }
        )

    return {
        "proposicoes_alvo": proposition_ids,
        "cobertura_por_proposicao": coverage,
        "proposicoes_sem_fragmentos": without_fragments,
        "proposicoes_sem_registo_impacto_explicito": sem_impacto_explicito,
    }


# =============================================================================
# GERAÇÃO DO ARTEFACTO
# =============================================================================


def build_base_fragmentaria_payload(
    confronto_id: str,
    dossier_path: Path,
    dossier_text: str,
    proposition_ids: List[str],
    propositions_data: Dict[str, Any],
    tree_data: Dict[str, Any],
    impact_data: Any,
    arch_data: Dict[str, Any],
    project_root: Path,
) -> Tuple[Dict[str, Any], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    propositions_index = {
        p["proposicao_id"]: p
        for p in safe_list(safe_dict(propositions_data).get("proposicoes"))
        if isinstance(safe_dict(p).get("proposicao_id"), str)
    }

    fragment_index = index_by_id(safe_list(tree_data.get("fragmentos")))
    microlinha_index = index_by_id(safe_list(tree_data.get("microlinhas")))
    ramo_index = index_by_id(safe_list(tree_data.get("ramos")))
    percurso_index = index_by_id(safe_list(tree_data.get("percursos")))
    argumento_index = index_by_id(safe_list(tree_data.get("argumentos")))

    impacts_by_fragment, impacts_by_prop = build_impact_index(impact_data)

    collected = collect_from_propositions(proposition_ids, propositions_index)
    if collected["missing_propositions"]:
        warnings.append(
            "Proposições não encontradas nas proposições enriquecidas: "
            + ", ".join(collected["missing_propositions"])
        )

    fragments_raw, missing_fragments = collect_tree_entities(collected["fragment_ids"], fragment_index)
    microlinhas_raw, missing_microlinhas = collect_tree_entities(collected["microlinha_ids"], microlinha_index)
    ramos_raw, missing_ramos = collect_tree_entities(collected["ramo_ids"], ramo_index)
    percursos_raw, missing_percursos = collect_tree_entities(collected["percurso_ids"], percurso_index)
    argumentos_raw, missing_argumentos = collect_tree_entities(collected["argumento_ids"], argumento_index)

    if missing_fragments:
        warnings.append("Fragmentos não encontrados na árvore: " + ", ".join(missing_fragments[:20]))
    if missing_microlinhas:
        warnings.append("Microlinhas não encontradas na árvore: " + ", ".join(missing_microlinhas[:20]))
    if missing_ramos:
        warnings.append("Ramos não encontrados na árvore: " + ", ".join(missing_ramos[:20]))
    if missing_percursos:
        warnings.append("Percursos não encontrados na árvore: " + ", ".join(missing_percursos[:20]))
    if missing_argumentos:
        warnings.append("Argumentos não encontrados na árvore: " + ", ".join(missing_argumentos[:20]))

    fragments = [
        summarize_fragment(frag, impacts_by_fragment.get(frag.get("id", ""), []))
        for frag in fragments_raw
    ]
    microlinhas = [summarize_microlinha(x) for x in microlinhas_raw]
    ramos = [summarize_ramo(x) for x in ramos_raw]
    percursos = [summarize_percurso(x) for x in percursos_raw]
    argumentos = [summarize_argumento(x) for x in argumentos_raw]

    # Estatísticas e cobertura
    coverage = infer_fragment_coverage(
        proposition_ids=proposition_ids,
        proposition_entries=collected["propositions"],
        impacts_by_prop=impacts_by_prop,
    )
    stats = {
        "n_proposicoes_dossier": len(proposition_ids),
        "n_proposicoes_localizadas": len(collected["propositions"]),
        "n_fragmentos": len(fragments),
        "n_microlinhas": len(microlinhas),
        "n_ramos": len(ramos),
        "n_percursos": len(percursos),
        "n_argumentos": len(argumentos),
        "n_registos_impacto_fragmentos": sum(len(safe_list(f.get("impacto_no_mapa_registos"))) for f in fragments),
        "n_fragmentos_com_tratamento_filosofico": sum(1 for f in fragments if f.get("tratamento_filosofico")),
    }

    if stats["n_fragmentos"] == 0:
        errors.append("Nenhum fragmento foi reconstituído a partir das proposições do confronto.")
    if stats["n_fragmentos_com_tratamento_filosofico"] == 0:
        warnings.append("Nenhum fragmento reconstituído traz tratamento_filosofico preenchido na árvore.")

    # Secções do dossier base
    sections = parse_markdown_sections(dossier_text)
    dossier_snapshot = {
        "pergunta_central": sections.get("2. Pergunta central", ""),
        "descricao_do_confronto": sections.get("3. Descrição do confronto", ""),
        "tese_canonica_provisoria": sections.get("5. Tese canónica provisória", ""),
        "articulacao_estrutural": sections.get("20. Articulação estrutural", ""),
    }

    # Informação auxiliar do mapa arquitetural, se presente
    arch_meta = safe_dict(arch_data.get("meta"))
    arch_indices = safe_dict(arch_data.get("indices"))

    payload = {
        "metadata": {
            "script": "reabrir_base_fragmentaria_confronto_v1.py",
            "gerado_em": utc_now_iso(),
            "estado_global": "reaberto",
            "confronto_id": confronto_id,
            "project_root": str(project_root),
            "fontes": {
                "dossier_confronto": relpath_str(dossier_path, project_root),
                "proposicoes_nucleares_enriquecidas": relpath_str(project_root / DEFAULT_INPUT_PROPOSICOES_RELATIVE, project_root),
                "arvore_do_pensamento": relpath_str(project_root / DEFAULT_INPUT_TREE_RELATIVE, project_root),
                "impacto_fragmentos_no_mapa": relpath_str(project_root / DEFAULT_INPUT_IMPACT_RELATIVE, project_root),
                "arquitetura_fragmentos_mapa": relpath_str(project_root / DEFAULT_INPUT_ARCH_RELATIVE, project_root),
            },
        },
        "confronto": {
            "confronto_id": confronto_id,
            "dossier_snapshot": dossier_snapshot,
            "proposicoes_do_dossier": proposition_ids,
        },
        "estatisticas": stats,
        "cobertura": coverage,
        "proposicoes": collected["propositions"],
        "fragmentos": fragments,
        "microlinhas": microlinhas,
        "ramos": ramos,
        "percursos": percursos,
        "argumentos": argumentos,
        "arquitetura_auxiliar": {
            "meta_arquitetura_fragmentos": arch_meta if arch_meta else None,
            "indices_disponiveis": list(arch_indices.keys()) if arch_indices else [],
        },
        "validacao": {
            "erros": errors,
            "alertas": warnings,
            "status": "ok" if not errors else "com_erros",
        },
    }

    return payload, errors, warnings


def render_markdown_from_payload(payload: Dict[str, Any]) -> str:
    md: List[str] = []
    meta = safe_dict(payload.get("metadata"))
    confronto = safe_dict(payload.get("confronto"))
    estat = safe_dict(payload.get("estatisticas"))
    cobertura = safe_dict(payload.get("cobertura"))
    valid = safe_dict(payload.get("validacao"))

    confronto_id = confronto.get("confronto_id", "CF??")
    snapshot = safe_dict(confronto.get("dossier_snapshot"))

    md.append(f"# {confronto_id} — Base fragmentária reaberta")
    md.append("")
    md.append("## 1. Função deste ficheiro")
    md.append(
        "Este ficheiro reabre a base fragmentária real do confronto, devolvendo ao dossier "
        "os fragmentos, microlinhas, ramos, percursos e argumentos herdados pelas proposições envolvidas."
    )
    md.append("")

    md.append("## 2. Snapshot do dossier de confronto")
    if snapshot.get("pergunta_central"):
        md.append("### Pergunta central")
        md.append(snapshot["pergunta_central"])
        md.append("")
    if snapshot.get("tese_canonica_provisoria"):
        md.append("### Tese canónica provisória")
        md.append(snapshot["tese_canonica_provisoria"])
        md.append("")
    if snapshot.get("articulacao_estrutural"):
        md.append("### Articulação estrutural")
        md.append(snapshot["articulacao_estrutural"])
        md.append("")

    md.append("## 3. Estatísticas de reabertura")
    for key, value in estat.items():
        md.append(f"- **{key}**: {value}")
    md.append("")

    md.append("## 4. Cobertura por proposição")
    for row in safe_list(cobertura.get("cobertura_por_proposicao")):
        md.append(
            f"- **{row.get('proposicao_id')}** — fragmentos: {row.get('n_fragmentos')}, "
            f"registos de impacto: {row.get('n_registos_impacto')}"
        )
    if safe_list(cobertura.get("proposicoes_sem_fragmentos")):
        md.append("")
        md.append("### Proposições sem fragmentos")
        for pid in safe_list(cobertura.get("proposicoes_sem_fragmentos")):
            md.append(f"- {pid}")
    md.append("")

    md.append("## 5. Proposições do confronto e herança arquitetural")
    for prop in safe_list(payload.get("proposicoes")):
        md.append(f"### {prop.get('proposicao_id')}")
        texto = prop.get("texto") or ""
        if texto:
            md.append(texto)
        arq = safe_dict(prop.get("arquitetura_origem"))
        md.append(
            f"- fragmentos: {len(safe_list(arq.get('fragmento_ids')))} | "
            f"microlinhas: {len(safe_list(arq.get('microlinha_ids')))} | "
            f"ramos: {len(safe_list(arq.get('ramo_ids')))} | "
            f"percursos: {len(safe_list(arq.get('percurso_ids')))} | "
            f"argumentos: {len(safe_list(arq.get('argumento_ids')))}"
        )
        md.append("")
    md.append("")

    md.append("## 6. Fragmentos herdados")
    for frag in safe_list(payload.get("fragmentos")):
        md.append(f"### {frag.get('id')}")
        md.append(f"- origem: {frag.get('ficheiro_origem')} | tipo_unidade: {frag.get('tipo_unidade')}")
        if frag.get("texto_fragmento"):
            md.append("")
            md.append(frag["texto_fragmento"])
            md.append("")
        trat = frag.get("tratamento_filosofico")
        if trat:
            md.append("#### Tratamento filosófico")
            md.append("```json")
            md.append(json.dumps(trat, ensure_ascii=False, indent=2))
            md.append("```")
        registos = safe_list(frag.get("impacto_no_mapa_registos"))
        if registos:
            md.append("#### Registos de impacto no mapa")
            for reg in registos[:8]:
                md.append(f"- {json.dumps(reg, ensure_ascii=False)}")
        md.append("")
    if not safe_list(payload.get("fragmentos")):
        md.append("_Nenhum fragmento reconstituído._")
        md.append("")

    md.append("## 7. Microlinhas herdadas")
    for item in safe_list(payload.get("microlinhas")):
        md.append(f"- **{item.get('id')}** — {item.get('titulo')}")
    if not safe_list(payload.get("microlinhas")):
        md.append("_Nenhuma microlinha reconstituída._")
    md.append("")

    md.append("## 8. Ramos herdados")
    for item in safe_list(payload.get("ramos")):
        md.append(f"- **{item.get('id')}** — {item.get('titulo')}")
    if not safe_list(payload.get("ramos")):
        md.append("_Nenhum ramo reconstituído._")
    md.append("")

    md.append("## 9. Percursos herdados")
    for item in safe_list(payload.get("percursos")):
        title = item.get("titulo") or item.get("id")
        md.append(f"- **{item.get('id')}** — {title}")
    if not safe_list(payload.get("percursos")):
        md.append("_Nenhum percurso reconstituído._")
    md.append("")

    md.append("## 10. Argumentos herdados")
    for item in safe_list(payload.get("argumentos")):
        resume = item.get("resumo") or ""
        line = f"- **{item.get('id')}**"
        if resume:
            line += f" — {resume}"
        md.append(line)
    if not safe_list(payload.get("argumentos")):
        md.append("_Nenhum argumento reconstituído._")
    md.append("")

    md.append("## 11. Alertas da reabertura")
    errs = safe_list(valid.get("erros"))
    warns = safe_list(valid.get("alertas"))
    if not errs and not warns:
        md.append("- sem alertas")
    else:
        for e in errs:
            md.append(f"- ERRO: {e}")
        for w in warns:
            md.append(f"- ALERTA: {w}")
    md.append("")

    md.append("## 12. Próximo uso filosófico")
    md.append(
        "Usar este ficheiro em paralelo com o dossier de confronto para verificar se a pergunta central, "
        "a tese provisória e as objeções realmente condensam a massa fragmentária herdada, ou se simplificam, "
        "misturam ou deixam cair tensões importantes."
    )
    md.append("")

    return "\n".join(md).strip() + "\n"


def render_report(
    *,
    confronto_id: str,
    payload: Dict[str, Any],
    md_path: Path,
    json_path: Path,
    project_root: Path,
) -> str:
    estat = safe_dict(payload.get("estatisticas"))
    valid = safe_dict(payload.get("validacao"))
    lines = [
        f"Relatório de reabertura fragmentária — {confronto_id}",
        f"Gerado em: {utc_now_iso()}",
        "",
        "1. Estado geral",
        f"- status: {valid.get('status')}",
        f"- confronto_id: {confronto_id}",
        "",
        "2. Estatísticas",
    ]
    for key, value in estat.items():
        lines.append(f"- {key}: {value}")
    lines += [
        "",
        "3. Outputs",
        f"- JSON: {relpath_str(json_path, project_root)}",
        f"- Markdown: {relpath_str(md_path, project_root)}",
        "",
        "4. Alertas",
    ]
    errs = safe_list(valid.get("erros"))
    warns = safe_list(valid.get("alertas"))
    if not errs and not warns:
        lines.append("- sem alertas")
    else:
        for e in errs:
            lines.append(f"- ERRO: {e}")
        for w in warns:
            lines.append(f"- ALERTA: {w}")
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# EXECUÇÃO POR DOSSIER / LOTE
# =============================================================================


def find_dossier_path(
    *,
    project_root: Path,
    confronto_id: Optional[str],
    dossier_path_arg: Optional[Path],
) -> Path:
    if dossier_path_arg:
        path = dossier_path_arg.resolve()
        if not path.exists():
            raise FileNotFoundError(f"Dossier não encontrado: {path}")
        return path

    if not confronto_id:
        raise ValueError("É necessário indicar --confronto ou --dossier-path.")

    filename = f"{confronto_id}_dossier_confronto.md"
    path = (project_root / DEFAULT_INPUT_DOSSIER_DIR_RELATIVE / filename).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Dossier não encontrado: {path}")
    return path


def infer_confronto_id_from_path(path: Path) -> str:
    m = re.search(r"(CF\d{2})", path.name)
    if m:
        return m.group(1)
    raise ValueError(f"Não foi possível inferir confronto_id a partir de: {path.name}")


def load_core_inputs(project_root: Path) -> Tuple[Dict[str, Any], Dict[str, Any], Any, Dict[str, Any]]:
    proposicoes = read_json(resolve_relative(project_root, DEFAULT_INPUT_PROPOSICOES_RELATIVE))
    tree = read_json(resolve_relative(project_root, DEFAULT_INPUT_TREE_RELATIVE))
    impact = read_json(resolve_relative(project_root, DEFAULT_INPUT_IMPACT_RELATIVE))
    arch = read_json(resolve_relative(project_root, DEFAULT_INPUT_ARCH_RELATIVE))
    return proposicoes, tree, impact, arch


def output_paths_for_confronto(project_root: Path, confronto_id: str) -> Tuple[Path, Path, Path]:
    out_dir = (project_root / DEFAULT_OUTPUT_DIR_RELATIVE).resolve()
    json_path = out_dir / f"{confronto_id}_base_fragmentaria.json"
    md_path = out_dir / f"{confronto_id}_base_fragmentaria.md"
    report_path = (project_root / "16_validacao_integral" / "02_outputs" / f"relatorio_reabertura_fragmentaria_{confronto_id}_v1.txt").resolve()
    return json_path, md_path, report_path


def process_one(
    *,
    project_root: Path,
    dossier_path: Path,
    proposicoes_data: Dict[str, Any],
    tree_data: Dict[str, Any],
    impact_data: Any,
    arch_data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Path, Path, Path, List[str], List[str]]:
    confronto_id = infer_confronto_id_from_path(dossier_path)
    dossier_text = dossier_path.read_text(encoding="utf-8")
    proposition_ids = extract_propositions_from_dossier_text(dossier_text)

    payload, errors, warnings = build_base_fragmentaria_payload(
        confronto_id=confronto_id,
        dossier_path=dossier_path,
        dossier_text=dossier_text,
        proposition_ids=proposition_ids,
        propositions_data=proposicoes_data,
        tree_data=tree_data,
        impact_data=impact_data,
        arch_data=arch_data,
        project_root=project_root,
    )

    json_path, md_path, report_path = output_paths_for_confronto(project_root, confronto_id)
    write_json(json_path, payload)
    write_text(md_path, render_markdown_from_payload(payload))
    write_text(
        report_path,
        render_report(
            confronto_id=confronto_id,
            payload=payload,
            md_path=md_path,
            json_path=json_path,
            project_root=project_root,
        ),
    )

    return payload, json_path, md_path, report_path, errors, warnings


def all_dossiers(project_root: Path) -> List[Path]:
    dossier_dir = (project_root / DEFAULT_INPUT_DOSSIER_DIR_RELATIVE).resolve()
    return sorted(dossier_dir.glob("CF??_dossier_confronto.md"), key=lambda p: order_from_prefixed_id(p.stem, "CF"))


# =============================================================================
# CLI
# =============================================================================


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reabre a base fragmentária de um ou mais dossiers de confronto."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Raiz do projeto DoReal. Se omitido, tenta inferir a partir do script/CWD.",
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--confronto",
        type=str,
        default=None,
        help="ID do confronto (ex.: CF08).",
    )
    group.add_argument(
        "--dossier-path",
        type=Path,
        default=None,
        help="Caminho explícito para o dossier Markdown.",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Reabre todos os dossiers CFxx encontrados em 16_validacao_integral/03_cadernos_confrontos.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    if not args.confronto and not args.dossier_path and not args.all:
        print("ERRO FATAL: É necessário indicar --confronto, --dossier-path ou --all.", file=sys.stderr)
        return 1

    try:
        project_root = project_root_from_explicit_or_cwd(args.project_root)
        proposicoes_data, tree_data, impact_data, arch_data = load_core_inputs(project_root)

        payloads_for_index: List[Dict[str, Any]] = []
        all_errors: List[str] = []
        processed = 0

        if args.all:
            dossiers = all_dossiers(project_root)
            if not dossiers:
                print("ERRO FATAL: Nenhum dossier CFxx encontrado.", file=sys.stderr)
                return 1

            report_lines = [
                "Relatório de reabertura fragmentária — lote",
                f"Gerado em: {utc_now_iso()}",
                f"Project root: {project_root}",
                "",
                "Confrontos processados:",
            ]

            for dossier_path in dossiers:
                payload, json_path, md_path, report_path, errors, warnings = process_one(
                    project_root=project_root,
                    dossier_path=dossier_path,
                    proposicoes_data=proposicoes_data,
                    tree_data=tree_data,
                    impact_data=impact_data,
                    arch_data=arch_data,
                )
                processed += 1
                confronto_id = safe_dict(payload.get("confronto")).get("confronto_id", "CF??")
                estat = safe_dict(payload.get("estatisticas"))
                report_lines.append(
                    f"- {confronto_id}: fragmentos={estat.get('n_fragmentos')}, "
                    f"microlinhas={estat.get('n_microlinhas')}, ramos={estat.get('n_ramos')}, "
                    f"percursos={estat.get('n_percursos')}, argumentos={estat.get('n_argumentos')}, "
                    f"status={safe_dict(payload.get('validacao')).get('status')}"
                )
                for e in errors:
                    report_lines.append(f"  ERRO: {e}")
                    all_errors.append(f"{confronto_id}: {e}")
                for w in warnings:
                    report_lines.append(f"  ALERTA: {w}")

                payloads_for_index.append(
                    {
                        "confronto_id": confronto_id,
                        "json_path": relpath_str(json_path, project_root),
                        "markdown_path": relpath_str(md_path, project_root),
                        "report_path": relpath_str(report_path, project_root),
                        "estatisticas": estat,
                        "validacao": safe_dict(payload.get("validacao")),
                    }
                )

            write_text((project_root / DEFAULT_REPORT_ALL_RELATIVE).resolve(), "\n".join(report_lines) + "\n")
            write_json(
                (project_root / DEFAULT_OUTPUT_INDEX_RELATIVE).resolve(),
                {
                    "metadata": {
                        "script": "reabrir_base_fragmentaria_confronto_v1.py",
                        "gerado_em": utc_now_iso(),
                        "estado_global": "reaberto",
                        "project_root": str(project_root),
                    },
                    "bases_fragmentarias": sorted(
                        payloads_for_index,
                        key=lambda x: order_from_prefixed_id(x.get("confronto_id", ""), "CF"),
                    ),
                },
            )

            print(f"Bases fragmentárias reabertas: {processed}")
            print(f"Índice gerado em: {(project_root / DEFAULT_OUTPUT_INDEX_RELATIVE).resolve()}")
            print(f"Relatório gerado em: {(project_root / DEFAULT_REPORT_ALL_RELATIVE).resolve()}")
            if all_errors:
                print("Concluído com erros de reabertura/validação.")
                return 2
            print("Concluído sem erros de reabertura.")
            return 0

        dossier_path = find_dossier_path(
            project_root=project_root,
            confronto_id=args.confronto,
            dossier_path_arg=args.dossier_path,
        )
        payload, json_path, md_path, report_path, errors, warnings = process_one(
            project_root=project_root,
            dossier_path=dossier_path,
            proposicoes_data=proposicoes_data,
            tree_data=tree_data,
            impact_data=impact_data,
            arch_data=arch_data,
        )

        # atualiza índice de forma incremental
        index_path = (project_root / DEFAULT_OUTPUT_INDEX_RELATIVE).resolve()
        index_data: Dict[str, Any]
        if index_path.exists():
            try:
                index_data = safe_dict(read_json(index_path))
            except Exception:
                index_data = {}
        else:
            index_data = {}

        bases = safe_list(index_data.get("bases_fragmentarias"))
        confronto_id = safe_dict(payload.get("confronto")).get("confronto_id", infer_confronto_id_from_path(dossier_path))
        entry = {
            "confronto_id": confronto_id,
            "json_path": relpath_str(json_path, project_root),
            "markdown_path": relpath_str(md_path, project_root),
            "report_path": relpath_str(report_path, project_root),
            "estatisticas": safe_dict(payload.get("estatisticas")),
            "validacao": safe_dict(payload.get("validacao")),
        }
        bases = [b for b in bases if safe_dict(b).get("confronto_id") != confronto_id] + [entry]
        bases = sorted(bases, key=lambda x: order_from_prefixed_id(safe_dict(x).get("confronto_id", ""), "CF"))
        write_json(
            index_path,
            {
                "metadata": {
                    "script": "reabrir_base_fragmentaria_confronto_v1.py",
                    "gerado_em": utc_now_iso(),
                    "estado_global": "reaberto",
                    "project_root": str(project_root),
                },
                "bases_fragmentarias": bases,
            },
        )

        print(f"Base fragmentária gerada em: {md_path}")
        print(f"JSON gerado em: {json_path}")
        print(f"Relatório gerado em: {report_path}")
        if errors:
            print("Concluído com erros de reabertura/validação.")
            return 2
        print("Concluído sem erros de reabertura.")
        return 0

    except Exception as e:
        print(f"ERRO FATAL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
