
from __future__ import annotations

from pathlib import Path
from typing import Any

from common import compact_text, read_text
from scanner import scan_faixas, scan_transicoes, latest_transition_for


def _safe(path: Path, max_chars: int = 16000) -> str:
    if not path or not path.exists():
        return ''
    return compact_text(read_text(path), max_chars=max_chars)


def build_context_pack(ctx, state: dict[str, Any]) -> dict[str, Any]:
    faixas = scan_faixas(ctx.descida_root)
    transicoes = scan_transicoes(ctx.transicao_root)
    current_num = state['current_faixa_number']
    current = next(f for f in faixas if f.number == current_num)

    previous = next((f for f in faixas if f.number == current_num - 1), None)
    latest_transition = latest_transition_for(transicoes, current_num)
    previous_transition = latest_transition_for(transicoes, current_num - 1)

    next_kind = state['next_artifact_kind']
    segments = []

    # Always include method anchors
    segments.append({
        'label': 'README_FINAL',
        'path': str(ctx.readme_path),
        'content': _safe(ctx.readme_path, 22000),
    })
    segments.append({
        'label': 'GUIAO_FAIXAS',
        'path': str(ctx.guiao_path),
        'content': _safe(ctx.guiao_path, 14000),
    })

    if next_kind == 'transicao':
        if current.active_file:
            segments.append({'label': 'FAIXA_ATUAL_ATIVA', 'path': str(current.active_file), 'content': _safe(current.active_file, 16000)})
        if previous_transition:
            segments.append({'label': 'TRANSICAO_ANTERIOR', 'path': str(previous_transition['file']), 'content': _safe(previous_transition['file'], 12000)})
    elif next_kind == 'abertura':
        if state.get('state_source_transition'):
            p = Path(state['state_source_transition'])
            segments.append({'label': 'DECISAO_TRANSICAO_ATIVA', 'path': str(p), 'content': _safe(p, 20000)})
        elif latest_transition:
            segments.append({'label': 'DECISAO_TRANSICAO_ATIVA', 'path': str(latest_transition['file']), 'content': _safe(latest_transition['file'], 20000)})
        if current.active_file:
            segments.append({'label': 'FAIXA_ANTERIOR_ATIVA', 'path': str(current.active_file), 'content': _safe(current.active_file, 16000)})
        if current.decisao_files:
            segments.append({'label': 'DECISAO_ANTERIOR', 'path': str(current.decisao_files[-1]), 'content': _safe(current.decisao_files[-1], 12000)})
        if current.abertura_files:
            segments.append({'label': 'ABERTURA_ANTERIOR', 'path': str(current.abertura_files[-1]), 'content': _safe(current.abertura_files[-1], 12000)})
    elif next_kind == 'ensaio':
        next_num = current_num + 1 if state['expected_folder'].find(f"{current_num+1:02d}_faixa") != -1 else current_num
        target = next((f for f in faixas if f.number == next_num), current)
        if target.abertura_files:
            segments.append({'label': 'ABERTURA_ATIVA', 'path': str(target.abertura_files[-1]), 'content': _safe(target.abertura_files[-1], 18000)})
        if latest_transition:
            segments.append({'label': 'DECISAO_TRANSICAO', 'path': str(latest_transition['file']), 'content': _safe(latest_transition['file'], 14000)})
        if current.active_file:
            segments.append({'label': 'FAIXA_ANTERIOR_ATIVA', 'path': str(current.active_file), 'content': _safe(current.active_file, 12000)})
    elif next_kind == 'decisao':
        target = current
        if current.status == 'CONSOLIDADA':
            next_num = current_num + 1
            target = next((f for f in faixas if f.number == next_num), current)
        if target.abertura_files:
            segments.append({'label': 'ABERTURA_ATIVA', 'path': str(target.abertura_files[-1]), 'content': _safe(target.abertura_files[-1], 18000)})
        if target.ensaio_files:
            segments.append({'label': 'ENSAIO_ATIVO', 'path': str(target.ensaio_files[-1]), 'content': _safe(target.ensaio_files[-1], 18000)})
    elif next_kind == 'consolidacao':
        if current.abertura_files:
            segments.append({'label': 'ABERTURA_ATIVA', 'path': str(current.abertura_files[-1]), 'content': _safe(current.abertura_files[-1], 14000)})
        if current.ensaio_files:
            segments.append({'label': 'ENSAIO_ATIVO', 'path': str(current.ensaio_files[-1]), 'content': _safe(current.ensaio_files[-1], 14000)})
        if current.decisao_files:
            segments.append({'label': 'DECISAO_ATIVA', 'path': str(current.decisao_files[-1]), 'content': _safe(current.decisao_files[-1], 14000)})

    segments = [s for s in segments if s['content'].strip()]
    return {'segments': segments}
