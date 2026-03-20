# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


INPUT_FILENAME = "arvore_do_pensamento_v1.json"
REPORT_FILENAME = "relatorio_validacao_ramos_v1.txt"

RAMO_ID_PATTERN = re.compile(r"^RA_\d{4}$")
PASSO_ID_PATTERN = re.compile(r"^P\d{1,4}$")


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


def parse_prop_number(prop_id: str) -> Optional[int]:
    match = re.fullmatch(r"P(\d+)", prop_id.strip()) if isinstance(prop_id, str) else None
    return int(match.group(1)) if match else None


def format_status(status: str) -> str:
    return {"PASS": "PASS", "WARNING": "WARNING", "FAIL": "FAIL"}.get(status, status)


def status_rank(status: str) -> int:
    return {"PASS": 0, "WARNING": 1, "FAIL": 2}.get(status, 99)


def merge_status(current: str, new: str) -> str:
    return new if status_rank(new) > status_rank(current) else current


def safe_str(value: Any) -> str:
    if value is None:
        return "None"
    return str(value)


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_paths(script_dir: Path) -> Dict[str, Path]:
    arvore_root = script_dir.parent
    return {
        "script_dir": script_dir,
        "arvore_root": arvore_root,
        "input": arvore_root / "01_dados" / INPUT_FILENAME,
        "report": arvore_root / "01_dados" / REPORT_FILENAME,
    }


def get_fragment_order(fragment: Dict[str, Any], fragment_id: str) -> int:
    order = fragment.get("ordem_no_ficheiro")
    if not isinstance(order, int):
        raise ValidationFatalError(
            f"O fragmento '{fragment_id}' não tem 'ordem_no_ficheiro' inteiro."
        )
    return order


def get_microlinha_fragment_ids(microlinha: Dict[str, Any], microlinha_id: str) -> List[str]:
    fragment_ids = microlinha.get("fragmento_ids")
    if not isinstance(fragment_ids, list):
        raise ValidationFatalError(
            f"A microlinha '{microlinha_id}' não tem 'fragmento_ids' em formato array/list."
        )
    return fragment_ids


def get_microlinha_order_range(
    microlinha: Dict[str, Any],
    microlinha_id: str,
    fragment_map: Dict[str, Dict[str, Any]],
) -> Tuple[int, int]:
    fragment_ids = get_microlinha_fragment_ids(microlinha, microlinha_id)
    if not fragment_ids:
        raise ValidationFatalError(
            f"A microlinha '{microlinha_id}' não contém fragmentos."
        )

    orders: List[int] = []
    for fragment_id in fragment_ids:
        if not isinstance(fragment_id, str) or not fragment_id.strip():
            raise ValidationFatalError(
                f"A microlinha '{microlinha_id}' contém fragmento inválido em 'fragmento_ids'."
            )
        fragment = fragment_map.get(fragment_id)
        if fragment is None:
            raise ValidationFatalError(
                f"A microlinha '{microlinha_id}' refere o fragmento inexistente '{fragment_id}'."
            )
        orders.append(get_fragment_order(fragment, fragment_id))

    return min(orders), max(orders)


def get_all_microlinha_exception_ids(microlinha: Dict[str, Any], microlinha_id: str) -> List[str]:
    value = microlinha.get("excecao_ids", [])
    if not isinstance(value, list):
        raise ValidationFatalError(
            f"A microlinha '{microlinha_id}' tem 'excecao_ids' inválido; esperado array/list."
        )
    result: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def microlinha_has_active_exception(microlinha: Dict[str, Any]) -> bool:
    estado = microlinha.get("estado_excecao")
    if not isinstance(estado, str):
        return False
    return estado.strip() in {"ativa_prioritaria", "ativa_tolerada"}


def ramo_has_active_exception(ramo: Dict[str, Any]) -> bool:
    estado = ramo.get("estado_excecao")
    if not isinstance(estado, str):
        return False
    return estado.strip() in {"ativa_prioritaria", "ativa_tolerada"}


def collect_tree_maps(
    tree: Dict[str, Any],
) -> Tuple[
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Set[str],
]:
    fragmentos = require_list(require_key(tree, "fragmentos", "raiz"), "fragmentos")
    microlinhas = require_list(require_key(tree, "microlinhas", "raiz"), "microlinhas")
    ramos = require_list(require_key(tree, "ramos", "raiz"), "ramos")
    excecoes = require_list(require_key(tree, "excecoes", "raiz"), "excecoes")

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

    excecao_ids: Set[str] = set()
    for idx, excecao in enumerate(excecoes, start=1):
        excecao_dict = require_dict(excecao, f"excecoes[{idx}]")
        exc_id = require_key(excecao_dict, "id", f"excecoes[{idx}]")
        if not isinstance(exc_id, str) or not exc_id.strip():
            raise ValidationFatalError(f"excecoes[{idx}].id é inválido.")
        excecao_ids.add(exc_id)

    return (
        fragmentos,
        microlinhas,
        ramos,
        fragment_map,
        microlinha_map,
        ramo_map,
        excecao_ids,
    )


def validate_ramos_existence_and_type(tree: Dict[str, Any]) -> CheckResult:
    result = CheckResult("1. Existência e tipo do bloco ramos", "PASS")
    if "ramos" not in tree:
        result.status = "FAIL"
        result.add("O bloco 'ramos' não existe.")
        return result
    if not isinstance(tree["ramos"], list):
        result.status = "FAIL"
        result.add("O bloco 'ramos' existe mas não é array/list.")
        return result
    result.add(f"Bloco 'ramos' presente e com tipo array/list; total atual: {len(tree['ramos'])}.")
    return result


def validate_ramo_minimum_fields(ramos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("2. Campos mínimos de cada ramo", "PASS")
    required_fields = [
        "id",
        "tipo_no",
        "titulo",
        "descricao_funcional",
        "criterio_de_unidade",
        "microlinha_ids",
        "percurso_ids_associados",
        "argumento_ids_associados",
        "passo_ids_alvo",
        "convergencia_ids",
        "prioridade_de_consolidacao",
        "estado_validacao",
        "estado_excecao",
        "excecao_ids",
        "observacoes",
    ]

    for idx, ramo in enumerate(ramos, start=1):
        context = f"ramos[{idx}]"
        missing = [field for field in required_fields if field not in ramo]
        if missing:
            result.status = "FAIL"
            result.add(f"{context} sem campos obrigatórios: {', '.join(missing)}.")

    if result.status == "PASS":
        result.add("Todos os ramos contêm os campos mínimos obrigatórios.")

    return result


def validate_ramo_ids(ramos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("3. Convenção e unicidade de IDs", "PASS")
    seen: Set[str] = set()

    for idx, ramo in enumerate(ramos, start=1):
        ramo_id = ramo.get("id")
        context = f"ramos[{idx}]"
        if not isinstance(ramo_id, str) or not ramo_id.strip():
            result.status = "FAIL"
            result.add(f"{context}.id ausente ou inválido.")
            continue
        if not RAMO_ID_PATTERN.fullmatch(ramo_id):
            result.status = "FAIL"
            result.add(f"{context}.id='{ramo_id}' não respeita o formato RA_0001.")
        if ramo_id in seen:
            result.status = "FAIL"
            result.add(f"ID duplicado encontrado: {ramo_id}.")
        seen.add(ramo_id)

    if result.status == "PASS":
        result.add("Todos os IDs de ramo são únicos e respeitam o padrão esperado.")

    return result


def validate_ramo_tipo_no(ramos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("4. Tipo de nó", "PASS")
    for idx, ramo in enumerate(ramos, start=1):
        tipo_no = ramo.get("tipo_no")
        if tipo_no != "ramo":
            result.status = "FAIL"
            result.add(f"ramos[{idx}] id={safe_str(ramo.get('id'))} tem tipo_no={safe_str(tipo_no)}; esperado 'ramo'.")

    if result.status == "PASS":
        result.add("Todos os ramos têm tipo_no='ramo'.")

    return result


def validate_ramo_auxiliary_arrays(ramos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("5. Arrays auxiliares", "PASS")
    array_fields = [
        "percurso_ids_associados",
        "argumento_ids_associados",
        "passo_ids_alvo",
        "convergencia_ids",
        "excecao_ids",
        "observacoes",
    ]

    for idx, ramo in enumerate(ramos, start=1):
        for field_name in array_fields:
            value = ramo.get(field_name)
            if not isinstance(value, list):
                result.status = "FAIL"
                result.add(
                    f"ramos[{idx}] id={safe_str(ramo.get('id'))} tem '{field_name}' inválido; esperado array/list."
                )

    if result.status == "PASS":
        result.add("Todos os arrays auxiliares existem e têm tipo válido.")

    return result


def validate_ramo_required_nonempty_fields(ramos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("6. Estado de validação e campos textuais obrigatórios", "PASS")
    required_nonempty = [
        "criterio_de_unidade",
        "prioridade_de_consolidacao",
        "estado_validacao",
        "estado_excecao",
        "titulo",
        "descricao_funcional",
    ]

    for idx, ramo in enumerate(ramos, start=1):
        for field_name in required_nonempty:
            value = ramo.get(field_name)
            if not isinstance(value, str) or not value.strip():
                result.status = "FAIL"
                result.add(
                    f"ramos[{idx}] id={safe_str(ramo.get('id'))} tem '{field_name}' ausente, vazio ou inválido."
                )

    if result.status == "PASS":
        result.add("Todos os campos textuais obrigatórios estão preenchidos.")

    return result


def validate_microlinha_integrity_and_uniqueness(
    ramos: List[Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
) -> Tuple[CheckResult, Dict[str, str]]:
    result = CheckResult("7. Integridade de microlinha_ids", "PASS")
    microlinha_to_ramo: Dict[str, str] = {}

    for idx, ramo in enumerate(ramos, start=1):
        ramo_id = safe_str(ramo.get("id"))
        microlinha_ids = ramo.get("microlinha_ids")

        if not isinstance(microlinha_ids, list):
            result.status = "FAIL"
            result.add(f"ramos[{idx}] id={ramo_id} tem 'microlinha_ids' inválido; esperado array/list.")
            continue

        if not microlinha_ids:
            result.status = "FAIL"
            result.add(f"ramos[{idx}] id={ramo_id} tem 'microlinha_ids' vazio.")
            continue

        local_seen: Set[str] = set()
        for pos, microlinha_id in enumerate(microlinha_ids, start=1):
            if not isinstance(microlinha_id, str) or not microlinha_id.strip():
                result.status = "FAIL"
                result.add(f"ramos[{idx}] id={ramo_id} tem microlinha_id inválido na posição {pos}.")
                continue

            if microlinha_id in local_seen:
                result.status = "FAIL"
                result.add(f"ramos[{idx}] id={ramo_id} contém microlinha duplicada: {microlinha_id}.")
            local_seen.add(microlinha_id)

            if microlinha_id not in microlinha_map:
                result.status = "FAIL"
                result.add(f"ramos[{idx}] id={ramo_id} refere microlinha inexistente: {microlinha_id}.")
                continue

            previous_ramo = microlinha_to_ramo.get(microlinha_id)
            if previous_ramo is not None and previous_ramo != ramo_id:
                result.status = "FAIL"
                result.add(
                    f"A microlinha {microlinha_id} pertence a mais de um ramo: {previous_ramo} e {ramo_id}."
                )
            else:
                microlinha_to_ramo[microlinha_id] = ramo_id

    if result.status == "PASS":
        result.add("Todas as microlinhas referidas existem e cada microlinha pertence no máximo a um ramo.")

    return result, microlinha_to_ramo


def validate_ramo_microlinha_consistency(
    ramos: List[Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("8. Consistência entre ramos e microlinhas", "PASS")

    for idx, ramo in enumerate(ramos, start=1):
        ramo_id = safe_str(ramo.get("id"))
        microlinha_ids = ramo.get("microlinha_ids")
        if not isinstance(microlinha_ids, list) or not microlinha_ids:
            continue

        ordem_pairs: List[Tuple[int, int, str]] = []
        ramo_exc_ids = ramo.get("excecao_ids")
        if not isinstance(ramo_exc_ids, list):
            ramo_exc_ids = []

        ramo_exc_set = {
            x.strip() for x in ramo_exc_ids
            if isinstance(x, str) and x.strip()
        }

        ramo_has_exc = ramo_has_active_exception(ramo)

        for expected_ordem, microlinha_id in enumerate(microlinha_ids, start=1):
            microlinha = microlinha_map.get(microlinha_id)
            if microlinha is None:
                continue

            actual_ordem = microlinha.get("ordem_no_ramo")
            if not isinstance(actual_ordem, int):
                result.status = "FAIL"
                result.add(
                    f"Ramo {ramo_id}: microlinha {microlinha_id} sem 'ordem_no_ramo' inteiro."
                )
            elif actual_ordem != expected_ordem:
                result.status = "FAIL"
                result.add(
                    f"Ramo {ramo_id}: microlinha {microlinha_id} com ordem_no_ramo={actual_ordem}; esperado {expected_ordem}."
                )

            try:
                order_start, order_end = get_microlinha_order_range(microlinha, microlinha_id, fragment_map)
                ordem_pairs.append((order_start, order_end, microlinha_id))
            except ValidationFatalError as exc:
                result.status = "FAIL"
                result.add(f"Ramo {ramo_id}: {exc}")

            mic_exc_ids = set(get_all_microlinha_exception_ids(microlinha, microlinha_id))
            mic_has_exc = microlinha_has_active_exception(microlinha)

            if mic_has_exc and not ramo_has_exc:
                result.status = "FAIL"
                result.add(
                    f"Ramo {ramo_id}: contém microlinha {microlinha_id} com exceção ativa, "
                    f"mas o ramo não reflete exceção ativa em 'estado_excecao'."
                )

            missing_exc = sorted(mic_exc_ids - ramo_exc_set)
            if mic_has_exc and missing_exc:
                result.status = "FAIL"
                result.add(
                    f"Ramo {ramo_id}: faltam exceções do ramo para refletir microlinha {microlinha_id}: "
                    f"{', '.join(missing_exc)}."
                )

        if ordem_pairs:
            listed_order = [item[2] for item in ordem_pairs]
            sorted_by_fragment_order = [item[2] for item in sorted(ordem_pairs, key=lambda x: (x[0], x[1], x[2]))]
            if listed_order != sorted_by_fragment_order:
                result.status = "FAIL"
                result.add(
                    f"Ramo {ramo_id}: a ordem de 'microlinha_ids' não é coerente com a ordem dos fragmentos. "
                    f"Declarada={listed_order}; esperada={sorted_by_fragment_order}."
                )

    if result.status == "PASS":
        result.add("As ordens internas e a relação com exceções nas microlinhas estão coerentes.")

    return result


def validate_fragment_ramo_consistency(
    ramos: List[Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
    fragment_map: Dict[str, Dict[str, Any]],
    ramo_map: Dict[str, Dict[str, Any]],
) -> CheckResult:
    result = CheckResult("9. Consistência com fragmentos[].ligacoes_arvore.ramo_ids", "PASS")

    expected_fragment_ramo: Dict[str, Set[str]] = defaultdict(set)

    for ramo in ramos:
        ramo_id = safe_str(ramo.get("id"))
        microlinha_ids = ramo.get("microlinha_ids")
        if not isinstance(microlinha_ids, list):
            continue

        for microlinha_id in microlinha_ids:
            microlinha = microlinha_map.get(microlinha_id)
            if microlinha is None:
                continue
            try:
                fragment_ids = get_microlinha_fragment_ids(microlinha, microlinha_id)
            except ValidationFatalError as exc:
                result.status = "FAIL"
                result.add(f"Ramo {ramo_id}: {exc}")
                continue
            for fragment_id in fragment_ids:
                expected_fragment_ramo[fragment_id].add(ramo_id)

    for fragment_id, fragment in fragment_map.items():
        ligacoes = fragment.get("ligacoes_arvore")
        if not isinstance(ligacoes, dict):
            result.status = "FAIL"
            result.add(f"Fragmento {fragment_id} sem 'ligacoes_arvore' válido.")
            continue

        ramo_ids = ligacoes.get("ramo_ids")
        if not isinstance(ramo_ids, list):
            result.status = "FAIL"
            result.add(f"Fragmento {fragment_id} sem 'ligacoes_arvore.ramo_ids' em formato array/list.")
            continue

        declared = {
            item.strip()
            for item in ramo_ids
            if isinstance(item, str) and item.strip()
        }

        for declared_ramo_id in sorted(declared):
            if declared_ramo_id not in ramo_map:
                result.status = "FAIL"
                result.add(
                    f"Fragmento {fragment_id} refere ramo inexistente em ligacoes_arvore.ramo_ids: {declared_ramo_id}."
                )

        expected = expected_fragment_ramo.get(fragment_id, set())
        if expected != declared:
            result.status = "FAIL"
            result.add(
                f"Fragmento {fragment_id}: ramo_ids declarados={sorted(declared)} "
                f"divergem do esperado={sorted(expected)}."
            )

    if result.status == "PASS":
        result.add("As ligações de ramo nos fragmentos estão coerentes com os ramos declarados.")

    return result


def validate_unitary_ramos(ramos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("10. Ramos unitários", "PASS")

    for ramo in ramos:
        ramo_id = safe_str(ramo.get("id"))
        microlinha_ids = ramo.get("microlinha_ids")
        estado_validacao = ramo.get("estado_validacao")

        if isinstance(microlinha_ids, list) and len(microlinha_ids) == 1:
            if not isinstance(estado_validacao, str) or estado_validacao.strip() == "valido":
                result.status = merge_status(result.status, "FAIL")
                result.add(
                    f"Ramo unitário {ramo_id} está marcado como plenamente válido; "
                    f"esperava-se estado compatível com aviso."
                )

    if result.status == "PASS":
        result.add("Os ramos unitários estão assinalados com estado compatível com aviso.")

    return result


def validate_ramo_exceptions(
    ramos: List[Dict[str, Any]],
    microlinha_map: Dict[str, Dict[str, Any]],
    excecao_ids_validas: Set[str],
) -> CheckResult:
    result = CheckResult("11. Ramos com exceções", "PASS")

    for ramo in ramos:
        ramo_id = safe_str(ramo.get("id"))
        ramo_excecao_ids = ramo.get("excecao_ids")
        if not isinstance(ramo_excecao_ids, list):
            result.status = "FAIL"
            result.add(f"Ramo {ramo_id} tem 'excecao_ids' inválido.")
            continue

        ramo_exc_set = {
            item.strip() for item in ramo_excecao_ids
            if isinstance(item, str) and item.strip()
        }

        invalid_exc = sorted([item for item in ramo_exc_set if item not in excecao_ids_validas])
        if invalid_exc:
            result.status = "FAIL"
            result.add(
                f"Ramo {ramo_id} refere exceções inexistentes: {', '.join(invalid_exc)}."
            )

        microlinha_ids = ramo.get("microlinha_ids")
        if not isinstance(microlinha_ids, list):
            continue

        active_mic_exc: Set[str] = set()
        has_active_mic = False
        for microlinha_id in microlinha_ids:
            microlinha = microlinha_map.get(microlinha_id)
            if microlinha is None:
                continue
            if microlinha_has_active_exception(microlinha):
                has_active_mic = True
                active_mic_exc.update(get_all_microlinha_exception_ids(microlinha, microlinha_id))

        if has_active_mic and not ramo_has_active_exception(ramo):
            result.status = "FAIL"
            result.add(
                f"Ramo {ramo_id} contém microlinhas com exceção ativa mas o ramo não reflete exceção ativa."
            )

        missing = sorted(active_mic_exc - ramo_exc_set)
        if missing:
            result.status = "FAIL"
            result.add(
                f"Ramo {ramo_id} não lista todas as exceções ativas das microlinhas: {', '.join(missing)}."
            )

    if result.status == "PASS":
        result.add("Os ramos com exceções refletem corretamente as exceções das microlinhas.")

    return result


def validate_global_metrics(tree: Dict[str, Any], actual_total_ramos: int) -> CheckResult:
    result = CheckResult("12. Métricas globais", "PASS")

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

    total_ramos_metric = metricas.get("total_ramos")
    if not isinstance(total_ramos_metric, int):
        result.status = "FAIL"
        result.add("O campo 'validacao.metricas.total_ramos' não existe ou não é inteiro.")
        return result

    if total_ramos_metric != actual_total_ramos:
        result.status = "FAIL"
        result.add(
            f"total_ramos divergente: métrica={total_ramos_metric}; real={actual_total_ramos}."
        )
    else:
        result.add(f"total_ramos coerente: {actual_total_ramos}.")

    return result


def validate_passo_ids_alvo(ramos: List[Dict[str, Any]]) -> CheckResult:
    result = CheckResult("13. Coerência básica de passo_ids_alvo", "PASS")

    for ramo in ramos:
        ramo_id = safe_str(ramo.get("id"))
        passo_ids = ramo.get("passo_ids_alvo")
        if not isinstance(passo_ids, list):
            result.status = "FAIL"
            result.add(f"Ramo {ramo_id} tem 'passo_ids_alvo' inválido.")
            continue

        for item in passo_ids:
            if not isinstance(item, str) or not item.strip():
                result.status = "FAIL"
                result.add(f"Ramo {ramo_id} contém valor inválido em 'passo_ids_alvo': {safe_str(item)}.")
                continue
            if not PASSO_ID_PATTERN.fullmatch(item.strip()):
                result.status = merge_status(result.status, "WARNING")
                result.add(
                    f"Ramo {ramo_id} contém passo_ids_alvo com formato anómalo: {item}."
                )

    if result.status == "PASS":
        result.add("Os campos 'passo_ids_alvo' têm formato básico plausível.")
    elif result.status == "WARNING":
        result.add("Existem entradas anómalas em 'passo_ids_alvo', mas sem bloquear a estrutura.")

    return result


def size_distribution(ramos: List[Dict[str, Any]]) -> Dict[str, int]:
    dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5+": 0}
    for ramo in ramos:
        microlinha_ids = ramo.get("microlinha_ids")
        if not isinstance(microlinha_ids, list):
            continue
        n = len(microlinha_ids)
        if n <= 0:
            continue
        if n == 1:
            dist["1"] += 1
        elif n == 2:
            dist["2"] += 1
        elif n == 3:
            dist["3"] += 1
        elif n == 4:
            dist["4"] += 1
        else:
            dist["5+"] += 1
    return dist


def count_ramos_with_exceptions(ramos: List[Dict[str, Any]]) -> int:
    total = 0
    for ramo in ramos:
        if ramo_has_active_exception(ramo):
            total += 1
    return total


def determine_quality_conclusion(
    checks: List[CheckResult],
    total_ramos: int,
    unitary_ramos: int,
    exception_ramos: int,
) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "INVALIDA"

    warning_checks = [check for check in checks if check.status == "WARNING"]
    many_unitaries = total_ramos > 0 and unitary_ramos / total_ramos >= 0.35
    many_exceptions = total_ramos > 0 and exception_ramos / total_ramos >= 0.25

    if warning_checks or many_unitaries or many_exceptions:
        return "VALIDA COM AVISOS"

    return "VALIDA"


def build_terminal_output(
    total_ramos: int,
    total_microlinhas: int,
    total_fragmentos: int,
    unitary_ramos: int,
    exception_ramos: int,
    checks: List[CheckResult],
    conclusion: str,
    report_path: Path,
) -> str:
    lines: List[str] = []
    lines.append(f"Ramos totais: {total_ramos}")
    lines.append(f"Microlinhas totais: {total_microlinhas}")
    lines.append(f"Fragmentos totais: {total_fragmentos}")
    lines.append(f"Ramos unitários: {unitary_ramos}")
    lines.append(f"Ramos com exceções: {exception_ramos}")
    lines.append("")

    for check in checks:
        lines.append(f"[{format_status(check.status)}] {check.nome}")

    lines.append("")
    lines.append(f"Conclusão final: {conclusion}")
    lines.append(f"Relatório escrito em: {report_path}")
    return "\n".join(lines)


def build_report(
    input_path: Path,
    total_ramos: int,
    total_microlinhas: int,
    total_fragmentos: int,
    unitary_ramos: int,
    exception_ramos: int,
    dist: Dict[str, int],
    checks: List[CheckResult],
    conclusion: str,
) -> str:
    lines: List[str] = []
    lines.append("RELATÓRIO DE VALIDAÇÃO DE RAMOS V1")
    lines.append("=" * 72)
    lines.append(f"Data/hora UTC: {current_utc_iso()}")
    lines.append(f"Ficheiro validado: {input_path}")
    lines.append("")

    lines.append("Contagem geral")
    lines.append("-" * 72)
    lines.append(f"Número total de ramos: {total_ramos}")
    lines.append(f"Número total de microlinhas: {total_microlinhas}")
    lines.append(f"Número total de fragmentos: {total_fragmentos}")
    lines.append(f"Número de ramos unitários: {unitary_ramos}")
    lines.append(f"Número de ramos com exceções: {exception_ramos}")
    lines.append("")

    lines.append("Distribuição de tamanhos")
    lines.append("-" * 72)
    lines.append(f"Ramos com 1 microlinha: {dist['1']}")
    lines.append(f"Ramos com 2 microlinhas: {dist['2']}")
    lines.append(f"Ramos com 3 microlinhas: {dist['3']}")
    lines.append(f"Ramos com 4 microlinhas: {dist['4']}")
    lines.append(f"Ramos com 5 ou mais microlinhas: {dist['5+']}")
    lines.append("")

    lines.append("Verificações executadas")
    lines.append("-" * 72)
    for check in checks:
        lines.append(f"[{format_status(check.status)}] {check.nome}")
        if check.detalhes:
            for detail in check.detalhes:
                lines.append(f"  - {detail}")
        else:
            lines.append("  - Sem observações.")
    lines.append("")

    lines.append("Conclusão final")
    lines.append("-" * 72)
    lines.append(conclusion)
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    _ = argv  # script sem argumentos nesta v1

    script_dir = Path(__file__).resolve().parent
    paths = build_paths(script_dir)

    tree = load_json(paths["input"])
    tree = require_dict(tree, "raiz")

    checks: List[CheckResult] = []

    check_ramos = validate_ramos_existence_and_type(tree)
    checks.append(check_ramos)

    if check_ramos.status == "FAIL":
        total_ramos = 0
        total_microlinhas = len(tree.get("microlinhas", [])) if isinstance(tree.get("microlinhas"), list) else 0
        total_fragmentos = len(tree.get("fragmentos", [])) if isinstance(tree.get("fragmentos"), list) else 0
        unitary_ramos = 0
        exception_ramos = 0
        dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5+": 0}
        conclusion = "INVALIDA"
        report = build_report(
            input_path=paths["input"],
            total_ramos=total_ramos,
            total_microlinhas=total_microlinhas,
            total_fragmentos=total_fragmentos,
            unitary_ramos=unitary_ramos,
            exception_ramos=exception_ramos,
            dist=dist,
            checks=checks,
            conclusion=conclusion,
        )
        write_text(paths["report"], report)
        print(
            build_terminal_output(
                total_ramos=total_ramos,
                total_microlinhas=total_microlinhas,
                total_fragmentos=total_fragmentos,
                unitary_ramos=unitary_ramos,
                exception_ramos=exception_ramos,
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
        fragment_map,
        microlinha_map,
        ramo_map,
        excecao_ids_validas,
    ) = collect_tree_maps(tree)

    total_ramos = len(ramos)
    total_microlinhas = len(microlinhas)
    total_fragmentos = len(fragmentos)
    unitary_ramos = sum(
        1 for ramo in ramos
        if isinstance(ramo.get("microlinha_ids"), list) and len(ramo.get("microlinha_ids")) == 1
    )
    exception_ramos = count_ramos_with_exceptions(ramos)
    dist = size_distribution(ramos)

    checks.append(validate_ramo_minimum_fields(ramos))
    checks.append(validate_ramo_ids(ramos))
    checks.append(validate_ramo_tipo_no(ramos))
    checks.append(validate_ramo_auxiliary_arrays(ramos))
    checks.append(validate_ramo_required_nonempty_fields(ramos))

    check_mic_integrity, _ = validate_microlinha_integrity_and_uniqueness(ramos, microlinha_map)
    checks.append(check_mic_integrity)

    checks.append(validate_ramo_microlinha_consistency(ramos, microlinha_map, fragment_map))
    checks.append(validate_fragment_ramo_consistency(ramos, microlinha_map, fragment_map, ramo_map))
    checks.append(validate_unitary_ramos(ramos))
    checks.append(validate_ramo_exceptions(ramos, microlinha_map, excecao_ids_validas))
    checks.append(validate_global_metrics(tree, total_ramos))
    checks.append(validate_passo_ids_alvo(ramos))

    conclusion = determine_quality_conclusion(
        checks=checks,
        total_ramos=total_ramos,
        unitary_ramos=unitary_ramos,
        exception_ramos=exception_ramos,
    )

    report = build_report(
        input_path=paths["input"],
        total_ramos=total_ramos,
        total_microlinhas=total_microlinhas,
        total_fragmentos=total_fragmentos,
        unitary_ramos=unitary_ramos,
        exception_ramos=exception_ramos,
        dist=dist,
        checks=checks,
        conclusion=conclusion,
    )
    write_text(paths["report"], report)

    print(
        build_terminal_output(
            total_ramos=total_ramos,
            total_microlinhas=total_microlinhas,
            total_fragmentos=total_fragmentos,
            unitary_ramos=unitary_ramos,
            exception_ramos=exception_ramos,
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