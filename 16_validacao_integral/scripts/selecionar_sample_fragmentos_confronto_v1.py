#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
selecionar_sample_fragmentos_confronto_v1.py

Seleciona um sample nuclear de fragmentos a partir de uma base fragmentária
já reaberta por confronto.

Objetivo:
- reduzir centenas de fragmentos a um núcleo manejável (ex.: 10-20);
- privilegiar fragmentos já tratados filosoficamente;
- privilegiar fragmentos com vocabulário e estrutura descritiva fortes;
- gerar um sample utilizável para confrontar o dossier com a base viva.

Input esperado:
- 16_validacao_integral/04_bases_fragmentarias_confrontos/CFxx_base_fragmentaria.json

Outputs:
- 16_validacao_integral/04_bases_fragmentarias_confrontos/samples/CFxx_sample_fragmentos_v1.json
- 16_validacao_integral/04_bases_fragmentarias_confrontos/samples/CFxx_sample_fragmentos_v1.md
- 16_validacao_integral/02_outputs/relatorio_selecao_sample_fragmentos_CFxx_v1.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# CONFIGURAÇÃO CANÓNICA
# =============================================================================

DEFAULT_INPUT_DIR_RELATIVE = Path(
    "16_validacao_integral/04_bases_fragmentarias_confrontos"
)
DEFAULT_OUTPUT_DIR_RELATIVE = Path(
    "16_validacao_integral/04_bases_fragmentarias_confrontos/samples"
)
DEFAULT_OUTPUT_REPORT_DIR_RELATIVE = Path(
    "16_validacao_integral/02_outputs"
)

DEFAULT_KEYWORDS = [
    "campo",
    "escala",
    "local",
    "absolut",
    "continuid",
    "regularidade",
    "rela",
    "media",
    "representa",
    "simbol",
    "linguag",
    "consci",
    "reflex",
    "valid",
    "proje",
    "atualiza",
    "limite",
    "real",
    "erro",
    "crit",
]

DEFAULT_TOP_N = 15


# =============================================================================
# UTILITÁRIOS
# =============================================================================


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_spaces(text: str) -> str:
    return " ".join((text or "").strip().split())


def shorten(text: str, max_len: int = 280) -> str:
    text = normalize_spaces(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def relpath_str(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve())).replace("\\", "/")
    except Exception:
        return str(path.resolve())


def project_root_from_explicit_or_cwd(explicit_root: Optional[Path]) -> Path:
    if explicit_root:
        return explicit_root.resolve()

    script_path = Path(__file__).resolve()
    candidates = [
        script_path.parent.parent.parent,
        script_path.parent.parent,
        Path.cwd(),
        Path.cwd().parent,
        Path.cwd().parent.parent,
    ]

    for cand in candidates:
        cand = cand.resolve()
        if (cand / DEFAULT_INPUT_DIR_RELATIVE).exists():
            return cand
        if (cand / "04_bases_fragmentarias_confrontos").exists() and (cand / "02_outputs").exists():
            return cand.parent.resolve()

    return script_path.parent.parent.parent.resolve()


def resolve_existing_input(project_root: Path, confronto_id: str, explicit_input: Optional[Path]) -> Path:
    if explicit_input:
        p = explicit_input.resolve()
        if not p.exists():
            raise FileNotFoundError(f"Ficheiro não encontrado: {p}")
        return p

    p = (project_root / DEFAULT_INPUT_DIR_RELATIVE / f"{confronto_id}_base_fragmentaria.json").resolve()
    if not p.exists():
        raise FileNotFoundError(f"Base fragmentária não encontrada: {p}")
    return p


def serialize_for_search(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(data)


def keyword_hits(text: str, keywords: Sequence[str]) -> List[str]:
    txt = (text or "").lower()
    hits: List[str] = []
    for kw in keywords:
        if kw.lower() in txt:
            hits.append(kw)
    return hits


def centralidade_score(value: Any) -> int:
    v = normalize_spaces(str(value or "")).lower()
    mapping = {
        "nuclear": 4,
        "alta": 3,
        "medio_alta": 3,
        "média": 2,
        "media": 2,
        "media_alta": 2,
        "baixa": 1,
    }
    return mapping.get(v, 0)


def statuto_score(value: Any) -> int:
    v = normalize_spaces(str(value or "")).lower()
    if "nuclear" in v:
        return 3
    if "estrutural" in v:
        return 2
    if "transicao" in v or "transição" in v:
        return 2
    if "apoio" in v or "suporte" in v:
        return 1
    return 0


def funcao_score(value: Any) -> int:
    v = normalize_spaces(str(value or "")).lower()
    bonus_terms = [
        "crit",
        "objec",
        "objec",
        "distin",
        "defin",
        "tens",
        "problema",
        "transi",
        "media",
        "representa",
        "reflex",
    ]
    return 2 if any(term in v for term in bonus_terms) else 0


# =============================================================================
# LÓGICA DE SCORING
# =============================================================================


def score_fragment(fragment: Dict[str, Any], keywords: Sequence[str]) -> Dict[str, Any]:
    texto = normalize_spaces(fragment.get("texto_fragmento", ""))
    trat = fragment.get("tratamento_filosofico")
    trat_text = serialize_for_search(trat) if trat else ""
    joined_text = f"{texto}\n{trat_text}".lower()

    cad = safe_dict(fragment.get("cadencia"))
    impacto_rows = safe_list(fragment.get("impacto_no_mapa_registos"))
    lig = safe_dict(fragment.get("ligacoes_arvore"))

    hits = keyword_hits(joined_text, keywords)
    proposicoes_impactadas = sorted({row.get("proposicao_id") for row in impacto_rows if row.get("proposicao_id")})

    score = 0
    motivos: List[str] = []

    if trat:
        score += 12
        motivos.append("tratamento_filosofico")

    if texto:
        score += 3
        motivos.append("texto_fragmento")

    if hits:
        score += min(len(hits) * 2, 14)
        motivos.append(f"keywords:{','.join(hits[:8])}")

    cent_score = centralidade_score(cad.get("centralidade"))
    if cent_score:
        score += cent_score
        motivos.append(f"centralidade:{cad.get('centralidade')}")

    estat_score = statuto_score(cad.get("estatuto_no_percurso"))
    if estat_score:
        score += estat_score
        motivos.append(f"estatuto:{cad.get('estatuto_no_percurso')}")

    func_score = funcao_score(fragment.get("funcao_textual_dominante"))
    if func_score:
        score += func_score
        motivos.append(f"funcao:{fragment.get('funcao_textual_dominante')}")

    impacto_bonus = min(len(impacto_rows), 6)
    if impacto_bonus:
        score += impacto_bonus
        motivos.append(f"impacto:{len(impacto_rows)}")

    prop_bonus = min(len(proposicoes_impactadas), 5)
    if prop_bonus:
        score += prop_bonus
        motivos.append(f"proposicoes_impactadas:{len(proposicoes_impactadas)}")

    lig_bonus = 0
    for key in ("microlinha_ids", "ramo_ids", "percurso_ids", "argumento_ids"):
        if safe_list(lig.get(key)):
            lig_bonus += 1
    if lig_bonus:
        score += min(lig_bonus, 4)
        motivos.append(f"ligacoes_arvore:{lig_bonus}")

    # Bonus para padrões linguísticos de distinção/tensão
    text_lower = texto.lower()
    if any(pat in text_lower for pat in ["não é", "mas", "sem", "entre", "ao mesmo tempo", "não autoriza"]):
        score += 2
        motivos.append("estrutura_distintiva")

    return {
        "id": fragment.get("id"),
        "origem_id": fragment.get("origem_id"),
        "score": score,
        "motivos": motivos,
        "hits_keywords": hits,
        "texto_curto": fragment.get("texto_curto") or shorten(texto),
        "texto_fragmento": texto,
        "tratamento_filosofico": trat,
        "cadencia": cad,
        "funcao_textual_dominante": fragment.get("funcao_textual_dominante"),
        "tipo_unidade": fragment.get("tipo_unidade"),
        "ficheiro_origem": fragment.get("ficheiro_origem"),
        "proposicoes_impactadas": proposicoes_impactadas,
        "n_registos_impacto": len(impacto_rows),
        "impacto_no_mapa_registos": impacto_rows,
        "ligacoes_arvore": lig,
        "estado_validacao": fragment.get("estado_validacao"),
    }


# =============================================================================
# CONSTRUÇÃO DE SAÍDAS
# =============================================================================


def build_markdown(
    confronto_id: str,
    base_path: Path,
    project_root: Path,
    payload: Dict[str, Any],
    sample: List[Dict[str, Any]],
    keywords: Sequence[str],
) -> str:
    estat = safe_dict(payload.get("estatisticas"))
    meta = safe_dict(payload.get("meta"))
    snap = safe_dict(payload.get("snapshot_dossier"))

    lines: List[str] = []
    lines.append(f"# {confronto_id} — Sample fragmentário nuclear")
    lines.append("")
    lines.append(f"- gerado_em: `{utc_now_iso()}`")
    lines.append(f"- base_fragmentaria: `{relpath_str(base_path, project_root)}`")
    lines.append(f"- n_fragmentos_base: **{estat.get('n_fragmentos')}**")
    lines.append(f"- n_fragmentos_sample: **{len(sample)}**")
    lines.append(f"- keywords_usadas: `{', '.join(keywords)}`")
    lines.append("")

    if snap:
        lines.append("## Snapshot do dossier")
        lines.append("")
        if snap.get("pergunta_central"):
            lines.append(f"- pergunta_central: {snap.get('pergunta_central')}")
        if snap.get("tese_canonica_provisoria"):
            lines.append(f"- tese_canonica_provisoria: {snap.get('tese_canonica_provisoria')}")
        if snap.get("proposicoes_envolvidas"):
            lines.append(f"- proposicoes_envolvidas: {', '.join(safe_list(snap.get('proposicoes_envolvidas')))}")
        lines.append("")

    lines.append("## Critério de seleção")
    lines.append("")
    lines.append("Sample construído por scoring combinado de:")
    lines.append("- presença de tratamento filosófico;")
    lines.append("- densidade lexical em torno das keywords;")
    lines.append("- centralidade/cadência;")
    lines.append("- impacto no mapa e multiplicidade de proposições impactadas;")
    lines.append("- sinais mínimos de estrutura distintiva no texto.")
    lines.append("")

    lines.append("## Fragmentos selecionados")
    lines.append("")
    for idx, frag in enumerate(sample, 1):
        lines.append(f"### {idx}. {frag.get('id')} (score={frag.get('score')})")
        lines.append("")
        lines.append(f"- origem_id: `{frag.get('origem_id')}`")
        if frag.get("ficheiro_origem"):
            lines.append(f"- ficheiro_origem: `{frag.get('ficheiro_origem')}`")
        if frag.get("tipo_unidade"):
            lines.append(f"- tipo_unidade: `{frag.get('tipo_unidade')}`")
        if frag.get("funcao_textual_dominante"):
            lines.append(f"- funcao_textual_dominante: `{frag.get('funcao_textual_dominante')}`")
        if frag.get("proposicoes_impactadas"):
            lines.append(f"- proposicoes_impactadas: {', '.join(frag.get('proposicoes_impactadas'))}")
        if frag.get("hits_keywords"):
            lines.append(f"- keywords_acionadas: {', '.join(frag.get('hits_keywords'))}")
        if frag.get("motivos"):
            lines.append(f"- motivos_score: {', '.join(frag.get('motivos'))}")
        lines.append("")
        lines.append("#### Texto")
        lines.append("")
        lines.append(frag.get("texto_fragmento") or "[sem texto]")
        lines.append("")
        if frag.get("tratamento_filosofico"):
            lines.append("#### Tratamento filosófico")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(frag.get("tratamento_filosofico"), ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_report(
    confronto_id: str,
    base_path: Path,
    project_root: Path,
    payload: Dict[str, Any],
    sample: List[Dict[str, Any]],
    keywords: Sequence[str],
) -> str:
    estat = safe_dict(payload.get("estatisticas"))
    all_frags = safe_list(payload.get("fragmentos"))

    keyword_counter: Counter[str] = Counter()
    prop_counter: Counter[str] = Counter()
    for frag in sample:
        keyword_counter.update(safe_list(frag.get("hits_keywords")))
        prop_counter.update(safe_list(frag.get("proposicoes_impactadas")))

    lines: List[str] = []
    lines.append(f"RELATÓRIO — SELEÇÃO DE SAMPLE FRAGMENTÁRIO — {confronto_id}")
    lines.append(f"gerado_em: {utc_now_iso()}")
    lines.append("")
    lines.append(f"base_fragmentaria: {relpath_str(base_path, project_root)}")
    lines.append(f"n_fragmentos_base: {estat.get('n_fragmentos', len(all_frags))}")
    lines.append(f"n_fragmentos_sample: {len(sample)}")
    lines.append(f"keywords_usadas: {', '.join(keywords)}")
    lines.append("")

    if sample:
        lines.append("Top fragmentos selecionados:")
        for frag in sample:
            lines.append(
                f"- {frag.get('id')}: score={frag.get('score')} | proposicoes={','.join(safe_list(frag.get('proposicoes_impactadas')))} | texto={shorten(frag.get('texto_fragmento') or '', 180)}"
            )
        lines.append("")

    if keyword_counter:
        lines.append("Keywords mais presentes no sample:")
        for key, count in keyword_counter.most_common(20):
            lines.append(f"- {key}: {count}")
        lines.append("")

    if prop_counter:
        lines.append("Proposições mais representadas no sample:")
        for key, count in prop_counter.most_common(20):
            lines.append(f"- {key}: {count}")
        lines.append("")

    status = "ok" if sample else "erros_de_selecao"
    lines.append(f"status: {status}")
    return "\n".join(lines).strip() + "\n"


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seleciona um sample nuclear de fragmentos a partir de uma base fragmentária por confronto."
    )
    parser.add_argument("--project-root", type=Path, help="Raiz do projeto DoReal.")
    parser.add_argument("--confronto", required=True, help="Ex.: CF08")
    parser.add_argument("--input-json", type=Path, help="Caminho explícito para CFxx_base_fragmentaria.json")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="Número de fragmentos a selecionar.")
    parser.add_argument(
        "--keywords",
        help="Lista separada por vírgulas. Se omitido, usa keywords padrão.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Score mínimo para entrar no sample.",
    )
    return parser.parse_args(argv)



def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    confronto_id = normalize_spaces(args.confronto).upper()
    if not re.fullmatch(r"CF\d{2,4}", confronto_id):
        print(f"ERRO FATAL: confronto inválido: {confronto_id}")
        return 1

    project_root = project_root_from_explicit_or_cwd(args.project_root)

    try:
        input_json = resolve_existing_input(project_root, confronto_id, args.input_json)
        payload = read_json(input_json)

        fragments = safe_list(payload.get("fragmentos"))
        if not fragments:
            print(f"ERRO FATAL: sem fragmentos em {input_json}")
            return 1

        keywords = [normalize_spaces(x).lower() for x in (args.keywords.split(",") if args.keywords else DEFAULT_KEYWORDS) if normalize_spaces(x)]
        if not keywords:
            print("ERRO FATAL: lista de keywords vazia.")
            return 1

        scored: List[Dict[str, Any]] = []
        for frag in fragments:
            row = score_fragment(safe_dict(frag), keywords)
            if row["score"] >= args.min_score:
                scored.append(row)

        scored.sort(
            key=lambda x: (
                -int(x.get("score") or 0),
                -len(safe_list(x.get("proposicoes_impactadas"))),
                -int(x.get("n_registos_impacto") or 0),
                str(x.get("id") or ""),
            )
        )

        sample = scored[: max(args.top_n, 1)]

        out_dir = (project_root / DEFAULT_OUTPUT_DIR_RELATIVE).resolve()
        out_json = out_dir / f"{confronto_id}_sample_fragmentos_v1.json"
        out_md = out_dir / f"{confronto_id}_sample_fragmentos_v1.md"
        out_report = (project_root / DEFAULT_OUTPUT_REPORT_DIR_RELATIVE / f"relatorio_selecao_sample_fragmentos_{confronto_id}_v1.txt").resolve()

        sample_payload = {
            "meta": {
                "script": Path(__file__).name,
                "gerado_em": utc_now_iso(),
                "confronto_id": confronto_id,
                "fonte_base_fragmentaria": relpath_str(input_json, project_root),
                "top_n": args.top_n,
                "min_score": args.min_score,
                "keywords": keywords,
            },
            "estatisticas": {
                "n_fragmentos_base": len(fragments),
                "n_fragmentos_scored": len(scored),
                "n_fragmentos_sample": len(sample),
            },
            "snapshot_dossier": safe_dict(payload.get("snapshot_dossier")),
            "sample": sample,
        }

        write_json(out_json, sample_payload)
        write_text(out_md, build_markdown(confronto_id, input_json, project_root, payload, sample, keywords))
        write_text(out_report, build_report(confronto_id, input_json, project_root, payload, sample, keywords))

        print(f"Sample gerado em: {out_md}")
        print(f"JSON gerado em: {out_json}")
        print(f"Relatório gerado em: {out_report}")
        print("Concluído sem erros.")
        return 0

    except Exception as exc:
        print(f"ERRO FATAL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
