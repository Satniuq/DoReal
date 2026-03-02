#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de ARGUMENTOS (ARG_*) — D_*, OP_*, REGIME_*, P_*

Valida, para cada ficheiro ARG_*.json:
- IDs D_* em pressupostos_ontologicos / outputs_instalados / conceito_alvo existem em todos_os_conceitos.json
- IDs OP_* em operacoes_chave existem em operacoes.json
- IDs REGIME_* em fundamenta.regimes existem em meta_indice.json
- IDs P_* em fundamenta.percursos existem em meta_referencia_do_percurso.json
- Estrutura mínima obrigatória do argumento
- (Opcional) Valida que o capítulo existe no índice_sequencial.json

Uso:
  python 13_Meta_Indice/scripts/validar_argumentos.py
  python 13_Meta_Indice/scripts/validar_argumentos.py --dir argumentos
  python 13_Meta_Indice/scripts/validar_argumentos.py --strict
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

DEFAULT_ARGUMENTOS_DIR = os.path.join(META_INDICE_ROOT, "indice", "argumentos")
DEFAULT_CONCEITOS_FILE = os.path.join(META_INDICE_ROOT, "dados_base", "todos_os_conceitos.json")
DEFAULT_OPERACOES_FILE = os.path.join(META_INDICE_ROOT, "dados_base", "operacoes.json")
DEFAULT_META_INDICE_FILE = os.path.join(META_INDICE_ROOT, "meta", "meta_indice.json")
DEFAULT_META_REF_FILE = os.path.join(META_INDICE_ROOT, "meta", "meta_referencia_do_percurso.json")
DEFAULT_INDICE_SEQUENCIAL_FILE = os.path.join(META_INDICE_ROOT, "indice", "indice_sequencial.json")

DEFAULT_RELATORIO_OUT = os.path.join(META_INDICE_ROOT, "data", "relatorio_validacao_argumentos.json")


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
# Extracção de IDs canónicos
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


def extract_capitulo_ids(indice_sequencial: Any) -> Set[str]:
    if not isinstance(indice_sequencial, dict):
        return set()
    caps = indice_sequencial.get("capitulos", [])
    if not isinstance(caps, list):
        return set()
    ids: Set[str] = set()
    for c in caps:
        if isinstance(c, dict) and isinstance(c.get("id"), str):
            ids.add(c["id"])
    return ids


# ----------------------------
# Validação de um argumento
# ----------------------------

REQUIRED_FIELDS = [
    "id",
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
    "operacoes_chave",
    "estrutura_logica",
]

def validate_argument_structure(arg: Any, origin: str) -> Report:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(arg, dict):
        return Report(errors=[f"{origin}: argumento não é objecto JSON."], warnings=[])

    for f in REQUIRED_FIELDS:
        if f not in arg:
            errors.append(f"{origin}: campo obrigatório em falta: '{f}'")

    aid = arg.get("id", origin)
    if isinstance(aid, str) and not aid.startswith("ARG_"):
        warnings.append(f"{origin}: id não começa por 'ARG_': {aid}")

    # campos compostos
    fund = arg.get("fundamenta")
    if isinstance(fund, dict):
        if "regimes" not in fund or "percursos" not in fund:
            errors.append(f"{origin}: 'fundamenta' deve conter 'regimes' e 'percursos'.")
        else:
            if not isinstance(fund.get("regimes"), list):
                errors.append(f"{origin}: fundamenta.regimes deve ser lista.")
            if not isinstance(fund.get("percursos"), list):
                errors.append(f"{origin}: fundamenta.percursos deve ser lista.")
            if "modulos" in fund and not isinstance(fund.get("modulos"), list):
                errors.append(f"{origin}: fundamenta.modulos deve ser lista.")
    else:
        errors.append(f"{origin}: 'fundamenta' inválido (deve ser objecto).")

    # estrutura_logica
    el = arg.get("estrutura_logica")
    if isinstance(el, dict):
        for k in ["premissas", "deducoes_necessarias", "conclusao"]:
            if k not in el:
                errors.append(f"{origin}: estrutura_logica em falta: '{k}'")
        if "premissas" in el and not isinstance(el.get("premissas"), list):
            errors.append(f"{origin}: estrutura_logica.premissas deve ser lista.")
        if "deducoes_necessarias" in el and not isinstance(el.get("deducoes_necessarias"), list):
            errors.append(f"{origin}: estrutura_logica.deducoes_necessarias deve ser lista.")
        if "conclusao" in el and not isinstance(el.get("conclusao"), str):
            errors.append(f"{origin}: estrutura_logica.conclusao deve ser string.")
    else:
        errors.append(f"{origin}: 'estrutura_logica' inválido (deve ser objecto).")

    # listas simples
    for lf in ["pressupostos_ontologicos", "operacoes_chave"]:
        if lf in arg and not isinstance(arg.get(lf), list):
            errors.append(f"{origin}: '{lf}' deve ser lista.")

    if "outputs_instalados" in arg and not isinstance(arg.get("outputs_instalados"), list):
        errors.append(f"{origin}: 'outputs_instalados' deve ser lista (se existir).")

    return Report(errors=errors, warnings=warnings)


def validate_argument_references(
    arg: Dict[str, Any],
    origin: str,
    concept_ids: Set[str],
    op_ids: Set[str],
    regime_ids: Set[str],
    percurso_ids: Set[str],
    capitulo_ids: Set[str] | None = None,
) -> Report:
    errors: List[str] = []
    warnings: List[str] = []

    def _need_concept(x: Any, ctx: str) -> None:
        if not isinstance(x, str):
            errors.append(f"{origin}: {ctx} não é string: {x!r}")
            return
        if x not in concept_ids:
            errors.append(f"{origin}: conceito inexistente: {x} ({ctx})")

    def _need_op(x: Any, ctx: str) -> None:
        if not isinstance(x, str):
            errors.append(f"{origin}: {ctx} não é string: {x!r}")
            return
        if x not in op_ids:
            errors.append(f"{origin}: operação inexistente: {x} ({ctx})")

    def _need_regime(x: Any, ctx: str) -> None:
        if not isinstance(x, str):
            errors.append(f"{origin}: {ctx} não é string: {x!r}")
            return
        if x not in regime_ids:
            errors.append(f"{origin}: regime inexistente: {x} ({ctx})")

    def _need_percurso(x: Any, ctx: str) -> None:
        if not isinstance(x, str):
            errors.append(f"{origin}: {ctx} não é string: {x!r}")
            return
        if x not in percurso_ids:
            errors.append(f"{origin}: percurso inexistente: {x} ({ctx})")

    # capítulo (opcional)
    cap = arg.get("capitulo")
    if capitulo_ids is not None:
        if not isinstance(cap, str):
            errors.append(f"{origin}: capitulo inválido (não-string).")
        elif cap not in capitulo_ids:
            errors.append(f"{origin}: capitulo não existe no índice sequencial: {cap}")

    # conceito_alvo
    _need_concept(arg.get("conceito_alvo"), "conceito_alvo")

    # pressupostos + outputs
    for d in arg.get("pressupostos_ontologicos", []):
        _need_concept(d, "pressupostos_ontologicos")

    for d in arg.get("outputs_instalados", []):
        _need_concept(d, "outputs_instalados")

    # operações
    for op in arg.get("operacoes_chave", []):
        _need_op(op, "operacoes_chave")

    # regimes/percursos
    fund = arg.get("fundamenta", {})
    if isinstance(fund, dict):
        for r in fund.get("regimes", []):
            _need_regime(r, "fundamenta.regimes")
        for p in fund.get("percursos", []):
            _need_percurso(p, "fundamenta.percursos")

    return Report(errors=errors, warnings=warnings)


# ----------------------------
# Execução
# ----------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Validador de argumentos ARG_*.json (D/OP/REGIME/P).")
    parser.add_argument("--dir", dest="arg_dir", default=None, help="Directório de argumentos (default: 13_Meta_Indice/argumentos).")
    parser.add_argument("--conceitos", default=None, help="Override do caminho de conceitos.")
    parser.add_argument("--operacoes", default=None, help="Override do caminho de operações.")
    parser.add_argument("--meta-indice", dest="meta_indice", default=None, help="Override do meta_indice.")
    parser.add_argument("--meta-ref", dest="meta_ref", default=None, help="Override do meta_ref.")
    parser.add_argument("--indice-sequencial", dest="indice_sequencial", default=None, help="(Opcional) índice sequencial para validar capitulo.")
    parser.add_argument("--no-capitulo-check", action="store_true", help="Não valida capitulo contra o índice sequencial.")
    parser.add_argument("--out", default=None, help="Caminho do relatório JSON (opcional).")
    parser.add_argument("--strict", action="store_true", help="Falha também com warnings (exit code 2).")
    args = parser.parse_args()

    arg_dir = Path(args.arg_dir or DEFAULT_ARGUMENTOS_DIR)
    conceitos_path = Path(args.conceitos or DEFAULT_CONCEITOS_FILE)
    operacoes_path = Path(args.operacoes or DEFAULT_OPERACOES_FILE)
    meta_indice_path = Path(args.meta_indice or DEFAULT_META_INDICE_FILE)
    meta_ref_path = Path(args.meta_ref or DEFAULT_META_REF_FILE)
    indice_seq_path = Path(args.indice_sequencial or DEFAULT_INDICE_SEQUENCIAL_FILE)
    out_path = Path(args.out or DEFAULT_RELATORIO_OUT)

    try:
        conceitos = load_json(conceitos_path)
        operacoes = load_json(operacoes_path)
        meta_indice = load_json(meta_indice_path)
        meta_ref = load_json(meta_ref_path)
        indice_seq = load_json(indice_seq_path) if not args.no_capitulo_check else None
    except Exception as e:
        print(f"ERRO ao carregar ficheiros base: {e}")
        return 1

    concept_ids = extract_concept_ids(conceitos)
    op_ids = extract_operation_ids(operacoes)
    regime_ids = extract_regime_ids(meta_indice)
    percurso_ids = extract_percurso_ids(meta_ref)
    capitulo_ids = extract_capitulo_ids(indice_seq) if indice_seq is not None else None

    if not arg_dir.exists() or not arg_dir.is_dir():
        print(f"ERRO: directório de argumentos não encontrado: {arg_dir}")
        return 1

    # procurar argumentos com ou sem prefixo numérico
    files = sorted(arg_dir.glob("ARG_*.json"))
    files += sorted(arg_dir.glob("*_ARG_*.json"))

    # remover duplicados (caso apanhe o mesmo por dois padrões)
    files = sorted({p.resolve() for p in files})
    if not files:
        print(f"WARNING: não encontrei ARG_*.json em {arg_dir}")
        return 0

    all_errors: List[str] = []
    all_warnings: List[str] = []

    per_file: Dict[str, Dict[str, Any]] = {}

    for f in files:
        origin = f.name
        try:
            arg = load_json(f)
        except Exception as e:
            all_errors.append(f"{origin}: falha ao ler JSON: {e}")
            continue

        r_struct = validate_argument_structure(arg, origin)
        r_refs = validate_argument_references(
            arg=arg if isinstance(arg, dict) else {},
            origin=origin,
            concept_ids=concept_ids,
            op_ids=op_ids,
            regime_ids=regime_ids,
            percurso_ids=percurso_ids,
            capitulo_ids=capitulo_ids,
        )

        errs = r_struct.errors + r_refs.errors
        warns = r_struct.warnings + r_refs.warnings

        all_errors.extend(errs)
        all_warnings.extend(warns)

        per_file[origin] = {
            "ok": len(errs) == 0,
            "errors": errs,
            "warnings": warns,
            "arg_id": arg.get("id") if isinstance(arg, dict) else None
        }

    report_obj = {
        "ok": len(all_errors) == 0,
        "errors": all_errors,
        "warnings": all_warnings,
        "files_checked": [p.name for p in files],
        "per_file": per_file,
        "paths": {
            "argumentos_dir": str(arg_dir),
            "conceitos": str(conceitos_path),
            "operacoes": str(operacoes_path),
            "meta_indice": str(meta_indice_path),
            "meta_ref": str(meta_ref_path),
            "indice_sequencial": str(indice_seq_path) if indice_seq is not None else None
        }
    }

    Report(all_errors, all_warnings).print()
    dump_json(out_path, report_obj)

    if all_errors:
        return 1
    if args.strict and all_warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())