
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def validate_markdown_text(kind: str, expected_filename: str, text: str) -> dict[str, Any]:
    errors = []
    stripped = text.strip()
    if len(stripped) < 250:
        errors.append('texto demasiado curto')
    if not ('#' in stripped or '##' in stripped):
        errors.append('sem headings markdown')
    if '```' in stripped and kind != 'transicao':
        errors.append('contém code fences desnecessárias')
    if expected_filename.startswith('ABERTURA_') and 'abertura' not in stripped.lower():
        errors.append('não parece abertura')
    if expected_filename.startswith('ENSAIO_') and 'ensaio' not in stripped.lower():
        errors.append('não parece ensaio')
    if expected_filename.startswith('DECISAO_') and 'decis' not in stripped.lower():
        errors.append('não parece decisão')
    if expected_filename.startswith('CONSOLIDACAO_') and 'consolida' not in stripped.lower():
        errors.append('não parece consolidação')
    verdict = 'VALID' if not errors else 'INVALID'
    return {'verdict': verdict, 'errors': errors}
