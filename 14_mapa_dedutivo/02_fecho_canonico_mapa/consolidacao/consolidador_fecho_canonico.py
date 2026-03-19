#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

PIPELINE_VERSION = "1.0.0"
STEP_ID_RE = re.compile(r"^P\d{2}$")
SUBSTEP_ID_RE = re.compile(r"^P\d{2}_SP\d{2}$")
CORRIDOR_ID_RE = re.compile(r"^P\d{2}(?:_P\d{2})?$")
FRAGMENT_ID_RE = re.compile(r"^F[0-9A-Z_]+$")


class ConsolidationError(Exception):
    """Erro de consolidação terminal do pipeline."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def json_load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def json_dump(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def unique_preserve_order(values: Iterable[Any]) -> List[Any]:
    seen = set()
    result = []
    for value in values:
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else repr(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def cleaned_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return re.sub(r"\s+", " ", str(value)).strip()


def string_list(values: Any) -> List[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        values = [values]
    output: List[str] = []
    for item in values:
        text = cleaned_string(item)
        if text:
            output.append(text)
    return unique_preserve_order(output)


def path_to_string(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve())).replace("\\", "/")
    except Exception:
        return os.path.relpath(str(path.resolve()), str(base_dir.resolve())).replace("\\", "/")


def numeric_step_id(step_id: str) -> int:
    if not STEP_ID_RE.match(step_id):
        raise ConsolidationError(f"Passo inválido: {step_id}")
    return int(step_id[1:])


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent

    parser = argparse.ArgumentParser(
        description="Consolidador terminal local e determinístico do fecho canónico."
    )
    parser.add_argument("--base-dir", default=str(project_dir), help="Diretório-base do projeto local.")
    parser.add_argument("--manifesto", default="manifesto_fecho_canonico.json", help="Manifesto do pipeline.")
    parser.add_argument(
        "--agregador",
        default="outputs/decisoes_canonicas_intermedias_consolidado_final_intermedio.json",
        help="Agregador normativo consolidado.",
    )
    parser.add_argument(
        "--mapa",
        default="../01_reconstrucao_mapa_v2/mapa_dedutivo_precanonico_v4.json",
        help="Mapa dedutivo pré-canónico.",
    )
    parser.add_argument(
        "--matriz",
        default="../01_reconstrucao_mapa_v2/matriz_inevitabilidades_v4.json",
        help="Matriz de inevitabilidades v4.",
    )
    parser.add_argument(
        "--relatorio",
        default="../01_reconstrucao_mapa_v2/relatorio_fecho_canonico_v4.json",
        help="Relatório de fecho canónico v4.",
    )
    parser.add_argument(
        "--output-mapa",
        default=None,
        help="Output final do mapa; se omitido, usa o manifesto ou outputs/mapa_dedutivo_canonico_final.json.",
    )
    parser.add_argument(
        "--output-relatorio",
        default=None,
        help="Output final do relatório; se omitido, usa o manifesto ou outputs/relatorio_final_de_inevitabilidades.json.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Nível de logging.",
    )
    return parser.parse_args()


def candidate_paths(base_dir: Path, hint: str) -> List[Path]:
    raw = Path(hint)
    if raw.is_absolute():
        return [raw]
    candidates = [base_dir / raw, base_dir / raw.name]
    return unique_preserve_order([candidate.resolve() for candidate in candidates])


def resolve_existing_path(base_dir: Path, hint: str, label: str) -> Path:
    for candidate in candidate_paths(base_dir, hint):
        if candidate.exists():
            return candidate
    pretty = ", ".join(str(p) for p in candidate_paths(base_dir, hint))
    raise ConsolidationError(f"{label} não encontrado. Tentativas: {pretty}")


def resolve_output_path(base_dir: Path, explicit_hint: Optional[str], manifest: Dict[str, Any], output_key: str, fallback: str) -> Path:
    if explicit_hint:
        raw = Path(explicit_hint)
        return raw if raw.is_absolute() else (base_dir / raw).resolve()
    manifest_outputs = manifest.get("outputs_finais", {}) if isinstance(manifest, dict) else {}
    if isinstance(manifest_outputs, dict):
        entry = manifest_outputs.get(output_key)
        if isinstance(entry, dict) and isinstance(entry.get("path"), str) and entry["path"].strip():
            raw = Path(entry["path"])
            return raw if raw.is_absolute() else (base_dir / raw).resolve()
    return (base_dir / fallback).resolve()


def resolve_log_path(base_dir: Path, manifest: Dict[str, Any]) -> Path:
    exec_local = manifest.get("execucao_local", {}) if isinstance(manifest, dict) else {}
    dirs = exec_local.get("diretorios", {}) if isinstance(exec_local, dict) else {}
    log_dir = dirs.get("logs") if isinstance(dirs, dict) else None
    if isinstance(log_dir, str) and log_dir.strip():
        return ((base_dir / log_dir).resolve() / "consolidador_fecho_canonico.log")
    return (base_dir / "logs" / "consolidador_fecho_canonico.log").resolve()


def configure_logging(log_path: Path, level_name: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, level_name.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)



def require(condition: bool, message: str) -> None:
    if not condition:
        raise ConsolidationError(message)



def parse_corridor(corridor_id: str) -> Tuple[int, int]:
    require(bool(CORRIDOR_ID_RE.match(corridor_id)), f"Corredor inválido: {corridor_id}")
    parts = corridor_id.split("_")
    if len(parts) == 1:
        value = int(parts[0][1:])
        return value, value
    start = int(parts[0][1:])
    end = int(parts[1][1:])
    if start > end:
        start, end = end, start
    return start, end



def step_belongs_to_corridor(step_id: str, corridor_id: str) -> bool:
    value = numeric_step_id(step_id)
    start, end = parse_corridor(corridor_id)
    return start <= value <= end



def validate_map_and_matrix(mapa: Dict[str, Any], matriz: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    require(isinstance(mapa, dict), "O mapa pré-canónico tem de ser um objeto JSON.")
    require(isinstance(matriz, dict), "A matriz de inevitabilidades tem de ser um objeto JSON.")
    passos = mapa.get("passos")
    linhas = matriz.get("linhas")
    require(isinstance(passos, list), "O mapa pré-canónico não contém 'passos' válidos.")
    require(isinstance(linhas, list), "A matriz de inevitabilidades não contém 'linhas' válidas.")

    map_by_id: Dict[str, Dict[str, Any]] = {}
    matrix_by_id: Dict[str, Dict[str, Any]] = {}

    for step in passos:
        require(isinstance(step, dict), "Cada passo do mapa tem de ser um objeto JSON.")
        step_id = cleaned_string(step.get("id"))
        require(bool(STEP_ID_RE.match(step_id)), f"ID de passo inválido no mapa: {step_id}")
        require(step_id not in map_by_id, f"Passo duplicado no mapa: {step_id}")
        map_by_id[step_id] = step

    for line in linhas:
        require(isinstance(line, dict), "Cada linha da matriz tem de ser um objeto JSON.")
        step_id = cleaned_string(line.get("id"))
        require(bool(STEP_ID_RE.match(step_id)), f"ID de linha inválido na matriz: {step_id}")
        require(step_id not in matrix_by_id, f"Linha duplicada na matriz: {step_id}")
        matrix_by_id[step_id] = line

    require(set(map_by_id) == set(matrix_by_id), "Mapa e matriz não referenciam exatamente o mesmo conjunto de passos.")
    return map_by_id, matrix_by_id



def validate_aggregator(
    aggregator: Dict[str, Any],
    map_by_id: Dict[str, Dict[str, Any]],
    matrix_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    require(isinstance(aggregator, dict), "O agregador normativo tem de ser um objeto JSON.")
    for key in [
        "meta",
        "inputs_utilizados",
        "ordem_de_execucao",
        "decisoes_por_passo",
        "decisoes_por_subpasso",
        "arbitragens_de_corredor",
        "resumo",
    ]:
        require(key in aggregator, f"O agregador não contém a chave obrigatória: {key}")

    decisions = aggregator["decisoes_por_passo"]
    substeps = aggregator["decisoes_por_subpasso"]
    arbitrations = aggregator["arbitragens_de_corredor"]

    require(isinstance(decisions, list), "'decisoes_por_passo' tem de ser uma lista.")
    require(isinstance(substeps, list), "'decisoes_por_subpasso' tem de ser uma lista.")
    require(isinstance(arbitrations, list), "'arbitragens_de_corredor' tem de ser uma lista.")

    step_by_id: Dict[str, Dict[str, Any]] = {}
    substep_by_id: Dict[str, Dict[str, Any]] = {}
    arbitration_by_corridor: Dict[str, Dict[str, Any]] = {}

    for decision in decisions:
        require(isinstance(decision, dict), "Cada decisão por passo tem de ser um objeto JSON.")
        step_id = cleaned_string(decision.get("passo_id"))
        corridor = cleaned_string(decision.get("corredor"))
        require(bool(STEP_ID_RE.match(step_id)), f"Passo inválido no agregador: {step_id}")
        require(bool(CORRIDOR_ID_RE.match(corridor)), f"Corredor inválido no agregador: {corridor}")
        require(step_id not in step_by_id, f"Decisão de passo duplicada: {step_id}")
        require(step_id in map_by_id, f"O agregador referencia um passo ausente do mapa: {step_id}")
        require(step_id in matrix_by_id, f"O agregador referencia um passo ausente da matriz: {step_id}")
        require(step_belongs_to_corridor(step_id, corridor), f"{step_id} não pertence ao corredor {corridor}.")
        for ref in string_list(decision.get("depende_de")) + string_list(decision.get("prepara")):
            require(bool(STEP_ID_RE.match(ref)), f"Referência de passo inválida em {step_id}: {ref}")
            require(ref in map_by_id, f"{step_id} referencia passo inexistente: {ref}")
        for sub_ref in string_list(decision.get("subpassos_aprovados_ids")):
            require(bool(SUBSTEP_ID_RE.match(sub_ref)), f"Subpasso inválido em {step_id}: {sub_ref}")
            require(sub_ref.startswith(step_id + "_"), f"{step_id} referencia subpasso estranho: {sub_ref}")
        step_by_id[step_id] = decision

    for substep in substeps:
        require(isinstance(substep, dict), "Cada decisão por subpasso tem de ser um objeto JSON.")
        substep_id = cleaned_string(substep.get("subpasso_id"))
        parent_id = cleaned_string(substep.get("passo_pai_id"))
        corridor = cleaned_string(substep.get("corredor"))
        require(bool(SUBSTEP_ID_RE.match(substep_id)), f"Subpasso inválido no agregador: {substep_id}")
        require(bool(STEP_ID_RE.match(parent_id)), f"Passo pai inválido no agregador: {parent_id}")
        require(bool(CORRIDOR_ID_RE.match(corridor)), f"Corredor inválido no subpasso {substep_id}: {corridor}")
        require(substep_id not in substep_by_id, f"Subpasso duplicado no agregador: {substep_id}")
        require(parent_id in map_by_id, f"Subpasso {substep_id} aponta para passo ausente: {parent_id}")
        require(step_belongs_to_corridor(parent_id, corridor), f"{substep_id} não é compatível com o corredor {corridor}.")
        if parent_id in step_by_id:
            require(step_by_id[parent_id]["corredor"] == corridor, f"{substep_id} e o seu passo pai divergem de corredor.")
        decision_value = cleaned_string(substep.get("decisao_subpasso"))
        require(decision_value in {"aprovado", "rejeitado", "adiado"}, f"Decisão inválida em {substep_id}: {decision_value}")
        if decision_value == "aprovado":
            require(cleaned_string(substep.get("estatuto_final_no_mapa")) == "inserido_no_mapa", f"Subpasso aprovado sem estatuto inserido: {substep_id}")
        substep_by_id[substep_id] = substep

    for arbitration in arbitrations:
        require(isinstance(arbitration, dict), "Cada arbitragem de corredor tem de ser um objeto JSON.")
        corridor = cleaned_string(arbitration.get("corredor"))
        require(bool(CORRIDOR_ID_RE.match(corridor)), f"Corredor inválido em arbitragem: {corridor}")
        require(corridor not in arbitration_by_corridor, f"Arbitragem duplicada para o corredor {corridor}.")
        referenced_steps = string_list(arbitration.get("decisoes_por_passo_referenciadas"))
        for step_id in referenced_steps + string_list(arbitration.get("sequencia_minima_do_corredor")):
            require(step_id in step_by_id, f"Arbitragem {corridor} referencia passo sem decisão: {step_id}")
            require(step_belongs_to_corridor(step_id, corridor), f"Arbitragem {corridor} contém passo fora do corredor: {step_id}")
        referenced_substeps = string_list(arbitration.get("decisoes_por_subpasso_referenciadas"))
        for substep_id in referenced_substeps + string_list(arbitration.get("subpassos_aprovados")):
            require(substep_id in substep_by_id, f"Arbitragem {corridor} referencia subpasso inexistente: {substep_id}")
        require(cleaned_string(arbitration.get("estado_final_do_corredor")) == "fechado", f"O corredor {corridor} não ficou fechado no agregador.")
        require(bool(arbitration.get("sequencia_minima_ficou_fechada")), f"O corredor {corridor} não tem fecho terminal marcado como verdadeiro.")
        require(len(string_list(arbitration.get("passos_a_reabrir"))) == 0, f"O corredor {corridor} ainda tem passos a reabrir.")
        arbitration_by_corridor[corridor] = arbitration

    summary = aggregator.get("resumo", {})
    if isinstance(summary, dict):
        expected = {
            "total_decisoes_por_passo": len(step_by_id),
            "total_decisoes_por_subpasso": len(substep_by_id),
            "total_arbitragens_de_corredor": len(arbitration_by_corridor),
            "passos_fechados": sum(1 for d in step_by_id.values() if cleaned_string(d.get("estado_final_do_passo")) == "fechado"),
            "subpassos_aprovados": sum(1 for s in substep_by_id.values() if cleaned_string(s.get("decisao_subpasso")) == "aprovado"),
            "subpassos_rejeitados": sum(1 for s in substep_by_id.values() if cleaned_string(s.get("decisao_subpasso")) == "rejeitado"),
            "subpassos_adiados": sum(1 for s in substep_by_id.values() if cleaned_string(s.get("decisao_subpasso")) == "adiado"),
            "corredores_fechados": len(arbitration_by_corridor),
        }
        for key, value in expected.items():
            if key in summary:
                require(summary[key] == value, f"Resumo do agregador inconsistente em {key}: esperado {value}, obtido {summary[key]}")

    return step_by_id, substep_by_id, arbitration_by_corridor



def merge_observations(*groups: Sequence[str]) -> List[str]:
    merged: List[str] = []
    for group in groups:
        merged.extend(string_list(list(group) if isinstance(group, list) else group))
    return unique_preserve_order(merged)



def approved_substeps_by_parent(substep_by_id: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for substep in substep_by_id.values():
        if cleaned_string(substep.get("decisao_subpasso")) == "aprovado":
            grouped[cleaned_string(substep.get("passo_pai_id"))].append(substep)
    return grouped



def convert_substep_for_map(substep: Dict[str, Any], normative_source_rel: str) -> Dict[str, Any]:
    return {
        "id": cleaned_string(substep.get("subpasso_id")),
        "numero_ordinal_no_passo": substep.get("numero_ordinal_no_passo"),
        "decisao_subpasso": cleaned_string(substep.get("decisao_subpasso")),
        "justificacao_da_decisao": cleaned_string(substep.get("justificacao_da_decisao")),
        "formulacao_subpasso": substep.get("formulacao_subpasso"),
        "justificacao_minima_suficiente": substep.get("justificacao_minima_suficiente"),
        "funcao_dedutiva": substep.get("funcao_dedutiva"),
        "localizacao_na_cadeia": copy.deepcopy(substep.get("localizacao_na_cadeia")),
        "ponte_entrada": substep.get("ponte_entrada"),
        "ponte_saida": substep.get("ponte_saida"),
        "objecao_letal_a_bloquear": substep.get("objecao_letal_a_bloquear"),
        "bloqueio_curto_da_objecao": substep.get("bloqueio_curto_da_objecao"),
        "fragmentos_de_apoio_final": string_list(substep.get("fragmentos_de_apoio_final")),
        "objecoes_bloqueadas_final": string_list(substep.get("objecoes_bloqueadas_final")),
        "observacoes_editoriais": string_list(substep.get("observacoes_editoriais")),
        "fonte_normativa_final": normative_source_rel,
    }



def apply_step_decision_to_map_step(
    base_step: Dict[str, Any],
    decision: Dict[str, Any],
    approved_substeps: List[Dict[str, Any]],
    normative_source_rel: str,
) -> Dict[str, Any]:
    step = copy.deepcopy(base_step)
    closed = cleaned_string(decision.get("estado_final_do_passo")) == "fechado"

    step["numero_final"] = decision.get("numero_final")
    step["bloco_id"] = cleaned_string(decision.get("bloco_id")) or step.get("bloco_id")
    step["bloco_titulo"] = cleaned_string(decision.get("bloco_titulo")) or step.get("bloco_titulo")
    step["depende_de"] = string_list(decision.get("depende_de"))
    step["prepara"] = string_list(decision.get("prepara"))
    step["proposicao_final"] = cleaned_string(decision.get("formulacao_canonica_final")) or step.get("proposicao_final")
    step["justificacao_minima_suficiente"] = cleaned_string(decision.get("justificacao_minima_suficiente")) or step.get("justificacao_minima_suficiente")
    step["objecoes_bloqueadas"] = string_list(decision.get("objecoes_bloqueadas_final"))
    step["fragmentos_de_apoio_final"] = [fragment for fragment in string_list(decision.get("fragmentos_de_apoio_final")) if FRAGMENT_ID_RE.match(fragment)]
    step["estatuto_no_mapa"] = cleaned_string(decision.get("decisao_editorial")) or step.get("estatuto_no_mapa")
    step["estado_de_fecho_canonico"] = cleaned_string(decision.get("estado_final_do_passo")) or step.get("estado_de_fecho_canonico")
    step["tipos_de_fragilidade"] = [] if closed else string_list(decision.get("tipos_de_fragilidade_iniciais"))
    step["precisa_de_subpasso"] = bool(approved_substeps) or bool(decision.get("precisa_de_subpasso"))
    step["subpasso_sugerido"] = None
    step["texto_meta_editorial_detectado"] = False if closed else bool(step.get("texto_meta_editorial_detectado"))
    step["requer_arbitragem_humana"] = bool(decision.get("reabrir_em_arbitragem_de_corredor"))
    step["porque_o_anterior_nao_basta"] = cleaned_string(decision.get("porque_o_anterior_nao_basta")) or step.get("porque_o_anterior_nao_basta")
    step["porque_nao_pode_ser_suprimido"] = cleaned_string(decision.get("porque_nao_pode_ser_suprimido")) or step.get("porque_nao_pode_ser_suprimido")
    step["objecao_letal_a_bloquear"] = cleaned_string(decision.get("objecao_letal_a_bloquear")) or step.get("objecao_letal_a_bloquear")
    step["mediacao_necessaria"] = []
    step["observacoes_editoriais"] = string_list(decision.get("observacoes_editoriais"))
    step["fonte_decisao_prioritaria"] = "agregador_intermedio_consolidado"
    step["fonte_formulacao_escolhida"] = "agregador_intermedio_consolidado"

    step["ponte_entrada"] = cleaned_string(decision.get("ponte_entrada"))
    step["ponte_saida"] = cleaned_string(decision.get("ponte_saida"))
    step["bloqueio_curto_da_objecao"] = cleaned_string(decision.get("bloqueio_curto_da_objecao"))
    step["decisao_editorial_canonica"] = cleaned_string(decision.get("decisao_editorial"))
    step["estado_inicial_do_passo_canonico"] = cleaned_string(decision.get("estado_inicial_do_passo"))
    step["tipos_de_fragilidade_iniciais_canonicos"] = string_list(decision.get("tipos_de_fragilidade_iniciais"))
    step["subpassos_aprovados_ids"] = string_list(decision.get("subpassos_aprovados_ids"))
    step["justificacao_da_decisao_canonica"] = cleaned_string(decision.get("justificacao_da_decisao"))
    step["reabrir_em_arbitragem_de_corredor"] = bool(decision.get("reabrir_em_arbitragem_de_corredor"))
    step["fonte_normativa_final"] = normative_source_rel
    step["origem_no_fecho_terminal"] = "agregador_intermedio_consolidado"
    step["subpassos_inseridos"] = [convert_substep_for_map(substep, normative_source_rel) for substep in approved_substeps]
    return step



def prepare_preserved_map_step(base_step: Dict[str, Any], base_source_rel: str) -> Dict[str, Any]:
    step = copy.deepcopy(base_step)
    step.setdefault("subpassos_inseridos", [])
    step.setdefault("subpassos_aprovados_ids", [])
    step["fonte_normativa_final"] = base_source_rel
    step["origem_no_fecho_terminal"] = "mapa_precanonico_preservado"
    return step



def apply_final_numbering(passos: List[Dict[str, Any]]) -> List[str]:
    adjustments: List[str] = []
    numbers = [step.get("numero_final") for step in passos]
    duplicates = len(numbers) != len(set(numbers))
    if duplicates or any(step.get("numero_final") != numeric_step_id(step["id"]) for step in passos):
        for step in passos:
            target = numeric_step_id(step["id"])
            if step.get("numero_final") != target:
                adjustments.append(f"{step['id']}: {step.get('numero_final')} -> {target}")
                step["numero_final"] = target
    passos.sort(key=lambda item: (item["numero_final"], item["id"]))
    return adjustments



def build_final_map(
    manifesto_path: Path,
    manifesto: Dict[str, Any],
    agregador_path: Path,
    agregador: Dict[str, Any],
    mapa_path: Path,
    matriz_path: Path,
    relatorio_path: Path,
    mapa: Dict[str, Any],
    step_decisions: Dict[str, Dict[str, Any]],
    substep_decisions: Dict[str, Dict[str, Any]],
    arbitrations: Dict[str, Dict[str, Any]],
    base_dir: Path,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]], List[str]]:
    map_source_rel = path_to_string(mapa_path, base_dir)
    normative_rel = path_to_string(agregador_path, base_dir)
    approved_by_parent = approved_substeps_by_parent(substep_decisions)

    final_steps: List[Dict[str, Any]] = []
    for raw_step in mapa["passos"]:
        step_id = raw_step["id"]
        if step_id in step_decisions:
            final_steps.append(
                apply_step_decision_to_map_step(raw_step, step_decisions[step_id], approved_by_parent.get(step_id, []), normative_rel)
            )
        else:
            final_steps.append(prepare_preserved_map_step(raw_step, map_source_rel))

    numbering_adjustments = apply_final_numbering(final_steps)
    final_steps_by_id = {step["id"]: step for step in final_steps}

    approved_ids = [sub_id for sub_id, sub in substep_decisions.items() if cleaned_string(sub.get("decisao_subpasso")) == "aprovado"]
    rejected_ids = [sub_id for sub_id, sub in substep_decisions.items() if cleaned_string(sub.get("decisao_subpasso")) == "rejeitado"]
    adiado_ids = [sub_id for sub_id, sub in substep_decisions.items() if cleaned_string(sub.get("decisao_subpasso")) == "adiado"]

    final_map: Dict[str, Any] = {
        "meta": {
            "gerado_em_utc": utc_now_iso(),
            "script": "consolidador_fecho_canonico.py",
            "versao": PIPELINE_VERSION,
            "objetivo": "Mapa dedutivo canónico final gerado por consolidação terminal local e determinística.",
            "manifesto_utilizado": path_to_string(manifesto_path, base_dir),
            "fonte_normativa_prevalecente": normative_rel,
            "mapa_estrutural_base": map_source_rel,
            "matriz_utilizada": path_to_string(matriz_path, base_dir),
            "relatorio_base": path_to_string(relatorio_path, base_dir),
            "modo_execucao": "local_auditavel_sem_api",
        },
        "fontes": copy.deepcopy(mapa.get("fontes", {})),
        "resumo_de_consolidacao": {
            "total_passos_no_mapa": len(final_steps),
            "passos_substituidos_pelo_agregador": len(step_decisions),
            "passos_preservados_do_precanonico": len(final_steps) - len(step_decisions),
            "subpassos_aprovados_inseridos": approved_ids,
            "subpassos_rejeitados_nao_inseridos": rejected_ids,
            "subpassos_adiados": adiado_ids,
            "corredores_fechados_por_arbitragem": list(arbitrations.keys()),
            "ajustes_de_numeracao_final": numbering_adjustments,
        },
        "arbitragens_de_corredor": [copy.deepcopy(arbitrations[key]) for key in agregador.get("ordem_de_execucao", []) if key in arbitrations],
        "subpassos_decididos": {
            "aprovados_inseridos": [copy.deepcopy(substep_decisions[sub_id]) for sub_id in approved_ids],
            "rejeitados_nao_inseridos": [copy.deepcopy(substep_decisions[sub_id]) for sub_id in rejected_ids],
            "adiados": [copy.deepcopy(substep_decisions[sub_id]) for sub_id in adiado_ids],
        },
        "passos": final_steps,
    }
    return final_map, final_steps_by_id, numbering_adjustments



def final_line_from_matrix_and_map(
    base_line: Dict[str, Any],
    final_step: Dict[str, Any],
    arbitration_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    line = copy.deepcopy(base_line)
    line["numero_final"] = final_step.get("numero_final")
    line["bloco_id"] = final_step.get("bloco_id")
    line["bloco_titulo"] = final_step.get("bloco_titulo")
    line["depende_de"] = string_list(final_step.get("depende_de"))
    line["prepara"] = string_list(final_step.get("prepara"))
    line["proposicao_canonica_curta"] = cleaned_string(final_step.get("proposicao_final"))
    line["proposicao_canonica_tecnica"] = cleaned_string(final_step.get("proposicao_final"))
    if cleaned_string(final_step.get("tese_minima")):
        line["tese_minima_canonica"] = cleaned_string(final_step.get("tese_minima"))
    if cleaned_string(final_step.get("justificacao_minima_suficiente")):
        line["justificacao_minima_canonica"] = cleaned_string(final_step.get("justificacao_minima_suficiente"))
    line["estado_de_fecho"] = cleaned_string(final_step.get("estado_de_fecho_canonico")) or cleaned_string(line.get("estado_de_fecho"))
    line["tipos_de_fragilidade"] = string_list(final_step.get("tipos_de_fragilidade"))
    line["precisa_de_subpasso"] = bool(final_step.get("precisa_de_subpasso"))
    line["subpasso_sugerido"] = final_step.get("subpasso_sugerido")
    line["fragmentos_de_apoio_final"] = string_list(final_step.get("fragmentos_de_apoio_final"))
    line["objecoes_bloqueadas"] = string_list(final_step.get("objecoes_bloqueadas"))
    line["observacoes_editoriais"] = string_list(final_step.get("observacoes_editoriais"))
    line["porque_o_anterior_nao_basta"] = cleaned_string(final_step.get("porque_o_anterior_nao_basta")) or line.get("porque_o_anterior_nao_basta")
    line["porque_nao_pode_ser_suprimido"] = cleaned_string(final_step.get("porque_nao_pode_ser_suprimido")) or line.get("porque_nao_pode_ser_suprimido")
    line["objecao_letal_a_bloquear"] = cleaned_string(final_step.get("objecao_letal_a_bloquear")) or line.get("objecao_letal_a_bloquear")
    line["texto_meta_editorial_detectado"] = bool(final_step.get("texto_meta_editorial_detectado"))
    line["requer_arbitragem_humana"] = bool(final_step.get("requer_arbitragem_humana"))
    line["fonte_decisao_prioritaria"] = cleaned_string(final_step.get("fonte_decisao_prioritaria")) or line.get("fonte_decisao_prioritaria")
    line["ponte_entrada"] = final_step.get("ponte_entrada")
    line["ponte_saida"] = final_step.get("ponte_saida")
    line["bloqueio_curto_da_objecao"] = final_step.get("bloqueio_curto_da_objecao")
    line["subpassos_aprovados_ids"] = string_list(final_step.get("subpassos_aprovados_ids"))
    line["subpassos_inseridos"] = copy.deepcopy(final_step.get("subpassos_inseridos", []))
    line["fonte_normativa_final"] = cleaned_string(final_step.get("fonte_normativa_final"))
    line["origem_no_fecho_terminal"] = cleaned_string(final_step.get("origem_no_fecho_terminal"))

    arbitration = None
    for corridor, corridor_data in arbitration_lookup.items():
        if step_belongs_to_corridor(final_step["id"], corridor):
            arbitration = corridor_data
            break
    if arbitration is not None:
        line["corredor_canonico"] = cleaned_string(arbitration.get("corredor"))
        line["estado_final_do_corredor"] = cleaned_string(arbitration.get("estado_final_do_corredor"))
    return line



def count_fragilities(lines: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for line in lines:
        for fragility in string_list(line.get("tipos_de_fragilidade")):
            counter[fragility] += 1
    return dict(counter)



def sort_open_lines(lines: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates = [line for line in lines if cleaned_string(line.get("estado_de_fecho")) != "fechado"]
    candidates.sort(key=lambda item: (float(item.get("score_canonico_de_fecho", 9999)), item["id"]))
    return candidates



def build_final_report(
    manifesto_path: Path,
    agregador_path: Path,
    matriz_path: Path,
    relatorio_path: Path,
    matrix: Dict[str, Any],
    relatorio_base: Dict[str, Any],
    final_map: Dict[str, Any],
    final_steps_by_id: Dict[str, Dict[str, Any]],
    step_decisions: Dict[str, Dict[str, Any]],
    substep_decisions: Dict[str, Dict[str, Any]],
    arbitrations: Dict[str, Dict[str, Any]],
    numbering_adjustments: List[str],
    base_dir: Path,
) -> Dict[str, Any]:
    lines = [final_line_from_matrix_and_map(copy.deepcopy(line), final_steps_by_id[line["id"]], arbitrations) for line in matrix["linhas"]]
    lines.sort(key=lambda item: (item["numero_final"], item["id"]))

    state_counts = Counter(cleaned_string(line.get("estado_de_fecho")) or "desconhecido" for line in lines)
    fragility_counts = count_fragilities(lines)
    passos_com_subpasso = [
        line["id"]
        for line in lines
        if bool(line.get("precisa_de_subpasso")) or bool(line.get("subpassos_inseridos"))
    ]
    passos_com_meta = [line["id"] for line in lines if bool(line.get("texto_meta_editorial_detectado"))]
    passos_arbitragem = [line["id"] for line in lines if bool(line.get("requer_arbitragem_humana"))]

    open_lines = sort_open_lines(lines)
    top_abertos = [
        {
            "id": line["id"],
            "score_canonico_de_fecho": line.get("score_canonico_de_fecho"),
            "tipos_de_fragilidade": string_list(line.get("tipos_de_fragilidade")),
            "subpasso_sugerido": line.get("subpasso_sugerido"),
        }
        for line in open_lines[:15]
    ]
    top_mediacao = [
        {
            "id": line["id"],
            "score_canonico_de_fecho": line.get("score_canonico_de_fecho"),
            "subpasso_sugerido": line.get("subpasso_sugerido"),
        }
        for line in open_lines
        if "mediacao" in string_list(line.get("tipos_de_fragilidade"))
    ][:15]

    corredores_criticos: Dict[str, Dict[str, Any]] = {}
    for corridor, arbitration in arbitrations.items():
        step_ids = string_list(arbitration.get("sequencia_minima_do_corredor"))
        states = Counter(cleaned_string(final_steps_by_id[step_id].get("estado_de_fecho_canonico")) for step_id in step_ids)
        corredores_criticos[corridor] = {
            "total": len(step_ids),
            "fechados": states.get("fechado", 0),
            "abertos": states.get("aberto", 0),
            "quase_fechados": states.get("quase_fechado", 0),
            "subpassos": string_list(arbitration.get("decisoes_por_subpasso_referenciadas")),
            "estado_final_do_corredor": cleaned_string(arbitration.get("estado_final_do_corredor")),
            "sequencia_minima_ficou_fechada": bool(arbitration.get("sequencia_minima_ficou_fechada")),
        }

    approved = [copy.deepcopy(sub) for sub in substep_decisions.values() if cleaned_string(sub.get("decisao_subpasso")) == "aprovado"]
    rejected = [copy.deepcopy(sub) for sub in substep_decisions.values() if cleaned_string(sub.get("decisao_subpasso")) == "rejeitado"]
    adiado = [copy.deepcopy(sub) for sub in substep_decisions.values() if cleaned_string(sub.get("decisao_subpasso")) == "adiado"]

    report: Dict[str, Any] = {
        "meta": {
            "gerado_em_utc": utc_now_iso(),
            "script": "consolidador_fecho_canonico.py",
            "versao": PIPELINE_VERSION,
            "objetivo": "Relatório final de inevitabilidades após projeção canónica terminal sobre o mapa dedutivo.",
            "manifesto_utilizado": path_to_string(manifesto_path, base_dir),
            "agregador_normativo": path_to_string(agregador_path, base_dir),
            "matriz_base": path_to_string(matriz_path, base_dir),
            "relatorio_base": path_to_string(relatorio_path, base_dir),
            "mapa_final_gerado": "outputs/mapa_dedutivo_canonico_final.json",
            "modo_execucao": "local_auditavel_sem_api",
        },
        "resumo_global": {
            "total_passos": len(lines),
            "estado_de_fecho": {
                "aberto": state_counts.get("aberto", 0),
                "quase_fechado": state_counts.get("quase_fechado", 0),
                "fechado": state_counts.get("fechado", 0),
            },
            "tipos_de_fragilidade": fragility_counts,
            "passos_com_subpasso": passos_com_subpasso,
            "passos_com_texto_meta_editorial": passos_com_meta,
            "passos_que_requerem_arbitragem_humana": passos_arbitragem,
        },
        "corredores_criticos": corredores_criticos,
        "top_passos_mais_abertos": top_abertos,
        "top_passos_com_fragilidade_mediacional": top_mediacao,
        "argumentos_referidos_mas_ausentes": copy.deepcopy(relatorio_base.get("argumentos_referidos_mas_ausentes", [])),
        "continuidade_com_v3": copy.deepcopy(relatorio_base.get("continuidade_com_v3", {})),
        "subpassos_decididos": {
            "aprovados_inseridos": approved,
            "rejeitados_nao_inseridos": rejected,
            "adiados": adiado,
        },
        "passos_canonizados_nesta_fase": [
            {
                "id": step_id,
                "corredor": cleaned_string(decision.get("corredor")),
                "numero_final": final_steps_by_id[step_id].get("numero_final"),
                "formulacao_canonica_final": cleaned_string(decision.get("formulacao_canonica_final")),
                "estado_final_do_passo": cleaned_string(decision.get("estado_final_do_passo")),
                "subpassos_aprovados_ids": string_list(decision.get("subpassos_aprovados_ids")),
            }
            for step_id, decision in sorted(step_decisions.items(), key=lambda item: final_steps_by_id[item[0]]["numero_final"])
        ],
        "arbitragens_de_corredor": [copy.deepcopy(arbitrations[key]) for key in final_map.get("resumo_de_consolidacao", {}).get("corredores_fechados_por_arbitragem", []) if key in arbitrations],
        "validacao_interna": {
            "ids_unicos_ok": True,
            "numeracao_final_contigua_ok": True,
            "referencias_minimas_ok": True,
            "subpassos_aprovados_inseridos_ok": len(approved) == 1 and approved[0]["subpasso_id"] == "P36_SP01",
            "corredores_criticos_fechados_ok": all(corridors["estado_final_do_corredor"] == "fechado" for corridors in corredores_criticos.values()),
            "ajustes_de_numeracao_final": numbering_adjustments,
        },
        "linhas": lines,
    }
    return report



def validate_final_map(final_map: Dict[str, Any]) -> Dict[str, Any]:
    passos = final_map.get("passos", [])
    require(isinstance(passos, list) and passos, "O mapa final ficou vazio.")
    ids = [cleaned_string(step.get("id")) for step in passos]
    numbers = [step.get("numero_final") for step in passos]
    require(len(ids) == len(set(ids)), "O mapa final contém IDs de passos duplicados.")
    require(all(STEP_ID_RE.match(step_id) for step_id in ids), "O mapa final contém IDs de passos inválidos.")
    require(len(numbers) == len(set(numbers)), "O mapa final contém numeração final duplicada.")
    expected_numbers = list(range(1, len(passos) + 1))
    require(sorted(numbers) == expected_numbers, f"A numeração final não ficou contígua: {sorted(numbers)}")
    step_ids = set(ids)
    approved_substeps: List[str] = []
    for step in passos:
        for ref in string_list(step.get("depende_de")) + string_list(step.get("prepara")):
            require(ref in step_ids, f"Referência de passo inexistente no mapa final: {ref}")
        for sub in step.get("subpassos_inseridos", []):
            require(isinstance(sub, dict), f"Subpasso inserido inválido em {step.get('id')}")
            sub_id = cleaned_string(sub.get("id"))
            require(bool(SUBSTEP_ID_RE.match(sub_id)), f"Subpasso inserido inválido: {sub_id}")
            require(sub_id.startswith(step["id"] + "_"), f"Subpasso {sub_id} não pertence ao passo {step['id']}")
            approved_substeps.append(sub_id)
    require(approved_substeps == ["P36_SP01"], f"O mapa final não inseriu exatamente o subpasso aprovado esperado: {approved_substeps}")
    return {
        "total_passos": len(passos),
        "ids_unicos": True,
        "numeracao_contigua": True,
        "subpassos_aprovados_inseridos": approved_substeps,
    }



def validate_final_report(final_report: Dict[str, Any]) -> Dict[str, Any]:
    lines = final_report.get("linhas", [])
    require(isinstance(lines, list) and lines, "O relatório final ficou sem linhas.")
    ids = [cleaned_string(line.get("id")) for line in lines]
    require(len(ids) == len(set(ids)), "O relatório final contém linhas duplicadas.")
    for line in lines:
        require(bool(STEP_ID_RE.match(cleaned_string(line.get("id")))), f"Linha inválida no relatório final: {line.get('id')}")
        for ref in string_list(line.get("depende_de")) + string_list(line.get("prepara")):
            require(ref in ids, f"Linha {line.get('id')} referencia passo inexistente: {ref}")
    resumo = final_report.get("resumo_global", {})
    require(isinstance(resumo, dict), "O relatório final não contém resumo_global válido.")
    total = resumo.get("total_passos")
    require(total == len(lines), f"Resumo global inconsistente: total_passos={total}, linhas={len(lines)}")
    return {
        "total_linhas": len(lines),
        "ids_unicos": True,
        "referencias_validas": True,
    }



def main() -> int:
    args = parse_args()
    base_dir = Path(args.base_dir).resolve()

    manifesto_path = resolve_existing_path(base_dir, args.manifesto, "manifesto")
    manifesto = json_load(manifesto_path)
    log_path = resolve_log_path(base_dir, manifesto)
    configure_logging(log_path, args.log_level)

    logging.info("Início da consolidação terminal do fecho canónico.")
    logging.info("Base-dir: %s", base_dir)
    logging.info("Manifesto: %s", manifesto_path)

    agregador_path = resolve_existing_path(base_dir, args.agregador, "agregador normativo")
    mapa_path = resolve_existing_path(base_dir, args.mapa, "mapa pré-canónico")
    matriz_path = resolve_existing_path(base_dir, args.matriz, "matriz de inevitabilidades")
    relatorio_path = resolve_existing_path(base_dir, args.relatorio, "relatório base")

    output_mapa_path = resolve_output_path(
        base_dir,
        args.output_mapa,
        manifesto,
        "mapa_dedutivo_canonico_final",
        "outputs/mapa_dedutivo_canonico_final.json",
    )
    output_relatorio_path = resolve_output_path(
        base_dir,
        args.output_relatorio,
        manifesto,
        "relatorio_final_de_inevitabilidades",
        "outputs/relatorio_final_de_inevitabilidades.json",
    )

    logging.info("Agregador normativo: %s", agregador_path)
    logging.info("Mapa base: %s", mapa_path)
    logging.info("Matriz base: %s", matriz_path)
    logging.info("Relatório base: %s", relatorio_path)
    logging.info("Output mapa final: %s", output_mapa_path)
    logging.info("Output relatório final: %s", output_relatorio_path)

    agregador = json_load(agregador_path)
    mapa = json_load(mapa_path)
    matriz = json_load(matriz_path)
    relatorio = json_load(relatorio_path)

    map_by_id, matrix_by_id = validate_map_and_matrix(mapa, matriz)
    step_decisions, substep_decisions, arbitrations = validate_aggregator(agregador, map_by_id, matrix_by_id)
    logging.info("Validação de inputs concluída: %s passos no mapa, %s decisões normativas, %s subpassos, %s arbitragens.", len(map_by_id), len(step_decisions), len(substep_decisions), len(arbitrations))

    final_map, final_steps_by_id, numbering_adjustments = build_final_map(
        manifesto_path,
        manifesto,
        agregador_path,
        agregador,
        mapa_path,
        matriz_path,
        relatorio_path,
        mapa,
        step_decisions,
        substep_decisions,
        arbitrations,
        base_dir,
    )

    if numbering_adjustments:
        for item in numbering_adjustments:
            logging.info("Ajuste de numeração final aplicado: %s", item)
    else:
        logging.info("Sem necessidade de ajustes adicionais de numeração final.")

    final_report = build_final_report(
        manifesto_path,
        agregador_path,
        matriz_path,
        relatorio_path,
        matriz,
        relatorio,
        final_map,
        final_steps_by_id,
        step_decisions,
        substep_decisions,
        arbitrations,
        numbering_adjustments,
        base_dir,
    )

    map_validation = validate_final_map(final_map)
    report_validation = validate_final_report(final_report)
    final_map["validacao_interna"] = map_validation

    json_dump(output_mapa_path, final_map)
    json_dump(output_relatorio_path, final_report)

    logging.info("Mapa final escrito com sucesso: %s", output_mapa_path)
    logging.info("Relatório final escrito com sucesso: %s", output_relatorio_path)
    logging.info("Resumo final do mapa: %s", json.dumps(map_validation, ensure_ascii=False))
    logging.info("Resumo final do relatório: %s", json.dumps(report_validation, ensure_ascii=False))
    logging.info("Consolidação terminal concluída sem chamadas a API.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConsolidationError as exc:
        logging.error("ERRO DE CONSOLIDAÇÃO: %s", exc)
        print(f"ERRO DE CONSOLIDAÇÃO: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except FileNotFoundError as exc:
        logging.error("Ficheiro não encontrado: %s", exc)
        print(f"Ficheiro não encontrado: {exc}", file=sys.stderr)
        raise SystemExit(1)
