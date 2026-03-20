# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


INPUT_FILENAME = "arvore_do_pensamento_v1.json"
REPORT_FILENAME = "relatorio_validacao_microlinhas_v1.txt"


class ValidationRuntimeError(RuntimeError):
    """Erro fatal de execução do validador."""


@dataclass
class ValidationResult:
    name: str
    status: str  # PASS | WARNING | FAIL
    details: List[str]


class ValidationCollector:
    """Acumulador de resultados por grupo de validação."""

    def __init__(self) -> None:
        self.results: List[ValidationResult] = []

    def add(self, name: str, status: str, details: Optional[List[str]] = None) -> None:
        status = status.upper().strip()
        if status not in {"PASS", "WARNING", "FAIL"}:
            raise ValueError(f"Estado de validação inválido: {status}")
        self.results.append(
            ValidationResult(name=name, status=status, details=list(details or []))
        )

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def pass_count(self) -> int:
        return sum(1 for result in self.results if result.status == "PASS")

    @property
    def warning_count(self) -> int:
        return sum(1 for result in self.results if result.status == "WARNING")

    @property
    def fail_count(self) -> int:
        return sum(1 for result in self.results if result.status == "FAIL")

    def final_verdict(self) -> str:
        if self.fail_count > 0:
            return "INVALIDA"
        if self.warning_count > 0:
            return "VALIDA COM AVISOS"
        return "VALIDA"


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise ValidationRuntimeError(f"Ficheiro não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationRuntimeError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise ValidationRuntimeError(f"Não foi possível ler {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as exc:
        raise ValidationRuntimeError(f"Não foi possível escrever o relatório {path}: {exc}") from exc


def require_dict(value: Any, context: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationRuntimeError(
            f"Tipo inválido em {context}: esperado object/dict, obtido {type(value).__name__}."
        )
    return value


def require_list(value: Any, context: str) -> List[Any]:
    if not isinstance(value, list):
        raise ValidationRuntimeError(
            f"Tipo inválido em {context}: esperado array/list, obtido {type(value).__name__}."
        )
    return value


def get_top_path() -> Dict[str, Path]:
    script_dir = Path(__file__).resolve().parent
    arvore_root = script_dir.parent
    return {
        "script_dir": script_dir,
        "arvore_root": arvore_root,
        "input": arvore_root / "01_dados" / INPUT_FILENAME,
        "report": arvore_root / "01_dados" / REPORT_FILENAME,
    }


def get_fragment_map(tree: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    details: List[str] = []
    fragment_map: Dict[str, Dict[str, Any]] = {}

    fragmentos = tree.get("fragmentos")
    if not isinstance(fragmentos, list):
        details.append("O bloco 'fragmentos' não existe ou não é array/list.")
        return fragment_map, details

    for idx, fragmento in enumerate(fragmentos, start=1):
        if not isinstance(fragmento, dict):
            details.append(f"fragmentos[{idx}] tem tipo inválido: esperado object/dict.")
            continue
        fragment_id = fragmento.get("id")
        if not isinstance(fragment_id, str) or not fragment_id.strip():
            details.append(f"fragmentos[{idx}] não tem 'id' string válido.")
            continue
        if fragment_id in fragment_map:
            details.append(f"ID de fragmento duplicado: '{fragment_id}'.")
            continue
        fragment_map[fragment_id] = fragmento

    return fragment_map, details


def get_exception_map(tree: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    details: List[str] = []
    exception_map: Dict[str, Dict[str, Any]] = {}

    excecoes = tree.get("excecoes")
    if not isinstance(excecoes, list):
        details.append("O bloco 'excecoes' não existe ou não é array/list.")
        return exception_map, details

    for idx, excecao in enumerate(excecoes, start=1):
        if not isinstance(excecao, dict):
            details.append(f"excecoes[{idx}] tem tipo inválido: esperado object/dict.")
            continue
        exc_id = excecao.get("id")
        if not isinstance(exc_id, str) or not exc_id.strip():
            details.append(f"excecoes[{idx}] não tem 'id' string válido.")
            continue
        if exc_id in exception_map:
            details.append(f"ID de exceção duplicado: '{exc_id}'.")
            continue
        exception_map[exc_id] = excecao

    return exception_map, details


def get_microlinhas(tree: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    details: List[str] = []
    microlinhas_raw = tree.get("microlinhas")

    if "microlinhas" not in tree:
        details.append("Falta o bloco 'microlinhas'.")
        return [], details

    if not isinstance(microlinhas_raw, list):
        details.append(
            f"O bloco 'microlinhas' tem tipo inválido: esperado array/list, obtido {type(microlinhas_raw).__name__}."
        )
        return [], details

    microlinhas: List[Dict[str, Any]] = []
    for idx, item in enumerate(microlinhas_raw, start=1):
        if not isinstance(item, dict):
            details.append(f"microlinhas[{idx}] tem tipo inválido: esperado object/dict.")
            continue
        microlinhas.append(item)

    return microlinhas, details


def compute_counts(tree: Dict[str, Any]) -> Dict[str, int]:
    microlinhas = tree.get("microlinhas", [])
    fragmentos = tree.get("fragmentos", [])
    excecoes = tree.get("excecoes", [])

    microlinhas_count = len(microlinhas) if isinstance(microlinhas, list) else 0
    fragmentos_count = len(fragmentos) if isinstance(fragmentos, list) else 0
    excecoes_count = len(excecoes) if isinstance(excecoes, list) else 0

    unitarias = 0
    com_excecoes = 0
    if isinstance(microlinhas, list):
        for microlinha in microlinhas:
            if not isinstance(microlinha, dict):
                continue
            fragmento_ids = microlinha.get("fragmento_ids", [])
            if isinstance(fragmento_ids, list) and len(fragmento_ids) == 1:
                unitarias += 1
            estado_excecao = microlinha.get("estado_excecao")
            excecao_ids = microlinha.get("excecao_ids", [])
            if (
                isinstance(estado_excecao, str)
                and estado_excecao.startswith("ativa")
            ) or (isinstance(excecao_ids, list) and len(excecao_ids) > 0):
                com_excecoes += 1

    return {
        "total_microlinhas": microlinhas_count,
        "total_fragmentos": fragmentos_count,
        "total_excecoes": excecoes_count,
        "unitarias": unitarias,
        "com_excecoes": com_excecoes,
    }


def validate_1_existencia_e_tipo(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    if "microlinhas" not in tree:
        details.append("Falta o bloco 'microlinhas'.")
        collector.add("1. Existência e tipo do bloco", "FAIL", details)
        return

    if not isinstance(tree["microlinhas"], list):
        details.append(
            f"O bloco 'microlinhas' tem tipo inválido: esperado array/list, obtido {type(tree['microlinhas']).__name__}."
        )

    collector.add("1. Existência e tipo do bloco", "PASS" if not details else "FAIL", details)


def validate_2_contagem(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    counts = compute_counts(tree)

    if not isinstance(tree.get("fragmentos"), list):
        details.append("O bloco 'fragmentos' não existe ou não é array/list.")
    if not isinstance(tree.get("microlinhas"), list):
        details.append("O bloco 'microlinhas' não existe ou não é array/list.")
    if not isinstance(tree.get("excecoes"), list):
        details.append("O bloco 'excecoes' não existe ou não é array/list.")

    details.append(f"Número total de microlinhas: {counts['total_microlinhas']}")
    details.append(f"Número total de fragmentos: {counts['total_fragmentos']}")
    details.append(f"Número de microlinhas unitárias: {counts['unitarias']}")
    details.append(f"Número de microlinhas com exceções: {counts['com_excecoes']}")

    collector.add("2. Contagem", "PASS" if len(details) == 4 else "FAIL", details)


def validate_3_campos_minimos(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    required_fields = [
        "id",
        "tipo_no",
        "titulo",
        "descricao_funcional",
        "criterio_de_agregacao",
        "fragmento_ids",
        "relacao_ids_internas",
        "percurso_ids_sugeridos",
        "argumento_ids_sugeridos",
        "convergencia_ids",
        "ordem_no_ramo",
        "prioridade_de_consolidacao",
        "estado_validacao",
        "estado_excecao",
        "excecao_ids",
        "observacoes",
    ]

    for idx, microlinha in enumerate(microlinhas, start=1):
        context = f"microlinhas[{idx}]"
        for field in required_fields:
            if field not in microlinha:
                details.append(f"Falta a chave obrigatória '{context}.{field}'.")

    collector.add("3. Campos mínimos de cada microlinha", "PASS" if not details else "FAIL", details)


def validate_4_criterio_de_agregacao(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    required_fields = [
        "base_dominante",
        "regra_curta",
        "problema_filosofico_dominante",
        "direcao_movimento_dominante",
        "tipo_de_utilidade_dominante",
    ]

    for idx, microlinha in enumerate(microlinhas, start=1):
        context = f"microlinhas[{idx}].criterio_de_agregacao"
        criterio = microlinha.get("criterio_de_agregacao")
        if not isinstance(criterio, dict):
            details.append(f"{context} tem tipo inválido: esperado object/dict.")
            continue
        for field in required_fields:
            if field not in criterio:
                details.append(f"Falta a chave obrigatória '{context}.{field}'.")

    collector.add("4. Conteúdo mínimo de criterio_de_agregacao", "PASS" if not details else "FAIL", details)


def validate_5_ids(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    pattern = re.compile(r"^ML_\d{4}$")
    seen: Set[str] = set()

    for idx, microlinha in enumerate(microlinhas, start=1):
        context = f"microlinhas[{idx}]"
        microlinha_id = microlinha.get("id")
        if not isinstance(microlinha_id, str) or not microlinha_id.strip():
            details.append(f"{context}.id tem de ser string não vazia.")
            continue
        if not pattern.fullmatch(microlinha_id):
            details.append(f"{context}.id não respeita o formato 'ML_0001': '{microlinha_id}'.")
        if microlinha_id in seen:
            details.append(f"ID de microlinha duplicado: '{microlinha_id}'.")
        seen.add(microlinha_id)

    collector.add("5. Convenção de IDs", "PASS" if not details else "FAIL", details)


def validate_6_tipo_no(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    for idx, microlinha in enumerate(microlinhas, start=1):
        context = f"microlinhas[{idx}]"
        if microlinha.get("tipo_no") != "microlinha":
            details.append(
                f"{context}.tipo_no tem valor inválido: esperado 'microlinha', obtido {microlinha.get('tipo_no')!r}."
            )

    collector.add("6. Tipo de nó", "PASS" if not details else "FAIL", details)


def validate_7_integridade_fragmento_ids(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    fragment_map, fragment_details = get_fragment_map(tree)
    details.extend(fragment_details)

    memberships: Dict[str, List[str]] = {}

    for idx, microlinha in enumerate(microlinhas, start=1):
        context = f"microlinhas[{idx}]"
        microlinha_id = microlinha.get("id", f"<sem-id-{idx}>")
        fragmento_ids = microlinha.get("fragmento_ids")

        if not isinstance(fragmento_ids, list):
            details.append(f"{context}.fragmento_ids tem tipo inválido: esperado array/list.")
            continue

        if len(fragmento_ids) == 0:
            details.append(f"{context}.fragmento_ids não pode estar vazio.")
            continue

        seen_inside: Set[str] = set()
        for item_idx, fragment_id in enumerate(fragmento_ids, start=1):
            item_context = f"{context}.fragmento_ids[{item_idx}]"
            if not isinstance(fragment_id, str) or not fragment_id.strip():
                details.append(f"{item_context} tem valor inválido: esperado string não vazia.")
                continue
            if fragment_id in seen_inside:
                details.append(f"{context} contém fragmento duplicado internamente: '{fragment_id}'.")
            seen_inside.add(fragment_id)

            if fragment_id not in fragment_map:
                details.append(f"{context} refere fragmento inexistente: '{fragment_id}'.")
                continue

            memberships.setdefault(fragment_id, []).append(str(microlinha_id))

    for fragment_id, microlinha_ids in sorted(memberships.items()):
        if len(microlinha_ids) > 1:
            details.append(
                f"O fragmento '{fragment_id}' aparece em mais de uma microlinha: {', '.join(microlinha_ids)}."
            )

    collector.add("7. Integridade de fragmento_ids", "PASS" if not details else "FAIL", details)


def validate_8_consistencia_ligacoes(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    fragment_map, fragment_details = get_fragment_map(tree)
    details.extend(fragment_details)

    microlinha_map: Dict[str, Dict[str, Any]] = {}
    microlinha_fragment_sets: Dict[str, Set[str]] = {}

    for idx, microlinha in enumerate(microlinhas, start=1):
        microlinha_id = microlinha.get("id")
        if isinstance(microlinha_id, str):
            microlinha_map[microlinha_id] = microlinha
            fragmento_ids = microlinha.get("fragmento_ids", [])
            if isinstance(fragmento_ids, list):
                microlinha_fragment_sets[microlinha_id] = {
                    fid for fid in fragmento_ids if isinstance(fid, str)
                }

    # Direção microlinha -> fragmento
    for idx, microlinha in enumerate(microlinhas, start=1):
        microlinha_id = microlinha.get("id", f"<sem-id-{idx}>")
        fragmento_ids = microlinha.get("fragmento_ids", [])
        if not isinstance(fragmento_ids, list):
            continue

        for fragment_id in fragmento_ids:
            if not isinstance(fragment_id, str):
                continue
            fragment = fragment_map.get(fragment_id)
            if fragment is None:
                continue
            ligacoes = fragment.get("ligacoes_arvore")
            if not isinstance(ligacoes, dict):
                details.append(
                    f"O fragmento '{fragment_id}' não tem 'ligacoes_arvore' válido para refletir a microlinha '{microlinha_id}'."
                )
                continue
            microlinha_ids = ligacoes.get("microlinha_ids")
            if not isinstance(microlinha_ids, list):
                details.append(
                    f"O fragmento '{fragment_id}' tem 'ligacoes_arvore.microlinha_ids' inválido."
                )
                continue
            if microlinha_id not in microlinha_ids:
                details.append(
                    f"O fragmento '{fragment_id}' não referencia a microlinha '{microlinha_id}' em 'ligacoes_arvore.microlinha_ids'."
                )

    # Direção fragmento -> microlinha
    for fragment_id, fragment in sorted(fragment_map.items()):
        ligacoes = fragment.get("ligacoes_arvore")
        if not isinstance(ligacoes, dict):
            details.append(f"O fragmento '{fragment_id}' não tem 'ligacoes_arvore' válido.")
            continue
        microlinha_ids = ligacoes.get("microlinha_ids")
        if not isinstance(microlinha_ids, list):
            details.append(
                f"O fragmento '{fragment_id}' não tem 'ligacoes_arvore.microlinha_ids' em formato array/list."
            )
            continue
        if len(microlinha_ids) > 1:
            details.append(
                f"O fragmento '{fragment_id}' referencia mais de uma microlinha em 'ligacoes_arvore.microlinha_ids'."
            )

        for microlinha_id in microlinha_ids:
            if not isinstance(microlinha_id, str):
                details.append(
                    f"O fragmento '{fragment_id}' contém microlinha_id inválido em 'ligacoes_arvore.microlinha_ids'."
                )
                continue
            if microlinha_id not in microlinha_map:
                details.append(
                    f"O fragmento '{fragment_id}' refere microlinha inexistente em 'ligacoes_arvore.microlinha_ids': '{microlinha_id}'."
                )
                continue
            if fragment_id not in microlinha_fragment_sets.get(microlinha_id, set()):
                details.append(
                    f"O fragmento '{fragment_id}' refere a microlinha '{microlinha_id}', mas não consta em 'microlinhas[].fragmento_ids'."
                )

    collector.add(
        "8. Consistência com fragmentos[].ligacoes_arvore.microlinha_ids",
        "PASS" if not details else "FAIL",
        details,
    )


def validate_9_unitarias(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    warnings: List[str] = []
    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    unitarias = 0
    for idx, microlinha in enumerate(microlinhas, start=1):
        context = f"microlinhas[{idx}]"
        fragmento_ids = microlinha.get("fragmento_ids")
        if not isinstance(fragmento_ids, list):
            continue
        if len(fragmento_ids) == 1:
            unitarias += 1
            estado_validacao = microlinha.get("estado_validacao")
            if estado_validacao == "valido":
                details.append(
                    f"{context} é unitária, mas está marcada como 'valido'; deveria ter estado com aviso."
                )

    if details:
        collector.add("9. Microlinhas unitárias", "FAIL", details)
        return

    if unitarias > 0:
        warnings.append(
            f"Existem {unitarias} microlinha(s) unitária(s); a estrutura é aceitável na v1, mas exige consolidação posterior."
        )
        collector.add("9. Microlinhas unitárias", "WARNING", warnings)
    else:
        collector.add("9. Microlinhas unitárias", "PASS", ["Não existem microlinhas unitárias."])


def validate_10_excecoes(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    warnings: List[str] = []

    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    fragment_map, fragment_details = get_fragment_map(tree)
    details.extend(fragment_details)

    exception_map, exception_details = get_exception_map(tree)
    details.extend(exception_details)

    consistent_microlinhas_with_exceptions = 0

    for idx, microlinha in enumerate(microlinhas, start=1):
        context = f"microlinhas[{idx}]"
        fragmento_ids = microlinha.get("fragmento_ids")
        microlinha_estado_excecao = microlinha.get("estado_excecao")
        microlinha_excecao_ids = microlinha.get("excecao_ids")

        if not isinstance(fragmento_ids, list):
            continue
        if not isinstance(microlinha_excecao_ids, list):
            details.append(f"{context}.excecao_ids tem tipo inválido: esperado array/list.")
            continue

        active_fragment_exception_ids: Set[str] = set()
        for fragment_id in fragmento_ids:
            if not isinstance(fragment_id, str):
                continue
            fragment = fragment_map.get(fragment_id)
            if fragment is None:
                continue

            estado_excecao = fragment.get("estado_excecao")
            exc_ids = fragment.get("excecao_ids", [])
            if (
                isinstance(estado_excecao, str)
                and estado_excecao.startswith("ativa")
                and isinstance(exc_ids, list)
            ):
                for exc_id in exc_ids:
                    if isinstance(exc_id, str):
                        active_fragment_exception_ids.add(exc_id)

        # Toda exceção referida pela microlinha deve existir.
        for exc_id in microlinha_excecao_ids:
            if not isinstance(exc_id, str):
                details.append(f"{context}.excecao_ids contém valor inválido não-string.")
                continue
            if exc_id not in exception_map:
                details.append(f"{context} refere exceção inexistente: '{exc_id}'.")

        if active_fragment_exception_ids:
            if not (isinstance(microlinha_estado_excecao, str) and microlinha_estado_excecao.startswith("ativa")):
                details.append(
                    f"{context} contém fragmento(s) com exceção ativa, mas 'estado_excecao' não reflete isso."
                )
            missing = sorted(active_fragment_exception_ids.difference(set(x for x in microlinha_excecao_ids if isinstance(x, str))))
            if missing:
                details.append(
                    f"{context} não reflete todas as exceções ativas dos seus fragmentos: faltam {', '.join(missing)}."
                )
            if not missing and isinstance(microlinha_estado_excecao, str) and microlinha_estado_excecao.startswith("ativa"):
                consistent_microlinhas_with_exceptions += 1
        else:
            if (isinstance(microlinha_estado_excecao, str) and microlinha_estado_excecao.startswith("ativa")) or len(microlinha_excecao_ids) > 0:
                warnings.append(
                    f"{context} marca exceção ao nível da microlinha, mas não há fragmentos com exceção ativa."
                )

    if details:
        collector.add("10. Microlinhas com exceções", "FAIL", details)
        return

    if consistent_microlinhas_with_exceptions > 0 or warnings:
        warning_lines = []
        if consistent_microlinhas_with_exceptions > 0:
            warning_lines.append(
                f"Existem {consistent_microlinhas_with_exceptions} microlinha(s) com exceções ativas coerentes com os seus fragmentos."
            )
        warning_lines.extend(warnings)
        collector.add("10. Microlinhas com exceções", "WARNING", warning_lines)
    else:
        collector.add("10. Microlinhas com exceções", "PASS", ["Não existem microlinhas com exceções ativas."])


def validate_11_arrays_auxiliares(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    required_array_fields = [
        "relacao_ids_internas",
        "percurso_ids_sugeridos",
        "argumento_ids_sugeridos",
        "convergencia_ids",
        "excecao_ids",
        "observacoes",
    ]

    for idx, microlinha in enumerate(microlinhas, start=1):
        context = f"microlinhas[{idx}]"
        for field in required_array_fields:
            if field not in microlinha:
                details.append(f"Falta a chave obrigatória '{context}.{field}'.")
                continue
            if not isinstance(microlinha[field], list):
                details.append(f"{context}.{field} tem tipo inválido: esperado array/list.")

    collector.add("11. Arrays auxiliares", "PASS" if not details else "FAIL", details)


def validate_12_estados(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    for idx, microlinha in enumerate(microlinhas, start=1):
        context = f"microlinhas[{idx}]"

        if "estado_validacao" not in microlinha:
            details.append(f"Falta a chave obrigatória '{context}.estado_validacao'.")
        else:
            value = microlinha["estado_validacao"]
            if not isinstance(value, str) or not value.strip():
                details.append(f"{context}.estado_validacao tem valor vazio ou inválido.")

        if "estado_excecao" not in microlinha:
            details.append(f"Falta a chave obrigatória '{context}.estado_excecao'.")
        else:
            value = microlinha["estado_excecao"]
            if not isinstance(value, str) or not value.strip():
                details.append(f"{context}.estado_excecao tem valor vazio ou inválido.")

        if "prioridade_de_consolidacao" not in microlinha:
            details.append(f"Falta a chave obrigatória '{context}.prioridade_de_consolidacao'.")
        else:
            value = microlinha["prioridade_de_consolidacao"]
            if not isinstance(value, str) or not value.strip():
                details.append(f"{context}.prioridade_de_consolidacao tem valor vazio ou inválido.")

    collector.add("12. Estado de validação", "PASS" if not details else "FAIL", details)


def validate_13_metricas_globais(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []

    validacao = tree.get("validacao")
    if not isinstance(validacao, dict):
        details.append("O bloco 'validacao' não existe ou não é object/dict.")
        collector.add("13. Métricas globais", "FAIL", details)
        return

    metricas = validacao.get("metricas")
    if not isinstance(metricas, dict):
        details.append("O bloco 'validacao.metricas' não existe ou não é object/dict.")
        collector.add("13. Métricas globais", " é object/dict.")
        collector.add("13. Métricas globais", "FAIL", details)
        return

    microlinhas = tree.get("microlinhas")
    if not isinstance(microlinhas, list):
        details.append("O bloco 'microlinhas' não existe ou não é array/list.")
        collector.add("13. Métricas globais", "FAIL", details)
        return

    total_real = len(microlinhas)
    total_metrica = metricas.get("total_microlinhas")
    if total_metrica != total_real:
        details.append(
            f"validacao.metricas.total_microlinhas = {total_metrica}, mas o número real de microlinhas é {total_real}."
        )

    collector.add("13. Métricas globais", "PASS" if not details else "FAIL", details)


def validate_14_distribuicao_tamanhos(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    warnings: List[str] = []

    microlinhas, load_details = get_microlinhas(tree)
    details.extend(load_details)

    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    above_five = 0

    for idx, microlinha in enumerate(microlinhas, start=1):
        fragmento_ids = microlinha.get("fragmento_ids", [])
        if not isinstance(fragmento_ids, list):
            continue
        size = len(fragmento_ids)
        if size in dist:
            dist[size] += 1
        elif size >= 5:
            above_five += 1

    details.append(f"Microlinhas com 1 fragmento: {dist[1]}")
    details.append(f"Microlinhas com 2 fragmentos: {dist[2]}")
    details.append(f"Microlinhas com 3 fragmentos: {dist[3]}")
    details.append(f"Microlinhas com 4 fragmentos: {dist[4]}")
    details.append(f"Microlinhas com 5 ou mais fragmentos: {dist[5] + above_five}")

    # Tratamento mais rigoroso: >5 gera aviso, não falha estrutural.
    oversized = 0
    for microlinha in microlinhas:
        fragmento_ids = microlinha.get("fragmento_ids", [])
        if isinstance(fragmento_ids, list) and len(fragmento_ids) > 5:
            oversized += 1

    if details and load_details:
        collector.add("14. Distribuição de tamanhos", "FAIL", details)
        return

    if oversized > 0:
        warnings.extend(details)
        warnings.append(
            f"Existem {oversized} microlinha(s) com mais de 5 fragmentos; isso excede o tamanho-alvo da v1."
        )
        collector.add("14. Distribuição de tamanhos", "WARNING", warnings)
    else:
        collector.add("14. Distribuição de tamanhos", "PASS", details)


def build_terminal_summary(
    collector: ValidationCollector,
    tree: Dict[str, Any],
    verdict: str,
    input_path: Path,
    report_path: Path,
) -> str:
    counts = compute_counts(tree)
    lines: List[str] = []
    lines.append(f"Ficheiro validado: {input_path}")
    lines.append("")
    for result in collector.results:
        lines.append(f"[{result.status}] {result.name}")
        for detail in result.details:
            lines.append(f"  - {detail}")
    lines.append("")
    lines.append(f"Número total de microlinhas: {counts['total_microlinhas']}")
    lines.append(f"Número de microlinhas unitárias: {counts['unitarias']}")
    lines.append(f"Número de microlinhas com exceções: {counts['com_excecoes']}")
    lines.append(f"PASS: {collector.pass_count}")
    lines.append(f"WARNING: {collector.warning_count}")
    lines.append(f"FAIL: {collector.fail_count}")
    lines.append(f"Conclusão final: {verdict}")
    lines.append(f"Relatório escrito em: {report_path}")
    return "\n".join(lines)


def build_report_text(
    collector: ValidationCollector,
    tree: Dict[str, Any],
    verdict: str,
    input_path: Path,
) -> str:
    counts = compute_counts(tree)
    now_utc = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    lines: List[str] = []
    lines.append("RELATÓRIO DE VALIDAÇÃO — MICROLINHAS V1")
    lines.append("=" * 60)
    lines.append(f"Data/hora UTC: {now_utc}")
    lines.append(f"Ficheiro validado: {input_path}")
    lines.append("")

    lines.append("Verificações executadas")
    lines.append("-" * 60)
    for result in collector.results:
        lines.append(f"{result.status} — {result.name}")
        if result.details:
            for detail in result.details:
                lines.append(f"  - {detail}")
        else:
            lines.append("  - Sem inconformidades.")
        lines.append("")

    lines.append("Resumo de contagem")
    lines.append("-" * 60)
    lines.append(f"Número total de microlinhas: {counts['total_microlinhas']}")
    lines.append(f"Número total de fragmentos: {counts['total_fragmentos']}")
    lines.append(f"Número de microlinhas unitárias: {counts['unitarias']}")
    lines.append(f"Número de microlinhas com exceções: {counts['com_excecoes']}")
    lines.append(f"Número total de exceções: {counts['total_excecoes']}")
    lines.append("")

    lines.append("Conclusão final")
    lines.append("-" * 60)
    lines.append(verdict)
    lines.append("")
    if verdict == "VALIDA":
        lines.append("A camada de microlinhas está estruturalmente coerente e sem avisos relevantes.")
    elif verdict == "VALIDA COM AVISOS":
        lines.append("A camada de microlinhas é estruturalmente utilizável, mas contém avisos relevantes.")
    else:
        lines.append("A camada de microlinhas contém falhas estruturais ou de consistência e deve ser corrigida.")
    lines.append("")

    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    _ = argv  # Sem argumentos nesta v1.
    paths = get_top_path()
    input_path = paths["input"]
    report_path = paths["report"]

    if not input_path.exists():
        raise ValidationRuntimeError(f"O ficheiro da árvore não existe: {input_path}")

    tree = load_json(input_path)
    if not isinstance(tree, dict):
        raise ValidationRuntimeError(f"O conteúdo de {input_path} não é um objeto JSON no topo.")

    collector = ValidationCollector()

    validate_1_existencia_e_tipo(tree, collector)
    validate_2_contagem(tree, collector)
    validate_3_campos_minimos(tree, collector)
    validate_4_criterio_de_agregacao(tree, collector)
    validate_5_ids(tree, collector)
    validate_6_tipo_no(tree, collector)
    validate_7_integridade_fragmento_ids(tree, collector)
    validate_8_consistencia_ligacoes(tree, collector)
    validate_9_unitarias(tree, collector)
    validate_10_excecoes(tree, collector)
    validate_11_arrays_auxiliares(tree, collector)
    validate_12_estados(tree, collector)
    validate_13_metricas_globais(tree, collector)
    validate_14_distribuicao_tamanhos(tree, collector)

    verdict = collector.final_verdict()

    terminal_summary = build_terminal_summary(
        collector=collector,
        tree=tree,
        verdict=verdict,
        input_path=input_path,
        report_path=report_path,
    )
    report_text = build_report_text(
        collector=collector,
        tree=tree,
        verdict=verdict,
        input_path=input_path,
    )

    write_text(report_path, report_text)
    print(terminal_summary)
    return 0 if verdict in {"VALIDA", "VALIDA COM AVISOS"} else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationRuntimeError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)