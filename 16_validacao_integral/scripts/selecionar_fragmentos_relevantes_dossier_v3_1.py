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
from typing import Any, Dict, Iterable, List, Tuple

STOPWORDS = {
    'a', 'o', 'e', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'nos', 'nas',
    'por', 'para', 'com', 'sem', 'um', 'uma', 'uns', 'umas', 'que', 'se', 'ao',
    'aos', 'à', 'às', 'como', 'mais', 'menos', 'ja', 'já', 'ou', 'ser', 'é', 'foi',
    'sao', 'são', 'era', 'nao', 'não', 'sim', 'lhe', 'lhes', 'seu', 'sua', 'seus', 'suas', 'eu',
    'tu', 'ele', 'ela', 'eles', 'elas', 'isto', 'isso', 'aquilo', 'num', 'numa',
    'entre', 'sobre', 'tambem', 'também', 'muito', 'muita', 'muitos', 'muitas', 'todo',
    'toda', 'todos', 'todas', 'cada', 'ha', 'há', 'nosso', 'nossa', 'nossos', 'nossas',
    'teu', 'tua', 'teus', 'tuas', 'meu', 'minha', 'meus', 'minhas', 'porque', 'pois',
    'onde', 'quando', 'qual', 'quais', 'qualquer', 'mesmo', 'mesma', 'mesmos', 'mesmas'
}

GENERIC_LOW_SIGNAL_TERMS = {
    'problema', 'problemas', 'questao', 'questoes', 'sistema', 'sistemas',
    'funcional', 'funcionais', 'processo', 'processos', 'realidade', 'teoria',
    'teorico', 'teorica', 'campo', 'campos', 'relacao', 'relacoes', 'nivel', 'niveis',
    'coisa', 'coisas', 'modo', 'modos', 'forma', 'formas', 'estrutura', 'estruturas',
    'dinamica', 'dinamicas', 'situacao', 'caso', 'casos', 'plano', 'planos', 'efeito',
    'efeitos', 'parte', 'partes', 'contexto', 'contextos'
}

DEFAULT_HINTS = [
    'consci', 'consciência', 'consciência reflexiva', 'media', 'mediação',
    'representa', 'representação', 'simbol', 'símbolo', 'linguagem', 'reflex',
    'ponto de vista', 'erro', 'erro categorial', 'erro de escala', 'dualismo',
    'panpsiquismo', 'continuidade', 'continuidade ontológica', 'localidade',
    'local', 'real', 'interioridade', 'apreensão', 'apreensao', 'mediação simbólica'
]

PROFILE_CONFIGS: Dict[str, Dict[str, Any]] = {
    'nucleo_consciencia_no_real': {
        'label': 'Núcleo: consciência no real',
        'description': 'Consciência como modo, processo ou relação no real, sem exterioridade ontológica.',
        'hints': [
            'consciência', 'consci', 'consciência reflexiva', 'interioridade', 'eu',
            'localidade', 'local', 'apreensão', 'apreensao', 'ponto de vista',
            'no real', 'relação no real', 'relacao no real', 'continuidade ontológica',
            'nao esta fora do real', 'não está fora do real'
        ],
        'boost_terms': ['consci', 'real', 'local', 'interioridade', 'apreensao', 'ponto', 'vista'],
        'anti_hints': ['novidade qualitativa', 'unidade funcional'],
    },
    'mediacao_representacao_simbolo': {
        'label': 'Núcleo: mediação, representação e símbolo',
        'description': 'Mediação, representação, símbolo, linguagem e enquadramento operativo do real.',
        'hints': [
            'mediação', 'media', 'representação', 'representa', 'símbolo', 'simbol',
            'linguagem', 'linguistico', 'linguístico', 'signo', 'significação',
            'significacao', 'enquadramento', 'fixação', 'fixacao', 'mediação simbólica',
            'comum entre diferenças', 'comum entre diferencas'
        ],
        'boost_terms': ['medi', 'representa', 'simbol', 'linguag', 'sign'],
        'anti_hints': ['novidade qualitativa'],
    },
    'erro_categorial_dualismo_panpsiquismo': {
        'label': 'Núcleo: erro categorial, dualismo e panpsiquismo',
        'description': 'Críticas a separações ontológicas, erros de escala, dualismos e pseudoproblemas.',
        'hints': [
            'erro categorial', 'erro', 'erro de escala', 'dualismo', 'panpsiquismo',
            'absolutização', 'absolutizacao', 'absolutiza', 'separação', 'separacao',
            'ponte', 'pseudo-problema', 'pseudoproblema', 'categoria', 'nagel',
            'wittgenstein', 'kant', 'interioridade fantasmagórica', 'interioridade fantasmagorica'
        ],
        'boost_terms': ['erro', 'dual', 'panpsiqu', 'separa', 'ponte', 'categoria'],
        'anti_hints': ['unidade funcional'],
    },
    'emergencia_passagem_niveis': {
        'label': 'Núcleo: emergência e passagem de níveis',
        'description': 'Surgimento, novidade qualitativa, reorganização e passagem entre níveis.',
        'hints': [
            'emergência', 'emergencia', 'emerge', 'surgimento', 'novidade qualitativa',
            'passagem', 'salto', 'níveis', 'niveis', 'reorganização', 'reorganizacao',
            'reorganizações', 'reorganizacoes', 'unidade funcional', 'qualitativamente novo',
            'aparecimento'
        ],
        'boost_terms': ['emerg', 'novidade', 'passag', 'salto', 'reorganiz', 'nivel'],
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


def normalize(text: str) -> str:
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace('—', ' ').replace('–', ' ').replace('-', ' ')
    text = re.sub(r'[^a-z0-9\s_]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    toks = re.findall(r'[a-z0-9_]+', normalize(text))
    out: List[str] = []
    for t in toks:
        if len(t) < TERM_MIN_LEN:
            continue
        if t in STOPWORDS:
            continue
        out.append(t)
    return out


def stems_from_text(text: str) -> List[str]:
    stems: List[str] = []
    for tok in tokenize(text):
        stems.append(tok)
        if len(tok) >= 5:
            stems.append(tok[:5])
        if len(tok) >= 6:
            stems.append(tok[:6])
    return stems


def unique_preserve(seq: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def get_fragment_text(fragment: Dict[str, Any]) -> str:
    for key in ('texto_integral', 'texto', 'fragmento', 'conteudo', 'text', 'body'):
        val = fragment.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ''


def extract_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    confronto = safe_dict(payload.get('confronto'))
    snapshot = safe_dict(confronto.get('dossier_snapshot'))
    if snapshot:
        return snapshot
    return safe_dict(payload.get('snapshot_dossier'))


def extract_fragments(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ('fragmentos', 'base_fragmentaria', 'itens', 'items', 'sample'):
        val = payload.get(key)
        if isinstance(val, list):
            return [safe_dict(v) for v in val]
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
        n = normalize(s)
        if len(n) >= PHRASE_MIN_LEN and ' ' in n:
            phrases.append(s.strip())
    result = []
    seen = set()
    for p in phrases:
        n = normalize(p)
        if n and n not in seen:
            seen.add(n)
            result.append(p)
    return result[:80]


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
    return ranked[:100]


def build_dossier_queries(snapshot: Dict[str, Any], extra_terms: List[str]) -> Dict[str, Any]:
    phrases = select_candidate_phrases(snapshot)
    terms = select_candidate_terms(snapshot, extra_terms)
    hints = unique_preserve([item for item in extra_terms if normalize(item)])
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
    out = []
    for phrase in phrases:
        p = normalize(phrase)
        if p and p in text_norm:
            out.append(phrase)
    return out


def term_matches(tokens: List[str], terms: Iterable[str]) -> List[str]:
    tok_set = set(tokens)
    out = []
    for term in terms:
        t = normalize(term)
        if not t:
            continue
        t_compact = t.replace(' ', '')
        if t in tok_set or t_compact in tok_set:
            out.append(term)
            continue
        for tok in tok_set:
            if tok.startswith(t) or t.startswith(tok):
                out.append(term)
                break
    return unique_preserve(out)


def hint_matches(text_norm: str, tokens: List[str], hints: Iterable[str]) -> List[str]:
    tok_set = set(tokens)
    token_stems = set()
    for tok in tok_set:
        token_stems.add(tok)
        if len(tok) >= 5:
            token_stems.add(tok[:5])
        if len(tok) >= 6:
            token_stems.add(tok[:6])
    out = []
    for hint in hints:
        h_norm = normalize(hint)
        if not h_norm:
            continue
        if ' ' in h_norm:
            if h_norm in text_norm:
                out.append(hint)
                continue
            parts = [p for p in tokenize(h_norm) if len(p) >= 4]
            if parts and sum(1 for p in parts if p in tok_set or p[:5] in token_stems) >= max(1, len(parts) - 1):
                out.append(hint)
                continue
        else:
            if h_norm in tok_set or h_norm in token_stems:
                out.append(hint)
                continue
            if any(tok.startswith(h_norm) or h_norm.startswith(tok) for tok in tok_set if len(tok) >= 4):
                out.append(hint)
                continue
            h5 = h_norm[:5]
            if h5 and h5 in token_stems:
                out.append(hint)
                continue
    return unique_preserve(out)


def idf(term: str, doc_freq: Counter, total_docs: int) -> float:
    df = doc_freq.get(term, 0)
    return math.log((1 + total_docs) / (1 + df)) + 1.0


def get_structural_score(fragment: Dict[str, Any]) -> float:
    tratamento = parse_float(fragment.get('tratamento_filosofico') or fragment.get('score_tratamento_filosofico'))
    centralidade = parse_float(fragment.get('centralidade_lexical') or fragment.get('score_centralidade_lexical'))
    cadencia = parse_float(fragment.get('cadencia_nuclear') or fragment.get('score_cadencia_nuclear'))
    score = (
        min(tratamento, 5.0) * 0.9 +
        min(centralidade, 5.0) * 0.45 +
        min(cadencia, 5.0) * 0.35
    )
    funcao = normalize(str(fragment.get('funcao_textual') or fragment.get('função_textual') or ''))
    if funcao in {'tese', 'nucleo', 'critica', 'definicao'}:
        score += 1.1
    elif funcao:
        score += 0.35
    arv = fragment.get('ligacoes_arvore') or fragment.get('ligações_árvore') or fragment.get('ligacoes_na_arvore')
    if isinstance(arv, list):
        score += min(len(arv), 6) * 0.3
    impacto = fragment.get('impacto_no_mapa_registos') or fragment.get('proposicoes_impactadas')
    if isinstance(impacto, list):
        score += min(len(impacto), 8) * 0.45
    return score


def collect_reasons(fragment: Dict[str, Any], matches_phrase: List[str], matches_term: List[str], matches_hint: List[str]) -> List[str]:
    reasons: List[str] = []
    if matches_phrase:
        reasons.append(f"frases do dossier: {', '.join(matches_phrase[:4])}")
    if matches_term:
        reasons.append(f"termos do dossier: {', '.join(matches_term[:8])}")
    if matches_hint:
        reasons.append(f"hints semânticos: {', '.join(matches_hint[:8])}")
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
    return reasons


def score_profile_from_text(
    text: str,
    profile_name: str,
    profile_cfg: Dict[str, Any],
    doc_freq: Counter,
    total_docs: int,
    structural_score: float,
) -> Dict[str, Any]:
    text_norm = normalize(text)
    tokens = tokenize(text)
    matches_hint = hint_matches(text_norm, tokens, profile_cfg.get('hints', []))
    matches_boost = []
    tok_set = set(tokens)
    for boost in profile_cfg.get('boost_terms', []):
        b = normalize(boost)
        if not b:
            continue
        if any(tok.startswith(b) or b.startswith(tok) for tok in tok_set if len(tok) >= 4):
            matches_boost.append(boost)
    matches_boost = unique_preserve(matches_boost)
    anti_matches = hint_matches(text_norm, tokens, profile_cfg.get('anti_hints', []))

    hint_score = len(matches_hint) * 1.75
    boost_score = 0.0
    for item in matches_boost:
        n = normalize(item)
        base = n[:6] if len(n) >= 6 else n
        boost_score += 0.55 * idf(base, doc_freq, total_docs)
    anti_penalty = min(len(anti_matches), 3) * 0.5
    score = hint_score + boost_score + structural_score * 0.25 - anti_penalty
    return {
        'profile_name': profile_name,
        'profile_label': profile_cfg.get('label', profile_name),
        'score': round(score, 4),
        'matched_hints': matches_hint,
        'matched_boost_terms': matches_boost,
        'matched_anti_hints': anti_matches,
    }


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
        idf_key = tn.split()[0]
        term_score += 0.15 if tn in GENERIC_LOW_SIGNAL_TERMS else 0.60 * idf(idf_key, doc_freq, total_docs)

    phrase_score = min(len(matches_phrase), 6) * 2.0
    hint_score = min(len(matches_hint), 10) * 1.25
    structural_score = get_structural_score(fragment)
    score_base = phrase_score + hint_score + term_score + structural_score

    profile_scores: Dict[str, Dict[str, Any]] = {}
    for profile_name, profile_cfg in PROFILE_CONFIGS.items():
        profile_scores[profile_name] = score_profile_from_text(text, profile_name, profile_cfg, doc_freq, total_docs, structural_score)

    best_profile, best_profile_payload = max(
        profile_scores.items(),
        key=lambda kv: (kv[1]['score'], kv[0])
    )
    score_global = score_base + min(best_profile_payload['score'], 8.0) * 0.18

    out = dict(fragment)
    out['texto_integral'] = text
    out['score_base'] = round(score_base, 4)
    out['score'] = round(score_global, 4)
    out['matched_phrases'] = matches_phrase
    out['matched_terms'] = matches_term
    out['matched_hints'] = matches_hint
    out['reasons'] = collect_reasons(fragment, matches_phrase, matches_term, matches_hint)
    out['profile_scores'] = {k: v['score'] for k, v in profile_scores.items()}
    out['profile_details'] = profile_scores
    out['best_profile'] = best_profile
    out['best_profile_score'] = best_profile_payload['score']
    return out


def summarize_profile_stats(profile_samples: Dict[str, List[Dict[str, Any]]], global_sample: List[Dict[str, Any]], threshold: float) -> Dict[str, Dict[str, Any]]:
    global_ids = {str(item.get('id') or item.get('fragment_id') or '') for item in global_sample}
    stats: Dict[str, Dict[str, Any]] = {}
    for name, items in profile_samples.items():
        top10 = items[:10]
        top10_scores = [float(item.get('profile_details', {}).get(name, {}).get('score', 0.0)) for item in top10]
        stats[name] = {
            'label': PROFILE_CONFIGS[name]['label'],
            'description': PROFILE_CONFIGS[name]['description'],
            'n_candidates_above_threshold': len(items),
            'avg_top10_score': round(sum(top10_scores) / len(top10_scores), 4) if top10_scores else 0.0,
            'max_score': round(max(top10_scores), 4) if top10_scores else 0.0,
            'top10_overlap_with_global': sum(1 for item in top10 if str(item.get('id') or item.get('fragment_id') or '') in global_ids),
            'threshold': threshold,
        }
    return stats


def count_snapshot_profile_mentions(snapshot: Dict[str, Any]) -> Dict[str, int]:
    snapshot_text = ' '.join(harvest_strings(snapshot))
    text_norm = normalize(snapshot_text)
    tokens = tokenize(snapshot_text)
    mentions: Dict[str, int] = {}
    for name, cfg in PROFILE_CONFIGS.items():
        mentions[name] = len(hint_matches(text_norm, tokens, cfg.get('hints', [])))
    return mentions


def build_alignment_diagnosis(profile_stats: Dict[str, Dict[str, Any]], snapshot: Dict[str, Any], sample_global: List[Dict[str, Any]]) -> Dict[str, Any]:
    dossier_profile_mentions = count_snapshot_profile_mentions(snapshot)
    if not sample_global:
        return {
            'dossier_profile_mentions': dossier_profile_mentions,
            'dominant_profile': None,
            'dossier_declared_profile': max(dossier_profile_mentions.items(), key=lambda kv: kv[1])[0] if dossier_profile_mentions else None,
            'mismatch_flag': None,
            'diagnosis_lines': ['Diagnóstico inconclusivo: não houve fragmentos selecionados no sample global.'],
        }

    ranked = sorted(
        profile_stats.items(),
        key=lambda kv: (-(kv[1].get('avg_top10_score', 0.0)), -(kv[1].get('top10_overlap_with_global', 0)), kv[0])
    )
    dominant_profile = ranked[0][0] if ranked else None
    dossier_declared_profile = max(dossier_profile_mentions.items(), key=lambda kv: kv[1])[0] if dossier_profile_mentions else None
    mismatch = False
    diagnosis_lines: List[str] = []

    if dominant_profile and dossier_declared_profile and dominant_profile != dossier_declared_profile:
        mismatch = True
        diagnosis_lines.append(
            f"O dossier parece formular-se mais no eixo '{dossier_declared_profile}', mas os fragmentos mais fortes caem sobretudo em '{dominant_profile}'."
        )
    elif dominant_profile:
        diagnosis_lines.append(
            f"O eixo dominante dos fragmentos é '{PROFILE_CONFIGS[dominant_profile]['label']}'."
        )

    emerg = profile_stats.get('emergencia_passagem_niveis', {}).get('avg_top10_score', 0.0)
    strongest_other = max(
        profile_stats.get('nucleo_consciencia_no_real', {}).get('avg_top10_score', 0.0),
        profile_stats.get('mediacao_representacao_simbolo', {}).get('avg_top10_score', 0.0),
        profile_stats.get('erro_categorial_dualismo_panpsiquismo', {}).get('avg_top10_score', 0.0),
    )
    if strongest_other > emerg + 0.75:
        mismatch = True
        diagnosis_lines.append('Há indício de que o dossier esteja a forçar uma moldura de emergência sobre material cujo centro efetivo é consciência/mediação/erro categorial.')
    elif emerg >= strongest_other and dominant_profile == 'emergencia_passagem_niveis':
        diagnosis_lines.append('O eixo de emergência/passagem de níveis aparece efetivamente forte nos fragmentos selecionados.')

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
    snapshot: Dict[str, Any],
    dossier_queries: Dict[str, Any],
    sample_global: List[Dict[str, Any]],
    profile_samples: Dict[str, List[Dict[str, Any]]],
    profile_stats: Dict[str, Dict[str, Any]],
    alignment: Dict[str, Any],
) -> str:
    lines: List[str] = []
    lines.append(f'# {confronto_id} — fragmentos relevantes para o dossier (v3.1)')
    lines.append('')
    lines.append(f'- Gerado em: {utc_now_iso()}')
    lines.append(f'- Fonte base fragmentária: `{source_json}`')
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
    lines.append('')
    for p in dossier_queries.get('phrases', []):
        lines.append(f'- {p}')
    lines.append('')
    lines.append('### Termos')
    lines.append('')
    lines.append(', '.join(dossier_queries.get('terms', [])))
    lines.append('')
    lines.append('### Hints')
    lines.append('')
    lines.append(', '.join(dossier_queries.get('hints', [])))
    lines.append('')
    lines.append('## Estatísticas por perfil')
    lines.append('')
    for name, stats in profile_stats.items():
        lines.append(f"### {PROFILE_CONFIGS[name]['label']}")
        lines.append('')
        lines.append(f"- Candidatos acima do limiar: {stats.get('n_candidates_above_threshold')}")
        lines.append(f"- Média top10: {stats.get('avg_top10_score')}")
        lines.append(f"- Máximo top10: {stats.get('max_score')}")
        lines.append(f"- Sobreposição top10 com global: {stats.get('top10_overlap_with_global')}")
        lines.append('')
    lines.append('## Sample global')
    lines.append('')
    if not sample_global:
        lines.append('_Sem fragmentos selecionados._')
    for i, item in enumerate(sample_global, 1):
        frag_id = item.get('id') or item.get('fragment_id') or f'frag_{i}'
        lines.append(f'### {i}. {frag_id}')
        lines.append('')
        lines.append(f"- score global: {item.get('score')}")
        lines.append(f"- score base: {item.get('score_base')}")
        lines.append(f"- melhor perfil: {item.get('best_profile')} ({item.get('best_profile_score')})")
        lines.append(f"- matched_phrases: {item.get('matched_phrases', [])}")
        lines.append(f"- matched_terms: {item.get('matched_terms', [])}")
        lines.append(f"- matched_hints: {item.get('matched_hints', [])}")
        lines.append(f"- reasons: {item.get('reasons', [])}")
        lines.append('')
        lines.append(item.get('texto_integral', ''))
        lines.append('')
    for profile_name, items in profile_samples.items():
        lines.append(f"## Sample por perfil — {PROFILE_CONFIGS[profile_name]['label']}")
        lines.append('')
        if not items:
            lines.append('_Sem fragmentos selecionados neste perfil._')
            lines.append('')
            continue
        for i, item in enumerate(items, 1):
            frag_id = item.get('id') or item.get('fragment_id') or f'frag_{i}'
            p = item.get('profile_details', {}).get(profile_name, {})
            lines.append(f'### {i}. {frag_id}')
            lines.append('')
            lines.append(f"- score do perfil: {p.get('score')}")
            lines.append(f"- hints do perfil: {p.get('matched_hints', [])}")
            lines.append(f"- boost_terms do perfil: {p.get('matched_boost_terms', [])}")
            lines.append(f"- anti_hints do perfil: {p.get('matched_anti_hints', [])}")
            lines.append('')
            lines.append(item.get('texto_integral', ''))
            lines.append('')
    return '\n'.join(lines)


def build_report(
    confronto_id: str,
    sample_global: List[Dict[str, Any]],
    profile_samples: Dict[str, List[Dict[str, Any]]],
    profile_stats: Dict[str, Dict[str, Any]],
    alignment: Dict[str, Any],
    min_score: float,
    profile_min_score: float,
) -> str:
    lines: List[str] = []
    lines.append(f'RELATÓRIO — {confronto_id} (v3.1)')
    lines.append('')
    lines.append(f'min_score_global={min_score}')
    lines.append(f'min_score_perfil={profile_min_score}')
    lines.append(f'selecionados_global={len(sample_global)}')
    lines.append('')
    lines.append('DIAGNÓSTICO')
    lines.append('')
    lines.append(f"dominant_profile={alignment.get('dominant_profile')}")
    lines.append(f"dossier_declared_profile={alignment.get('dossier_declared_profile')}")
    lines.append(f"mismatch_flag={alignment.get('mismatch_flag')}")
    for item in alignment.get('diagnosis_lines', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append('PERFIS')
    lines.append('')
    for name, stats in profile_stats.items():
        lines.append(
            f"- {name}: candidatos={stats.get('n_candidates_above_threshold')} avg_top10_score={stats.get('avg_top10_score')} max_score={stats.get('max_score')} overlap_global={stats.get('top10_overlap_with_global')}"
        )
    lines.append('')
    lines.append('TOP GLOBAL')
    lines.append('')
    if not sample_global:
        lines.append('- sem fragmentos')
    for i, item in enumerate(sample_global[:15], 1):
        frag_id = item.get('id') or item.get('fragment_id') or f'frag_{i}'
        lines.append(
            f"{i:02d}. {frag_id} | score={item.get('score')} | base={item.get('score_base')} | best_profile={item.get('best_profile')}:{item.get('best_profile_score')}"
        )
    return '\n'.join(lines)


def build_debug_dump(scored: List[Dict[str, Any]], limit: int) -> str:
    lines: List[str] = []
    lines.append('DEBUG — primeiros fragmentos scoreados')
    lines.append('')
    for i, item in enumerate(scored[:limit], 1):
        frag_id = item.get('id') or item.get('fragment_id') or f'frag_{i}'
        lines.append(f'## {i}. {frag_id}')
        lines.append(f"score={item.get('score')} score_base={item.get('score_base')} best_profile={item.get('best_profile')} best_profile_score={item.get('best_profile_score')}")
        lines.append(f"matched_phrases={item.get('matched_phrases', [])}")
        lines.append(f"matched_terms={item.get('matched_terms', [])}")
        lines.append(f"matched_hints={item.get('matched_hints', [])}")
        lines.append(f"profile_scores={item.get('profile_scores', {})}")
        lines.append('')
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='Seleciona fragmentos relevantes para um dossier, com score global robusto e perfis paralelos de relevância.')
    parser.add_argument('--confronto', required=True)
    parser.add_argument('--input-json', required=True, type=Path)
    parser.add_argument('--project-root', type=Path)
    parser.add_argument('--top-n', type=int, default=20)
    parser.add_argument('--min-score', type=float, default=8.0)
    parser.add_argument('--profile-min-score', type=float, default=4.0)
    parser.add_argument('--extra-terms', nargs='*', default=[])
    parser.add_argument('--output-prefix', default='v3_1')
    parser.add_argument('--debug-limit', type=int, default=30)
    args = parser.parse_args()

    confronto_id = args.confronto.strip()
    payload = read_json(args.input_json.resolve())
    snapshot = extract_snapshot(payload)
    fragments = extract_fragments(payload)
    if not fragments:
        raise SystemExit('Sem fragmentos no input JSON.')

    merged_hints = DEFAULT_HINTS + list(args.extra_terms)
    dossier_queries = build_dossier_queries(snapshot, merged_hints)
    doc_freq = compute_doc_frequencies(fragments)
    total_docs = len(fragments)

    scored = [score_fragment(safe_dict(f), dossier_queries, doc_freq, total_docs) for f in fragments]
    scored.sort(key=lambda x: (-float(x.get('score', 0.0)), -float(x.get('score_base', 0.0)), str(x.get('id') or x.get('fragment_id') or '')))

    filtered_global = [row for row in scored if float(row.get('score', 0.0)) >= args.min_score]
    sample_global = filtered_global[:max(1, args.top_n)]

    profile_samples: Dict[str, List[Dict[str, Any]]] = {}
    for profile_name in PROFILE_CONFIGS:
        ranked = [
            row for row in scored
            if float(row.get('profile_details', {}).get(profile_name, {}).get('score', 0.0)) >= args.profile_min_score
        ]
        ranked.sort(
            key=lambda x: (
                -float(x.get('profile_details', {}).get(profile_name, {}).get('score', 0.0)),
                -float(x.get('score_base', 0.0)),
                str(x.get('id') or x.get('fragment_id') or '')
            )
        )
        profile_samples[profile_name] = ranked[:max(1, args.top_n)]

    profile_stats = summarize_profile_stats(profile_samples, sample_global, args.profile_min_score)
    alignment = build_alignment_diagnosis(profile_stats, snapshot, sample_global)

    stem = f'{confronto_id}_fragmentos_relevantes_dossier_{args.output_prefix}'
    out_dir = args.input_json.resolve().parent / 'samples'
    out_json = out_dir / f'{stem}.json'
    out_md = out_dir / f'{stem}.md'
    out_debug = out_dir / f'{stem}__debug.txt'

    if args.project_root:
        base_validacao_dir = args.project_root.resolve()
    else:
        base_validacao_dir = args.input_json.resolve().parent.parent
    out_report = base_validacao_dir / '02_outputs' / f'relatorio_{stem}.txt'

    payload_out = {
        'meta': {
            'script': Path(__file__).name,
            'gerado_em': utc_now_iso(),
            'confronto_id': confronto_id,
            'fonte_base_fragmentaria': str(args.input_json.resolve()),
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
            'n_fragmentos_filtrados_global': len(filtered_global),
            'n_fragmentos_sample_global': len(sample_global),
        },
        'sample_global': sample_global,
        'samples_por_perfil': profile_samples,
        'profile_stats': profile_stats,
        'alignment_diagnosis': alignment,
    }

    write_json(out_json, payload_out)
    write_text(out_md, build_markdown(confronto_id, args.input_json.resolve(), snapshot, dossier_queries, sample_global, profile_samples, profile_stats, alignment))
    write_text(out_report, build_report(confronto_id, sample_global, profile_samples, profile_stats, alignment, args.min_score, args.profile_min_score))
    write_text(out_debug, build_debug_dump(scored, args.debug_limit))

    print(out_json)
    print(out_md)
    print(out_report)
    print(out_debug)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
