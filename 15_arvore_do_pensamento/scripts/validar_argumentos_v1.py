# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


INPUT_FILENAME = "arvore_do_pensamento_v1.json"
REPORT_FILENAME = "relatorio_validacao_argumentos_v1.txt"


class ValidationFatalError(RuntimeError):
    """Erro fatal que impede a validação."""


@dataclass
class CheckResult:
    nome: str
    status: str  # PASS | WARNING | FAIL
    detalhes: List[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        self.detalhes.append(message)


@dataclass
class PlausibilityWarning:
    ramo_id: str
    argumento_id: str
    tipo: str
    detalhe: str


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


def safe_list_of_strings(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    result: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def normalize_text(text: Optional[str]) -> str:
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().replace("-", "_").replace("/", "_").replace(" ", "_")


def tokenize_text(text: Optional[str]) -> Set[str]:
    normalized = normalize_text(text)
    cleaned = []
    for ch in normalized:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    tokens: Set[str] = set()
    for token in "".join(cleaned).split():
        token = token.strip("_")
        if token:
            tokens.add(token)
    return tokens


def parse_cap_number(cap_id: Any) -> Optional[int]:
    if not isinstance(cap_id, str):
        return None
    cap_id = cap_id.strip()
    if not cap_id.startswith("CAP_"):
        return None
    parts = cap_id.split("_")
    if len(parts) >= 2 and parts[1].isdigit():
        return int(parts[1])
    return None


def parse_prop_number(prop_id: Any) -> Optional[int]:
    if not isinstance(prop_id, str):
        return None
    prop_id = prop_id.strip()
    if not prop_id.startswith("P"):
        return None
    suffix = prop_id[1:]
    if suffix.isdigit():
        return int(suffix)
    return None


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
    argumentos = require_list(require_key(tree, "argumentos", "raiz"), "argumentos")

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

    argumento_map: Dict[str, Dict[str, Any]] = {}
    for idx, argumento in enumerate(argumentos, start=1):
        argumento_dict = require_dict(argumento, f"argumentos[{idx}]")
        argumento_id = require_key(argumento_dict, "id", f"argumentos[{idx}]")
        if not isinstance(argumento_id, str) or not argumento_id.strip():
            raise ValidationFatalError(f"argumentos[{idx}].id é inválido.")
        argumento_map[argumento_id] = argumento_dict

    return (
        fragmentos,
        microlinhas,
        ramos,
        argumentos,
        fragment_map,
        microlinha_map,
        ramo_map,
        argumento_map,
    )


def validate_argumentos_existence_and_type(tree: Dict[str, Any]) -> CheckResult:
    result = CheckResult("1. Existência e tipo do bloco argumentos", "PASS")
    if "argumentos" not in tree:
        result.status = "FAIL"
        result.add("O bloco 'argumentos' não existe.")
        return result
    if not isinstance(tree["argumentos"], list):
        result.status = "FAIL"
        result.add("O bloco 'argumentos' existe mas não é array/list.")
        return result
    result.add(f"Bloco 'argumentos' presente e com tipo array/list; total atual: {len(tree['argumentos'])}.")
    return result


def validate_argumento_minimum_fields(argumentos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("2. Campos mínimos de cada argumento", "PASS")
    required_fields = [
        "id",
        "tipo_no",
        "fontes_argumento",
        "capitulo",
        "parte",
        "nivel",
        "conceito_alvo",
        "criterio_ultimo",
        "natureza",
        "tipo_de_necessidade",
        "nivel_de_operacao",
        "fundamenta",
        "pressupostos_ontologicos",
        "outputs_instalados",
        "operacoes_chave",
        "estrutura_logica",
        "reducao_ao_absurdo",
        "ligacoes_narrativas",
        "observacoes",
        "ramo_ids",
        "convergencia_ids",
        "estado_validacao",
    ]

    for idx, argumento in enumerate(argumentos, start=1):
        missing = [field for field in required_fields if field not in argumento]
        if missing:
            result.status = "FAIL"
            result.add(
                f"argumentos[{idx}] id={safe_str(argumento.get('id'))} sem campos obrigatórios: {', '.join(missing)}."
            )

    if result.status == "PASS":
        result.add("Todos os argumentos contêm os campos mínimos obrigatórios.")
    return result


def validate_argumento_tipo_no(argumentos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("3. Tipo de nó", "PASS")
    for idx, argumento in enumerate(argumentos, start=1):
        tipo_no = argumento.get("tipo_no")
        if tipo_no != "argumento":
            result.status = "FAIL"
            result.add(
                f"argumentos[{idx}] id={safe_str(argumento.get('id'))} tem tipo_no={safe_str(tipo_no)}; esperado 'argumento'."
            )
    if result.status == "PASS":
        result.add("Todos os argumentos têm tipo_no='argumento'.")
    return result


def validate_ids_and_sources(argumentos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("4. Convenção e unicidade de IDs", "PASS")
    seen: Set[str] = set()

    for idx, argumento in enumerate(argumentos, start=1):
        argumento_id = argumento.get("id")
        if not isinstance(argumento_id, str) or not argumento_id.strip():
            result.status = "FAIL"
            result.add(f"argumentos[{idx}] tem id ausente, vazio ou inválido.")
            continue

        if argumento_id in seen:
            result.status = "FAIL"
            result.add(f"ID duplicado encontrado em argumentos[]: {argumento_id}.")
        seen.add(argumento_id)

        fontes = argumento.get("fontes_argumento")
        if not isinstance(fontes, list):
            result.status = "FAIL"
            result.add(
                f"argumentos[{idx}] id={argumento_id} tem 'fontes_argumento' inválido; esperado array/list."
            )

    if result.status == "PASS":
        result.add("Todos os IDs de argumentos são únicos e as fontes estão agregadas em objetos únicos.")
    return result


def validate_fundamenta_structure(argumentos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("5. Estrutura mínima de fundamenta", "PASS")
    for idx, argumento in enumerate(argumentos, start=1):
        fundamenta = argumento.get("fundamenta")
        if not isinstance(fundamenta, dict):
            result.status = "FAIL"
            result.add(
                f"argumentos[{idx}] id={safe_str(argumento.get('id'))} tem 'fundamenta' inválido; esperado object/dict."
            )
            continue

        for field_name in ("percursos", "regimes", "modulos"):
            value = fundamenta.get(field_name)
            if value is not None and not isinstance(value, list):
                result.status = merge_status(result.status, "WARNING")
                result.add(
                    f"argumentos[{idx}] id={safe_str(argumento.get('id'))} tem fundamenta.{field_name} com tipo inesperado."
                )

    if result.status == "PASS":
        result.add("Todos os argumentos têm bloco 'fundamenta' estruturalmente válido.")
    elif result.status == "WARNING":
        result.add("O bloco 'fundamenta' existe em todos os argumentos, com anomalias ligeiras em campos previstos.")
    return result


def validate_estrutura_logica_structure(argumentos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("6. Estrutura mínima de estrutura_logica", "PASS")
    for idx, argumento in enumerate(argumentos, start=1):
        estrutura = argumento.get("estrutura_logica")
        if not isinstance(estrutura, dict):
            result.status = "FAIL"
            result.add(
                f"argumentos[{idx}] id={safe_str(argumento.get('id'))} tem 'estrutura_logica' inválido; esperado object/dict."
            )
            continue

        for field_name in ("premissas", "deducoes_necessarias", "conclusao"):
            value = estrutura.get(field_name)
            if value is not None and not isinstance(value, (list, str, dict)):
                result.status = merge_status(result.status, "WARNING")
                result.add(
                    f"argumentos[{idx}] id={safe_str(argumento.get('id'))} tem estrutura_logica.{field_name} com tipo inesperado."
                )

    if result.status == "PASS":
        result.add("Todos os argumentos têm bloco 'estrutura_logica' estruturalmente válido.")
    elif result.status == "WARNING":
        result.add("O bloco 'estrutura_logica' existe em todos os argumentos, com anomalias ligeiras em campos previstos.")
    return result


def validate_reducao_ao_absurdo_structure(argumentos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("7. Estrutura mínima de reducao_ao_absurdo", "PASS")
    for idx, argumento in enumerate(argumentos, start=1):
        bloco = argumento.get("reducao_ao_absurdo")
        if not isinstance(bloco, dict):
            result.status = "FAIL"
            result.add(
                f"argumentos[{idx}] id={safe_str(argumento.get('id'))} tem 'reducao_ao_absurdo' inválido; esperado object/dict."
            )
    if result.status == "PASS":
        result.add("Todos os argumentos têm bloco 'reducao_ao_absurdo' estruturalmente válido.")
    return result


def validate_ligacoes_narrativas_structure(argumentos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("8. Estrutura mínima de ligacoes_narrativas", "PASS")
    for idx, argumento in enumerate(argumentos, start=1):
        bloco = argumento.get("ligacoes_narrativas")
        if not isinstance(bloco, dict):
            result.status = "FAIL"
            result.add(
                f"argumentos[{idx}] id={safe_str(argumento.get('id'))} tem 'ligacoes_narrativas' inválido; esperado object/dict."
            )
            continue

        for field_name in ("back_links", "depende_de_argumentos", "forward_links", "prepara_argumentos"):
            value = bloco.get(field_name)
            if value is not None and not isinstance(value, list):
                result.status = merge_status(result.status, "WARNING")
                result.add(
                    f"argumentos[{idx}] id={safe_str(argumento.get('id'))} tem ligacoes_narrativas.{field_name} com tipo inesperado."
                )

    if result.status == "PASS":
        result.add("Todos os argumentos têm bloco 'ligacoes_narrativas' estruturalmente válido.")
    elif result.status == "WARNING":
        result.add("O bloco 'ligacoes_narrativas' existe em todos os argumentos, com anomalias ligeiras em campos previstos.")
    return result


def validate_auxiliary_arrays(argumentos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("9. Arrays auxiliares", "PASS")
    array_fields = [
        "fontes_argumento",
        "pressupostos_ontologicos",
        "outputs_instalados",
        "operacoes_chave",
        "observacoes",
        "ramo_ids",
        "convergencia_ids",
    ]

    for idx, argumento in enumerate(argumentos, start=1):
        for field_name in array_fields:
            value = argumento.get(field_name)
            if not isinstance(value, list):
                result.status = "FAIL"
                result.add(
                    f"argumentos[{idx}] id={safe_str(argumento.get('id'))} tem '{field_name}' inválido; esperado array/list."
                )

    if result.status == "PASS":
        result.add("Todos os arrays auxiliares obrigatórios existem e têm tipo válido.")
    return result


def validate_ramo_ids_integrity(
    argumentos: List[Dict[str, Any]],
    ramo_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("10. Integridade de ramo_ids", "PASS")

    for idx, argumento in enumerate(argumentos, start=1):
        argumento_id = safe_str(argumento.get("id"))
        ramo_ids = argumento.get("ramo_ids")
        if not isinstance(ramo_ids, list):
            result.status = "FAIL"
            result.add(
                f"argumentos[{idx}] id={argumento_id} tem 'ramo_ids' inválido; esperado array/list."
            )
            continue

        local_seen: Set[str] = set()
        for pos, ramo_id in enumerate(ramo_ids, start=1):
            if not isinstance(ramo_id, str) or not ramo_id.strip():
                result.status = "FAIL"
                result.add(
                    f"argumentos[{idx}] id={argumento_id} tem ramo_id inválido na posição {pos}."
                )
                continue

            if ramo_id in local_seen:
                result.status = "FAIL"
                result.add(
                    f"argumentos[{idx}] id={argumento_id} contém ramo duplicado: {ramo_id}."
                )
            local_seen.add(ramo_id)

            if ramo_id not in ramo_map:
                result.status = "FAIL"
                result.add(
                    f"argumentos[{idx}] id={argumento_id} refere ramo inexistente: {ramo_id}."
                )

    if result.status == "PASS":
        result.add("Todos os 'ramo_ids' são válidos, existentes e sem duplicados internos.")
    return result


def validate_argumento_to_ramo_consistency(
    argumentos: List[Dict[str, Any]],
    ramo_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("11. Consistência argumento → ramo", "PASS")

    for argumento in argumentos:
        argumento_id = safe_str(argumento.get("id"))
        ramo_ids = argumento.get("ramo_ids")
        if not isinstance(ramo_ids, list):
            continue

        for ramo_id in ramo_ids:
            if not isinstance(ramo_id, str) or not ramo_id.strip():
                continue
            ramo = ramo_map.get(ramo_id)
            if ramo is None:
                continue

            argumento_ids_associados = safe_list_of_strings(ramo.get("argumento_ids_associados", []))
            if argumento_id not in argumento_ids_associados:
                result.status = "FAIL"
                result.add(
                    f"Argumento {argumento_id} lista o ramo {ramo_id}, mas o ramo não contém esse argumento em 'argumento_ids_associados'."
                )

    if result.status == "PASS":
        result.add("Todas as referências argumento → ramo são bidirecionalmente coerentes.")
    return result


def validate_ramo_to_argumento_consistency(
    ramos: List[Dict[str, Any]],
    argumento_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("12. Consistência ramo → argumento", "PASS")

    for idx, ramo in enumerate(ramos, start=1):
        ramo_id = safe_str(ramo.get("id"))
        argumento_ids = ramo.get("argumento_ids_associados", [])
        if argumento_ids is None:
            argumento_ids = []

        if not isinstance(argumento_ids, list):
            result.status = "FAIL"
            result.add(
                f"ramos[{idx}] id={ramo_id} tem 'argumento_ids_associados' inválido; esperado array/list."
            )
            continue

        for argumento_id in argumento_ids:
            if not isinstance(argumento_id, str) or not argumento_id.strip():
                result.status = "FAIL"
                result.add(
                    f"ramos[{idx}] id={ramo_id} contém argumento_id inválido em 'argumento_ids_associados'."
                )
                continue
            if argumento_id not in argumento_map:
                result.status = "FAIL"
                result.add(
                    f"ramos[{idx}] id={ramo_id} refere argumento inexistente: {argumento_id}."
                )

    if result.status == "PASS":
        result.add("Todos os 'argumento_ids_associados' referidos pelos ramos existem em 'argumentos[]'.")
    return result


def validate_microlinha_propagation(
    ramos: List[Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("13. Propagação para microlinhas", "PASS")

    for ramo in ramos:
        ramo_id = safe_str(ramo.get("id"))
        argumento_ids = set(safe_list_of_strings(ramo.get("argumento_ids_associados", [])))
        if not argumento_ids:
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

            sugeridos = set(safe_list_of_strings(microlinha.get("argumento_ids_sugeridos", [])))
            missing = sorted(argumento_ids - sugeridos)
            if missing:
                result.status = merge_status(result.status, "FAIL")
                result.add(
                    f"Microlinha {microlinha_id} do ramo {ramo_id} não reflete todos os argumentos do ramo em 'argumento_ids_sugeridos': "
                    f"{', '.join(missing)}."
                )

    if result.status == "PASS":
        result.add("A propagação de argumentos para microlinhas está coerente.")
    return result


def validate_fragment_propagation(
    ramos: List[Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("14. Propagação para fragmentos", "PASS")

    for ramo in ramos:
        ramo_id = safe_str(ramo.get("id"))
        argumento_ids = set(safe_list_of_strings(ramo.get("argumento_ids_associados", [])))
        if not argumento_ids:
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
                result.status = "FAIL"
                result.add(f"Microlinha {microlinha_id} tem 'fragmento_ids' inválido.")
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
                    result.add(f"Fragmento {fragmento_id} não tem 'ligacoes_arvore' válido.")
                    continue

                argumento_ids_frag = set(safe_list_of_strings(ligacoes.get("argumento_ids", [])))
                missing = sorted(argumento_ids - argumento_ids_frag)
                if missing:
                    result.status = merge_status(result.status, "FAIL")
                    result.add(
                        f"Fragmento {fragmento_id}, ligado à microlinha {microlinha_id} e ao ramo {ramo_id}, "
                        f"não reflete todos os argumentos esperados em 'ligacoes_arvore.argumento_ids': {', '.join(missing)}."
                    )

    if result.status == "PASS":
        result.add("A propagação de argumentos para fragmentos está coerente.")
    return result


def validate_estado_validacao(argumentos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("15. Estado de validação", "PASS")
    for idx, argumento in enumerate(argumentos, start=1):
        estado = argumento.get("estado_validacao")
        if not isinstance(estado, str) or not estado.strip():
            result.status = "FAIL"
            result.add(
                f"argumentos[{idx}] id={safe_str(argumento.get('id'))} tem 'estado_validacao' ausente, vazio ou inválido."
            )
    if result.status == "PASS":
        result.add("Todos os argumentos têm 'estado_validacao' preenchido.")
    return result


def validate_global_metrics(tree: Dict[str, Any], actual_total_argumentos: int) -> CheckResult:
    result = CheckResult("16. Métricas globais", "PASS")

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

    total_argumentos_metric = metricas.get("total_argumentos")
    if not isinstance(total_argumentos_metric, int):
        result.status = "FAIL"
        result.add("O campo 'validacao.metricas.total_argumentos' não existe ou não é inteiro.")
        return result

    if total_argumentos_metric != actual_total_argumentos:
        result.status = "FAIL"
        result.add(
            f"total_argumentos divergente: métrica={total_argumentos_metric}; real={actual_total_argumentos}."
        )
    else:
        result.add(f"total_argumentos coerente: {actual_total_argumentos}.")

    return result


def argumento_size_distribution(argumentos: List[Dict[str, Any]]) -> Dict[str, int]:
    dist = {"0": 0, "1": 0, "2": 0, "3": 0, "4+": 0}
    for argumento in argumentos:
        ramo_ids = argumento.get("ramo_ids")
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


def count_argumentos_with_ramos(argumentos: List[Dict[str, Any]]) -> int:
    total = 0
    for argumento in argumentos:
        ramo_ids = argumento.get("ramo_ids")
        if isinstance(ramo_ids, list) and len(ramo_ids) > 0:
            total += 1
    return total


def count_ramos_with_argumento(ramos: List[Dict[str, Any]]) -> int:
    total = 0
    for ramo in ramos:
        argumento_ids = ramo.get("argumento_ids_associados", [])
        if isinstance(argumento_ids, list) and len(safe_list_of_strings(argumento_ids)) > 0:
            total += 1
    return total


def infer_ramo_profile_for_plausibility(
    ramo: Dict[str, Any],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    microlinha_ids = ramo.get("microlinha_ids")
    if not isinstance(microlinha_ids, list):
        microlinha_ids = []

    zone_values: List[str] = []
    problem_values: List[str] = []
    work_values: List[str] = []
    percurso_ids = safe_list_of_strings(ramo.get("percurso_ids_associados", []))
    step_nums: List[int] = []
    tokens: Set[str] = set()

    tokens.update(tokenize_text(ramo.get("titulo")))
    tokens.update(tokenize_text(ramo.get("descricao_funcional")))
    tokens.update(tokenize_text(ramo.get("criterio_de_unidade")))
    for percurso_id in percurso_ids:
        tokens.update(tokenize_text(percurso_id))

    for passo_id in safe_list_of_strings(ramo.get("passo_ids_alvo", [])):
        n = parse_prop_number(passo_id)
        if n is not None:
            step_nums.append(n)
        tokens.update(tokenize_text(passo_id))

    for microlinha_id in microlinha_ids:
        microlinha = microlinha_map.get(microlinha_id)
        if not isinstance(microlinha, dict):
            continue

        tokens.update(tokenize_text(microlinha.get("titulo")))
        tokens.update(tokenize_text(microlinha.get("descricao_funcional")))

        criterio = microlinha.get("criterio_de_agregacao")
        if isinstance(criterio, dict):
            problema = criterio.get("problema_filosofico_dominante")
            if isinstance(problema, str) and problema.strip():
                problem_values.append(problema.strip())
                tokens.update(tokenize_text(problema))

        fragmento_ids = microlinha.get("fragmento_ids")
        if not isinstance(fragmento_ids, list):
            continue

        for fragmento_id in fragmento_ids:
            fragmento = fragment_map.get(fragmento_id)
            if not isinstance(fragmento, dict):
                continue

            cadencia = fragmento.get("cadencia")
            if isinstance(cadencia, dict):
                zona = cadencia.get("zona_provavel_percurso")
                if isinstance(zona, str) and zona.strip():
                    zone_values.append(zona.strip())
                    tokens.update(tokenize_text(zona))

            tratamento = fragmento.get("tratamento_filosofico")
            if isinstance(tratamento, dict):
                problema = tratamento.get("problema_filosofico_central")
                trabalho = tratamento.get("trabalho_no_sistema")
                if isinstance(problema, str) and problema.strip():
                    problem_values.append(problema.strip())
                    tokens.update(tokenize_text(problema))
                if isinstance(trabalho, str) and trabalho.strip():
                    work_values.append(trabalho.strip())
                    tokens.update(tokenize_text(trabalho))

            impacto = fragmento.get("impacto_mapa")
            if isinstance(impacto, dict):
                proposicoes = impacto.get("proposicoes_do_mapa_tocadas")
                if isinstance(proposicoes, list):
                    for proposicao in proposicoes:
                        if isinstance(proposicao, dict):
                            proposicao_id = proposicao.get("proposicao_id")
                            n = parse_prop_number(proposicao_id)
                            if n is not None:
                                step_nums.append(n)

    return {
        "ramo_id": safe_str(ramo.get("id")),
        "percurso_ids": percurso_ids,
        "dominant_zone": mode_from_list(zone_values),
        "dominant_problem": mode_from_list(problem_values),
        "dominant_work": mode_from_list(work_values),
        "step_nums": sorted(set(step_nums)),
        "tokens": tokens,
    }


def infer_argumento_profile_for_plausibility(argumento: Dict[str, Any]) -> Dict[str, Any]:
    fundamenta = argumento.get("fundamenta")
    if not isinstance(fundamenta, dict):
        fundamenta = {}

    tokens: Set[str] = set()
    for value in (
        argumento.get("id"),
        argumento.get("capitulo"),
        argumento.get("parte"),
        argumento.get("conceito_alvo"),
        argumento.get("criterio_ultimo"),
        argumento.get("natureza"),
        argumento.get("tipo_de_necessidade"),
        argumento.get("nivel_de_operacao"),
    ):
        tokens.update(tokenize_text(value if isinstance(value, str) else safe_str(value)))

    for value in safe_list_of_strings(argumento.get("pressupostos_ontologicos", [])):
        tokens.update(tokenize_text(value))
    for value in safe_list_of_strings(argumento.get("outputs_instalados", [])):
        tokens.update(tokenize_text(value))
    for value in safe_list_of_strings(argumento.get("operacoes_chave", [])):
        tokens.update(tokenize_text(value))
    for value in safe_list_of_strings(fundamenta.get("percursos", [])):
        tokens.update(tokenize_text(value))

    return {
        "argumento_id": safe_str(argumento.get("id")),
        "chapter_num": parse_cap_number(argumento.get("capitulo")),
        "parte": argumento.get("parte") if isinstance(argumento.get("parte"), str) else "",
        "nivel_de_operacao": argumento.get("nivel_de_operacao") if isinstance(argumento.get("nivel_de_operacao"), str) else "",
        "tipo_de_necessidade": argumento.get("tipo_de_necessidade") if isinstance(argumento.get("tipo_de_necessidade"), str) else "",
        "conceito_alvo": argumento.get("conceito_alvo") if isinstance(argumento.get("conceito_alvo"), str) else "",
        "fundamenta_percursos": safe_list_of_strings(fundamenta.get("percursos", [])),
        "tokens": tokens,
    }


def mode_from_list(values: List[str]) -> str:
    filtered = [v.strip() for v in values if isinstance(v, str) and v.strip()]
    if not filtered:
        return ""
    counts = Counter(filtered)
    best_count = max(counts.values())
    best = {k for k, v in counts.items() if v == best_count}
    for value in filtered:
        if value in best:
            return value
    return ""


def analyse_plausibility(
    ramos: List[Dict[str, Any]],
    argumento_map: Dict[str, Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
) -> List[PlausibilityWarning]:
    warnings: List[PlausibilityWarning] = []

    ramo_profiles: Dict[str, Dict[str, Any]] = {}
    argumento_profiles: Dict[str, Dict[str, Any]] = {}

    for ramo in ramos:
        ramo_id = safe_str(ramo.get("id"))
        ramo_profiles[ramo_id] = infer_ramo_profile_for_plausibility(ramo, microlinha_map, fragment_map)

    for argumento_id, argumento in argumento_map.items():
        argumento_profiles[argumento_id] = infer_argumento_profile_for_plausibility(argumento)

    for ramo in ramos:
        ramo_id = safe_str(ramo.get("id"))
        argumento_ids = safe_list_of_strings(ramo.get("argumento_ids_associados", []))
        ramo_profile = ramo_profiles[ramo_id]

        if len(argumento_ids) >= 3:
            partes = set()
            niveis = set()
            necessidades = set()
            conceitos = set()

            for argumento_id in argumento_ids:
                profile = argumento_profiles.get(argumento_id)
                if not profile:
                    continue
                if profile["parte"]:
                    partes.add(profile["parte"])
                if profile["nivel_de_operacao"]:
                    niveis.add(profile["nivel_de_operacao"])
                if profile["tipo_de_necessidade"]:
                    necessidades.add(profile["tipo_de_necessidade"])
                if profile["conceito_alvo"]:
                    conceitos.add(profile["conceito_alvo"])

            if len(partes) >= 3 or len(niveis) >= 3 or len(necessidades) >= 3 or len(conceitos) >= 3:
                warnings.append(
                    PlausibilityWarning(
                        ramo_id=ramo_id,
                        argumento_id=",".join(argumento_ids[:3]) + ("..." if len(argumento_ids) > 3 else ""),
                        tipo="heterogeneidade_excessiva",
                        detalhe=(
                            f"Ramo com vários argumentos e dispersão elevada "
                            f"(partes={len(partes)}, níveis_operação={len(niveis)}, necessidades={len(necessidades)}, conceitos={len(conceitos)})."
                        ),
                    )
                )

        for argumento_id in argumento_ids:
            argumento_profile = argumento_profiles.get(argumento_id)
            if not argumento_profile:
                continue

            overlap_tokens = ramo_profile["tokens"].intersection(argumento_profile["tokens"])
            percurso_overlap = set(ramo_profile["percurso_ids"]).intersection(set(argumento_profile["fundamenta_percursos"]))

            if ramo_profile["step_nums"] and argumento_profile["chapter_num"] is not None:
                min_gap = min(abs(s - argumento_profile["chapter_num"]) for s in ramo_profile["step_nums"])
            else:
                min_gap = None

            zone_problem_tokens = set()
            zone_problem_tokens.update(tokenize_text(ramo_profile["dominant_zone"]))
            zone_problem_tokens.update(tokenize_text(ramo_profile["dominant_problem"]))
            zone_problem_tokens.update(tokenize_text(ramo_profile["dominant_work"]))

            # B. Tensão entre ramo e argumento
            if min_gap is not None and min_gap >= 4 and not percurso_overlap and len(overlap_tokens) <= 1:
                warnings.append(
                    PlausibilityWarning(
                        ramo_id=ramo_id,
                        argumento_id=argumento_id,
                        tipo="tensao_ramo_argumento",
                        detalhe=(
                            f"Capítulo do argumento parece distante dos passos do ramo "
                            f"(diferença mínima={min_gap}) e sem apoio forte de percurso/sinais textuais."
                        ),
                    )
                )

            # C. Associação fraca por sinais mínimos
            weak_signal_count = 0
            if min_gap is not None and min_gap <= 1:
                weak_signal_count += 1
            if percurso_overlap:
                weak_signal_count += 1
            if zone_problem_tokens.intersection(argumento_profile["tokens"]):
                weak_signal_count += 1
            if len(overlap_tokens) >= 2:
                weak_signal_count += 1

            if weak_signal_count <= 1:
                warnings.append(
                    PlausibilityWarning(
                        ramo_id=ramo_id,
                        argumento_id=argumento_id,
                        tipo="associacao_fraca",
                        detalhe=(
                            "Associação com poucos sinais observáveis independentes "
                            f"(sinais_detectados={weak_signal_count})."
                        ),
                    )
                )
                continue

            # B adicional: ramo aparentemente estreito vs argumento muito transversal
            if len(argumento_ids) == 1 and argumento_profile["nivel_de_operacao"]:
                nivel_tokens = tokenize_text(argumento_profile["nivel_de_operacao"])
                if "transversal" in nivel_tokens and len(ramo_profile["step_nums"]) <= 1 and len(overlap_tokens) <= 2:
                    warnings.append(
                        PlausibilityWarning(
                            ramo_id=ramo_id,
                            argumento_id=argumento_id,
                            tipo="tensao_escala",
                            detalhe="Ramo local estreito associado a argumento com nível de operação aparentemente transversal.",
                        )
                    )

    deduped: List[PlausibilityWarning] = []
    seen_keys: Set[Tuple[str, str, str, str]] = set()
    for item in warnings:
        key = (item.ramo_id, item.argumento_id, item.tipo, item.detalhe)
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(item)

    deduped.sort(key=lambda x: (x.ramo_id, x.argumento_id, x.tipo, x.detalhe))
    return deduped


def validate_plausibility_block(
    ramos: List[Dict[str, Any]],
    argumento_map: Dict[str, Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
) -> Tuple[CheckResult, List[PlausibilityWarning], int, int]:
    warnings = analyse_plausibility(ramos, argumento_map, microlinha_map, fragment_map)

    total_associacoes = 0
    for ramo in ramos:
        total_associacoes += len(safe_list_of_strings(ramo.get("argumento_ids_associados", [])))

    assoc_keys_with_warning: Set[Tuple[str, str]] = set()
    for item in warnings:
        if "," in item.argumento_id and item.tipo == "heterogeneidade_excessiva":
            continue
        assoc_keys_with_warning.add((item.ramo_id, item.argumento_id))

    total_associacoes_com_aviso = len(assoc_keys_with_warning)
    total_associacoes_sem_aviso = max(total_associacoes - total_associacoes_com_aviso, 0)

    result = CheckResult("17. Bloco de plausibilidade das associações", "PASS")
    if warnings:
        result.status = "WARNING"
        result.add(
            f"Foram detetados {len(warnings)} aviso(s) de plausibilidade em {total_associacoes_com_aviso} associação(ões) ramo→argumento."
        )
        for item in warnings[:20]:
            result.add(
                f"{item.ramo_id} -> {item.argumento_id} [{item.tipo}]: {item.detalhe}"
            )
        if len(warnings) > 20:
            result.add(f"... e mais {len(warnings) - 20} aviso(s) não listados nesta secção resumida.")
    else:
        result.add("Não foram detetados avisos relevantes de plausibilidade.")
    return result, warnings, total_associacoes_sem_aviso, total_associacoes_com_aviso


def determine_quality_conclusion(
    checks: List[CheckResult],
    total_argumentos: int,
    argumentos_vazios: int,
    total_ramos: int,
    ramos_sem_argumento: int,
    plausibility_warning_count: int,
) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "INVALIDA"

    has_warning_check = any(check.status == "WARNING" for check in checks)
    muitos_argumentos_vazios = total_argumentos > 0 and (argumentos_vazios / total_argumentos) >= 0.35
    muitos_ramos_sem_argumento = total_ramos > 0 and (ramos_sem_argumento / total_ramos) >= 0.25
    muitos_avisos_plausibilidade = plausibility_warning_count >= 5

    if has_warning_check or muitos_argumentos_vazios or muitos_ramos_sem_argumento or muitos_avisos_plausibilidade:
        return "VALIDA COM AVISOS"

    return "VALIDA"


def build_terminal_output(
    total_argumentos: int,
    argumentos_com_ramos: int,
    argumentos_vazios: int,
    ramos_com_argumento: int,
    ramos_sem_argumento: int,
    plausibility_warning_count: int,
    checks: List[CheckResult],
    conclusion: str,
    report_path: Path,
) -> str:
    lines: List[str] = []
    lines.append(f"Argumentos totais: {total_argumentos}")
    lines.append(f"Argumentos com ramos: {argumentos_com_ramos}")
    lines.append(f"Argumentos vazios: {argumentos_vazios}")
    lines.append(f"Ramos com argumento: {ramos_com_argumento}")
    lines.append(f"Ramos sem argumento: {ramos_sem_argumento}")
    lines.append(f"Avisos de plausibilidade: {plausibility_warning_count}")
    lines.append("")

    for check in checks:
        lines.append(f"[{format_status(check.status)}] {check.nome}")

    lines.append("")
    lines.append(f"Conclusão final: {conclusion}")
    lines.append(f"Relatório escrito em: {report_path}")
    return "\n".join(lines)


def build_report(
    input_path: Path,
    total_argumentos: int,
    total_ramos: int,
    total_microlinhas: int,
    total_fragmentos: int,
    argumentos_com_ramos: int,
    argumentos_vazios: int,
    ramos_com_argumento: int,
    ramos_sem_argumento: int,
    dist: Dict[str, int],
    checks: List[CheckResult],
    conclusion: str,
    plausibility_warnings: List[PlausibilityWarning],
    total_associacoes: int,
    associacoes_sem_aviso: int,
    associacoes_com_aviso: int,
) -> str:
    lines: List[str] = []
    lines.append("RELATÓRIO DE VALIDAÇÃO DE ARGUMENTOS V1")
    lines.append("=" * 72)
    lines.append(f"Data/hora UTC: {current_utc_iso()}")
    lines.append(f"Ficheiro validado: {input_path}")
    lines.append("")

    lines.append("Contagem geral")
    lines.append("-" * 72)
    lines.append(f"Número total de argumentos: {total_argumentos}")
    lines.append(f"Número total de ramos: {total_ramos}")
    lines.append(f"Número total de microlinhas: {total_microlinhas}")
    lines.append(f"Número total de fragmentos: {total_fragmentos}")
    lines.append(f"Argumentos com ramos associados: {argumentos_com_ramos}")
    lines.append(f"Argumentos sem ramos associados: {argumentos_vazios}")
    lines.append(f"Ramos associados a pelo menos um argumento: {ramos_com_argumento}")
    lines.append(f"Ramos sem argumento: {ramos_sem_argumento}")
    lines.append("")

    lines.append("Distribuição dos argumentos por número de ramos")
    lines.append("-" * 72)
    lines.append(f"Argumentos com 0 ramos: {dist['0']}")
    lines.append(f"Argumentos com 1 ramo: {dist['1']}")
    lines.append(f"Argumentos com 2 ramos: {dist['2']}")
    lines.append(f"Argumentos com 3 ramos: {dist['3']}")
    lines.append(f"Argumentos com 4 ou mais ramos: {dist['4+']}")
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

    lines.append("Bloco de plausibilidade")
    lines.append("-" * 72)
    lines.append(f"Número total de associações ramo→argumento: {total_associacoes}")
    lines.append(f"Número de associações plausíveis sem aviso: {associacoes_sem_aviso}")
    lines.append(f"Número de associações com aviso de plausibilidade: {associacoes_com_aviso}")
    lines.append(f"Número total de avisos registados: {len(plausibility_warnings)}")
    if plausibility_warnings:
        lines.append("Casos mais problemáticos:")
        for item in plausibility_warnings[:25]:
            lines.append(
                f"  - {item.ramo_id} -> {item.argumento_id} [{item.tipo}] {item.detalhe}"
            )
        if len(plausibility_warnings) > 25:
            lines.append(f"  - ... e mais {len(plausibility_warnings) - 25} aviso(s).")
    else:
        lines.append("Sem avisos relevantes de plausibilidade.")
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

    check_argumentos = validate_argumentos_existence_and_type(tree)
    checks.append(check_argumentos)

    if check_argumentos.status == "FAIL":
        total_argumentos = 0
        total_ramos = len(tree.get("ramos", [])) if isinstance(tree.get("ramos"), list) else 0
        total_microlinhas = len(tree.get("microlinhas", [])) if isinstance(tree.get("microlinhas"), list) else 0
        total_fragmentos = len(tree.get("fragmentos", [])) if isinstance(tree.get("fragmentos"), list) else 0
        argumentos_com_ramos = 0
        argumentos_vazios = 0
        ramos_com_argumento = 0
        ramos_sem_argumento = total_ramos
        dist = {"0": 0, "1": 0, "2": 0, "3": 0, "4+": 0}
        conclusion = "INVALIDA"
        plausibility_warnings: List[PlausibilityWarning] = []

        report = build_report(
            input_path=paths["input"],
            total_argumentos=total_argumentos,
            total_ramos=total_ramos,
            total_microlinhas=total_microlinhas,
            total_fragmentos=total_fragmentos,
            argumentos_com_ramos=argumentos_com_ramos,
            argumentos_vazios=argumentos_vazios,
            ramos_com_argumento=ramos_com_argumento,
            ramos_sem_argumento=ramos_sem_argumento,
            dist=dist,
            checks=checks,
            conclusion=conclusion,
            plausibility_warnings=plausibility_warnings,
            total_associacoes=0,
            associacoes_sem_aviso=0,
            associacoes_com_aviso=0,
        )
        write_text(paths["report"], report)
        print(
            build_terminal_output(
                total_argumentos=total_argumentos,
                argumentos_com_ramos=argumentos_com_ramos,
                argumentos_vazios=argumentos_vazios,
                ramos_com_argumento=ramos_com_argumento,
                ramos_sem_argumento=ramos_sem_argumento,
                plausibility_warning_count=0,
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
        argumentos,
        fragment_map,
        microlinha_map,
        ramo_map,
        argumento_map,
    ) = collect_tree_maps(tree)

    total_argumentos = len(argumentos)
    total_ramos = len(ramos)
    total_microlinhas = len(microlinhas)
    total_fragmentos = len(fragmentos)

    checks.append(validate_argumento_minimum_fields(argumentos))
    checks.append(validate_argumento_tipo_no(argumentos))
    checks.append(validate_ids_and_sources(argumentos))
    checks.append(validate_fundamenta_structure(argumentos))
    checks.append(validate_estrutura_logica_structure(argumentos))
    checks.append(validate_reducao_ao_absurdo_structure(argumentos))
    checks.append(validate_ligacoes_narrativas_structure(argumentos))
    checks.append(validate_auxiliary_arrays(argumentos))
    checks.append(validate_ramo_ids_integrity(argumentos, ramo_map))
    checks.append(validate_argumento_to_ramo_consistency(argumentos, ramo_map))
    checks.append(validate_ramo_to_argumento_consistency(ramos, argumento_map))
    checks.append(validate_microlinha_propagation(ramos, microlinha_map))
    checks.append(validate_fragment_propagation(ramos, microlinha_map, fragment_map))
    checks.append(validate_estado_validacao(argumentos))
    checks.append(validate_global_metrics(tree, total_argumentos))

    plausibility_check, plausibility_warnings, associacoes_sem_aviso, associacoes_com_aviso = validate_plausibility_block(
        ramos=ramos,
        argumento_map=argumento_map,
        microlinha_map=microlinha_map,
        fragment_map=fragment_map,
    )
    checks.append(plausibility_check)

    argumentos_com_ramos = count_argumentos_with_ramos(argumentos)
    argumentos_vazios = total_argumentos - argumentos_com_ramos
    ramos_com_argumento = count_ramos_with_argumento(ramos)
    ramos_sem_argumento = total_ramos - ramos_com_argumento
    dist = argumento_size_distribution(argumentos)

    total_associacoes = 0
    for ramo in ramos:
        total_associacoes += len(safe_list_of_strings(ramo.get("argumento_ids_associados", [])))

    conclusion = determine_quality_conclusion(
        checks=checks,
        total_argumentos=total_argumentos,
        argumentos_vazios=argumentos_vazios,
        total_ramos=total_ramos,
        ramos_sem_argumento=ramos_sem_argumento,
        plausibility_warning_count=len(plausibility_warnings),
    )

    report = build_report(
        input_path=paths["input"],
        total_argumentos=total_argumentos,
        total_ramos=total_ramos,
        total_microlinhas=total_microlinhas,
        total_fragmentos=total_fragmentos,
        argumentos_com_ramos=argumentos_com_ramos,
        argumentos_vazios=argumentos_vazios,
        ramos_com_argumento=ramos_com_argumento,
        ramos_sem_argumento=ramos_sem_argumento,
        dist=dist,
        checks=checks,
        conclusion=conclusion,
        plausibility_warnings=plausibility_warnings,
        total_associacoes=total_associacoes,
        associacoes_sem_aviso=associacoes_sem_aviso,
        associacoes_com_aviso=associacoes_com_aviso,
    )
    write_text(paths["report"], report)

    print(
        build_terminal_output(
            total_argumentos=total_argumentos,
            argumentos_com_ramos=argumentos_com_ramos,
            argumentos_vazios=argumentos_vazios,
            ramos_com_argumento=ramos_com_argumento,
            ramos_sem_argumento=ramos_sem_argumento,
            plausibility_warning_count=len(plausibility_warnings),
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