#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

DEFAULT_TOP_N = 25
DEFAULT_MIN_SCORE = 8.0
DEFAULT_MIN_TERM_LEN = 4
DEFAULT_STOPWORDS = {
    'como','para','entre','sobre','pelos','pelas','pela','pelo','dos','das','nas','nos','uma','umas','uns','com',
    'sem','que','quando','onde','deve','deves','ser','sao','são','mais','menos','muito','muita','muitas','muitos',
    'algo','real','níveis','niveis','forma','formas','tipo','tipos','exige','antes','nova','novo','novos','novas',
    'porque','esta','este','isto','essa','esse','aquela','aquele','their','from','into','then','also','than',
    'problema','sistema','sistemas','funcional','funcionais','seguinte','quanto','possivel','possível','especialmente',
    'provisoria','provisória','tese','qualitativa','qualitativamente','surge','surgimento','causal','causalidade'
}

DEFAULT_HINTS = [
    'consciência', 'mediação', 'representação', 'símbolo', 'linguagem', 'reflexividade',
    'ponto de vista', 'erro categorial', 'erro de escala', 'dualismo', 'panpsiquismo',
    'localidade', 'critério', 'absolutização', 'campo', 'escala', 'media', 'representa',
    'simbol', 'consci', 'reflex', 'erro', 'crit'
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def normalize_spaces(text: str) -> str:
    return ' '.join((text or '').split())


def strip_accents(text: str) -> str:
    return ''.join(ch for ch in unicodedata.normalize('NFKD', text) if not unicodedata.combining(ch))


def normalize_text(text: str) -> str:
    text = strip_accents((text or '').lower())
    text = re.sub(r'[^a-z0-9\s_-]', ' ', text)
    return normalize_spaces(text)


def tokenize(text: str, min_len: int = DEFAULT_MIN_TERM_LEN) -> List[str]:
    toks = re.findall(r'[a-z0-9_/-]+', normalize_text(text))
    return [t for t in toks if len(t) >= min_len and t not in DEFAULT_STOPWORDS and not t.isdigit()]


def serialize_for_search(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(data)


def read_json(path: Path) -> Any:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def relpath_str(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace('\\', '/')
    except Exception:
        return str(path.resolve())


def project_root_from_paths(explicit_root: Optional[Path], explicit_input: Optional[Path]) -> Path:
    if explicit_root:
        return explicit_root.resolve()
    if explicit_input:
        return explicit_input.resolve().parent.parent.parent
    return Path.cwd().resolve()


def resolve_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    direct = safe_dict(payload.get('snapshot_dossier'))
    if direct:
        return direct
    return safe_dict(safe_dict(payload.get('confronto')).get('dossier_snapshot'))


def build_dossier_queries(snapshot: Dict[str, Any], extra_terms: Sequence[str]) -> Dict[str, List[str]]:
    fields = {
        'pergunta_central': normalize_spaces(snapshot.get('pergunta_central', '')),
        'descricao_do_confronto': normalize_spaces(snapshot.get('descricao_do_confronto', '')),
        'tese_canonica_provisoria': normalize_spaces(snapshot.get('tese_canonica_provisoria', '')),
        'articulacao_estrutural': normalize_spaces(snapshot.get('articulacao_estrutural', '')),
    }

    extracted_terms: List[str] = []
    for value in fields.values():
        extracted_terms.extend(tokenize(value))

    # reforça bigramas semânticos curtos
    combined = ' '.join(v for v in fields.values() if v)
    bigrams = re.findall(r'([A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ]+)', combined)
    candidate_phrases = []
    for bg in bigrams:
        nbg = normalize_text(bg)
        toks = nbg.split()
        if len(toks) == 2 and all(len(t) >= 4 and t not in DEFAULT_STOPWORDS for t in toks):
            candidate_phrases.append(' '.join(toks))

    ranked_terms = [t for t, _ in Counter(extracted_terms).most_common(40)]
    ranked_phrases = [p for p, _ in Counter(candidate_phrases).most_common(20)]

    extras = [normalize_spaces(x) for x in extra_terms if normalize_spaces(x)]

    return {
        'campos_textuais': [v for v in fields.values() if v],
        'termos_nucleares': ranked_terms,
        'frases_nucleares': ranked_phrases,
        'hints_manuais': extras,
    }



def compute_doc_frequencies(fragments: Sequence[Dict[str, Any]]) -> Counter[str]:
    df: Counter[str] = Counter()
    for frag in fragments:
        texto = normalize_spaces(frag.get('texto_fragmento', ''))
        trat = serialize_for_search(frag.get('tratamento_filosofico')) if frag.get('tratamento_filosofico') else ''
        all_text = f"{texto}\n{trat}\n{frag.get('funcao_textual_dominante') or ''}"
        toks = set(tokenize(all_text))
        df.update(toks)
    return df


def weighted_term_hits(text: str, terms: Sequence[str], doc_freq: Counter[str], total_docs: int) -> Tuple[List[str], float]:
    txt = normalize_text(text)
    found: List[str] = []
    score = 0.0
    for term in terms:
        nterm = normalize_text(term)
        if not nterm:
            continue
        matched = False
        if ' ' in nterm:
            matched = nterm in txt
            df = min(doc_freq.get(tok, 1) for tok in nterm.split()) if nterm.split() else 1
        else:
            matched = nterm in txt
            df = doc_freq.get(nterm, 1)
        if matched:
            found.append(term)
            idf = math.log((1 + total_docs) / (1 + df)) + 1.0
            score += max(0.4, min(idf, 2.5))
    return found, score


def hit_terms(text: str, terms: Sequence[str]) -> List[str]:
    txt = normalize_text(text)
    found = []
    for term in terms:
        nterm = normalize_text(term)
        if not nterm:
            continue
        if ' ' in nterm:
            if nterm in txt:
                found.append(term)
        else:
            if nterm in txt:
                found.append(term)
    return found


def score_fragment(fragment: Dict[str, Any], dossier_queries: Dict[str, List[str]], doc_freq: Counter[str], total_docs: int) -> Dict[str, Any]:
    texto = normalize_spaces(fragment.get('texto_fragmento', ''))
    tratamento = fragment.get('tratamento_filosofico')
    trat_text = serialize_for_search(tratamento) if tratamento else ''
    cad = safe_dict(fragment.get('cadencia'))
    lig = safe_dict(fragment.get('ligacoes_arvore'))
    impacto = safe_list(fragment.get('impacto_no_mapa_registos'))

    all_text = '\n'.join([texto, trat_text, fragment.get('funcao_textual_dominante') or '', serialize_for_search(cad)])
    matched_terms, weighted_term_score = weighted_term_hits(all_text, dossier_queries['termos_nucleares'], doc_freq, total_docs)
    matched_phrases, weighted_phrase_score = weighted_term_hits(all_text, dossier_queries['frases_nucleares'], doc_freq, total_docs)
    matched_hints = hit_terms(all_text, dossier_queries['hints_manuais'])

    score = 0.0
    reasons: List[str] = []

    term_score = min(weighted_term_score, 12.0)
    if term_score:
        score += term_score
        reasons.append(f'termos_dossier:{len(set(matched_terms))}')

    phrase_score = min(weighted_phrase_score * 1.2, 8.0)
    if phrase_score:
        score += phrase_score
        reasons.append(f'frases_dossier:{len(set(matched_phrases))}')

    hint_score = min(len(set(matched_hints)) * 1.5, 12.0)
    if hint_score:
        score += hint_score
        reasons.append(f'hints:{len(set(matched_hints))}')

    if tratamento:
        score += 5.0
        reasons.append('tratamento_filosofico')
        confianca = normalize_text(str(safe_dict(tratamento).get('confianca_tratamento_filosofico', '')))
        if 'alta' in confianca:
            score += 2.0
            reasons.append('tratamento_confianca_alta')
        elif 'media' in confianca or 'média' in confianca:
            score += 1.0
            reasons.append('tratamento_confianca_media')

    centralidade = normalize_text(str(cad.get('centralidade', '')))
    if 'nuclear' in centralidade:
        score += 3.0
        reasons.append('centralidade_nuclear')
    elif 'alta' in centralidade:
        score += 2.0
        reasons.append('centralidade_alta')
    elif 'media' in centralidade:
        score += 1.0
        reasons.append('centralidade_media')

    estatuto = normalize_text(str(cad.get('estatuto_no_percurso', '')))
    if 'nuclear' in estatuto:
        score += 2.0
        reasons.append('estatuto_nuclear')
    elif 'estrutural' in estatuto or 'transicao' in estatuto or 'transicao' in estatuto:
        score += 1.0
        reasons.append('estatuto_estrutural_ou_transicao')

    funcao = normalize_text(str(fragment.get('funcao_textual_dominante', '')))
    if any(x in funcao for x in ['distin', 'crit', 'objec', 'problema', 'defin', 'tens', 'media', 'transi']):
        score += 1.5
        reasons.append('funcao_relevante')

    lig_count = sum(1 for key in ('microlinha_ids', 'ramo_ids', 'percurso_ids', 'argumento_ids', 'convergencia_ids') if safe_list(lig.get(key)))
    if lig_count:
        score += min(lig_count * 0.5, 2.5)
        reasons.append(f'ligacoes_arvore:{lig_count}')

    if impacto:
        score += min(len(impacto) * 0.5, 3.0)
        reasons.append(f'impacto_mapa:{len(impacto)}')

    if any(p in normalize_text(texto) for p in ['nao e', 'mas', 'sem', 'entre', 'ao mesmo tempo', 'nao autoriza', 'erro', 'criterio']):
        score += 1.5
        reasons.append('estrutura_distintiva')

    proposicoes = sorted({row.get('proposicao_id') for row in impacto if isinstance(row, dict) and row.get('proposicao_id')})

    return {
        'id': fragment.get('id'),
        'origem_id': fragment.get('origem_id'),
        'ordem_no_ficheiro': fragment.get('ordem_no_ficheiro'),
        'score': round(score, 3),
        'motivos': reasons,
        'matched_terms': sorted(set(matched_terms)),
        'matched_phrases': sorted(set(matched_phrases)),
        'matched_hints': sorted(set(matched_hints)),
        'texto_fragmento': texto,
        'texto_curto': fragment.get('texto_curto') or texto,
        'tratamento_filosofico': tratamento,
        'cadencia': cad,
        'funcao_textual_dominante': fragment.get('funcao_textual_dominante'),
        'tipo_unidade': fragment.get('tipo_unidade'),
        'ficheiro_origem': fragment.get('ficheiro_origem'),
        'proposicoes_impactadas': proposicoes,
        'impacto_no_mapa_registos': impacto,
        'ligacoes_arvore': lig,
        'estado_validacao': fragment.get('estado_validacao'),
        'estado_excecao': fragment.get('estado_excecao'),
        'excecao_ids': safe_list(fragment.get('excecao_ids')),
    }


def build_markdown(confronto_id: str, input_json: Path, project_root: Path, snapshot: Dict[str, Any], dossier_queries: Dict[str, List[str]], sample: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append(f'# {confronto_id} — Fragmentos relevantes para o dossier')
    lines.append('')
    lines.append(f'- gerado_em: `{utc_now_iso()}`')
    lines.append(f'- fonte: `{relpath_str(input_json, project_root)}`')
    lines.append(f'- n_fragmentos_selecionados: **{len(sample)}**')
    lines.append('')
    lines.append('## Snapshot do dossier')
    lines.append('')
    for key in ('pergunta_central', 'descricao_do_confronto', 'tese_canonica_provisoria', 'articulacao_estrutural'):
        if snapshot.get(key):
            lines.append(f'- **{key}**: {snapshot.get(key)}')
    lines.append('')
    lines.append('## Vocabulário nuclear extraído do dossier')
    lines.append('')
    lines.append(f"- termos_nucleares: {', '.join(dossier_queries['termos_nucleares'][:30])}")
    if dossier_queries['frases_nucleares']:
        lines.append(f"- frases_nucleares: {', '.join(dossier_queries['frases_nucleares'][:15])}")
    if dossier_queries['hints_manuais']:
        lines.append(f"- hints_manuais: {', '.join(dossier_queries['hints_manuais'])}")
    lines.append('')
    lines.append('## Fragmentos selecionados')
    lines.append('')

    for i, frag in enumerate(sample, 1):
        lines.append(f"### {i}. {frag['id']} — score {frag['score']}")
        lines.append('')
        meta = [
            f"origem_id={frag.get('origem_id')}",
            f"ordem_no_ficheiro={frag.get('ordem_no_ficheiro')}",
            f"tipo_unidade={frag.get('tipo_unidade')}",
            f"funcao={frag.get('funcao_textual_dominante')}",
            f"estado_validacao={frag.get('estado_validacao')}",
        ]
        lines.append('- ' + ' | '.join(meta))
        if frag.get('proposicoes_impactadas'):
            lines.append(f"- proposicoes_impactadas: {', '.join(frag['proposicoes_impactadas'])}")
        if frag.get('motivos'):
            lines.append(f"- motivos: {', '.join(frag['motivos'])}")
        if frag.get('matched_terms'):
            lines.append(f"- termos_do_dossier_encontrados: {', '.join(frag['matched_terms'][:25])}")
        if frag.get('matched_phrases'):
            lines.append(f"- frases_do_dossier_encontradas: {', '.join(frag['matched_phrases'])}")
        if frag.get('matched_hints'):
            lines.append(f"- hints_encontrados: {', '.join(frag['matched_hints'])}")
        lines.append('')
        lines.append('#### Texto integral')
        lines.append('')
        lines.append(frag.get('texto_fragmento') or '[sem texto]')
        lines.append('')
        if frag.get('tratamento_filosofico'):
            lines.append('#### Tratamento filosófico')
            lines.append('')
            lines.append('```json')
            lines.append(json.dumps(frag['tratamento_filosofico'], ensure_ascii=False, indent=2))
            lines.append('```')
            lines.append('')
    return '\n'.join(lines).strip() + '\n'


def build_report(confronto_id: str, sample: List[Dict[str, Any]], dossier_queries: Dict[str, List[str]], min_score: float, top_n: int) -> str:
    lines = [
        f'RELATÓRIO — FRAGMENTOS RELEVANTES PARA O DOSSIER — {confronto_id}',
        f'gerado_em: {utc_now_iso()}',
        f'min_score: {min_score}',
        f'top_n: {top_n}',
        '',
        'Resumo dos critérios efetivos:',
        '- overlap lexical e frásico com o snapshot do dossier;',
        '- hints manuais para temas que o dossier pode estar a formular mal ou incompletamente;',
        '- tratamento filosófico, centralidade, função textual, ligações de árvore e impacto no mapa;',
        '- sem truncar o texto integral no ficheiro markdown.',
        ''
    ]
    if sample:
        lines.append('Fragmentos mais relevantes:')
        for frag in sample:
            lines.append(
                f"- {frag['id']} | score={frag['score']} | termos={','.join(frag.get('matched_terms', [])[:10])} | hints={','.join(frag.get('matched_hints', [])[:10])}"
            )
    else:
        lines.append('Nenhum fragmento passou o limiar.')
    lines.append('')
    term_counter = Counter()
    hint_counter = Counter()
    for frag in sample:
        term_counter.update(frag.get('matched_terms', []))
        hint_counter.update(frag.get('matched_hints', []))
    if term_counter:
        lines.append('Termos do dossier mais encontrados:')
        for term, count in term_counter.most_common(20):
            lines.append(f'- {term}: {count}')
        lines.append('')
    if hint_counter:
        lines.append('Hints mais encontrados:')
        for term, count in hint_counter.most_common(20):
            lines.append(f'- {term}: {count}')
        lines.append('')
    lines.append('status: ok' if sample else 'status: sem_resultados')
    return '\n'.join(lines).strip() + '\n'


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Seleciona fragmentos realmente relevantes para o dossier sem cortar texto.')
    p.add_argument('--confronto', required=True)
    p.add_argument('--input-json', type=Path, required=True)
    p.add_argument('--project-root', type=Path)
    p.add_argument('--top-n', type=int, default=DEFAULT_TOP_N)
    p.add_argument('--min-score', type=float, default=DEFAULT_MIN_SCORE)
    p.add_argument('--extra-terms', default='')
    p.add_argument('--output-prefix', default='v2')
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    confronto_id = normalize_spaces(args.confronto).upper()
    payload = read_json(args.input_json.resolve())
    fragments = safe_list(payload.get('fragmentos'))
    if not fragments:
        raise SystemExit('ERRO FATAL: sem fragmentos')

    project_root = project_root_from_paths(args.project_root, args.input_json)
    snapshot = resolve_snapshot(payload)
    extra_terms = [x.strip() for x in args.extra_terms.split(',') if x.strip()]
    merged_hints = DEFAULT_HINTS + extra_terms
    dossier_queries = build_dossier_queries(snapshot, merged_hints)

    doc_freq = compute_doc_frequencies([safe_dict(f) for f in fragments])
    scored = [score_fragment(safe_dict(f), dossier_queries, doc_freq, len(fragments)) for f in fragments]
    filtered = [row for row in scored if row['score'] >= args.min_score]
    filtered.sort(
        key=lambda x: (
            -x['score'],
            -len(x.get('matched_phrases', [])),
            -len(x.get('matched_terms', [])),
            str(x.get('id') or '')
        )
    )
    sample = filtered[:max(1, args.top_n)]

    stem = f'{confronto_id}_fragmentos_relevantes_dossier_{args.output_prefix}'
    out_dir = args.input_json.resolve().parent / 'samples'
    out_json = out_dir / f'{stem}.json'
    out_md = out_dir / f'{stem}.md'
    out_report = project_root / '02_outputs' / f'relatorio_{stem}.txt'

    payload_out = {
        'meta': {
            'script': Path(__file__).name,
            'gerado_em': utc_now_iso(),
            'confronto_id': confronto_id,
            'fonte_base_fragmentaria': str(args.input_json.resolve()),
            'top_n': args.top_n,
            'min_score': args.min_score,
            'output_prefix': args.output_prefix,
        },
        'snapshot_dossier': snapshot,
        'queries_dossier': dossier_queries,
        'estatisticas': {
            'n_fragmentos_base': len(fragments),
            'n_fragmentos_scored': len(scored),
            'n_fragmentos_filtrados': len(filtered),
            'n_fragmentos_sample': len(sample),
        },
        'sample': sample,
    }

    write_json(out_json, payload_out)
    write_text(
        out_md,
        build_markdown(
            confronto_id,
            args.input_json.resolve(),
            project_root,
            snapshot,
            dossier_queries,
            sample
        )
    )
    write_text(
        out_report,
        build_report(confronto_id, sample, dossier_queries, args.min_score, args.top_n)
    )

    print(out_json)
    print(out_md)
    print(out_report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
