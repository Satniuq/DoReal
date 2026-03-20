# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


INPUT_FILENAME = "arvore_do_pensamento_v1.json"
REPORT_FILENAME = "relatorio_validacao_arvore_v1.txt"


class ValidationRuntimeError(RuntimeError):
    """Erro fatal de execução do validador."""


class ValidationCollector:
    """
    Acumulador determinístico de resultados de validação.
    Cada grupo de validação gera:
    - nome
    - PASS / FAIL
    - detalhes
    """

    def __init__(self) -> None:
        self.results: List[Dict[str, Any]] = []

    def add(self, name: str, passed: bool, details: Optional[List[str]] = None) -> None:
        self.results.append(
            {
                "name": name,
                "passed": passed,
                "details": details[:] if details else [],
            }
        )

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def failed(self) -> int:
        return sum(1 for result in self.results if not result["passed"])

    @property
    def passed(self) -> int:
        return self.total - self.failed

    def final_verdict(self, tree: Optional[Dict[str, Any]]) -> str:
        if self.failed > 0:
            return "INVALIDA"

        if tree is None:
            return "INVALIDA"

        excecoes = tree.get("excecoes", [])
        if isinstance(excecoes, list) and len(excecoes) > 0:
            return "VALIDA COM EXCEÇÕES"

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


def is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def is_list(value: Any) -> bool:
    return isinstance(value, list)


def require_top_key(
    mapping: Dict[str, Any],
    key: str,
    details: List[str],
    expected_type: Optional[type] = None,
) -> Optional[Any]:
    if key not in mapping:
        details.append(f"Falta a chave obrigatória '{key}'.")
        return None

    value = mapping[key]
    if expected_type is not None and not isinstance(value, expected_type):
        details.append(
            f"A chave '{key}' tem tipo inválido: esperado {expected_type.__name__}, obtido {type(value).__name__}."
        )
        return None

    return value


def validate_top_level_structure(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    required_top_keys = [
        "schema_meta",
        "fontes",
        "manifesto_cobertura",
        "fragmentos",
        "relacoes",
        "microlinhas",
        "ramos",
        "percursos",
        "argumentos",
        "convergencias",
        "excecoes",
        "validacao",
    ]

    details: List[str] = []
    for key in required_top_keys:
        if key not in tree:
            details.append(f"Falta o bloco de topo obrigatório '{key}'.")

    collector.add("1. Estrutura de topo obrigatória", passed=(len(details) == 0), details=details)


def validate_top_level_types(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []

    expected_objects = ["schema_meta", "fontes", "manifesto_cobertura", "validacao"]
    for key in expected_objects:
        if key in tree and not isinstance(tree[key], dict):
            details.append(
                f"O bloco '{key}' tem tipo inválido: esperado object/dict, obtido {type(tree[key]).__name__}."
            )

    expected_arrays = [
        "fragmentos",
        "relacoes",
        "microlinhas",
        "ramos",
        "percursos",
        "argumentos",
        "convergencias",
        "excecoes",
    ]
    for key in expected_arrays:
        if key in tree and not isinstance(tree[key], list):
            details.append(
                f"O bloco '{key}' tem tipo inválido: esperado array/list, obtido {type(tree[key]).__name__}."
            )

    collector.add("2. Tipos estruturais básicos", passed=(len(details) == 0), details=details)


def validate_schema_meta(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    schema_meta = tree.get("schema_meta")

    if not isinstance(schema_meta, dict):
        details.append("O bloco 'schema_meta' não é um objeto válido.")
        collector.add("3. Campos mínimos em schema_meta", passed=False, details=details)
        return

    required_keys = [
        "schema_name",
        "schema_version",
        "objeto",
        "generated_at_utc",
        "lote_geracao_id",
        "politica_excecoes_version",
    ]
    for key in required_keys:
        if key not in schema_meta:
            details.append(f"Falta a chave obrigatória 'schema_meta.{key}'.")

    collector.add("3. Campos mínimos em schema_meta", passed=(len(details) == 0), details=details)


def validate_fontes(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    fontes = tree.get("fontes")

    if not isinstance(fontes, dict):
        details.append("O bloco 'fontes' não é um objeto válido.")
        collector.add("4. Campos mínimos em fontes", passed=False, details=details)
        return

    required_subblocks = [
        "fragmentos_resegmentados",
        "cadencia_extraida",
        "cadencia_schema",
        "tratamento_filosofico_fragmentos",
        "impacto_fragmentos_no_mapa",
        "indice_por_percurso",
        "argumentos_unificados",
        "mapa_dedutivo_canonico_final",
    ]

    for subblock in required_subblocks:
        if subblock not in fontes:
            details.append(f"Falta o subbloco obrigatório 'fontes.{subblock}'.")
            continue

        value = fontes[subblock]
        if not isinstance(value, dict):
            details.append(
                f"O subbloco 'fontes.{subblock}' tem tipo inválido: esperado object/dict, obtido {type(value).__name__}."
            )
            continue

        for field in ("ficheiro", "obrigatorio", "presente"):
            if field not in value:
                details.append(f"Falta a chave obrigatória 'fontes.{subblock}.{field}'.")

    collector.add("4. Campos mínimos em fontes", passed=(len(details) == 0), details=details)


def validate_manifesto_cobertura(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    manifesto = tree.get("manifesto_cobertura")

    if not isinstance(manifesto, dict):
        details.append("O bloco 'manifesto_cobertura' não é um objeto válido.")
        collector.add("5. Campos mínimos em manifesto_cobertura", passed=False, details=details)
        return

    required_fields = [
        "arranque_permitido",
        "total_fragmentos_base",
        "total_fragmentos_com_cadencia",
        "total_fragmentos_com_tratamento",
        "total_fragmentos_com_impacto",
        "fragmentos_sem_tratamento_ids",
        "fragmentos_com_validacao_base_problemática_ids",
    ]
    for field in required_fields:
        if field not in manifesto:
            details.append(f"Falta a chave obrigatória 'manifesto_cobertura.{field}'.")

    collector.add("5. Campos mínimos em manifesto_cobertura", passed=(len(details) == 0), details=details)


def validate_fragmentos(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    fragmentos = tree.get("fragmentos")
    excecoes = tree.get("excecoes")

    if not isinstance(fragmentos, list):
        details.append("O bloco 'fragmentos' não é um array válido.")
        collector.add("6. Validação dos fragmentos", passed=False, details=details)
        return

    if not isinstance(excecoes, list):
        details.append("O bloco 'excecoes' não é um array válido.")
        collector.add("6. Validação dos fragmentos", passed=False, details=details)
        return

    excecoes_por_id: Dict[str, Dict[str, Any]] = {}
    for i, excecao in enumerate(excecoes, start=1):
        if isinstance(excecao, dict):
            exc_id = excecao.get("id")
            if isinstance(exc_id, str):
                excecoes_por_id[exc_id] = excecao

    required_fragment_fields = [
        "id",
        "tipo_no",
        "origem_id",
        "ordem_no_ficheiro",
        "base_empirica",
        "cadencia",
        "tratamento_filosofico",
        "impacto_mapa",
        "ligacoes_arvore",
        "estado_validacao",
        "estado_excecao",
        "excecao_ids",
    ]

    for idx, fragmento in enumerate(fragmentos, start=1):
        context = f"fragmentos[{idx}]"

        if not isinstance(fragmento, dict):
            details.append(f"{context} tem tipo inválido: esperado object/dict.")
            continue

        for field in required_fragment_fields:
            if field not in fragmento:
                details.append(f"Falta a chave obrigatória '{context}.{field}'.")

        fragment_id = fragmento.get("id", f"<sem-id-{idx}>")

        base_empirica = fragmento.get("base_empirica")
        if not isinstance(base_empirica, dict):
            details.append(f"{context}.base_empirica tem tipo inválido ou está ausente.")
        else:
            for field in ("ficheiro_origem", "texto_fragmento", "segmentacao", "funcao_textual_dominante"):
                if field not in base_empirica:
                    details.append(f"Falta a chave obrigatória '{context}.base_empirica.{field}'.")
            segmentacao = base_empirica.get("segmentacao")
            if not isinstance(segmentacao, dict):
                details.append(f"{context}.base_empirica.segmentacao tem tipo inválido.")
            else:
                if "tipo_unidade" not in segmentacao:
                    details.append(f"Falta a chave obrigatória '{context}.base_empirica.segmentacao.tipo_unidade'.")

        cadencia = fragmento.get("cadencia")
        if not isinstance(cadencia, dict):
            details.append(f"{context}.cadencia tem tipo inválido ou está ausente.")
        else:
            for field in (
                "funcao_cadencia_principal",
                "direcao_movimento",
                "centralidade",
                "estatuto_no_percurso",
                "zona_provavel_percurso",
                "confianca_cadencia",
                "necessita_revisao_humana",
            ):
                if field not in cadencia:
                    details.append(f"Falta a chave obrigatória '{context}.cadencia.{field}'.")

        tratamento = fragmento.get("tratamento_filosofico")
        excecao_ids = fragmento.get("excecao_ids")
        if not isinstance(excecao_ids, list):
            details.append(f"{context}.excecao_ids tem tipo inválido: esperado array/list.")
            excecao_ids = []

        if tratamento is None:
            if len(excecao_ids) == 0:
                details.append(
                    f"{context} tem 'tratamento_filosofico = null' mas 'excecao_ids' está vazio."
                )
            else:
                found_matching_exception = False
                for exc_id in excecao_ids:
                    exc_obj = excecoes_por_id.get(exc_id)
                    if (
                        isinstance(exc_obj, dict)
                        and isinstance(exc_obj.get("entidade_ref"), dict)
                        and exc_obj.get("entidade_ref", {}).get("tipo_no") == "fragmento"
                        and exc_obj.get("entidade_ref", {}).get("id") == fragment_id
                    ):
                        found_matching_exception = True
                        break
                if not found_matching_exception:
                    details.append(
                        f"{context} tem 'tratamento_filosofico = null' mas não existe exceção correspondente em 'excecoes'."
                    )
        elif isinstance(tratamento, dict):
            for field in (
                "descricao_funcional_curta",
                "problema_filosofico_central",
                "trabalho_no_sistema",
                "confianca_tratamento_filosofico",
            ):
                if field not in tratamento:
                    details.append(f"Falta a chave obrigatória '{context}.tratamento_filosofico.{field}'.")
        else:
            details.append(
                f"{context}.tratamento_filosofico tem tipo inválido: esperado object/dict ou null, obtido {type(tratamento).__name__}."
            )

        impacto = fragmento.get("impacto_mapa")
        if not isinstance(impacto, dict):
            details.append(f"{context}.impacto_mapa tem tipo inválido ou está ausente.")
        else:
            for field in (
                "tipo_de_utilidade_principal",
                "proposicoes_do_mapa_tocadas",
                "efeito_principal_no_mapa",
                "decisao_final",
            ):
                if field not in impacto:
                    details.append(f"Falta a chave obrigatória '{context}.impacto_mapa.{field}'.")

            proposicoes = impacto.get("proposicoes_do_mapa_tocadas")
            if not isinstance(proposicoes, list):
                details.append(f"{context}.impacto_mapa.proposicoes_do_mapa_tocadas tem tipo inválido.")
            else:
                for pidx, prop in enumerate(proposicoes, start=1):
                    prop_context = f"{context}.impacto_mapa.proposicoes_do_mapa_tocadas[{pidx}]"
                    if not isinstance(prop, dict):
                        details.append(f"{prop_context} tem tipo inválido: esperado object/dict.")
                        continue
                    for field in ("proposicao_id", "grau_de_relevancia", "tipo_de_relacao"):
                        if field not in prop:
                            details.append(f"Falta a chave obrigatória '{prop_context}.{field}'.")

            decisao_final = impacto.get("decisao_final")
            if not isinstance(decisao_final, dict):
                details.append(f"{context}.impacto_mapa.decisao_final tem tipo inválido.")
            else:
                for field in (
                    "acao_recomendada_sobre_o_mapa",
                    "prioridade_editorial",
                    "confianca_da_analise",
                ):
                    if field not in decisao_final:
                        details.append(f"Falta a chave obrigatória '{context}.impacto_mapa.decisao_final.{field}'.")

        ligacoes = fragmento.get("ligacoes_arvore")
        if not isinstance(ligacoes, dict):
            details.append(f"{context}.ligacoes_arvore tem tipo inválido ou está ausente.")
        else:
            for field in (
                "microlinha_ids",
                "ramo_ids",
                "percurso_ids",
                "argumento_ids",
                "relacao_ids",
                "convergencia_ids",
            ):
                if field not in ligacoes:
                    details.append(f"Falta a chave obrigatória '{context}.ligacoes_arvore.{field}'.")
                elif not isinstance(ligacoes[field], list):
                    details.append(
                        f"{context}.ligacoes_arvore.{field} tem tipo inválido: esperado array/list."
                    )

    collector.add("6. Validação dos fragmentos", passed=(len(details) == 0), details=details)


def validate_unique_ids(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []

    collections = [
        ("fragmentos", "id"),
        ("relacoes", "id"),
        ("microlinhas", "id"),
        ("ramos", "id"),
        ("percursos", "id"),
        ("argumentos", "id"),
        ("convergencias", "id"),
        ("excecoes", "id"),
    ]

    for collection_name, id_field in collections:
        collection = tree.get(collection_name)
        if not isinstance(collection, list):
            details.append(f"O bloco '{collection_name}' não é um array válido para verificação de unicidade.")
            continue

        seen: Set[str] = set()
        for idx, item in enumerate(collection, start=1):
            if not isinstance(item, dict):
                details.append(
                    f"{collection_name}[{idx}] tem tipo inválido: esperado object/dict para verificação de unicidade."
                )
                continue
            if id_field not in item:
                details.append(f"Falta a chave '{id_field}' em {collection_name}[{idx}].")
                continue
            item_id = item[id_field]
            if not isinstance(item_id, str):
                details.append(f"{collection_name}[{idx}].{id_field} tem tipo inválido: esperado string.")
                continue
            if item_id in seen:
                details.append(f"ID duplicado em '{collection_name}': '{item_id}'.")
            seen.add(item_id)

    collector.add("7. Unicidade", passed=(len(details) == 0), details=details)


def validate_fragmentos_excecoes_consistency(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []

    fragmentos = tree.get("fragmentos")
    excecoes = tree.get("excecoes")

    if not isinstance(fragmentos, list) or not isinstance(excecoes, list):
        details.append("Os blocos 'fragmentos' e/ou 'excecoes' não estão em formato válido.")
        collector.add("8. Consistência entre fragmentos e excecoes", passed=False, details=details)
        return

    fragment_ids: Set[str] = set()
    for idx, fragmento in enumerate(fragmentos, start=1):
        if isinstance(fragmento, dict):
            frag_id = fragmento.get("id")
            if isinstance(frag_id, str):
                fragment_ids.add(frag_id)

    excecoes_por_id: Dict[str, Dict[str, Any]] = {}
    for idx, excecao in enumerate(excecoes, start=1):
        if not isinstance(excecao, dict):
            details.append(f"excecoes[{idx}] tem tipo inválido: esperado object/dict.")
            continue
        exc_id = excecao.get("id")
        if isinstance(exc_id, str):
            excecoes_por_id[exc_id] = excecao

        entidade_ref = excecao.get("entidade_ref")
        if entidade_ref is not None:
            if not isinstance(entidade_ref, dict):
                details.append(f"excecoes[{idx}].entidade_ref tem tipo inválido: esperado object/dict.")
            else:
                if entidade_ref.get("tipo_no") == "fragmento":
                    exc_frag_id = entidade_ref.get("id")
                    if not isinstance(exc_frag_id, str) or exc_frag_id not in fragment_ids:
                        details.append(
                            f"excecoes[{idx}] refere fragmento inexistente: '{exc_frag_id}'."
                        )

    for idx, fragmento in enumerate(fragmentos, start=1):
        if not isinstance(fragmento, dict):
            continue

        fragment_id = fragmento.get("id", f"<sem-id-{idx}>")
        excecao_ids = fragmento.get("excecao_ids", [])
        tratamento = fragmento.get("tratamento_filosofico")

        if not isinstance(excecao_ids, list):
            details.append(f"fragmentos[{idx}].excecao_ids tem tipo inválido: esperado array/list.")
            continue

        for exc_id in excecao_ids:
            if exc_id not in excecoes_por_id:
                details.append(
                    f"fragmentos[{idx}] refere exceção inexistente em 'excecao_ids': '{exc_id}'."
                )

        if tratamento is None:
            active_match = False
            for exc_id in excecao_ids:
                exc_obj = excecoes_por_id.get(exc_id)
                if not isinstance(exc_obj, dict):
                    continue
                entidade_ref = exc_obj.get("entidade_ref")
                if (
                    isinstance(entidade_ref, dict)
                    and entidade_ref.get("tipo_no") == "fragmento"
                    and entidade_ref.get("id") == fragment_id
                ):
                    estado_excecao = exc_obj.get("estado_excecao")
                    if isinstance(estado_excecao, str) and estado_excecao.startswith("ativa"):
                        active_match = True
                        break
            if not active_match:
                details.append(
                    f"fragmentos[{idx}] tem tratamento_filosofico = null sem exceção ativa correspondente."
                )

    collector.add("8. Consistência entre fragmentos e excecoes", passed=(len(details) == 0), details=details)


def validate_manifesto_vs_content(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []

    manifesto = tree.get("manifesto_cobertura")
    fragmentos = tree.get("fragmentos")

    if not isinstance(manifesto, dict) or not isinstance(fragmentos, list):
        details.append("Os blocos 'manifesto_cobertura' e/ou 'fragmentos' não estão em formato válido.")
        collector.add("9. Consistência entre manifesto_cobertura e conteúdo real", passed=False, details=details)
        return

    fragmentos_com_tratamento = []
    fragmentos_sem_tratamento = []

    for idx, fragmento in enumerate(fragmentos, start=1):
        if not isinstance(fragmento, dict):
            details.append(f"fragmentos[{idx}] tem tipo inválido para cálculo de manifesto.")
            continue
        frag_id = fragmento.get("id")
        if not isinstance(frag_id, str):
            details.append(f"fragmentos[{idx}] não tem 'id' válido para cálculo de manifesto.")
            continue
        if fragmento.get("tratamento_filosofico") is None:
            fragmentos_sem_tratamento.append(frag_id)
        else:
            fragmentos_com_tratamento.append(frag_id)

    total_fragmentos_base = manifesto.get("total_fragmentos_base")
    total_fragmentos_com_tratamento = manifesto.get("total_fragmentos_com_tratamento")
    fragmentos_sem_tratamento_ids = manifesto.get("fragmentos_sem_tratamento_ids")

    if total_fragmentos_base != len(fragmentos):
        details.append(
            f"manifesto_cobertura.total_fragmentos_base = {total_fragmentos_base}, mas len(fragmentos) = {len(fragmentos)}."
        )

    if total_fragmentos_com_tratamento != len(fragmentos_com_tratamento):
        details.append(
            "manifesto_cobertura.total_fragmentos_com_tratamento = "
            f"{total_fragmentos_com_tratamento}, mas o número real é {len(fragmentos_com_tratamento)}."
        )

    if not isinstance(fragmentos_sem_tratamento_ids, list):
        details.append("manifesto_cobertura.fragmentos_sem_tratamento_ids tem tipo inválido: esperado array/list.")
    else:
        if sorted(fragmentos_sem_tratamento_ids) != sorted(fragmentos_sem_tratamento):
            details.append(
                "manifesto_cobertura.fragmentos_sem_tratamento_ids não coincide exatamente com os IDs reais sem tratamento."
            )

    collector.add(
        "9. Consistência entre manifesto_cobertura e conteúdo real",
        passed=(len(details) == 0),
        details=details,
    )


def validate_metricas_vs_content(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []

    validacao = tree.get("validacao")
    if not isinstance(validacao, dict):
        details.append("O bloco 'validacao' não é um objeto válido.")
        collector.add("10. Consistência entre validacao.metricas e conteúdo real", passed=False, details=details)
        return

    metricas = validacao.get("metricas")
    if not isinstance(metricas, dict):
        details.append("O bloco 'validacao.metricas' não é um objeto válido.")
        collector.add("10. Consistência entre validacao.metricas e conteúdo real", passed=False, details=details)
        return

    expected_lengths = {
        "total_fragmentos": len(tree.get("fragmentos", [])) if isinstance(tree.get("fragmentos"), list) else None,
        "total_relacoes": len(tree.get("relacoes", [])) if isinstance(tree.get("relacoes"), list) else None,
        "total_microlinhas": len(tree.get("microlinhas", [])) if isinstance(tree.get("microlinhas"), list) else None,
        "total_ramos": len(tree.get("ramos", [])) if isinstance(tree.get("ramos"), list) else None,
        "total_percursos": len(tree.get("percursos", [])) if isinstance(tree.get("percursos"), list) else None,
        "total_argumentos": len(tree.get("argumentos", [])) if isinstance(tree.get("argumentos"), list) else None,
        "total_convergencias": len(tree.get("convergencias", [])) if isinstance(tree.get("convergencias"), list) else None,
        "total_excecoes_ativas": len(tree.get("excecoes", [])) if isinstance(tree.get("excecoes"), list) else None,
    }

    for metric_key, expected_value in expected_lengths.items():
        actual_value = metricas.get(metric_key)
        if actual_value != expected_value:
            details.append(
                f"validacao.metricas.{metric_key} = {actual_value}, mas o valor real é {expected_value}."
            )

    collector.add(
        "10. Consistência entre validacao.metricas e conteúdo real",
        passed=(len(details) == 0),
        details=details,
    )


def validate_validacao_block(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    validacao = tree.get("validacao")

    if not isinstance(validacao, dict):
        details.append("O bloco 'validacao' não é um objeto válido.")
        collector.add("11. Campos mínimos em validacao", passed=False, details=details)
        return

    required_keys = [
        "estado_validacao_global",
        "pronto_para_artefacto_operacional",
        "metricas",
        "excecao_ids_ativas",
    ]
    for key in required_keys:
        if key not in validacao:
            details.append(f"Falta a chave obrigatória 'validacao.{key}'.")

    collector.add("11. Campos mínimos em validacao", passed=(len(details) == 0), details=details)


def validate_allowed_empty_arrays(tree: Dict[str, Any], collector: ValidationCollector) -> None:
    details: List[str] = []
    allowed_empty = [
        "relacoes",
        "microlinhas",
        "ramos",
        "percursos",
        "argumentos",
        "convergencias",
    ]

    for key in allowed_empty:
        value = tree.get(key)
        if not isinstance(value, list):
            details.append(f"O bloco '{key}' deveria ser um array/list, mesmo quando vazio.")
        # Se for lista, vazia ou não, está tudo bem nesta v1.

    collector.add("12. Validação de arrays vazios permitidos", passed=(len(details) == 0), details=details)


def build_terminal_summary(
    collector: ValidationCollector,
    tree: Optional[Dict[str, Any]],
    verdict: str,
    input_path: Path,
    report_path: Path,
) -> str:
    lines: List[str] = []
    lines.append(f"Ficheiro validado: {input_path}")
    lines.append("")

    for result in collector.results:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(f"[{status}] {result['name']}")
        for detail in result["details"]:
            lines.append(f"  - {detail}")

    lines.append("")
    if isinstance(tree, dict):
        fragmentos = tree.get("fragmentos", [])
        excecoes = tree.get("excecoes", [])
        if isinstance(fragmentos, list):
            lines.append(f"Fragmentos: {len(fragmentos)}")
        if isinstance(excecoes, list):
            lines.append(f"Exceções: {len(excecoes)}")

    lines.append(f"Resultados PASS: {collector.passed}")
    lines.append(f"Resultados FAIL: {collector.failed}")
    lines.append(f"Conclusão final: {verdict}")
    lines.append(f"Relatório escrito em: {report_path}")
    return "\n".join(lines)


def build_report_text(
    collector: ValidationCollector,
    tree: Optional[Dict[str, Any]],
    verdict: str,
    input_path: Path,
) -> str:
    now_utc = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    lines: List[str] = []
    lines.append("RELATÓRIO DE VALIDAÇÃO — ÁRVORE DO PENSAMENTO V1")
    lines.append("=" * 60)
    lines.append(f"Data/hora UTC: {now_utc}")
    lines.append(f"Ficheiro validado: {input_path}")
    lines.append("")

    lines.append("Verificações executadas")
    lines.append("-" * 60)
    for result in collector.results:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(f"{status} — {result['name']}")
        if result["details"]:
            for detail in result["details"]:
                lines.append(f"  - {detail}")
        else:
            lines.append("  - Sem inconformidades.")
        lines.append("")

    lines.append("Resumo")
    lines.append("-" * 60)
    if isinstance(tree, dict):
        fragmentos = tree.get("fragmentos", [])
        relacoes = tree.get("relacoes", [])
        microlinhas = tree.get("microlinhas", [])
        ramos = tree.get("ramos", [])
        percursos = tree.get("percursos", [])
        argumentos = tree.get("argumentos", [])
        convergencias = tree.get("convergencias", [])
        excecoes = tree.get("excecoes", [])

        if isinstance(fragmentos, list):
            lines.append(f"Número de fragmentos: {len(fragmentos)}")
        if isinstance(relacoes, list):
            lines.append(f"Número de relações: {len(relacoes)}")
        if isinstance(microlinhas, list):
            lines.append(f"Número de microlinhas: {len(microlinhas)}")
        if isinstance(ramos, list):
            lines.append(f"Número de ramos: {len(ramos)}")
        if isinstance(percursos, list):
            lines.append(f"Número de percursos: {len(percursos)}")
        if isinstance(argumentos, list):
            lines.append(f"Número de argumentos: {len(argumentos)}")
        if isinstance(convergencias, list):
            lines.append(f"Número de convergências: {len(convergencias)}")
        if isinstance(excecoes, list):
            lines.append(f"Número de exceções: {len(excecoes)}")

    lines.append(f"Resultados PASS: {collector.passed}")
    lines.append(f"Resultados FAIL: {collector.failed}")
    lines.append("")
    lines.append("Conclusão final")
    lines.append("-" * 60)
    lines.append(verdict)
    lines.append("")

    if verdict == "VALIDA COM EXCEÇÕES":
        lines.append("Nota:")
        lines.append(
            "A instância cumpre as exigências estruturais mínimas da v1, mantendo exceções toleradas consistentes com a política definida."
        )
    elif verdict == "INVALIDA":
        lines.append("Nota:")
        lines.append(
            "Existem inconformidades estruturais ou de consistência que impedem a validação da instância."
        )
    else:
        lines.append("Nota:")
        lines.append("A instância cumpre integralmente as exigências estruturais mínimas da v1.")

    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    _ = argv  # Sem argumentos nesta v1.

    script_dir = Path(__file__).resolve().parent
    arvore_root = script_dir.parent
    input_path = arvore_root / "01_dados" / INPUT_FILENAME
    report_path = arvore_root / "01_dados" / REPORT_FILENAME

    if not input_path.exists():
        raise ValidationRuntimeError(
            f"O ficheiro da árvore não existe: {input_path}"
        )

    tree_data = load_json(input_path)
    if not isinstance(tree_data, dict):
        raise ValidationRuntimeError(
            f"O conteúdo de {input_path} não é um objeto JSON no topo."
        )

    collector = ValidationCollector()

    validate_top_level_structure(tree_data, collector)
    validate_top_level_types(tree_data, collector)
    validate_schema_meta(tree_data, collector)
    validate_fontes(tree_data, collector)
    validate_manifesto_cobertura(tree_data, collector)
    validate_fragmentos(tree_data, collector)
    validate_unique_ids(tree_data, collector)
    validate_fragmentos_excecoes_consistency(tree_data, collector)
    validate_manifesto_vs_content(tree_data, collector)
    validate_metricas_vs_content(tree_data, collector)
    validate_validacao_block(tree_data, collector)
    validate_allowed_empty_arrays(tree_data, collector)

    verdict = collector.final_verdict(tree_data)

    terminal_summary = build_terminal_summary(
        collector=collector,
        tree=tree_data,
        verdict=verdict,
        input_path=input_path,
        report_path=report_path,
    )
    report_text = build_report_text(
        collector=collector,
        tree=tree_data,
        verdict=verdict,
        input_path=input_path,
    )

    write_text(report_path, report_text)

    print(terminal_summary)
    return 0 if verdict in {"VALIDA", "VALIDA COM EXCEÇÕES"} else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationRuntimeError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)