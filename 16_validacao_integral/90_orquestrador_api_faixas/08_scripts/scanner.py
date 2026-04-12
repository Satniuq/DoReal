from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import list_md_files, natural_sort_key, read_text, slugify


FAIXA_RE = re.compile(r'^(?P<num>\d{2})_faixa_(?P<slug>.+)$', re.I)
TRANS_RE = re.compile(r'^(?P<from>\d{2})_para_(?P<to>\d{2})_DECISAO_.*\.md$', re.I)
FAIXA_SEGMENT_RE = re.compile(r'^(?P<num>\d{2})_faixa_(?P<slug>.+)$', re.I)

DERIVATIVE_MARKERS = {
    'inicio', 'desenvolvimento', 'pos', 'post', 'bloqueio', 'continuidade',
    'seguimento', 'sequencia', 'reabertura', 'reaberto', 'retoma', 'continuacao'
}


@dataclass
class FaixaInfo:
    number: int
    name: str
    path: Path
    abertura_dir: Path
    ensaios_dir: Path
    decisoes_dir: Path
    consolidado_dir: Path
    abertura_files: list[Path]
    ensaio_files: list[Path]
    decisao_files: list[Path]
    consolidado_files: list[Path]
    active_file: Path | None
    status: str


CONDITIONAL_OPENING_MARKERS = [
    'a mera existência desta decisão não abre',
    'a mera existencia desta decisao nao abre',
    'só a criar por decisão futura legítima',
    'so a criar por decisao futura legitima',
    'próxima ação (condicionada)',
    'proxima acao (condicionada)',
    'se for deliberado avançar',
    'se for deliberado avancar',
    'apenas fixa o lugar e o ficheiro',
    'apenas fixa o lugar e o ficheiro para uma eventual deliberação ulterior',
    'apenas fixa o lugar e o ficheiro para uma eventual deliberacao ulterior',
]


POSITIVE_OPENING_MARKERS = [
    'próxima ação:',
    'proxima acao:',
    'criar `abertura_faixa_expositiva_controlada_',
    'criar abertura_faixa_expositiva_controlada_',
    'o próximo passo legítimo é a abertura',
    'o proximo passo legitimo e a abertura',
]


LABEL_NEXT_FILENAME = [
    'nome do próximo ficheiro de abertura',
    'nome do proximo ficheiro de abertura',
    'nome exato do ficheiro seguinte',
    'nome exato do ficheiro de abertura',
    'nome do ficheiro de abertura',
]

LABEL_NEXT_FOLDER = [
    'pasta canónica de destino',
    'pasta canonica de destino',
    'pasta de destino prevista',
    'pasta de destino',
    'diretoria de destino',
    'directoria de destino',
]


def _stage_dir(item: Path, stage: str, default_name: str) -> Path:
    exact = item / default_name
    if exact.exists() and exact.is_dir():
        return exact

    candidates: list[tuple[int, str, Path]] = []
    for child in item.iterdir():
        if not child.is_dir():
            continue
        name = child.name.lower()
        score = -1
        if stage == 'abertura':
            if 'abertura' in name:
                score = 100
        elif stage == 'ensaios':
            if 'ensaio' in name:
                score = 100
            elif 'historico' in name or 'teste' in name:
                score = 70
        elif stage == 'decisoes':
            if 'decis' in name or 'limite' in name:
                score = 100
        elif stage == 'consolidado':
            if 'consolid' in name:
                score = 100
        if score >= 0:
            candidates.append((score, child.name.lower(), child))

    if candidates:
        candidates.sort(key=lambda t: (-t[0], natural_sort_key(t[1])))
        return candidates[0][2]
    return exact


def scan_faixas(descida_root: Path) -> list[FaixaInfo]:
    faixas: list[FaixaInfo] = []
    for item in sorted(descida_root.iterdir(), key=lambda p: natural_sort_key(p.name)):
        if not item.is_dir():
            continue
        m = FAIXA_RE.match(item.name)
        if not m:
            continue
        num = int(m.group('num'))
        abertura_dir = _stage_dir(item, 'abertura', '00_abertura')
        ensaios_dir = _stage_dir(item, 'ensaios', '01_ensaios')
        decisoes_dir = _stage_dir(item, 'decisoes', '02_decisoes_e_limites')
        consolidado_dir = _stage_dir(item, 'consolidado', '03_consolidado')
        abertura_files = list_md_files(abertura_dir) if abertura_dir.exists() else []
        ensaio_files = list_md_files(ensaios_dir) if ensaios_dir.exists() else []
        decisao_files = list_md_files(decisoes_dir) if decisoes_dir.exists() else []
        consolidado_files = list_md_files(consolidado_dir) if consolidado_dir.exists() else []
        active = None
        status = 'VAZIA'
        if consolidado_files:
            active = consolidado_files[-1]
            status = 'CONSOLIDADA'
        elif decisao_files:
            active = decisao_files[-1]
            status = 'DECIDIDA_SEM_CONSOLIDAR'
        elif ensaio_files:
            active = ensaio_files[-1]
            status = 'EM_ENSAIO'
        elif abertura_files:
            active = abertura_files[-1]
            status = 'ABERTA'
        faixas.append(FaixaInfo(
            number=num,
            name=item.name,
            path=item,
            abertura_dir=abertura_dir,
            ensaios_dir=ensaios_dir,
            decisoes_dir=decisoes_dir,
            consolidado_dir=consolidado_dir,
            abertura_files=abertura_files,
            ensaio_files=ensaio_files,
            decisao_files=decisao_files,
            consolidado_files=consolidado_files,
            active_file=active,
            status=status,
        ))
    return faixas


def scan_transicoes(transicao_root: Path) -> list[dict[str, Any]]:
    out = []
    if not transicao_root.exists():
        return out
    for p in sorted(transicao_root.glob('*.md'), key=lambda x: natural_sort_key(x.name)):
        m = TRANS_RE.match(p.name)
        if not m:
            continue
        out.append({
            'from': int(m.group('from')),
            'to': int(m.group('to')),
            'file': p,
            'name': p.name,
        })
    return out


def latest_transition_for(transicoes: list[dict[str, Any]], from_num: int) -> dict[str, Any] | None:
    candidates = [t for t in transicoes if t['from'] == from_num]
    return candidates[-1] if candidates else None


def faixa_slug(name: str) -> str:
    m = FAIXA_RE.match(name)
    return m.group('slug') if m else name


def normalized_slug(slug: str) -> str:
    return slugify(slug)


def semantic_core_slug(slug: str) -> str:
    slug_n = normalized_slug(slug)
    toks = [t for t in slug_n.split('_') if t]
    if not toks:
        return slug_n

    out: list[str] = []
    i = 0
    if re.fullmatch(r'cf\d+', toks[0]):
        out.append(toks[0])
        i = 1

    rest = toks[i:]
    has_primary_numeric = any(re.fullmatch(r'p\d+', t) for t in rest)
    if not rest:
        return '_'.join(out) if out else slug_n

    if has_primary_numeric:
        for t in rest:
            if t in DERIVATIVE_MARKERS:
                break
            out.append(t)
        return '_'.join(out) if out else slug_n

    # Sem passos Pxx, se começar logo por marcador derivativo, o núcleo fica no CF.
    if out:
        return '_'.join(out)
    return rest[0]


def slug_has_derivative_markers(slug: str) -> bool:
    toks = [t for t in normalized_slug(slug).split('_') if t]
    return any(t in DERIVATIVE_MARKERS for t in toks)


def repeated_pos_post_depth(slug: str) -> int:
    toks = [t for t in normalized_slug(slug).split('_') if t]
    return sum(1 for t in toks if t in {'pos', 'post'})


def duplicate_slug_map(faixas: list[FaixaInfo]) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for f in faixas:
        s = normalized_slug(faixa_slug(f.name))
        out.setdefault(s, []).append(f.number)
    return {k: v for k, v in out.items() if len(v) > 1}


def tail_same_core_chain(faixas: list[FaixaInfo]) -> list[FaixaInfo]:
    if not faixas:
        return []
    tail = list(faixas)
    core = semantic_core_slug(faixa_slug(tail[-1].name))
    chain: list[FaixaInfo] = []
    for f in reversed(tail):
        if semantic_core_slug(faixa_slug(f.name)) != core:
            break
        chain.append(f)
    chain.reverse()
    return chain


def _clean_inline_value(value: str) -> str:
    value = value.strip().strip('`').strip()
    value = re.sub(r'^[-*]\s*', '', value)
    return value.strip()


def _is_probable_filename(value: str) -> bool:
    if not value or '*' in value:
        return False
    return bool(re.fullmatch(r'[A-Za-z0-9_./\\-]+\.md', value))


def _is_probable_folder(value: str) -> bool:
    if not value or '*' in value:
        return False
    low = value.lower()
    if 'nome do próximo ficheiro' in low or 'nome do proximo ficheiro' in low:
        return False
    if 'pasta can' in low or 'pasta de destino' in low:
        return False
    if '00_abertura' in value:
        return True
    if re.match(r'^\d{2}_faixa_[A-Za-z0-9_./\\-]+$', value, re.I):
        return True
    if re.match(r'^[A-Za-z]:\\', value):
        return True
    return False


def _next_nonempty_value(lines: list[str], start_idx: int, kind: str) -> str:
    for j in range(start_idx + 1, min(start_idx + 6, len(lines))):
        cand = _clean_inline_value(lines[j])
        if not cand:
            continue
        if cand.startswith('**') and cand.endswith('**'):
            continue
        if kind == 'filename' and _is_probable_filename(cand):
            return cand
        if kind == 'folder' and _is_probable_folder(cand):
            return cand
    return ''


def _extract_labeled_value(text: str, labels: list[str], kind: str) -> str:
    lines = text.splitlines()
    for i, raw in enumerate(lines):
        line = raw.strip()
        low = line.lower()
        for label in labels:
            if label in low:
                same_line = ''
                m = re.search(r':\s*(.*)$', line)
                if m:
                    same_line = _clean_inline_value(m.group(1))
                if kind == 'filename' and _is_probable_filename(same_line):
                    return same_line
                if kind == 'folder' and _is_probable_folder(same_line):
                    return same_line
                nxt = _next_nonempty_value(lines, i, kind)
                if nxt:
                    return nxt
    return ''


def _match_abertura_filename(text: str) -> str | None:
    labeled = _extract_labeled_value(text, LABEL_NEXT_FILENAME, 'filename')
    if labeled:
        return labeled

    patterns = [
        r'para gerar o ficheiro\s*[:\-]?\s*`?([^`\n]+?\.md)`?',
        r'(ABERTURA_FAIXA_EXPOSITIVA_CONTROLADA_[A-Z0-9_]+\.md)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            cand = _clean_inline_value(m.group(1))
            if _is_probable_filename(cand):
                return cand
    return None


def _match_folder_hint(text: str) -> str:
    labeled = _extract_labeled_value(text, LABEL_NEXT_FOLDER, 'folder')
    if labeled:
        return labeled

    patterns = [
        r'([A-Za-z]:\\[^`\n]+?00_abertura)',
        r'((?:\d{2}_faixa_[^`\n/\\]+(?:[/\\][^`\n/\\]+)*)[/\\]00_abertura)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            cand = _clean_inline_value(m.group(1))
            if _is_probable_folder(cand):
                return cand
    return ''


def infer_next_faixa_folder_from_filename(to_num: int, filename: str) -> str:
    stem = filename[:-3] if filename.lower().endswith('.md') else filename
    stem = re.sub(r'^ABERTURA_FAIXA_EXPOSITIVA_CONTROLADA_', '', stem, flags=re.I)
    stem = re.sub(r'^ABERTURA_', '', stem, flags=re.I)
    slug = slugify(stem)
    return f"{to_num:02d}_faixa_{slug}\\00_abertura"


def transition_allows_auto_open(text: str) -> bool:
    low = text.lower()
    if any(marker in low for marker in CONDITIONAL_OPENING_MARKERS):
        return False
    if any(marker in low for marker in POSITIVE_OPENING_MARKERS):
        return True
    return True


def _coerce_folder_to_to_num(folder: str, to_num: int, filename: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if not folder:
        return infer_next_faixa_folder_from_filename(to_num, filename), warnings

    p = Path(folder)
    parts = list(p.parts)
    replaced = False
    for idx, part in enumerate(parts):
        m = FAIXA_SEGMENT_RE.match(part)
        if not m:
            continue
        actual_num = int(m.group('num'))
        if actual_num != to_num:
            parts[idx] = f"{to_num:02d}_faixa_{m.group('slug')}"
            warnings.append(
                f"Pasta da decisão apontava para faixa {actual_num:02d}, mas a transição é para {to_num:02d}; prefixo corrigido automaticamente."
            )
        replaced = True
        break

    new_path = Path(*parts) if parts else Path(folder)
    new_folder = str(new_path)

    if not replaced:
        new_folder = infer_next_faixa_folder_from_filename(to_num, filename)
        warnings.append('Pasta da decisão sem segmento canónico de faixa; pasta inferida automaticamente a partir do nome do ficheiro.')

    if '00_abertura' not in new_folder.replace('/', '\\').lower():
        new_folder = str(Path(new_folder) / '00_abertura')
        warnings.append('Pasta da decisão sem subpasta 00_abertura; subpasta acrescentada automaticamente.')

    return new_folder, warnings


def parse_transition_next_target(transition_file: Path) -> dict[str, Any] | None:
    text = read_text(transition_file)
    filename = _match_abertura_filename(text)
    if not filename:
        return None
    folder = _match_folder_hint(text)
    m = TRANS_RE.match(transition_file.name)
    to_num = int(m.group('to')) if m else 0
    if not _is_probable_folder(folder):
        folder = ''
    folder, warnings = _coerce_folder_to_to_num(folder, to_num, filename)
    return {
        'filename': filename,
        'folder': folder,
        'to_num': to_num,
        'auto_open': transition_allows_auto_open(text),
        'warnings': warnings,
    }




def decision_requires_preserve_limit(decision_file: Path) -> bool:
    """
    Deteta decisões locais que mandam preservar o limite atual e bloquear
    continuação automática, consolidação ou transição por defeito.
    """
    try:
        text = decision_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    t = text.lower()
    # Normalizações leves para reduzir falhas por variantes gráficas
    t = t.replace("—", "-").replace("–", "-").replace("`", "")
    t = " ".join(t.split())

    preserve_patterns = [
        # padrões já usados antes
        "próximo passo prudente é preservar o limite",
        "proximo passo prudente é preservar o limite",
        "não há base para continuação automática",
        "nao ha base para continuacao automatica",
        "não fica decidido agora",
        "nao fica decidido agora",
        "nem transitar para",
        "não transitar para",
        "nao transitar para",

        # padrões novos que apareceram em CF12
        "preservar o limite agora fixado",
        "preservar primeiro; só reensaiar por decisão explícita",
        "preservar primeiro; so reensaiar por decisao explicita",
        "não há autorização para continuação automática",
        "nao ha autorizacao para continuacao automatica",
        "não abrir novo ensaio automaticamente",
        "nao abrir novo ensaio automaticamente",
        "o próximo passo prudente não é prolongar a faixa por inércia",
        "o proximo passo prudente nao e prolongar a faixa por inercia",
        "manter cf12 no limite agora fixado",
        "manter no limite agora fixado",
        "só admitir novo ensaio por deliberação explícita",
        "so admitir novo ensaio por deliberacao explicita",
        "a faixa ainda não está consolidada",
        "a faixa ainda nao esta consolidada",

        # variantes prudenciais úteis
        "não há base para consolidação",
        "nao ha base para consolidacao",
        "não há base para continuação automatica",
        "nao ha base para continuacao automatica",
        "não há autorização para transição automática",
        "nao ha autorizacao para transicao automatica",
        "não autoriza passagem para",
        "nao autoriza passagem para",
    ]

    return any(p in t for p in preserve_patterns)

def decision_suggests_consolidation(decision_file: Path) -> bool:
    text = read_text(decision_file).lower()
    positive_markers = [
        'próximo passo recomendado é consolidar',
        'proximo passo recomendado e consolidar',
        'base imediata para decidir a consolidação',
        'base imediata para a consolidação',
        'vale como base imediata para a consolidação',
        'gera-se um ficheiro único de consolidação',
    ]
    negative_markers = [
        'teste negativo controlado',
        'não produziu ganho positivo novo',
        'nao produziu ganho positivo novo',
        'base imediata para a decisão de transição seguinte',
        'base imediata para a decisao de transicao seguinte',
        'não um ganho positivo novo',
        'nao um ganho positivo novo',
    ]
    if any(m in text for m in negative_markers):
        return False
    if any(m in text for m in positive_markers):
        return True
    return True
