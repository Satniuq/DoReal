#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
conferencia_final_fecho.py

Conferência material final dos outputs terminais do fecho canónico.

Características:
- execução local, determinística e sem API;
- resolução de caminhos a partir de Path(__file__).resolve().parent;
- veredito objetivo: ACEITE / NÃO ACEITE;
- geração automática de relatório textual no mesmo diretório do script.
"""

import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import re
import sys
import os


# Expressões regulares mínimas para ids estruturais.
RE_PASSO = re.compile(r"^P\d{2}$")
RE_SUBPASSO = re.compile(r"^P\d{2}_SP\d{2}$")
RE_CORREDOR = re.compile(r"^P\d{2}(?:_P\d{2})?$")

# Ficheiros esperados pela estrutura operacional do projeto.
EXPECTED_MAIN_FILES = (
    "mapa_dedutivo_canonico_final.json",
    "relatorio_final_de_inevitabilidades.json",
    "decisoes_canonicas_intermedias_consolidado_final_intermedio.json",
)

EXPECTED_PARENT_FILES = (
    "manifesto_fecho_canonico.json",
    "07_README_estado_atual_e_transicao_para_fecho_do_mapa.md",
    "orquestrador_fecho_canonico_api.py",
)

EXPECTED_STRUCTURAL_FILES = (
    "mapa_dedutivo_precanonico_v4.json",
    "matriz_inevitabilidades_v4.json",
    "relatorio_fecho_canonico_v4.json",
)

EXPECTED_CORRIDORS = ("P33_P37", "P25_P30", "P42_P48", "P50")
REPORT_NAME_DEFAULT = "relatorio_conferencia_final.txt"


# ---------------------------------------------------------------------------
# Utilitários básicos
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Conferência final local dos outputs terminais do fecho canónico."
    )
    parser.add_argument(
        "--report-file",
        default=None,
        help="Caminho opcional do relatório textual. Por omissão, usa relatorio_conferencia_final.txt no diretório do script.",
    )
    return parser.parse_args()


def normalize_text(value):
    if value is None:
        return None
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_value(value):
    if isinstance(value, str):
        return normalize_text(value)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key in sorted(value.keys()):
            result[key] = normalize_value(value[key])
        return result
    return value


def scalar_list(value):
    return isinstance(value, list) and all(not isinstance(item, (list, dict)) for item in value)


def values_equal(a, b):
    a = normalize_value(a)
    b = normalize_value(b)
    if scalar_list(a) and scalar_list(b):
        return sorted(a) == sorted(b)
    return a == b


def is_step_id(value):
    return isinstance(value, str) and bool(RE_PASSO.match(value.strip()))


def is_substep_id(value):
    return isinstance(value, str) and bool(RE_SUBPASSO.match(value.strip()))


def is_corridor_id(value):
    return isinstance(value, str) and bool(RE_CORREDOR.match(value.strip()))


def get_step_id(record):
    if not isinstance(record, dict):
        return None
    for key in ("id", "passo_id"):
        value = record.get(key)
        if is_step_id(value):
            return value.strip()
    return None


def get_substep_id(record):
    if not isinstance(record, dict):
        return None
    for key in ("subpasso_id", "id"):
        value = record.get(key)
        if is_substep_id(value):
            return value.strip()
    return None


def get_corridor_id(record):
    if not isinstance(record, dict):
        return None
    value = record.get("corredor")
    if is_corridor_id(value):
        return value.strip()
    return None


def get_step_number(record):
    if not isinstance(record, dict):
        return None
    value = record.get("numero_final")
    if isinstance(value, int):
        return value
    return None


def to_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def unique_preserve_order(values):
    seen = set()
    result = []
    for value in values:
        marker = json.dumps(normalize_value(value), ensure_ascii=False, sort_keys=True)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def truncate_for_log(value, max_len=180):
    text = json.dumps(normalize_value(value), ensure_ascii=False, sort_keys=True)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_text(path):
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def short_hash(value):
    return value[:12]


def fail_with_clear_message(message):
    print("ERRO: {0}".format(message))
    sys.exit(2)


# ---------------------------------------------------------------------------
# Descoberta defensiva de coleções em JSON
# ---------------------------------------------------------------------------

def recursive_list_candidates(node, path="root"):
    candidates = []
    if isinstance(node, list):
        candidates.append((path, node))
        for idx, item in enumerate(node):
            candidates.extend(recursive_list_candidates(item, "{0}[{1}]".format(path, idx)))
    elif isinstance(node, dict):
        for key, value in node.items():
            candidates.extend(recursive_list_candidates(value, "{0}.{1}".format(path, key)))
    return candidates


def score_step_list(candidate):
    if not isinstance(candidate, list) or not candidate:
        return -1
    valid = 0
    score = 0
    for item in candidate:
        if not isinstance(item, dict):
            continue
        if get_step_id(item):
            valid += 1
            score += 10
        if "numero_final" in item:
            score += 2
        if any(key in item for key in ("proposicao_final", "proposicao_canonica_curta", "depende_de", "prepara")):
            score += 1
    if valid >= 3 and valid >= max(1, len(candidate) // 2):
        return score
    return -1


def score_substep_list(candidate):
    if not isinstance(candidate, list) or not candidate:
        return -1
    valid = 0
    score = 0
    for item in candidate:
        if not isinstance(item, dict):
            continue
        if get_substep_id(item):
            valid += 1
            score += 10
        if "decisao_subpasso" in item:
            score += 2
    if valid >= 1 and valid >= max(1, len(candidate) // 2):
        return score
    return -1


def score_arbitration_list(candidate):
    if not isinstance(candidate, list) or not candidate:
        return -1
    valid = 0
    score = 0
    for item in candidate:
        if not isinstance(item, dict):
            continue
        if get_corridor_id(item) and normalize_text(item.get("tipo_registo")) == "arbitragem_corredor":
            valid += 1
            score += 10
        if "sequencia_minima_do_corredor" in item:
            score += 2
    if valid >= 1 and valid >= max(1, len(candidate) // 2):
        return score
    return -1


def find_best_list(document, scorer, preferred_keys=None):
    preferred_keys = preferred_keys or ()
    if isinstance(document, dict):
        for key in preferred_keys:
            value = document.get(key)
            if scorer(value) >= 0:
                return value, "root.{0}".format(key)

    best_score = -1
    best_value = None
    best_path = None
    for path, candidate in recursive_list_candidates(document):
        score = scorer(candidate)
        if score > best_score:
            best_score = score
            best_value = candidate
            best_path = path
    return best_value, best_path


def index_records(records, id_getter):
    index = {}
    duplicates = []
    for record in records:
        record_id = id_getter(record)
        if not record_id:
            continue
        if record_id in index:
            duplicates.append(record_id)
        else:
            index[record_id] = record
    return index, duplicates


# ---------------------------------------------------------------------------
# Extração de ids e estruturas ativas
# ---------------------------------------------------------------------------

def extract_scalar_id_list(value, validator):
    result = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and validator(item.strip()):
                result.append(item.strip())
    return unique_preserve_order(result)


def extract_substep_ids_from_container(value):
    result = []

    if isinstance(value, str) and is_substep_id(value.strip()):
        result.append(value.strip())
        return result

    if isinstance(value, dict):
        direct_id = get_substep_id(value)
        if direct_id:
            result.append(direct_id)
        for key in (
            "subpassos_inseridos",
            "subpassos_aprovados_ids",
            "aprovados_inseridos",
            "rejeitados_nao_inseridos",
            "subpassos_aprovados",
            "subpassos",
        ):
            if key in value:
                result.extend(extract_substep_ids_from_container(value[key]))
        return unique_preserve_order(result)

    if isinstance(value, list):
        for item in value:
            result.extend(extract_substep_ids_from_container(item))
        return unique_preserve_order(result)

    return unique_preserve_order(result)


def collect_active_substeps_from_map(step_records, map_document):
    """
    Recolhe apenas subpassos operativamente ativos no mapa:
    - registos efetivamente inseridos em subpassos_inseridos;
    - ids aprovados ativos por passo;
    - resumos/validações que confirmem inserção ativa.
    Menções históricas a subpassos rejeitados em arbitragens ou resumos não contam.
    """
    active_ids = []
    active_records = {}
    duplicate_active_ids = []

    for step in step_records:
        inserted = step.get("subpassos_inseridos")
        if isinstance(inserted, list):
            for item in inserted:
                substep_id = None
                if isinstance(item, dict):
                    substep_id = get_substep_id(item)
                elif isinstance(item, str) and is_substep_id(item):
                    substep_id = item
                if substep_id:
                    active_ids.append(substep_id)
                    if substep_id in active_records:
                        duplicate_active_ids.append(substep_id)
                    else:
                        active_records[substep_id] = item

        active_ids.extend(extract_scalar_id_list(step.get("subpassos_aprovados_ids"), is_substep_id))

    summary_candidates = []
    if isinstance(map_document, dict):
        summary_candidates.extend(
            [
                map_document.get("subpassos_decididos"),
                map_document.get("resumo_de_consolidacao"),
                map_document.get("validacao_interna"),
            ]
        )

    for candidate in summary_candidates:
        if isinstance(candidate, dict):
            for key in ("aprovados_inseridos", "subpassos_aprovados_inseridos"):
                if key in candidate:
                    active_ids.extend(extract_substep_ids_from_container(candidate[key]))

    return unique_preserve_order(active_ids), active_records, unique_preserve_order(duplicate_active_ids)


# ---------------------------------------------------------------------------
# Registo de checks
# ---------------------------------------------------------------------------

def record_check(results, name, passed, details=None, critical=True):
    results.append(
        {
            "name": name,
            "passed": bool(passed),
            "details": details or [],
            "critical": bool(critical),
        }
    )


def summarize_mismatch(record_id, field_name, expected_value, actual_value):
    return (
        "{0}: campo '{1}' divergente; esperado={2}; obtido={3}".format(
            record_id,
            field_name,
            truncate_for_log(expected_value),
            truncate_for_log(actual_value),
        )
    )


# ---------------------------------------------------------------------------
# Resolução de caminhos e carga inicial
# ---------------------------------------------------------------------------

def resolve_paths(script_dir):
    """
    Resolve caminhos de forma estritamente coerente com a árvore pedida.
    """
    if script_dir.name.lower() != "outputs":
        fail_with_clear_message(
            "O script deve estar na pasta 'outputs'. Diretório atual detetado: {0}".format(script_dir)
        )

    fecho_dir = script_dir.parent
    if fecho_dir.name != "02_fecho_canonico_mapa":
        fail_with_clear_message(
            "Estrutura inesperada: o diretório pai de 'outputs' deve ser '02_fecho_canonico_mapa'. Foi encontrado: {0}".format(
                fecho_dir.name
            )
        )

    mapa_dir = fecho_dir.parent
    if mapa_dir.name != "14_mapa_dedutivo":
        fail_with_clear_message(
            "Estrutura inesperada: acima de '02_fecho_canonico_mapa' deve existir '14_mapa_dedutivo'. Foi encontrado: {0}".format(
                mapa_dir.name
            )
        )

    structural_dir = mapa_dir / "01_reconstrucao_mapa_v2"

    return {
        "script_dir": script_dir,
        "fecho_dir": fecho_dir,
        "mapa_dir": mapa_dir,
        "structural_dir": structural_dir,
        "main": {name: script_dir / name for name in EXPECTED_MAIN_FILES},
        "parent": {name: fecho_dir / name for name in EXPECTED_PARENT_FILES},
        "structural": {name: structural_dir / name for name in EXPECTED_STRUCTURAL_FILES},
    }


def load_inputs(paths):
    loaded = {
        "json": {},
        "text": {},
        "file_info": {},
        "errors": [],
    }

    groups = (
        ("main", "json"),
        ("parent", "mixed"),
        ("structural", "json"),
    )

    for group_name, mode in groups:
        for file_name, path in paths[group_name].items():
            if not path.exists():
                loaded["errors"].append("Ficheiro obrigatório em falta: {0}".format(path))
                continue

            try:
                stat = path.stat()
                digest = file_sha256(path)
                loaded["file_info"][file_name] = {
                    "path": path,
                    "size": stat.st_size,
                    "sha256": digest,
                }

                if mode == "json" or path.suffix.lower() == ".json":
                    loaded["json"][file_name] = load_json(path)
                else:
                    loaded["text"][file_name] = load_text(path)
            except Exception as exc:
                loaded["errors"].append("Falha ao ler {0}: {1}".format(path, exc))

    return loaded


def collect_core_collections(loaded_json):
    """
    Localiza, de forma defensiva, as coleções essenciais dos três JSON centrais.
    """
    errors = []
    core = {
        "mapa_final": None,
        "relatorio_final": None,
        "agregador": None,
        "mapa_steps": [],
        "mapa_steps_path": None,
        "rel_lines": [],
        "rel_lines_path": None,
        "agg_steps": [],
        "agg_steps_path": None,
        "agg_substeps": [],
        "agg_substeps_path": None,
        "agg_arbitrations": [],
        "agg_arbitrations_path": None,
    }

    for required in EXPECTED_MAIN_FILES:
        if required not in loaded_json:
            errors.append("JSON principal não carregado: {0}".format(required))

    if errors:
        return core, errors

    mapa_final = loaded_json["mapa_dedutivo_canonico_final.json"]
    relatorio_final = loaded_json["relatorio_final_de_inevitabilidades.json"]
    agregador = loaded_json["decisoes_canonicas_intermedias_consolidado_final_intermedio.json"]

    mapa_steps, mapa_steps_path = find_best_list(mapa_final, score_step_list, preferred_keys=("passos", "linhas"))
    rel_lines, rel_lines_path = find_best_list(relatorio_final, score_step_list, preferred_keys=("linhas", "passos"))
    agg_steps, agg_steps_path = find_best_list(agregador, score_step_list, preferred_keys=("decisoes_por_passo",))
    agg_substeps, agg_substeps_path = find_best_list(agregador, score_substep_list, preferred_keys=("decisoes_por_subpasso",))
    agg_arbitrations, agg_arbitrations_path = find_best_list(agregador, score_arbitration_list, preferred_keys=("arbitragens_de_corredor",))

    if mapa_steps is None:
        errors.append("Não foi possível localizar a coleção de passos no mapa final.")
    if rel_lines is None:
        errors.append("Não foi possível localizar a coleção de linhas/passos no relatório final.")
    if agg_steps is None:
        errors.append("Não foi possível localizar a coleção de decisões por passo no agregador consolidado.")
    if agg_substeps is None:
        errors.append("Não foi possível localizar a coleção de decisões por subpasso no agregador consolidado.")
    if agg_arbitrations is None:
        errors.append("Não foi possível localizar a coleção de arbitragens de corredor no agregador consolidado.")

    core.update(
        {
            "mapa_final": mapa_final,
            "relatorio_final": relatorio_final,
            "agregador": agregador,
            "mapa_steps": mapa_steps or [],
            "mapa_steps_path": mapa_steps_path,
            "rel_lines": rel_lines or [],
            "rel_lines_path": rel_lines_path,
            "agg_steps": agg_steps or [],
            "agg_steps_path": agg_steps_path,
            "agg_substeps": agg_substeps or [],
            "agg_substeps_path": agg_substeps_path,
            "agg_arbitrations": agg_arbitrations or [],
            "agg_arbitrations_path": agg_arbitrations_path,
        }
    )
    return core, errors


# ---------------------------------------------------------------------------
# Comparações e verificações materiais
# ---------------------------------------------------------------------------

def compare_field_mapping(index_a, index_b, field_pairs):
    mismatches = []
    for record_id in sorted(index_a.keys()):
        if record_id not in index_b:
            mismatches.append("{0}: registo ausente no segundo conjunto".format(record_id))
            continue
        record_a = index_a[record_id]
        record_b = index_b[record_id]
        for field_a, field_b in field_pairs:
            has_a = field_a in record_a
            has_b = field_b in record_b
            if not has_a and not has_b:
                continue
            value_a = record_a.get(field_a)
            value_b = record_b.get(field_b)
            if not values_equal(value_a, value_b):
                mismatches.append(summarize_mismatch(record_id, "{0} -> {1}".format(field_a, field_b), value_a, value_b))
    return mismatches


def step_reference_issues(step_index):
    issues = []
    valid_ids = set(step_index.keys())
    for step_id in sorted(step_index.keys()):
        record = step_index[step_id]
        for field in ("depende_de", "prepara"):
            refs = extract_scalar_id_list(record.get(field), is_step_id)
            invalid = [ref for ref in refs if ref not in valid_ids]
            if invalid:
                issues.append(
                    "{0}: referências inválidas em {1}: {2}".format(
                        step_id,
                        field,
                        ", ".join(invalid),
                    )
                )
    return issues


def proposition_duplicates(step_index):
    duplicates = []
    seen = defaultdict(list)
    for step_id, record in step_index.items():
        proposition = normalize_text(record.get("proposicao_final"))
        if proposition:
            seen[proposition].append(step_id)
    for proposition, ids in seen.items():
        if len(ids) > 1:
            duplicates.append("Proposição final duplicada em {0}".format(", ".join(sorted(ids))))
    return duplicates


def substep_formulation_duplicates(active_substep_records):
    duplicates = []
    seen = defaultdict(list)
    for substep_id, record in active_substep_records.items():
        if isinstance(record, dict):
            formulation = normalize_text(record.get("formulacao_subpasso"))
            if formulation:
                seen[formulation].append(substep_id)
    for formulation, ids in seen.items():
        if len(ids) > 1:
            duplicates.append("Formulação de subpasso duplicada em {0}".format(", ".join(sorted(ids))))
    return duplicates


def run_checks(paths, loaded, core):
    results = []

    record_check(
        results,
        "Estrutura de caminhos e ficheiros obrigatórios",
        not loaded["errors"],
        loaded["errors"] or [
            "Estrutura esperada confirmada a partir de {0}".format(paths["script_dir"]),
            "Ficheiros principais, auxiliares e estruturais localizados e legíveis.",
        ],
    )

    manifesto = loaded["json"].get("manifesto_fecho_canonico.json", {})
    manifesto_output_ok = False
    manifesto_details = []
    if isinstance(manifesto, dict):
        outputs_finais = manifesto.get("outputs_finais", {})
        mapa_entry = outputs_finais.get("mapa_dedutivo_canonico_final", {})
        rel_entry = outputs_finais.get("relatorio_final_de_inevitabilidades", {})
        mapa_path = normalize_text(mapa_entry.get("path"))
        rel_path = normalize_text(rel_entry.get("path"))
        manifesto_output_ok = mapa_path == "outputs/mapa_dedutivo_canonico_final.json" and rel_path == "outputs/relatorio_final_de_inevitabilidades.json"
        manifesto_details.append("Manifesto: outputs finais declarados = {0} | {1}".format(mapa_path, rel_path))
        manifesto_details.append("Manifesto: usar_caminhos_relativos = {0}".format(manifesto.get("usar_caminhos_relativos")))
    record_check(
        results,
        "Manifesto coerente com os outputs finais esperados",
        manifesto_output_ok,
        manifesto_details or ["Manifesto não pôde ser avaliado."],
    )

    mapa_index, mapa_duplicate_ids = index_records(core["mapa_steps"], get_step_id)
    rel_index, rel_duplicate_ids = index_records(core["rel_lines"], get_step_id)
    agg_step_index, agg_step_duplicate_ids = index_records(core["agg_steps"], get_step_id)
    agg_substep_index, agg_substep_duplicate_ids = index_records(core["agg_substeps"], get_substep_id)
    agg_arbitration_index, agg_arbitration_duplicate_ids = index_records(core["agg_arbitrations"], get_corridor_id)

    active_substep_ids, active_substep_records, duplicate_active_substep_ids = collect_active_substeps_from_map(
        core["mapa_steps"], core["mapa_final"]
    )

    map_numbers = [get_step_number(record) for record in mapa_index.values() if get_step_number(record) is not None]
    report_numbers = [get_step_number(record) for record in rel_index.values() if get_step_number(record) is not None]

    # 1) Mapa final: contagem mínima obrigatória.
    record_check(
        results,
        "Mapa final contém 51 passos",
        len(mapa_index) == 51,
        [
            "Passos localizados no mapa final: {0}".format(len(mapa_index)),
            "Coleção usada no mapa final: {0}".format(core["mapa_steps_path"]),
        ],
    )

    # 2) Presença do único subpasso que deve estar ativo.
    p36_present = "P36" in mapa_index
    p36_active_local = extract_substep_ids_from_container(mapa_index.get("P36", {}).get("subpassos_inseridos")) + extract_scalar_id_list(
        mapa_index.get("P36", {}).get("subpassos_aprovados_ids"),
        is_substep_id,
    )
    p36_sp01_ok = p36_present and "P36_SP01" in unique_preserve_order(p36_active_local + active_substep_ids)
    record_check(
        results,
        "Mapa final contém o subpasso ativo P36_SP01",
        p36_sp01_ok,
        [
            "Subpassos ativos detetados no mapa: {0}".format(", ".join(active_substep_ids) or "(nenhum)"),
            "Subpassos ativos em P36: {0}".format(", ".join(unique_preserve_order(p36_active_local)) or "(nenhum)"),
        ],
    )

    # 3) Os 16 rejeitados não podem entrar como elementos operativos do mapa.
    rejected_substeps = sorted(
        substep_id
        for substep_id, record in agg_substep_index.items()
        if normalize_text(record.get("decisao_subpasso")) == "rejeitado"
    )
    approved_substeps = sorted(
        substep_id
        for substep_id, record in agg_substep_index.items()
        if normalize_text(record.get("decisao_subpasso")) == "aprovado"
    )
    active_rejected = sorted(set(rejected_substeps) & set(active_substep_ids))
    record_check(
        results,
        "Os 16 subpassos rejeitados estão ausentes do mapa final operativo",
        len(rejected_substeps) == 16 and not active_rejected,
        [
            "Rejeitados no agregador: {0}".format(", ".join(rejected_substeps) or "(nenhum)"),
            "Ativos no mapa final: {0}".format(", ".join(active_substep_ids) or "(nenhum)"),
            "Interseção indevida: {0}".format(", ".join(active_rejected) or "(vazia)"),
            "Nota: menções históricas em arbitragens ou resumos não contam como inserção ativa.",
        ],
    )

    # 4) Duplicações materiais.
    structural_duplicate_issues = []
    duplicate_number_map = sorted(number for number, count in Counter(map_numbers).items() if count > 1)
    duplicate_number_report = sorted(number for number, count in Counter(report_numbers).items() if count > 1)

    if mapa_duplicate_ids:
        structural_duplicate_issues.append("IDs de passo duplicados no mapa: {0}".format(", ".join(sorted(set(mapa_duplicate_ids)))))
    if rel_duplicate_ids:
        structural_duplicate_issues.append("IDs de linha duplicados no relatório: {0}".format(", ".join(sorted(set(rel_duplicate_ids)))))
    if agg_step_duplicate_ids:
        structural_duplicate_issues.append("IDs de decisão por passo duplicados no agregador: {0}".format(", ".join(sorted(set(agg_step_duplicate_ids)))))
    if agg_substep_duplicate_ids:
        structural_duplicate_issues.append("IDs de decisão por subpasso duplicados no agregador: {0}".format(", ".join(sorted(set(agg_substep_duplicate_ids)))))
    if agg_arbitration_duplicate_ids:
        structural_duplicate_issues.append("Corredores duplicados no agregador: {0}".format(", ".join(sorted(set(agg_arbitration_duplicate_ids)))))
    if duplicate_number_map:
        structural_duplicate_issues.append("numero_final duplicado no mapa: {0}".format(", ".join(str(x) for x in duplicate_number_map)))
    if duplicate_number_report:
        structural_duplicate_issues.append("numero_final duplicado no relatório: {0}".format(", ".join(str(x) for x in duplicate_number_report)))
    if duplicate_active_substep_ids:
        structural_duplicate_issues.append("Subpassos ativos duplicados no mapa: {0}".format(", ".join(sorted(set(duplicate_active_substep_ids)))))

    structural_duplicate_issues.extend(proposition_duplicates(mapa_index))
    structural_duplicate_issues.extend(substep_formulation_duplicates(active_substep_records))

    record_check(
        results,
        "Não subsistem duplicações materiais de passos ou subpassos",
        not structural_duplicate_issues,
        structural_duplicate_issues or [
            "Sem IDs duplicados.",
            "Sem numero_final duplicado.",
            "Sem proposições finais duplicadas no mapa.",
            "Sem formulações duplicadas entre subpassos ativos.",
        ],
    )

    # 5) Ajuste de numeração P49.
    reference_issues = []
    reference_issues.extend(step_reference_issues(mapa_index))
    reference_issues.extend(step_reference_issues(rel_index))

    numeration_contiguous_map = sorted(map_numbers) == list(range(1, 52))
    numeration_contiguous_report = sorted(report_numbers) == list(range(1, 52))

    p49_map = mapa_index.get("P49")
    p49_report = rel_index.get("P49")
    p49_ok = (
        p49_map is not None
        and p49_report is not None
        and get_step_number(p49_map) == 49
        and get_step_number(p49_report) == 49
    )

    old_p49_mismatch = []
    if p49_map is not None and get_step_number(p49_map) != 49:
        old_p49_mismatch.append("No mapa final, P49 tem numero_final={0}".format(get_step_number(p49_map)))
    if p49_report is not None and get_step_number(p49_report) != 49:
        old_p49_mismatch.append("No relatório final, P49 tem numero_final={0}".format(get_step_number(p49_report)))

    p49_summary_notes = []
    map_summary = core["mapa_final"].get("resumo_de_consolidacao", {}) if isinstance(core["mapa_final"], dict) else {}
    rel_validation = core["relatorio_final"].get("validacao_interna", {}) if isinstance(core["relatorio_final"], dict) else {}
    if isinstance(map_summary, dict) and "ajustes_de_numeracao_final" in map_summary:
        p49_summary_notes.append("Mapa final resume ajustes: {0}".format(", ".join(map_summary.get("ajustes_de_numeracao_final", []))))
    if isinstance(rel_validation, dict) and "ajustes_de_numeracao_final" in rel_validation:
        p49_summary_notes.append("Relatório final resume ajustes: {0}".format(", ".join(rel_validation.get("ajustes_de_numeracao_final", []))))

    record_check(
        results,
        "Ajuste de numeração P49 (48 -> 49) refletido sem restos ativos incompatíveis",
        numeration_contiguous_map and numeration_contiguous_report and p49_ok and not reference_issues and not old_p49_mismatch,
        [
            "Numeracao contínua no mapa: {0}".format(numeration_contiguous_map),
            "Numeracao contínua no relatório: {0}".format(numeration_contiguous_report),
            "P49 no mapa final: numero_final={0}".format(get_step_number(p49_map) if p49_map else None),
            "P49 no relatório final: numero_final={0}".format(get_step_number(p49_report) if p49_report else None),
        ] + p49_summary_notes + old_p49_mismatch + reference_issues,
    )

    # 6) Resíduos ativos herdados do pré-canónico nos passos canonicamente substituídos.
    precanonical_residue_issues = []
    for step_id in sorted(agg_step_index.keys()):
        final_step = mapa_index.get(step_id)
        if final_step is None:
            precanonical_residue_issues.append("{0}: não existe no mapa final.".format(step_id))
            continue

        if normalize_text(final_step.get("estado_de_fecho_canonico")) != "fechado":
            precanonical_residue_issues.append(
                "{0}: estado_de_fecho_canonico deveria estar 'fechado' e está '{1}'.".format(
                    step_id, final_step.get("estado_de_fecho_canonico")
                )
            )
        if final_step.get("texto_meta_editorial_detectado") is True:
            precanonical_residue_issues.append("{0}: texto_meta_editorial_detectado ainda está ativo.".format(step_id))
        if normalize_text(final_step.get("subpasso_sugerido")):
            precanonical_residue_issues.append("{0}: subpasso_sugerido ainda está preenchido.".format(step_id))
        if final_step.get("requer_arbitragem_humana") is True:
            precanonical_residue_issues.append("{0}: requer_arbitragem_humana ainda está ativo.".format(step_id))

        fonte_normativa = normalize_text(final_step.get("fonte_normativa_final") or "")
        if fonte_normativa and "decisoes_canonicas_intermedias_consolidado_final_intermedio.json" not in fonte_normativa:
            precanonical_residue_issues.append("{0}: fonte_normativa_final inesperada: {1}".format(step_id, fonte_normativa))

        origem_terminal = normalize_text(final_step.get("origem_no_fecho_terminal") or "")
        if origem_terminal and "agregador_intermedio_consolidado" not in origem_terminal:
            precanonical_residue_issues.append("{0}: origem_no_fecho_terminal inesperada: {1}".format(step_id, origem_terminal))

    record_check(
        results,
        "Não subsistem referências ativas do pré-canónico que contrariem o fecho consolidado",
        not precanonical_residue_issues,
        precanonical_residue_issues or [
            "Todos os passos canonicamente substituídos pelo agregador estão fechados e sem marcadores editoriais residuais.",
        ],
    )

    # 7) Corredores críticos.
    corridor_issues = []
    for corridor in EXPECTED_CORRIDORS:
        arbitration = agg_arbitration_index.get(corridor)
        if arbitration is None:
            corridor_issues.append("Arbitragem obrigatória em falta para o corredor {0}".format(corridor))
            continue

        if normalize_text(arbitration.get("estado_final_do_corredor")) != "fechado":
            corridor_issues.append("{0}: estado_final_do_corredor != fechado".format(corridor))
        if arbitration.get("sequencia_minima_ficou_fechada") is not True:
            corridor_issues.append("{0}: sequencia_minima_ficou_fechada != true".format(corridor))

        sequence = extract_scalar_id_list(arbitration.get("sequencia_minima_do_corredor"), is_step_id)
        missing_steps = [step_id for step_id in sequence if step_id not in mapa_index]
        if missing_steps:
            corridor_issues.append("{0}: passos da sequência mínima ausentes no mapa final: {1}".format(corridor, ", ".join(missing_steps)))

        for step_id in sequence:
            final_step = mapa_index.get(step_id)
            if final_step is None:
                continue
            if normalize_text(final_step.get("estado_de_fecho_canonico")) != "fechado":
                corridor_issues.append("{0}: passo {1} não está fechado no mapa final.".format(corridor, step_id))

        for previous_step, next_step in zip(sequence, sequence[1:]):
            prev_record = mapa_index.get(previous_step)
            next_record = mapa_index.get(next_step)
            if prev_record is None or next_record is None:
                continue
            if next_step not in extract_scalar_id_list(prev_record.get("prepara"), is_step_id):
                corridor_issues.append("{0}: {1} não prepara explicitamente {2}.".format(corridor, previous_step, next_step))
            if previous_step not in extract_scalar_id_list(next_record.get("depende_de"), is_step_id):
                corridor_issues.append("{0}: {2} não depende explicitamente de {1}.".format(corridor, previous_step, next_step))

        for item in to_list(arbitration.get("formulacoes_fixadas")):
            if not isinstance(item, dict):
                continue
            step_id = item.get("passo_id")
            formulation = item.get("formulacao_canonica_final")
            final_step = mapa_index.get(step_id)
            if final_step is None:
                corridor_issues.append("{0}: formulação fixada para passo ausente {1}.".format(corridor, step_id))
                continue
            if not values_equal(formulation, final_step.get("proposicao_final")):
                corridor_issues.append(
                    summarize_mismatch(step_id, "formulacao_canonica_final -> proposicao_final", formulation, final_step.get("proposicao_final"))
                )

        approved_in_corridor = extract_scalar_id_list(arbitration.get("subpassos_aprovados"), is_substep_id)
        for substep_id in approved_in_corridor:
            if substep_id not in active_substep_ids:
                corridor_issues.append("{0}: subpasso aprovado {1} não está ativo no mapa final.".format(corridor, substep_id))

    record_check(
        results,
        "Corredores críticos P33_P37, P25_P30, P42_P48 e P50 refletidos coerentemente no mapa final",
        not corridor_issues,
        corridor_issues or ["Todos os corredores críticos constam como fechados e coerentes com a projeção terminal."],
    )

    # 8) Relatório final: existência e coleção localizável.
    record_check(
        results,
        "Relatório final existe, é legível e tem coleção 1:1 localizável",
        len(rel_index) > 0,
        [
            "Linhas/passos localizados no relatório final: {0}".format(len(rel_index)),
            "Coleção usada no relatório final: {0}".format(core["rel_lines_path"]),
        ],
    )

    # 9) Relatório final vs mapa final.
    map_ids = set(mapa_index.keys())
    report_ids = set(rel_index.keys())
    missing_in_report = sorted(map_ids - report_ids)
    orphan_in_report = sorted(report_ids - map_ids)

    # Nota: estatuto_no_mapa é tratado aqui como materialmente relevante, porque o relatório
    # final afirma ser já pós-projeção canónica terminal. Divergência neste campo é, por isso,
    # considerada inconformidade de alinhamento 1:1.
    map_report_field_pairs = (
        ("numero_final", "numero_final"),
        ("bloco_id", "bloco_id"),
        ("bloco_titulo", "bloco_titulo"),
        ("depende_de", "depende_de"),
        ("prepara", "prepara"),
        ("proposicao_final", "proposicao_canonica_curta"),
        ("proposicao_final", "proposicao_canonica_tecnica"),
        ("tese_minima", "tese_minima_canonica"),
        ("justificacao_minima_suficiente", "justificacao_minima_canonica"),
        ("porque_o_anterior_nao_basta", "porque_o_anterior_nao_basta"),
        ("porque_nao_pode_ser_suprimido", "porque_nao_pode_ser_suprimido"),
        ("objecao_letal_a_bloquear", "objecao_letal_a_bloquear"),
        ("tipo_de_necessidade", "tipo_de_necessidade"),
        ("estado_de_fecho_canonico", "estado_de_fecho"),
        ("classificacao_funcional", "classificacao_funcional"),
        ("estatuto_no_mapa", "estatuto_no_mapa"),
        ("score_canonico_de_fecho", "score_canonico_de_fecho"),
        ("tipos_de_fragilidade", "tipos_de_fragilidade"),
        ("precisa_de_subpasso", "precisa_de_subpasso"),
        ("subpasso_sugerido", "subpasso_sugerido"),
        ("texto_meta_editorial_detectado", "texto_meta_editorial_detectado"),
        ("requer_arbitragem_humana", "requer_arbitragem_humana"),
        ("fragmentos_de_apoio_final", "fragmentos_de_apoio_final"),
        ("objecoes_bloqueadas", "objecoes_bloqueadas"),
        ("ponte_entrada", "ponte_entrada"),
        ("ponte_saida", "ponte_saida"),
        ("bloqueio_curto_da_objecao", "bloqueio_curto_da_objecao"),
        ("subpassos_aprovados_ids", "subpassos_aprovados_ids"),
        ("fonte_normativa_final", "fonte_normativa_final"),
        ("origem_no_fecho_terminal", "origem_no_fecho_terminal"),
    )
    report_mismatches = compare_field_mapping(mapa_index, rel_index, map_report_field_pairs)

    report_validacao = core["relatorio_final"].get("validacao_interna", {}) if isinstance(core["relatorio_final"], dict) else {}
    report_validacao_issues = []
    if isinstance(report_validacao, dict):
        for key in (
            "ids_unicos_ok",
            "numeracao_final_contigua_ok",
            "referencias_minimas_ok",
            "subpassos_aprovados_inseridos_ok",
            "corredores_criticos_fechados_ok",
        ):
            if key in report_validacao and report_validacao.get(key) is not True:
                report_validacao_issues.append("validacao_interna.{0} != true".format(key))

    report_substep_issues = []
    substeps_section = core["relatorio_final"].get("subpassos_decididos", {}) if isinstance(core["relatorio_final"], dict) else {}
    if isinstance(substeps_section, dict):
        approved_in_report = sorted(extract_substep_ids_from_container(substeps_section.get("aprovados_inseridos")))
        rejected_in_report = sorted(extract_substep_ids_from_container(substeps_section.get("rejeitados_nao_inseridos")))
        if approved_in_report and approved_in_report != sorted(approved_substeps):
            report_substep_issues.append("Aprovados no relatório não coincidem com o agregador: {0}".format(", ".join(approved_in_report)))
        if rejected_in_report and rejected_in_report != sorted(rejected_substeps):
            report_substep_issues.append("Rejeitados no relatório não coincidem com o agregador: {0}".format(", ".join(rejected_in_report)))

    record_check(
        results,
        "Relatório final alinhado 1:1 com o mapa final, sem órfãos e com numeração coerente",
        not missing_in_report and not orphan_in_report and not report_mismatches and not report_validacao_issues and not report_substep_issues,
        []
        + (["Passos do mapa sem linha correspondente: {0}".format(", ".join(missing_in_report))] if missing_in_report else [])
        + (["Linhas órfãs no relatório: {0}".format(", ".join(orphan_in_report))] if orphan_in_report else [])
        + report_mismatches
        + report_validacao_issues
        + report_substep_issues
        + ["Total no mapa: {0}; total no relatório: {1}".format(len(mapa_index), len(rel_index))],
    )

    # 10) Agregador consolidado -> mapa final.
    aggregator_step_pairs = (
        ("numero_final", "numero_final"),
        ("bloco_id", "bloco_id"),
        ("bloco_titulo", "bloco_titulo"),
        ("depende_de", "depende_de"),
        ("prepara", "prepara"),
        ("formulacao_canonica_final", "proposicao_final"),
        ("justificacao_minima_suficiente", "justificacao_minima_suficiente"),
        ("ponte_entrada", "ponte_entrada"),
        ("ponte_saida", "ponte_saida"),
        ("porque_o_anterior_nao_basta", "porque_o_anterior_nao_basta"),
        ("porque_nao_pode_ser_suprimido", "porque_nao_pode_ser_suprimido"),
        ("objecao_letal_a_bloquear", "objecao_letal_a_bloquear"),
        ("bloqueio_curto_da_objecao", "bloqueio_curto_da_objecao"),
        ("precisa_de_subpasso", "precisa_de_subpasso"),
        ("subpassos_aprovados_ids", "subpassos_aprovados_ids"),
        ("fragmentos_de_apoio_final", "fragmentos_de_apoio_final"),
        ("objecoes_bloqueadas_final", "objecoes_bloqueadas"),
        ("estado_final_do_passo", "estado_de_fecho_canonico"),
        ("reabrir_em_arbitragem_de_corredor", "reabrir_em_arbitragem_de_corredor"),
    )
    agg_step_projection_issues = []
    for step_id, record in agg_step_index.items():
        if step_id not in mapa_index:
            agg_step_projection_issues.append("{0}: passo decidido no agregador não existe no mapa final.".format(step_id))
        if normalize_text(record.get("estado_final_do_passo")) != "fechado":
            agg_step_projection_issues.append("{0}: estado_final_do_passo no agregador não é 'fechado'.".format(step_id))
    agg_step_projection_issues.extend(compare_field_mapping(agg_step_index, mapa_index, aggregator_step_pairs))

    record_check(
        results,
        "Mapa final respeita o fecho normativo projetado pelo agregador consolidado",
        not agg_step_projection_issues,
        agg_step_projection_issues or ["Todos os 19 passos decididos no agregador estão refletidos no mapa final sem divergências materiais."],
    )

    # 11) Agregador consolidado -> subpassos ativos.
    agg_substep_issues = []
    if sorted(active_substep_ids) != sorted(approved_substeps):
        agg_substep_issues.append(
            "Subpassos ativos no mapa ({0}) não coincidem com os aprovados no agregador ({1}).".format(
                ", ".join(sorted(active_substep_ids)) or "(nenhum)",
                ", ".join(sorted(approved_substeps)) or "(nenhum)",
            )
        )

    for approved_id in approved_substeps:
        approved_record = agg_substep_index.get(approved_id)
        active_record = active_substep_records.get(approved_id)
        if approved_record is None:
            agg_substep_issues.append("Subpasso aprovado ausente do agregador indexado: {0}".format(approved_id))
            continue
        if active_record is None:
            agg_substep_issues.append("Subpasso aprovado não encontrado como ativo no mapa: {0}".format(approved_id))
            continue

        substep_pairs = (
            ("subpasso_id", "id"),
            ("numero_ordinal_no_passo", "numero_ordinal_no_passo"),
            ("justificacao_da_decisao", "justificacao_da_decisao"),
            ("formulacao_subpasso", "formulacao_subpasso"),
            ("justificacao_minima_suficiente", "justificacao_minima_suficiente"),
            ("funcao_dedutiva", "funcao_dedutiva"),
            ("localizacao_na_cadeia", "localizacao_na_cadeia"),
            ("ponte_entrada", "ponte_entrada"),
            ("ponte_saida", "ponte_saida"),
            ("objecao_letal_a_bloquear", "objecao_letal_a_bloquear"),
            ("bloqueio_curto_da_objecao", "bloqueio_curto_da_objecao"),
            ("fragmentos_de_apoio_final", "fragmentos_de_apoio_final"),
            ("objecoes_bloqueadas_final", "objecoes_bloqueadas_final"),
        )
        for field_a, field_b in substep_pairs:
            if not values_equal(approved_record.get(field_a), active_record.get(field_b)):
                agg_substep_issues.append(
                    summarize_mismatch(approved_id, "{0} -> {1}".format(field_a, field_b), approved_record.get(field_a), active_record.get(field_b))
                )

    rejected_actives = sorted(set(rejected_substeps) & set(active_substep_ids))
    if rejected_actives:
        agg_substep_issues.append("Subpassos rejeitados ativos indevidamente: {0}".format(", ".join(rejected_actives)))

    record_check(
        results,
        "Não há reintroduções indevidas de subpassos rejeitados nem reversões aparentes de decisões consolidadas",
        not agg_substep_issues,
        agg_substep_issues or ["Apenas {0} está ativo no mapa final; os 16 rejeitados permanecem fora da estrutura operativa.".format(", ".join(sorted(approved_substeps)) or "(nenhum)")],
    )

    # 12) Corredores nos três níveis: agregador, mapa e relatório.
    agg_corridor_projection_issues = []
    report_corridors = core["relatorio_final"].get("corredores_criticos", {}) if isinstance(core["relatorio_final"], dict) else {}

    for corridor in EXPECTED_CORRIDORS:
        arbitration = agg_arbitration_index.get(corridor)
        report_corridor = report_corridors.get(corridor) if isinstance(report_corridors, dict) else None

        if arbitration is None:
            agg_corridor_projection_issues.append("Arbitragem ausente para o corredor {0}".format(corridor))
            continue
        if report_corridor is None:
            agg_corridor_projection_issues.append("Corredor {0} ausente do relatório final.".format(corridor))
            continue

        seq = extract_scalar_id_list(arbitration.get("sequencia_minima_do_corredor"), is_step_id)
        expected_total = len(seq)

        if report_corridor.get("total") != expected_total:
            agg_corridor_projection_issues.append("{0}: relatório final indica total={1}, esperado={2}".format(corridor, report_corridor.get("total"), expected_total))
        if report_corridor.get("fechados") != expected_total:
            agg_corridor_projection_issues.append("{0}: relatório final indica fechados={1}, esperado={2}".format(corridor, report_corridor.get("fechados"), expected_total))
        if report_corridor.get("abertos") not in (0, None):
            agg_corridor_projection_issues.append("{0}: relatório final indica abertos={1}".format(corridor, report_corridor.get("abertos")))
        if report_corridor.get("quase_fechados") not in (0, None):
            agg_corridor_projection_issues.append("{0}: relatório final indica quase_fechados={1}".format(corridor, report_corridor.get("quase_fechados")))
        if normalize_text(report_corridor.get("estado_final_do_corredor")) != "fechado":
            agg_corridor_projection_issues.append("{0}: relatório final não marca o corredor como fechado.".format(corridor))
        if report_corridor.get("sequencia_minima_ficou_fechada") is not True:
            agg_corridor_projection_issues.append("{0}: relatório final não marca sequencia_minima_ficou_fechada=true.".format(corridor))

    record_check(
        results,
        "Relatório final e mapa final refletem os corredores críticos fechados sem contradição material relevante",
        not agg_corridor_projection_issues,
        agg_corridor_projection_issues or ["Os quatro corredores críticos surgem fechados e sem contradições relevantes entre agregador, mapa e relatório."],
    )

    derived = {
        "mapa_index": mapa_index,
        "rel_index": rel_index,
        "agg_step_index": agg_step_index,
        "agg_substep_index": agg_substep_index,
        "agg_arbitration_index": agg_arbitration_index,
        "active_substep_ids": active_substep_ids,
        "approved_substeps": approved_substeps,
        "rejected_substeps": rejected_substeps,
    }
    return results, derived


# ---------------------------------------------------------------------------
# Relatório textual
# ---------------------------------------------------------------------------

def make_empty_derived():
    return {
        "mapa_index": {},
        "rel_index": {},
        "agg_step_index": {},
        "agg_substep_index": {},
        "agg_arbitration_index": {},
        "active_substep_ids": [],
        "approved_substeps": [],
        "rejected_substeps": [],
    }


def build_report_text(paths, loaded, results, derived, accepted):
    derived = derived or make_empty_derived()
    lines = []

    lines.append("RELATÓRIO DE CONFERÊNCIA FINAL DO FECHO CANÓNICO")
    lines.append("=" * 62)
    lines.append("")
    lines.append("Data/hora local: {0}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    lines.append("Veredito final: {0}".format("ACEITE" if accepted else "NÃO ACEITE"))
    lines.append("")

    lines.append("1. Estrutura de caminhos resolvida")
    lines.append("-" * 35)
    lines.append("Diretório do script: {0}".format(paths["script_dir"]))
    lines.append("Diretório do fecho canónico: {0}".format(paths["fecho_dir"]))
    lines.append("Diretório estrutural: {0}".format(paths["structural_dir"]))
    lines.append("")

    lines.append("2. Ficheiros usados")
    lines.append("-" * 17)
    for group_name in ("main", "parent", "structural"):
        lines.append("[{0}]".format(group_name))
        for file_name, path in paths[group_name].items():
            info = loaded["file_info"].get(file_name)
            if info:
                lines.append("- {0} | tamanho={1} bytes | sha256={2}".format(path, info["size"], short_hash(info["sha256"])))
            else:
                lines.append("- {0} | ERRO DE LEITURA".format(path))
        lines.append("")

    lines.append("3. Contagens principais")
    lines.append("-" * 22)
    lines.append("Passos no mapa final: {0}".format(len(derived.get("mapa_index", {}))))
    lines.append("Linhas no relatório final: {0}".format(len(derived.get("rel_index", {}))))
    lines.append("Decisões por passo no agregador: {0}".format(len(derived.get("agg_step_index", {}))))
    lines.append("Decisões por subpasso no agregador: {0}".format(len(derived.get("agg_substep_index", {}))))
    lines.append("Arbitragens de corredor no agregador: {0}".format(len(derived.get("agg_arbitration_index", {}))))
    lines.append("Subpassos ativos no mapa final: {0}".format(", ".join(sorted(derived.get("active_substep_ids", []))) or "(nenhum)"))
    lines.append("Subpassos aprovados no agregador: {0}".format(", ".join(sorted(derived.get("approved_substeps", []))) or "(nenhum)"))
    lines.append("Subpassos rejeitados no agregador: {0}".format(", ".join(sorted(derived.get("rejected_substeps", []))) or "(nenhum)"))
    lines.append("")

    lines.append("4. Verificações executadas")
    lines.append("-" * 27)
    for item in results:
        status = "PASS" if item["passed"] else "FAIL"
        lines.append("[{0}] {1}".format(status, item["name"]))
        for detail in item["details"]:
            lines.append("    - {0}".format(detail))
        lines.append("")

    lines.append("5. Inconformidades encontradas")
    lines.append("-" * 28)
    any_fail = False
    for item in results:
        if item["passed"]:
            continue
        any_fail = True
        lines.append("* {0}".format(item["name"]))
        for detail in item["details"]:
            lines.append("    - {0}".format(detail))
    if not any_fail:
        lines.append("Nenhuma inconformidade crítica detetada.")
    lines.append("")

    lines.append("6. Conclusão final")
    lines.append("-" * 18)
    if accepted:
        lines.append("Resultado final: ACEITE")
        lines.append("Os outputs terminais satisfazem, cumulativamente, os critérios materiais mínimos de conferência definidos para esta fase.")
    else:
        lines.append("Resultado final: NÃO ACEITE")
        lines.append("Pelo menos uma verificação crítica falhou; os outputs terminais não podem ser aceites como versão final corrente de trabalho sem correção prévia.")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def print_terminal_summary(results, accepted, report_path):
    print("")
    print("=== CONFERÊNCIA FINAL DO FECHO CANÓNICO ===")
    print("")
    for item in results:
        status = "PASS" if item["passed"] else "FAIL"
        print("[{0}] {1}".format(status, item["name"]))
        for detail in item["details"][:4]:
            print("    - {0}".format(detail))
        if len(item["details"]) > 4:
            print("    - ...")
    print("")
    print("Conclusão final: {0}".format("ACEITE" if accepted else "NÃO ACEITE"))
    print("Relatório gravado em: {0}".format(report_path))
    print("")


# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------

def main():
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    paths = resolve_paths(script_dir)
    report_path = Path(args.report_file).resolve() if args.report_file else (script_dir / REPORT_NAME_DEFAULT)

    loaded = load_inputs(paths)
    core, core_errors = collect_core_collections(loaded["json"])

    if core_errors:
        # Mesmo em falha inicial, gera relatório e devolve NÃO ACEITE.
        results = []
        combined_errors = list(loaded["errors"]) + list(core_errors)
        record_check(
            results,
            "Estrutura de caminhos e ficheiros obrigatórios",
            False,
            combined_errors or ["Falha inicial não especificada."],
        )

        manifesto = loaded["json"].get("manifesto_fecho_canonico.json", {})
        manifesto_ok = False
        manifesto_details = []
        if isinstance(manifesto, dict):
            outputs_finais = manifesto.get("outputs_finais", {})
            mapa_entry = outputs_finais.get("mapa_dedutivo_canonico_final", {})
            rel_entry = outputs_finais.get("relatorio_final_de_inevitabilidades", {})
            mapa_path = normalize_text(mapa_entry.get("path"))
            rel_path = normalize_text(rel_entry.get("path"))
            manifesto_ok = mapa_path == "outputs/mapa_dedutivo_canonico_final.json" and rel_path == "outputs/relatorio_final_de_inevitabilidades.json"
            manifesto_details.append("Manifesto: outputs finais declarados = {0} | {1}".format(mapa_path, rel_path))
            manifesto_details.append("Manifesto: usar_caminhos_relativos = {0}".format(manifesto.get("usar_caminhos_relativos")))
        record_check(
            results,
            "Manifesto coerente com os outputs finais esperados",
            manifesto_ok,
            manifesto_details or ["Manifesto não pôde ser avaliado."],
        )

        accepted = False
        report_text = build_report_text(paths, loaded, results, make_empty_derived(), accepted)
        report_path.write_text(report_text, encoding="utf-8")
        print_terminal_summary(results, accepted, report_path)
        sys.exit(1)

    results, derived = run_checks(paths, loaded, core)
    accepted = all(item["passed"] for item in results if item["critical"])

    report_text = build_report_text(paths, loaded, results, derived, accepted)
    report_path.write_text(report_text, encoding="utf-8")

    print_terminal_summary(results, accepted, report_path)
    sys.exit(0 if accepted else 1)


if __name__ == "__main__":
    main()