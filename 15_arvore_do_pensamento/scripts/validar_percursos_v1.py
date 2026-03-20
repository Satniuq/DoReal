# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


INPUT_FILENAME = "arvore_do_pensamento_v1.json"
REPORT_FILENAME = "relatorio_validacao_percursos_v1.txt"


class ValidationFatalError(RuntimeError):
    """Erro fatal que impede a validação."""


@dataclass
class CheckResult:
    nome: str
    status: str  # PASS | WARNING | FAIL
    detalhes: List[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        self.detalhes.append(message)


def require_dict(value: Any, context: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationFatalError(
            f"Tipo inválido em {context}: esperado object/dict, obtido {type(value).__name__}."
        )
    return value


def require_list(value: Any, context: str) -> List[Any]:
    if not isinstance(value, list):
        raise ValidationFatalError(
            f"Tipo inválido em {context}: esperado array/list, obtido {type(value).__name__}."
        )
    return value


def require_key(mapping: Dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ValidationFatalError(f"Falta a chave obrigatória '{key}' em {context}.")
    return mapping[key]


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise ValidationFatalError(f"Ficheiro não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationFatalError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise ValidationFatalError(f"Não foi possível ler {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as exc:
        raise ValidationFatalError(f"Não foi possível escrever o relatório {path}: {exc}") from exc


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def safe_str(value: Any) -> str:
    if value is None:
        return "None"
    return str(value)


def status_rank(status: str) -> int:
    return {"PASS": 0, "WARNING": 1, "FAIL": 2}.get(status, 99)


def merge_status(current: str, new: str) -> str:
    return new if status_rank(new) > status_rank(current) else current


def format_status(status: str) -> str:
    return {"PASS": "PASS", "WARNING": "WARNING", "FAIL": "FAIL"}.get(status, status)


def build_paths(script_dir: Path) -> Dict[str, Path]:
    arvore_root = script_dir.parent
    return {
        "script_dir": script_dir,
        "arvore_root": arvore_root,
        "input": arvore_root / "01_dados" / INPUT_FILENAME,
        "report": arvore_root / "01_dados" / REPORT_FILENAME,
    }


def safe_list_of_strings(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    result: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def collect_tree_maps(
    tree: Dict[str, Any],
) -> Tuple[
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
]:
    fragmentos = require_list(require_key(tree, "fragmentos", "raiz"), "fragmentos")
    microlinhas = require_list(require_key(tree, "microlinhas", "raiz"), "microlinhas")
    ramos = require_list(require_key(tree, "ramos", "raiz"), "ramos")
    percursos = require_list(require_key(tree, "percursos", "raiz"), "percursos")

    fragment_map: Dict[str, Dict[str, Any]] = {}
    for idx, fragment in enumerate(fragmentos, start=1):
        fragment_dict = require_dict(fragment, f"fragmentos[{idx}]")
        fragment_id = require_key(fragment_dict, "id", f"fragmentos[{idx}]")
        if not isinstance(fragment_id, str) or not fragment_id.strip():
            raise ValidationFatalError(f"fragmentos[{idx}].id é inválido.")
        fragment_map[fragment_id] = fragment_dict

    microlinha_map: Dict[str, Dict[str, Any]] = {}
    for idx, microlinha in enumerate(microlinhas, start=1):
        microlinha_dict = require_dict(microlinha, f"microlinhas[{idx}]")
        microlinha_id = require_key(microlinha_dict, "id", f"microlinhas[{idx}]")
        if not isinstance(microlinha_id, str) or not microlinha_id.strip():
            raise ValidationFatalError(f"microlinhas[{idx}].id é inválido.")
        microlinha_map[microlinha_id] = microlinha_dict

    ramo_map: Dict[str, Dict[str, Any]] = {}
    for idx, ramo in enumerate(ramos, start=1):
        ramo_dict = require_dict(ramo, f"ramos[{idx}]")
        ramo_id = require_key(ramo_dict, "id", f"ramos[{idx}]")
        if not isinstance(ramo_id, str) or not ramo_id.strip():
            raise ValidationFatalError(f"ramos[{idx}].id é inválido.")
        ramo_map[ramo_id] = ramo_dict

    percurso_map: Dict[str, Dict[str, Any]] = {}
    for idx, percurso in enumerate(percursos, start=1):
        percurso_dict = require_dict(percurso, f"percursos[{idx}]")
        percurso_id = require_key(percurso_dict, "id", f"percursos[{idx}]")
        if not isinstance(percurso_id, str) or not percurso_id.strip():
            raise ValidationFatalError(f"percursos[{idx}].id é inválido.")
        percurso_map[percurso_id] = percurso_dict

    return (
        fragmentos,
        microlinhas,
        ramos,
        percursos,
        fragment_map,
        microlinha_map,
        ramo_map,
        percurso_map,
    )


def validate_percursos_existence_and_type(tree: Dict[str, Any]) -> CheckResult:
    result = CheckResult("1. Existência e tipo do bloco percursos", "PASS")
    if "percursos" not in tree:
        result.status = "FAIL"
        result.add("O bloco 'percursos' não existe.")
        return result
    if not isinstance(tree["percursos"], list):
        result.status = "FAIL"
        result.add("O bloco 'percursos' existe mas não é array/list.")
        return result

    result.add(f"Bloco 'percursos' presente e com tipo array/list; total atual: {len(tree['percursos'])}.")
    return result


def validate_percurso_minimum_fields(percursos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("2. Campos mínimos de cada percurso", "PASS")
    required_fields = [
        "id",
        "tipo_no",
        "meta",
        "pressupostos_fecho_ids",
        "directo",
        "com_pressupostos",
        "ramo_ids",
        "convergencia_ids",
        "estado_validacao",
    ]

    for idx, percurso in enumerate(percursos, start=1):
        missing = [field for field in required_fields if field not in percurso]
        if missing:
            result.status = "FAIL"
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} sem campos obrigatórios: {', '.join(missing)}."
            )

    if result.status == "PASS":
        result.add("Todos os percursos contêm os campos mínimos obrigatórios.")

    return result


def validate_percurso_tipo_no(percursos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("3. Tipo de nó", "PASS")
    for idx, percurso in enumerate(percursos, start=1):
        tipo_no = percurso.get("tipo_no")
        if tipo_no != "percurso":
            result.status = "FAIL"
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem tipo_no={safe_str(tipo_no)}; esperado 'percurso'."
            )

    if result.status == "PASS":
        result.add("Todos os percursos têm tipo_no='percurso'.")

    return result


def validate_meta_structure(percursos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("4. Estrutura mínima de meta", "PASS")
    for idx, percurso in enumerate(percursos, start=1):
        meta = percurso.get("meta")
        if not isinstance(meta, dict):
            result.status = "FAIL"
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem 'meta' inválido; esperado object/dict."
            )
            continue

        tipo_instancia = meta.get("tipo_instancia")
        if tipo_instancia is not None and not isinstance(tipo_instancia, str):
            result.status = merge_status(result.status, "WARNING")
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem meta.tipo_instancia com tipo inesperado."
            )

        pressupoe = meta.get("pressupoe_percursos")
        if pressupoe is not None and not isinstance(pressupoe, list):
            result.status = merge_status(result.status, "WARNING")
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem meta.pressupoe_percursos com tipo inesperado."
            )

        observacao = meta.get("observacao")
        if observacao is not None and not isinstance(observacao, str):
            result.status = merge_status(result.status, "WARNING")
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem meta.observacao com tipo inesperado."
            )

    if result.status == "PASS":
        result.add("Todos os percursos têm bloco 'meta' estruturalmente válido.")
    elif result.status == "WARNING":
        result.add("O bloco 'meta' existe em todos os percursos, com anomalias ligeiras em campos opcionais.")

    return result


def validate_directo_structure(percursos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("5. Estrutura mínima de directo", "PASS")
    for idx, percurso in enumerate(percursos, start=1):
        directo = percurso.get("directo")
        if not isinstance(directo, dict):
            result.status = "FAIL"
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem 'directo' inválido; esperado object/dict."
            )
            continue

        for field_name in ("caps_ids", "cap_ids_axiais", "cap_ids_participantes"):
            value = directo.get(field_name)
            if value is not None and not isinstance(value, list):
                result.status = merge_status(result.status, "WARNING")
                result.add(
                    f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem directo.{field_name} com tipo inesperado."
                )

    if result.status == "PASS":
        result.add("Todos os percursos têm bloco 'directo' estruturalmente válido.")
    elif result.status == "WARNING":
        result.add("O bloco 'directo' existe em todos os percursos, com anomalias ligeiras em campos previstos.")

    return result


def validate_com_pressupostos_structure(percursos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("6. Estrutura mínima de com_pressupostos", "PASS")
    for idx, percurso in enumerate(percursos, start=1):
        bloco = percurso.get("com_pressupostos")
        if not isinstance(bloco, dict):
            result.status = "FAIL"
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem 'com_pressupostos' inválido; esperado object/dict."
            )
            continue

        percursos_base_ids = bloco.get("percursos_base_ids")
        if percursos_base_ids is not None and not isinstance(percursos_base_ids, list):
            result.status = merge_status(result.status, "WARNING")
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem com_pressupostos.percursos_base_ids com tipo inesperado."
            )

        caps_ids = bloco.get("caps_ids")
        if caps_ids is not None and not isinstance(caps_ids, list):
            result.status = merge_status(result.status, "WARNING")
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem com_pressupostos.caps_ids com tipo inesperado."
            )

        resumo = bloco.get("resumo")
        if resumo is not None and not isinstance(resumo, str):
            result.status = merge_status(result.status, "WARNING")
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem com_pressupostos.resumo com tipo inesperado."
            )

    if result.status == "PASS":
        result.add("Todos os percursos têm bloco 'com_pressupostos' estruturalmente válido.")
    elif result.status == "WARNING":
        result.add("O bloco 'com_pressupostos' existe em todos os percursos, com anomalias ligeiras em campos previstos.")

    return result


def validate_auxiliary_arrays(percursos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("7. Arrays auxiliares", "PASS")
    for idx, percurso in enumerate(percursos, start=1):
        for field_name in ("pressupostos_fecho_ids", "ramo_ids", "convergencia_ids"):
            value = percurso.get(field_name)
            if not isinstance(value, list):
                result.status = "FAIL"
                result.add(
                    f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem '{field_name}' inválido; esperado array/list."
                )

    if result.status == "PASS":
        result.add("Todos os arrays auxiliares obrigatórios existem e têm tipo válido.")

    return result


def validate_estado_validacao(percursos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("8. Estado de validação", "PASS")
    for idx, percurso in enumerate(percursos, start=1):
        estado = percurso.get("estado_validacao")
        if not isinstance(estado, str) or not estado.strip():
            result.status = "FAIL"
            result.add(
                f"percursos[{idx}] id={safe_str(percurso.get('id'))} tem 'estado_validacao' ausente, vazio ou inválido."
            )

    if result.status == "PASS":
        result.add("Todos os percursos têm 'estado_validacao' preenchido.")

    return result


def validate_ramo_ids_integrity(
    percursos: List[Dict[str, Any]],
    ramo_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("9. Integridade de ramo_ids", "PASS")

    for idx, percurso in enumerate(percursos, start=1):
        percurso_id = safe_str(percurso.get("id"))
        ramo_ids = percurso.get("ramo_ids")
        if not isinstance(ramo_ids, list):
            result.status = "FAIL"
            result.add(
                f"percursos[{idx}] id={percurso_id} tem 'ramo_ids' inválido; esperado array/list."
            )
            continue

        local_seen: Set[str] = set()
        for pos, ramo_id in enumerate(ramo_ids, start=1):
            if not isinstance(ramo_id, str) or not ramo_id.strip():
                result.status = "FAIL"
                result.add(
                    f"percursos[{idx}] id={percurso_id} tem ramo_id inválido na posição {pos}."
                )
                continue

            if ramo_id in local_seen:
                result.status = "FAIL"
                result.add(
                    f"percursos[{idx}] id={percurso_id} contém ramo duplicado: {ramo_id}."
                )
            local_seen.add(ramo_id)

            if ramo_id not in ramo_map:
                result.status = "FAIL"
                result.add(
                    f"percursos[{idx}] id={percurso_id} refere ramo inexistente: {ramo_id}."
                )

    if result.status == "PASS":
        result.add("Todos os 'ramo_ids' são válidos, existentes e sem duplicados internos.")

    return result


def validate_percurso_to_ramo_consistency(
    percursos: List[Dict[str, Any]],
    ramo_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("10. Consistência percurso → ramo", "PASS")

    for percurso in percursos:
        percurso_id = safe_str(percurso.get("id"))
        ramo_ids = percurso.get("ramo_ids")
        if not isinstance(ramo_ids, list):
            continue

        for ramo_id in ramo_ids:
            if not isinstance(ramo_id, str) or not ramo_id.strip():
                continue
            ramo = ramo_map.get(ramo_id)
            if ramo is None:
                continue

            percurso_ids_associados = safe_list_of_strings(ramo.get("percurso_ids_associados", []))
            if percurso_id not in percurso_ids_associados:
                result.status = "FAIL"
                result.add(
                    f"Percurso {percurso_id} lista o ramo {ramo_id}, mas o ramo não contém esse percurso em 'percurso_ids_associados'."
                )

    if result.status == "PASS":
        result.add("Todas as referências percurso → ramo são bidirecionalmente coerentes.")

    return result


def validate_ramo_to_percurso_consistency(
    ramos: List[Dict[str, Any]],
    percurso_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("11. Consistência ramo → percurso", "PASS")

    for idx, ramo in enumerate(ramos, start=1):
        ramo_id = safe_str(ramo.get("id"))
        percurso_ids = ramo.get("percurso_ids_associados", [])
        if percurso_ids is None:
            percurso_ids = []
        if not isinstance(percurso_ids, list):
            result.status = "FAIL"
            result.add(
                f"ramos[{idx}] id={ramo_id} tem 'percurso_ids_associados' inválido; esperado array/list."
            )
            continue

        for percurso_id in percurso_ids:
            if not isinstance(percurso_id, str) or not percurso_id.strip():
                result.status = "FAIL"
                result.add(
                    f"ramos[{idx}] id={ramo_id} contém percurso_id inválido em 'percurso_ids_associados'."
                )
                continue
            if percurso_id not in percurso_map:
                result.status = "FAIL"
                result.add(
                    f"ramos[{idx}] id={ramo_id} refere percurso inexistente: {percurso_id}."
                )

    if result.status == "PASS":
        result.add("Todos os 'percurso_ids_associados' referidos pelos ramos existem em 'percursos[]'.")

    return result


def validate_microlinha_propagation(
    ramos: List[Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("12. Propagação para microlinhas", "PASS")

    for ramo in ramos:
        ramo_id = safe_str(ramo.get("id"))
        percurso_ids = set(safe_list_of_strings(ramo.get("percurso_ids_associados", [])))
        if not percurso_ids:
            continue

        microlinha_ids = ramo.get("microlinha_ids")
        if not isinstance(microlinha_ids, list):
            result.status = "FAIL"
            result.add(f"Ramo {ramo_id} tem 'microlinha_ids' inválido.")
            continue

        for microlinha_id in microlinha_ids:
            if not isinstance(microlinha_id, str) or not microlinha_id.strip():
                continue
            microlinha = microlinha_map.get(microlinha_id)
            if microlinha is None:
                continue

            sugeridos = set(safe_list_of_strings(microlinha.get("percurso_ids_sugeridos", [])))
            missing = sorted(percurso_ids - sugeridos)
            if missing:
                result.status = merge_status(result.status, "FAIL")
                result.add(
                    f"Microlinha {microlinha_id} do ramo {ramo_id} não reflete todos os percursos do ramo em 'percurso_ids_sugeridos': "
                    f"{', '.join(missing)}."
                )

    if result.status == "PASS":
        result.add("A propagação de percursos para microlinhas está coerente.")
    return result


def validate_fragment_propagation(
    ramos: List[Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("13. Propagação para fragmentos", "PASS")

    for ramo in ramos:
        ramo_id = safe_str(ramo.get("id"))
        percurso_ids = set(safe_list_of_strings(ramo.get("percurso_ids_associados", [])))
        if not percurso_ids:
            continue

        microlinha_ids = ramo.get("microlinha_ids")
        if not isinstance(microlinha_ids, list):
            result.status = "FAIL"
            result.add(f"Ramo {ramo_id} tem 'microlinha_ids' inválido.")
            continue

        for microlinha_id in microlinha_ids:
            if not isinstance(microlinha_id, str) or not microlinha_id.strip():
                continue
            microlinha = microlinha_map.get(microlinha_id)
            if microlinha is None:
                continue

            fragmento_ids = microlinha.get("fragmento_ids")
            if not isinstance(fragmento_ids, list):
                result.status = merge_status(result.status, "FAIL")
                result.add(
                    f"Microlinha {microlinha_id} tem 'fragmento_ids' inválido."
                )
                continue

            for fragmento_id in fragmento_ids:
                if not isinstance(fragmento_id, str) or not fragmento_id.strip():
                    continue
                fragmento = fragment_map.get(fragmento_id)
                if fragmento is None:
                    continue

                ligacoes = fragmento.get("ligacoes_arvore")
                if not isinstance(ligacoes, dict):
                    result.status = "FAIL"
                    result.add(
                        f"Fragmento {fragmento_id} não tem 'ligacoes_arvore' válido."
                    )
                    continue

                percurso_ids_frag = set(safe_list_of_strings(ligacoes.get("percurso_ids", [])))
                missing = sorted(percurso_ids - percurso_ids_frag)
                if missing:
                    result.status = merge_status(result.status, "FAIL")
                    result.add(
                        f"Fragmento {fragmento_id}, ligado à microlinha {microlinha_id} e ao ramo {ramo_id}, "
                        f"não reflete todos os percursos esperados em 'ligacoes_arvore.percurso_ids': {', '.join(missing)}."
                    )

    if result.status == "PASS":
        result.add("A propagação de percursos para fragmentos está coerente.")
    return result


def validate_global_metrics(tree: Dict[str, Any], actual_total_percursos: int) -> CheckResult:
    result = CheckResult("14. Métricas globais", "PASS")

    validacao = tree.get("validacao")
    if not isinstance(validacao, dict):
        result.status = "FAIL"
        result.add("O bloco 'validacao' não existe ou não é object/dict.")
        return result

    metricas = validacao.get("metricas")
    if not isinstance(metricas, dict):
        result.status = "FAIL"
        result.add("O bloco 'validacao.metricas' não existe ou não é object/dict.")
        return result

    total_percursos_metric = metricas.get("total_percursos")
    if not isinstance(total_percursos_metric, int):
        result.status = "FAIL"
        result.add("O campo 'validacao.metricas.total_percursos' não existe ou não é inteiro.")
        return result

    if total_percursos_metric != actual_total_percursos:
        result.status = "FAIL"
        result.add(
            f"total_percursos divergente: métrica={total_percursos_metric}; real={actual_total_percursos}."
        )
    else:
        result.add(f"total_percursos coerente: {actual_total_percursos}.")

    return result


def percurso_size_distribution(percursos: List[Dict[str, Any]]) -> Dict[str, int]:
    dist = {"0": 0, "1": 0, "2": 0, "3": 0, "4+": 0}
    for percurso in percursos:
        ramo_ids = percurso.get("ramo_ids")
        if not isinstance(ramo_ids, list):
            continue
        n = len(ramo_ids)
        if n == 0:
            dist["0"] += 1
        elif n == 1:
            dist["1"] += 1
        elif n == 2:
            dist["2"] += 1
        elif n == 3:
            dist["3"] += 1
        else:
            dist["4+"] += 1
    return dist


def count_percursos_with_ramos(percursos: List[Dict[str, Any]]) -> int:
    total = 0
    for percurso in percursos:
        ramo_ids = percurso.get("ramo_ids")
        if isinstance(ramo_ids, list) and len(ramo_ids) > 0:
            total += 1
    return total


def count_ramos_with_percurso(ramos: List[Dict[str, Any]]) -> int:
    total = 0
    for ramo in ramos:
        percurso_ids = ramo.get("percurso_ids_associados", [])
        if isinstance(percurso_ids, list) and len(safe_list_of_strings(percurso_ids)) > 0:
            total += 1
    return total


def determine_quality_conclusion(
    checks: List[CheckResult],
    total_percursos: int,
    percursos_vazios: int,
    total_ramos: int,
    ramos_sem_percurso: int,
) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "INVALIDA"

    has_warning_check = any(check.status == "WARNING" for check in checks)

    muitos_percursos_vazios = total_percursos > 0 and (percursos_vazios / total_percursos) >= 0.35
    muitos_ramos_sem_percurso = total_ramos > 0 and (ramos_sem_percurso / total_ramos) >= 0.25

    if has_warning_check or muitos_percursos_vazios or muitos_ramos_sem_percurso:
        return "VALIDA COM AVISOS"

    return "VALIDA"


def build_terminal_output(
    total_percursos: int,
    percursos_com_ramos: int,
    percursos_vazios: int,
    ramos_com_percurso: int,
    ramos_sem_percurso: int,
    checks: List[CheckResult],
    conclusion: str,
    report_path: Path,
) -> str:
    lines: List[str] = []
    lines.append(f"Percursos totais: {total_percursos}")
    lines.append(f"Percursos com ramos: {percursos_com_ramos}")
    lines.append(f"Percursos vazios: {percursos_vazios}")
    lines.append(f"Ramos com percurso: {ramos_com_percurso}")
    lines.append(f"Ramos sem percurso: {ramos_sem_percurso}")
    lines.append("")

    for check in checks:
        lines.append(f"[{format_status(check.status)}] {check.nome}")

    lines.append("")
    lines.append(f"Conclusão final: {conclusion}")
    lines.append(f"Relatório escrito em: {report_path}")
    return "\n".join(lines)


def build_report(
    input_path: Path,
    total_percursos: int,
    total_ramos: int,
    total_microlinhas: int,
    total_fragmentos: int,
    percursos_com_ramos: int,
    percursos_vazios: int,
    ramos_com_percurso: int,
    ramos_sem_percurso: int,
    dist: Dict[str, int],
    checks: List[CheckResult],
    conclusion: str,
) -> str:
    lines: List[str] = []
    lines.append("RELATÓRIO DE VALIDAÇÃO DE PERCURSOS V1")
    lines.append("=" * 72)
    lines.append(f"Data/hora UTC: {current_utc_iso()}")
    lines.append(f"Ficheiro validado: {input_path}")
    lines.append("")

    lines.append("Contagem geral")
    lines.append("-" * 72)
    lines.append(f"Número total de percursos: {total_percursos}")
    lines.append(f"Número total de ramos: {total_ramos}")
    lines.append(f"Número total de microlinhas: {total_microlinhas}")
    lines.append(f"Número total de fragmentos: {total_fragmentos}")
    lines.append(f"Percursos com ramos associados: {percursos_com_ramos}")
    lines.append(f"Percursos sem ramos associados: {percursos_vazios}")
    lines.append(f"Ramos associados a pelo menos um percurso: {ramos_com_percurso}")
    lines.append(f"Ramos sem percurso: {ramos_sem_percurso}")
    lines.append("")

    lines.append("Distribuição de percursos por número de ramos")
    lines.append("-" * 72)
    lines.append(f"Percursos com 0 ramos: {dist['0']}")
    lines.append(f"Percursos com 1 ramo: {dist['1']}")
    lines.append(f"Percursos com 2 ramos: {dist['2']}")
    lines.append(f"Percursos com 3 ramos: {dist['3']}")
    lines.append(f"Percursos com 4 ou mais ramos: {dist['4+']}")
    lines.append("")

    lines.append("Verificações executadas")
    lines.append("-" * 72)
    for check in checks:
        lines.append(f"[{format_status(check.status)}] {check.nome}")
        if check.detalhes:
            for detalhe in check.detalhes:
                lines.append(f"  - {detalhe}")
        else:
            lines.append("  - Sem observações.")
    lines.append("")

    lines.append("Conclusão final")
    lines.append("-" * 72)
    lines.append(conclusion)
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    _ = argv  # sem argumentos nesta v1

    script_dir = Path(__file__).resolve().parent
    paths = build_paths(script_dir)

    tree = load_json(paths["input"])
    tree = require_dict(tree, "raiz")

    checks: List[CheckResult] = []

    check_percursos = validate_percursos_existence_and_type(tree)
    checks.append(check_percursos)

    if check_percursos.status == "FAIL":
        total_percursos = 0
        total_ramos = len(tree.get("ramos", [])) if isinstance(tree.get("ramos"), list) else 0
        total_microlinhas = len(tree.get("microlinhas", [])) if isinstance(tree.get("microlinhas"), list) else 0
        total_fragmentos = len(tree.get("fragmentos", [])) if isinstance(tree.get("fragmentos"), list) else 0
        percursos_com_ramos = 0
        percursos_vazios = 0
        ramos_com_percurso = 0
        ramos_sem_percurso = total_ramos
        dist = {"0": 0, "1": 0, "2": 0, "3": 0, "4+": 0}
        conclusion = "INVALIDA"

        report = build_report(
            input_path=paths["input"],
            total_percursos=total_percursos,
            total_ramos=total_ramos,
            total_microlinhas=total_microlinhas,
            total_fragmentos=total_fragmentos,
            percursos_com_ramos=percursos_com_ramos,
            percursos_vazios=percursos_vazios,
            ramos_com_percurso=ramos_com_percurso,
            ramos_sem_percurso=ramos_sem_percurso,
            dist=dist,
            checks=checks,
            conclusion=conclusion,
        )
        write_text(paths["report"], report)
        print(
            build_terminal_output(
                total_percursos=total_percursos,
                percursos_com_ramos=percursos_com_ramos,
                percursos_vazios=percursos_vazios,
                ramos_com_percurso=ramos_com_percurso,
                ramos_sem_percurso=ramos_sem_percurso,
                checks=checks,
                conclusion=conclusion,
                report_path=paths["report"],
            )
        )
        return 1

    (
        fragmentos,
        microlinhas,
        ramos,
        percursos,
        fragment_map,
        microlinha_map,
        ramo_map,
        percurso_map,
    ) = collect_tree_maps(tree)

    total_percursos = len(percursos)
    total_ramos = len(ramos)
    total_microlinhas = len(microlinhas)
    total_fragmentos = len(fragmentos)

    checks.append(validate_percurso_minimum_fields(percursos))
    checks.append(validate_percurso_tipo_no(percursos))
    checks.append(validate_meta_structure(percursos))
    checks.append(validate_directo_structure(percursos))
    checks.append(validate_com_pressupostos_structure(percursos))
    checks.append(validate_auxiliary_arrays(percursos))
    checks.append(validate_estado_validacao(percursos))
    checks.append(validate_ramo_ids_integrity(percursos, ramo_map))
    checks.append(validate_percurso_to_ramo_consistency(percursos, ramo_map))
    checks.append(validate_ramo_to_percurso_consistency(ramos, percurso_map))
    checks.append(validate_microlinha_propagation(ramos, microlinha_map))
    checks.append(validate_fragment_propagation(ramos, microlinha_map, fragment_map))
    checks.append(validate_global_metrics(tree, total_percursos))

    percursos_com_ramos = count_percursos_with_ramos(percursos)
    percursos_vazios = total_percursos - percursos_com_ramos
    ramos_com_percurso = count_ramos_with_percurso(ramos)
    ramos_sem_percurso = total_ramos - ramos_com_percurso
    dist = percurso_size_distribution(percursos)

    conclusion = determine_quality_conclusion(
        checks=checks,
        total_percursos=total_percursos,
        percursos_vazios=percursos_vazios,
        total_ramos=total_ramos,
        ramos_sem_percurso=ramos_sem_percurso,
    )

    report = build_report(
        input_path=paths["input"],
        total_percursos=total_percursos,
        total_ramos=total_ramos,
        total_microlinhas=total_microlinhas,
        total_fragmentos=total_fragmentos,
        percursos_com_ramos=percursos_com_ramos,
        percursos_vazios=percursos_vazios,
        ramos_com_percurso=ramos_com_percurso,
        ramos_sem_percurso=ramos_sem_percurso,
        dist=dist,
        checks=checks,
        conclusion=conclusion,
    )
    write_text(paths["report"], report)

    print(
        build_terminal_output(
            total_percursos=total_percursos,
            percursos_com_ramos=percursos_com_ramos,
            percursos_vazios=percursos_vazios,
            ramos_com_percurso=ramos_com_percurso,
            ramos_sem_percurso=ramos_sem_percurso,
            checks=checks,
            conclusion=conclusion,
            report_path=paths["report"],
        )
    )

    return 1 if conclusion == "INVALIDA" else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationFatalError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)