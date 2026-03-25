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
    'onde', 'quando', 'qual', 'quais', 'qualquer', 'mesmo', 'mesma', 'mesmos', 'mesmas',
    'esse', 'essa', 'esses', 'essas', 'este', 'esta', 'estes', 'estas', 'aquele', 'aquela',
    'aqueles', 'aquelas', 'algo', 'algum', 'alguma', 'alguns', 'algumas'
}

GENERIC_LOW_SIGNAL_TERMS = {
    'problema', 'problemas', 'questao', 'questoes', 'sistema', 'sistemas',
    'funcional', 'funcionais', 'processo', 'processos', 'realidade', 'teoria',
    'teorico', 'teorica', 'campo', 'campos', 'relacao', 'relacoes', 'nivel', 'niveis',
    'coisa', 'coisas', 'modo', 'modos', 'forma', 'formas', 'estrutura', 'estruturas',
    'dinamica', 'dinamicas', 'situacao', 'caso', 'casos', 'plano', 'planos', 'efeito',
    'efeitos', 'parte', 'partes', 'contexto', 'contextos', 'projeto', 'material',
    'materiais', 'confronto', 'filosofico', 'filosofica', 'filosoficos', 'filosoficas'
}

DEFAULT_HINTS = [
    'verdade', 'erro', 'criterio', 'critério', 'correcao', 'correção', 'adequação', 'adequacao',
    'objetividade', 'representação', 'representacao', 'apreensão', 'apreensao',
    'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva',
    'localidade', 'local', 'mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica',
    'símbolo', 'simbolo', 'linguagem', 'fechamento', 'fecho sistémico', 'fecho sistemico',
    'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente',
    'substituição do real', 'substituicao do real', 'erro categorial', 'erro de escala',
    'sistema autónomo', 'sistema autonomo', 'coerência interna', 'coerencia interna',
    'critério submetido ao real', 'criterio submetido ao real'
]

PROFILE_CONFIGS: Dict[str, Dict[str, Any]] = {
    'adequacao_criterio_verdade_correcao': {
        'label': 'Adequação, critério, verdade e correção',
        'description': 'Eixo epistemológico explícito: adequação/desadequação ao real, critério, verdade, erro e correção.',
        'hints': [
            'verdade', 'erro', 'critério', 'criterio', 'correção', 'correcao', 'objetividade',
            'adequação', 'adequacao', 'desadequação', 'desadequacao', 'real independente',
            'adequado ao real', 'submetido ao real', 'critério submetido ao real',
            'validade', 'validação', 'validacao', 'falsidade', 'juízo', 'juizo', 'acerto',
            'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente'
        ],
        'boost_terms': ['verdad', 'erro', 'criter', 'correc', 'adequ', 'objetiv', 'valida', 'juiz'],
        'anti_hints': ['consciência reflexiva', 'mediação simbólica']
    },
    'apreensao_representacao_consciencia_localidade': {
        'label': 'Apreensão, representação, consciência e localidade',
        'description': 'Modo humano situado de apreensão do real, consciência reflexiva, representação e localização do ponto de vista.',
        'hints': [
            'apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia',
            'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'humano situado',
            'ponto de vista', 'interioridade', 'memória', 'memoria', 'presença', 'presenca',
            'fixação', 'fixacao', 'fixar', 'apreender', 'representar', 'modo humano', 'situação humana',
            'consciência no real', 'consciencia no real'
        ],
        'boost_terms': ['apree', 'repre', 'consc', 'local', 'inter', 'memor', 'human'],
        'anti_hints': ['coerência interna', 'coerencia interna']
    },
    'mediacao_simbolo_linguagem_fechamento': {
        'label': 'Mediação, símbolo, linguagem e fechamento',
        'description': 'Mediação simbólica, linguagem, forma, sistema e risco de fechamento interno do circuito de validação.',
        'hints': [
            'mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo',
            'linguagem', 'signo', 'forma', 'formalismo', 'simbólico', 'simbolico', 'fechamento',
            'fechamento simbólico', 'fechamento simbolico', 'fechamento sistémico', 'fechamento sistemico',
            'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna',
            'sistema de signos', 'mediações', 'mediacoes', 'representação simbólica', 'discurso formal'
        ],
        'boost_terms': ['media', 'simbo', 'lingu', 'fecha', 'coere', 'forma', 'signo', 'formal'],
        'anti_hints': ['objetividade']
    },
    'substituicao_do_real_erro_categorial_erro_de_escala': {
        'label': 'Substituição do real, erro categorial e erro de escala',
        'description': 'Quando forma, sistema, símbolo ou escala errada passam a funcionar como critério do real.',
        'hints': [
            'substituição do real', 'substituicao do real', 'erro categorial', 'erro de escala',
            'mistura de escalas', 'mistura de regimes', 'troca de critério', 'troca de regime',
            'forma substitui o real', 'sistema substitui o real', 'critério autónomo', 'criterio autonomo',
            'validade interna', 'fecho interno', 'absolutização', 'absolutizacao', 'autonomização',
            'autonomizacao', 'projeção', 'projecao', 'o sistema manda', 'coerência sem real',
            'sistema autónomo', 'sistema autonomo', 'critério sem real', 'formalismo desligado do real'
        ],
        'boost_terms': ['substi', 'catego', 'escala', 'autono', 'projec', 'coere', 'troca', 'absolu'],
        'anti_hints': ['memória', 'memoria']
    },
}

DOSSIER_SECTION_WEIGHTS = {
    'pergunta_central': 1.45,
    'descricao_do_confronto': 1.25,
    'tese_canonica_provisoria': 1.60,
    'articulacao_estrutural': 0.75,
}

PHRASE_MIN_LEN = 12
TERM_MIN_LEN = 4
MIN_STRONG_SAMPLE = 8
MIN_STRONG_GAP = 0.9
MIN_STRONG_DOMINANCE_SHARE = 0.40


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


def unique_preserve(seq: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def get_fragment_text(fragment: Dict[str, Any]) -> str:
    for key in ('texto_integral', 'texto_fragmento', 'texto_curto', 'texto', 'fragmento', 'conteudo', 'text', 'body'):
        val = fragment.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    harvested = []
    for k, v in fragment.items():
        if isinstance(v, str) and v.strip() and k not in {
            'id', 'origem_id', 'ficheiro_origem', 'tipo_unidade', 'funcao_textual_dominante',
            'cadencia', 'estado_validacao', 'estado_excecao'
        }:
            harvested.append(v.strip())
    return '\n'.join(harvested) if harvested else ''


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
    return ranked[:120]


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
        if t in tok_set:
            out.append(term)
            continue
        parts = t.split()
        if len(parts) > 1 and all(any(tok.startswith(p[:5]) or p.startswith(tok[:5]) for tok in tok_set if len(tok) >= 4) for p in parts if len(p) >= 4):
            out.append(term)
            continue
        for tok in tok_set:
            if tok.startswith(t[:5]) or t.startswith(tok[:5]):
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
            if parts and sum(1 for p in parts if p in tok_set or p[:5] in token_stems or p[:6] in token_stems) >= max(1, len(parts) - 1):
                out.append(hint)
                continue
        else:
            if h_norm in tok_set or h_norm in token_stems:
                out.append(hint)
                continue
            h5 = h_norm[:5]
            h6 = h_norm[:6]
            if (h5 and h5 in token_stems) or (h6 and h6 in token_stems):
                out.append(hint)
                continue
            if any(tok.startswith(h5) or h5.startswith(tok[:5]) for tok in tok_set if len(tok) >= 4):
                out.append(hint)
                continue
    return unique_preserve(out)


def idf(term: str, doc_freq: Counter, total_docs: int) -> float:
    df = doc_freq.get(term, 0)
    return math.log((1 + total_docs) / (1 + df)) + 1.0


def estimate_centrality_from_map(fragment: Dict[str, Any]) -> float:
    impact = fragment.get('impacto_mapa_arvore')
    if isinstance(impact, dict):
        numeric_values = [parse_float(v) for v in impact.values() if isinstance(v, (int, float, str))]
        if numeric_values:
            return min(sum(numeric_values), 6.0)
        return min(float(len(impact)), 4.0)
    if isinstance(impact, list):
        return min(float(len(impact)), 4.0)
    return 0.0


def get_structural_score(fragment: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    tratamento = parse_float(fragment.get('tratamento_filosofico') or fragment.get('score_tratamento_filosofico'))
    centralidade = parse_float(fragment.get('centralidade_lexical') or fragment.get('score_centralidade_lexical'))
    cadencia = parse_float(fragment.get('cadencia_nuclear') or fragment.get('score_cadencia_nuclear') or fragment.get('cadencia'))
    impacto_mapa = estimate_centrality_from_map(fragment)

    score = (
        min(tratamento, 5.0) * 0.95 +
        min(centralidade, 5.0) * 0.45 +
        min(cadencia, 5.0) * 0.35 +
        min(impacto_mapa, 6.0) * 0.40
    )

    funcao = normalize(str(fragment.get('funcao_textual') or fragment.get('função_textual') or fragment.get('funcao_textual_dominante') or ''))
    funcao_bonus = 0.0
    if funcao in {'tese', 'nucleo', 'critica', 'definicao', 'argumento', 'objecao', 'objeção'}:
        funcao_bonus = 1.10
    elif funcao in {'descricao', 'distincao', 'distinção'}:
        funcao_bonus = 0.65
    elif funcao:
        funcao_bonus = 0.30
    score += funcao_bonus

    arv = fragment.get('ligacoes_arvore') or fragment.get('ligações_árvore') or fragment.get('ligacoes_na_arvore')
    arv_bonus = min(len(arv), 6) * 0.28 if isinstance(arv, list) else 0.0
    score += arv_bonus

    impacto = fragment.get('impacto_no_mapa_registos') or fragment.get('proposicoes_impactadas')
    impacto_bonus = min(len(impacto), 8) * 0.42 if isinstance(impacto, list) else 0.0
    score += impacto_bonus

    components = {
        'tratamento_filosofico': round(min(tratamento, 5.0) * 0.95, 4),
        'centralidade': round(min(centralidade, 5.0) * 0.45, 4),
        'cadencia': round(min(cadencia, 5.0) * 0.35, 4),
        'impacto_mapa_arvore': round(min(impacto_mapa, 6.0) * 0.40, 4),
        'funcao_textual': round(funcao_bonus, 4),
        'ligacoes_arvore': round(arv_bonus, 4),
        'impacto_no_mapa_registos': round(impacto_bonus, 4),
    }
    return score, components


def collect_reasons(
    fragment: Dict[str, Any],
    matches_phrase: List[str],
    matches_term: List[str],
    matches_hint: List[str],
    best_profile: str,
    structural_components: Dict[str, float],
) -> List[str]:
    reasons: List[str] = []
    if matches_phrase:
        reasons.append(f"frases do dossier: {', '.join(matches_phrase[:4])}")
    if matches_term:
        reasons.append(f"termos do dossier: {', '.join(matches_term[:8])}")
    if matches_hint:
        reasons.append(f"hints gerais: {', '.join(matches_hint[:8])}")
    if best_profile:
        reasons.append(f"perfil dominante no fragmento: {best_profile}")
    for key, value in structural_components.items():
        if value > 0:
            reasons.append(f"{key}={value:g}")
    funcao = fragment.get('funcao_textual') or fragment.get('função_textual') or fragment.get('funcao_textual_dominante')
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
        if any(tok.startswith(b[:5]) or b.startswith(tok[:5]) for tok in tok_set if len(tok) >= 4):
            matches_boost.append(boost)
    matches_boost = unique_preserve(matches_boost)
    anti_matches = hint_matches(text_norm, tokens, profile_cfg.get('anti_hints', []))

    hint_score = len(matches_hint) * 1.7
    boost_score = 0.0
    for item in matches_boost:
        n = normalize(item)
        base = n[:6] if len(n) >= 6 else n
        boost_score += 0.52 * idf(base, doc_freq, total_docs)
    anti_penalty = min(len(anti_matches), 3) * 0.45
    score = hint_score + boost_score + structural_score * 0.24 - anti_penalty
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
        idf_key = tn.split()[0][:6]
        term_score += 0.18 if tn in GENERIC_LOW_SIGNAL_TERMS else 0.62 * idf(idf_key, doc_freq, total_docs)

    phrase_score = min(len(matches_phrase), 6) * 2.0
    hint_score = min(len(matches_hint), 12) * 1.20
    structural_score, structural_components = get_structural_score(fragment)
    score_base = phrase_score + hint_score + term_score + structural_score

    profile_scores: Dict[str, Dict[str, Any]] = {}
    for profile_name, profile_cfg in PROFILE_CONFIGS.items():
        profile_scores[profile_name] = score_profile_from_text(text, profile_name, profile_cfg, doc_freq, total_docs, structural_score)

    best_profile, best_profile_payload = max(
        profile_scores.items(),
        key=lambda kv: (kv[1]['score'], kv[0])
    )
    second_profile, second_profile_payload = sorted(
        profile_scores.items(),
        key=lambda kv: (kv[1]['score'], kv[0]),
        reverse=True,
    )[1]
    score_global = score_base + min(best_profile_payload['score'], 9.5) * 0.18

    out = dict(fragment)
    out['texto_integral'] = text
    out['score_base'] = round(score_base, 4)
    out['score_global'] = round(score_global, 4)
    out['score'] = round(score_global, 4)
    out['matched_phrases'] = matches_phrase
    out['matched_terms'] = matches_term
    out['matched_hints'] = matches_hint
    out['profile_scores'] = {k: v['score'] for k, v in profile_scores.items()}
    out['profile_details'] = profile_scores
    out['best_profile'] = best_profile
    out['best_profile_score'] = best_profile_payload['score']
    out['second_profile'] = second_profile
    out['second_profile_score'] = second_profile_payload['score']
    out['structural_components'] = structural_components
    out['reasons'] = collect_reasons(fragment, matches_phrase, matches_term, matches_hint, best_profile, structural_components)
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


def estimate_dossier_declared_profile(snapshot: Dict[str, Any], forced_profile: str | None = None) -> Dict[str, Any]:
    if forced_profile:
        forced_profile = forced_profile.strip()
        if forced_profile not in PROFILE_CONFIGS:
            valid = ', '.join(PROFILE_CONFIGS.keys())
            raise SystemExit(f'--forced-dossier-profile inválido. Opções: {valid}')
        return {
            'profile': forced_profile,
            'method': 'forced_cli',
            'section_scores': {},
            'raw_profile_scores': {forced_profile: 999.0},
            'confidence': 'forced',
        }

    section_scores: Dict[str, Dict[str, float]] = {}
    raw_scores = {name: 0.0 for name in PROFILE_CONFIGS}

    for section, weight in DOSSIER_SECTION_WEIGHTS.items():
        text = str(snapshot.get(section) or '')
        text_norm = normalize(text)
        tokens = tokenize(text)
        section_scores[section] = {}
        for name, cfg in PROFILE_CONFIGS.items():
            hits = hint_matches(text_norm, tokens, cfg.get('hints', []))
            boosts = hint_matches(text_norm, tokens, cfg.get('boost_terms', []))
            score = (len(hits) * 1.0 + len(boosts) * 0.55) * weight
            section_scores[section][name] = round(score, 4)
            raw_scores[name] += score

    ranked = sorted(raw_scores.items(), key=lambda kv: (-kv[1], kv[0]))
    top_name, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    gap = top_score - second_score
    confidence = 'high' if top_score >= 5.0 and gap >= 1.0 else 'medium' if top_score >= 2.5 else 'low'
    return {
        'profile': top_name,
        'method': 'weighted_snapshot_estimation',
        'section_scores': section_scores,
        'raw_profile_scores': {k: round(v, 4) for k, v in raw_scores.items()},
        'confidence': confidence,
        'gap_to_second': round(gap, 4),
    }


def rank_global_profiles(sample_global: List[Dict[str, Any]]) -> List[Tuple[str, float, int]]:
    profile_data = []
    for name in PROFILE_CONFIGS:
        scores = [float(item.get('profile_details', {}).get(name, {}).get('score', 0.0)) for item in sample_global[:15]]
        best_hits = sum(1 for item in sample_global if item.get('best_profile') == name)
        avg = (sum(scores) / len(scores)) if scores else 0.0
        composite = avg + best_hits * 0.18
        profile_data.append((name, round(composite, 4), best_hits))
    profile_data.sort(key=lambda x: (-x[1], -x[2], x[0]))
    return profile_data


def classify_alignment(
    dominant_profile: str | None,
    second_profile: str | None,
    dossier_declared_profile: str | None,
    global_ranked_profiles: List[Tuple[str, float, int]],
    sample_size: int,
    sample_global: List[Dict[str, Any]],
) -> Tuple[str, bool, List[str]]:
    lines: List[str] = []
    if not dominant_profile or not dossier_declared_profile:
        return 'inconclusive', False, ['Diagnóstico inconclusivo: perfil dominante ou perfil declarado não determinado.']

    if sample_size < MIN_STRONG_SAMPLE:
        lines.append(f'Amostra global útil curta ({sample_size}); o diagnóstico forte fica travado por robustez.')
        if dominant_profile == dossier_declared_profile:
            return 'aligned', False, lines + ['Apesar disso, o perfil dominante coincide com o perfil declarado do dossier.']
        return 'partially_misaligned', True, lines + ['Há diferença entre o perfil dominante e o perfil declarado, mas sem massa suficiente para classificá-la como forte.']

    dominant_score = next((score for name, score, _hits in global_ranked_profiles if name == dominant_profile), 0.0)
    second_score = next((score for name, score, _hits in global_ranked_profiles if name == second_profile), 0.0)
    gap = dominant_score - second_score
    dominance_share = sum(1 for item in sample_global if item.get('best_profile') == dominant_profile) / max(1, sample_size)

    if dominant_profile == dossier_declared_profile:
        lines.append('O perfil dominante dos fragmentos coincide com o perfil declarado do dossier.')
        if gap < 0.45:
            lines.append('Mas a distância para o segundo perfil é curta; convém ler o alinhamento como estável mas não exclusivo.')
        return 'aligned', False, lines

    lines.append(f"O dossier declara sobretudo o eixo '{dossier_declared_profile}', mas o sample global pende para '{dominant_profile}'.")
    if gap >= MIN_STRONG_GAP and dominance_share >= MIN_STRONG_DOMINANCE_SHARE:
        lines.append(f'Gap entre perfis no sample global={gap:.2f}; quota do perfil dominante={dominance_share:.2%}.')
        lines.append('Há indício forte de que o centro real do confronto excede ou desloca a formulação declarada do dossier.')
        return 'strongly_misaligned', True, lines

    lines.append(f'Gap entre perfis no sample global={gap:.2f}; quota do perfil dominante={dominance_share:.2%}.')
    lines.append('Há desalinhamento, mas não suficientemente nítido para o classificar como forte.')
    return 'partially_misaligned', True, lines


def build_alignment_diagnosis(
    profile_stats: Dict[str, Dict[str, Any]],
    snapshot: Dict[str, Any],
    sample_global: List[Dict[str, Any]],
    forced_profile: str | None,
) -> Dict[str, Any]:
    dossier_estimation = estimate_dossier_declared_profile(snapshot, forced_profile)
    dossier_declared_profile = dossier_estimation.get('profile')

    if not sample_global:
        return {
            'dominant_profile': None,
            'second_profile': None,
            'dossier_declared_profile': dossier_declared_profile,
            'dossier_declared_profile_estimation': dossier_estimation,
            'mismatch_flag': None,
            'alignment_classification': 'inconclusive',
            'diagnosis_lines': ['Diagnóstico inconclusivo: não houve fragmentos selecionados no sample global.'],
            'sample_size_used': 0,
            'global_profile_ranking': [],
        }

    global_ranked = rank_global_profiles(sample_global)
    dominant_profile = global_ranked[0][0] if global_ranked else None
    second_profile = global_ranked[1][0] if len(global_ranked) > 1 else None

    alignment_classification, mismatch_flag, lines = classify_alignment(
        dominant_profile=dominant_profile,
        second_profile=second_profile,
        dossier_declared_profile=dossier_declared_profile,
        global_ranked_profiles=global_ranked,
        sample_size=len(sample_global),
        sample_global=sample_global,
    )

    if dominant_profile:
        lines.append(f"Perfil dominante dos fragmentos: {dominant_profile}.")
    if second_profile:
        lines.append(f"Segundo perfil dos fragmentos: {second_profile}.")

    return {
        'dominant_profile': dominant_profile,
        'second_profile': second_profile,
        'dossier_declared_profile': dossier_declared_profile,
        'dossier_declared_profile_estimation': dossier_estimation,
        'mismatch_flag': mismatch_flag,
        'alignment_classification': alignment_classification,
        'diagnosis_lines': lines,
        'sample_size_used': len(sample_global),
        'global_profile_ranking': [
            {'profile': name, 'composite_score': score, 'best_profile_hits': hits}
            for name, score, hits in global_ranked
        ],
        'profile_stats_snapshot': profile_stats,
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
    lines.append(f'# {confronto_id} — fragmentos relevantes para o dossier (CF07 v1)')
    lines.append('')
    lines.append(f'- Gerado em: {utc_now_iso()}')
    lines.append(f'- Fonte base fragmentária: `{source_json}`')
    lines.append(f'- Nº fragmentos no sample global: {len(sample_global)}')
    lines.append('')
    lines.append('## Diagnóstico de alinhamento')
    lines.append('')
    lines.append(f"- dominant_profile: {alignment.get('dominant_profile')}")
    lines.append(f"- second_profile: {alignment.get('second_profile')}")
    lines.append(f"- dossier_declared_profile: {alignment.get('dossier_declared_profile')}")
    lines.append(f"- mismatch_flag: {alignment.get('mismatch_flag')}")
    lines.append(f"- alignment_classification: {alignment.get('alignment_classification')}")
    for item in alignment.get('diagnosis_lines', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append('### Estimativa do perfil declarado do dossier')
    lines.append('')
    lines.append('```json')
    lines.append(json.dumps(alignment.get('dossier_declared_profile_estimation', {}), ensure_ascii=False, indent=2))
    lines.append('```')
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
        lines.append(f"- score global: {item.get('score_global')}")
        lines.append(f"- score base: {item.get('score_base')}")
        lines.append(f"- best profile: {item.get('best_profile')} ({item.get('best_profile_score')})")
        lines.append(f"- second profile: {item.get('second_profile')} ({item.get('second_profile_score')})")
        lines.append(f"- profile scores: {item.get('profile_scores', {})}")
        lines.append(f"- matched phrases: {item.get('matched_phrases', [])}")
        lines.append(f"- matched terms: {item.get('matched_terms', [])}")
        lines.append(f"- matched hints: {item.get('matched_hints', [])}")
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
            lines.append(f"- score global: {item.get('score_global')}")
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
    lines.append(f'RELATÓRIO — {confronto_id} (CF07 v1)')
    lines.append('')
    lines.append(f'min_score_global={min_score}')
    lines.append(f'min_score_perfil={profile_min_score}')
    lines.append(f'selecionados_global={len(sample_global)}')
    lines.append('')
    lines.append('DIAGNÓSTICO')
    lines.append('')
    lines.append(f"dominant_profile={alignment.get('dominant_profile')}")
    lines.append(f"second_profile={alignment.get('second_profile')}")
    lines.append(f"dossier_declared_profile={alignment.get('dossier_declared_profile')}")
    lines.append(f"mismatch_flag={alignment.get('mismatch_flag')}")
    lines.append(f"alignment_classification={alignment.get('alignment_classification')}")
    for item in alignment.get('diagnosis_lines', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append('ESTIMATIVA DO PERFIL DECLARADO')
    lines.append('')
    dossier_est = alignment.get('dossier_declared_profile_estimation', {})
    lines.append(json.dumps(dossier_est, ensure_ascii=False, indent=2))
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
            f"{i:02d}. {frag_id} | score={item.get('score_global')} | base={item.get('score_base')} | best_profile={item.get('best_profile')}:{item.get('best_profile_score')} | second_profile={item.get('second_profile')}:{item.get('second_profile_score')}"
        )
    return '\n'.join(lines)


def build_debug_dump(scored: List[Dict[str, Any]], limit: int, alignment: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append('DEBUG — primeiros fragmentos scoreados')
    lines.append('')
    lines.append('ALIGNMENT SNAPSHOT')
    lines.append(json.dumps(alignment, ensure_ascii=False, indent=2))
    lines.append('')
    for i, item in enumerate(scored[:limit], 1):
        frag_id = item.get('id') or item.get('fragment_id') or f'frag_{i}'
        lines.append(f'## {i}. {frag_id}')
        lines.append(
            f"score={item.get('score_global')} score_base={item.get('score_base')} best_profile={item.get('best_profile')} best_profile_score={item.get('best_profile_score')} second_profile={item.get('second_profile')} second_profile_score={item.get('second_profile_score')}"
        )
        lines.append(f"matched_phrases={item.get('matched_phrases', [])}")
        lines.append(f"matched_terms={item.get('matched_terms', [])}")
        lines.append(f"matched_hints={item.get('matched_hints', [])}")
        lines.append(f"profile_scores={item.get('profile_scores', {})}")
        lines.append(f"structural_components={item.get('structural_components', {})}")
        lines.append('')
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Seleciona fragmentos relevantes para o dossier CF07, com score global robusto, perfis paralelos e diagnóstico de alinhamento/desalinhamento.'
    )
    parser.add_argument('--confronto', required=True)
    parser.add_argument('--input-json', required=True, type=Path)
    parser.add_argument('--project-root', type=Path)
    parser.add_argument('--top-n', type=int, default=24)
    parser.add_argument('--min-score', type=float, default=8.0)
    parser.add_argument('--profile-min-score', type=float, default=4.0)
    parser.add_argument('--extra-terms', nargs='*', default=[])
    parser.add_argument('--output-prefix', default='v1')
    parser.add_argument('--debug-limit', type=int, default=35)
    parser.add_argument('--forced-dossier-profile', default=None)
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
    scored.sort(key=lambda x: (-float(x.get('score_global', 0.0)), -float(x.get('score_base', 0.0)), str(x.get('id') or x.get('fragment_id') or '')))

    filtered_global = [row for row in scored if float(row.get('score_global', 0.0)) >= args.min_score]
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
    alignment = build_alignment_diagnosis(profile_stats, snapshot, sample_global, args.forced_dossier_profile)

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
            'forced_dossier_profile': args.forced_dossier_profile,
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
    write_text(out_debug, build_debug_dump(scored, args.debug_limit, alignment))

    print(out_json)
    print(out_md)
    print(out_report)
    print(out_debug)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
