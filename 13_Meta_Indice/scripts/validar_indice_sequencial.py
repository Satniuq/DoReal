#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador do INDICE_SEQUENCIAL (D_*, OP_*, REGIME_*, P_*).

- Verifica se todos os D_* referidos em "campos" existem em dados_base/todos_os_conceitos.json
- Verifica se todos os REGIME_* existem em meta/meta_indice.json
- Verifica se todos os P_* existem em meta/meta_referencia_do_percurso.json
- Verifica enum de estado_instalacao, ordens duplicadas, e coerência básica.
- (Opcional) Valida também se as OP_* listadas em meta_indice existem em dados_base/operacoes.json

Uso:
  python 13_Meta_Indice/scripts/validar_indice_sequencial.py
  python 13_Meta_Indice/scripts/validar_indice_sequencial.py --strict
  python 13_Meta_Indice/scripts/validar_indice_sequencial.py --indice "C:\\...\\indice_sequencial.json"
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set

from dotenv import load_dotenv


# =====================================================
# 0.1) PATHS PORTÁTEIS (DOREAL_ROOT)
# =====================================================

def _guess_root(default_here: bool = True) -> str:
    """
    Resolve a raiz DoReal:
    1) usa env DOREAL_ROOT se existir e contiver 13_Meta_Indice/
    2) caso contrário, tenta inferir a partir do local do script (13_Meta_Indice/scripts)
    """
    load_dotenv()
    root = os.getenv("DOREAL_ROOT")
    if root and os.path.isdir(root) and os.path.isdir(os.path.join(root, "13_Meta_Indice")):
        return root

    if default_here:
        here = os.path.abspath(os.path.dirname(__file__))  # .../13_Meta_Indice/scripts
        cand = os.path.abspath(os.path.join(here, "..", ".."))  # .../DoReal
        if os.path.isdir(os.path.join(cand, "13_Meta_Indice")):
            return cand

    return os.getcwd()


DOREAL_ROOT = _guess_root()
META_INDICE_ROOT = os.path.join(DOREAL_ROOT, "13_Meta_Indice")

# ---- Defaults portáteis ----
DEFAULT_INDICE_FILE = os.path.join(META_INDICE_ROOT, "indice", "indice_sequencial.json")
DEFAULT_CONCEITOS_FILE = os.path.join(META_INDICE_ROOT, "dados_base", "todos_os_conceitos.json")
DEFAULT_OPERACOES_FILE = os.path.join(META_INDICE_ROOT, "dados_base", "operacoes.json")
DEFAULT_META_INDICE_FILE = os.path.join(META_INDICE_ROOT, "meta", "meta_indice.json")
DEFAULT_META_REF_FILE = os.path.join(META_INDICE_ROOT, "meta", "meta_referencia_do_percurso.json")

DEFAULT_RELATORIO_OUT = os.path.join(META_INDICE_ROOT, "data", "relatorio_validacao_indice_sequencial.json")


# ----------------------------
# Utilitários
# ----------------------------

def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido em {path}: {e}") from e


def dump_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class Report:
    errors: List[str]
    warnings: List[str]

    def ok(self) -> bool:
        return len(self.errors) == 0

    def print(self) -> None:
        if self.errors:
            print("ERROS:")
            for e in self.errors:
                print(f" - {e}")
        else:
            print("ERROS: (nenhum)")

        print()

        if self.warnings:
            print("WARNINGS:")
            for w in self.warnings:
                print(f" - {w}")
        else:
            print("WARNINGS: (nenhum)")


# ----------------------------
# Extracção de IDs
# ----------------------------

def extract_concept_ids(conceitos_json: Any) -> Set[str]:
    if isinstance(conceitos_json, dict):
        return {k for k in conceitos_json.keys() if isinstance(k, str)}
    if isinstance(conceitos_json, list):
        ids: Set[str] = set()
        for item in conceitos_json:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                ids.add(item["id"])
        return ids
    return set()


def extract_operation_ids(operacoes_json: Any) -> Set[str]:
    if isinstance(operacoes_json, dict):
        return {k for k in operacoes_json.keys() if isinstance(k, str)}
    if isinstance(operacoes_json, list):
        ids: Set[str] = set()
        for item in operacoes_json:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                ids.add(item["id"])
        return ids
    return set()


def extract_regime_ids(meta_indice_json: Any) -> Set[str]:
    if isinstance(meta_indice_json, dict):
        root = meta_indice_json.get("meta_indice", meta_indice_json)
        regimes = root.get("regimes", {})
        if isinstance(regimes, dict):
            return set(regimes.keys())
    return set()


def extract_percurso_ids(meta_ref_json: Any) -> Set[str]:
    if isinstance(meta_ref_json, dict):
        return set(meta_ref_json.keys())
    return set()


# ----------------------------
# Validações
# ----------------------------

def validate_indice_structure(indice: Any) -> Report:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(indice, dict):
        return Report(errors=["O índice sequencial não é um objecto JSON (dict)."], warnings=[])

    for key in ["schema_version", "id", "criterio_ultimo", "capitulos"]:
        if key not in indice:
            errors.append(f"Campo obrigatório em falta no índice: '{key}'")

    if "capitulos" in indice and not isinstance(indice["capitulos"], list):
        errors.append("Campo 'capitulos' deve ser uma lista.")

    # enum estado_instalacao
    enum = indice.get("enum")
    if isinstance(enum, dict) and isinstance(enum.get("estado_instalacao"), list):
        allowed_states = set(enum["estado_instalacao"])
    else:
        allowed_states = {"introduz", "desenvolve", "fecha"}
        warnings.append("Índice sem 'enum.estado_instalacao'. A validar contra {introduz, desenvolve, fecha}.")

    seen_ids: Set[str] = set()
    seen_orders: Set[int] = set()
    orders: List[int] = []

    for i, cap in enumerate(indice.get("capitulos", []), start=1):
        if not isinstance(cap, dict):
            errors.append(f"Capítulo na posição {i} não é um objecto.")
            continue

        cid = cap.get("id", f"<cap_{i}>")

        if not isinstance(cap.get("id"), str) or not cap["id"].startswith("CAP_"):
            errors.append(f"Capítulo na posição {i} tem 'id' inválido: {cap.get('id')!r}")
        else:
            if cap["id"] in seen_ids:
                errors.append(f"ID de capítulo repetido: {cap['id']}")
            seen_ids.add(cap["id"])

        ordem = cap.get("ordem")
        if not isinstance(ordem, int):
            errors.append(f"{cid}: 'ordem' deve ser inteiro.")
        else:
            if ordem in seen_orders:
                errors.append(f"Ordem repetida {ordem} (capítulo {cid}).")
            seen_orders.add(ordem)
            orders.append(ordem)

        for req in ["parte", "nivel", "campos", "regime_principal", "percurso_axial", "estado_instalacao"]:
            if req not in cap:
                errors.append(f"{cid}: campo obrigatório em falta: '{req}'")

        if "campos" in cap and not isinstance(cap["campos"], list):
            errors.append(f"{cid}: 'campos' deve ser lista.")
        if "regimes_secundarios" in cap and not isinstance(cap["regimes_secundarios"], list):
            errors.append(f"{cid}: 'regimes_secundarios' deve ser lista.")
        if "percursos_participantes" in cap and not isinstance(cap["percursos_participantes"], list):
            errors.append(f"{cid}: 'percursos_participantes' deve ser lista.")

        st = cap.get("estado_instalacao")
        if isinstance(st, str) and st not in allowed_states:
            errors.append(f"{cid}: estado_instalacao inválido: {st!r} (permitidos: {sorted(allowed_states)})")

    if orders:
        o_sorted = sorted(orders)
        expected = list(range(min(o_sorted), max(o_sorted) + 1))
        if o_sorted != expected:
            warnings.append(f"Ordens não consecutivas. Encontradas: {o_sorted}. Esperado: {expected}.")

    return Report(errors=errors, warnings=warnings)


def validate_references(
    indice: Dict[str, Any],
    concept_ids: Set[str],
    regime_ids: Set[str],
    percurso_ids: Set[str],
) -> Report:
    errors: List[str] = []
    warnings: List[str] = []

    for cap in indice.get("capitulos", []):
        cid = cap.get("id", "<sem_id>")

        for d in cap.get("campos", []):
            if not isinstance(d, str):
                errors.append(f"{cid}: campo não-string em 'campos': {d!r}")
                continue
            if d not in concept_ids:
                errors.append(f"{cid}: conceito inexistente: {d}")

        rp = cap.get("regime_principal")
        if not isinstance(rp, str):
            errors.append(f"{cid}: regime_principal inválido (não-string).")
        elif rp not in regime_ids:
            errors.append(f"{cid}: regime_principal desconhecido: {rp}")

        for r in cap.get("regimes_secundarios", []):
            if not isinstance(r, str):
                errors.append(f"{cid}: regime_secundario inválido (não-string): {r!r}")
                continue
            if r not in regime_ids:
                errors.append(f"{cid}: regime_secundario desconhecido: {r}")

        pa = cap.get("percurso_axial")
        if not isinstance(pa, str):
            errors.append(f"{cid}: percurso_axial inválido (não-string).")
        elif pa not in percurso_ids:
            errors.append(f"{cid}: percurso_axial desconhecido: {pa}")

        for p in cap.get("percursos_participantes", []):
            if not isinstance(p, str):
                errors.append(f"{cid}: percurso_participante inválido (não-string): {p!r}")
                continue
            if p not in percurso_ids:
                errors.append(f"{cid}: percurso_participante desconhecido: {p}")

    return Report(errors=errors, warnings=warnings)


def validate_meta_indice_operations(meta_indice: Any, op_ids: Set[str]) -> Report:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(meta_indice, dict):
        return Report(errors=["meta_indice.json não é um objecto JSON."], warnings=[])

    root = meta_indice.get("meta_indice", meta_indice)
    regimes = root.get("regimes", {})
    if not isinstance(regimes, dict):
        return Report(errors=["meta_indice.json: 'regimes' ausente ou inválido."], warnings=[])

    for rid, r in regimes.items():
        if not isinstance(r, dict):
            errors.append(f"Regime {rid}: definição inválida (não-objecto).")
            continue
        ops = r.get("operacoes", [])
        if not isinstance(ops, list):
            errors.append(f"Regime {rid}: 'operacoes' deve ser lista.")
            continue
        for op in ops:
            if not isinstance(op, str):
                errors.append(f"Regime {rid}: OP inválida (não-string): {op!r}")
                continue
            if op not in op_ids:
                errors.append(f"Regime {rid}: OP não existe em operacoes.json: {op}")

    return Report(errors=errors, warnings=warnings)


def validate_meta_ref(meta_ref: Any) -> Report:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(meta_ref, dict):
        return Report(errors=["meta_referencia_do_percurso.json não é um objecto JSON."], warnings=[])

    percurso_ids = set(meta_ref.keys())

    for pid, pdef in meta_ref.items():
        if not isinstance(pdef, dict):
            errors.append(f"{pid}: definição inválida (não-objecto).")
            continue
        deps = pdef.get("pressupoe_percursos", [])
        if not isinstance(deps, list):
            errors.append(f"{pid}: 'pressupoe_percursos' deve ser lista.")
            continue
        for dep in deps:
            if not isinstance(dep, str):
                errors.append(f"{pid}: pressuposto inválido (não-string): {dep!r}")
                continue
            if dep not in percurso_ids:
                errors.append(f"{pid}: pressupõe percurso inexistente: {dep}")

    visiting: Set[str] = set()
    visited: Set[str] = set()

    def dfs(node: str, path: List[str]) -> None:
        nonlocal errors
        if node in visiting:
            cycle_start = path.index(node) if node in path else 0
            cycle = path[cycle_start:] + [node]
            errors.append(f"Ciclo detectado em meta_ref: {' -> '.join(cycle)}")
            return
        if node in visited:
            return
        visiting.add(node)
        deps = meta_ref.get(node, {}).get("pressupoe_percursos", [])
        if isinstance(deps, list):
            for dep in deps:
                if isinstance(dep, str):
                    dfs(dep, path + [node])
        visiting.remove(node)
        visited.add(node)

    for pid in percurso_ids:
        if pid not in visited:
            dfs(pid, [])

    return Report(errors=errors, warnings=warnings)


# ----------------------------
# CLI
# ----------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Validador do INDICE_SEQUENCIAL (D/OP/REGIME/P).")
    parser.add_argument("--indice", default=None, help="Override do caminho do índice.")
    parser.add_argument("--conceitos", default=None, help="Override do caminho de conceitos.")
    parser.add_argument("--operacoes", default=None, help="Override do caminho de operações.")
    parser.add_argument("--meta-indice", dest="meta_indice", default=None, help="Override do meta_indice.")
    parser.add_argument("--meta-ref", dest="meta_ref", default=None, help="Override do meta_ref.")
    parser.add_argument("--out", default=None, help="Caminho do relatório JSON (opcional).")
    parser.add_argument("--strict", action="store_true", help="Falha também com warnings (exit code 2).")
    args = parser.parse_args()

    indice_path = Path(args.indice or DEFAULT_INDICE_FILE)
    conceitos_path = Path(args.conceitos or DEFAULT_CONCEITOS_FILE)
    operacoes_path = Path(args.operacoes or DEFAULT_OPERACOES_FILE)
    meta_indice_path = Path(args.meta_indice or DEFAULT_META_INDICE_FILE)
    meta_ref_path = Path(args.meta_ref or DEFAULT_META_REF_FILE)
    out_path = Path(args.out or DEFAULT_RELATORIO_OUT)

    try:
        indice = load_json(indice_path)
        conceitos = load_json(conceitos_path)
        operacoes = load_json(operacoes_path)
        meta_indice = load_json(meta_indice_path)
        meta_ref = load_json(meta_ref_path)
    except Exception as e:
        print(f"ERRO ao carregar ficheiros: {e}")
        return 1

    concept_ids = extract_concept_ids(conceitos)
    op_ids = extract_operation_ids(operacoes)
    regime_ids = extract_regime_ids(meta_indice)
    percurso_ids = extract_percurso_ids(meta_ref)

    r1 = validate_indice_structure(indice)
    r2 = validate_references(indice, concept_ids, regime_ids, percurso_ids)
    r3 = validate_meta_indice_operations(meta_indice, op_ids)
    r4 = validate_meta_ref(meta_ref)

    all_errors = r1.errors + r2.errors + r3.errors + r4.errors
    all_warnings = r1.warnings + r2.warnings + r3.warnings + r4.warnings

    report_obj = {
        "ok": len(all_errors) == 0,
        "errors": all_errors,
        "warnings": all_warnings,
        "paths": {
            "indice": str(indice_path),
            "conceitos": str(conceitos_path),
            "operacoes": str(operacoes_path),
            "meta_indice": str(meta_indice_path),
            "meta_ref": str(meta_ref_path)
        }
    }

    # imprime e grava relatório
    Report(all_errors, all_warnings).print()
    dump_json(out_path, report_obj)

    if all_errors:
        return 1
    if args.strict and all_warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())