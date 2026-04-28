#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pipeline_fragmentos_main.py

Orquestrador principal do pipeline de fragmentos.

Colocar em:

    00_Pipeline_fragmentos/01_scripts/pipeline_fragmentos_main.py

Estrutura esperada:

    00_Pipeline_fragmentos/
    ├── 00_inbox_novos/
    │   └── fragmentos_novos.md
    ├── 01_scripts/
    │   ├── pipeline_fragmentos_main.py
    │   ├── gerar_run_containers_nao_resegmentados_v4.py
    │   ├── resegmentar_containers_semanticos_v6_openai.py
    │   └── tratar_fragmentos_resegmentados_api.py
    ├── 02_base_referencia/
    │   ├── fragmentos.md
    │   ├── fragmentos_ja_processados.md
    │   └── instancia_total_dividida/
    │       ├── 03_entidades_fragmentos__parte_001.json
    │       └── 03_entidades_fragmentos__parte_002.json
    ├── 03_runs/
    ├── 04_outputs_prontos_para_integrar/
    ├── 05_tratamento/
    └── 90_arquivo/

Comandos:
    python pipeline_fragmentos_main.py status
    python pipeline_fragmentos_main.py next-id
    python pipeline_fragmentos_main.py match
    python pipeline_fragmentos_main.py containers
    python pipeline_fragmentos_main.py resegmentar
    python pipeline_fragmentos_main.py tratar
    python pipeline_fragmentos_main.py all

Uso típico:
    1. escrever fragmentos novos em:
          00_inbox_novos/fragmentos_novos.md

    2. correr:
          python pipeline_fragmentos_main.py all

    3. tratar fragmentos já resegmentados:
          python pipeline_fragmentos_main.py tratar

    4. ver estado:
          python pipeline_fragmentos_main.py status
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Caminhos
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent

INBOX_DIR = PIPELINE_DIR / "00_inbox_novos"
SCRIPTS_DIR = PIPELINE_DIR / "01_scripts"
BASE_REF_DIR = PIPELINE_DIR / "02_base_referencia"
INSTANCIA_DIR = BASE_REF_DIR / "instancia_total_dividida"
RUNS_DIR = PIPELINE_DIR / "03_runs"
READY_DIR = PIPELINE_DIR / "04_outputs_prontos_para_integrar"
TRATAMENTO_DIR = PIPELINE_DIR / "05_tratamento"
ARCHIVE_DIR = PIPELINE_DIR / "90_arquivo"

TRATAMENTO_PARTIAL_DIR = TRATAMENTO_DIR / "06_instancia_parcial_novas_runs"

FRAGMENTOS_NOVOS = INBOX_DIR / "fragmentos_novos.md"
MATCH_JSON = INBOX_DIR / "match_nao_processados_vs_processados.json"
MATCH_RELATORIO = INBOX_DIR / "relatorio_match_nao_processados_vs_processados.md"
APENAS_NOVOS = INBOX_DIR / "fragmentos_nao_processados__apenas_novos.md"
POSSIVEIS_DUPLICADOS = INBOX_DIR / "fragmentos_nao_processados__possiveis_duplicados.md"

GERAR_RUN_SCRIPT = SCRIPTS_DIR / "gerar_run_containers_nao_resegmentados_v4.py"
RESEGMENTAR_SCRIPT = SCRIPTS_DIR / "resegmentar_containers_semanticos_v6_openai.py"
TRATAR_SCRIPT = SCRIPTS_DIR / "tratar_fragmentos_resegmentados_api.py"

PROCESSADOS_MD = [
    BASE_REF_DIR / "fragmentos.md",
    BASE_REF_DIR / "fragmentos_ja_processados.md",
]

JSON_FRAGMENTOS_INTEGRADOS = [
    INSTANCIA_DIR / "03_entidades_fragmentos__parte_001.json",
    INSTANCIA_DIR / "03_entidades_fragmentos__parte_002.json",
]

HEADER_RE = re.compile(r"^##\s+(F\d{4}(?:_A\d{2})?)(?:\s+—\s+.*?)?\s*$", re.MULTILINE)
F_ID_RE = re.compile(r"\bF(\d{4})\b")


# =============================================================================
# Dataclasses
# =============================================================================

@dataclass
class MatchResult:
    id_nao_processado: str
    chars: int
    inicio: str
    melhor_match_id: Optional[str]
    melhor_match_origem: Optional[str]
    score: float
    classe: str
    texto: str


# =============================================================================
# Utilidades gerais
# =============================================================================

def ensure_dirs() -> None:
    for path in [
        INBOX_DIR,
        SCRIPTS_DIR,
        BASE_REF_DIR,
        INSTANCIA_DIR,
        RUNS_DIR,
        READY_DIR,
        TRATAMENTO_DIR,
        TRATAMENTO_PARTIAL_DIR,
        ARCHIVE_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    if not FRAGMENTOS_NOVOS.exists():
        FRAGMENTOS_NOVOS.write_text("", encoding="utf-8")


def print_header(title: str) -> None:
    print("=" * 78)
    print(title)
    print("=" * 78)


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * 78)


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json_if_exists(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_subprocess(cmd: List[str], cwd: Optional[Path] = None) -> None:
    print()
    print("[exec]", " ".join(str(x) for x in cmd))
    result = subprocess.run(cmd, cwd=str(cwd or SCRIPT_DIR))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PIPELINE_DIR))
    except Exception:
        return str(path)


# =============================================================================
# Normalização e split de markdown
# =============================================================================

def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKC", texto or "")
    texto = texto.casefold()
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"[#*_`>\[\]{}()]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def hash_norm(texto: str) -> str:
    return hashlib.sha1(normalizar(texto).encode("utf-8")).hexdigest()


def split_md(texto: str) -> List[Dict[str, str]]:
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    headers = list(HEADER_RE.finditer(texto))

    if headers:
        blocos: List[Dict[str, str]] = []
        for i, h in enumerate(headers):
            start = h.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(texto)
            fid = h.group(1)
            corpo = texto[start:end].strip()
            if corpo:
                blocos.append({"id": fid, "texto": corpo})
        return blocos

    partes = [p.strip() for p in re.split(r"\n\s*\n+", texto) if p.strip()]
    return [
        {
            "id": f"BLOCO_{i:04d}",
            "texto": p,
        }
        for i, p in enumerate(partes, start=1)
    ]


# =============================================================================
# Base processada e matching
# =============================================================================

def carregar_fragmentos_integrados() -> List[Dict[str, str]]:
    corpus: List[Dict[str, str]] = []

    for path in JSON_FRAGMENTOS_INTEGRADOS:
        data = read_json_if_exists(path)
        if not isinstance(data, dict):
            continue

        for frag in data.get("fragmentos", []):
            if not isinstance(frag, dict):
                continue

            fid = frag.get("fragment_id")
            textos: List[str] = []

            emp = frag.get("camada_empirica", {}) or {}
            txt = frag.get("camada_textual_derivada", {}) or {}

            for key in ["texto_fragmento", "texto_normalizado", "texto_fonte_reconstituido"]:
                value = emp.get(key)
                if value:
                    textos.append(str(value))

            if txt.get("texto_limpo"):
                textos.append(str(txt["texto_limpo"]))

            texto = "\n\n".join(textos).strip()
            if texto:
                corpus.append({
                    "id": str(fid),
                    "origem": path.name,
                    "texto": texto,
                    "norm": normalizar(texto),
                })

    return corpus


def carregar_processados_md() -> List[Dict[str, str]]:
    corpus: List[Dict[str, str]] = []

    for path in PROCESSADOS_MD:
        if not path.exists():
            continue

        blocos = split_md(path.read_text(encoding="utf-8", errors="ignore"))
        for b in blocos:
            corpus.append({
                "id": b["id"],
                "origem": path.name,
                "texto": b["texto"],
                "norm": normalizar(b["texto"]),
            })

    return corpus


def carregar_processados() -> List[Dict[str, str]]:
    return carregar_fragmentos_integrados() + carregar_processados_md()


def score_match(a_norm: str, b_norm: str) -> float:
    if not a_norm or not b_norm:
        return 0.0

    if a_norm == b_norm:
        return 1.0

    if len(a_norm) > 120 and a_norm in b_norm:
        return 0.99

    if len(b_norm) > 120 and b_norm in a_norm:
        return min(0.98, len(b_norm) / max(1, len(a_norm)))

    tokens_a = set(re.findall(r"\w{4,}", a_norm))
    tokens_b = set(re.findall(r"\w{4,}", b_norm))

    if not tokens_a or not tokens_b:
        jaccard = 0.0
    else:
        jaccard = len(tokens_a & tokens_b) / max(1, len(tokens_a | tokens_b))

    if jaccard < 0.08:
        return jaccard

    ratio = difflib.SequenceMatcher(None, a_norm, b_norm).ratio()
    return max(jaccard, ratio)


def classificar(score: float) -> str:
    if score >= 0.95:
        return "ja_integrado"
    if score >= 0.72:
        return "possivel_duplicado"
    return "novo_provavel"


def fazer_match() -> Dict[str, Any]:
    ensure_dirs()

    if not FRAGMENTOS_NOVOS.exists():
        raise SystemExit(f"[erro] Não existe: {FRAGMENTOS_NOVOS}")

    processados = carregar_processados()
    if not processados:
        raise SystemExit(
            "[erro] Não encontrei base processada. "
            "Verifica 02_base_referencia/ e instancia_total_dividida/."
        )

    texto_novos = FRAGMENTOS_NOVOS.read_text(encoding="utf-8", errors="ignore")
    novos_blocos = split_md(texto_novos)

    hashes_nao: Dict[str, List[str]] = {}
    for b in novos_blocos:
        h = hash_norm(b["texto"])
        hashes_nao.setdefault(h, []).append(b["id"])

    duplicados_internos = {
        h: ids for h, ids in hashes_nao.items()
        if len(ids) > 1
    }

    resultados: List[MatchResult] = []

    for b in novos_blocos:
        n = normalizar(b["texto"])
        melhor_score = 0.0
        melhor_id: Optional[str] = None
        melhor_origem: Optional[str] = None

        for p in processados:
            s = score_match(n, p["norm"])
            if s > melhor_score:
                melhor_score = s
                melhor_id = p["id"]
                melhor_origem = p["origem"]

        resultados.append(
            MatchResult(
                id_nao_processado=b["id"],
                chars=len(b["texto"]),
                inicio=b["texto"][:180].replace("\n", " "),
                melhor_match_id=melhor_id,
                melhor_match_origem=melhor_origem,
                score=round(melhor_score, 4),
                classe=classificar(melhor_score),
                texto=b["texto"],
            )
        )

    novos = [r for r in resultados if r.classe == "novo_provavel"]
    possiveis = [r for r in resultados if r.classe == "possivel_duplicado"]
    integrados = [r for r in resultados if r.classe == "ja_integrado"]

    payload = {
        "resumo": {
            "total_nao_processados": len(resultados),
            "ja_integrados": len(integrados),
            "possiveis_duplicados": len(possiveis),
            "novos_provaveis": len(novos),
            "duplicados_internos": list(duplicados_internos.values()),
            "total_processados_comparados": len(processados),
            "input": str(FRAGMENTOS_NOVOS),
        },
        "resultados": [
            {
                "id_nao_processado": r.id_nao_processado,
                "chars": r.chars,
                "inicio": r.inicio,
                "melhor_match_id": r.melhor_match_id,
                "melhor_match_origem": r.melhor_match_origem,
                "score": r.score,
                "classe": r.classe,
                "texto": r.texto,
            }
            for r in resultados
        ],
    }

    write_json(MATCH_JSON, payload)

    linhas: List[str] = []
    linhas.append("# Relatório — match de fragmentos novos contra base processada\n")
    linhas.append("## Resumo\n")
    linhas.append(f"- Input: `{FRAGMENTOS_NOVOS.name}`")
    linhas.append(f"- Total no input: {len(resultados)}")
    linhas.append(f"- Já integrados: {len(integrados)}")
    linhas.append(f"- Possíveis duplicados: {len(possiveis)}")
    linhas.append(f"- Novos prováveis: {len(novos)}")
    linhas.append(f"- Duplicados internos: {len(duplicados_internos)}")
    linhas.append(f"- Base processada comparada: {len(processados)} blocos/fragmentos\n")

    if duplicados_internos:
        linhas.append("## Duplicados internos\n")
        for ids in duplicados_internos.values():
            linhas.append("- " + ", ".join(ids))
        linhas.append("")

    linhas.append("## Já integrados\n")
    if integrados:
        for r in integrados:
            linhas.append(
                f"- `{r.id_nao_processado}` ≈ `{r.melhor_match_id}` "
                f"({r.melhor_match_origem}) — score {r.score}"
            )
    else:
        linhas.append("- Nenhum.")
    linhas.append("")

    linhas.append("## Possíveis duplicados\n")
    if possiveis:
        for r in possiveis:
            linhas.append(
                f"- `{r.id_nao_processado}` ≈ `{r.melhor_match_id}` "
                f"({r.melhor_match_origem}) — score {r.score}"
            )
    else:
        linhas.append("- Nenhum.")
    linhas.append("")

    linhas.append("## Novos prováveis\n")
    if novos:
        for r in novos:
            linhas.append(f"- `{r.id_nao_processado}` — {r.inicio}")
    else:
        linhas.append("- Nenhum.")
    linhas.append("")

    MATCH_RELATORIO.write_text("\n".join(linhas), encoding="utf-8")

    APENAS_NOVOS.write_text(
        ("\n\n".join(r.texto for r in novos).strip() + "\n") if novos else "",
        encoding="utf-8",
    )

    POSSIVEIS_DUPLICADOS.write_text(
        ("\n\n".join(r.texto for r in possiveis).strip() + "\n") if possiveis else "",
        encoding="utf-8",
    )

    return payload


# =============================================================================
# Deteção do próximo F####
# =============================================================================

def extract_max_f_from_obj(obj: Any) -> int:
    max_id = 0

    if isinstance(obj, dict):
        for value in obj.values():
            max_id = max(max_id, extract_max_f_from_obj(value))

    elif isinstance(obj, list):
        for item in obj:
            max_id = max(max_id, extract_max_f_from_obj(item))

    elif isinstance(obj, str):
        for m in F_ID_RE.finditer(obj):
            max_id = max(max_id, int(m.group(1)))

    return max_id


def extract_max_f_from_text(path: Path) -> int:
    text = read_text_if_exists(path)
    max_id = 0
    for m in F_ID_RE.finditer(text):
        max_id = max(max_id, int(m.group(1)))
    return max_id


def candidate_id_reference_paths() -> List[Path]:
    out: List[Path] = []

    for p in PROCESSADOS_MD + JSON_FRAGMENTOS_INTEGRADOS:
        if p.exists() and p not in out:
            out.append(p)

    for pattern in ["*.json", "*.md", "*.txt"]:
        for p in sorted(READY_DIR.glob(pattern)):
            if p.exists() and p not in out:
                out.append(p)

    for pattern in [
        "**/fragmentos_resegmentados__*.json",
        "**/containers_segmentacao__*.json",
        "**/*.md",
    ]:
        for p in sorted(RUNS_DIR.glob(pattern)):
            if p.exists() and p not in out:
                out.append(p)

    for pattern in [
        "03_entidades_fragmentos__parte_*.json",
        "*.json",
    ]:
        for p in sorted(TRATAMENTO_PARTIAL_DIR.glob(pattern)):
            if p.exists() and p not in out:
                out.append(p)

    return out


def detect_next_f_id() -> Tuple[int, List[str]]:
    max_found = 0
    notes: List[str] = []

    for path in candidate_id_reference_paths():
        try:
            if path.suffix.lower() == ".json":
                data = read_json_if_exists(path)
                local = extract_max_f_from_obj(data)
            else:
                local = extract_max_f_from_text(path)

            if local > 0:
                notes.append(f"{path.name}: max_F={local:04d}")

            max_found = max(max_found, local)

        except Exception as exc:
            notes.append(f"{path.name}: erro={exc.__class__.__name__}")

    return max_found + 1 if max_found > 0 else 1, notes


# =============================================================================
# Runs
# =============================================================================

def latest_run_dir(prefix: Optional[str] = None) -> Optional[Path]:
    if not RUNS_DIR.exists():
        return None

    candidates = [
        p for p in RUNS_DIR.iterdir()
        if p.is_dir() and (prefix is None or p.name.startswith(prefix))
    ]

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def find_container_json(run_dir: Path) -> Path:
    containers_dir = run_dir / "02_containers"
    candidates = sorted(containers_dir.glob("containers_segmentacao__*.json"))

    if not candidates:
        raise SystemExit(f"[erro] Não encontrei containers em: {containers_dir}")

    return candidates[-1]


def gerar_containers(
    output_prefix: str,
    run_name: Optional[str],
    start_from: Optional[int],
    keep_control_blocks: bool,
    keep_duplicates: bool,
    keep_superblocks: bool,
) -> Path:
    if not GERAR_RUN_SCRIPT.exists():
        raise SystemExit(f"[erro] Script não existe: {GERAR_RUN_SCRIPT}")

    if not APENAS_NOVOS.exists() or not APENAS_NOVOS.read_text(encoding="utf-8").strip():
        raise SystemExit(
            "[erro] Não há ficheiro de novos válido. "
            "Corre primeiro: python pipeline_fragmentos_main.py match"
        )

    if start_from is None:
        start_from, _notes = detect_next_f_id()

    before = set(p.name for p in RUNS_DIR.iterdir() if p.is_dir()) if RUNS_DIR.exists() else set()

    cmd = [
        sys.executable,
        str(GERAR_RUN_SCRIPT),
        "--input",
        str(APENAS_NOVOS),
        "--output-prefix",
        output_prefix,
        "--start-from",
        str(start_from),
    ]

    if run_name:
        cmd.extend(["--run-name", run_name])

    if keep_control_blocks:
        cmd.append("--keep-control-blocks")

    if keep_duplicates:
        cmd.append("--keep-duplicates")

    if keep_superblocks:
        cmd.append("--keep-superblocks")

    run_subprocess(cmd, cwd=SCRIPTS_DIR)

    if run_name:
        run_dir = RUNS_DIR / run_name
        if not run_dir.exists():
            raise SystemExit(f"[erro] A run esperada não foi criada: {run_dir}")
        return run_dir

    after_dirs = [p for p in RUNS_DIR.iterdir() if p.is_dir() and p.name not in before]
    if after_dirs:
        return max(after_dirs, key=lambda p: p.stat().st_mtime)

    latest = latest_run_dir(output_prefix)
    if latest is None:
        raise SystemExit("[erro] Não consegui detetar a run criada.")
    return latest


def resegmentar_run(run_dir: Path, local_only: bool, model: Optional[str], retries: int) -> None:
    if not RESEGMENTAR_SCRIPT.exists():
        raise SystemExit(f"[erro] Script não existe: {RESEGMENTAR_SCRIPT}")

    input_json = find_container_json(run_dir)

    cmd = [
        sys.executable,
        str(RESEGMENTAR_SCRIPT),
        str(input_json),
        "--retries",
        str(retries),
    ]

    if local_only:
        cmd.append("--local-only")

    if model:
        cmd.extend(["--model", model])

    run_subprocess(cmd, cwd=SCRIPTS_DIR)


def tratar_fragmentos(
    input_paths: Optional[List[str]],
    local_only: bool,
    model: Optional[str],
    retries: int,
    limit: Optional[int],
    force: bool,
    update_existing: bool,
    include_existing_base: bool,
    part_num: int,
    max_part_size: int,
    search_project_context: bool,
) -> None:
    if not TRATAR_SCRIPT.exists():
        raise SystemExit(f"[erro] Script não existe: {TRATAR_SCRIPT}")

    cmd = [
        sys.executable,
        str(TRATAR_SCRIPT),
        "--retries",
        str(retries),
        "--part-num",
        str(part_num),
        "--max-part-size",
        str(max_part_size),
    ]

    if input_paths:
        for p in input_paths:
            cmd.extend(["--input", p])

    if local_only:
        cmd.append("--local-only")

    if model:
        cmd.extend(["--model", model])

    if limit is not None:
        cmd.extend(["--limit", str(limit)])

    if force:
        cmd.append("--force")

    if update_existing:
        cmd.append("--update-existing")

    if include_existing_base:
        cmd.append("--include-existing-base")

    if search_project_context:
        cmd.append("--search-project-context")

    run_subprocess(cmd, cwd=SCRIPTS_DIR)


# =============================================================================
# Status
# =============================================================================

def count_json_fragmentos(path: Path) -> int:
    data = read_json_if_exists(path)
    if not isinstance(data, dict):
        return 0
    value = data.get("fragmentos")
    return len(value) if isinstance(value, list) else 0


def count_resegmentados(path: Path) -> int:
    data = read_json_if_exists(path)
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict) and isinstance(data.get("fragmentos"), list):
        return len(data["fragmentos"])
    return 0


def treatment_index_summary() -> Optional[Dict[str, Any]]:
    path = TRATAMENTO_PARTIAL_DIR / "INDEX_NOVOS_FRAGMENTOS_TRATADOS.json"
    data = read_json_if_exists(path)
    return data if isinstance(data, dict) else None


def status() -> None:
    ensure_dirs()

    print_header("ESTADO DO PIPELINE DE FRAGMENTOS")
    print(f"Pipeline: {PIPELINE_DIR}")

    print_section("1. Base canónica / tratada")
    total_integrados = 0
    for p in JSON_FRAGMENTOS_INTEGRADOS:
        n = count_json_fragmentos(p)
        total_integrados += n
        estado = "ok" if p.exists() else "em falta"
        print(f"- {rel(p)} — {estado} — fragmentos={n}")

    print(f"\nTotal integrado de referência: {total_integrados}")

    print_section("2. Inbox / entrada viva")
    blocos_novos = split_md(read_text_if_exists(FRAGMENTOS_NOVOS))
    print(f"- {rel(FRAGMENTOS_NOVOS)} — blocos={len(blocos_novos)}")

    if APENAS_NOVOS.exists():
        blocos_apenas = split_md(read_text_if_exists(APENAS_NOVOS))
        print(f"- {rel(APENAS_NOVOS)} — blocos={len(blocos_apenas)}")
    else:
        print(f"- {rel(APENAS_NOVOS)} — ainda não existe")

    if POSSIVEIS_DUPLICADOS.exists():
        blocos_dup = split_md(read_text_if_exists(POSSIVEIS_DUPLICADOS))
        print(f"- {rel(POSSIVEIS_DUPLICADOS)} — blocos={len(blocos_dup)}")
    else:
        print(f"- {rel(POSSIVEIS_DUPLICADOS)} — ainda não existe")

    if MATCH_JSON.exists():
        data = read_json_if_exists(MATCH_JSON) or {}
        resumo = data.get("resumo", {})
        print(f"- {rel(MATCH_JSON)} — existe")
        if resumo:
            print(
                "  resumo: "
                f"total={resumo.get('total_nao_processados')}, "
                f"novos={resumo.get('novos_provaveis')}, "
                f"duplicados={resumo.get('possiveis_duplicados')}, "
                f"integrados={resumo.get('ja_integrados')}"
            )
    else:
        print(f"- {rel(MATCH_JSON)} — ainda não existe")

    print_section("3. Runs")
    runs = sorted([p for p in RUNS_DIR.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not runs:
        print("- Nenhuma run.")
    else:
        for r in runs:
            container_jsons = list((r / "02_containers").glob("containers_segmentacao__*.json"))
            reseg_jsons = list((r / "03_resegmentacao").glob("fragmentos_resegmentados__*.json"))
            valid_jsons = list((r / "04_validacao").glob("relatorio_validacao_fragmentos__*.json"))

            frag_count = count_resegmentados(reseg_jsons[-1]) if reseg_jsons else 0
            valid_state = "sem_validacao"
            if valid_jsons:
                v = read_json_if_exists(valid_jsons[-1])
                if isinstance(v, dict):
                    valid_state = f"valido={v.get('valido')} n_erros={v.get('n_erros')}"

            print(
                f"- {r.name} — containers={len(container_jsons)} "
                f"resegmentados={len(reseg_jsons)} fragmentos={frag_count} {valid_state}"
            )

    print_section("4. Outputs prontos para tratamento/integração")
    ready = sorted(READY_DIR.glob("fragmentos_resegmentados__*.json"))
    if not ready:
        print("- Nenhum output pronto.")
    else:
        for p in ready:
            print(f"- {p.name} — fragmentos={count_resegmentados(p)}")

    print_section("5. Tratamento incremental")
    parts = sorted(TRATAMENTO_PARTIAL_DIR.glob("03_entidades_fragmentos__parte_*.json"))
    if not parts:
        print("- Nenhuma parte incremental tratada.")
    else:
        for p in parts:
            data = read_json_if_exists(p)
            if isinstance(data, dict):
                n = len(data.get("fragmentos", []) or [])
                oi = data.get("offset_inicio")
                of = data.get("offset_fim_exclusivo")
                print(f"- {rel(p)} — fragmentos={n} offsets={oi}–{of}")
            else:
                print(f"- {rel(p)} — inválido ou ilegível")

    idx = treatment_index_summary()
    if idx:
        stats = idx.get("estatisticas", {})
        print(
            "  index: "
            f"processed={stats.get('processed')}, "
            f"skipped={stats.get('skipped_existing')}, "
            f"api_calls={stats.get('api_calls')}, "
            f"errors={stats.get('errors')}"
        )

    print_section("6. Próximo ID provável")
    next_id, notes = detect_next_f_id()
    print(f"- próximo F provável: F{next_id:04d}")
    if notes:
        print("- referências consideradas:")
        for n in notes[-12:]:
            print(f"  - {n}")

    print()


# =============================================================================
# CLI
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Orquestrador do pipeline de fragmentos."
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Mostra estado atual do pipeline.")

    sub.add_parser("next-id", help="Mostra o próximo F#### provável.")

    sub.add_parser("match", help="Compara fragmentos_novos.md contra a base processada.")

    p_cont = sub.add_parser("containers", help="Gera run de containers a partir dos novos após match.")
    p_cont.add_argument("--output-prefix", default="run_fragmentos_novos")
    p_cont.add_argument("--run-name", default=None)
    p_cont.add_argument("--start-from", type=int, default=None)
    p_cont.add_argument("--keep-control-blocks", action="store_true")
    p_cont.add_argument("--keep-duplicates", action="store_true")
    p_cont.add_argument("--keep-superblocks", action="store_true")

    p_res = sub.add_parser("resegmentar", help="Ressegmenta uma run.")
    p_res.add_argument("--run", default="latest", help="Nome da run ou 'latest'.")
    p_res.add_argument("--local-only", action="store_true")
    p_res.add_argument("--model", default=None)
    p_res.add_argument("--retries", type=int, default=3)

    p_trat = sub.add_parser("tratar", help="Trata fragmentos resegmentados e gera parte incremental.")
    p_trat.add_argument(
        "--input",
        action="append",
        default=None,
        help="JSON de fragmentos resegmentados. Pode ser usado várias vezes. Por defeito usa todos em 04_outputs_prontos_para_integrar.",
    )
    p_trat.add_argument("--local-only", action="store_true")
    p_trat.add_argument("--model", default=None)
    p_trat.add_argument("--retries", type=int, default=3)
    p_trat.add_argument("--limit", type=int, default=None)
    p_trat.add_argument("--force", action="store_true")
    p_trat.add_argument("--update-existing", action="store_true")
    p_trat.add_argument("--include-existing-base", action="store_true")
    p_trat.add_argument("--part-num", type=int, default=3)
    p_trat.add_argument("--max-part-size", type=int, default=500)
    p_trat.add_argument("--search-project-context", action="store_true")
    p_trat.add_argument("--no-search-project-context", dest="search_project_context", action="store_false")
    p_trat.set_defaults(search_project_context=True)

    p_all = sub.add_parser("all", help="Executa match + containers + resegmentação.")
    p_all.add_argument("--output-prefix", default="run_fragmentos_novos")
    p_all.add_argument("--run-name", default=None)
    p_all.add_argument("--start-from", type=int, default=None)
    p_all.add_argument("--local-only", action="store_true")
    p_all.add_argument("--model", default=None)
    p_all.add_argument("--retries", type=int, default=3)
    p_all.add_argument("--keep-control-blocks", action="store_true")
    p_all.add_argument("--keep-duplicates", action="store_true")
    p_all.add_argument("--keep-superblocks", action="store_true")
    p_all.add_argument(
        "--tratar-after",
        action="store_true",
        help="Depois de resegmentar, chama também o tratamento incremental.",
    )
    p_all.add_argument("--tratar-limit", type=int, default=None)
    p_all.add_argument("--tratar-force", action="store_true")
    p_all.add_argument("--tratar-update-existing", action="store_true")
    p_all.add_argument("--tratar-local-only", action="store_true")
    p_all.add_argument("--tratar-model", default=None)
    p_all.add_argument("--tratar-part-num", type=int, default=3)
    p_all.add_argument("--tratar-max-part-size", type=int, default=500)
    p_all.add_argument("--tratar-search-project-context", action="store_true")
    p_all.add_argument("--no-tratar-search-project-context", dest="tratar_search_project_context", action="store_false")
    p_all.set_defaults(tratar_search_project_context=True)

    return parser


def main() -> None:
    ensure_dirs()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "status":
        status()
        return

    if args.command == "next-id":
        next_id, notes = detect_next_f_id()
        print_header("PRÓXIMO ID PROVÁVEL")
        print(f"F{next_id:04d}")
        print_section("Referências consideradas")
        for n in notes:
            print(f"- {n}")
        return

    if args.command == "match":
        print_header("MATCH — FRAGMENTOS NOVOS VS BASE PROCESSADA")
        payload = fazer_match()
        resumo = payload["resumo"]
        print(f"Total:                {resumo['total_nao_processados']}")
        print(f"Já integrados:        {resumo['ja_integrados']}")
        print(f"Possíveis duplicados: {resumo['possiveis_duplicados']}")
        print(f"Novos prováveis:      {resumo['novos_provaveis']}")
        print(f"Duplicados internos:  {len(resumo['duplicados_internos'])}")
        print("-" * 78)
        print(f"Relatório:            {MATCH_RELATORIO}")
        print(f"Apenas novos:         {APENAS_NOVOS}")
        print(f"Possíveis duplicados: {POSSIVEIS_DUPLICADOS}")
        return

    if args.command == "containers":
        print_header("GERAR RUN DE CONTAINERS")
        run_dir = gerar_containers(
            output_prefix=args.output_prefix,
            run_name=args.run_name,
            start_from=args.start_from,
            keep_control_blocks=args.keep_control_blocks,
            keep_duplicates=args.keep_duplicates,
            keep_superblocks=args.keep_superblocks,
        )
        print(f"Run criada: {run_dir}")
        return

    if args.command == "resegmentar":
        print_header("RESSEGMENTAR RUN")
        if args.run == "latest":
            run_dir = latest_run_dir()
            if run_dir is None:
                raise SystemExit("[erro] Não há runs.")
        else:
            run_dir = RUNS_DIR / args.run
            if not run_dir.exists():
                raise SystemExit(f"[erro] Run não existe: {run_dir}")

        print(f"Run: {run_dir}")
        resegmentar_run(
            run_dir=run_dir,
            local_only=args.local_only,
            model=args.model,
            retries=args.retries,
        )
        return

    if args.command == "tratar":
        print_header("TRATAMENTO — FRAGMENTOS RESSEGMENTADOS")
        tratar_fragmentos(
            input_paths=args.input,
            local_only=args.local_only,
            model=args.model,
            retries=args.retries,
            limit=args.limit,
            force=args.force,
            update_existing=args.update_existing,
            include_existing_base=args.include_existing_base,
            part_num=args.part_num,
            max_part_size=args.max_part_size,
            search_project_context=args.search_project_context,
        )
        return

    if args.command == "all":
        print_header("PIPELINE COMPLETO — MATCH + CONTAINERS + RESSEGMENTAÇÃO")

        print_section("1. Match")
        payload = fazer_match()
        resumo = payload["resumo"]
        print(f"Novos prováveis: {resumo['novos_provaveis']}")
        print(f"Possíveis duplicados: {resumo['possiveis_duplicados']}")

        if resumo["novos_provaveis"] <= 0:
            print("[fim] Não há novos fragmentos para gerar run.")
            if args.tratar_after:
                print_section("Tratamento pedido, mas sem nova run")
                tratar_fragmentos(
                    input_paths=None,
                    local_only=args.tratar_local_only,
                    model=args.tratar_model,
                    retries=args.retries,
                    limit=args.tratar_limit,
                    force=args.tratar_force,
                    update_existing=args.tratar_update_existing,
                    include_existing_base=False,
                    part_num=args.tratar_part_num,
                    max_part_size=args.tratar_max_part_size,
                    search_project_context=args.tratar_search_project_context,
                )
            return

        print_section("2. Gerar containers")
        run_dir = gerar_containers(
            output_prefix=args.output_prefix,
            run_name=args.run_name,
            start_from=args.start_from,
            keep_control_blocks=args.keep_control_blocks,
            keep_duplicates=args.keep_duplicates,
            keep_superblocks=args.keep_superblocks,
        )
        print(f"Run criada: {run_dir}")

        print_section("3. Ressegmentar")
        resegmentar_run(
            run_dir=run_dir,
            local_only=args.local_only,
            model=args.model,
            retries=args.retries,
        )

        if args.tratar_after:
            print_section("4. Tratamento incremental")
            tratar_fragmentos(
                input_paths=None,
                local_only=args.tratar_local_only,
                model=args.tratar_model,
                retries=args.retries,
                limit=args.tratar_limit,
                force=args.tratar_force,
                update_existing=args.tratar_update_existing,
                include_existing_base=False,
                part_num=args.tratar_part_num,
                max_part_size=args.tratar_max_part_size,
                search_project_context=args.tratar_search_project_context,
            )

        print_section("Estado final")
        status()
        return

    raise SystemExit(f"[erro] Comando desconhecido: {args.command}")


if __name__ == "__main__":
    main()
