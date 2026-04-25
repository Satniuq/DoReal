#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SCRIPT_NAME = "pos_processar_limpeza_fragmentos_v1.py"
SCHEMA_VERSION = "1.0.0"
DEFAULT_LIMPEZAS_JSON = Path("limpeza_output") / "limpezas_agregadas.json"
DEFAULT_MANIFESTO_LIMPEZA_JSON = Path("limpeza_output") / "manifesto_limpeza.json"
DEFAULT_BUNDLES_JSON = Path("output") / "lote_bundles_fragmentos.json"
DEFAULT_OUTPUT_DIR = Path("corpus_pos_limpeza")


class ScriptError(Exception):
    pass


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_space(value: str) -> str:
    return " ".join((value or "").split()).strip()


def preview(text: str, limit: int = 300) -> str:
    text = normalize_space(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def resolve_path(script_dir: Path, explicit: Optional[str], default_rel: Path, required: bool = True) -> Optional[Path]:
    if explicit:
        path = Path(explicit).expanduser().resolve()
    else:
        path = (script_dir / default_rel).resolve()

    if path.exists():
        return path

    if required:
        raise ScriptError(f"Ficheiro não encontrado: {path}")
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pós-processa as limpezas dos fragmentos, separando aprováveis, revisão humana e auditoria."
    )
    parser.add_argument("--limpezas-json", help="Caminho para limpezas_agregadas.json")
    parser.add_argument("--manifesto-limpeza-json", help="Caminho para manifesto_limpeza.json")
    parser.add_argument("--bundles-json", help="Caminho para lote_bundles_fragmentos.json")
    parser.add_argument("--output-dir", help="Diretório de saída. Default: ./corpus_pos_limpeza")
    parser.add_argument("--print-paths", action="store_true", help="Imprime caminhos resolvidos e continua.")
    return parser.parse_args()


def build_clean_record(item: Dict[str, Any]) -> Dict[str, Any]:
    output = item.get("output_limpeza") or {}
    bundle = item.get("input_bundle_minimo") or {}

    return {
        "fragment_id": item.get("fragment_id"),
        "estado_origem": item.get("estado_origem"),
        "regime_limpeza": item.get("regime_limpeza"),
        "resultado": item.get("resultado"),
        "tipo_unidade": bundle.get("tipo_unidade"),
        "tema_dominante_provisorio": bundle.get("tema_dominante_provisorio"),
        "motivos_estado": bundle.get("motivos_estado") or [],
        "texto_limpo": output.get("texto_limpo") or "",
        "resumo_alteracoes": output.get("resumo_alteracoes") or [],
        "notas_cautela": output.get("notas_cautela") or [],
        "preservou_ordem_argumentativa_local": output.get("preservou_ordem_argumentativa_local"),
        "sinalizar_revisao_humana": bool(output.get("sinalizar_revisao_humana")),
        "modelo": item.get("modelo"),
        "gerado_em_utc": item.get("gerado_em_utc"),
    }


def build_audit_record(bundle: Dict[str, Any]) -> Dict[str, Any]:
    ident = bundle.get("identificacao") or {}
    unidade = bundle.get("unidade_base") or {}
    runtime = bundle.get("bundle_runtime") or {}
    instr = bundle.get("instrucao_de_limpeza_minima") or {}

    texto_principal = unidade.get("texto_principal") or unidade.get("texto_fonte_reconstituido") or unidade.get("texto_fragmento") or ""

    return {
        "fragment_id": ident.get("fragment_id"),
        "estado_origem": runtime.get("estado_bundle"),
        "regime_limpeza": None,
        "resultado": "nao_processado",
        "tipo_unidade": ((unidade.get("segmentacao") or {}).get("tipo_unidade")),
        "tema_dominante_provisorio": unidade.get("tema_dominante_provisorio"),
        "motivos_estado": runtime.get("motivos_estado") or [],
        "texto_base_preview": preview(texto_principal),
        "instrucao_bundle": instr,
        "sinalizar_revisao_humana": True,
    }


def build_not_processed_record(bundle: Dict[str, Any]) -> Dict[str, Any]:
    ident = bundle.get("identificacao") or {}
    unidade = bundle.get("unidade_base") or {}
    runtime = bundle.get("bundle_runtime") or {}

    texto_principal = unidade.get("texto_principal") or unidade.get("texto_fonte_reconstituido") or unidade.get("texto_fragmento") or ""

    return {
        "fragment_id": ident.get("fragment_id"),
        "estado_origem": runtime.get("estado_bundle"),
        "regime_limpeza": None,
        "resultado": "nao_processado",
        "tipo_unidade": ((unidade.get("segmentacao") or {}).get("tipo_unidade")),
        "tema_dominante_provisorio": unidade.get("tema_dominante_provisorio"),
        "motivos_estado": runtime.get("motivos_estado") or [],
        "texto_base_preview": preview(texto_principal),
    }


def render_records_markdown(title: str, records: List[Dict[str, Any]], include_clean_text: bool = True) -> str:
    lines: List[str] = [f"# {title}", ""]
    if not records:
        lines.append("_Sem entradas._")
        lines.append("")
        return "\n".join(lines)

    for rec in records:
        lines.append(f"## {rec.get('fragment_id')}")
        lines.append("")
        lines.append(f"- estado_origem: `{rec.get('estado_origem')}`")
        regime = rec.get("regime_limpeza")
        if regime:
            lines.append(f"- regime_limpeza: `{regime}`")
        if rec.get("tipo_unidade"):
            lines.append(f"- tipo_unidade: `{rec.get('tipo_unidade')}`")
        if rec.get("tema_dominante_provisorio"):
            lines.append(f"- tema_dominante_provisorio: `{rec.get('tema_dominante_provisorio')}`")
        motivos = rec.get("motivos_estado") or []
        if motivos:
            lines.append(f"- motivos_estado: `{', '.join(motivos)}`")
        if "sinalizar_revisao_humana" in rec:
            lines.append(f"- sinalizar_revisao_humana: `{bool(rec.get('sinalizar_revisao_humana'))}`")
        lines.append("")
        if include_clean_text:
            texto = rec.get("texto_limpo") or ""
            if texto:
                lines.append("### Texto limpo")
                lines.append("")
                lines.append(texto)
                lines.append("")
        else:
            texto_prev = rec.get("texto_base_preview") or ""
            if texto_prev:
                lines.append("### Texto base (preview)")
                lines.append("")
                lines.append(texto_prev)
                lines.append("")
        notas = rec.get("notas_cautela") or []
        if notas:
            lines.append("### Notas de cautela")
            lines.append("")
            for nota in notas:
                lines.append(f"- {nota}")
            lines.append("")
        alterações = rec.get("resumo_alteracoes") or []
        if alterações:
            lines.append("### Resumo das alterações")
            lines.append("")
            for alt in alterações:
                lines.append(f"- {alt}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_master_markdown(
    aprovaveis: List[Dict[str, Any]],
    revisao: List[Dict[str, Any]],
    auditoria: List[Dict[str, Any]],
    nao_processados: List[Dict[str, Any]],
    summary: Dict[str, Any],
) -> str:
    lines = [
        "# CORPUS PÓS-LIMPEZA — resumo",
        "",
        f"- Gerado em: `{now_utc_iso()}`",
        f"- Script: `{SCRIPT_NAME}`",
        f"- Entradas limpas: `{summary['total_limpezas']}`",
        f"- Aprováveis: `{summary['aprovaveis']}`",
        f"- Revisão humana: `{summary['revisao_humana']}`",
        f"- Auditoria remanescente: `{summary['auditoria_remanescente']}`",
        f"- Não processados fora da auditoria: `{summary['nao_processados']}`",
        "",
        "## Critério",
        "",
        "- **Aprováveis**: limpezas com `sinalizar_revisao_humana=false`.",
        "- **Revisão humana**: limpezas com `sinalizar_revisao_humana=true`.",
        "- **Auditoria remanescente**: bundles que ficaram em `so_auditoria` e não entraram na limpeza.",
        "- **Não processados**: bundles não limpos e não marcados como `so_auditoria`.",
        "",
        "## Ficheiros gerados",
        "",
        "- `corpus_limpo_todos.json`",
        "- `corpus_limpo_aprovavel.json`",
        "- `corpus_limpo_revisao.json`",
        "- `corpus_auditoria_remanescente.json`",
        "- `corpus_nao_processado.json`",
        "- `corpus_limpo_aprovavel.md`",
        "- `corpus_limpo_revisao.md`",
        "- `corpus_auditoria_remanescente.md`",
        "- `corpus_nao_processado.md`",
        "- `manifesto_pos_limpeza.json`",
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent

    limpezas_json = resolve_path(script_dir, args.limpezas_json, DEFAULT_LIMPEZAS_JSON, required=True)
    manifesto_limpeza_json = resolve_path(script_dir, args.manifesto_limpeza_json, DEFAULT_MANIFESTO_LIMPEZA_JSON, required=False)
    bundles_json = resolve_path(script_dir, args.bundles_json, DEFAULT_BUNDLES_JSON, required=False)
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else (script_dir / DEFAULT_OUTPUT_DIR).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.print_paths:
        print(json.dumps({
            "script_dir": str(script_dir),
            "limpezas_json": str(limpezas_json) if limpezas_json else "",
            "manifesto_limpeza_json": str(manifesto_limpeza_json) if manifesto_limpeza_json else "",
            "bundles_json": str(bundles_json) if bundles_json else "",
            "output_dir": str(output_dir),
        }, ensure_ascii=False, indent=2))

    limpezas_payload = load_json(limpezas_json)
    if not isinstance(limpezas_payload, list):
        raise ScriptError("limpezas_agregadas.json tem de conter uma lista.")

    manifesto_limpeza = load_json(manifesto_limpeza_json) if manifesto_limpeza_json else {}
    bundles_payload = load_json(bundles_json) if bundles_json else {}
    bundles_list = bundles_payload.get("bundles", []) if isinstance(bundles_payload, dict) else []

    cleaned_records = [build_clean_record(item) for item in limpezas_payload]
    cleaned_ids = {rec["fragment_id"] for rec in cleaned_records if rec.get("fragment_id")}

    aprovaveis = [rec for rec in cleaned_records if not rec.get("sinalizar_revisao_humana")]
    revisao = [rec for rec in cleaned_records if rec.get("sinalizar_revisao_humana")]

    auditoria: List[Dict[str, Any]] = []
    nao_processados: List[Dict[str, Any]] = []

    if bundles_list:
        for bundle in bundles_list:
            ident = bundle.get("identificacao") or {}
            runtime = bundle.get("bundle_runtime") or {}
            fragment_id = ident.get("fragment_id")
            estado = runtime.get("estado_bundle")

            if fragment_id in cleaned_ids:
                continue
            if estado == "so_auditoria":
                auditoria.append(build_audit_record(bundle))
            else:
                nao_processados.append(build_not_processed_record(bundle))

    aprovaveis.sort(key=lambda x: x.get("fragment_id") or "")
    revisao.sort(key=lambda x: x.get("fragment_id") or "")
    auditoria.sort(key=lambda x: x.get("fragment_id") or "")
    nao_processados.sort(key=lambda x: x.get("fragment_id") or "")
    cleaned_records.sort(key=lambda x: x.get("fragment_id") or "")

    counts = {
        "total_limpezas": len(cleaned_records),
        "aprovaveis": len(aprovaveis),
        "revisao_humana": len(revisao),
        "auditoria_remanescente": len(auditoria),
        "nao_processados": len(nao_processados),
        "por_estado_origem": dict(Counter(rec.get("estado_origem") for rec in cleaned_records)),
        "por_regime_limpeza": dict(Counter(rec.get("regime_limpeza") for rec in cleaned_records)),
        "por_tipo_unidade": dict(Counter(rec.get("tipo_unidade") for rec in cleaned_records)),
    }

    manifesto = {
        "script": SCRIPT_NAME,
        "schema_version": SCHEMA_VERSION,
        "gerado_em_utc": now_utc_iso(),
        "fontes": {
            "limpezas_json": str(limpezas_json) if limpezas_json else "",
            "manifesto_limpeza_json": str(manifesto_limpeza_json) if manifesto_limpeza_json else "",
            "bundles_json": str(bundles_json) if bundles_json else "",
        },
        "resumo_limpeza_original": manifesto_limpeza.get("resumo_execucao") if isinstance(manifesto_limpeza, dict) else {},
        "contagens": counts,
    }

    write_json(output_dir / "manifesto_pos_limpeza.json", manifesto)
    write_json(output_dir / "corpus_limpo_todos.json", cleaned_records)
    write_json(output_dir / "corpus_limpo_aprovavel.json", aprovaveis)
    write_json(output_dir / "corpus_limpo_revisao.json", revisao)
    write_json(output_dir / "corpus_auditoria_remanescente.json", auditoria)
    write_json(output_dir / "corpus_nao_processado.json", nao_processados)

    write_text(output_dir / "README_corpus_pos_limpeza.md", render_master_markdown(aprovaveis, revisao, auditoria, nao_processados, counts))
    write_text(output_dir / "corpus_limpo_aprovavel.md", render_records_markdown("CORPUS LIMPO — aprováveis", aprovaveis, include_clean_text=True))
    write_text(output_dir / "corpus_limpo_revisao.md", render_records_markdown("CORPUS LIMPO — revisão humana", revisao, include_clean_text=True))
    write_text(output_dir / "corpus_auditoria_remanescente.md", render_records_markdown("CORPUS — auditoria remanescente", auditoria, include_clean_text=False))
    write_text(output_dir / "corpus_nao_processado.md", render_records_markdown("CORPUS — não processado", nao_processados, include_clean_text=False))

    print(json.dumps({
        "output_dir": str(output_dir),
        "total_limpezas": counts["total_limpezas"],
        "aprovaveis": counts["aprovaveis"],
        "revisao_humana": counts["revisao_humana"],
        "auditoria_remanescente": counts["auditoria_remanescente"],
        "nao_processados": counts["nao_processados"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScriptError as exc:
        print(json.dumps({"erro": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
