#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de INDICE POR PERCURSO — indice_por_percurso.json

Valida:
- Estrutura mínima do índice por percurso
- Percursos P_* existem em meta_referencia_do_percurso.json
- Capítulos existem no indice_sequencial.json
- Consistência:
  - directo.axial: cap.percurso_axial == percurso
  - directo.participante: percurso in cap.percursos_participantes
- Ordenação de capítulos (ordem crescente por indice_sequencial.ordem)
- "com_pressupostos":
  - percursos_base corresponde ao fecho transitivo de pressupoe_percursos
  - caps_ids corresponde à união dos capítulos directos de todos os percursos_base
- Argumentos listados por capítulo:
  - existem em argumentos_unificados.json (ou são planeados -> warning)
  - arg.capitulo bate com o capítulo
  - (opcional) ordem bate com indice_argumentos.json (warning)

Uso:
  python 13_Meta_Indice/scripts/validar_indice_por_percurso.py
  python 13_Meta_Indice/scripts/validar_indice_por_percurso.py --file 13_Meta_Indice/indice/indice_por_percurso.json
  python 13_Meta_Indice/scripts/validar_indice_por_percurso.py --strict
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

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

DEFAULT_INDICE_POR_PERCURSO_FILE = os.path.join(META_INDICE_ROOT, "indice", "indice_por_percurso.json")
DEFAULT_META_REF_FILE = os.path.join(META_INDICE_ROOT, "meta", "meta_referencia_do_percurso.json")
DEFAULT_INDICE_SEQUENCIAL_FILE = os.path.join(META_INDICE_ROOT, "indice", "indice_sequencial.json")
DEFAULT_ARGUMENTOS_UNIFICADOS_FILE = os.path.join(META_INDICE_ROOT, "indice", "argumentos", "argumentos_unificados.json")
DEFAULT_INDICE_ARGUMENTOS_FILE = os.path.join(META_INDICE_ROOT, "indice", "indice_argumentos.json")

DEFAULT_RELATORIO_OUT = os.path.join(META_INDICE_ROOT, "data", "relatorio_validacao_indice_por_percurso.json")


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
# Extractores
# ----------------------------

def extract_percurso_ids(meta_ref_json: Any) -> Set[str]:
    return set(meta_ref_json.keys()) if isinstance(meta_ref_json, dict) else set()

def extract_capitulos(indice_sequencial: Any) -> Dict[str, Dict[str, Any]]:
    caps: Dict[str, Dict[str, Any]] = {}
    if not isinstance(indice_sequencial, dict):
        return caps
    arr = indice_sequencial.get("capitulos", [])
    if not isinstance(arr, list):
        return caps
    for c in arr:
        if isinstance(c, dict) and isinstance(c.get("id"), str):
            caps[c["id"]] = c
    return caps

def extract_args_unificados(args_unificados: Any) -> Dict[str, Dict[str, Any]]:
    d: Dict[str, Dict[str, Any]] = {}
    if isinstance(args_unificados, list):
        for a in args_unificados:
            if isinstance(a, dict) and isinstance(a.get("id"), str):
                d[a["id"]] = a
    return d

def extract_indice_argumentos_ordem(indice_argumentos: Any, cap_ids_by_ordem: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Devolve map CAP_ID -> [ARG_ID ordenados] com base no indice_argumentos.json.
    cap_ids_by_ordem: "01" -> CAP_01_... (id interno)
    """
    out: Dict[str, List[str]] = {}
    if not isinstance(indice_argumentos, dict):
        return out

    aux = indice_argumentos.get("lista_auxiliar_argumentos", {})
    partes = aux.get("partes", [])
    if not isinstance(partes, list):
        return out

    for parte in partes:
        caps = parte.get("capitulos", [])
        if not isinstance(caps, list):
            continue
        for cap in caps:
            cap_str = cap.get("capitulo")
            if not isinstance(cap_str, str):
                continue
            m = re.match(r'^\s*CAP_(\d{2})\b', cap_str.replace("—", "-"))
            if not m:
                continue
            n = m.group(1)
            cap_id = cap_ids_by_ordem.get(n)
            if not cap_id:
                continue
            arr = cap.get("argumentos", [])
            if not isinstance(arr, list):
                continue
            out.setdefault(cap_id, [])
            for a in arr:
                if isinstance(a, dict) and isinstance(a.get("id"), str):
                    out[cap_id].append(a["id"])
    return out


# ----------------------------
# Fecho transitivo de pressupostos
# ----------------------------

def closure(meta_ref: Dict[str, Any], p: str) -> Set[str]:
    seen: Set[str] = set()
    stack: List[str] = [p]
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        pres = meta_ref.get(x, {}).get("pressupoe_percursos", [])
        if isinstance(pres, list):
            for y in pres:
                if isinstance(y, str) and y not in seen:
                    stack.append(y)
    return seen


# ----------------------------
# Validação principal
# ----------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Validador de indice_por_percurso.json (consistência com meta_ref e indice_sequencial).")
    parser.add_argument("--file", default=None, help="Caminho do indice_por_percurso.json (default: 13_Meta_Indice/indice/indice_por_percurso.json)")
    parser.add_argument("--meta-ref", dest="meta_ref", default=None, help="Override do meta_referencia_do_percurso.json")
    parser.add_argument("--indice-sequencial", dest="indice_sequencial", default=None, help="Override do indice_sequencial.json")
    parser.add_argument("--argumentos-unificados", dest="args_unif", default=None, help="Override do argumentos_unificados.json")
    parser.add_argument("--indice-argumentos", dest="indice_args", default=None, help="Override do indice_argumentos.json (para validar ordem)")
    parser.add_argument("--no-arg-order-check", action="store_true", help="Não valida a ordem de argumentos contra indice_argumentos.json")
    parser.add_argument("--out", default=None, help="Caminho do relatório JSON (opcional).")
    parser.add_argument("--strict", action="store_true", help="Falha também com warnings (exit code 2).")
    args = parser.parse_args()

    file_path = Path(args.file or DEFAULT_INDICE_POR_PERCURSO_FILE)
    meta_ref_path = Path(args.meta_ref or DEFAULT_META_REF_FILE)
    indice_seq_path = Path(args.indice_sequencial or DEFAULT_INDICE_SEQUENCIAL_FILE)
    args_unif_path = Path(args.args_unif or DEFAULT_ARGUMENTOS_UNIFICADOS_FILE)
    indice_args_path = Path(args.indice_args or DEFAULT_INDICE_ARGUMENTOS_FILE)
    out_path = Path(args.out or DEFAULT_RELATORIO_OUT)

    try:
        idx_pp = load_json(file_path)
        meta_ref = load_json(meta_ref_path)
        indice_seq = load_json(indice_seq_path)
        args_unif = load_json(args_unif_path)
        indice_args = load_json(indice_args_path) if not args.no_arg_order_check else None
    except Exception as e:
        print(f"ERRO ao carregar ficheiros base: {e}")
        return 1

    errors: List[str] = []
    warnings: List[str] = []

    # bases
    percurso_ids = extract_percurso_ids(meta_ref)
    caps = extract_capitulos(indice_seq)
    args_by_id = extract_args_unificados(args_unif)

    # map ordem -> cap_id (para cruzar com indice_argumentos)
    cap_ids_by_ordem: Dict[str, str] = {}
    for cid, c in caps.items():
        o = c.get("ordem")
        if isinstance(o, int):
            cap_ids_by_ordem[str(o).zfill(2)] = cid

    ordem_args_por_cap = extract_indice_argumentos_ordem(indice_args, cap_ids_by_ordem) if indice_args is not None else {}

    # estrutura topo
    if not isinstance(idx_pp, dict):
        errors.append(f"{file_path.name}: raiz não é objecto JSON.")
        Report(errors, warnings).print()
        return 1

    percursos_obj = idx_pp.get("percursos")
    if not isinstance(percursos_obj, dict):
        errors.append(f"{file_path.name}: falta 'percursos' ou não é objecto.")
        Report(errors, warnings).print()
        return 1

    # pré-computar capítulos directos por percurso com base no indice_sequencial (fonte de verdade)
    direct_axial_truth: Dict[str, Set[str]] = {p: set() for p in percurso_ids}
    direct_part_truth: Dict[str, Set[str]] = {p: set() for p in percurso_ids}

    for cid, c in caps.items():
        pa = c.get("percurso_axial")
        if isinstance(pa, str) and pa in direct_axial_truth:
            direct_axial_truth[pa].add(cid)
        pps = c.get("percursos_participantes", [])
        if isinstance(pps, list):
            for p in pps:
                if isinstance(p, str) and p in direct_part_truth:
                    direct_part_truth[p].add(cid)

    per_percurso: Dict[str, Dict[str, Any]] = {}

    def _is_sorted_by_ordem(cap_ids: List[str]) -> bool:
        ords: List[int] = []
        for cid in cap_ids:
            o = caps.get(cid, {}).get("ordem")
            ords.append(o if isinstance(o, int) else 10**9)
        return ords == sorted(ords)

    # validar cada percurso do ficheiro
    for p, pobj in percursos_obj.items():
        origin = f"{file_path.name}: percurso {p}"

        if not isinstance(p, str):
            errors.append(f"{origin}: chave de percurso não é string.")
            continue

        if p not in percurso_ids:
            errors.append(f"{origin}: percurso não existe em meta_referencia_do_percurso.json.")
            continue

        if not isinstance(pobj, dict):
            errors.append(f"{origin}: valor do percurso não é objecto.")
            continue

        # secções esperadas
        direct = pobj.get("directo")
        with_pres = pobj.get("com_pressupostos")

        if not isinstance(direct, dict):
            errors.append(f"{origin}: falta 'directo' ou não é objecto.")
            continue
        if not isinstance(with_pres, dict):
            errors.append(f"{origin}: falta 'com_pressupostos' ou não é objecto.")
            continue

        # --- direct validation ---
        axial = direct.get("axial", [])
        part = direct.get("participante", [])
        caps_ids = direct.get("caps_ids", [])

        if not isinstance(axial, list) or not isinstance(part, list) or not isinstance(caps_ids, list):
            errors.append(f"{origin}: 'directo.axial/participante/caps_ids' com tipo inválido.")
            continue

        # axial/participante items: aceitamos objectos cap_entry (com id), mas validamos por id
        axial_ids = []
        for item in axial:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                axial_ids.append(item["id"])
            else:
                errors.append(f"{origin}: 'directo.axial' contém item sem 'id' string.")
        part_ids = []
        for item in part:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                part_ids.append(item["id"])
            else:
                errors.append(f"{origin}: 'directo.participante' contém item sem 'id' string.")

        # caps_ids
        bad_caps = [cid for cid in caps_ids if not isinstance(cid, str)]
        if bad_caps:
            errors.append(f"{origin}: 'directo.caps_ids' tem entradas não-string: {bad_caps!r}")

        # caps existem
        for cid in set(axial_ids + part_ids + [c for c in caps_ids if isinstance(c, str)]):
            if cid not in caps:
                errors.append(f"{origin}: capítulo inexistente no indice_sequencial.json: {cid}")

        # consistência axial/participante com indice_sequencial
        for cid in axial_ids:
            pa = caps.get(cid, {}).get("percurso_axial")
            if pa != p:
                errors.append(f"{origin}: capítulo em directo.axial mas percurso_axial do capítulo é {pa!r}: {cid}")

        for cid in part_ids:
            pps = caps.get(cid, {}).get("percursos_participantes", [])
            ok = isinstance(pps, list) and (p in pps)
            if not ok:
                errors.append(f"{origin}: capítulo em directo.participante mas percurso não está em percursos_participantes: {cid}")

        # direct.caps_ids deve ser união (axial ∪ participante)
        expected_direct = sorted(set(axial_ids) | set(part_ids), key=lambda x: caps.get(x, {}).get("ordem", 10**9))
        got_direct = [c for c in caps_ids if isinstance(c, str)]
        if set(got_direct) != set(expected_direct):
            errors.append(f"{origin}: direct.caps_ids não bate com união de axial+participante (por conjunto).")
        else:
            # ordem
            if not _is_sorted_by_ordem(got_direct):
                warnings.append(f"{origin}: direct.caps_ids não está ordenado por 'ordem' do indice_sequencial.")

        # comparar com verdade derivada do indice_sequencial
        truth_ax = direct_axial_truth.get(p, set())
        truth_pt = direct_part_truth.get(p, set())
        if set(axial_ids) != truth_ax:
            errors.append(f"{origin}: direct.axial diverge do indice_sequencial (axial).")
        if set(part_ids) != truth_pt:
            errors.append(f"{origin}: direct.participante diverge do indice_sequencial (participante).")

        # --- argumentos por capítulo (no direct) ---
        def validate_args_in_cap(cap_entry: Dict[str, Any], ctx: str) -> None:
            cid = cap_entry.get("id")
            if not isinstance(cid, str):
                errors.append(f"{origin}: {ctx}: capítulo sem id string.")
                return
            arg_list = cap_entry.get("argumentos", [])
            if not isinstance(arg_list, list):
                errors.append(f"{origin}: {ctx}: 'argumentos' não é lista em {cid}.")
                return

            # ordem esperada pelo indice_argumentos (se disponível)
            expected_order = ordem_args_por_cap.get(cid)

            seen: Set[str] = set()
            got_ids: List[str] = []
            for a in arg_list:
                if not isinstance(a, dict) or not isinstance(a.get("id"), str):
                    errors.append(f"{origin}: {ctx}: argumento sem id string em {cid}.")
                    continue
                aid = a["id"]
                if aid in seen:
                    errors.append(f"{origin}: {ctx}: argumento repetido em {cid}: {aid}")
                seen.add(aid)
                got_ids.append(aid)

                # existe em argumentos_unificados?
                if aid not in args_by_id:
                    warnings.append(f"{origin}: {ctx}: argumento não encontrado em argumentos_unificados.json (planeado?): {aid}")
                else:
                    # capítulo bate?
                    acap = args_by_id[aid].get("capitulo")
                    if acap != cid:
                        errors.append(f"{origin}: {ctx}: argumento {aid} tem capitulo={acap!r} mas está listado em {cid}")

            if expected_order:
                # só comparamos os que existem na lista (tolerante a planeados/extras)
                # Se a lista do índice por percurso for um prefixo/superconjunto, avisamos.
                if got_ids != expected_order:
                    warnings.append(f"{origin}: {ctx}: ordem de argumentos em {cid} difere do indice_argumentos.json.")

        for ce in axial:
            if isinstance(ce, dict):
                validate_args_in_cap(ce, "directo.axial")
        for ce in part:
            if isinstance(ce, dict):
                validate_args_in_cap(ce, "directo.participante")

        # --- com_pressupostos validation ---
        base = with_pres.get("percursos_base", [])
        caps_union_ids = with_pres.get("caps_ids", [])

        if not isinstance(base, list) or not all(isinstance(x, str) for x in base):
            errors.append(f"{origin}: com_pressupostos.percursos_base inválido (deve ser lista de strings).")
            base = [x for x in base if isinstance(x, str)]

        # fecho transitivo esperado
        expected_base_set = closure(meta_ref, p)
        got_base_set = set(base)

        # deve conter pelo menos o próprio percurso
        if p not in got_base_set:
            errors.append(f"{origin}: com_pressupostos.percursos_base não contém o próprio percurso {p}.")

        if got_base_set != expected_base_set:
            # conjunto diferente é erro
            errors.append(f"{origin}: com_pressupostos.percursos_base (conjunto) não bate com fecho transitivo de pressupostos.")
        else:
            # ordem (se difere, warning)
            # sugerimos ordem por meta_ref (chaves), mas não impomos como erro
            meta_order = [k for k in meta_ref.keys() if k in expected_base_set]
            if base != meta_order:
                warnings.append(f"{origin}: com_pressupostos.percursos_base tem ordem diferente da ordem canónica (meta_ref).")

        # caps_ids esperados = união de directos de todos os percursos base (verdade do indice_sequencial)
        expected_caps_union: Set[str] = set()
        for bp in expected_base_set:
            expected_caps_union |= direct_axial_truth.get(bp, set())
            expected_caps_union |= direct_part_truth.get(bp, set())

        if not isinstance(caps_union_ids, list) or not all(isinstance(x, str) for x in caps_union_ids):
            errors.append(f"{origin}: com_pressupostos.caps_ids inválido (deve ser lista de strings).")
        else:
            got_caps_union_set = set(caps_union_ids)
            if got_caps_union_set != expected_caps_union:
                errors.append(f"{origin}: com_pressupostos.caps_ids não bate com a união esperada (por conjunto).")
            else:
                if not _is_sorted_by_ordem(caps_union_ids):
                    warnings.append(f"{origin}: com_pressupostos.caps_ids não está ordenado por 'ordem' do indice_sequencial.")

        per_percurso[p] = {
            "ok": True,  # preenchido no fim
        }

    ok = (len(errors) == 0)

    report_obj = {
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "file_checked": str(file_path),
        "paths": {
            "indice_por_percurso": str(file_path),
            "meta_ref": str(meta_ref_path),
            "indice_sequencial": str(indice_seq_path),
            "argumentos_unificados": str(args_unif_path),
            "indice_argumentos": str(indice_args_path) if indice_args is not None else None,
        },
    }

    Report(errors, warnings).print()
    dump_json(out_path, report_obj)

    if errors:
        return 1
    if args.strict and warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())