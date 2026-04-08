
from __future__ import annotations

from pathlib import Path
from typing import Any

from common import open_folder, write_text


def publish_text(ctx, target_folder: str, filename: str, text: str) -> Path:
    folder = Path(target_folder)
    if not folder.is_absolute():
        folder = ctx.project_root / folder
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / filename
    write_text(target, text)
    open_folder(folder, bool(ctx.settings.get('open_folders_in_explorer', False)))
    return target
