from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from scanner import (
    scan_faixas,
    scan_transicoes,
    latest_transition_for,
    parse_transition_next_target,
    infer_next_faixa_folder_from_filename,
    decision_suggests_consolidation,
    decision_requires_preserve_limit,
    faixa_slug,
    normalized_slug,
    semantic_core_slug,
    slug_has_derivative_markers,
    repeated_pos_post_depth,
    duplicate_slug_map,
    tail_same_core_chain,
)


def _artifact_from_existing_next_faixa(next_faixa) -> dict[str, Any]:
    if not next_faixa.abertura_files:
        filename = f"ABERTURA_{next_faixa.name.upper()}.md"
        return {'kind': 'abertura', 'filename': filename, 'folder': str(next_faixa.abertura_dir)}
    if len(next_faixa.ensaio_files) < 1:
        stem = next_faixa.name.split('_faixa_', 1)[1].upper()
        filename = f'ENSAIO_CONTROLADO_{stem}_v1.md'
        return {'kind': 'ensaio', 'filename': filename, 'folder': str(next_faixa.ensaios_dir)}
    if not next_faixa.decisao_files:
        stem = next_faixa.name.split('_faixa_', 1)[1].upper()
        filename = f'DECISAO_CONTROLADA_SOBRE_USO_MAXIMO_INICIAL_{stem}.md'
        return {'kind': 'decisao', 'filename': filename, 'folder': str(next_faixa.decisoes_dir)}
    if not next_faixa.consolidado_files and decision_suggests_consolidation(next_faixa.decisao_files[-1]):
        stem = next_faixa.name.split('_faixa_', 1)[1].upper()
        filename = f'CONSOLIDACAO_FAIXA_EXPOSITIVA_{stem}.md'
        return {'kind': 'consolidacao', 'filename': filename, 'folder': str(next_faixa.consolidado_dir)}
    return {'kind': 'none', 'filename': '', 'folder': ''}


def _resolve_transition_folder(ctx, folder_str: str) -> Path:
    p = Path(folder_str.strip())
    if p.is_absolute():
        return p

    parts = list(p.parts)
    lower_parts = [part.lower() for part in parts]
    descida_name = ctx.descida_root.name.lower()
    trans_name = ctx.transicao_root.name.lower()

    if descida_name in lower_parts:
        idx = lower_parts.index(descida_name)
        return ctx.descida_root.parent / Path(*parts[idx:])
    if trans_name in lower_parts:
        idx = lower_parts.index(trans_name)
        return ctx.descida_root / Path(*parts[idx:])
    if parts and re.match(r'^\d{2}_faixa_', parts[0], re.I):
        return ctx.descida_root / p
    return ctx.descida_root.parent / p


def _target_slug_from_artifact_filename(filename: str) -> str:
    stem = filename[:-3] if filename.lower().endswith('.md') else filename
    stem = re.sub(r'^ABERTURA_FAIXA_EXPOSITIVA_CONTROLADA_', '', stem, flags=re.I)
    stem = re.sub(r'^ABERTURA_', '', stem, flags=re.I)
    return normalized_slug(stem)


def _history_guardrails(faixas, settings: dict[str, Any]) -> tuple[bool, str | None, list[str]]:
    warnings: list[str] = []
    dup_map = duplicate_slug_map(faixas)
    if dup_map:
        for slug, nums in sorted(dup_map.items()):
            warnings.append(f"Slug de faixa repetido já existente: {slug} em {nums}.")
        if bool(settings.get('block_on_exact_slug_duplicate', True)):
            return True, (
                'Existem slugs de faixa repetidos na árvore atual. Rever manualmente antes de prosseguir.'
            ), warnings

    chain = tail_same_core_chain(faixas)
    if not chain:
        return False, None, warnings

    core = semantic_core_slug(faixa_slug(chain[-1].name))
    chain_len = len(chain)
    derivative_count = sum(1 for f in chain if slug_has_derivative_markers(faixa_slug(f.name)))
    pos_post_depth_max = max(repeated_pos_post_depth(faixa_slug(f.name)) for f in chain)
    threshold = int(settings.get('semantic_core_human_gate_threshold', 5))
    derivative_threshold = int(settings.get('derivative_marker_human_gate_threshold', 3))
    generic_core_only = bool(settings.get('semantic_core_gate_only_for_generic_cores', True))
    core_is_generic = bool(re.fullmatch(r'cf\d+', core))

    if chain_len >= 3:
        warnings.append(
            f"Cadeia consecutiva do mesmo núcleo semântico no fim da série: {core} (n={chain_len})."
        )
    if derivative_count >= 2:
        warnings.append(
            f"Várias faixas derivativas no mesmo núcleo {core} (derivativas={derivative_count}, profundidade_pos/post={pos_post_depth_max})."
        )

    should_gate_core = chain_len >= threshold and (core_is_generic or not generic_core_only)
    should_gate_derivative = derivative_count >= derivative_threshold or pos_post_depth_max >= 2

    if bool(settings.get('block_on_repeated_semantic_core', True)) and should_gate_core and should_gate_derivative:
        return True, (
            f"Há {chain_len} faixas consecutivas no mesmo núcleo semântico ({core}) com deriva derivativa acumulada; é necessária deliberação humana antes de abrir nova faixa."
        ), warnings

    return False, None, warnings


def _proposed_opening_guardrails(faixas, parsed_target: dict[str, Any], settings: dict[str, Any]) -> tuple[bool, str | None, list[str]]:
    warnings: list[str] = []
    target_slug = _target_slug_from_artifact_filename(parsed_target['filename'])
    target_core = semantic_core_slug(target_slug)
    exact_existing = {normalized_slug(faixa_slug(f.name)): f.number for f in faixas}
    if target_slug in exact_existing and bool(settings.get('block_on_exact_slug_duplicate', True)):
        return True, f"A abertura seguinte repetiria exatamente um slug de faixa já existente ({target_slug}) na faixa {exact_existing[target_slug]:02d}.", warnings

    chain = tail_same_core_chain(faixas)
    if chain:
        current_core = semantic_core_slug(faixa_slug(chain[-1].name))
        if target_core == current_core and bool(settings.get('block_on_repeated_semantic_core', True)):
            threshold = int(settings.get('semantic_core_human_gate_threshold', 5))
            derivative_threshold = int(settings.get('derivative_marker_human_gate_threshold', 3))
            derivative_count = sum(1 for f in chain if slug_has_derivative_markers(faixa_slug(f.name)))
            target_derivative = slug_has_derivative_markers(target_slug)
            if len(chain) >= threshold or (derivative_count >= derivative_threshold and target_derivative):
                return True, (
                    f"A abertura seguinte manteria o mesmo núcleo semântico ({target_core}) após uma cadeia já longa/derivativa; exigir decisão humana explícita."
                ), warnings
    return False, None, warnings


def resolve_state(ctx) -> dict[str, Any]:
    faixas = scan_faixas(ctx.descida_root)
    transicoes = scan_transicoes(ctx.transicao_root)

    state: dict[str, Any] = {
        'project_root': str(ctx.project_root),
        'descida_root': str(ctx.descida_root),
        'faixas_presentes': [f.number for f in faixas],
        'transicoes_presentes': [t['name'] for t in transicoes],
        'blocked': False,
        'warnings': [],
    }

    if not faixas:
        state.update({'blocked': True, 'reason': 'Sem faixas presentes na pasta de descida.'})
        return state

    current = faixas[-1]
    state['current_faixa_number'] = current.number
    state['current_faixa_name'] = current.name
    state['current_faixa_status'] = current.status
    state['current_active_file'] = str(current.active_file) if current.active_file else None

    faixas_catalog = {}
    for f in faixas:
        faixas_catalog[f'{f.number:02d}'] = {
            'name': f.name,
            'status': f.status,
            'active_file': str(f.active_file) if f.active_file else None,
        }
    state['faixas_catalog'] = faixas_catalog

    blocked_hist, reason_hist, warnings_hist = _history_guardrails(faixas, ctx.settings)
    state['warnings'].extend(warnings_hist)
    if blocked_hist:
        state.update({'blocked': True, 'reason': reason_hist, 'state_source_transition': None})
        return state

    latest_trans_current = latest_transition_for(transicoes, current.number)
    next_num = current.number + 1
    next_faixa = next((f for f in faixas if f.number == next_num), None)

    artifact = None

    if latest_trans_current and not next_faixa:
        parsed = parse_transition_next_target(latest_trans_current['file'])
        if parsed:
            state['warnings'].extend(parsed.get('warnings', []))
            if not parsed.get('auto_open', True):
                state.update({
                    'blocked': True,
                    'reason': (
                        'A decisão de transição existe, mas não autoriza abertura automática da faixa seguinte. '
                        'É necessária deliberação explícita de avanço ou revisão da própria decisão.'
                    ),
                    'state_source_transition': str(latest_trans_current['file']),
                })
                return state

            blocked_open, reason_open, warnings_open = _proposed_opening_guardrails(faixas, parsed, ctx.settings)
            state['warnings'].extend(warnings_open)
            if blocked_open:
                state.update({
                    'blocked': True,
                    'reason': reason_open,
                    'state_source_transition': str(latest_trans_current['file']),
                })
                return state

            folder_path = _resolve_transition_folder(ctx, parsed['folder'])
            artifact = {
                'kind': 'abertura',
                'filename': parsed['filename'],
                'folder': str(folder_path),
                'source_transition': str(latest_trans_current['file']),
            }

    if artifact is None and next_faixa is not None:
        a = _artifact_from_existing_next_faixa(next_faixa)
        if a['kind'] != 'none':
            artifact = a

    if artifact is None:
        if current.status == 'CONSOLIDADA':
            artifact = {
                'kind': 'transicao',
                'filename': f'{current.number:02d}_para_{next_num:02d}_DECISAO_SOBRE_PROXIMA_FAIXA_EXPOSITIVA_CONTROLADA.md',
                'folder': str(ctx.transicao_root),
            }
        elif current.status == 'ABERTA':
            stem = current.name.split('_faixa_', 1)[1].upper()
            artifact = {
                'kind': 'ensaio',
                'filename': f'ENSAIO_CONTROLADO_{stem}_v1.md',
                'folder': str(current.ensaios_dir),
            }
        elif current.status == 'EM_ENSAIO':
            stem = current.name.split('_faixa_', 1)[1].upper()
            artifact = {
                'kind': 'decisao',
                'filename': f'DECISAO_CONTROLADA_SOBRE_USO_MAXIMO_INICIAL_{stem}.md',
                'folder': str(current.decisoes_dir),
            }
        elif current.status == 'DECIDIDA_SEM_CONSOLIDAR':
            if current.decisao_files and decision_requires_preserve_limit(current.decisao_files[-1]):
                state.update({
                    'blocked': True,
                    'reason': (
                        'A decisão local vigente manda preservar o limite atual e não autoriza continuação automática nem transição. '
                        'É necessária deliberação humana explícita antes de abrir nova faixa ou gerar nova transição.'
                    ),
                    'state_source_transition': None,
                })
                return state
            if current.decisao_files and decision_suggests_consolidation(current.decisao_files[-1]):
                stem = current.name.split('_faixa_', 1)[1].upper()
                artifact = {
                    'kind': 'consolidacao',
                    'filename': f'CONSOLIDACAO_FAIXA_EXPOSITIVA_{stem}.md',
                    'folder': str(current.consolidado_dir),
                }
            else:
                artifact = {
                    'kind': 'transicao',
                    'filename': f'{current.number:02d}_para_{next_num:02d}_DECISAO_SOBRE_PROXIMA_FAIXA_EXPOSITIVA_CONTROLADA.md',
                    'folder': str(ctx.transicao_root),
                }
        else:
            state.update({'blocked': True, 'reason': 'Estado atual não reconhecido.'})
            return state

    state['next_artifact_kind'] = artifact['kind']
    state['expected_artifact'] = artifact['filename']
    state['expected_folder'] = artifact['folder']
    state['state_source_transition'] = artifact.get('source_transition')
    return state
