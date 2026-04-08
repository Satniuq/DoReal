from __future__ import annotations

import argparse
import json

from common import dump_json, write_text
from settings import load_runtime_context
from resolve_state import resolve_state
from build_context import build_context_pack
from build_prompt import build_prompt_text
from openai_client import run_openai
from validator import validate_markdown_text
from publisher import publish_text


def cmd_status(args):
    ctx = load_runtime_context(args.project_root)
    state = resolve_state(ctx)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def cmd_next(args):
    ctx = load_runtime_context(args.project_root)
    state = resolve_state(ctx)
    pack = build_context_pack(ctx, state)
    prompt = build_prompt_text(state, pack)
    dump_json(ctx.runtime_root / '03_estado_runtime' / 'ultimo_estado.json', state)
    dump_json(ctx.runtime_root / '03_estado_runtime' / 'ultimo_context_pack.json', pack)
    write_text(ctx.runtime_root / '04_prompts_gerados' / f"{state['expected_artifact']}.prompt.txt", prompt)
    print(json.dumps({
        'next_artifact_kind': state['next_artifact_kind'],
        'expected_artifact': state['expected_artifact'],
        'expected_folder': state['expected_folder'],
        'prompt_file': str(ctx.runtime_root / '04_prompts_gerados' / f"{state['expected_artifact']}.prompt.txt"),
    }, ensure_ascii=False, indent=2))
    return 0


def _single_artifact(ctx, model: str | None = None, dry_run: bool = False) -> tuple[bool, str]:
    state = resolve_state(ctx)
    if state.get('blocked'):
        return False, state.get('reason', 'Estado bloqueado.')
    pack = build_context_pack(ctx, state)
    prompt = build_prompt_text(state, pack)

    prompt_path = ctx.runtime_root / '04_prompts_gerados' / f"{state['expected_artifact']}.prompt.txt"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(prompt_path, prompt)
    dump_json(ctx.runtime_root / '03_estado_runtime' / 'ultimo_estado.json', state)
    dump_json(ctx.runtime_root / '03_estado_runtime' / 'ultimo_context_pack.json', pack)

    if dry_run:
        return True, f"Dry-run ok: {state['expected_artifact']}"

    retries = int(ctx.settings.get('retries_per_artifact', 3))
    last_errors = []
    for attempt in range(1, retries + 1):
        try:
            run = run_openai(ctx, prompt, model=model)
        except Exception as exc:
            last_errors = [str(exc)]
            dump_json(ctx.logs_dir / 'auditoria' / f"{state['expected_artifact']}.retry{attempt}.error.json", {'errors': last_errors})
            if attempt < retries:
                continue
            return False, 'Falhou após 3 tentativas: ' + '; '.join(last_errors)

        text = run['output_text'].strip()
        validation = validate_markdown_text(state['next_artifact_kind'], state['expected_artifact'], text)
        dump_json(ctx.logs_dir / 'auditoria' / f"{run['run_id']}__validation.json", validation)
        if validation['verdict'] == 'VALID':
            target = publish_text(ctx, state['expected_folder'], state['expected_artifact'], text)
            return True, f"[tentativa {attempt}/{retries}] publicado: {target}"
        last_errors = validation['errors']
        prompt = (
            prompt
            + "\n\nCORREÇÃO OBRIGATÓRIA DA NOVA TENTATIVA:\n"
            + "- a tentativa anterior falhou formalmente;\n"
            + "- corrige estritamente estes problemas: "
            + '; '.join(last_errors)
            + "\n- reescreve a peça integralmente e entrega apenas markdown final.\n"
        )
        write_text(ctx.runtime_root / '04_prompts_gerados' / f"{state['expected_artifact']}.retry{attempt}.prompt.txt", prompt)
    return False, 'Falhou após 3 tentativas: ' + '; '.join(last_errors)


def cmd_run_once(args):
    ctx = load_runtime_context(args.project_root)
    ok, msg = _single_artifact(ctx, model=args.model, dry_run=args.dry_run)
    print(msg)
    return 0 if ok else 1


def cmd_run_all(args):
    ctx = load_runtime_context(args.project_root)
    max_steps = args.steps or int(ctx.settings.get('default_max_steps', 20))
    for i in range(max_steps):
        ok, msg = _single_artifact(ctx, model=args.model, dry_run=args.dry_run)
        print(f"[{i+1}/{max_steps}] {msg}")
        if args.dry_run:
            return 0
        if not ok:
            return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description='Automatizador das faixas expositivas controladas.')
    parser.add_argument('--project-root', default=None)
    sub = parser.add_subparsers(dest='cmd', required=True)

    sub.add_parser('status')
    sub.add_parser('next')
    p1 = sub.add_parser('run-once')
    p1.add_argument('--dry-run', action='store_true')
    p1.add_argument('--model', default=None)
    p2 = sub.add_parser('run-all')
    p2.add_argument('--steps', type=int, default=None)
    p2.add_argument('--dry-run', action='store_true')
    p2.add_argument('--model', default=None)

    args = parser.parse_args()
    if args.cmd == 'status':
        raise SystemExit(cmd_status(args))
    if args.cmd == 'next':
        raise SystemExit(cmd_next(args))
    if args.cmd == 'run-once':
        raise SystemExit(cmd_run_once(args))
    if args.cmd == 'run-all':
        raise SystemExit(cmd_run_all(args))


if __name__ == '__main__':
    main()
