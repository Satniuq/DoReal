
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r'[^a-z0-9à-ÿ]+', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text


def natural_sort_key(value: str):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r'(\d+)', value)]


def latest_md_file(folder: Path) -> Path | None:
    files = sorted([p for p in folder.glob('*.md') if p.is_file()], key=lambda p: natural_sort_key(p.name))
    return files[-1] if files else None


def list_md_files(folder: Path) -> list[Path]:
    return sorted([p for p in folder.glob('*.md') if p.is_file()], key=lambda p: natural_sort_key(p.name))


def open_folder(path: Path, enabled: bool) -> None:
    if not enabled:
        return
    try:
        if os.name == 'nt':
            os.startfile(str(path))  # type: ignore[attr-defined]
    except Exception:
        pass


def compact_text(text: str, max_chars: int = 16000) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    head = text[: int(max_chars * 0.7)]
    tail = text[-int(max_chars * 0.3) :]
    return head + "\n\n[... conteúdo intermédio omitido automaticamente ...]\n\n" + tail


def now_iso() -> str:
    import datetime as _dt
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
