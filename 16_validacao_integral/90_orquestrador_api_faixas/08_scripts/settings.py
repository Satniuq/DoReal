
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from common import load_json


@dataclass
class RuntimeContext:
    project_root: Path
    descida_root: Path
    transicao_root: Path
    readme_path: Path
    guiao_path: Path
    runtime_root: Path
    config_path: Path
    settings: dict[str, Any]
    logs_dir: Path


def load_runtime_context(project_root_override: str | None = None) -> RuntimeContext:
    this_dir = Path(__file__).resolve().parent
    runtime_root = this_dir.parent
    config_path = runtime_root / '00_config' / 'settings_runtime.json'
    settings = load_json(config_path)

    project_root = Path(project_root_override) if project_root_override else Path(settings['project_root'])
    descida_root = project_root / Path(str(settings['descida_root_rel']).replace('\\', '/'))
    transicao_root = descida_root / settings['transicao_dir_name']
    readme_path = descida_root / settings['readme_filename']
    guiao_path = descida_root / settings['guiao_filename']
    logs_dir = runtime_root / '07_logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    return RuntimeContext(
        project_root=project_root,
        descida_root=descida_root,
        transicao_root=transicao_root,
        readme_path=readme_path,
        guiao_path=guiao_path,
        runtime_root=runtime_root,
        config_path=config_path,
        settings=settings,
        logs_dir=logs_dir,
    )
