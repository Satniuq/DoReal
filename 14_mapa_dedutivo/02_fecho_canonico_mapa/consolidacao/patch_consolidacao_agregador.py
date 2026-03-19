#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Patch estrutural do agregador de decisões canónicas intermédias.

Objetivo:
- separar decisões por passo e por subpasso;
- corrigir meta.modo_execucao;
- corrigir referências arbitrais inválidas;
- corrigir numero_final residual de P42_P48;
- limpar/normalizar fontes_utilizadas e inputs_utilizados;
- recomputar resumo;
- validar o resultado contra os schemas.

Uso:
    python patch_consolidacao_agregador.py \
        --input "..\\outputs\\decisoes_canonicas_intermedias_copy_3 copy.json" \
        --output "decisoes_canonicas_intermedias_consolidado_candidato.json" \
        --schema-dir "..\\schemas"
"""

from __future__ import annotations

import argparse
import collections
import copy
import json
import os
import sys
import unicodedata
from pathlib import Path
from typing import Iterable, List

from jsonschema import Draft202012Validator, RefResolver


DROP_PLACEHOLDERS = {
    "dados/MATRIZ_INEVITABILIDADES_RECORTE_JSON",
    "dados/MAPA_PRECANONICO_RECORTE_JSON",
    "dados/DOSSIER_CORREDOR_RECORTE_JSON",
    "dados/INPUTS_SECUNDARIOS_RELEVANTES_JSON",
}

P42_P48_NUMEROS_FINAIS = {
    "P42": 42,
    "P43": 43,
    "P44": 44,
    "P45": 45,
    "P46": 46,
    "P47": 47,
    "P48": 48,
}


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def ascii_path(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def clean_paths(paths: Iterable[str], *, drop_aggregator_refs: bool) -> List[str]:
    out: List[str] = []
    seen = set()

    for raw in paths:
        path = ascii_path(raw)

        if path in DROP_PLACEHOLDERS:
            continue

        base = os.path.basename(path)
        if drop_aggregator_refs and base.startswith("decisoes_canonicas_intermedias"):
            continue

        if path not in seen:
            seen.add(path)
            out.append(path)

    return out


def split_step_and_substep_records(data: dict) -> None:
    mixed = data["decisoes_por_passo"]
    passos = [item for item in mixed if item.get("tipo_registo") == "decisao_passo"]
    subpassos = [item for item in mixed if item.get("tipo_registo") == "decisao_subpasso"]

    data["decisoes_por_passo"] = passos
    data["decisoes_por_subpasso"] = subpassos


def fix_meta(data: dict) -> None:
    data["meta"]["modo_execucao"] = "local_auditavel"


def fix_p42_p48_numbers(data: dict) -> None:
    for item in data["decisoes_por_passo"]:
        if item.get("corredor") == "P42_P48":
            passo_id = item.get("passo_id")
            if passo_id in P42_P48_NUMEROS_FINAIS:
                item["numero_final"] = P42_P48_NUMEROS_FINAIS[passo_id]


def fix_arbitration_substep_refs(data: dict) -> None:
    subpassos_por_corredor = collections.defaultdict(set)
    for item in data["decisoes_por_subpasso"]:
        subpassos_por_corredor[item["corredor"]].add(item["subpasso_id"])

    for arb in data["arbitragens_de_corredor"]:
        existentes = subpassos_por_corredor[arb["corredor"]]

        arb["decisoes_por_subpasso_referenciadas"] = [
            sid for sid in arb.get("decisoes_por_subpasso_referenciadas", [])
            if sid in existentes
        ]

        arb["subpassos_aprovados"] = [
            sid for sid in arb.get("subpassos_aprovados", [])
            if sid in existentes
        ]


def normalize_sources(data: dict) -> None:
    data["inputs_utilizados"]["inputs_nucleares"] = clean_paths(
        data["inputs_utilizados"].get("inputs_nucleares", []),
        drop_aggregator_refs=False,
    )
    data["inputs_utilizados"]["inputs_secundarios"] = clean_paths(
        data["inputs_utilizados"].get("inputs_secundarios", []),
        drop_aggregator_refs=False,
    )

    for section in ("decisoes_por_passo", "decisoes_por_subpasso", "arbitragens_de_corredor"):
        for item in data.get(section, []):
            if "fontes_utilizadas" in item:
                item["fontes_utilizadas"] = clean_paths(
                    item.get("fontes_utilizadas", []),
                    drop_aggregator_refs=True,
                )


def recompute_summary(data: dict) -> None:
    passos = data["decisoes_por_passo"]
    subpassos = data["decisoes_por_subpasso"]
    arbitragens = data["arbitragens_de_corredor"]

    passos_estado = collections.Counter(item.get("estado_final_do_passo") for item in passos)
    sub_estado = collections.Counter(item.get("decisao_subpasso") for item in subpassos)
    corr_estado = collections.Counter(item.get("estado_final_do_corredor") for item in arbitragens)

    data["resumo"] = {
        "total_decisoes_por_passo": len(passos),
        "total_decisoes_por_subpasso": len(subpassos),
        "total_arbitragens_de_corredor": len(arbitragens),
        "passos_fechados": passos_estado.get("fechado", 0),
        "passos_quase_fechados": passos_estado.get("quase_fechado", 0),
        "passos_abertos": passos_estado.get("aberto", 0),
        "subpassos_aprovados": sub_estado.get("aprovado", 0),
        "subpassos_rejeitados": sub_estado.get("rejeitado", 0),
        "subpassos_adiados": sub_estado.get("adiado", 0),
        "corredores_fechados": corr_estado.get("fechado", 0),
        "corredores_parciais": corr_estado.get("parcial", 0),
        "corredores_para_reabrir": corr_estado.get("reabrir", 0),
    }


def validate_output(data: dict, schema_dir: str) -> None:
    schema_name = "schema_decisoes_canonicas_intermedias.json"
    schema_dir_path = Path(schema_dir).resolve()
    schema_path = schema_dir_path / schema_name

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    base_uri = schema_dir_path.as_uri() + "/"
    resolver = RefResolver(base_uri=base_uri, referrer=schema)
    Draft202012Validator(schema, resolver=resolver).validate(data)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Ficheiro agregador de entrada")
    parser.add_argument("--output", required=True, help="Ficheiro consolidado de saída")
    parser.add_argument("--schema-dir", required=True, help="Diretório dos schemas")
    args = parser.parse_args()

    data = load_json(args.input)

    split_step_and_substep_records(data)
    fix_meta(data)
    fix_arbitration_substep_refs(data)
    fix_p42_p48_numbers(data)
    normalize_sources(data)
    recompute_summary(data)
    validate_output(data, args.schema_dir)
    dump_json(args.output, data)

    print("OK: patch aplicado e ficheiro validado contra os schemas.")
    print(f"Saída: {args.output}")
    print("Resumo:")
    print(json.dumps(data["resumo"], ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
