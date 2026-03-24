#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

STOPWORDS = {
    'a', 'o', 'e', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'nos', 'nas',
    'por', 'para', 'com', 'sem', 'um', 'uma', 'uns', 'umas', 'que', 'se', 'ao',
    'aos', 'à', 'às', 'como', 'mais', 'menos', 'já', 'ou', 'ser', 'é', 'foi',
    'são', 'era', 'não', 'sim', 'lhe', 'lhes', 'seu', 'sua', 'seus', 'suas', 'eu',
    'tu', 'ele', 'ela', 'eles', 'elas', 'isto', 'isso', 'aquilo', 'num', 'numa',
    'entre', 'sobre', 'também', 'muito', 'muita', 'muitos', 'muitas', 'todo',
    'toda', 'todos', 'todas', 'cada', 'há', 'nosso', 'nossa', 'nossos', 'nossas',
    'teu', 'tua', 'teus', 'tuas', 'meu', 'minha', 'meus', 'minhas', 'sua', 'se',
    'porque', 'pois', 'onde', 'quando', 'qual', 'quais', 'qualquer', 'mesmo', 'mesma'
}

GENERIC_LOW_SIGNAL_TERMS = {
    'problema', 'problemas', 'questao', 'questões', 'questoes', 'sistema', 'sistemas',
    'funcional', 'funcionais', 'processo', 'processos', 'realidade', 'teoria',
    'teorico', 'teórica', 'teorica', 'campo', 'campos', 'relação', 'relacao',
    'relações', 'relacoes', 'nível', 'nivel', 'níveis', 'niveis', 'coisa', 'coisas',
    'modo', 'modos', 'forma', 'formas', 'estrutura', 'estruturas', 'dinamica',
    'dinâmica', 'dinamicas', 'dinâmicas', 'situação', 'situacao', 'caso', 'casos'
}

DEFAULT_HINTS = [
    'consci', 'consciência', 'consciência reflexiva', 'media', 'mediação',
    'representa', 'representação', 'simbol', 'símbolo', 'linguagem', 'reflex',
    'ponto de vista', 'erro', 'erro categorial', 'erro de escala', 'dualismo',
    'panpsiquismo', 'continuidade', 'continuidade ontológica', 'localidade',
    'local', 'real', 'interioridade', 'apreensão', 'apreensao', 'mediação simbólica'
]

PROFILE_CONFIGS = {
    'nucleo_consciencia_no_real': {
        'label': 'Núcleo: consciência no real',
        'description': 'Fragmentos sobre consciência como modo, processo ou relação no real, sem exterioridade ontológica.',
        'hints': [
            'consciência', 'consci', 'consciência reflexiva', 'interioridade', 'eu',
            'localidade', 'local', 'real', 'relação no real', 'continuidade ontológica',
            'apreensão', 'ponto de vista', 'não está fora do real', 'no real'
        ],
        'boost_terms': ['consciência', 'real', 'local', 'interioridade', 'apreensão'],
        'anti_hints': ['emergência', 'novidade qualitativa'],
    },
    'mediacao_representacao_simbolo': {
        'label': 'Núcleo: mediação, representação e símbolo',
        'description': 'Fragmentos sobre mediação, representação, símbolo, linguagem e articulação operativa do real.',
        'hints': [
            'mediação', 'media', 'representação', 'representa', 'símbolo', 'simbol',
            'linguagem', 'linguístico', 'signo', 'significação', 'enquadramento',
            'fixação', 'comum entre diferenças', 'mediação simbólica'
        ],
        'boost_terms': ['mediação', 'representação', 'símbolo', 'linguagem', 'signo'],
        'anti_hints': ['emergência'],
    },
    'erro_categorial_dualismo_panpsiquismo': {
        'label': 'Núcleo: erro categorial, dualismo e panpsiquismo',
        'description': 'Fragmentos críticos de separações ontológicas, erros de escala, dualismos e pseudoproblemas.',
        'hints': [
            'erro categorial', 'erro', 'erro de escala', 'dualismo', 'panpsiquismo',
            'absolutização', 'absolutiza', 'separação', 'ponte', 'pseudo-problema',
            'categoria', 'Nagel', 'Wittgenstein', 'Kant', 'interioridade fantasmagórica'
        ],
        'boost_terms': ['erro', 'dualismo', 'panpsiquismo', 'separação', 'ponte'],
        'anti_hints': ['novidade qualitativa'],
    },
    'emergencia_passagem_niveis': {
        'label': 'Núcleo: emergência e passagem de níveis',
        'description': 'Fragmentos sobre surgimento, novidade qualitativa, reorganização e passagem entre níveis.',
        'hints': [
            'emergência', 'emerge', 'surgimento', 'novidade qualitativa', 'passagem',
            'salto', 'níveis', 'reorganização', 'reorganizações', 'unidade funcional',
            'qualitativamente novo', 'aparecimento'
        ],
        'boost_terms': ['emergência', 'novidade', 'passagem', 'salto', 'reorganização'],
        'anti_hints': ['dualismo'],
    },
}

PHRASE_MIN_LEN = 12
TERM_MIN_LEN = 4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def safe_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def strip_accents_basic(text: str) -> str:
    repl = str.maketrans({
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'Á': 'a', 'À': 'a', 'Â': 'a', 'Ã': 'a', 'Ä': 'a',
        'É': 'e', 'È': 'e', 'Ê': 'e', 'Ë': 'e',
        'Í': 'i', 'Ì': 'i', 'Î': 'i', 'Ï': 'i',
        'Ó': 'o', 'Ò': 'o', 'Ô': 'o', 'Õ': 'o', 'Ö': 'o',
        'Ú': 'u', 'Ù': 'u', 'Û': 'u', 'Ü': 'u',
        'Ç': 'c'
    })
    return text.translate(repl)


def normalize(text: str) -> str:
    text = strip_accents_basic(text or '').lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    text = normalize(text)
    toks = re.findall(r'[a-z0-9_\-]+', text)
    out: List[str] = []
    for t in toks:
        if len(t) < TERM_MIN_LEN:
            continue
        if t in STOPWORDS:
            continue
        out.append(t)
    return out


def get_fragment_text(fragment: Dict[str, Any]) -> str:
    candidates = [
        fragment.get('texto_integral'),
        fragment.get('texto'),
        fragment.get('fragmento'),
        fragment.get('conteudo'),
        fragment.get('text'),
        fragment.get('body'),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return ''


def extract_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    confronto = safe_dict(payload.get('confronto'))
    snapshot = safe_dict(confronto.get('dossier_snapshot'))
    if snapshot:
        return snapshot
    return safe_dict(payload.get('snapshot_dossier'))


def extract_fragments(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ('fragmentos', 'base_fragmentaria', 'itens', 'items', 'sample'):
        value = payload.get(key)
        if isinstance(value, list):
            return [safe_dict(v) for v in value]
    return []


def harvest_strings(obj: Any) -> List[str]:
    out: List[str] = []
    if isinstance(obj, str):
        s = obj.strip()
        if s:
            out.append(s)
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(harvest_strings(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(harvest_strings(v))
    return out


def select_candidate_phrases(snapshot: Dict[str, Any]) -> List[str]:
    phrases: List[str] = []
    for s in harvest_strings(snapshot):
        s_norm = normalize(s)
        if len(s_norm) >= PHRASE_MIN_LEN and ' ' in s_norm:
            phrases.append(s.strip())
    seen = set()
    result = []
    for p in phrases:
        n = normalize(p)
        if n not in seen:
            seen.add(n)
            result.append(p)
    return result[:60]


def select_candidate_terms(snapshot: Dict[str, Any], extra_terms: List[str]) -> List[str]:
    bag: List[str] = []
    for s in harvest_strings(snapshot):
        bag.extend(tokenize(s))
    bag.extend(tokenize(' '.join(extra_terms)))
    freq = Counter(bag)
    ranked = []
    for term, _count in freq.most_common():
        if term in GENERIC_LOW_SIGNAL_TERMS:
            continue
        if len(term) < TERM_MIN_LEN:
            continue
        ranked.append(term)
    return ranked[:80]


def build_dossier_queries(snapshot: Dict[str, Any], extra_terms: List[str]) -> Dict[str, Any]:
    phrases = select_candidate_phrases(snapshot)
    terms = select_candidate_terms(snapshot, extra_terms)
    hints: List[str] = []
    seen = set()
    for item in extra_terms:
        n = normalize(item)
        if n and n not in seen:
            seen.add(n)
            hints.append(item)
    return {'phrases': phrases, 'terms': terms, 'hints': hints}


def compute_doc_frequencies(fragments: List[Dict[str, Any]]) -> Counter:
    df: Counter = Counter()
    for fr in fragments:
        toks = set(tokenize(get_fragment_text(fr)))
        for t in toks:
            df[t] += 1
    return df


def parse_float(x: Any, default: float = 0.0) -> float:
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x.replace(',', '.'))
        except ValueError:
            return default
    return default


def phrase_matches(text_norm: str, phrases: Iterable[str]) -> List[str]:
    return [phrase for phrase in phrases if normalize(phrase) and normalize(phrase) in text_norm]


def term_matches(tokens: List[str], terms: Iterable[str]) -> List[str]:
    toks = set(tokens)
    matches = []
    for term in terms:
        t = normalize(term)
        if not t:
            continue
        if t in toks:
            matches.append(term)
        elif any(tok.startswith(t) or t.startswith(tok) for tok in toks if len(tok) >= 4):
            matches.append(term)
    return matches


def hint_matches(text_norm: str, tokens: List[str], hints: Iterable[str]) -> List[str]:
    toks = set(tokens)
    matches = []
    for hint in hints:
        h = normalize(hint)
        if not h:
            continue
        if ' ' in h:
            if h in text_norm:
                matches.append(hint)
        else:
            if any(tok.startswith(h) or h.startswith(tok) for tok in toks if len(tok) >= 4):
                matches.append(hint)
    return matches


def idf(term: str, doc_freq: Counter, total_docs: int) -> float:
    df = doc_freq.get(term, 0)
    return math.log((1 + total_docs) / (1 + df)) + 1.0


def collect_reasons(fragment: Dict[str, Any], matches_phrase: List[str], matches_term: List[str], matches_hint: List[str]) -> List[str]:
    reasons = []
    if matches_phrase:
        reasons.append(f"frases do dossier: {', '.join(matches_phrase[:4])}")
    if matches_term:
        reasons.append(f"termos do dossier: {', '.join(matches_term[:6])}")
    if matches_hint:
        reasons.append(f"hints semânticos: {', '.join(matches_hint[:6])}")

    tratamento = parse_float(fragment.get('tratamento_filosofico') or fragment.get('score_tratamento_filosofico'))
    if tratamento > 0:
        reasons.append(f"tratamento filosófico={tratamento:g}")

    centralidade = parse_float(fragment.get('centralidade_lexical') or fragment.get('score_centralidade_lexical'))
    if centralidade > 0:
        reasons.append(f"centralidade lexical={centralidade:g}")

    cadencia = parse_float(fragment.get('cadencia_nuclear') or fragment.get('score_cadencia_nuclear'))
    if cadencia > 0:
        reasons.append(f"cadência nuclear={cadencia:g}")

    funcao = fragment.get('funcao_textual') or fragment.get('função_textual')
    if isinstance(funcao, str) and funcao.strip():
        reasons.append(f"função textual={funcao.strip()}")

    arv = fragment.get('ligacoes_arvore') or fragment.get('ligações_árvore') or fragment.get('ligacoes_na_arvore')
    if isinstance(arv, list) and arv:
        reasons.append(f"ligações árvore={len(arv)}")

    impacto = fragment.get('impacto_no_mapa_registos') or fragment.get('proposicoes_impactadas')
    if isinstance(impacto, list) and impacto:
        reasons.append(f"impacto no mapa={len(impacto)}")
    return reasons


def get_structural_score(fragment: Dict[str, Any]) -> float:
    tratamento = parse_float(fragment.get('tratamento_filosofico') or fragment.get('score_tratamento_filosofico'))
    centralidade = parse_float(fragment.get('centralidade_lexical') or fragment.get('score_centralidade_lexical'))
    cadencia = parse_float(fragment.get('cadencia_nuclear') or fragment.get('score_cadencia_nuclear'))
    structural_score = (
        min(tratamento, 5.0) * 0.9 +
        min(centralidade, 5.0) * 0.45 +
        min(cadencia, 5.0) * 0.35
    )
    funcao = normalize(str(fragment.get('funcao_textual') or fragment.get('função_textual') or ''))
    if funcao in {'tese', 'nucleo', 'núcleo', 'critica', 'crítica', 'definicao', 'definição'}:
        structural_score += 1.1
    elif funcao:
        structural_score += 0.35
    arv = fragment.get('ligacoes_arvore') or fragment.get('ligações_árvore') or fragment.get('ligacoes_na_arvore')
    if isinstance(arv, list):
        structural_score += min(len(arv), 6) * 0.3
    impacto = fragment.get('impacto_no_mapa_registos') or fragment.get('proposicoes_impactadas')
    if isinstance(impacto, list):
        structural_score += min(len(impacto), 8) * 0.45
    return structural_score


def score_fragment(fragment: Dict[str, Any], dossier_queries: Dict[str, Any], doc_freq: Counter, total_docs: int) -> Dict[str, Any]:
    text = get_fragment_text(fragment)
    text_norm = normalize(text)
    tokens = tokenize(text)

    matches_phrase = phrase_matches(text_norm, dossier_queries.get('phrases', []))
    matches_term = term_matches(tokens, dossier_queries.get('terms', []))
    matches_hint = hint_matches(text_norm, tokens, dossier_queries.get('hints', []))

    term_score = 0.0
    matched_term_norms = set()
    for term in matches_term:
        tn = normalize(term)
        if tn in matched_term_norms:
            continue
        matched_term_norms.add(tn)
        term_score += 0.15 if tn in GENERIC_LOW_SIGNAL_TERMS else 0.60 * idf(tn, doc_freq, total_docs)

    phrase_score = min(len(matches_phrase), 6) * 2.0
    hint_score = min(len(matches_hint), 8) * 1.25
    structural_score = get_structural_score(fragment)
    score = phrase_score + hint_score + term_score + structural_score

    out = dict(fragment)
    out['score'] = round(score, 4)
    out['matched_phrases'] = matches_phrase
    out['matched_terms'] = matches_term
    out['matched_hints'] = matches_hint
    out['reasons'] = collect_reasons(fragment, matches_phrase, matches_term, matches_hint)
    out['texto_integral'] = text
    return out


def score_profile(fragment: Dict[str, Any], profile_name: str, profile_cfg: Dict[str, Any], doc_freq: Counter, total_docs: int) -> Dict[str, Any]:
    text = get_fragment_text(fragment)
    text_norm = normalize(text)
    tokens = tokenize(text)
    matches_hint = hint_matches(text_norm, tokens, profile_cfg.get('hints', []))
    matches_boost = term_matches(tokens, profile_cfg.get('boost_terms', []))
    anti_matches = hint_matches(text_norm, tokens, profile_cfg.get('anti_hints', []))

    hint_score = 0.0
    seen = set()
    for item in matches_hint:
        n = normalize(item)
        if n in seen:
            continue
        seen.add(n)
        hint_score += 1.75

    boost_score = 0.0
    seen_boost = set()
    for item in matches_boost:
        n = normalize(item)
        if n in seen_boost:
            continue
        seen_boost.add(n)
        boost_score += 0.65 * idf(n, doc_freq, total_docs)

    structural = get_structural_score(fragment) * 0.55
    anti_penalty = min(len(anti_matches), 3) * 0.45
    profile_score = hint_score + boost_score + structural - anti_penalty

    return {
        'profile_name': profile_name,
        'profile_label': profile_cfg.get('label', profile_name),
        'score': round(profile_score, 4),
        'matched_hints': matches_hint,
        'matched_boost_terms': matches_boost,
        'matched_anti_hints': anti_matches,
    }


def build_alignment_diagnosis(profile_stats: Dict[str, Dict[str, Any]], snapshot: Dict[str, Any]) -> Dict[str, Any]:
    dossier_text = normalize(' '.join(harvest_strings(snapshot)))
    dossier_profile_mentions = {}
    for name, cfg in PROFILE_CONFIGS.items():
        dossier_profile_mentions[name] = len(hint_matches(dossier_text, tokenize(dossier_text), cfg.get('hints', [])))

    ranking = sorted(
        profile_stats.items(),
        key=lambda kv: (-(kv[1].get('avg_top10_score', 0.0)), -(kv[1].get('top10_overlap_with_global', 0)), kv[0])
    )
    dominant_profile = ranking[0][0] if ranking else None
    dossier_declared_profile = max(dossier_profile_mentions.items(), key=lambda kv: kv[1])[0] if dossier_profile_mentions else None

    mismatch = False
    diagnosis_lines = []
    if dominant_profile and dossier_declared_profile and dominant_profile != dossier_declared_profile:
        mismatch = True
        diagnosis_lines.append(
            f"O dossier parece formular-se mais no eixo '{dossier_declared_profile}', mas os fragmentos mais fortes caem sobretudo em '{dominant_profile}'."
        )
    if dominant_profile == 'emergencia_passagem_niveis':
        diagnosis_lines.append('O eixo dominante dos fragmentos coincide mais diretamente com emergência/passagem de níveis.')
    elif dominant_profile:
        diagnosis_lines.append(
            f"O eixo dominante dos fragmentos não é emergência/passagem de níveis, mas sim '{PROFILE_CONFIGS[dominant_profile]['label']}'."
        )

    if profile_stats.get('emergencia_passagem_niveis', {}).get('avg_top10_score', 0.0) < max(
        profile_stats.get('nucleo_consciencia_no_real', {}).get('avg_top10_score', 0.0),
        profile_stats.get('mediacao_representacao_simbolo', {}).get('avg_top10_score', 0.0),
        profile_stats.get('erro_categorial_dualismo_panpsiquismo', {}).get('avg_top10_score', 0.0),
    ):
        diagnosis_lines.append('Há indício de que o dossier esteja a forçar uma moldura de emergência sobre material cujo centro efetivo é consciência/mediação/erro categorial.')
        mismatch = True

    return {
        'dossier_profile_mentions': dossier_profile_mentions,
        'dominant_profile': dominant_profile,
        'dossier_declared_profile': dossier_declared_profile,
        'mismatch_flag': mismatch,
        'diagnosis_lines': diagnosis_lines,
    }


def build_markdown(
    confronto_id: str,
    source_json: Path,
    project_root: Path,
    snapshot: Dict[str, Any],
    dossier_queries: Dict[str, Any],
    sample_global: List[Dict[str, Any]],
    profile_samples: Dict[str, List[Dict[str, Any]]],
    profile_stats: Dict[str, Dict[str, Any]],
    alignment: Dict[str, Any],
) -> str:
    lines: List[str] = []
    lines.append(f'# {confronto_id} — fragmentos relevantes para o dossier (v3)')
    lines.append('')
    lines.append(f'- Gerado em: {utc_now_iso()}')
    lines.append(f'- Fonte base fragmentária: `{source_json}`')
    lines.append(f'- Projeto base: `{project_root}`')
    lines.append(f'- Nº fragmentos no sample global: {len(sample_global)}')
    lines.append('')
    lines.append('## Diagnóstico de alinhamento')
    lines.append('')
    lines.append(f"- Perfil dominante dos fragmentos: {alignment.get('dominant_profile')}")
    lines.append(f"- Perfil mais sugerido pelo snapshot do dossier: {alignment.get('dossier_declared_profile')}")
    lines.append(f"- Desalinhamento sinalizado: {alignment.get('mismatch_flag')}")
    for item in alignment.get('diagnosis_lines', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append('## Snapshot do dossier')
    lines.append('')
    lines.append('```json')
    lines.append(json.dumps(snapshot, ensure_ascii=False, indent=2))
    lines.append('```')
    lines.append('')
    lines.append('## Queries derivadas do dossier')
    lines.append('')
    lines.append('### Frases')
    lines.extend([''] + [f'- {p}' for p in dossier_queries.get('phrases', [])])
    lines.append('')
    lines.append('### Termos')
    lines.append('')
    lines.append(', '.join(dossier_queries.get('terms', [])))
    lines.append('')
    lines.append('### Hints')
    lines.append('')
    lines.append(', '.join(dossier_queries.get('hints', [])))
    lines.append('')
    lines.append('## Perfis de relevância')
    lines.append('')
    for name, stats in profile_stats.items():
        lines.append(f"### {name} — {PROFILE_CONFIGS[name]['label']}")
        lines.append('')
        lines.append(f"- Média top10: {stats.get('avg_top10_score', 0.0):.3f}")
        lines.append(f"- Máximo: {stats.get('max_score', 0.0):.3f}")
        lines.append(f"- Overlap com sample global top10: {stats.get('top10_overlap_with_global', 0)}")
        lines.append(f"- Hints dominantes: {', '.join(stats.get('top_hints', []))}")
        lines.append('')
    lines.append('## Sample global')
    lines.append('')
    for idx, fr in enumerate(sample_global, start=1):
        fid = fr.get('id') or fr.get('fragmento_id') or f'fragmento_{idx:03d}'
        lines.append(f'### {idx}. {fid}')
        lines.append('')
        lines.append(f"- Score global: {fr.get('score')}")
        lines.append(f"- Melhor perfil: {fr.get('best_profile')}")
        profile_scores = fr.get('profile_scores', {})
        if profile_scores:
            score_bits = [f"{k}={v.get('score')}" for k, v in sorted(profile_scores.items())]
            lines.append(f"- Scores por perfil: {' | '.join(score_bits)}")
        if fr.get('matched_phrases'):
            lines.append(f"- Frases correspondentes: {', '.join(fr['matched_phrases'])}")
        if fr.get('matched_terms'):
            lines.append(f"- Termos correspondentes: {', '.join(fr['matched_terms'])}")
        if fr.get('matched_hints'):
            lines.append(f"- Hints correspondentes: {', '.join(fr['matched_hints'])}")
        lines.append(f"- Razões: {' | '.join(fr.get('reasons', []))}")
        lines.append('')
        lines.append('```text')
        lines.append(fr.get('texto_integral', ''))
        lines.append('```')
        lines.append('')
    for profile_name, items in profile_samples.items():
        lines.append(f"## Sample do perfil — {profile_name}")
        lines.append('')
        for idx, fr in enumerate(items, start=1):
            fid = fr.get('id') or fr.get('fragmento_id') or f'fragmento_{idx:03d}'
            pscore = safe_dict(fr.get('profile_scores')).get(profile_name, {}).get('score')
            lines.append(f"### {idx}. {fid}")
            lines.append('')
            lines.append(f"- Score do perfil: {pscore}")
            lines.append(f"- Hints do perfil: {', '.join(safe_dict(fr.get('profile_scores')).get(profile_name, {}).get('matched_hints', []))}")
            lines.append('')
            lines.append('```text')
            lines.append(fr.get('texto_integral', ''))
            lines.append('```')
            lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def build_report(
    confronto_id: str,
    sample_global: List[Dict[str, Any]],
    dossier_queries: Dict[str, Any],
    profile_stats: Dict[str, Dict[str, Any]],
    alignment: Dict[str, Any],
    min_score: float,
    top_n: int,
) -> str:
    hint_counter = Counter()
    term_counter = Counter()
    phrase_counter = Counter()
    profile_counter = Counter()
    for fr in sample_global:
        hint_counter.update(fr.get('matched_hints', []))
        term_counter.update(fr.get('matched_terms', []))
        phrase_counter.update(fr.get('matched_phrases', []))
        if fr.get('best_profile'):
            profile_counter.update([fr.get('best_profile')])

    lines: List[str] = []
    lines.append(f'Relatório v3 — {confronto_id}')
    lines.append(f'Gerado em: {utc_now_iso()}')
    lines.append(f'min_score={min_score} | top_n={top_n} | selecionados_global={len(sample_global)}')
    lines.append('')
    lines.append('Diagnóstico de alinhamento:')
    lines.append(f"  - dominant_profile={alignment.get('dominant_profile')}")
    lines.append(f"  - dossier_declared_profile={alignment.get('dossier_declared_profile')}")
    lines.append(f"  - mismatch_flag={alignment.get('mismatch_flag')}")
    for item in alignment.get('diagnosis_lines', []):
        lines.append(f'  - {item}')
    lines.append('')
    lines.append('Distribuição de melhores perfis no top global:')
    for name, count in profile_counter.most_common():
        lines.append(f'  - {name}: {count}')
    lines.append('')
    lines.append('Perfis por média top10:')
    ranking = sorted(profile_stats.items(), key=lambda kv: (-(kv[1].get('avg_top10_score', 0.0)), kv[0]))
    for name, stats in ranking:
        lines.append(f"  - {name}: avg_top10={stats.get('avg_top10_score', 0.0):.3f} | overlap_global={stats.get('top10_overlap_with_global', 0)} | hints={', '.join(stats.get('top_hints', []))}")
    lines.append('')
    lines.append('Hints globais mais encontrados:')
    for term, count in hint_counter.most_common(15):
        lines.append(f'  - {term}: {count}')
    lines.append('')
    lines.append('Termos do dossier mais encontrados:')
    for term, count in term_counter.most_common(20):
        lines.append(f'  - {term}: {count}')
    lines.append('')
    lines.append('Frases do dossier mais encontradas:')
    for phrase, count in phrase_counter.most_common(10):
        lines.append(f'  - {phrase}: {count}')
    lines.append('')
    lines.append('Top global:')
    for fr in sample_global[:20]:
        fid = fr.get('id') or fr.get('fragmento_id') or 'sem_id'
        lines.append(f"  - {fid} | score={fr.get('score')} | best_profile={fr.get('best_profile')}")
    lines.append('')
    lines.append('Hints usados no score global:')
    lines.append('  - ' + ', '.join(dossier_queries.get('hints', [])))
    return '\n'.join(lines).rstrip() + '\n'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Seleciona fragmentos relevantes para confrontar e reajustar um dossier com perfis separados de relevância.')
    parser.add_argument('--confronto', required=True, help='ID do confronto, ex.: CF08')
    parser.add_argument('--input-json', required=True, type=Path, help='JSON da base fragmentária do confronto')
    parser.add_argument('--project-root', type=Path, default=None, help='Raiz do projeto 16_validacao_integral')
    parser.add_argument('--top-n', type=int, default=20, help='Número máximo de fragmentos a devolver no sample global e por perfil')
    parser.add_argument('--min-score', type=float, default=8.0, help='Score mínimo para inclusão no sample global')
    parser.add_argument('--profile-min-score', type=float, default=4.0, help='Score mínimo para inclusão nos samples de perfil')
    parser.add_argument('--extra-terms', nargs='*', default=[], help='Termos/hints adicionais para relevância global')
    parser.add_argument('--output-prefix', default='v3', help='Sufixo dos ficheiros de output')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    confronto_id = args.confronto.strip()
    payload = read_json(args.input_json.resolve())
    snapshot = extract_snapshot(safe_dict(payload))
    fragments = extract_fragments(safe_dict(payload))
    if not fragments:
        raise SystemExit(f'Nenhum fragmento encontrado em: {args.input_json.resolve()}')

    project_root = args.project_root.resolve() if args.project_root else args.input_json.resolve().parent.parent
    base_validacao_dir = args.input_json.resolve().parent.parent

    merged_hints = DEFAULT_HINTS + list(args.extra_terms)
    dossier_queries = build_dossier_queries(snapshot, merged_hints)
    doc_freq = compute_doc_frequencies([safe_dict(f) for f in fragments])
    total_docs = len(fragments)

    scored: List[Dict[str, Any]] = []
    for raw_fr in fragments:
        fr = score_fragment(safe_dict(raw_fr), dossier_queries, doc_freq, total_docs)
        profile_scores = {
            name: score_profile(fr, name, cfg, doc_freq, total_docs)
            for name, cfg in PROFILE_CONFIGS.items()
        }
        best_profile_name, best_profile_payload = max(
            profile_scores.items(), key=lambda kv: (kv[1].get('score', 0.0), kv[0])
        )
        fr['profile_scores'] = profile_scores
        fr['best_profile'] = best_profile_name
        fr['best_profile_score'] = best_profile_payload.get('score', 0.0)
        scored.append(fr)

    filtered = [row for row in scored if row['score'] >= args.min_score]
    filtered.sort(
        key=lambda x: (
            -x['score'],
            -len(x.get('matched_phrases', [])),
            -len(x.get('matched_hints', [])),
            -len(x.get('matched_terms', [])),
            -x.get('best_profile_score', 0.0),
            str(x.get('id') or x.get('fragmento_id') or '')
        )
    )
    sample_global = filtered[:max(1, args.top_n)]

    global_top10_ids = {
        str(fr.get('id') or fr.get('fragmento_id') or '')
        for fr in sample_global[:10]
    }

    profile_samples: Dict[str, List[Dict[str, Any]]] = {}
    profile_stats: Dict[str, Dict[str, Any]] = {}
    for profile_name, cfg in PROFILE_CONFIGS.items():
        profile_rows = [
            fr for fr in scored if safe_dict(fr.get('profile_scores')).get(profile_name, {}).get('score', 0.0) >= args.profile_min_score
        ]
        profile_rows.sort(
            key=lambda x: (
                -safe_dict(x.get('profile_scores')).get(profile_name, {}).get('score', 0.0),
                -x.get('score', 0.0),
                str(x.get('id') or x.get('fragmento_id') or '')
            )
        )
        top_rows = profile_rows[:max(1, args.top_n)]
        profile_samples[profile_name] = top_rows
        hint_counter = Counter()
        for fr in top_rows:
            hint_counter.update(safe_dict(fr.get('profile_scores')).get(profile_name, {}).get('matched_hints', []))
        overlap = 0
        for fr in top_rows[:10]:
            fid = str(fr.get('id') or fr.get('fragmento_id') or '')
            if fid in global_top10_ids:
                overlap += 1
        top_scores = [safe_dict(fr.get('profile_scores')).get(profile_name, {}).get('score', 0.0) for fr in top_rows[:10]]
        profile_stats[profile_name] = {
            'label': cfg.get('label', profile_name),
            'description': cfg.get('description', ''),
            'n_candidates_above_threshold': len(profile_rows),
            'avg_top10_score': round(sum(top_scores) / len(top_scores), 4) if top_scores else 0.0,
            'max_score': round(max(top_scores), 4) if top_scores else 0.0,
            'top10_overlap_with_global': overlap,
            'top_hints': [term for term, _count in hint_counter.most_common(8)],
        }

    alignment = build_alignment_diagnosis(profile_stats, snapshot)

    stem = f'{confronto_id}_fragmentos_relevantes_dossier_{args.output_prefix}'
    out_dir = args.input_json.resolve().parent / 'samples'
    out_json = out_dir / f'{stem}.json'
    out_md = out_dir / f'{stem}.md'
    out_report = base_validacao_dir / '02_outputs' / f'relatorio_{stem}.txt'

    payload_out = {
        'meta': {
            'script': Path(__file__).name,
            'gerado_em': utc_now_iso(),
            'confronto_id': confronto_id,
            'fonte_base_fragmentaria': str(args.input_json.resolve()),
            'project_root': str(project_root),
            'base_validacao_dir': str(base_validacao_dir),
            'top_n': args.top_n,
            'min_score': args.min_score,
            'profile_min_score': args.profile_min_score,
            'output_prefix': args.output_prefix,
        },
        'snapshot_dossier': snapshot,
        'queries_dossier': dossier_queries,
        'estatisticas': {
            'n_fragmentos_base': len(fragments),
            'n_fragmentos_scored': len(scored),
            'n_fragmentos_filtrados_global': len(filtered),
            'n_fragmentos_sample_global': len(sample_global),
        },
        'alignment_diagnosis': alignment,
        'profile_stats': profile_stats,
        'sample_global': sample_global,
        'samples_por_perfil': profile_samples,
    }

    write_json(out_json, payload_out)
    write_text(out_md, build_markdown(
        confronto_id,
        args.input_json.resolve(),
        project_root,
        snapshot,
        dossier_queries,
        sample_global,
        profile_samples,
        profile_stats,
        alignment,
    ))
    write_text(out_report, build_report(
        confronto_id,
        sample_global,
        dossier_queries,
        profile_stats,
        alignment,
        args.min_score,
        args.top_n,
    ))

    print(out_json)
    print(out_md)
    print(out_report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
