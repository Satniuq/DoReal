#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_NAME = "gerar_bundles_fragmentos_v1.py"
SCHEMA_VERSION = "1.1.0"
DIVERGENCE_THRESHOLD = 0.96
PREVIEW_LIMIT = 420

HEADING_RE = re.compile(r"^##\s+(F\d{4})(?:\s+—\s+(.+))?\s*$", re.MULTILINE)
BASE_CONTAINER_RE = re.compile(r"^(F\d{4})")

AUTHOR_TAGS = {
    "autor",
    "resposta do autor",
    "resposta autor",
    "questao do autor",
    "questão do autor",
}

CANONICAL_SEG_PATHS = [
    Path("13_Meta_Indice") / "cadência" / "01_segmentar_fragmentos" / "fragmentos_resegmentados.json",
    Path("13_Meta_Indice") / "cadencia" / "01_segmentar_fragmentos" / "fragmentos_resegmentados.json",
    Path("02_bruto") / "fragmentos_resegmentados.json",
    Path("fragmentos_resegmentados.json"),
]

CANONICAL_BRUTO_PATHS = {
    "fragmentos_md": [
        Path("02_bruto") / "fragmentos.md",
        Path("fragmentos.md"),
    ],
    "fragmentos_nao_processados": [
        Path("02_bruto") / "fragmentos_nao_processados.md",
        Path("fragmentos_nao_processados.md"),
    ],
    "fragmentos_ja_processados": [
        Path("02_bruto") / "fragmentos_ja_processados.md",
        Path("fragmentos_ja_processados.md"),
    ],
}


class BundleError(Exception):
    """Erro recuperável/diagnosticável na montagem de um bundle."""


@dataclass
class SelectionConfig:
    all_items: bool
    ids: List[str]
    max_items: Optional[int]


@dataclass
class RuntimeConfig:
    modo_dialogo: str
    incluir_contexto_local: bool
    modo_falha: str


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def is_blank(value: Optional[str]) -> bool:
    return not (value and str(value).strip())


def get_nested(payload: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def normalize_label(value: str) -> str:
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return normalize_space(value.lower())


def similarity_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_space(a), normalize_space(b)).ratio()


def is_divergence_relevant(a: str, b: str, threshold: float = DIVERGENCE_THRESHOLD) -> bool:
    if is_blank(a) or is_blank(b):
        return False
    return similarity_ratio(a, b) < threshold


def preview(text: str, limit: int = PREVIEW_LIMIT) -> str:
    text = normalize_space(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def base_container_id_from_origin_id(origin_id: Optional[str]) -> Optional[str]:
    if is_blank(origin_id):
        return None
    match = BASE_CONTAINER_RE.match(str(origin_id).strip())
    return match.group(1) if match else None


def parse_fragmentos_md(text: str) -> Dict[str, Dict[str, Any]]:
    containers: Dict[str, Dict[str, Any]] = {}
    matches = list(HEADING_RE.finditer(text))
    for idx, match in enumerate(matches):
        base_id = match.group(1)
        date = match.group(2)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        containers[base_id] = {
            "base_container_id": base_id,
            "header": match.group(0).strip(),
            "data": date,
            "texto_container": body,
            "hash_texto_container": sha256_text(body),
        }
    return containers


def extract_author_blocks(text: str) -> Optional[str]:
    tag_line_re = re.compile(r"(?m)^\[(?P<tag>[^\]\n]+)\]\s*$")
    matches = list(tag_line_re.finditer(text))
    if not matches:
        return None

    blocks: List[str] = []
    for idx, match in enumerate(matches):
        tag_original = match.group("tag").strip()
        tag_normalized = normalize_label(tag_original)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if tag_normalized in AUTHOR_TAGS and not is_blank(body):
            blocks.append(f"[{tag_original}]\n{body}".strip())

    if not blocks:
        return None
    return "\n\n".join(blocks).strip()


def choose_primary_text(fragment: Dict[str, Any], modo_dialogo: str) -> Tuple[str, str, bool, List[str]]:
    reasons: List[str] = []
    text_reconstructed = str(fragment.get("texto_fonte_reconstituido") or "")
    text_fragment = str(fragment.get("texto_fragmento") or "")
    text_normalized = str(fragment.get("texto_normalizado") or "")

    if not is_blank(text_reconstructed):
        base_text = text_reconstructed
        source = "texto_fonte_reconstituido"
    elif not is_blank(text_fragment):
        base_text = text_fragment
        source = "texto_fragmento"
        reasons.append("fallback_para_texto_fragmento")
    elif not is_blank(text_normalized):
        base_text = text_normalized
        source = "texto_normalizado"
        reasons.append("fallback_para_texto_normalizado")
    else:
        return "", "sem_texto", False, ["sem_texto_utilizavel"]

    tipo_material = str(fragment.get("tipo_material_fonte") or "")
    if tipo_material != "dialogo_com_ia":
        return base_text, source, False, reasons

    if modo_dialogo == "manter_dialogo":
        reasons.append("dialogo_mantido_integralmente")
        return base_text, source, False, reasons

    if modo_dialogo == "marcar_para_auditoria":
        return "", "dialogo_marcado_para_auditoria", True, ["dialogo_com_ia_marcado_para_auditoria"]

    extracted = extract_author_blocks(base_text)
    if extracted and not is_blank(extracted):
        reasons.append("voz_autor_extraida")
        return extracted, "texto_autor_extraido", False, reasons

    return "", "dialogo_nao_separavel", True, ["dialogo_com_ia_sem_voz_autor_separavel"]


def build_local_context(
    fragment: Dict[str, Any],
    fragments_index: Dict[str, Dict[str, Any]],
    include_context: bool,
) -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "continuidade_ativa": False,
        "fragmento_anterior": None,
        "fragmento_seguinte": None,
    }
    if not include_context:
        return context

    rel = fragment.get("relacoes_locais") or {}
    prev_id = rel.get("fragmento_anterior")
    next_id = rel.get("fragmento_seguinte")
    continues_prev = bool(rel.get("continua_anterior"))
    prepares_next = bool(rel.get("prepara_seguinte"))
    active = continues_prev or prepares_next
    context["continuidade_ativa"] = active

    def make_neighbor_payload(neighbor_id: str) -> Optional[Dict[str, Any]]:
        if not neighbor_id:
            return None
        neighbor = fragments_index.get(neighbor_id)
        if not neighbor:
            return {
                "fragment_id": neighbor_id,
                "encontrado": False,
            }
        text = str(neighbor.get("texto_fonte_reconstituido") or neighbor.get("texto_fragmento") or neighbor.get("texto_normalizado") or "")
        return {
            "fragment_id": neighbor.get("fragment_id"),
            "encontrado": True,
            "tipo_unidade": get_nested(neighbor, "segmentacao", "tipo_unidade"),
            "funcao_textual_dominante": neighbor.get("funcao_textual_dominante"),
            "tema_dominante_provisorio": neighbor.get("tema_dominante_provisorio"),
            "texto_preview": preview(text),
        }

    if active and prev_id:
        context["fragmento_anterior"] = make_neighbor_payload(prev_id)
    if active and next_id:
        context["fragmento_seguinte"] = make_neighbor_payload(next_id)

    return context


def infer_modo_limpeza(fragment: Dict[str, Any], text_source: str) -> str:
    tipo_unidade = str(get_nested(fragment, "segmentacao", "tipo_unidade", default="") or "")
    tipo_material = str(fragment.get("tipo_material_fonte") or "")

    if tipo_material == "dialogo_com_ia" or text_source == "texto_autor_extraido":
        return "separacao_de_vozes"
    if tipo_unidade == "afirmacao_curta":
        return "minima"
    if tipo_unidade in {"distincao_conceptual", "resposta_local"}:
        return "conservadora"
    if tipo_unidade in {"sequencia_argumentativa", "desenvolvimento_medio", "desenvolvimento_curto"}:
        return "estrutural"
    if tipo_unidade == "fragmento_intuitivo":
        return "sintatica_local"
    return "conservadora"


def build_cleaning_instruction(
    fragment: Dict[str, Any],
    text_source: str,
    estado_bundle: str,
    runtime_reasons: List[str],
) -> Dict[str, Any]:
    tipo_unidade = str(get_nested(fragment, "segmentacao", "tipo_unidade", default="") or "")
    tipo_material = str(fragment.get("tipo_material_fonte") or "")

    observations: List[str] = []
    if bool(get_nested(fragment, "segmentacao", "houve_corte_interno", default=False)):
        observations.append("fragmento_com_corte_interno")
    if bool(get_nested(fragment, "segmentacao", "houve_fusao_de_paragrafos", default=False)):
        observations.append("fragmento_com_fusao_de_paragrafos")
    if bool(get_nested(fragment, "sinalizador_para_cadencia", "requer_revisao_manual_prioritaria", default=False)):
        observations.append("revisao_manual_prioritaria_sinalizada")
    observations.extend(runtime_reasons)

    return {
        "modo_limpeza": infer_modo_limpeza(fragment, text_source),
        "preservar_voz_autoral": tipo_material != "dialogo_com_ia" or text_source == "texto_autor_extraido",
        "preservar_ordem_argumentativa_local": tipo_unidade in {"sequencia_argumentativa", "desenvolvimento_medio", "desenvolvimento_curto"},
        "nao_subir_altitude_filosofica": True,
        "nao_introduzir_conteudo_novo": True,
        "nao_unificar_vozes_distintas": True,
        "tratar_oralidade": True,
        "tratar_repeticao": True,
        "tratar_cortes_e_elipses": True,
        "observacoes_especificas": sorted(set(observations)),
        "estado_bundle_destino": estado_bundle,
    }


def determine_bundle_state(
    fragment: Dict[str, Any],
    join_ok: bool,
    primary_text: str,
    dialog_needs_audit: bool,
    divergence_relevant: bool,
    local_context: Dict[str, Any],
) -> Tuple[str, List[str]]:
    reasons: List[str] = []

    if not join_ok:
        return "so_auditoria", ["join_origem_incompleto"]
    if dialog_needs_audit:
        return "so_auditoria", ["dialogo_com_ia_nao_separavel"]
    if is_blank(primary_text):
        return "so_auditoria", ["texto_principal_vazio"]

    if divergence_relevant:
        reasons.append("divergencia_textual_relevante")

    if bool(get_nested(fragment, "sinalizador_para_cadencia", "requer_revisao_manual_prioritaria", default=False)):
        reasons.append("revisao_manual_prioritaria")

    if not bool(get_nested(fragment, "sinalizador_para_cadencia", "pronto_para_extrator_cadencia", default=False)):
        reasons.append("nao_pronto_para_extrator_cadencia")

    integridade = str(get_nested(fragment, "integridade_semantica", "grau", default="") or "").lower()
    if integridade in {"baixo", "muito_baixo"}:
        reasons.append("integridade_semantica_baixa")

    confianca = str(fragment.get("confianca_segmentacao") or "").lower()
    if confianca == "baixa":
        reasons.append("confianca_segmentacao_baixa")

    if bool(get_nested(fragment, "segmentacao", "houve_fusao_de_paragrafos", default=False)):
        reasons.append("houve_fusao_de_paragrafos")
    if bool(get_nested(fragment, "segmentacao", "houve_corte_interno", default=False)):
        reasons.append("houve_corte_interno")

    if bool(local_context.get("continuidade_ativa")):
        reasons.append("continuidade_local_ativa")

    tipo_material = str(fragment.get("tipo_material_fonte") or "")
    if tipo_material == "dialogo_com_ia":
        reasons.append("material_dialogico_com_ia")

    return ("limpavel_com_cautela", reasons) if reasons else ("limpavel", [])


def build_origin_context(
    fragment: Dict[str, Any],
    containers_index: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Any], bool]:
    origin_id = get_nested(fragment, "origem", "origem_id")
    header_original = get_nested(fragment, "origem", "header_original")
    base_container_id = base_container_id_from_origin_id(origin_id)
    container = containers_index.get(base_container_id or "") if base_container_id else None

    join_ok = bool(base_container_id and header_original and container)
    context = {
        "join_origem_resolvido": join_ok,
        "base_container_id": base_container_id,
        "container_origem": None,
    }

    if container:
        context["container_origem"] = {
            "base_container_id": container["base_container_id"],
            "header": container["header"],
            "data": container["data"],
            "texto_container": container["texto_container"],
            "texto_container_preview": preview(container["texto_container"]),
            "hash_texto_container": container["hash_texto_container"],
        }

    return context, join_ok


def build_bundle(
    fragment: Dict[str, Any],
    fragments_index: Dict[str, Dict[str, Any]],
    containers_index: Dict[str, Dict[str, Any]],
    runtime: RuntimeConfig,
    source_paths: Dict[str, str],
) -> Dict[str, Any]:
    fragment_id = fragment.get("fragment_id")
    if is_blank(str(fragment_id) if fragment_id is not None else ""):
        raise BundleError("fragmento_sem_fragment_id")

    origin = fragment.get("origem") or {}
    required_origin_fields = {
        "origem_id": origin.get("origem_id"),
        "header_original": origin.get("header_original"),
        "ordem_no_ficheiro": origin.get("ordem_no_ficheiro"),
    }
    missing_origin = [k for k, v in required_origin_fields.items() if v in (None, "")]
    if missing_origin:
        raise BundleError(f"campos_origem_em_falta: {', '.join(missing_origin)}")

    primary_text, text_source, dialog_needs_audit, text_reasons = choose_primary_text(fragment, runtime.modo_dialogo)
    origin_context, join_ok = build_origin_context(fragment, containers_index)
    local_context = build_local_context(fragment, fragments_index, runtime.incluir_contexto_local)

    text_reconstructed = str(fragment.get("texto_fonte_reconstituido") or "")
    text_fragment = str(fragment.get("texto_fragmento") or "")
    divergence_relevant = is_divergence_relevant(text_reconstructed, text_fragment)

    estado_bundle, state_reasons = determine_bundle_state(
        fragment=fragment,
        join_ok=join_ok,
        primary_text=primary_text,
        dialog_needs_audit=dialog_needs_audit,
        divergence_relevant=divergence_relevant,
        local_context=local_context,
    )

    runtime_reasons = list(dict.fromkeys(text_reasons + state_reasons))

    bundle = {
        "identificacao": {
            "fragment_id": fragment_id,
            "origem_id": origin.get("origem_id"),
            "header_original": origin.get("header_original"),
            "ordem_no_ficheiro": origin.get("ordem_no_ficheiro"),
            "base_container_id": origin_context.get("base_container_id"),
            "tipo_material_fonte": fragment.get("tipo_material_fonte"),
        },
        "unidade_base": {
            "origem": origin,
            "tipo_material_fonte": fragment.get("tipo_material_fonte"),
            "texto_fragmento": text_fragment,
            "texto_normalizado": str(fragment.get("texto_normalizado") or ""),
            "texto_fonte_reconstituido": text_reconstructed,
            "texto_principal": primary_text,
            "segmentacao": fragment.get("segmentacao"),
            "funcao_textual_dominante": fragment.get("funcao_textual_dominante"),
            "tema_dominante_provisorio": fragment.get("tema_dominante_provisorio"),
            "conceitos_relevantes_provisorios": fragment.get("conceitos_relevantes_provisorios"),
            "integridade_semantica": fragment.get("integridade_semantica"),
            "confianca_segmentacao": fragment.get("confianca_segmentacao"),
            "relacoes_locais": fragment.get("relacoes_locais"),
            "estado_revisao": fragment.get("estado_revisao"),
            "sinalizador_para_cadencia": fragment.get("sinalizador_para_cadencia"),
            "metadados_segmentador": fragment.get("_metadados_segmentador"),
        },
        "contexto_local_imediato": {
            **origin_context,
            **local_context,
        },
        "bundle_runtime": {
            "texto_principal_escolhido": primary_text,
            "fonte_texto_principal": text_source,
            "estado_bundle": estado_bundle,
            "motivos_estado": runtime_reasons,
            "tem_contexto_local": bool(local_context.get("continuidade_ativa")),
            "modo_dialogo_aplicado": runtime.modo_dialogo if fragment.get("tipo_material_fonte") == "dialogo_com_ia" else None,
            "divergencia_textual_relevante": divergence_relevant,
            "join_origem_resolvido": join_ok,
            "hash_texto_principal": sha256_text(primary_text) if primary_text else None,
            "similaridade_texto_reconstituido_vs_fragmento": round(similarity_ratio(text_reconstructed, text_fragment), 6) if not is_blank(text_reconstructed) and not is_blank(text_fragment) else None,
        },
        "instrucao_de_limpeza_minima": build_cleaning_instruction(fragment, text_source, estado_bundle, runtime_reasons),
        "rastreabilidade": {
            "script": SCRIPT_NAME,
            "schema_version": SCHEMA_VERSION,
            "gerado_em_utc": now_utc_iso(),
            "ficheiros_fonte": source_paths,
            "hashes_textuais": {
                "texto_fragmento": sha256_text(text_fragment) if text_fragment else None,
                "texto_normalizado": sha256_text(str(fragment.get("texto_normalizado") or "")) if str(fragment.get("texto_normalizado") or "") else None,
                "texto_fonte_reconstituido": sha256_text(text_reconstructed) if text_reconstructed else None,
                "texto_principal": sha256_text(primary_text) if primary_text else None,
            },
        },
    }

    return bundle


def parse_ids_file(path: Path) -> List[str]:
    ids: List[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        ids.append(line)
    return ids


def resolve_selection(args: argparse.Namespace, all_ids: List[str]) -> SelectionConfig:
    explicit_ids: List[str] = []
    if args.fragment_id:
        for item in args.fragment_id:
            explicit_ids.extend([part.strip() for part in item.split(",") if part.strip()])
    if args.ids_file:
        explicit_ids.extend(parse_ids_file(Path(args.ids_file)))

    if args.all:
        selected = list(all_ids)
        all_items = True
    else:
        if not explicit_ids:
            raise SystemExit("É obrigatório indicar --all, --fragment-id ou --ids-file.")
        seen = set()
        selected = []
        for frag_id in explicit_ids:
            if frag_id not in seen:
                selected.append(frag_id)
                seen.add(frag_id)
        all_items = False

    if args.max_fragmentos is not None:
        selected = selected[: args.max_fragmentos]

    return SelectionConfig(all_items=all_items, ids=selected, max_items=args.max_fragmentos)


def build_report(
    selection: SelectionConfig,
    counts: Dict[str, int],
    bundles_index: List[Dict[str, Any]],
    errors: List[Dict[str, Any]],
    source_paths: Dict[str, str],
) -> str:
    lines: List[str] = []
    lines.append("# RELATÓRIO — bundles de fragmentos v1")
    lines.append("")
    lines.append(f"- Gerado em: `{now_utc_iso()}`")
    lines.append(f"- Script: `{SCRIPT_NAME}`")
    lines.append(f"- Total selecionados: `{len(selection.ids)}`")
    lines.append(f"- Limpáveis: `{counts.get('limpavel', 0)}`")
    lines.append(f"- Limpáveis com cautela: `{counts.get('limpavel_com_cautela', 0)}`")
    lines.append(f"- Só auditoria: `{counts.get('so_auditoria', 0)}`")
    lines.append(f"- Erros de montagem: `{len(errors)}`")
    lines.append("")
    lines.append("## Fontes")
    lines.append("")
    for key, value in source_paths.items():
        lines.append(f"- **{key}**: `{value}`")
    lines.append("")
    lines.append("## Resumo por fragmento")
    lines.append("")
    lines.append("| fragment_id | estado | tipo_material | tipo_unidade | motivos |")
    lines.append("|---|---|---|---|---|")
    for bundle in bundles_index:
        ident = bundle["identificacao"]
        runtime = bundle["bundle_runtime"]
        unidade = bundle["unidade_base"]
        motivos = ", ".join(runtime.get("motivos_estado") or [])
        lines.append(
            f"| {ident.get('fragment_id')} | {runtime.get('estado_bundle')} | {ident.get('tipo_material_fonte') or ''} | {get_nested(unidade, 'segmentacao', 'tipo_unidade', default='') or ''} | {motivos} |"
        )
    if errors:
        lines.append("")
        lines.append("## Erros")
        lines.append("")
        for err in errors:
            lines.append(f"- `{err.get('fragment_id')}` — {err.get('erro')}")
    return "\n".join(lines).strip() + "\n"


def infer_project_root(explicit: Optional[str], script_dir: Path) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not root.exists():
            raise SystemExit(f"--project-root não existe: {root}")
        return root

    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "02_bruto").exists() and (candidate / "13_Meta_Indice").exists():
            return candidate.resolve()

    raise SystemExit(
        "Não foi possível inferir a raiz do projeto. Usa --project-root "
        "ou coloca o script dentro da árvore DoReal (ex.: DoReal/18_bundles_fragmentos)."
    )


def choose_existing(candidates: List[Path]) -> Optional[Path]:
    for path in candidates:
        if path.exists() and path.is_file():
            return path.resolve()
    return None


def find_latest_run_file(base_dir: Path, pattern: str) -> Optional[Path]:
    if not base_dir.exists():
        return None
    matches = sorted(base_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0].resolve() if matches else None


def autodiscover_fragmentos_resegmentados(project_root: Path) -> Path:
    direct_candidates = [(project_root / rel) for rel in CANONICAL_SEG_PATHS]
    found = choose_existing(direct_candidates)
    if found:
        return found

    bruto_dir = project_root / "02_bruto"
    latest_run = find_latest_run_file(bruto_dir, "fragmentos_resegmentados__*.json")
    if latest_run:
        return latest_run

    recursive_plain = sorted(project_root.rglob("fragmentos_resegmentados.json"))
    if recursive_plain:
        # preferir o que estiver mais perto da cadeia canónica
        recursive_plain.sort(key=lambda p: (
            "13_Meta_Indice" not in str(p),
            len(p.parts),
            str(p),
        ))
        return recursive_plain[0].resolve()

    recursive_run = sorted(project_root.rglob("fragmentos_resegmentados__*.json"))
    if recursive_run:
        recursive_run.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return recursive_run[0].resolve()

    raise SystemExit(
        "Não encontrei `fragmentos_resegmentados.json` nem ficheiro run equivalente. "
        "Usa --fragmentos-resegmentados para indicar o caminho manualmente."
    )


def autodiscover_bruto_file(project_root: Path, key: str) -> Optional[Path]:
    candidates = [(project_root / rel) for rel in CANONICAL_BRUTO_PATHS[key]]
    found = choose_existing(candidates)
    if found:
        return found

    filename = CANONICAL_BRUTO_PATHS[key][-1].name
    recursive = sorted(project_root.rglob(filename))
    if recursive:
        recursive.sort(key=lambda p: (len(p.parts), str(p)))
        return recursive[0].resolve()
    return None


def resolve_source_paths(args: argparse.Namespace, script_dir: Path) -> Tuple[Path, Dict[str, Path], Path]:
    project_root = infer_project_root(args.project_root, script_dir)

    fragmentos_resegmentados = (
        Path(args.fragmentos_resegmentados).expanduser().resolve()
        if args.fragmentos_resegmentados
        else autodiscover_fragmentos_resegmentados(project_root)
    )
    if not fragmentos_resegmentados.exists():
        raise SystemExit(f"Ficheiro de fragmentos resegmentados não existe: {fragmentos_resegmentados}")

    fragmentos_md = (
        Path(args.fragmentos_md).expanduser().resolve()
        if args.fragmentos_md
        else autodiscover_bruto_file(project_root, "fragmentos_md")
    )
    if not fragmentos_md or not fragmentos_md.exists():
        raise SystemExit(
            "Não encontrei `fragmentos.md`. Usa --fragmentos-md ou garante a presença em `02_bruto/fragmentos.md`."
        )

    fragmentos_nao_processados = (
        Path(args.fragmentos_nao_processados).expanduser().resolve()
        if args.fragmentos_nao_processados
        else autodiscover_bruto_file(project_root, "fragmentos_nao_processados")
    )

    fragmentos_ja_processados = (
        Path(args.fragmentos_ja_processados).expanduser().resolve()
        if args.fragmentos_ja_processados
        else autodiscover_bruto_file(project_root, "fragmentos_ja_processados")
    )

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else (script_dir / "output").resolve()
    )

    source_paths = {
        "project_root": project_root,
        "fragmentos_resegmentados": fragmentos_resegmentados,
        "fragmentos_md": fragmentos_md,
        "fragmentos_nao_processados": fragmentos_nao_processados,
        "fragmentos_ja_processados": fragmentos_ja_processados,
    }

    return project_root, source_paths, output_dir


def path_to_display(path: Optional[Path], project_root: Path) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except Exception:
        return str(path.resolve())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera bundles reais de fragmentos para limpeza contextual posterior.",
    )
    parser.add_argument("--project-root", help="Raiz do projeto DoReal. Se omitido, o script tenta inferir a partir da sua própria pasta.")
    parser.add_argument("--fragmentos-resegmentados", help="Override manual para fragmentos_resegmentados.json")
    parser.add_argument("--fragmentos-md", help="Override manual para fragmentos.md")
    parser.add_argument("--fragmentos-nao-processados", help="Override manual para fragmentos_nao_processados.md")
    parser.add_argument("--fragmentos-ja-processados", help="Override manual para fragmentos_ja_processados.md")
    parser.add_argument("--output-dir", help="Diretório de output. Default: ./output dentro da pasta do script")
    parser.add_argument("--print-paths", action="store_true", help="Imprime os caminhos resolvidos e continua")

    parser.add_argument("--fragment-id", action="append", help="ID de fragmento (pode repetir; aceita CSV simples)")
    parser.add_argument("--ids-file", help="Ficheiro com IDs de fragmentos, um por linha")
    parser.add_argument("--all", action="store_true", help="Seleciona todos os fragmentos")
    parser.add_argument("--max-fragmentos", type=int, help="Limite máximo de fragmentos a processar")

    parser.add_argument(
        "--modo-dialogo",
        choices=["manter_dialogo", "extrair_voz_autor", "marcar_para_auditoria"],
        default="extrair_voz_autor",
        help="Política para fragmentos do tipo dialogo_com_ia",
    )
    parser.add_argument(
        "--incluir-contexto-local",
        action="store_true",
        help="Inclui contexto local imediato quando a continuidade está ativa",
    )
    parser.add_argument(
        "--modo-falha",
        choices=["strict", "soft"],
        default="soft",
        help="strict interrompe ao primeiro erro estrutural; soft continua e regista erro",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent

    project_root, resolved_paths, output_dir = resolve_source_paths(args, script_dir)

    if args.print_paths:
        print(json.dumps({
            "project_root": str(project_root),
            "fragmentos_resegmentados": str(resolved_paths["fragmentos_resegmentados"]),
            "fragmentos_md": str(resolved_paths["fragmentos_md"]),
            "fragmentos_nao_processados": str(resolved_paths["fragmentos_nao_processados"]) if resolved_paths["fragmentos_nao_processados"] else "",
            "fragmentos_ja_processados": str(resolved_paths["fragmentos_ja_processados"]) if resolved_paths["fragmentos_ja_processados"] else "",
            "output_dir": str(output_dir),
        }, ensure_ascii=False, indent=2))

    fragments = load_json(resolved_paths["fragmentos_resegmentados"])
    if not isinstance(fragments, list):
        raise SystemExit("fragmentos_resegmentados.json tem de conter uma lista de fragmentos.")

    fragmentos_md_text = load_text(resolved_paths["fragmentos_md"])
    containers_index = parse_fragmentos_md(fragmentos_md_text)

    fragments_index: Dict[str, Dict[str, Any]] = {}
    ordered_ids: List[str] = []
    for item in fragments:
        frag_id = item.get("fragment_id")
        if not frag_id:
            if args.modo_falha == "strict":
                raise SystemExit("Encontrado fragmento sem fragment_id em fragmentos_resegmentados.json")
            continue
        fragments_index[frag_id] = item
        ordered_ids.append(frag_id)

    selection = resolve_selection(args, ordered_ids)
    runtime = RuntimeConfig(
        modo_dialogo=args.modo_dialogo,
        incluir_contexto_local=args.incluir_contexto_local,
        modo_falha=args.modo_falha,
    )

    source_paths_str = {
        "project_root": path_to_display(project_root, project_root),
        "fragmentos_resegmentados": path_to_display(resolved_paths["fragmentos_resegmentados"], project_root),
        "fragmentos_md": path_to_display(resolved_paths["fragmentos_md"], project_root),
        "fragmentos_nao_processados": path_to_display(resolved_paths["fragmentos_nao_processados"], project_root) if resolved_paths["fragmentos_nao_processados"] else "",
        "fragmentos_ja_processados": path_to_display(resolved_paths["fragmentos_ja_processados"], project_root) if resolved_paths["fragmentos_ja_processados"] else "",
        "script_dir": path_to_display(script_dir, project_root),
        "output_dir": path_to_display(output_dir, project_root),
    }

    counts = {"limpavel": 0, "limpavel_com_cautela": 0, "so_auditoria": 0}
    bundles_list: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    per_fragment_dir = output_dir / "bundles" / "fragmentos"
    per_fragment_dir.mkdir(parents=True, exist_ok=True)

    for fragment_id in selection.ids:
        fragment = fragments_index.get(fragment_id)
        if not fragment:
            error = {"fragment_id": fragment_id, "erro": "fragmento_nao_encontrado"}
            errors.append(error)
            if runtime.modo_falha == "strict":
                raise SystemExit(json.dumps(error, ensure_ascii=False))
            continue
        try:
            bundle = build_bundle(
                fragment=fragment,
                fragments_index=fragments_index,
                containers_index=containers_index,
                runtime=runtime,
                source_paths=source_paths_str,
            )
        except BundleError as exc:
            error = {"fragment_id": fragment_id, "erro": str(exc)}
            errors.append(error)
            if runtime.modo_falha == "strict":
                raise SystemExit(json.dumps(error, ensure_ascii=False))
            continue
        except Exception as exc:  # fallback defensivo
            error = {"fragment_id": fragment_id, "erro": f"erro_inesperado: {exc}"}
            errors.append(error)
            if runtime.modo_falha == "strict":
                raise
            continue

        estado = bundle["bundle_runtime"]["estado_bundle"]
        counts[estado] = counts.get(estado, 0) + 1
        bundles_list.append(bundle)
        write_json(per_fragment_dir / f"{fragment_id}.bundle.json", bundle)

    manifest = {
        "script": SCRIPT_NAME,
        "schema_version": SCHEMA_VERSION,
        "gerado_em_utc": now_utc_iso(),
        "fontes": source_paths_str,
        "selecao": {
            "all": selection.all_items,
            "ids": selection.ids,
            "max_fragmentos": selection.max_items,
            "modo_dialogo": runtime.modo_dialogo,
            "incluir_contexto_local": runtime.incluir_contexto_local,
            "modo_falha": runtime.modo_falha,
        },
        "resumo": {
            "total_selecionados": len(selection.ids),
            "bundles_gerados": len(bundles_list),
            "limpavel": counts.get("limpavel", 0),
            "limpavel_com_cautela": counts.get("limpavel_com_cautela", 0),
            "so_auditoria": counts.get("so_auditoria", 0),
            "erros": len(errors),
        },
    }

    lote = {
        "manifesto_resumido": manifest,
        "bundles": bundles_list,
    }

    write_json(output_dir / "manifesto_lote.json", manifest)
    write_json(output_dir / "lote_bundles_fragmentos.json", lote)
    write_json(output_dir / "erros_fragmentos.json", errors)
    write_text(output_dir / "relatorio_lote_fragmentos.md", build_report(selection, counts, bundles_list, errors, source_paths_str))

    print(json.dumps({
        "resumo": manifest["resumo"],
        "output_dir": str(output_dir),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
