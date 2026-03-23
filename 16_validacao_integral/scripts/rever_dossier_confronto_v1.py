#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
rever_dossier_confronto_v1.py

Revê formalmente um ou mais cadernos de confronto já gerados, produzindo:
- validação estrutural mínima das secções do dossier;
- extração de metadados operacionais a partir do Markdown;
- deteção de lacunas e inconsistências simples;
- relatório textual auditável;
- versão de trabalho em pasta `revisados/`, quando solicitada.

Não substitui a revisão filosófica humana. Funciona como etapa intermédia entre:
- geração automática dos cadernos; e
- revisão substantiva do conteúdo.

Inputs esperados:
- 16_validacao_integral/03_cadernos_confrontos/CFxx_dossier_confronto.md
- 16_validacao_integral/03_cadernos_confrontos/indice_cadernos_confrontos.json

Outputs:
- 16_validacao_integral/02_outputs/relatorio_revisao_dossier_CFxx_v1.txt
- opcionalmente:
  16_validacao_integral/03_cadernos_confrontos/revisados/CFxx_dossier_confronto_revisto.md
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


# =============================================================================
# CONFIGURAÇÃO CANÓNICA
# =============================================================================

DEFAULT_INPUT_DIR_RELATIVE = Path("16_validacao_integral/03_cadernos_confrontos")
DEFAULT_INPUT_INDEX_RELATIVE = Path(
    "16_validacao_integral/03_cadernos_confrontos/indice_cadernos_confrontos.json"
)
DEFAULT_OUTPUT_REVISED_DIR_RELATIVE = Path(
    "16_validacao_integral/03_cadernos_confrontos/revisados"
)
DEFAULT_REPORT_DIR_RELATIVE = Path("16_validacao_integral/02_outputs")


# =============================================================================
# ENUMS / CONSTANTES
# =============================================================================

VALID_ESTADO_ITEM = {
    "por_preencher",
    "preenchido",
    "revisto",
    "validado",
    "integrado",
}

VALID_GRAU_RISCO = {"baixo", "medio", "alto", "critico"}
VALID_GRAU_PRIORIDADE = {"baixa", "media", "alta", "estrutural", "critica"}

SECOES_MINIMAS_DOSSIER = {
    "1. Identificação",
    "2. Pergunta central",
    "3. Descrição do confronto",
    "4. Síntese adjudicada",
    "5. Tese canónica provisória",
    "6. Teses de sustentação",
    "7. Proposições envolvidas",
    "8. Pontes entre níveis associadas",
    "9. Ancoragens científicas associadas",
    "10. Campos do real relacionados",
    "12. Distinções conceptuais mínimas",
    "13. Objeções priorizadas",
    "22. Sequência de redação canónica",
    "23. Checklist de fecho",
}

SECOES_RECOMENDADAS = {
    "11. Subproblemas",
    "14. Insuficiências típicas identificadas",
    "15. Autores e tradições a mobilizar",
    "18. Linhas de tratamento",
    "21. Decisão de adjudicação",
    "24. Necessidades de trabalho",
    "25. Lacunas identificadas",
    "26. Notas de revisão humana",
}

REQUIRED_BOOL_FIELDS = {
    "exige_resposta_canonica",
    "precisa_capitulo_proprio",
    "precisa_subcapitulo",
    "precisa_argumento_canonico",
    "necessita_revisao_humana",
}

METADATA_KEYS = {
    "confronto_id",
    "problema_id",
    "tipo_de_problema",
    "nivel_arquitetonico",
    "grau_de_prioridade",
    "grau_de_risco",
    "grau_de_centralidade",
    "grau_de_cobertura_no_projeto",
    "estado_item",
    "exige_resposta_canonica",
    "precisa_capitulo_proprio",
    "precisa_subcapitulo",
    "precisa_argumento_canonico",
    "necessita_revisao_humana",
    "confiança_heurística",
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
    path.write_text(text, encoding="utf-8", newline="\n")



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
        script_path.parent.parent.parent,
        script_path.parent.parent,
        Path.cwd(),
        Path.cwd().parent,
        Path.cwd().parent.parent,
    ]

    for cand in candidates:
        if (cand / DEFAULT_INPUT_INDEX_RELATIVE).exists():
            return cand.resolve()

    return script_path.parent.parent.parent



def resolve_relative(project_root: Path, relative_path: Path) -> Path:
    path = (project_root / relative_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {path}")
    return path



def order_from_id(value: str, prefix: str) -> int:
    value = str(value or "")
    if value.startswith(prefix):
        suffix = value[len(prefix):]
        if suffix.isdigit():
            return int(suffix)
    return 0



def sim_nao_to_bool(value: str) -> Optional[bool]:
    v = normalize_spaces(value).strip("*").strip().lower()
    if v == "sim":
        return True
    if v == "não" or v == "nao":
        return False
    return None



def bool_to_sim_nao(value: bool) -> str:
    return "Sim" if value else "Não"



def markdown_code_unwrap(value: str) -> str:
    v = normalize_spaces(value)
    if v.startswith("`") and v.endswith("`") and len(v) >= 2:
        return v[1:-1]
    return v



def slug_report_name(cf_id: str) -> str:
    return f"relatorio_revisao_dossier_{cf_id}_v1.txt"



def make_revision_filename(source_name: str) -> str:
    stem = source_name[:-3] if source_name.lower().endswith(".md") else source_name
    return f"{stem}_revisto.md"


# =============================================================================
# PARSER DE MARKDOWN
# =============================================================================


HEADING_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)
LIST_FIELD_RE = re.compile(r"^-\s+([A-Za-zÀ-ÿ_çÇãõáéíóúâêô0-9]+):\s*(.+?)\s*$")
PN_RE = re.compile(r"\bPN\d{2}\b")
AC_RE = re.compile(r"\bAC\d{2}\b")
CR_RE = re.compile(r"\bCR\d{2}\b")
P_RE = re.compile(r"\bP\d{2}\b")
CF_RE = re.compile(r"\bCF\d{2}\b")
CHECKBOX_RE = re.compile(r"^-\s+\[( |x|X)\]\s+(.+?)\s*$", re.MULTILINE)
OBJ_RE = re.compile(r"^-\s+\[(\d+)\]\s+(.+)$", re.MULTILINE)



def split_sections(markdown: str) -> Tuple[str, Dict[str, str], List[str]]:
    matches = list(HEADING_RE.finditer(markdown))
    preamble_end = matches[0].start() if matches else len(markdown)
    preamble = markdown[:preamble_end].strip()
    sections: Dict[str, str] = {}
    order: List[str] = []

    for i, match in enumerate(matches):
        title = normalize_spaces(match.group("title"))
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        body = markdown[body_start:body_end].strip()
        sections[title] = body
        order.append(title)

    return preamble, sections, order



def parse_identificacao(section_text: str) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    for line in section_text.splitlines():
        m = LIST_FIELD_RE.match(line.strip())
        if not m:
            continue
        key, raw = m.group(1), m.group(2)
        value = raw.strip()
        if key in REQUIRED_BOOL_FIELDS:
            parsed = sim_nao_to_bool(value)
            meta[key] = parsed if parsed is not None else value
        elif key == "confiança_heurística":
            try:
                meta[key] = float(markdown_code_unwrap(value).replace(",", "."))
            except Exception:
                meta[key] = markdown_code_unwrap(value)
        else:
            meta[key] = markdown_code_unwrap(value).strip("*").strip()
    return meta



def extract_ids(text: str, pattern: re.Pattern[str]) -> List[str]:
    return sorted(set(pattern.findall(text)), key=lambda x: order_from_id(x, x[:2] if len(x) >= 2 else ""))



def extract_checklist(section_text: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for m in CHECKBOX_RE.finditer(section_text):
        items.append({
            "marcado": m.group(1).strip().lower() == "x",
            "texto": normalize_spaces(m.group(2)),
        })
    return items



def extract_bullets(section_text: str) -> List[str]:
    out: List[str] = []
    for line in section_text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            out.append(normalize_spaces(line[2:]))
    return out



def parse_dossier(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    preamble, sections, order = split_sections(raw)

    title_line = ""
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("# "):
            title_line = line[2:].strip()
            break

    identificacao = parse_identificacao(sections.get("1. Identificação", ""))
    cf_from_title = next(iter(extract_ids(title_line, CF_RE)), "")
    cf_from_ident = str(identificacao.get("confronto_id", "")).strip()
    cf_id = cf_from_ident or cf_from_title or path.stem[:4]

    articulacao = sections.get("20. Articulação estrutural", "")
    secoes_presentes = set(order)

    return {
        "path": str(path),
        "nome_ficheiro": path.name,
        "titulo": title_line,
        "confronto_id": cf_id,
        "raw": raw,
        "preamble": preamble,
        "sections": sections,
        "section_order": order,
        "secoes_presentes": sorted(secoes_presentes),
        "identificacao": identificacao,
        "pergunta_central": normalize_spaces(sections.get("2. Pergunta central", "")),
        "tese_canonica": normalize_spaces(sections.get("5. Tese canónica provisória", "")),
        "decisao_adjudicacao": normalize_spaces(sections.get("21. Decisão de adjudicação", "")),
        "notas_revisao_humana": normalize_spaces(sections.get("26. Notas de revisão humana", "")),
        "lacunas_identificadas": extract_bullets(sections.get("25. Lacunas identificadas", "")),
        "necessidades_trabalho": extract_bullets(sections.get("24. Necessidades de trabalho", "")),
        "objeções": [normalize_spaces(m.group(2)) for m in OBJ_RE.finditer(sections.get("13. Objeções priorizadas", ""))],
        "checklist": extract_checklist(sections.get("23. Checklist de fecho", "")),
        "ids_proposicoes_sec7": extract_ids(sections.get("7. Proposições envolvidas", ""), P_RE),
        "ids_pontes_sec8": extract_ids(sections.get("8. Pontes entre níveis associadas", ""), PN_RE),
        "ids_ancoragens_sec9": extract_ids(sections.get("9. Ancoragens científicas associadas", ""), AC_RE),
        "ids_campos_sec10": extract_ids(sections.get("10. Campos do real relacionados", ""), CR_RE),
        "ids_proposicoes_sec20": extract_ids(articulacao, P_RE),
        "ids_pontes_sec20": extract_ids(articulacao, PN_RE),
        "ids_ancoragens_sec20": extract_ids(articulacao, AC_RE),
        "ids_campos_sec20": extract_ids(articulacao, CR_RE),
    }


# =============================================================================
# VALIDAÇÃO E REVISÃO FORMAL
# =============================================================================



def compare_sets(left: Iterable[str], right: Iterable[str]) -> Dict[str, List[str]]:
    lset = set(left)
    rset = set(right)
    return {
        "apenas_esquerda": sorted(lset - rset, key=lambda x: order_from_id(x, x[:2])),
        "apenas_direita": sorted(rset - lset, key=lambda x: order_from_id(x, x[:2])),
    }



def revisar_dossier(
    dossier: Dict[str, Any],
    index_entry: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    erros: List[str] = []
    alertas: List[str] = []
    observacoes: List[str] = []

    secs = set(dossier["secoes_presentes"])
    missing_required = sorted(SECOES_MINIMAS_DOSSIER - secs)
    missing_recommended = sorted(SECOES_RECOMENDADAS - secs)

    if missing_required:
        for sec in missing_required:
            erros.append(f"Secção obrigatória em falta: {sec}")
    if missing_recommended:
        for sec in missing_recommended:
            alertas.append(f"Secção recomendada em falta: {sec}")

    meta = dossier["identificacao"]
    meta_keys_present = set(meta.keys())
    missing_meta = sorted(METADATA_KEYS - meta_keys_present)
    for key in missing_meta:
        alertas.append(f"Metadado em falta na identificação: {key}")

    estado_item = str(meta.get("estado_item", "")).strip()
    if estado_item and estado_item not in VALID_ESTADO_ITEM:
        erros.append(f"estado_item inválido: {estado_item}")

    grau_risco = str(meta.get("grau_de_risco", "")).strip()
    if grau_risco and grau_risco not in VALID_GRAU_RISCO:
        erros.append(f"grau_de_risco inválido: {grau_risco}")

    grau_prioridade = str(meta.get("grau_de_prioridade", "")).strip()
    if grau_prioridade and grau_prioridade not in VALID_GRAU_PRIORIDADE:
        erros.append(f"grau_de_prioridade inválido: {grau_prioridade}")

    for key in REQUIRED_BOOL_FIELDS:
        if key in meta and not isinstance(meta[key], bool):
            alertas.append(f"Campo booleano não normalizado: {key}={meta[key]!r}")

    confianca = meta.get("confiança_heurística")
    if isinstance(confianca, float) and not (0.0 <= confianca <= 1.0):
        erros.append(f"confiança_heurística fora de intervalo [0,1]: {confianca}")

    if not dossier["pergunta_central"]:
        erros.append("Pergunta central vazia.")
    if not dossier["tese_canonica"]:
        erros.append("Tese canónica provisória vazia.")
    if len(dossier["ids_proposicoes_sec7"]) == 0:
        erros.append("Sem proposições identificadas na secção 7.")
    if len(dossier["objeções"]) == 0:
        alertas.append("Sem objeções priorizadas detetadas.")
    if len(dossier["checklist"]) == 0:
        alertas.append("Checklist de fecho vazia ou não reconhecida.")

    cmp_props = compare_sets(dossier["ids_proposicoes_sec7"], dossier["ids_proposicoes_sec20"])
    cmp_pontes = compare_sets(dossier["ids_pontes_sec8"], dossier["ids_pontes_sec20"])
    cmp_anc = compare_sets(dossier["ids_ancoragens_sec9"], dossier["ids_ancoragens_sec20"])
    cmp_campos = compare_sets(dossier["ids_campos_sec10"], dossier["ids_campos_sec20"])

    if cmp_props["apenas_esquerda"] or cmp_props["apenas_direita"]:
        alertas.append(
            "Inconsistência entre secção 7 e secção 20 nas proposições: "
            f"sec7_only={cmp_props['apenas_esquerda']} sec20_only={cmp_props['apenas_direita']}"
        )
    if cmp_pontes["apenas_esquerda"] or cmp_pontes["apenas_direita"]:
        alertas.append(
            "Inconsistência entre secção 8 e secção 20 nas pontes: "
            f"sec8_only={cmp_pontes['apenas_esquerda']} sec20_only={cmp_pontes['apenas_direita']}"
        )
    if cmp_anc["apenas_esquerda"] or cmp_anc["apenas_direita"]:
        alertas.append(
            "Inconsistência entre secção 9 e secção 20 nas ancoragens: "
            f"sec9_only={cmp_anc['apenas_esquerda']} sec20_only={cmp_anc['apenas_direita']}"
        )
    if cmp_campos["apenas_esquerda"] or cmp_campos["apenas_direita"]:
        alertas.append(
            "Inconsistência entre secção 10 e secção 20 nos campos: "
            f"sec10_only={cmp_campos['apenas_esquerda']} sec20_only={cmp_campos['apenas_direita']}"
        )

    if isinstance(meta.get("necessita_revisao_humana"), bool):
        need_human = bool(meta["necessita_revisao_humana"])
        has_notes = bool(dossier["notas_revisao_humana"])
        if need_human and not has_notes:
            alertas.append("necessita_revisao_humana=Sim, mas a secção 26 está vazia.")
        if (not need_human) and has_notes:
            alertas.append("Há notas de revisão humana, mas o metadado indica que não necessita revisão humana.")

    if index_entry:
        idx_cf = str(index_entry.get("confronto_id", "")).strip()
        if idx_cf and idx_cf != dossier["confronto_id"]:
            erros.append(
                f"confronto_id divergente entre dossier ({dossier['confronto_id']}) e índice ({idx_cf})"
            )
        idx_estado = str(index_entry.get("estado_item", "")).strip()
        if idx_estado and estado_item and idx_estado != estado_item:
            alertas.append(
                f"estado_item difere do índice: dossier={estado_item} índice={idx_estado}"
            )
        idx_prioridade = str(index_entry.get("grau_de_prioridade", "")).strip()
        if idx_prioridade and grau_prioridade and idx_prioridade != grau_prioridade:
            alertas.append(
                f"grau_de_prioridade difere do índice: dossier={grau_prioridade} índice={idx_prioridade}"
            )

    score = 100
    score -= 12 * len(erros)
    score -= 4 * len(alertas)
    score = max(0, score)

    if erros:
        status_revisao = "com_erros"
    elif alertas:
        status_revisao = "com_alertas"
    else:
        status_revisao = "ok"

    if score >= 90:
        prontidao = "alta"
    elif score >= 75:
        prontidao = "media"
    else:
        prontidao = "baixa"

    observacoes.append(
        f"Prontidão formal estimada: {prontidao} (score={score}/100)."
    )
    if missing_required:
        observacoes.append("Há falhas estruturais obrigatórias que devem ser corrigidas antes de revisão substantiva.")
    elif cmp_pontes["apenas_esquerda"] or cmp_pontes["apenas_direita"]:
        observacoes.append("Convém harmonizar pontes entre a secção 8 e a secção 20 antes da redação canónica.")

    return {
        "confronto_id": dossier["confronto_id"],
        "nome_ficheiro": dossier["nome_ficheiro"],
        "status_revisao": status_revisao,
        "score_formal": score,
        "prontidao_formal": prontidao,
        "erros": erros,
        "alertas": alertas,
        "observacoes": observacoes,
        "resumo": {
            "grau_de_prioridade": grau_prioridade,
            "grau_de_risco": grau_risco,
            "estado_item": estado_item,
            "necessita_revisao_humana": meta.get("necessita_revisao_humana"),
            "num_proposicoes": len(dossier["ids_proposicoes_sec7"]),
            "num_pontes": len(dossier["ids_pontes_sec8"]),
            "num_ancoragens": len(dossier["ids_ancoragens_sec9"]),
            "num_campos": len(dossier["ids_campos_sec10"]),
            "num_objeções": len(dossier["objeções"]),
            "num_itens_checklist": len(dossier["checklist"]),
            "num_lacunas": len(dossier["lacunas_identificadas"]),
        },
        "comparacoes": {
            "proposicoes": cmp_props,
            "pontes": cmp_pontes,
            "ancoragens": cmp_anc,
            "campos": cmp_campos,
        },
    }


# =============================================================================
# ÍNDICE E RESOLUÇÃO DE FICHEIROS
# =============================================================================



def load_index_map(index_path: Path) -> Dict[str, Dict[str, Any]]:
    if not index_path.exists():
        return {}
    data = read_json(index_path)
    if isinstance(data, dict):
        if isinstance(data.get("cadernos"), list):
            items = data["cadernos"]
        elif isinstance(data.get("itens"), list):
            items = data["itens"]
        else:
            items = []
    elif isinstance(data, list):
        items = data
    else:
        items = []

    out: Dict[str, Dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        cf = str(item.get("confronto_id", "")).strip()
        if cf:
            out[cf] = item
    return out



def resolve_target_dossiers(
    input_dir: Path,
    all_dossiers: bool,
    confronto: Optional[str],
    dossier_path: Optional[Path],
) -> List[Path]:
    if dossier_path:
        if not dossier_path.exists():
            raise FileNotFoundError(f"Dossier não encontrado: {dossier_path}")
        return [dossier_path.resolve()]

    if confronto:
        cf = confronto.strip().upper()
        target = input_dir / f"{cf}_dossier_confronto.md"
        if not target.exists():
            raise FileNotFoundError(f"Dossier do confronto não encontrado: {target}")
        return [target.resolve()]

    if all_dossiers:
        paths = sorted(input_dir.glob("CF??_dossier_confronto.md"), key=lambda p: order_from_id(p.name[:4], "CF"))
        if not paths:
            raise FileNotFoundError(f"Nenhum dossier encontrado em: {input_dir}")
        return [p.resolve() for p in paths]

    raise ValueError("É necessário indicar --confronto, --dossier-path ou --all.")


# =============================================================================
# OUTPUTS
# =============================================================================



def build_revision_header(result: Dict[str, Any]) -> str:
    resumo = result["resumo"]
    lines = [
        "<!--",
        "REVISÃO FORMAL AUTOMÁTICA",
        f"confronto_id: {result['confronto_id']}",
        f"status_revisao: {result['status_revisao']}",
        f"score_formal: {result['score_formal']}",
        f"prontidao_formal: {result['prontidao_formal']}",
        f"grau_de_prioridade: {resumo.get('grau_de_prioridade', '')}",
        f"grau_de_risco: {resumo.get('grau_de_risco', '')}",
        f"necessita_revisao_humana: {bool_to_sim_nao(bool(resumo.get('necessita_revisao_humana')))}",
        f"gerado_em: {utc_now_iso()}",
        "-->",
        "",
    ]
    return "\n".join(lines)



def build_report_text(
    project_root: Path,
    dossier: Dict[str, Any],
    result: Dict[str, Any],
    source_path: Path,
    revised_path: Optional[Path],
) -> str:
    r = result
    resumo = r["resumo"]
    comps = r["comparacoes"]

    lines: List[str] = []
    lines.append("RELATÓRIO DE REVISÃO DE DOSSIER DE CONFRONTO")
    lines.append("")
    lines.append(f"Confronto: {r['confronto_id']}")
    lines.append(f"Ficheiro de origem: {relpath_str(source_path, project_root)}")
    if revised_path:
        lines.append(f"Ficheiro revisto: {relpath_str(revised_path, project_root)}")
    lines.append(f"Gerado em (UTC): {utc_now_iso()}")
    lines.append("")

    lines.append("1. Estado global da revisão")
    lines.append(f"- status_revisao: {r['status_revisao']}")
    lines.append(f"- score_formal: {r['score_formal']}/100")
    lines.append(f"- prontidao_formal: {r['prontidao_formal']}")
    lines.append("")

    lines.append("2. Resumo do dossier")
    lines.append(f"- grau_de_prioridade: {resumo.get('grau_de_prioridade', '')}")
    lines.append(f"- grau_de_risco: {resumo.get('grau_de_risco', '')}")
    lines.append(f"- estado_item: {resumo.get('estado_item', '')}")
    lines.append(f"- necessita_revisao_humana: {resumo.get('necessita_revisao_humana')}")
    lines.append(f"- número de proposições: {resumo.get('num_proposicoes', 0)}")
    lines.append(f"- número de pontes: {resumo.get('num_pontes', 0)}")
    lines.append(f"- número de ancoragens: {resumo.get('num_ancoragens', 0)}")
    lines.append(f"- número de campos: {resumo.get('num_campos', 0)}")
    lines.append(f"- número de objeções: {resumo.get('num_objeções', 0)}")
    lines.append(f"- número de itens de checklist: {resumo.get('num_itens_checklist', 0)}")
    lines.append("")

    lines.append("3. Comparações estruturais internas")
    lines.append(
        f"- proposições (secção 7 vs 20): sec7_only={comps['proposicoes']['apenas_esquerda']} sec20_only={comps['proposicoes']['apenas_direita']}"
    )
    lines.append(
        f"- pontes (secção 8 vs 20): sec8_only={comps['pontes']['apenas_esquerda']} sec20_only={comps['pontes']['apenas_direita']}"
    )
    lines.append(
        f"- ancoragens (secção 9 vs 20): sec9_only={comps['ancoragens']['apenas_esquerda']} sec20_only={comps['ancoragens']['apenas_direita']}"
    )
    lines.append(
        f"- campos (secção 10 vs 20): sec10_only={comps['campos']['apenas_esquerda']} sec20_only={comps['campos']['apenas_direita']}"
    )
    lines.append("")

    lines.append("4. Erros")
    if r["erros"]:
        for item in r["erros"]:
            lines.append(f"- {item}")
    else:
        lines.append("- nenhum")
    lines.append("")

    lines.append("5. Alertas")
    if r["alertas"]:
        for item in r["alertas"]:
            lines.append(f"- {item}")
    else:
        lines.append("- nenhum")
    lines.append("")

    lines.append("6. Observações operacionais")
    if r["observacoes"]:
        for item in r["observacoes"]:
            lines.append(f"- {item}")
    else:
        lines.append("- nenhuma")
    lines.append("")

    lines.append("7. Próximo ato sugerido")
    if r["status_revisao"] == "com_erros":
        lines.append("- Corrigir erros estruturais mínimos antes de iniciar revisão substantiva.")
    elif r["status_revisao"] == "com_alertas":
        lines.append("- Harmonizar alertas principais e só depois avançar para redação canónica.")
    else:
        lines.append("- Dossier formalmente apto para revisão filosófica humana substantiva.")

    return "\n".join(lines).rstrip() + "\n"


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================



def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Revê formalmente dossiers de confronto em Markdown."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Raiz explícita do projeto DoReal.",
    )
    parser.add_argument(
        "--confronto",
        type=str,
        default=None,
        help="Identificador do confronto (ex.: CF08).",
    )
    parser.add_argument(
        "--dossier-path",
        type=Path,
        default=None,
        help="Caminho explícito para um dossier Markdown.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Revê todos os dossiers encontrados em 03_cadernos_confrontos.",
    )
    parser.add_argument(
        "--emitir-revisado",
        action="store_true",
        help="Cria uma cópia de trabalho em 03_cadernos_confrontos/revisados com cabeçalho de revisão.",
    )
    parser.add_argument(
        "--overwrite-revisado",
        action="store_true",
        help="Permite substituir ficheiros já existentes na pasta revisados.",
    )
    parser.add_argument(
        "--json-summary",
        action="store_true",
        help="Também gera um resumo JSON por dossier ao lado do relatório TXT.",
    )
    return parser.parse_args(argv)



def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    try:
        project_root = project_root_from_explicit_or_cwd(args.project_root)
        input_dir = resolve_relative(project_root, DEFAULT_INPUT_DIR_RELATIVE)
        index_path = resolve_relative(project_root, DEFAULT_INPUT_INDEX_RELATIVE)
        report_dir = (project_root / DEFAULT_REPORT_DIR_RELATIVE).resolve()
        revised_dir = (project_root / DEFAULT_OUTPUT_REVISED_DIR_RELATIVE).resolve()

        targets = resolve_target_dossiers(
            input_dir=input_dir,
            all_dossiers=args.all,
            confronto=args.confronto,
            dossier_path=args.dossier_path,
        )
        index_map = load_index_map(index_path)

        total_errors = 0
        total_alerts = 0
        status_counter: Counter[str] = Counter()
        revised_written: List[Path] = []
        reports_written: List[Path] = []

        for dossier_path in targets:
            dossier = parse_dossier(dossier_path)
            index_entry = index_map.get(dossier["confronto_id"])
            result = revisar_dossier(dossier, index_entry=index_entry)

            status_counter[result["status_revisao"]] += 1
            total_errors += len(result["erros"])
            total_alerts += len(result["alertas"])

            revised_path: Optional[Path] = None
            if args.emitir_revisado:
                revised_path = revised_dir / make_revision_filename(dossier_path.name)
                if revised_path.exists() and not args.overwrite_revisado:
                    raise FileExistsError(
                        f"Ficheiro revisto já existe (use --overwrite-revisado): {revised_path}"
                    )
                revised_path.parent.mkdir(parents=True, exist_ok=True)
                write_text(revised_path, build_revision_header(result) + dossier["raw"].lstrip())
                revised_written.append(revised_path)

            report_path = report_dir / slug_report_name(dossier["confronto_id"])
            report_text = build_report_text(
                project_root=project_root,
                dossier=dossier,
                result=result,
                source_path=dossier_path,
                revised_path=revised_path,
            )
            write_text(report_path, report_text)
            reports_written.append(report_path)

            if args.json_summary:
                summary_path = report_dir / slug_report_name(dossier["confronto_id"]).replace(".txt", ".json")
                write_json(summary_path, {
                    "gerado_em": utc_now_iso(),
                    "confronto_id": dossier["confronto_id"],
                    "source_path": relpath_str(dossier_path, project_root),
                    "revised_path": relpath_str(revised_path, project_root) if revised_path else None,
                    "resultado_revisao": result,
                })

        if len(targets) == 1:
            print(f"Relatório gerado em: {reports_written[0]}")
            if revised_written:
                print(f"Ficheiro revisto gerado em: {revised_written[0]}")
        else:
            print(f"Dossiers revistos: {len(targets)}")
            print(f"Relatórios gerados em: {report_dir}")
            if revised_written:
                print(f"Ficheiros revistos gerados em: {revised_dir}")

        if total_errors == 0:
            if total_alerts == 0:
                print("Concluído sem erros nem alertas formais.")
            else:
                print("Concluído sem erros fatais, mas com alertas formais.")
            return 0

        print("Concluído com erros de validação/revisão formal.")
        return 2

    except Exception as exc:
        print(f"ERRO FATAL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
