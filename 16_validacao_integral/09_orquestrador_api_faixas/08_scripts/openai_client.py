from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from common import dump_json, now_iso


def _extract_output_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get('output_text'), str) and payload['output_text'].strip():
        return payload['output_text']
    output = payload.get('output') or []
    texts: list[str] = []
    for item in output:
        if item.get('type') == 'message':
            for c in item.get('content', []):
                if c.get('type') in ('output_text', 'text'):
                    txt = c.get('text')
                    if isinstance(txt, str):
                        texts.append(txt)
        elif item.get('type') in ('output_text', 'text'):
            txt = item.get('text')
            if isinstance(txt, str):
                texts.append(txt)
    return "\n".join(texts).strip()


def _parse_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].strip()
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and ((value[0] == value[-1]) and value[0] in {'"', "'"}):
            value = value[1:-1]
        values[key] = value
    return values


def _candidate_env_paths(ctx) -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()

    direct = [
        ctx.project_root / '.env',
        ctx.runtime_root / '.env',
        Path.cwd() / '.env',
    ]
    for p in direct:
        rp = str(p.resolve()) if p.exists() else str(p)
        if rp not in seen:
            seen.add(rp)
            candidates.append(p)

    for base in [ctx.project_root, ctx.runtime_root, Path.cwd()]:
        current = base.resolve()
        for parent in [current, *current.parents]:
            p = parent / '.env'
            rp = str(p)
            if rp not in seen:
                seen.add(rp)
                candidates.append(p)
    return candidates


def _load_env_from_candidates(ctx) -> dict[str, Any]:
    info: dict[str, Any] = {'loaded': False, 'path': None, 'keys': []}
    for path in _candidate_env_paths(ctx):
        if not path.exists() or not path.is_file():
            continue
        try:
            values = _parse_env_text(path.read_text(encoding='utf-8', errors='replace'))
        except Exception:
            continue
        if not values:
            continue
        for key, value in values.items():
            os.environ.setdefault(key, value)
        info['loaded'] = True
        info['path'] = str(path)
        info['keys'] = sorted(values.keys())
        return info
    return info


def _ensure_api_key(ctx) -> tuple[str, dict[str, Any]]:
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    load_info: dict[str, Any] = {'loaded': False, 'path': None, 'keys': []}
    if api_key:
        return api_key, load_info
    load_info = _load_env_from_candidates(ctx)
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if api_key:
        return api_key, load_info
    raise RuntimeError(
        'Falta OPENAI_API_KEY no ambiente e não foi possível carregá-la de nenhum .env. '
        'O runtime procurou primeiro no ambiente do processo e depois em .env começando por '
        f'{ctx.project_root}. '
        'Confirma que existe um ficheiro .env na raiz do projeto com OPENAI_API_KEY=...'
    )


def _read_error_body(err: urllib.error.HTTPError) -> str:
    try:
        return err.read().decode('utf-8', errors='replace')
    except Exception:
        return ''


def _retry_after_seconds(err: urllib.error.HTTPError) -> float | None:
    try:
        value = err.headers.get('Retry-After')
    except Exception:
        value = None
    if not value:
        return None
    try:
        return float(value)
    except Exception:
        return None


def run_openai(ctx, prompt_text: str, model: str | None = None) -> dict[str, Any]:
    api_key, load_info = _ensure_api_key(ctx)

    chosen_model = os.environ.get('OPENAI_MODEL') or model or ctx.settings.get('default_model') or 'gpt-5.4'
    body = {
        'model': chosen_model,
        'input': prompt_text,
    }
    base_url = ctx.settings.get('openai_base_url', 'https://api.openai.com/v1/responses')
    http_retries = int(ctx.settings.get('http_retries_on_429', 6))
    backoff_seconds = float(ctx.settings.get('http_backoff_seconds', 8))

    last_error = None
    for attempt in range(1, http_retries + 1):
        req = urllib.request.Request(
            base_url,
            data=json.dumps(body).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                payload = json.loads(resp.read().decode('utf-8'))
            run_id = payload.get('id') or f"run_{now_iso().replace(':', '').replace('-', '')}"
            output_text = _extract_output_text(payload)
            payload.setdefault('_runtime_http', {})
            payload['_runtime_http']['attempt'] = attempt
            payload['_runtime_http']['http_retries_configured'] = http_retries
            if load_info.get('loaded'):
                payload.setdefault('_runtime_env', {})
                payload['_runtime_env']['dotenv_loaded'] = load_info
            dump_json(ctx.logs_dir / 'auditoria' / f'{run_id}.json', payload)
            return {
                'run_id': run_id,
                'model': chosen_model,
                'payload': payload,
                'output_text': output_text,
            }
        except urllib.error.HTTPError as err:
            body_text = _read_error_body(err)
            last_error = f'HTTP {err.code}: {body_text or err.reason}'
            if err.code in {429, 500, 502, 503, 504} and attempt < http_retries:
                delay = _retry_after_seconds(err)
                if delay is None:
                    delay = backoff_seconds * (2 ** (attempt - 1))
                time.sleep(min(delay, 90))
                continue
            raise RuntimeError(last_error) from err
        except urllib.error.URLError as err:
            last_error = f'Erro de rede: {err}'
            if attempt < http_retries:
                time.sleep(min(backoff_seconds * (2 ** (attempt - 1)), 90))
                continue
            raise RuntimeError(last_error) from err

    raise RuntimeError(last_error or 'Falha desconhecida ao chamar a API da OpenAI.')
