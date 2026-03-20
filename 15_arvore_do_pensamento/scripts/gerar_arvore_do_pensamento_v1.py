# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

SCHEMA_NAME = "schema_arvore_do_pensamento"
SCHEMA_VERSION = "1.0.0"
OBJETO = "arvore_do_pensamento"
POLITICA_EXCECOES_VERSION = "PE-1.0.0"
OUTPUT_FILENAME = "arvore_do_pensamento_v1.json"


class ArvoreGeracaoError(RuntimeError):
    """Erro explícito de geração da árvore."""


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera a v1 inicial da árvore do pensamento."
    )
    parser.add_argument(
        "--modo",
        choices=("estrutura-vazia", "povoamento-minimo"),
        required=True,
        help="Modo de geração da árvore.",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="Limite opcional de fragmentos a carregar no modo povoamento-minimo.",
    )
    args = parser.parse_args(argv)

    if args.limite is not None and args.limite <= 0:
        raise SystemExit("ERRO: --limite tem de ser um inteiro positivo.")

    return args


def build_paths(script_dir: Path) -> Dict[str, Path]:
    """
    Regra de caminhos:
    1. partir da pasta do próprio script;
    2. subir para 15_arvore_do_pensamento/;
    3. subir para a raiz do projeto;
    4. resolver a partir daí os ficheiros-fonte e o output.
    """
    arvore_root = script_dir.parent
    project_root = arvore_root.parent

    paths = {
        "script_dir": script_dir,
        "arvore_root": arvore_root,
        "project_root": project_root,
        "output": arvore_root / "01_dados" / OUTPUT_FILENAME,
        "fragmentos_resegmentados": project_root / "13_Meta_Indice" / "cadência" / "01_segmentar_fragmentos" / "fragmentos_resegmentados.json",
        "cadencia_extraida": project_root / "13_Meta_Indice" / "cadência" / "02_extrator_cadência" / "cadencia_extraida.json",
        "cadencia_schema": project_root / "13_Meta_Indice" / "cadência" / "02_extrator_cadência" / "cadencia_schema.json",
        "tratamento_filosofico_fragmentos": project_root / "13_Meta_Indice" / "cadência" / "04_extrator_q_faz_no_sistema" / "tratamento_filosofico_fragmentos.json",
        "impacto_fragmentos_no_mapa": project_root / "14_mapa_dedutivo" / "impacto_fragmentos_no_mapa.json",
        "indice_por_percurso": project_root / "13_Meta_Indice" / "indice" / "indice_por_percurso.json",
        "argumentos_unificados": project_root / "13_Meta_Indice" / "indice" / "argumentos" / "argumentos_unificados.json",
        "mapa_dedutivo_canonico_final": project_root / "14_mapa_dedutivo" / "02_fecho_canonico_mapa" / "outputs" / "mapa_dedutivo_canonico_final.json",
        # Fonte opcional apenas para preencher o manifesto com IDs problemáticos.
        "relatorio_validacao_fragmentos": project_root / "13_Meta_Indice" / "cadência" / "01_segmentar_fragmentos" / "relatorio_validacao_fragmentos.json",
    }
    return paths


def assert_essential_files_exist(paths: Dict[str, Path]) -> None:
    essential_keys = [
        "fragmentos_resegmentados",
        "cadencia_extraida",
        "cadencia_schema",
        "tratamento_filosofico_fragmentos",
        "impacto_fragmentos_no_mapa",
        "indice_por_percurso",
        "argumentos_unificados",
        "mapa_dedutivo_canonico_final",
    ]
    missing = [(key, paths[key]) for key in essential_keys if not paths[key].exists()]
    if missing:
        lines = ["Faltam ficheiros-fonte essenciais:"]
        for key, path in missing:
            lines.append(f"- {key}: {path}")
        raise ArvoreGeracaoError("\n".join(lines))


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise ArvoreGeracaoError(f"JSON inválido em {path}: {exc}") from exc
    except OSError as exc:
        raise ArvoreGeracaoError(f"Não foi possível ler {path}: {exc}") from exc


def maybe_load_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    return load_json(path)


def require_type(value: Any, expected_type: type | Tuple[type, ...], context: str) -> Any:
    if not isinstance(value, expected_type):
        expected_name = (
            ", ".join(t.__name__ for t in expected_type)
            if isinstance(expected_type, tuple)
            else expected_type.__name__
        )
        raise ArvoreGeracaoError(
            f"Estrutura inesperada em {context}: esperado {expected_name}, obtido {type(value).__name__}."
        )
    return value


def require_key(mapping: Dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ArvoreGeracaoError(f"Falta a chave obrigatória '{key}' em {context}.")
    return mapping[key]


def build_unique_index(
    records: Sequence[Dict[str, Any]],
    key_name: str,
    source_name: str,
) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for i, record in enumerate(records, start=1):
        require_type(record, dict, f"{source_name}[{i}]")
        key_value = require_key(record, key_name, f"{source_name}[{i}]")
        if not isinstance(key_value, str) or not key_value.strip():
            raise ArvoreGeracaoError(
                f"ID inválido em {source_name}[{i}] para a chave '{key_name}'."
            )
        if key_value in index:
            raise ArvoreGeracaoError(f"ID duplicado '{key_value}' em {source_name}.")
        index[key_value] = record
    return index


def sort_fragment_records(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def sort_key(record: Dict[str, Any]) -> Tuple[int, str]:
        fragment_id = str(record.get("fragment_id", "?"))
        origem = require_type(
            require_key(record, "origem", f"fragmento {fragment_id}"),
            dict,
            f"fragmento {fragment_id}.origem",
        )
        ordem = origem.get("ordem_no_ficheiro")
        if not isinstance(ordem, int):
            raise ArvoreGeracaoError(
                f"'ordem_no_ficheiro' inválido no fragmento {fragment_id}."
            )
        return ordem, fragment_id

    return sorted(records, key=sort_key)


def normalise_mode_token(mode: str) -> str:
    return mode.replace("-", "_").upper()


def compute_source_hash(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p).lower()):
        digest.update(str(path).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def deterministic_generated_at_utc(paths: Iterable[Path]) -> str:
    mtimes = [p.stat().st_mtime for p in paths]
    latest = max(mtimes) if mtimes else 0.0
    return datetime.fromtimestamp(latest, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def extract_problematic_fragment_ids(report_data: Optional[Any]) -> List[str]:
    if report_data is None:
        return []

    require_type(report_data, dict, "relatorio_validacao_fragmentos")
    errors = report_data.get("erros", [])
    if not isinstance(errors, list):
        raise ArvoreGeracaoError(
            "A chave 'erros' do relatório de validação de fragmentos tem de ser uma lista."
        )

    ids: List[str] = []
    for i, error in enumerate(errors, start=1):
        require_type(error, dict, f"relatorio_validacao_fragmentos.erros[{i}]")
        fragment_id = error.get("fragment_id")
        if isinstance(fragment_id, str) and fragment_id not in ids:
            ids.append(fragment_id)
    return ids


def infer_exception_priority(impacto: Dict[str, Any]) -> Tuple[str, str, str, str]:
    """
    Heurística conservadora:
    - prioriza quando há utilidade justificativa/mediacional com efeito relevante,
      ação editorial positiva, ou proposições tocadas com relevância material;
    - caso contrário, trata como omissão tolerada.
    """
    tipo_utilidade = impacto.get("tipo_de_utilidade_principal")
    efeito = impacto.get("efeito_principal_no_mapa")
    decisao_final = require_type(
        require_key(impacto, "decisao_final", "impacto_mapa.decisao_final"),
        dict,
        "impacto_mapa.decisao_final",
    )
    acao = decisao_final.get("acao_recomendada_sobre_o_mapa")
    prioridade_editorial = decisao_final.get("prioridade_editorial")
    proposicoes = impacto.get("proposicoes_do_mapa_tocadas", [])
    require_type(proposicoes, list, "impacto_mapa.proposicoes_do_mapa_tocadas")

    relacoes_materiais = {
        "apoia_justificacao",
        "faz_ponte_entre",
        "toca_diretamente",
        "bloqueia_objecao",
        "corrige_formulacao",
        "introduz_distincao_nova",
    }
    relevancias_materiais = {"alto", "medio"}

    ha_relacao_material = False
    for i, prop in enumerate(proposicoes, start=1):
        require_type(prop, dict, f"impacto_mapa.proposicoes_do_mapa_tocadas[{i}]")
        if (
            prop.get("grau_de_relevancia") in relevancias_materiais
            and prop.get("tipo_de_relacao") in relacoes_materiais
        ):
            ha_relacao_material = True
            break

    material = any(
        [
            tipo_utilidade in {"justificativa", "mediacional"},
            efeito in {"explicita", "medeia"},
            acao in {"densificar", "reformular"},
            prioridade_editorial in {"alta", "media"} and acao not in {None, "sem_acao"},
            ha_relacao_material,
        ]
    )

    if material:
        return (
            "ativa_prioritaria",
            "pendencia_prioritaria",
            "resolver_antes_artefacto_estavel",
            "Lacuna de tratamento filosófico com relevância dedutiva material inferida a partir do impacto no mapa.",
        )

    return (
        "ativa_tolerada",
        "omissao_tolerada",
        "tolerar_no_arranque",
        "Lacuna de tratamento filosófico tratada como omissão tolerada no arranque, por ausência de sinal dedutivo material forte no impacto no mapa.",
    )


def build_fontes_block(paths: Dict[str, Path]) -> Dict[str, Dict[str, Any]]:
    keys = [
        "fragmentos_resegmentados",
        "cadencia_extraida",
        "cadencia_schema",
        "tratamento_filosofico_fragmentos",
        "impacto_fragmentos_no_mapa",
        "indice_por_percurso",
        "argumentos_unificados",
        "mapa_dedutivo_canonico_final",
    ]
    return {
        key: {
            "ficheiro": paths[key].name,
            "obrigatorio": True,
            "presente": paths[key].exists(),
        }
        for key in keys
    }


def build_empty_tree(
    generated_at_utc: str,
    lote_geracao_id: str,
    fontes: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "schema_meta": {
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "objeto": OBJETO,
            "generated_at_utc": generated_at_utc,
            "lote_geracao_id": lote_geracao_id,
            "politica_excecoes_version": POLITICA_EXCECOES_VERSION,
        },
        "fontes": fontes,
        "manifesto_cobertura": {
            "arranque_permitido": True,
            "total_fragmentos_base": 0,
            "total_fragmentos_com_cadencia": 0,
            "total_fragmentos_com_tratamento": 0,
            "total_fragmentos_com_impacto": 0,
            "fragmentos_sem_tratamento_ids": [],
            "fragmentos_com_validacao_base_problemática_ids": [],
        },
        "fragmentos": [],
        "relacoes": [],
        "microlinhas": [],
        "ramos": [],
        "percursos": [],
        "argumentos": [],
        "convergencias": [],
        "excecoes": [],
        "validacao": {
            "estado_validacao_global": "nao_validado",
            "pronto_para_artefacto_operacional": False,
            "metricas": {
                "total_fragmentos": 0,
                "total_relacoes": 0,
                "total_microlinhas": 0,
                "total_ramos": 0,
                "total_percursos": 0,
                "total_argumentos": 0,
                "total_convergencias": 0,
                "total_excecoes_ativas": 0,
            },
            "excecao_ids_ativas": [],
        },
    }


def require_minimal_fragment_fields(fragment: Dict[str, Any], fragment_id: str) -> None:
    origem = require_type(
        require_key(fragment, "origem", f"fragmento {fragment_id}"),
        dict,
        f"fragmento {fragment_id}.origem",
    )
    require_key(origem, "origem_id", f"fragmento {fragment_id}.origem")
    require_key(origem, "ordem_no_ficheiro", f"fragmento {fragment_id}.origem")
    require_key(origem, "ficheiro", f"fragmento {fragment_id}.origem")

    require_key(fragment, "texto_fragmento", f"fragmento {fragment_id}")
    segmentacao = require_type(
        require_key(fragment, "segmentacao", f"fragmento {fragment_id}"),
        dict,
        f"fragmento {fragment_id}.segmentacao",
    )
    require_key(segmentacao, "tipo_unidade", f"fragmento {fragment_id}.segmentacao")
    require_key(fragment, "funcao_textual_dominante", f"fragmento {fragment_id}")


def build_fragment_node(
    fragmento_base: Dict[str, Any],
    cadencia_record: Dict[str, Any],
    impacto_record: Dict[str, Any],
    tratamento_record: Optional[Dict[str, Any]],
    problematic_ids: set[str],
    exception_sequence: int,
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    fragment_id = str(require_key(fragmento_base, "fragment_id", "fragmento_base"))
    require_minimal_fragment_fields(fragmento_base, fragment_id)

    origem = require_type(
        fragmento_base["origem"],
        dict,
        f"fragmento {fragment_id}.origem",
    )
    segmentacao = require_type(
        fragmento_base["segmentacao"],
        dict,
        f"fragmento {fragment_id}.segmentacao",
    )

    cadencia = require_type(
        require_key(cadencia_record, "cadencia", f"cadencia[{fragment_id}]"),
        dict,
        f"cadencia[{fragment_id}].cadencia",
    )
    impacto = require_type(
        require_key(impacto_record, "impacto_no_mapa_fragmento", f"impacto[{fragment_id}]"),
        dict,
        f"impacto[{fragment_id}].impacto_no_mapa_fragmento",
    )

    cadencia_min = {
        "funcao_cadencia_principal": require_key(cadencia, "funcao_cadencia_principal", f"cadencia[{fragment_id}]"),
        "direcao_movimento": require_key(cadencia, "direcao_movimento", f"cadencia[{fragment_id}]"),
        "centralidade": require_key(cadencia, "centralidade", f"cadencia[{fragment_id}]"),
        "estatuto_no_percurso": require_key(cadencia, "estatuto_no_percurso", f"cadencia[{fragment_id}]"),
        "zona_provavel_percurso": require_key(cadencia, "zona_provavel_percurso", f"cadencia[{fragment_id}]"),
        "confianca_cadencia": require_key(cadencia, "confianca_cadencia", f"cadencia[{fragment_id}]"),
        "necessita_revisao_humana": require_key(cadencia, "necessita_revisao_humana", f"cadencia[{fragment_id}]"),
    }

    proposicoes_origem = require_type(
        require_key(impacto, "proposicoes_do_mapa_tocadas", f"impacto[{fragment_id}]"),
        list,
        f"impacto[{fragment_id}].proposicoes_do_mapa_tocadas",
    )
    proposicoes_min: List[Dict[str, Any]] = []
    for i, prop in enumerate(proposicoes_origem, start=1):
        require_type(prop, dict, f"impacto[{fragment_id}].proposicoes_do_mapa_tocadas[{i}]")
        proposicoes_min.append(
            {
                "proposicao_id": require_key(prop, "proposicao_id", f"impacto[{fragment_id}].proposicoes_do_mapa_tocadas[{i}]"),
                "grau_de_relevancia": require_key(prop, "grau_de_relevancia", f"impacto[{fragment_id}].proposicoes_do_mapa_tocadas[{i}]"),
                "tipo_de_relacao": require_key(prop, "tipo_de_relacao", f"impacto[{fragment_id}].proposicoes_do_mapa_tocadas[{i}]"),
            }
        )

    decisao_final = require_type(
        require_key(impacto, "decisao_final", f"impacto[{fragment_id}]"),
        dict,
        f"impacto[{fragment_id}].decisao_final",
    )
    impacto_min = {
        "tipo_de_utilidade_principal": require_key(impacto, "tipo_de_utilidade_principal", f"impacto[{fragment_id}]"),
        "proposicoes_do_mapa_tocadas": proposicoes_min,
        "efeito_principal_no_mapa": require_key(impacto, "efeito_principal_no_mapa", f"impacto[{fragment_id}]"),
        "decisao_final": {
            "acao_recomendada_sobre_o_mapa": require_key(decisao_final, "acao_recomendada_sobre_o_mapa", f"impacto[{fragment_id}].decisao_final"),
            "prioridade_editorial": require_key(decisao_final, "prioridade_editorial", f"impacto[{fragment_id}].decisao_final"),
            "confianca_da_analise": require_key(decisao_final, "confianca_da_analise", f"impacto[{fragment_id}].decisao_final"),
        },
    }

    tratamento_min: Optional[Dict[str, Any]]
    exception_obj: Optional[Dict[str, Any]] = None
    state_validacao = "valido"
    state_excecao = "sem_excecao"
    excecao_ids: List[str] = []

    if tratamento_record is not None:
        tratamento = require_type(
            require_key(tratamento_record, "tratamento_filosofico_fragmento", f"tratamento[{fragment_id}]"),
            dict,
            f"tratamento[{fragment_id}].tratamento_filosofico_fragmento",
        )
        avaliacao_global = require_type(
            require_key(tratamento, "avaliacao_global", f"tratamento[{fragment_id}]"),
            dict,
            f"tratamento[{fragment_id}].avaliacao_global",
        )
        tratamento_min = {
            "descricao_funcional_curta": require_key(tratamento, "descricao_funcional_curta", f"tratamento[{fragment_id}]"),
            "problema_filosofico_central": require_key(tratamento, "problema_filosofico_central", f"tratamento[{fragment_id}]"),
            "trabalho_no_sistema": require_key(tratamento, "trabalho_no_sistema", f"tratamento[{fragment_id}]"),
            "confianca_tratamento_filosofico": require_key(avaliacao_global, "confianca_tratamento_filosofico", f"tratamento[{fragment_id}].avaliacao_global"),
        }
    else:
        tratamento_min = None
        state_validacao = "invalido_tolerado"
        state_excecao, tipo_excecao, politica_resolucao, descricao_base = infer_exception_priority(impacto)
        excecao_id = f"EXC_TRATAMENTO_{exception_sequence:04d}"
        excecao_ids = [excecao_id]
        severity = "alta" if state_excecao == "ativa_prioritaria" else "media"
        exception_obj = {
            "id": excecao_id,
            "entidade_ref": {
                "tipo_no": "fragmento",
                "id": fragment_id,
            },
            "camada_afetada": "tratamento_filosofico",
            "tipo_excecao": tipo_excecao,
            "severidade": severity,
            "bloqueante": False,
            "estado_excecao": state_excecao,
            "politica_resolucao": politica_resolucao,
            "descricao": descricao_base,
        }

    if fragment_id in problematic_ids and state_validacao == "valido":
        state_validacao = "valido_com_avisos"

    node = {
        "id": fragment_id,
        "tipo_no": "fragmento",
        "origem_id": require_key(origem, "origem_id", f"fragmento {fragment_id}.origem"),
        "ordem_no_ficheiro": require_key(origem, "ordem_no_ficheiro", f"fragmento {fragment_id}.origem"),
        "base_empirica": {
            "ficheiro_origem": require_key(origem, "ficheiro", f"fragmento {fragment_id}.origem"),
            "texto_fragmento": require_key(fragmento_base, "texto_fragmento", f"fragmento {fragment_id}"),
            "segmentacao": {
                "tipo_unidade": require_key(segmentacao, "tipo_unidade", f"fragmento {fragment_id}.segmentacao"),
            },
            "funcao_textual_dominante": require_key(fragmento_base, "funcao_textual_dominante", f"fragmento {fragment_id}"),
        },
        "cadencia": cadencia_min,
        "tratamento_filosofico": tratamento_min,
        "impacto_mapa": impacto_min,
        "ligacoes_arvore": {
            "microlinha_ids": [],
            "ramo_ids": [],
            "percurso_ids": [],
            "argumento_ids": [],
            "relacao_ids": [],
            "convergencia_ids": [],
        },
        "estado_validacao": state_validacao,
        "estado_excecao": state_excecao,
        "excecao_ids": excecao_ids,
    }

    return node, exception_obj


def build_populated_tree(
    args: argparse.Namespace,
    data: Dict[str, Any],
    paths: Dict[str, Path],
    generated_at_utc: str,
    lote_geracao_id: str,
) -> Dict[str, Any]:
    fragmentos_base = require_type(data["fragmentos_resegmentados"], list, "fragmentos_resegmentados.json")
    cadencia_records = require_type(data["cadencia_extraida"], list, "cadencia_extraida.json")
    _ = require_type(data["cadencia_schema"], dict, "cadencia_schema.json")
    tratamento_records = require_type(data["tratamento_filosofico_fragmentos"], list, "tratamento_filosofico_fragmentos.json")
    impacto_records = require_type(data["impacto_fragmentos_no_mapa"], list, "impacto_fragmentos_no_mapa.json")
    _ = require_type(data["indice_por_percurso"], dict, "indice_por_percurso.json")
    _ = require_type(data["argumentos_unificados"], list, "argumentos_unificados.json")
    _ = require_type(data["mapa_dedutivo_canonico_final"], dict, "mapa_dedutivo_canonico_final.json")

    problematic_ids = set(extract_problematic_fragment_ids(data.get("relatorio_validacao_fragmentos")))

    cadencia_index = build_unique_index(cadencia_records, "fragment_id", "cadencia_extraida.json")
    tratamento_index = build_unique_index(tratamento_records, "fragment_id", "tratamento_filosofico_fragmentos.json")
    impacto_index = build_unique_index(impacto_records, "fragment_id", "impacto_fragmentos_no_mapa.json")

    ordered_fragments = sort_fragment_records(fragmentos_base)
    if args.limite is not None:
        ordered_fragments = ordered_fragments[: args.limite]

    fragment_nodes: List[Dict[str, Any]] = []
    exceptions: List[Dict[str, Any]] = []

    exception_sequence = 1
    for base_fragment in ordered_fragments:
        fragment_id = str(require_key(base_fragment, "fragment_id", "fragmentos_resegmentados item"))

        if fragment_id not in cadencia_index:
            raise ArvoreGeracaoError(
                f"O fragmento {fragment_id} não tem correspondência em cadencia_extraida.json."
            )
        if fragment_id not in impacto_index:
            raise ArvoreGeracaoError(
                f"O fragmento {fragment_id} não tem correspondência em impacto_fragmentos_no_mapa.json."
            )

        tratamento_record = tratamento_index.get(fragment_id)
        node, exception_obj = build_fragment_node(
            fragmento_base=base_fragment,
            cadencia_record=cadencia_index[fragment_id],
            impacto_record=impacto_index[fragment_id],
            tratamento_record=tratamento_record,
            problematic_ids=problematic_ids,
            exception_sequence=exception_sequence,
        )
        fragment_nodes.append(node)
        if exception_obj is not None:
            exceptions.append(exception_obj)
            exception_sequence += 1

    fragmentos_sem_tratamento_ids = [
        node["id"] for node in fragment_nodes if node["tratamento_filosofico"] is None
    ]
    problematic_loaded_ids = [
        node["id"] for node in fragment_nodes if node["id"] in problematic_ids
    ]

    metricas = {
        "total_fragmentos": len(fragment_nodes),
        "total_relacoes": 0,
        "total_microlinhas": 0,
        "total_ramos": 0,
        "total_percursos": 0,
        "total_argumentos": 0,
        "total_convergencias": 0,
        "total_excecoes_ativas": len(exceptions),
    }

    fragment_states = {node["estado_validacao"] for node in fragment_nodes}
    if not fragment_nodes:
        estado_validacao_global = "nao_validado"
    elif "invalido_bloqueante" in fragment_states:
        estado_validacao_global = "invalido_bloqueante"
    elif "invalido_tolerado" in fragment_states:
        estado_validacao_global = "invalido_tolerado"
    elif "valido_com_avisos" in fragment_states:
        estado_validacao_global = "valido_com_avisos"
    else:
        estado_validacao_global = "valido"

    tree = {
        "schema_meta": {
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "objeto": OBJETO,
            "generated_at_utc": generated_at_utc,
            "lote_geracao_id": lote_geracao_id,
            "politica_excecoes_version": POLITICA_EXCECOES_VERSION,
        },
        "fontes": build_fontes_block(paths),
        "manifesto_cobertura": {
            "arranque_permitido": True,
            "total_fragmentos_base": len(fragment_nodes),
            "total_fragmentos_com_cadencia": len(fragment_nodes),
            "total_fragmentos_com_tratamento": sum(1 for node in fragment_nodes if node["tratamento_filosofico"] is not None),
            "total_fragmentos_com_impacto": len(fragment_nodes),
            "fragmentos_sem_tratamento_ids": fragmentos_sem_tratamento_ids,
            "fragmentos_com_validacao_base_problemática_ids": problematic_loaded_ids,
        },
        "fragmentos": fragment_nodes,
        "relacoes": [],
        "microlinhas": [],
        "ramos": [],
        "percursos": [],
        "argumentos": [],
        "convergencias": [],
        "excecoes": exceptions,
        "validacao": {
            "estado_validacao_global": estado_validacao_global,
            "pronto_para_artefacto_operacional": bool(fragment_nodes) and not exceptions,
            "metricas": metricas,
            "excecao_ids_ativas": [exc["id"] for exc in exceptions],
        },
    }
    return tree


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp_path.replace(path)
    except OSError as exc:
        raise ArvoreGeracaoError(f"Não foi possível escrever o ficheiro de saída {path}: {exc}") from exc


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    paths = build_paths(script_dir)

    assert_essential_files_exist(paths)

    essential_source_paths = [
        paths["fragmentos_resegmentados"],
        paths["cadencia_extraida"],
        paths["cadencia_schema"],
        paths["tratamento_filosofico_fragmentos"],
        paths["impacto_fragmentos_no_mapa"],
        paths["indice_por_percurso"],
        paths["argumentos_unificados"],
        paths["mapa_dedutivo_canonico_final"],
    ]
    generated_at_utc = deterministic_generated_at_utc(essential_source_paths)
    lote_hash = compute_source_hash(essential_source_paths)
    lote_geracao_id = f"LOT_{normalise_mode_token(args.modo)}_{'ALL' if args.limite is None else args.limite}_{lote_hash[:10].upper()}"

    loaded_data = {
        "fragmentos_resegmentados": load_json(paths["fragmentos_resegmentados"]),
        "cadencia_extraida": load_json(paths["cadencia_extraida"]),
        "cadencia_schema": load_json(paths["cadencia_schema"]),
        "tratamento_filosofico_fragmentos": load_json(paths["tratamento_filosofico_fragmentos"]),
        "impacto_fragmentos_no_mapa": load_json(paths["impacto_fragmentos_no_mapa"]),
        "indice_por_percurso": load_json(paths["indice_por_percurso"]),
        "argumentos_unificados": load_json(paths["argumentos_unificados"]),
        "mapa_dedutivo_canonico_final": load_json(paths["mapa_dedutivo_canonico_final"]),
        "relatorio_validacao_fragmentos": maybe_load_json(paths["relatorio_validacao_fragmentos"]),
    }

    if args.modo == "estrutura-vazia":
        tree = build_empty_tree(
            generated_at_utc=generated_at_utc,
            lote_geracao_id=lote_geracao_id,
            fontes=build_fontes_block(paths),
        )
    else:
        tree = build_populated_tree(
            args=args,
            data=loaded_data,
            paths=paths,
            generated_at_utc=generated_at_utc,
            lote_geracao_id=lote_geracao_id,
        )

    write_json_atomic(paths["output"], tree)

    print(f"OK: árvore gerada em {paths['output']}")
    print(
        "Resumo: "
        f"fragmentos={tree['validacao']['metricas']['total_fragmentos']}, "
        f"exceções={tree['validacao']['metricas']['total_excecoes_ativas']}, "
        f"estado={tree['validacao']['estado_validacao_global']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ArvoreGeracaoError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)