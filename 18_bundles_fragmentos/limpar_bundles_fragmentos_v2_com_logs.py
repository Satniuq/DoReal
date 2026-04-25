#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SCRIPT_NAME = "limpar_bundles_fragmentos_v2.py"
SCHEMA_VERSION = "2.1.0"
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4")
DEFAULT_INPUT_CANDIDATES = [
    Path("output") / "lote_bundles_fragmentos.json",
    Path("output") / "manifesto_lote.json",
]
DEFAULT_OUTPUT_DIRNAME = "limpeza_output"
DEFAULT_ENV_FILENAMES = [".env", ".env.local"]


class ScriptError(Exception):
    pass


def terminal_log(message: str) -> None:
    print(message, flush=True)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_simple_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return values

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export "):].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        values[key] = value

    return values


def candidate_env_paths(script_dir: Path, bundles_json: Optional[Path] = None) -> List[Path]:
    candidates: List[Path] = []
    seen = set()

    roots = [script_dir, *script_dir.parents]
    if bundles_json is not None:
        roots.extend([bundles_json.parent, *bundles_json.parent.parents])

    for root in roots:
        for name in DEFAULT_ENV_FILENAMES:
            p = (root / name).resolve()
            if p not in seen:
                seen.add(p)
                candidates.append(p)

    return candidates


def load_env_if_possible(script_dir: Path, bundles_json: Optional[Path] = None) -> Optional[Path]:
    if os.environ.get("OPENAI_API_KEY"):
        return None

    try:
        from dotenv import load_dotenv  # type: ignore

        for path in candidate_env_paths(script_dir, bundles_json):
            if path.exists() and path.is_file():
                load_dotenv(path, override=False)
                if os.environ.get("OPENAI_API_KEY"):
                    return path
    except Exception:
        pass

    for path in candidate_env_paths(script_dir, bundles_json):
        if not path.exists() or not path.is_file():
            continue
        parsed = parse_simple_env_file(path)
        if parsed.get("OPENAI_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = parsed["OPENAI_API_KEY"]
            return path

    return None


def detect_api_key_source(script_dir: Path, bundles_json: Optional[Path] = None) -> Tuple[Optional[str], Optional[Path]]:
    if os.environ.get("OPENAI_API_KEY"):
        return "environment", None

    loaded_from = load_env_if_possible(script_dir, bundles_json)
    if os.environ.get("OPENAI_API_KEY"):
        return ("dotenv_file", loaded_from) if loaded_from else ("environment", None)

    return None, None


def mask_secret(value: Optional[str]) -> str:
    if not value:
        return ""
    if len(value) <= 10:
        return "*" * len(value)
    return value[:7] + "…" + value[-4:]


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


def normalize_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def preview(text: str, limit: int = 500) -> str:
    text = normalize_ws(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consome bundles de fragmentos e produz limpeza por API em regimes distintos."
    )
    parser.add_argument(
        "--bundles-json",
        help="Caminho para lote_bundles_fragmentos.json. Se omitido, procura em ./output/.",
    )
    parser.add_argument(
        "--output-dir",
        help="Diretório de saída. Default: ./limpeza_output junto do script.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Modelo a usar na Responses API. Default: OPENAI_MODEL ou gpt-5.4",
    )
    parser.add_argument(
        "--only-state",
        action="append",
        choices=["limpavel", "limpavel_com_cautela", "so_auditoria"],
        help="Processa apenas bundles com estes estados. Pode repetir.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        help="Limite máximo de bundles a processar.",
    )
    parser.add_argument(
        "--fragment-id",
        action="append",
        help="Processa apenas estes fragment_ids. Pode repetir e aceitar CSV simples.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Não chama API; só materializa prompts e payloads.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Reprocessa fragmentos já existentes na saída.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Espera entre chamadas de API.",
    )
    parser.add_argument(
        "--print-paths",
        action="store_true",
        help="Imprime os caminhos resolvidos e continua.",
    )
    return parser.parse_args()


def resolve_bundles_json(script_dir: Path, explicit: Optional[str]) -> Path:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.exists():
            raise ScriptError(f"Ficheiro de bundles não existe: {p}")
        return p

    for rel in DEFAULT_INPUT_CANDIDATES:
        candidate = (script_dir / rel).resolve()
        if candidate.exists() and candidate.name == "lote_bundles_fragmentos.json":
            return candidate

    alt = sorted(script_dir.rglob("lote_bundles_fragmentos.json"))
    if alt:
        return alt[0].resolve()

    raise ScriptError(
        "Não encontrei lote_bundles_fragmentos.json. Usa --bundles-json ou garante ./output/lote_bundles_fragmentos.json."
    )


def resolve_output_dir(script_dir: Path, explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (script_dir / DEFAULT_OUTPUT_DIRNAME).resolve()


def extract_selection_ids(raw_values: Optional[List[str]]) -> List[str]:
    if not raw_values:
        return []

    out: List[str] = []
    seen = set()
    for raw in raw_values:
        for part in raw.split(","):
            frag = part.strip()
            if frag and frag not in seen:
                seen.add(frag)
                out.append(frag)
    return out


def load_bundles_from_lote(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ScriptError("O ficheiro de lote tem de ser um objeto JSON.")

    bundles = payload.get("bundles")
    manifesto = payload.get("manifesto_resumido", {})

    if not isinstance(bundles, list):
        raise ScriptError("O lote não contém uma lista 'bundles'.")

    return manifesto, bundles


def select_bundles(
    bundles: List[Dict[str, Any]],
    only_states: Optional[List[str]],
    fragment_ids: List[str],
    max_items: Optional[int],
) -> List[Dict[str, Any]]:
    selected = []
    ids_filter = set(fragment_ids) if fragment_ids else None
    states_filter = set(only_states) if only_states else {"limpavel", "limpavel_com_cautela"}

    for bundle in bundles:
        frag_id = (((bundle or {}).get("identificacao") or {}).get("fragment_id"))
        state = (((bundle or {}).get("bundle_runtime") or {}).get("estado_bundle"))

        if ids_filter is not None and frag_id not in ids_filter:
            continue
        if states_filter and state not in states_filter:
            continue

        selected.append(bundle)

    if max_items is not None:
        selected = selected[:max_items]

    return selected


def local_context_text(bundle: Dict[str, Any]) -> str:
    ctx = bundle.get("contexto_local_imediato") or {}
    parts: List[str] = []

    if ctx.get("continuidade_ativa"):
        ant = ctx.get("fragmento_anterior")
        seg = ctx.get("fragmento_seguinte")

        if isinstance(ant, dict):
            parts.append(
                "Fragmento anterior:\n"
                f"- id: {ant.get('fragment_id')}\n"
                f"- tema: {ant.get('tema_dominante_provisorio')}\n"
                f"- preview: {ant.get('texto_preview')}"
            )

        if isinstance(seg, dict):
            parts.append(
                "Fragmento seguinte:\n"
                f"- id: {seg.get('fragment_id')}\n"
                f"- tema: {seg.get('tema_dominante_provisorio')}\n"
                f"- preview: {seg.get('texto_preview')}"
            )

    return "\n\n".join(parts).strip()


def build_regime_prompt(bundle: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    ident = bundle.get("identificacao") or {}
    unidade = bundle.get("unidade_base") or {}
    runtime = bundle.get("bundle_runtime") or {}
    instr = bundle.get("instrucao_de_limpeza_minima") or {}
    seg = unidade.get("segmentacao") or {}
    texto_principal = unidade.get("texto_principal") or ""
    contexto_local = local_context_text(bundle)
    estado = runtime.get("estado_bundle")
    motivos = runtime.get("motivos_estado") or []
    regime = "direto" if estado == "limpavel" else "cautela"

    system = (
        "Tu limpas fragmentos filosóficos do projeto DoReal sem acrescentar conteúdo novo, "
        "sem subir a altitude filosófica e sem alterar a tese local. "
        "Preserva a voz autoral, a ordem argumentativa local quando ela exista, "
        "e limita-te a tornar o texto mais claro, coeso e utilizável. "
        "Responde apenas em JSON válido."
    )

    common_rules = [
        "Não introduzir exemplos novos.",
        "Não corrigir a filosofia para outra filosofia.",
        "Não resumir em vez de limpar.",
        "Não transformar em ensaio académico.",
        "Remover oralidade redundante, hesitações e repetições inúteis só quando isso não altera o conteúdo.",
        "Preservar o léxico importante do fragmento.",
        "Se houver elipses ou cortes, reconstruir apenas o mínimo necessário para a legibilidade sem inventar teses novas.",
        "Se o fragmento estiver realmente partido, assinalar cautela em vez de compensar com invenção.",
    ]

    if regime == "direto":
        extra = [
            "Aqui podes reordenar localmente frases curtas e corrigir sintaxe para obter uma formulação limpa.",
            "Mantém a agressividade crítica quando ela fizer parte do conteúdo, mas remove apenas ruído de oralidade.",
        ]
    else:
        extra = [
            "Aqui tens de ser conservador.",
            "Preserva mais da ordem original.",
            "Não feches lacunas argumentativas com conteúdo novo.",
            "Se houver contexto local ativo, usa-o apenas para evitar truncação e não para fundir fragmentos.",
            "Se o texto permanecer parcial após limpeza, assinala isso em 'notas_cautela'.",
        ]

    request = {
        "fragment_id": ident.get("fragment_id"),
        "estado_origem": estado,
        "regime_limpeza": regime,
        "origem_id": ident.get("origem_id"),
        "header_original": ident.get("header_original"),
        "tipo_material_fonte": ident.get("tipo_material_fonte"),
        "tipo_unidade": seg.get("tipo_unidade"),
        "tema_dominante_provisorio": unidade.get("tema_dominante_provisorio"),
        "motivos_estado": motivos,
        "instrucao_bundle": instr,
        "regras_gerais": common_rules + extra,
        "texto_a_limpar": texto_principal,
        "contexto_local": contexto_local or None,
        "formato_de_saida": {
            "fragment_id": "string",
            "estado_origem": "string",
            "regime_limpeza": "string",
            "texto_limpo": "string",
            "resumo_alteracoes": ["string"],
            "notas_cautela": ["string"],
            "preservou_ordem_argumentativa_local": "boolean",
            "sinalizar_revisao_humana": "boolean",
        },
    }

    user = (
        "Limpa o fragmento abaixo e devolve apenas JSON válido com exatamente estes campos:\n"
        "{\n"
        '  "fragment_id": string,\n'
        '  "estado_origem": string,\n'
        '  "regime_limpeza": string,\n'
        '  "texto_limpo": string,\n'
        '  "resumo_alteracoes": [string],\n'
        '  "notas_cautela": [string],\n'
        '  "preservou_ordem_argumentativa_local": boolean,\n'
        '  "sinalizar_revisao_humana": boolean\n'
        "}\n\n"
        "Payload do fragmento:\n"
        + json.dumps(request, ensure_ascii=False, indent=2)
    )

    return system, user, request


def extract_json_from_response(text: str) -> Dict[str, Any]:
    raw = text.strip()
    if not raw:
        raise ScriptError("Resposta vazia da API.")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, flags=re.S)
    if fenced:
        return json.loads(fenced.group(1))

    first = raw.find("{")
    last = raw.rfind("}")
    if first != -1 and last != -1 and last > first:
        return json.loads(raw[first:last + 1])

    raise ScriptError("Não foi possível extrair JSON da resposta do modelo.")


def call_openai_responses(model: str, system: str, user: str, script_dir: Path, bundles_json: Path) -> Tuple[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ScriptError("Pacote 'openai' não instalado. Executa: pip install openai") from exc

    _key_source, _loaded_path = detect_api_key_source(script_dir, bundles_json)
    if not os.environ.get("OPENAI_API_KEY"):
        searched = [str(p) for p in candidate_env_paths(script_dir, bundles_json) if p.exists()]
        extra = f" Ficheiros .env encontrados: {searched}" if searched else " Nenhum .env candidato encontrado."
        raise ScriptError("OPENAI_API_KEY não está disponível para o processo." + extra)

    client = OpenAI()
    response = client.responses.create(
        model=model,
        instructions=system,
        input=user,
    )
    output_text = getattr(response, "output_text", None)
    if not output_text:
        output_text = str(response)
    return output_text, response


def build_report(
    processed: List[Dict[str, Any]],
    skipped: List[Dict[str, Any]],
    errors: List[Dict[str, Any]],
    dry_run: bool,
    model: str,
    bundles_json: Path,
    output_dir: Path,
) -> str:
    def count_by(key: str, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for row in rows:
            value = row.get(key) or ""
            counts[value] = counts.get(value, 0) + 1
        return counts

    regime_counts = count_by("regime_limpeza", processed)
    lines = [
        "# RELATÓRIO — limpeza de bundles v2",
        "",
        f"- Gerado em: `{now_utc_iso()}`",
        f"- Script: `{SCRIPT_NAME}`",
        f"- Modo: `{'dry-run' if dry_run else 'api'}`",
        f"- Modelo: `{model}`",
        f"- Lote de entrada: `{bundles_json}`",
        f"- Diretório de saída: `{output_dir}`",
        f"- Processados: `{len(processed)}`",
        f"- Saltados: `{len(skipped)}`",
        f"- Erros: `{len(errors)}`",
        "",
        "## Regimes",
        "",
        f"- direto: `{regime_counts.get('direto', 0)}`",
        f"- cautela: `{regime_counts.get('cautela', 0)}`",
        "",
        "## Processados",
        "",
        "| fragment_id | estado_origem | regime | resultado |",
        "|---|---|---|---|",
    ]

    for row in processed:
        lines.append(
            f"| {row.get('fragment_id')} | {row.get('estado_origem')} | {row.get('regime_limpeza')} | {row.get('resultado')} |"
        )

    if skipped:
        lines.extend(["", "## Saltados", "", "| fragment_id | motivo |", "|---|---|"])
        for row in skipped:
            lines.append(f"| {row.get('fragment_id')} | {row.get('motivo')} |")

    if errors:
        lines.extend(["", "## Erros", "", "| fragment_id | erro |", "|---|---|"])
        for row in errors:
            lines.append(f"| {row.get('fragment_id')} | {row.get('erro')} |")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    bundles_json = resolve_bundles_json(script_dir, args.bundles_json)
    output_dir = resolve_output_dir(script_dir, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    key_source, loaded_env_path = detect_api_key_source(script_dir, bundles_json)

    if args.print_paths:
        print(json.dumps({
            "script_dir": str(script_dir),
            "bundles_json": str(bundles_json),
            "output_dir": str(output_dir),
            "api_key_disponivel": bool(os.environ.get("OPENAI_API_KEY")),
            "api_key_source": key_source or "nao_detetada",
            "api_key_masked": mask_secret(os.environ.get("OPENAI_API_KEY")),
            "dotenv_carregado_de": str(loaded_env_path) if loaded_env_path else "",
        }, ensure_ascii=False, indent=2))

    manifesto_lote, bundles = load_bundles_from_lote(bundles_json)
    fragment_ids = extract_selection_ids(args.fragment_id)
    selected = select_bundles(
        bundles=bundles,
        only_states=args.only_state,
        fragment_ids=fragment_ids,
        max_items=args.max_items,
    )

    terminal_log(
        f"[INÍCIO] selecionados={len(selected)} | dry_run={args.dry_run} | model={args.model}"
    )

    processed: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    agregados: List[Dict[str, Any]] = []

    per_fragment_dir = output_dir / "fragmentos"
    per_fragment_dir.mkdir(parents=True, exist_ok=True)

    total = len(selected)

    for idx, bundle in enumerate(selected, start=1):
        ident = bundle.get("identificacao") or {}
        runtime = bundle.get("bundle_runtime") or {}
        unidade = bundle.get("unidade_base") or {}

        fragment_id = ident.get("fragment_id")
        estado_origem = runtime.get("estado_bundle")
        tipo_unidade = ((unidade.get("segmentacao") or {}).get("tipo_unidade")) or ""

        terminal_log(
            f"[{idx}/{total}] {fragment_id} | estado={estado_origem} | tipo={tipo_unidade}"
        )

        texto = unidade.get("texto_principal") or ""
        out_json = per_fragment_dir / f"{fragment_id}.limpo.json"
        out_prompt = per_fragment_dir / f"{fragment_id}.prompt.json"

        if out_json.exists() and not args.overwrite:
            skipped.append({"fragment_id": fragment_id, "motivo": "ja_existente"})
            terminal_log(f"  -> SKIP | {fragment_id} | motivo=ja_existente")
            continue

        if not texto:
            skipped.append({"fragment_id": fragment_id, "motivo": "texto_principal_vazio"})
            terminal_log(f"  -> SKIP | {fragment_id} | motivo=texto_principal_vazio")
            continue

        try:
            system, user, prompt_payload = build_regime_prompt(bundle)
            write_json(out_prompt, {
                "fragment_id": fragment_id,
                "system": system,
                "user": user,
                "payload": prompt_payload,
            })

            regime = prompt_payload["regime_limpeza"]

            if args.dry_run:
                terminal_log(f"  -> DRY-RUN | {fragment_id} | regime={regime}")
                cleaned_payload = {
                    "fragment_id": fragment_id,
                    "estado_origem": estado_origem,
                    "regime_limpeza": regime,
                    "texto_limpo": texto,
                    "resumo_alteracoes": [],
                    "notas_cautela": ["dry_run_sem_chamada_api"],
                    "preservou_ordem_argumentativa_local": True,
                    "sinalizar_revisao_humana": regime == "cautela",
                }
                resultado = "dry_run"
                raw_output = None
            else:
                terminal_log(f"  -> API | {fragment_id} | regime={regime} | a chamar...")
                t0 = time.time()

                raw_text, _response_obj = call_openai_responses(
                    model=args.model,
                    system=system,
                    user=user,
                    script_dir=script_dir,
                    bundles_json=bundles_json,
                )

                dt = time.time() - t0
                terminal_log(f"  -> API_OK | {fragment_id} | {dt:.2f}s")

                cleaned_payload = extract_json_from_response(raw_text)
                resultado = "api_ok"
                raw_output = raw_text

            final_payload = {
                "fragment_id": fragment_id,
                "estado_origem": estado_origem,
                "regime_limpeza": regime,
                "resultado": resultado,
                "input_bundle_minimo": {
                    "fragment_id": fragment_id,
                    "estado_origem": estado_origem,
                    "motivos_estado": runtime.get("motivos_estado"),
                    "tipo_unidade": ((unidade.get("segmentacao") or {}).get("tipo_unidade")),
                    "tema_dominante_provisorio": unidade.get("tema_dominante_provisorio"),
                },
                "output_limpeza": cleaned_payload,
                "raw_output_text": raw_output,
                "gerado_em_utc": now_utc_iso(),
                "modelo": args.model,
            }

            write_json(out_json, final_payload)

            processed.append({
                "fragment_id": fragment_id,
                "estado_origem": estado_origem,
                "regime_limpeza": regime,
                "resultado": resultado,
            })
            agregados.append(final_payload)

            terminal_log(
                f"  -> GUARDADO | {fragment_id} | resultado={resultado} | revisao_humana={cleaned_payload.get('sinalizar_revisao_humana')}"
            )

            if not args.dry_run and args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)

        except Exception as exc:
            errors.append({
                "fragment_id": fragment_id,
                "erro": str(exc),
            })
            terminal_log(f"  -> ERRO | {fragment_id} | {exc}")

    write_json(output_dir / "manifesto_limpeza.json", {
        "script": SCRIPT_NAME,
        "schema_version": SCHEMA_VERSION,
        "gerado_em_utc": now_utc_iso(),
        "bundles_json": str(bundles_json),
        "output_dir": str(output_dir),
        "modelo": args.model,
        "dry_run": args.dry_run,
        "api_key_disponivel": bool(os.environ.get("OPENAI_API_KEY")),
        "api_key_source": key_source or "nao_detetada",
        "dotenv_carregado_de": str(loaded_env_path) if loaded_env_path else "",
        "resumo_entrada": manifesto_lote,
        "resumo_execucao": {
            "selecionados": len(selected),
            "processados": len(processed),
            "saltados": len(skipped),
            "erros": len(errors),
        },
    })
    write_json(output_dir / "limpezas_agregadas.json", agregados)
    write_json(output_dir / "saltados.json", skipped)
    write_json(output_dir / "erros_limpeza.json", errors)
    write_text(
        output_dir / "relatorio_limpeza.md",
        build_report(
            processed=processed,
            skipped=skipped,
            errors=errors,
            dry_run=args.dry_run,
            model=args.model,
            bundles_json=bundles_json,
            output_dir=output_dir,
        ),
    )

    terminal_log(
        f"[FIM] processados={len(processed)} | saltados={len(skipped)} | erros={len(errors)}"
    )

    print(json.dumps({
        "selecionados": len(selected),
        "processados": len(processed),
        "saltados": len(skipped),
        "erros": len(errors),
        "output_dir": str(output_dir),
        "dry_run": args.dry_run,
        "model": args.model,
        "api_key_disponivel": bool(os.environ.get("OPENAI_API_KEY")),
        "api_key_source": key_source or "nao_detetada",
        "dotenv_carregado_de": str(loaded_env_path) if loaded_env_path else "",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
