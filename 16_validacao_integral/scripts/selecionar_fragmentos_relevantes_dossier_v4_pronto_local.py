#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selecionar_fragmentos_relevantes_dossier_v4.py

Pipeline local, determinístico, auditável e sem API para validação integral de
confrontos filosóficos por reabertura fragmentária.

Objetivo operacional:
- ler o dossier reformulado e as fontes normativas do projeto;
- extrair o estado declarado do dossier por parsing estrutural Markdown;
- carregar e enriquecer a base fragmentária, com fallback disciplinado quando a
  base específica não existe;
- construir um centro admissível do confronto segundo precedência normativa;
- calcular scoring vetorial explícito e selecionador de sample equilibrado;
- diagnosticar centro dominante, corredores, vizinhança, altitude e operações;
- adjudicar uma decisão metodológica prudente;
- validar consistência interna;
- escrever outputs JSON, Markdown e TXT;
- executar self-checks opcionais de regressão.

Notas metodológicas vinculativas implementadas:
- o sample fragmentário nunca é soberano acima do dossier reformulado;
- mediacionalidade, peso epistemológico e corredores partilhados não contam por
  si sós como nuclearidade;
- IDs canónicos só entram após regex estrita e validação contra catálogo;
- tokens correntes contaminantes ficam em invalid_id_tokens;
- no caso CF03, o núcleo admissível é compatível com a reformulação forte:
  P14, P15, P18, P19, P21, P22 centrais; P01 e P13 como fundo; P02 e P05
  descentradas; corredor P23_P30 impedido de subir automaticamente a centro.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import re
import sys
import traceback
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence


# =============================================================================
# CONSTANTES CANÓNICAS
# =============================================================================

SCRIPT_NAME = "selecionar_fragmentos_relevantes_dossier_v4.py"
SUPPORTED_CONFRONTOS = {f"CF{i:02d}" for i in range(1, 19)}

# Hierarquia normativa obrigatória, da fonte mais forte para a mais fraca.
NORMATIVE_PRECEDENCE: tuple[tuple[str, float], ...] = (
    ("meta_norm_readme", 1.10),
    ("dossier_reformulado", 1.00),
    ("adjudicacao_restrita_confronto", 0.78),
    ("matriz_confronto", 0.58),
    ("fontes_estruturais", 0.42),
    ("config_confronto", 0.24),
    ("sample_fragmentario", 0.06),
)

DEFAULT_OUTPUT_DIRNAME = "outputs_dossier_v4"
DEFAULT_SAMPLE_SIZE = 15
DEFAULT_TOP_K_SCORING = 80

FILE_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "readme_reabertura": {"name": "05_README_Reajuste_dossiers_por_reabertura_fragmentaria_SUBSTITUICAO.md", "required": True},
    "matriz_confronto": {"name": "matriz_confronto_filosofico_v1.json", "required": True},
    "adjudicacao_confrontos": {"name": "adjudicacao_confrontos_filosoficos_restrita_v2.json", "required": True},
    "proposicoes_nucleares_enriquecidas": {"name": "proposicoes_nucleares_enriquecidas_v1.json", "required": True},
    "mapa_dedutivo_final": {"name": "mapa_dedutivo_canonico_final__vfinal_corrente.json", "required": True},
    "mapa_arquitetura_fragmentos": {"name": "02_mapa_dedutivo_arquitetura_fragmentos.json", "required": True},
    "impacto_fragmentos_no_mapa": {"name": "impacto_fragmentos_no_mapa.json", "required": True},
    "indice_sequencial": {"name": "indice_sequencial.json", "required": True},
    "mapa_integral_do_indice": {"name": "mapa_integral_do_indice.json", "required": True},
    "meta_indice": {"name": "meta_indice.json", "required": True},
    "meta_referencia_do_percurso": {"name": "meta_referencia_do_percurso.json", "required": True},
    "operacoes": {"name": "operacoes.json", "required": True},
    "todos_os_conceitos": {"name": "todos_os_conceitos.json", "required": True},
    "argumentos_unificados": {"name": "argumentos_unificados.json", "required": True},
    "arvore_fecho_superior": {"name": "arvore_do_pensamento_v1_fecho_superior.json", "required": True},
    "arvore_v1": {"name": "arvore_do_pensamento_v1.json", "required": False},
    "fragmentos_resegmentados": {"name": "fragmentos_resegmentados.json", "required": True},
    "proposicoes": {"name": "proposicoes.json", "required": True},
    "conteudo_completo_percursos": {"name": "conteudo_completo_percursos.txt", "required": True},
    "indice_de_percursos": {"name": "indice_de_percursos.json", "required": False},
    "grafo_resumo": {"name": "grafo_resumo.txt", "required": False},
    "relatorio_revisao_argumentos": {"name": "relatorio_revisao_argumentos_restritiva_v1.txt", "required": False},
    "decisoes_canonicas_intermedias": {"name": "decisoes_canonicas_intermedias_consolidado_candidato.json", "required": False},
    "adjudicacao_argumentos_api": {"name": "adjudicacao_argumentos_api_v1.json", "required": False},
}

OPTIONAL_CURRENT_DIAGNOSTIC_PATTERNS = (
    "{cf}_diagnostico_metodologico_v4.json",
    "{cf}_diagnostico_metodologico_v4.md",
    "relatorio_diagnostico_metodologico_{cf}_v4.txt",
)

DOSSIER_CANDIDATE_FILENAMES = (
    "{cf}_dossier_confronto_REFORMULADO.md",
    "{cf}_dossier_confronto_FINAL_CONSOLIDADO.md",
    "{cf}_dossier_confronto_CONSOLIDADO.md",
)

BASE_CANDIDATE_FILENAMES = (
    "{cf}_base_fragmentaria.json",
    "base_fragmentaria_{cf}.json",
)

STRICT_ID_PATTERNS: dict[str, str] = {
    "proposicao": r"^P\d{2,4}$",
    "ponte": r"^PN\d{2,4}$",
    "ancoragem": r"^AC\d{2,4}$",
    "campo": r"^CR\d{2,4}$",
    "capitulo": r"^CAP_\d{2}_[A-Z0-9_]+$",
    "regime": r"^REGIME_[A-Z0-9_]+$",
    "percurso": r"^P_[A-Z0-9_]+$",
    "argumento": r"^ARG_[A-Z0-9_]+$",
    "confronto": r"^CF\d{2}$",
}

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
BROAD_TOKEN_PATTERN = re.compile(r"[A-Za-zÀ-ÿ0-9_]+(?:_[A-Za-z0-9_]+)*")

STOPWORDS = {
    "a", "o", "e", "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
    "por", "para", "com", "sem", "um", "uma", "uns", "umas", "que", "se", "ao", "aos",
    "à", "às", "como", "mais", "menos", "já", "ja", "ou", "ser", "é", "foi", "são",
    "sao", "era", "não", "nao", "sim", "lhe", "lhes", "isto", "isso", "aquilo",
    "num", "numa", "entre", "sobre", "também", "tambem", "muito", "muita", "muitos",
    "muitas", "todo", "toda", "todos", "todas", "cada", "há", "ha", "porque", "pois",
    "onde", "quando", "qual", "quais", "qualquer", "mesmo", "mesma", "mesmos", "mesmas",
}

LOW_SIGNAL_TOKENS = {
    "problema", "problemas", "questao", "questões", "questoes", "sistema", "sistemas",
    "campo", "campos", "estrutura", "estruturas", "relação", "relacao", "relações", "relacoes",
    "nível", "níveis", "niveis", "modo", "modos", "forma", "formas", "processo", "processos",
}

CURRENT_BUG_GUARD_TOKENS = {
    "Passagem", "Pergunta", "Por", "preservar_com_restricoes",
    "precisa_revisao_humana", "precisa_revisão_humana", "aligned",
    "pseudo_aligned", "misaligned", "strongly_misaligned",
    "P23_P30", "P25_P30", "P33_P37",
}

VALIDATION_STATE_SCORE = {
    "valido": 1.00,
    "valido_com_avisos": 0.82,
    "invalido_tolerado": 0.44,
    "por_validar": 0.40,
    "desconhecido": 0.55,
}
CENTRALITY_SCORE = {"dominante": 1.00, "exploratorio": 0.66, "exploratório": 0.66, "auxiliar": 0.52, "marginal": 0.35}
IMPACT_EFFECT_SCORE = {"explicita": 0.95, "medeia": 0.72, "corrige": 0.84, "novo_passo": 1.00, "repete": 0.45, "sem_impacto_relevante": 0.18}
IMPACT_ACTION_SCORE = {"densificar": 0.82, "reescrever": 0.88, "sem_acao": 0.18, "criar_passo": 1.00, "sem_ação": 0.18}
PRIORITY_SCORE = {"alta": 1.00, "estrutural": 1.00, "media": 0.70, "média": 0.70, "baixa": 0.35}
CONFIDENCE_SCORE = {"alto": 1.00, "alta": 1.00, "medio": 0.70, "médio": 0.70, "media": 0.70, "baixa": 0.40, "baixo": 0.40}

CORRIDOR_DEFINITIONS: dict[str, list[str]] = {
    "P14_P22": [f"P{i:02d}" for i in range(14, 23)],
    "P23_P30": [f"P{i:02d}" for i in range(23, 31)],
    "P25_P30": [f"P{i:02d}" for i in range(25, 31)],
    "P27_P34": [f"P{i:02d}" for i in range(27, 35)],
    "P33_P37": [f"P{i:02d}" for i in range(33, 38)],
    "P42_P48": [f"P{i:02d}" for i in range(42, 49)],
    "P46_P49": [f"P{i:02d}" for i in range(46, 50)],
}

DEFAULT_NEIGHBOR_DOSSIERS = {
    "CF03": ["CF04", "CF05"],
    "CF04": ["CF03", "CF05", "CF06", "CF07"],
    "CF05": ["CF04", "CF06", "CF07"],
    "CF06": ["CF04", "CF05", "CF07", "CF08"],
    "CF07": ["CF04", "CF05", "CF06", "CF08"],
    "CF08": ["CF06", "CF07"],
}

DEFAULT_SENSITIVE_CORRIDORS = {
    "CF03": ["P14_P22", "P23_P30"],
    "CF04": ["P23_P30", "P25_P30", "P33_P37"],
    "CF05": ["P23_P30", "P25_P30"],
    "CF06": ["P25_P30", "P27_P34", "P33_P37"],
    "CF07": ["P25_P30", "P33_P37"],
    "CF08": ["P25_P30", "P33_P37"],
}

DEFAULT_ALTITUDE_EXPECTATION = {
    "CF03": "axial_transicional",
    "CF04": "axial_ontologico_derivado",
    "CF05": "axial_ontologico_derivado",
    "CF06": "axial_mediacional",
    "CF07": "axial_epistemologico",
    "CF08": "axial_mediacional",
}

DEFAULT_AUTONOMY_EXPECTATION = {
    "CF03": "shared_background_with_distinct_core",
    "CF04": "autonomous",
    "CF05": "autonomous_but_narrow",
    "CF06": "shared_background_with_distinct_core",
    "CF07": "shared_background_with_distinct_core",
    "CF08": "autonomous",
}

PATH_TYPE_ALTITUDE = {
    "axial_fundational": 1.0,
    "axial_fundational_dynamic": 1.3,
    "axial_transitional": 2.2,
    "axial_ontological_derived": 2.6,
    "axial_mediational": 3.3,
    "axial_epistemological": 4.0,
    "axial_epistemological_critical": 4.2,
    "axial_ethical_ontological": 4.1,
    "axial_critical_corrective": 4.4,
    "percursive": 3.8,
    "unknown": 0.0,
}


PATH_ID_ALIASES = {
    "P_TRANSICAO_ANTROPOLOGIA_ONTOLOGICA": "P_TRANSICAO_ANTROPOLOGICA_ONTOLOGICA",
}

PATH_TYPE_ALIASES = {
    "axial_transicional": "axial_transitional",
    "axial_ontologico_derivado": "axial_ontological_derived",
    "axial_epistemologico": "axial_epistemological",
    "axial_epistemologico_critico": "axial_epistemological_critical",
    "axial_etico_ontologico": "axial_ethical_ontological",
    "axial_critico_corretivo": "axial_critical_corrective",
    "axial_fundacional": "axial_fundational",
    "axial_fundacional_dinamico": "axial_fundational_dynamic",
    "percursivo_critico_epistemologico": "percursive",
    "percursivo_critico_transversal": "percursive",
    "percursivo_critico_etico": "percursive",
    "percursivo_critico_limite": "percursive",
    "percursivo_transversal_ontologico_etico": "percursive",
    "percursivo_transversal_filosofico": "percursive",
    "percursivo_ciclico_pratico": "percursive",
    "percursivo_integral": "percursive",
    "axial_transitional": "axial_transitional",
    "axial_ontological_derived": "axial_ontological_derived",
    "axial_epistemological": "axial_epistemological",
    "axial_epistemological_critical": "axial_epistemological_critical",
    "axial_ethical_ontological": "axial_ethical_ontological",
    "axial_critical_corrective": "axial_critical_corrective",
    "axial_fundational": "axial_fundational",
    "axial_fundational_dynamic": "axial_fundational_dynamic",
    "axial_mediational": "axial_mediational",
    "percursive": "percursive",
}

SEGMENTATION_CONFIDENCE_SCORE = {"alta": 1.00, "media": 0.68, "baixa": 0.35}
SEMANTIC_INTEGRITY_SCORE = {"alto": 1.00, "medio": 0.68, "médio": 0.68, "baixo": 0.35}

MEDIATIONAL_PATH_IDS = {"P_EIXO_SIMBOLICO_MEDIACIONAL"}
EPISTEMOLOGICAL_PATH_IDS = {"P_EIXO_EPISTEMOLOGICO", "P_PERCURSO_DO_ERRO_E_CORRECAO", "P_EIXO_ESCALA_E_ERRO_DE_ESCALA"}

SECTION_FUZZY_MAP: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("nota_previa", ("nota previa", "nota prévia", "redecisao metodologica", "redecisão metodológica", "diagnostico consolidado")),
    ("pergunta_central", ("pergunta central",)),
    ("formulacao_curta", ("formulacao curta", "formulação curta")),
    ("descricao_confronto", ("descricao do confronto", "descrição do confronto")),
    ("tese_canonica_provisoria", ("tese canonica provisoria", "tese canónica provisória")),
    ("tese_expandida", ("tese expandida", "tese negativa", "o que o dossier rejeita")),
    ("proposicoes_envolvidas", ("proposicoes envolvidas", "proposições envolvidas", "proposicoes nucleares", "proposições nucleares", "nucleo filosofico efetivo", "núcleo filosófico efetivo")),
    ("estatuto_arquitetonico", ("estatuto arquitetonico", "estatuto arquitetónico")),
    ("articulacao_estrutural", ("articulacao estrutural", "articulação estrutural")),
    ("pontes", ("pontes", "pontes entre niveis", "pontes entre níveis")),
    ("ancoragens", ("ancoragens", "ancoragem principal", "ancoragens cientificas", "ancoragens científicas")),
    ("campos_do_real", ("campo do real", "campos do real")),
    ("distincoes", ("distincoes", "distinções")),
    ("objecoes", ("objecoes", "objeções", "objeções fortes", "objecoes fortes")),
    ("decisao", ("decisao", "decisão", "sequencia", "sequência", "observacoes finais")),
)


# =============================================================================
# ENUMERAÇÕES
# =============================================================================

class AlignmentClassification(str, Enum):
    aligned = "aligned"
    pseudo_aligned = "pseudo_aligned"
    misaligned = "misaligned"
    strongly_misaligned = "strongly_misaligned"


class AutonomyClassification(str, Enum):
    autonomous = "autonomous"
    autonomous_but_narrow = "autonomous_but_narrow"
    shared_background_with_distinct_core = "shared_background_with_distinct_core"
    neighbor_absorption = "neighbor_absorption"
    indeterminate = "indeterminate"


class RecommendedMethodologicalDecision(str, Enum):
    preservar = "preservar"
    preservar_com_restricoes = "preservar_com_restricoes"
    recentrar = "recentrar"
    substituir_estruturalmente = "substituir_estruturalmente"
    reabrir_com_revisao_humana = "reabrir_com_revisao_humana"


class CorridorStatus(str, Enum):
    none = "none"
    corridor_support = "corridor_support"
    corridor_capture = "corridor_capture"


class NeighborStatus(str, Enum):
    none = "none"
    shared_background = "shared_background"
    neighbor_absorption = "neighbor_absorption"


class AltitudeStatus(str, Enum):
    aligned_altitude = "aligned_altitude"
    higher_axis_pressure = "higher_axis_pressure"
    higher_axis_capture = "higher_axis_capture"
    lower_axis_underreach = "lower_axis_underreach"


class DecisionRedecisionClass(str, Enum):
    none = "none"
    soft_recenter = "soft_recenter"
    deep_recenter = "deep_recenter"
    structural_substitution = "structural_substitution"


# =============================================================================
# EXCEÇÕES CUSTOMIZADAS
# =============================================================================

class DossierV4Error(Exception):
    pass


class ConfigurationError(DossierV4Error):
    pass


class MissingRequiredSourceError(DossierV4Error):
    pass


class SourceDecodeError(DossierV4Error):
    pass


class NormativeConsistencyError(DossierV4Error):
    pass


class UnknownStructuralIdError(DossierV4Error):
    pass


class DossierParsingError(DossierV4Error):
    pass


class StructuralExtractionError(DossierV4Error):
    pass


class FragmentBaseError(DossierV4Error):
    pass


class OperationInferenceError(DossierV4Error):
    pass


class ScoringError(DossierV4Error):
    pass


class SampleSelectionError(DossierV4Error):
    pass


class AdmissibleCenterError(DossierV4Error):
    pass


class DiagnosisError(DossierV4Error):
    pass


class DecisionAdjudicationError(DossierV4Error):
    pass


class InternalConsistencyError(DossierV4Error):
    pass


class OutputRenderingError(DossierV4Error):
    pass


class OutputWriteError(DossierV4Error):
    pass


class SelfCheckFailure(DossierV4Error):
    pass


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass(slots=True)
class ScoreWeights:
    base_strength: float = 0.30
    nuclearity: float = 0.34
    declared_alignment: float = 0.22
    mediationality_penalty: float = 0.16
    epistemic_penalty: float = 0.14
    background_penalty: float = 0.12
    neighbor_penalty: float = 0.14
    corridor_capture_penalty: float = 0.20
    higher_axis_penalty: float = 0.18


@dataclass(slots=True)
class RuntimeConfig:
    confronto_id: str
    project_root: Path
    dossier_path: Path
    output_dir: Path
    config_path: Optional[Path]
    base_fragment_path: Optional[Path]
    strict_mode: bool
    run_self_checks: bool
    sample_size: int
    top_k_scoring: int
    weights: ScoreWeights
    verbose: bool = True


@dataclass(slots=True)
class SourceBundle:
    data: dict[str, Any]
    paths: dict[str, Path]
    warnings: list[str]
    optional_missing: list[str]


@dataclass(slots=True)
class NormativeIndices:
    proposition_ids: set[str]
    bridge_ids: set[str]
    anchorage_ids: set[str]
    field_ids: set[str]
    chapter_ids: set[str]
    regime_ids: set[str]
    path_ids: set[str]
    argument_ids: set[str]
    cf_ids: set[str]
    proposition_to_chapters: dict[str, list[str]]
    proposition_to_regimes: dict[str, list[str]]
    proposition_to_paths: dict[str, list[str]]
    proposition_to_arguments: dict[str, list[str]]
    proposition_to_operations: dict[str, list[str]]
    proposition_dependencies: dict[str, list[str]]
    chapter_to_regimes: dict[str, list[str]]
    chapter_to_paths: dict[str, list[str]]
    chapter_to_operations: dict[str, list[str]]
    argument_to_operations: dict[str, list[str]]
    argument_to_regimes: dict[str, list[str]]
    argument_to_paths: dict[str, list[str]]
    argument_to_chapters: dict[str, list[str]]
    path_to_type: dict[str, str]
    path_to_required_paths: dict[str, list[str]]
    corridors: dict[str, list[str]]
    matrix_by_cf: dict[str, dict[str, Any]]
    adjudication_by_cf: dict[str, dict[str, Any]]
    cf_neighbor_map: dict[str, list[str]]
    cf_sensitive_corridors: dict[str, list[str]]
    cf_altitude_expectation: dict[str, str]
    cf_autonomy_expectation: dict[str, str]
    ramo_to_arguments: dict[str, list[str]]
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DeclaredDossierState:
    confronto_id: str
    dossier_title: str
    question_central: str
    descricao_do_confronto: str
    tese_canonica_provisoria: str
    proposicoes_envolvidas: list[str]
    proposicoes_nucleares_centrais: list[str]
    proposicoes_background: list[str]
    proposicoes_rejeitadas: list[str]
    pontes: list[str]
    ancoragens: list[str]
    campos_do_real: list[str]
    capitulos: list[str]
    regimes: list[str]
    percursos: list[str]
    argumentos: list[str]
    declared_profiles: list[str]
    invalid_id_tokens: list[str]
    parsing_warnings: list[str]
    redecision_class: DecisionRedecisionClass
    redecision_evidence: list[str]
    config_defaults: dict[str, Any]
    section_trace: list[dict[str, Any]]


@dataclass(slots=True)
class FragmentRecord:
    fragment_id: str
    source_mode: str
    text: str
    proposition_weights: dict[str, float]
    proposition_ids: list[str]
    chapter_ids: list[str]
    regime_ids: list[str]
    path_ids: list[str]
    argument_ids: list[str]
    corridor_ids: list[str]
    operation_ids_inferred: list[str]
    impact_effect: str
    impact_action: str
    impact_priority: str
    confidence_score: float
    validation_state: str
    centrality: str
    source_labels: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FragmentScoreVector:
    fragment_id: str
    base_strength: float
    nuclearity: float
    mediationality: float
    epistemic_weight: float
    shared_background: float
    neighbor_overlap: float
    corridor_support: float
    corridor_capture: float
    higher_axis_capture: float
    declared_alignment: float
    overall_selection_score: float
    categories: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SampleSelection:
    selected_fragment_ids: list[str]
    ranked_fragments: list[dict[str, Any]]
    coverage_summary: dict[str, Any]
    nuclear_fragments: list[str]
    mediational_fragments: list[str]
    background_fragments: list[str]
    capture_risk_fragments: list[str]
    contradictory_fragments: list[str]
    excluded_high_score_fragments_with_reason: list[dict[str, Any]]
    selection_warnings: list[str]


@dataclass(slots=True)
class AdmissibleConfrontCenter:
    confronto_id: str
    promoted_proposition_ids: list[str]
    promoted_weak_ids: list[str]
    nuclear_expanded_ids: list[str]
    background_proposition_ids: list[str]
    rejected_proposition_ids: list[str]
    promoted_bridge_ids: list[str]
    promoted_anchorage_ids: list[str]
    promoted_field_ids: list[str]
    promoted_chapter_ids: list[str]
    promoted_regime_ids: list[str]
    promoted_percurso_ids: list[str]
    promoted_argument_ids: list[str]
    admissible_corridors: list[str]
    rejected_corridors: list[str]
    source_contributions: list[dict[str, Any]]
    promoted_reasons: dict[str, list[str]]
    rejected_reasons: dict[str, list[str]]
    notes: list[str]


@dataclass(slots=True)
class ArchitecturalDiagnosis:
    confronto_id: str
    dominant_sample_center: list[str]
    dominant_center_ratio: float
    dominant_sample_props: dict[str, float]
    corridor_status: CorridorStatus
    dominant_corridor: str
    neighbor_status: NeighborStatus
    top_neighbor_cf: str
    top_neighbor_ratio: float
    altitude_status: AltitudeStatus
    dominant_altitude: float
    dominant_path_types: list[str]
    operations_counter: dict[str, int]
    dominant_operations_profile: list[str]
    alignment_classification: AlignmentClassification
    autonomy_classification: AutonomyClassification
    why_not_aligned: list[str]
    why_corridor_status: list[str]
    why_neighbor_status: list[str]
    why_altitude_status: list[str]
    additional_notes: list[str]


@dataclass(slots=True)
class MethodologicalDecision:
    confronto_id: str
    recommended_methodological_decision: RecommendedMethodologicalDecision
    confidence: float
    why_not_preserve: list[str]
    decision_rationale: list[str]
    decision_conflict_flag: bool
    decision_conflict_reasons: list[str]
    inferred_from_alignment: str
    preserved_nucleus_ids: list[str]


@dataclass(slots=True)
class OutputBundle:
    json_payload: dict[str, Any]
    markdown_text: str
    txt_text: str
    output_paths: dict[str, Path]


@dataclass(slots=True)
class SelfCheckReport:
    executed: bool
    passed: bool
    failures: list[str]
    warnings: list[str]
    checks: dict[str, bool]


@dataclass(slots=True)
class MarkdownSection:
    index: int
    level: int
    heading: str
    heading_normalized: str
    body: str


@dataclass(slots=True)
class ConsistencyCheckResult:
    success: bool
    warnings: list[str]
    errors: list[str]
    decision_conflict_flag: bool
    decision_conflict_reasons: list[str]
    central_projection: dict[str, Any]
    markdown_projection: str
    txt_projection: str


# =============================================================================
# UTILITÁRIOS
# =============================================================================


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_text(text: str) -> str:
    text = remove_accents(text).lower()
    text = re.sub(r"[^a-z0-9_\-\s]", " ", text)
    return normalize_spaces(text)




def normalize_path_id(path_id: str) -> str:
    path_id = _safe_str(path_id).strip() if "_safe_str" in globals() else str(path_id).strip()
    return PATH_ID_ALIASES.get(path_id, path_id)


def normalize_path_type(path_type: str) -> str:
    raw = (path_type or "").strip()
    if not raw:
        return "unknown"
    lowered = remove_accents(raw).lower().strip()
    return PATH_TYPE_ALIASES.get(lowered, PATH_TYPE_ALIASES.get(raw, raw))


def segmentation_confidence_to_score(text: str) -> float:
    return SEGMENTATION_CONFIDENCE_SCORE.get(normalize_text(text), 0.55)


def semantic_integrity_to_score(text: str) -> float:
    return SEMANTIC_INTEGRITY_SCORE.get(normalize_text(text), 0.55)


def _extract_base_fragment_scope_ids(payload: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, str):
                ids.add(item)
            elif isinstance(item, dict):
                fid = _safe_str(item.get("fragment_id")) or _safe_str(item.get("id")) or _safe_str(item.get("fragmento_id"))
                if fid:
                    ids.add(fid)
        return ids
    if isinstance(payload, dict):
        for key in ("fragment_ids", "selected_fragment_ids", "fragmentos_ids", "fragmentos"):
            val = payload.get(key)
            if isinstance(val, list):
                ids.update(_extract_base_fragment_scope_ids(val))
        return ids
    return ids

def tokenize(text: str) -> list[str]:
    return [tok for tok in normalize_text(text).split() if tok and tok not in STOPWORDS]


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def average(values: Iterable[float]) -> float:
    vals = list(values)
    return (sum(vals) / len(vals)) if vals else 0.0


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        raise SourceDecodeError(f"Falha ao ler texto em {path}: {exc}") from exc


def read_json(path: Path) -> Any:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise SourceDecodeError(f"JSON inválido em {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    except Exception as exc:
        raise OutputWriteError(f"Falha ao escrever ficheiro de texto {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    except Exception as exc:
        raise OutputWriteError(f"Falha ao escrever JSON {path}: {exc}") from exc


def dataclass_to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: dataclass_to_jsonable(val) for key, val in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): dataclass_to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [dataclass_to_jsonable(v) for v in value]
    return value


def relpath_str(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def find_file(project_root: Path, filename: str) -> Optional[Path]:
    direct = project_root / filename
    if direct.exists():
        return direct
    candidates = list(project_root.rglob(filename))
    if not candidates:
        return None
    candidates.sort(key=lambda p: (len(p.parts), str(p)))
    return candidates[0]


def weighted_overlap_ratio(weights: dict[str, float], target_ids: Sequence[str]) -> float:
    if not weights or not target_ids:
        return 0.0
    target = set(target_ids)
    total = sum(abs(v) for v in weights.values())
    if total <= 0:
        return 0.0
    hit = sum(abs(v) for k, v in weights.items() if k in target)
    return clamp(hit / total)


def confidence_text_to_score(text: str) -> float:
    return CONFIDENCE_SCORE.get(normalize_text(text), 0.55)


def priority_text_to_score(text: str) -> float:
    return PRIORITY_SCORE.get(normalize_text(text), 0.55)


def validation_state_to_score(text: str) -> float:
    return VALIDATION_STATE_SCORE.get(normalize_text(text), 0.55)


def centrality_to_score(text: str) -> float:
    return CENTRALITY_SCORE.get(normalize_text(text), 0.55)


def fuzzy_heading_key(heading: str) -> str:
    normalized = normalize_text(heading)
    for key, aliases in SECTION_FUZZY_MAP:
        if any(alias in normalized for alias in aliases):
            return key
    return normalized


def parse_markdown_sections(text: str) -> list[MarkdownSection]:
    lines = text.splitlines()
    sections: list[MarkdownSection] = []
    current_heading = ""
    current_level = 1
    current_body: list[str] = []
    index = 0
    started = False

    def flush() -> None:
        nonlocal index
        heading = current_heading or "Documento"
        body = "\n".join(current_body).strip()
        sections.append(
            MarkdownSection(
                index=index,
                level=current_level,
                heading=heading,
                heading_normalized=normalize_text(heading),
                body=body,
            )
        )
        index += 1

    for line in lines:
        match = HEADING_PATTERN.match(line)
        if match:
            if started:
                flush()
                current_body = []
            current_level = len(match.group(1))
            current_heading = normalize_spaces(match.group(2))
            started = True
        else:
            if not started:
                current_heading = "Documento"
                current_level = 1
                started = True
            current_body.append(line)
    if started:
        flush()
    return sections


def extract_inline_ids(text: str, id_kind: str, catalog: set[str]) -> list[str]:
    pattern = re.compile(STRICT_ID_PATTERNS[id_kind])
    ids = [token for token in BROAD_TOKEN_PATTERN.findall(text or "") if pattern.fullmatch(token) and token in catalog]
    return dedupe_preserve_order(ids)


def parse_conteudo_completo_percursos_txt(text: str) -> dict[str, dict[str, Any]]:
    parsed: dict[str, dict[str, Any]] = {}
    current_id = ""
    buffer: list[str] = []

    def flush() -> None:
        nonlocal current_id, buffer
        if not current_id:
            return
        raw = "\n".join(buffer).strip()
        payload: dict[str, Any] = {"raw_text": raw}
        if raw:
            try:
                payload.update(_safe_dict(json.loads(raw)))
            except Exception:
                pass
        parsed[current_id] = payload
        current_id = ""
        buffer = []

    for line in text.splitlines():
        m = re.match(r"^\s*FICHEIRO:\s*(P_[A-Z0-9_]+)\.json\s*$", line)
        if m:
            flush()
            current_id = normalize_path_id(m.group(1))
            buffer = []
            continue
        if current_id:
            buffer.append(line)
    flush()
    return parsed


# =============================================================================
# CONFIGURAÇÃO E CAMINHOS
# =============================================================================


def parse_cli_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validação integral de dossiers por reabertura fragmentária (v4).")
    parser.add_argument("confronto_id", help="ID do confronto, por exemplo CF03.")
    parser.add_argument("--project-root", type=Path, default=None, help="Raiz do projeto. Por omissão é inferida a partir do dossier ou do cwd.")
    parser.add_argument("--dossier-path", type=Path, default=None, help="Caminho explícito do dossier reformulado/consolidado.")
    parser.add_argument("--config-path", type=Path, default=None, help="Caminho explícito do ficheiro config do confronto.")
    parser.add_argument("--base-fragment-path", type=Path, default=None, help="Caminho explícito da base fragmentária do confronto.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Diretório de outputs. Por omissão usa outputs_dossier_v4.")
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE, help="Tamanho do sample final balanceado.")
    parser.add_argument("--top-k-scoring", type=int, default=DEFAULT_TOP_K_SCORING, help="Universo máximo após ranking para seleção balanceada.")
    parser.add_argument("--strict", action="store_true", help="Ativa modo estrito para consistência e self-checks.")
    parser.add_argument("--run-self-checks", action="store_true", help="Executa self-checks opcionais no fim.")
    parser.add_argument("--quiet", action="store_true", help="Silencia logs informativos." )
    return parser.parse_args(argv)


def infer_project_root(explicit_root: Optional[Path], dossier_path: Optional[Path]) -> Path:
    if explicit_root is not None:
        return explicit_root.resolve()
    if dossier_path is not None:
        return dossier_path.resolve().parent
    return Path.cwd().resolve()


def resolve_dossier_path(project_root: Path, confronto_id: str, explicit: Optional[Path]) -> Path:
    if explicit is not None:
        if not explicit.exists():
            raise ConfigurationError(f"Dossier explicitamente indicado não existe: {explicit}")
        return explicit.resolve()
    for candidate in DOSSIER_CANDIDATE_FILENAMES:
        located = find_file(project_root, candidate.format(cf=confronto_id))
        if located is not None:
            return located.resolve()
    raise ConfigurationError(f"Não foi possível localizar o dossier para {confronto_id}.")


def resolve_optional_config_path(project_root: Path, confronto_id: str, explicit: Optional[Path]) -> Optional[Path]:
    if explicit is not None:
        if not explicit.exists():
            raise ConfigurationError(f"Config explicitamente indicada não existe: {explicit}")
        return explicit.resolve()
    candidate = find_file(project_root, f"config_dossier_{confronto_id}_v4.json")
    return candidate.resolve() if candidate else None


def resolve_output_dir(project_root: Path, explicit: Optional[Path]) -> Path:
    if explicit is not None:
        return explicit.resolve()
    return (project_root / DEFAULT_OUTPUT_DIRNAME).resolve()


def build_runtime_config(args: argparse.Namespace) -> RuntimeConfig:
    confronto_id = args.confronto_id.strip().upper()
    if confronto_id not in SUPPORTED_CONFRONTOS:
        raise ConfigurationError(f"Confronto inválido: {confronto_id}")
    dossier_path = resolve_dossier_path(infer_project_root(args.project_root, args.dossier_path), confronto_id, args.dossier_path)
    project_root = infer_project_root(args.project_root, dossier_path)
    config_path = resolve_optional_config_path(project_root, confronto_id, args.config_path)
    base_fragment_path = args.base_fragment_path.resolve() if args.base_fragment_path else None
    sample_size = max(5, int(args.sample_size))
    top_k_scoring = max(sample_size, int(args.top_k_scoring))
    return RuntimeConfig(
        confronto_id=confronto_id,
        project_root=project_root,
        dossier_path=dossier_path,
        output_dir=resolve_output_dir(project_root, args.output_dir),
        config_path=config_path,
        base_fragment_path=base_fragment_path,
        strict_mode=bool(args.strict),
        run_self_checks=bool(args.run_self_checks),
        sample_size=sample_size,
        top_k_scoring=top_k_scoring,
        weights=ScoreWeights(),
        verbose=not bool(args.quiet),
    )


# =============================================================================
# CARREGAMENTO DE FONTES
# =============================================================================


def _resolve_base_fragment_path(runtime: RuntimeConfig) -> Optional[Path]:
    if runtime.base_fragment_path is not None and runtime.base_fragment_path.exists():
        return runtime.base_fragment_path
    for pattern in BASE_CANDIDATE_FILENAMES:
        located = find_file(runtime.project_root, pattern.format(cf=runtime.confronto_id))
        if located is not None:
            return located.resolve()
    return None


def load_source_bundle(runtime: RuntimeConfig) -> SourceBundle:
    data: dict[str, Any] = {}
    paths: dict[str, Path] = {}
    warnings: list[str] = []
    optional_missing: list[str] = []

    for key, spec in FILE_REQUIREMENTS.items():
        located = find_file(runtime.project_root, spec["name"])
        if located is None:
            if spec.get("required", False):
                raise MissingRequiredSourceError(f"Ficheiro obrigatório não encontrado: {spec['name']}")
            optional_missing.append(spec["name"])
            continue
        paths[key] = located.resolve()
        if located.suffix.lower() == ".json":
            data[key] = read_json(located)
        else:
            data[key] = read_text(located)

    paths["dossier"] = runtime.dossier_path
    data["dossier"] = read_text(runtime.dossier_path)

    if runtime.config_path is not None:
        paths["config_current"] = runtime.config_path
        data["config_current"] = read_json(runtime.config_path)

    base_fragment_path = _resolve_base_fragment_path(runtime)
    if base_fragment_path is not None:
        paths["base_fragmentaria"] = base_fragment_path
        data["base_fragmentaria"] = read_json(base_fragment_path)
    else:
        warnings.append("Base fragmentária específica não encontrada; será usado universo global resegmentado com filtragem disciplinada por scoring.")

    for pattern in OPTIONAL_CURRENT_DIAGNOSTIC_PATTERNS:
        located = find_file(runtime.project_root, pattern.format(cf=runtime.confronto_id))
        if located is not None:
            key = f"diagnostic::{located.name}"
            paths[key] = located.resolve()
            data[key] = read_json(located) if located.suffix.lower() == ".json" else read_text(located)

    return SourceBundle(data=data, paths=paths, warnings=warnings, optional_missing=optional_missing)


# =============================================================================
# CONSTRUÇÃO DOS ÍNDICES NORMATIVOS
# =============================================================================


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _flatten_structural_ids(payload: Any, prefix: str) -> list[str]:
    out: list[str] = []
    if isinstance(payload, dict):
        for key, val in payload.items():
            if isinstance(key, str) and key.startswith(prefix):
                out.append(key)
            out.extend(_flatten_structural_ids(val, prefix))
    elif isinstance(payload, list):
        for item in payload:
            out.extend(_flatten_structural_ids(item, prefix))
    elif isinstance(payload, str) and payload.startswith(prefix):
        out.append(payload)
    return dedupe_preserve_order(out)


def _collect_proposition_catalogs(bundle: SourceBundle) -> tuple[set[str], dict[str, list[str]]]:
    proposition_ids: set[str] = set()
    proposition_dependencies: dict[str, list[str]] = {}

    enriched = _safe_dict(bundle.data.get("proposicoes_nucleares_enriquecidas"))
    for item in _safe_list(enriched.get("proposicoes")):
        pid = _safe_str(item.get("proposicao_id"))
        if not pid:
            continue
        proposition_ids.add(pid)
        deps = _safe_dict(item.get("dependencias"))
        proposition_dependencies[pid] = dedupe_preserve_order(
            [dep for dep in _safe_list(deps.get("dependencias_anteriores")) if isinstance(dep, str) and dep.startswith("P")]
        )

    matrix_payload = _safe_dict(bundle.data.get("matriz_confronto"))
    for item in _safe_list(matrix_payload.get("confrontos")):
        for pid in _safe_list(item.get("proposicao_ids")):
            if isinstance(pid, str) and re.fullmatch(STRICT_ID_PATTERNS["proposicao"], pid):
                proposition_ids.add(pid)

    adj_payload = _safe_dict(bundle.data.get("adjudicacao_confrontos"))
    for item in _safe_list(adj_payload.get("confrontos")):
        for pid in _safe_list(item.get("proposicao_ids")):
            if isinstance(pid, str) and re.fullmatch(STRICT_ID_PATTERNS["proposicao"], pid):
                proposition_ids.add(pid)

    mapa_final = _safe_dict(bundle.data.get("mapa_dedutivo_final"))
    for bloco in _safe_list(mapa_final.get("blocos")):
        for prop in _safe_list(bloco.get("proposicoes")):
            pid = _safe_str(prop.get("id")) or _safe_str(prop.get("proposicao_id")) or _safe_str(prop.get("passo_id"))
            if pid and re.fullmatch(STRICT_ID_PATTERNS["proposicao"], pid):
                proposition_ids.add(pid)
                proposition_dependencies.setdefault(pid, [dep for dep in _safe_list(prop.get("depende_de")) if isinstance(dep, str) and dep.startswith("P")])

    proposition_dependencies = {k: dedupe_preserve_order(v) for k, v in proposition_dependencies.items()}
    return proposition_ids, proposition_dependencies


def _extract_argument_mappings(bundle: SourceBundle) -> tuple[set[str], dict[str, list[str]], dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
    argument_ids: set[str] = set()
    argument_to_operations: dict[str, list[str]] = {}
    argument_to_regimes: dict[str, list[str]] = {}
    argument_to_paths: dict[str, list[str]] = {}
    argument_to_chapters: dict[str, list[str]] = {}

    argumentos = _safe_list(bundle.data.get("argumentos_unificados"))
    for item in argumentos:
        arg_id = _safe_str(item.get("id")) or _safe_str(item.get("argumento_id"))
        if not arg_id:
            continue
        argument_ids.add(arg_id)
        argument_to_operations[arg_id] = dedupe_preserve_order([op for op in _safe_list(item.get("operacoes_chave")) if isinstance(op, str)])
        fundamenta = _safe_dict(item.get("fundamenta"))
        argument_to_regimes[arg_id] = dedupe_preserve_order([reg for reg in _safe_list(fundamenta.get("regimes")) if isinstance(reg, str)])
        argument_to_paths[arg_id] = dedupe_preserve_order([pid for pid in _safe_list(fundamenta.get("percursos")) if isinstance(pid, str)])
        chapter = _safe_str(item.get("capitulo"))
        argument_to_chapters[arg_id] = [chapter] if chapter else []

    mapa_integral = _safe_dict(bundle.data.get("mapa_integral_do_indice"))
    for chapter in _safe_list(mapa_integral.get("capitulos")):
        chapter_id = _safe_str(chapter.get("capitulo_id")) or _safe_str(chapter.get("id"))
        for arg in _safe_list(chapter.get("argumentos_canonicos")):
            arg_id = _safe_str(arg.get("argumento_id")) or _safe_str(arg.get("id"))
            if not arg_id:
                continue
            argument_ids.add(arg_id)
            if chapter_id:
                argument_to_chapters.setdefault(arg_id, [])
                argument_to_chapters[arg_id] = dedupe_preserve_order(argument_to_chapters[arg_id] + [chapter_id])
            argument_to_operations.setdefault(arg_id, [])
            argument_to_operations[arg_id] = dedupe_preserve_order(argument_to_operations[arg_id] + [op for op in _safe_list(arg.get("operacoes_chave")) if isinstance(op, str)])
            fund = _safe_list(arg.get("fundamenta"))
            for item_fund in fund:
                if isinstance(item_fund, dict):
                    argument_to_regimes.setdefault(arg_id, [])
                    argument_to_paths.setdefault(arg_id, [])
                    argument_to_regimes[arg_id] = dedupe_preserve_order(argument_to_regimes[arg_id] + [reg for reg in _safe_list(item_fund.get("regimes")) if isinstance(reg, str)])
                    argument_to_paths[arg_id] = dedupe_preserve_order(argument_to_paths[arg_id] + [pid for pid in _safe_list(item_fund.get("percursos")) if isinstance(pid, str)])
    return argument_ids, argument_to_operations, argument_to_regimes, argument_to_paths, argument_to_chapters


def _extract_ramo_argument_map(bundle: SourceBundle) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    payload = _safe_dict(bundle.data.get("adjudicacao_argumentos_api"))
    for item in _safe_list(payload.get("ramos_adjudicados")):
        ramo_id = _safe_str(item.get("ramo_id"))
        if not ramo_id:
            continue
        args = _safe_list(item.get("argumentos_mantidos")) or _safe_list(item.get("candidatos_iniciais"))
        out[ramo_id] = dedupe_preserve_order([arg for arg in args if isinstance(arg, str)])
    return out


def build_normative_indices(runtime: RuntimeConfig, bundle: SourceBundle) -> NormativeIndices:
    proposition_ids, proposition_dependencies = _collect_proposition_catalogs(bundle)

    chapter_ids: set[str] = set()
    regime_ids: set[str] = set()
    path_ids: set[str] = set()
    path_to_type: dict[str, str] = {}
    path_to_required_paths: dict[str, list[str]] = {}
    chapter_to_regimes: dict[str, list[str]] = {}
    chapter_to_paths: dict[str, list[str]] = {}
    chapter_to_operations: dict[str, list[str]] = {}

    indice_seq = _safe_dict(bundle.data.get("indice_sequencial"))
    for cap in _safe_list(indice_seq.get("capitulos")):
        cap_id = _safe_str(cap.get("id")) or _safe_str(cap.get("capitulo_id"))
        if not cap_id:
            continue
        chapter_ids.add(cap_id)
        regs = [_safe_str(cap.get("regime_principal"))] + [r for r in _safe_list(cap.get("regimes_secundarios")) if isinstance(r, str)]
        regs = dedupe_preserve_order([r for r in regs if r])
        paths = [normalize_path_id(_safe_str(cap.get("percurso_axial")))] + [normalize_path_id(p) for p in _safe_list(cap.get("percursos_participantes")) if isinstance(p, str)]
        paths = dedupe_preserve_order([p for p in paths if p])
        regime_ids.update(regs)
        path_ids.update(paths)
        chapter_to_regimes[cap_id] = regs
        chapter_to_paths[cap_id] = paths

    mapa_integral = _safe_dict(bundle.data.get("mapa_integral_do_indice"))
    for cap in _safe_list(mapa_integral.get("capitulos")):
        cap_id = _safe_str(cap.get("capitulo_id")) or _safe_str(cap.get("id"))
        if not cap_id:
            continue
        chapter_ids.add(cap_id)
        regs = [_safe_str(cap.get("regime_principal"))] + [r for r in _safe_list(cap.get("regimes_secundarios")) if isinstance(r, str)]
        regs = [r for r in regs if r]
        paths = [normalize_path_id(_safe_str(cap.get("percurso_axial")))] + [normalize_path_id(p) for p in _safe_list(cap.get("percursos_participantes")) if isinstance(p, str)]
        paths = [p for p in paths if p]
        chapter_to_regimes[cap_id] = dedupe_preserve_order(chapter_to_regimes.get(cap_id, []) + regs)
        chapter_to_paths[cap_id] = dedupe_preserve_order(chapter_to_paths.get(cap_id, []) + paths)
        ops: list[str] = []
        for arg in _safe_list(cap.get("argumentos_canonicos")):
            ops.extend(op for op in _safe_list(arg.get("operacoes_chave")) if isinstance(op, str))
        chapter_to_operations[cap_id] = dedupe_preserve_order(chapter_to_operations.get(cap_id, []) + ops)
        regime_ids.update(chapter_to_regimes[cap_id])
        path_ids.update(chapter_to_paths[cap_id])

    meta_ref = _safe_dict(bundle.data.get("meta_referencia_do_percurso"))
    for raw_path_id, meta in meta_ref.items():
        if not isinstance(raw_path_id, str):
            continue
        path_id = normalize_path_id(raw_path_id)
        path_ids.add(path_id)
        ptype = normalize_path_type(_safe_str(_safe_dict(meta).get("tipo_instancia")))
        path_to_type[path_id] = ptype or "unknown"
        path_to_required_paths[path_id] = dedupe_preserve_order(
            [normalize_path_id(p) for p in _safe_list(_safe_dict(meta).get("pressupoe_percursos")) if isinstance(p, str)]
        )

    # Índice por percurso pode trazer aliases úteis de ID e tipo.
    indice_percursos = _safe_dict(bundle.data.get("indice_de_percursos"))
    for maybe_type, ids in indice_percursos.items():
        if not isinstance(maybe_type, str):
            continue
        for pid in _safe_list(ids):
            if not isinstance(pid, str):
                continue
            path_id = normalize_path_id(pid)
            path_ids.add(path_id)
            path_to_type.setdefault(path_id, normalize_path_type(maybe_type))
            if path_id == "P_TRANSICAO_ANTROPOLOGICA_ONTOLOGICA":
                path_ids.add("P_TRANSICAO_ANTROPOLOGIA_ONTOLOGICA")

    meta_indice = _safe_dict(bundle.data.get("meta_indice"))
    meta_regimes = _safe_dict(_safe_dict(meta_indice.get("meta_indice")).get("regimes"))
    regime_ids.update([rid for rid in meta_regimes.keys() if isinstance(rid, str)])
    operacoes = _safe_dict(bundle.data.get("operacoes"))
    operation_ids = set(k for k in operacoes.keys() if isinstance(k, str))

    argument_ids, argument_to_operations, argument_to_regimes, argument_to_paths, argument_to_chapters = _extract_argument_mappings(bundle)
    # Fonte API é apenas auxiliar: nunca soberana para povoamento central.
    ramo_to_arguments: dict[str, list[str]] = {}

    proposition_to_chapters: dict[str, list[str]] = {pid: [] for pid in proposition_ids}
    proposition_to_regimes: dict[str, list[str]] = {pid: [] for pid in proposition_ids}
    proposition_to_paths: dict[str, list[str]] = {pid: [] for pid in proposition_ids}
    proposition_to_arguments: dict[str, list[str]] = {pid: [] for pid in proposition_ids}
    proposition_to_operations: dict[str, list[str]] = {pid: [] for pid in proposition_ids}

    enriched = _safe_dict(bundle.data.get("proposicoes_nucleares_enriquecidas"))
    for item in _safe_list(enriched.get("proposicoes")):
        pid = _safe_str(item.get("proposicao_id"))
        if not pid or pid not in proposition_ids:
            continue
        arch = _safe_dict(item.get("arquitetura_origem"))
        proposition_to_paths[pid] = dedupe_preserve_order([normalize_path_id(p) for p in _safe_list(arch.get("percurso_ids")) if isinstance(p, str)])
        proposition_to_arguments[pid] = dedupe_preserve_order([a for a in _safe_list(arch.get("argumento_ids")) if isinstance(a, str)])
        # capítulos e operações podem derivar dos argumentos locais da arquitetura de origem.
        for arg in proposition_to_arguments[pid]:
            proposition_to_operations[pid] = dedupe_preserve_order(proposition_to_operations[pid] + argument_to_operations.get(arg, []))
            proposition_to_chapters[pid] = dedupe_preserve_order(proposition_to_chapters[pid] + argument_to_chapters.get(arg, []))
            proposition_to_regimes[pid] = dedupe_preserve_order(proposition_to_regimes[pid] + argument_to_regimes.get(arg, []))
        regs = [r for r in _safe_list(item.get("regimes_de_validacao")) if isinstance(r, str)]
        proposition_to_regimes[pid] = dedupe_preserve_order(proposition_to_regimes[pid] + regs)

    matrix_payload = _safe_dict(bundle.data.get("matriz_confronto"))
    bridge_ids = set(_flatten_structural_ids(matrix_payload, "PN"))
    anchorage_ids = set(_flatten_structural_ids(matrix_payload, "AC"))
    field_ids = set(_flatten_structural_ids(matrix_payload, "CR"))
    cf_ids = set(_flatten_structural_ids(matrix_payload, "CF"))
    matrix_by_cf: dict[str, dict[str, Any]] = {}
    for item in _safe_list(matrix_payload.get("confrontos")):
        cf = _safe_str(item.get("confronto_id"))
        if not cf:
            continue
        matrix_by_cf[cf] = item
        cf_ids.add(cf)
        bridge_ids.update([x for x in _safe_list(item.get("ponte_ids_relacionadas")) if isinstance(x, str)])
        anchorage_ids.update([x for x in _safe_list(item.get("ancoragem_ids_relacionadas")) if isinstance(x, str)])
        field_ids.update([x for x in _safe_list(item.get("campo_ids_relacionados")) if isinstance(x, str)])

    adjudication_by_cf: dict[str, dict[str, Any]] = {}
    adj_payload = _safe_dict(bundle.data.get("adjudicacao_confrontos"))
    for item in _safe_list(adj_payload.get("confrontos")):
        cf = _safe_str(item.get("confronto_id"))
        if cf:
            adjudication_by_cf[cf] = item
            cf_ids.add(cf)

    warnings: list[str] = []
    if "P_TRANSICAO_ANTROPOLOGIA_ONTOLOGICA" in path_ids and "P_TRANSICAO_ANTROPOLOGICA_ONTOLOGICA" in path_ids:
        warnings.append("Alias de percurso normalizado: P_TRANSICAO_ANTROPOLOGIA_ONTOLOGICA -> P_TRANSICAO_ANTROPOLOGICA_ONTOLOGICA")

    return NormativeIndices(
        proposition_ids=proposition_ids,
        bridge_ids=bridge_ids,
        anchorage_ids=anchorage_ids,
        field_ids=field_ids,
        chapter_ids=chapter_ids,
        regime_ids=regime_ids,
        path_ids=path_ids,
        argument_ids=argument_ids,
        cf_ids=cf_ids,
        proposition_to_chapters={k: dedupe_preserve_order(v) for k, v in proposition_to_chapters.items()},
        proposition_to_regimes={k: dedupe_preserve_order(v) for k, v in proposition_to_regimes.items()},
        proposition_to_paths={k: dedupe_preserve_order([normalize_path_id(x) for x in v]) for k, v in proposition_to_paths.items()},
        proposition_to_arguments={k: dedupe_preserve_order(v) for k, v in proposition_to_arguments.items()},
        proposition_to_operations={k: dedupe_preserve_order([op for op in v if op in operation_ids]) for k, v in proposition_to_operations.items()},
        proposition_dependencies=proposition_dependencies,
        chapter_to_regimes={k: dedupe_preserve_order(v) for k, v in chapter_to_regimes.items()},
        chapter_to_paths={k: dedupe_preserve_order([normalize_path_id(x) for x in v]) for k, v in chapter_to_paths.items()},
        chapter_to_operations={k: dedupe_preserve_order([op for op in v if op in operation_ids]) for k, v in chapter_to_operations.items()},
        argument_to_operations={k: dedupe_preserve_order([op for op in v if op in operation_ids]) for k, v in argument_to_operations.items()},
        argument_to_regimes={k: dedupe_preserve_order(v) for k, v in argument_to_regimes.items()},
        argument_to_paths={k: dedupe_preserve_order([normalize_path_id(x) for x in v]) for k, v in argument_to_paths.items()},
        argument_to_chapters={k: dedupe_preserve_order(v) for k, v in argument_to_chapters.items()},
        path_to_type=path_to_type,
        path_to_required_paths={k: dedupe_preserve_order([normalize_path_id(x) for x in v]) for k, v in path_to_required_paths.items()},
        corridors=CORRIDOR_DEFINITIONS,
        matrix_by_cf=matrix_by_cf,
        adjudication_by_cf=adjudication_by_cf,
        cf_neighbor_map=dict(DEFAULT_NEIGHBOR_DOSSIERS),
        cf_sensitive_corridors=dict(DEFAULT_SENSITIVE_CORRIDORS),
        cf_altitude_expectation=dict(DEFAULT_ALTITUDE_EXPECTATION),
        cf_autonomy_expectation=dict(DEFAULT_AUTONOMY_EXPECTATION),
        ramo_to_arguments=ramo_to_arguments,
        warnings=warnings,
    )


# =============================================================================
# PARSING ESTRUTURAL DO DOSSIER
# =============================================================================


def read_dossier_text(runtime: RuntimeConfig) -> str:
    return read_text(runtime.dossier_path)


def _section_role(section: MarkdownSection) -> str:
    heading = normalize_text(section.heading)
    if any(phrase in heading for phrase in (
        "nucleo efetivamente dominante", "núcleo efetivamente dominante", "nucleo filosofico efetivo",
        "núcleo filosófico efetivo", "proposicoes nucleares", "proposições nucleares",
        "nucleares primarias", "nucleares primárias", "nucleares centrais", "nucleo primario",
        "núcleo primário", "eixo 1", "eixo 2", "eixo 3", "eixo 4", "eixo 5",
    )):
        return "strong"
    if any(phrase in heading for phrase in (
        "solo ontologico", "solo ontológico", "solo de fundo", "fundo", "laterais mas relevantes",
        "laterais", "nucleares secundarias", "nucleares secundárias", "secundarias de fecho",
        "secundárias de fecho", "prolongamentos", "vizinhanca arquitetonica", "vizinhança arquitetónica",
    )):
        return "background"
    if any(phrase in heading for phrase in (
        "a descentrar", "descentrar", "descentradas", "tese negativa", "o que o dossier rejeita", "rejeita expressamente", "rejeita",
    )):
        return "rejected"
    if fuzzy_heading_key(section.heading) == "proposicoes_envolvidas":
        return "declared"
    return "other"


def _extract_validated_ids_from_section_text(
    text: str,
    id_kind: str,
    catalog: set[str],
    invalid_token_sink: set[str],
    warning_sink: list[str],
) -> list[str]:
    pattern = re.compile(STRICT_ID_PATTERNS[id_kind])
    valid_ids: list[str] = []
    for token in BROAD_TOKEN_PATTERN.findall(text or ""):
        cleaned = token.strip("*`.,;:()[]{}<>\"'")
        parts = [part for part in re.split(r"[\-/]", cleaned) if part]
        for part in parts:
            if pattern.fullmatch(part) and part in catalog:
                valid_ids.append(part)
                continue
            starts_relevant = (
                (id_kind == "proposicao" and bool(re.match(r"^P\d", part)))
                or (id_kind == "ponte" and part.startswith("PN"))
                or (id_kind == "ancoragem" and part.startswith("AC"))
                or (id_kind == "campo" and part.startswith("CR"))
                or (id_kind == "capitulo" and part.startswith("CAP_"))
                or (id_kind == "regime" and part.startswith("REGIME_"))
                or (id_kind == "percurso" and part.startswith("P_"))
                or (id_kind == "argumento" and part.startswith("ARG_"))
            )
            looks_like_structural_token = starts_relevant or part in CURRENT_BUG_GUARD_TOKENS or ("_" in part and len(part) >= 3)
            if looks_like_structural_token and part not in catalog and part.lower() not in STOPWORDS:
                invalid_token_sink.add(part)
    if invalid_token_sink:
        warning_sink.append(f"Foram detetados tokens inválidos ao extrair {id_kind}: {', '.join(sorted(invalid_token_sink))}")
    return dedupe_preserve_order(valid_ids)


def _classify_redecision(text: str) -> tuple[DecisionRedecisionClass, list[str]]:
    normalized = normalize_text(text)
    evidence: list[str] = []
    if any(phrase in normalized for phrase in (
        "equivalente a novo dossier",
        "desalinhamento forte",
        "reformulacao estrutural profunda",
        "reformulação estrutural profunda",
        "substituido por reformulacao estrutural profunda",
        "substituição integral do dossier anterior",
        "substituicao integral do dossier anterior",
        "funcao substituir operacionalmente",
        "função substituir operacionalmente",
    )):
        evidence.append("redecisão estrutural explícita")
        return DecisionRedecisionClass.structural_substitution, evidence
    if any(phrase in normalized for phrase in (
        "recentrado", "recentrando", "recentrar", "desloca se para", "desloca-se para", "ja nao deve ser formulado", "já não deve ser formulado"
    )):
        evidence.append("recentramento forte explícito")
        return DecisionRedecisionClass.deep_recenter, evidence
    if any(phrase in normalized for phrase in ("ajuste", "ajuste metodologico", "ajuste metodológico", "afinado", "afinar")):
        evidence.append("ajuste metodológico explícito")
        return DecisionRedecisionClass.soft_recenter, evidence
    return DecisionRedecisionClass.none, evidence


def _extract_config_defaults(config_payload: dict[str, Any], indices: NormativeIndices) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for key in (
        "declared_profiles_expected", "competing_profiles", "neighbor_dossiers", "sensitive_corridors",
        "declared_capitulos_expected", "declared_regimes_expected", "altitude_expectation", "autonomy_expectation",
    ):
        if key in config_payload:
            defaults[key] = config_payload[key]
    if isinstance(defaults.get("neighbor_dossiers"), list):
        indices.cf_neighbor_map.setdefault(config_payload.get("confronto_id", ""), defaults["neighbor_dossiers"])
    return defaults


def parse_declared_dossier_state(
    runtime: RuntimeConfig,
    dossier_text: str,
    bundle: SourceBundle,
    indices: NormativeIndices,
) -> DeclaredDossierState:
    sections = parse_markdown_sections(dossier_text)
    invalid_tokens: set[str] = set()
    warnings: list[str] = []
    question_central = ""
    descricao = ""
    tese = ""
    title = sections[0].heading if sections else runtime.confronto_id

    propositions_all: list[str] = []
    propositions_strong: list[str] = []
    propositions_background: list[str] = []
    propositions_rejected: list[str] = []
    bridges: list[str] = []
    anchorages: list[str] = []
    fields: list[str] = []
    chapters: list[str] = []
    regimes: list[str] = []
    paths: list[str] = []
    arguments: list[str] = []
    trace: list[dict[str, Any]] = []

    for section in sections:
        key = fuzzy_heading_key(section.heading)
        role = _section_role(section)
        trace.append({"index": section.index, "level": section.level, "heading": section.heading, "key": key, "role": role})
        body = section.body

        if key == "pergunta_central" and body and not question_central:
            question_central = normalize_spaces(body)
        elif key == "descricao_confronto" and body and not descricao:
            descricao = normalize_spaces(body)
        elif key == "tese_canonica_provisoria" and body and not tese:
            tese = normalize_spaces(body)

        # Proposições só podem ser extraídas de secções proposicionais reais ou de subsecções com papel explícito.
        if key == "proposicoes_envolvidas" or role in {"strong", "background", "rejected"}:
            prop_window = body.split("\n\n", 1)[0] if role in {"strong", "background", "rejected"} else body
            pids = _extract_validated_ids_from_section_text(prop_window, "proposicao", indices.proposition_ids, invalid_tokens, warnings)
            if pids:
                propositions_all.extend(pids)
                if role == "strong":
                    propositions_strong.extend(pids)
                elif role == "background":
                    propositions_background.extend(pids)
                elif role == "rejected":
                    propositions_rejected.extend(pids)
                else:
                    propositions_all.extend([])

        if key in {"pontes", "articulacao_estrutural"}:
            bridges.extend(_extract_validated_ids_from_section_text(body, "ponte", indices.bridge_ids, invalid_tokens, warnings))
        if key in {"ancoragens", "articulacao_estrutural"}:
            anchorages.extend(_extract_validated_ids_from_section_text(body, "ancoragem", indices.anchorage_ids, invalid_tokens, warnings))
        if key in {"campos_do_real", "articulacao_estrutural"}:
            fields.extend(_extract_validated_ids_from_section_text(body, "campo", indices.field_ids, invalid_tokens, warnings))
        if key in {"estatuto_arquitetonico", "articulacao_estrutural"}:
            chapters.extend(_extract_validated_ids_from_section_text(body, "capitulo", indices.chapter_ids, invalid_tokens, warnings))
            regimes.extend(_extract_validated_ids_from_section_text(body, "regime", indices.regime_ids, invalid_tokens, warnings))
            paths.extend(_extract_validated_ids_from_section_text(body, "percurso", indices.path_ids, invalid_tokens, warnings))
            arguments.extend(_extract_validated_ids_from_section_text(body, "argumento", indices.argument_ids, invalid_tokens, warnings))

    nota_text = "\n\n".join(
        section.body for section in sections if fuzzy_heading_key(section.heading) in {"nota_previa", "estatuto_arquitetonico", "articulacao_estrutural", "decisao"}
    )
    redecision_class, redecision_evidence = _classify_redecision(nota_text or dossier_text)

    config_defaults: dict[str, Any] = {}
    if "config_current" in bundle.data:
        config_defaults = _extract_config_defaults(_safe_dict(bundle.data["config_current"]), indices)
        chapters.extend([cid for cid in _safe_list(config_defaults.get("declared_capitulos_expected")) if isinstance(cid, str) and cid in indices.chapter_ids])
        regimes.extend([rid for rid in _safe_list(config_defaults.get("declared_regimes_expected")) if isinstance(rid, str) and rid in indices.regime_ids])
        paths.extend([normalize_path_id(pid) for pid in _safe_list(config_defaults.get("declared_percursos_expected")) if isinstance(pid, str)])
        if isinstance(config_defaults.get("neighbor_dossiers"), list):
            indices.cf_neighbor_map[runtime.confronto_id] = [x for x in config_defaults["neighbor_dossiers"] if isinstance(x, str)]
        if isinstance(config_defaults.get("sensitive_corridors"), list):
            indices.cf_sensitive_corridors[runtime.confronto_id] = [x for x in config_defaults["sensitive_corridors"] if isinstance(x, str)]
        if isinstance(config_defaults.get("altitude_expectation"), str):
            indices.cf_altitude_expectation[runtime.confronto_id] = config_defaults["altitude_expectation"]
        if isinstance(config_defaults.get("autonomy_expectation"), str):
            indices.cf_autonomy_expectation[runtime.confronto_id] = config_defaults["autonomy_expectation"]

    if not question_central:
        question_central = _safe_str(_safe_dict(indices.matrix_by_cf.get(runtime.confronto_id)).get("pergunta_central"))
    if not descricao:
        descricao = _safe_str(_safe_dict(indices.matrix_by_cf.get(runtime.confronto_id)).get("descricao_do_confronto"))
    if not tese:
        adj = _safe_dict(indices.adjudication_by_cf.get(runtime.confronto_id))
        tese = _safe_str(_safe_dict(adj.get("adjudicacao_filosofica_restrita")).get("tese_central_adjudicada")) or _safe_str(_safe_dict(adj.get("adjudicacao_filosofica")).get("tese_central_adjudicada"))

    # Pós-processamento local: distinguir fundo e rejeição quando a própria frase o explicita dentro de secções nucleares.
    for match in re.finditer(r"\bcom\s+((?:P\d{2,4}(?:\s*(?:,|/|e)\s*P\d{2,4})*))\s+como\s+(?:solo de fundo|pano de fundo|fundo)", dossier_text, flags=re.I):
        ids_here = _extract_validated_ids_from_section_text(match.group(1), "proposicao", indices.proposition_ids, set(), [])
        propositions_background.extend(ids_here)
    for match in re.finditer(r"((?:P\d{2,4}(?:\s*(?:,|/|e)\s*P\d{2,4})*))\s+devem\s+deixar\s+de\s+funcionar", dossier_text, flags=re.I):
        ids_here = _extract_validated_ids_from_section_text(match.group(1), "proposicao", indices.proposition_ids, set(), [])
        propositions_rejected.extend(ids_here)

    propositions_rejected = dedupe_preserve_order(propositions_rejected)
    propositions_background = dedupe_preserve_order([pid for pid in propositions_background if pid not in propositions_rejected])
    propositions_strong = dedupe_preserve_order([pid for pid in propositions_strong if pid not in propositions_background and pid not in propositions_rejected])
    propositions_all = dedupe_preserve_order(propositions_strong + propositions_background + propositions_rejected + propositions_all)
    chapters = dedupe_preserve_order(chapters)
    regimes = dedupe_preserve_order(regimes)
    paths = dedupe_preserve_order([normalize_path_id(pid) for pid in paths if pid in indices.path_ids])
    arguments = dedupe_preserve_order(arguments)
    declared_profiles = [p for p in _safe_list(config_defaults.get("declared_profiles_expected")) if isinstance(p, str)]

    return DeclaredDossierState(
        confronto_id=runtime.confronto_id,
        dossier_title=title,
        question_central=question_central,
        descricao_do_confronto=descricao,
        tese_canonica_provisoria=tese,
        proposicoes_envolvidas=propositions_all,
        proposicoes_nucleares_centrais=dedupe_preserve_order(propositions_strong),
        proposicoes_background=propositions_background,
        proposicoes_rejeitadas=propositions_rejected,
        pontes=dedupe_preserve_order(bridges),
        ancoragens=dedupe_preserve_order(anchorages),
        campos_do_real=dedupe_preserve_order(fields),
        capitulos=chapters,
        regimes=regimes,
        percursos=paths,
        argumentos=arguments,
        declared_profiles=declared_profiles,
        invalid_id_tokens=sorted(invalid_tokens),
        parsing_warnings=dedupe_preserve_order(warnings),
        redecision_class=redecision_class,
        redecision_evidence=redecision_evidence,
        config_defaults=config_defaults,
        section_trace=trace,
    )


# =============================================================================
# CARREGAMENTO E ENRIQUECIMENTO FRAGMENTÁRIO
# =============================================================================


def _collect_fragment_items(tree_payload: Any) -> list[dict[str, Any]]:
    if isinstance(tree_payload, dict) and isinstance(tree_payload.get("fragmentos"), list):
        return [item for item in tree_payload["fragmentos"] if isinstance(item, dict)]
    if isinstance(tree_payload, list):
        return [item for item in tree_payload if isinstance(item, dict)]
    return []


def _fragment_text(item: dict[str, Any]) -> str:
    return normalize_spaces(
        _safe_str(_safe_dict(item.get("base_empirica")).get("texto_fragmento"))
        or _safe_str(item.get("texto"))
        or _safe_str(item.get("texto_fragmento"))
    )


def _fragment_id(item: dict[str, Any]) -> str:
    return _safe_str(item.get("fragment_id")) or _safe_str(item.get("id")) or _safe_str(item.get("fragmento_id"))


def _relevance_to_weight(text: str) -> float:
    return {"alto": 1.00, "alta": 1.00, "medio": 0.68, "médio": 0.68, "media": 0.68, "baixo": 0.36, "baixa": 0.36}.get(normalize_text(text), 0.45)


def _relation_boost(text: str) -> float:
    normalized = normalize_text(text)
    if "apoia_justificacao" in normalized or "apoia justificacao" in normalized:
        return 1.00
    if "faz_ponte_entre" in normalized:
        return 0.78
    if "introduz_distincao_nova" in normalized:
        return 0.88
    if "bloqueia_objecao" in normalized:
        return 0.82
    if "toca_indiretamente" in normalized:
        return 0.42
    return 0.60


def _extract_fragment_proposition_weights(item: dict[str, Any], proposition_catalog: set[str]) -> dict[str, float]:
    weights: Counter[str] = Counter()
    impacto = _safe_dict(item.get("impacto_mapa"))
    touched = _safe_list(_safe_dict(impacto).get("proposicoes_do_mapa_tocadas"))
    if not touched and "impacto_no_mapa_fragmento" in item:
        touched = _safe_list(_safe_dict(_safe_dict(item.get("impacto_no_mapa_fragmento")).get("impacto_no_mapa_fragmento", item.get("impacto_no_mapa_fragmento"))).get("proposicoes_do_mapa_tocadas"))
    if not touched and "impacto_no_mapa_fragmento" in item:
        touched = _safe_list(_safe_dict(item.get("impacto_no_mapa_fragmento")).get("proposicoes_do_mapa_tocadas"))
    for rel in touched:
        if not isinstance(rel, dict):
            continue
        pid = _safe_str(rel.get("proposicao_id"))
        if pid and pid in proposition_catalog:
            weights[pid] += _relevance_to_weight(_safe_str(rel.get("grau_de_relevancia"))) * _relation_boost(_safe_str(rel.get("tipo_de_relacao")))
    return {k: round(v, 6) for k, v in weights.items()}


def _merge_external_impact_weights(item: FragmentRecord, impact_by_fragment: dict[str, dict[str, Any]]) -> FragmentRecord:
    impact_item = impact_by_fragment.get(item.fragment_id)
    if not impact_item:
        return item
    weights = Counter(item.proposition_weights)
    touched = _safe_list(_safe_dict(_safe_dict(impact_item).get("impacto_no_mapa_fragmento")).get("proposicoes_do_mapa_tocadas"))
    for rel in touched:
        if isinstance(rel, dict):
            pid = _safe_str(rel.get("proposicao_id"))
            if pid:
                weights[pid] += _relevance_to_weight(_safe_str(rel.get("grau_de_relevancia"))) * _relation_boost(_safe_str(rel.get("tipo_de_relacao"))) * 0.70
    item.proposition_weights = {k: round(v, 6) for k, v in weights.items()}
    item.proposition_ids = dedupe_preserve_order(list(item.proposition_weights.keys()))
    payload = _safe_dict(_safe_dict(impact_item).get("impacto_no_mapa_fragmento"))
    item.impact_effect = _safe_str(payload.get("efeito_principal_no_mapa")) or item.impact_effect
    final_dec = _safe_dict(payload.get("decisao_final"))
    item.impact_action = _safe_str(final_dec.get("acao_recomendada_sobre_o_mapa")) or item.impact_action
    item.impact_priority = _safe_str(final_dec.get("prioridade_editorial")) or item.impact_priority
    return item


def _fallback_fragment_source(bundle: SourceBundle) -> list[dict[str, Any]]:
    source = _safe_list(bundle.data.get("fragmentos_resegmentados"))
    if source:
        return [item for item in source if isinstance(item, dict)]
    source = _collect_fragment_items(bundle.data.get("base_fragmentaria"))
    if source:
        return source
    upper = _collect_fragment_items(bundle.data.get("arvore_fecho_superior"))
    if upper:
        return upper
    lower = _collect_fragment_items(bundle.data.get("arvore_v1"))
    if lower:
        return lower
    raise FragmentBaseError("Não foi possível obter fragmentos nem de fragmentos_resegmentados nem da árvore do pensamento.")


def load_fragment_records(runtime: RuntimeConfig, bundle: SourceBundle, indices: NormativeIndices) -> list[FragmentRecord]:
    raw_items = _fallback_fragment_source(bundle)
    if not raw_items:
        raise FragmentBaseError("Nenhum fragmento utilizável foi carregado.")

    tree_items = _collect_fragment_items(bundle.data.get("arvore_fecho_superior")) or _collect_fragment_items(bundle.data.get("arvore_v1"))
    tree_by_id = {_fragment_id(item): item for item in tree_items if _fragment_id(item)}

    impact_payload = bundle.data.get("impacto_fragmentos_no_mapa")
    impact_by_fragment: dict[str, dict[str, Any]] = {}
    if isinstance(impact_payload, list):
        for item in impact_payload:
            if isinstance(item, dict):
                fid = _safe_str(item.get("fragment_id")) or _safe_str(item.get("id"))
                if fid:
                    impact_by_fragment[fid] = item

    base_scope_ids = _extract_base_fragment_scope_ids(bundle.data.get("base_fragmentaria"))
    records: list[FragmentRecord] = []
    source_mode = "fragmentos_resegmentados" if "fragmentos_resegmentados" in bundle.paths else ("base_fragmentaria" if base_scope_ids else "fallback_arvore")

    for item in raw_items:
        fragment_id = _safe_str(item.get("fragment_id")) or _safe_str(item.get("id")) or _safe_str(item.get("fragmento_id"))
        if not fragment_id:
            continue
        if base_scope_ids and fragment_id not in base_scope_ids:
            continue

        tree_item = tree_by_id.get(fragment_id, {})
        lig = _safe_dict(tree_item.get("ligacoes_arvore"))
        cad = _safe_dict(tree_item.get("cadencia"))
        impacto_tree = _safe_dict(tree_item.get("impacto_mapa"))
        impact_external = impact_by_fragment.get(fragment_id, {})
        impact_payload_item = _safe_dict(impact_external.get("impacto_no_mapa_fragmento"))
        tratamento = _safe_dict(tree_item.get("tratamento_filosofico"))
        origem = _safe_dict(item.get("origem"))
        segmentacao = _safe_dict(item.get("segmentacao"))
        integridade = _safe_dict(item.get("integridade_semantica"))
        review_flag = bool(_safe_dict(item.get("sinalizador_para_cadencia")).get("requer_revisao_manual_prioritaria"))

        text = normalize_spaces(_safe_str(item.get("texto_fragmento")) or _safe_str(_safe_dict(tree_item.get("base_empirica")).get("texto_fragmento")))
        if not text:
            continue

        carrier: dict[str, Any] = {}
        carrier.update(tree_item if isinstance(tree_item, dict) else {})
        if impact_external:
            carrier["impacto_no_mapa_fragmento"] = impact_external.get("impacto_no_mapa_fragmento", impact_external)
        if not carrier.get("impacto_mapa") and impacto_tree:
            carrier["impacto_mapa"] = impacto_tree

        proposition_weights = _extract_fragment_proposition_weights(carrier, indices.proposition_ids)
        proposition_ids = dedupe_preserve_order(list(proposition_weights.keys()))
        path_ids = dedupe_preserve_order([normalize_path_id(pid) for pid in _safe_list(lig.get("percurso_ids")) if isinstance(pid, str) and normalize_path_id(pid) in indices.path_ids])
        argument_ids = dedupe_preserve_order([aid for aid in _safe_list(lig.get("argumento_ids")) if isinstance(aid, str) and aid in indices.argument_ids])
        chapter_ids: list[str] = []
        regime_ids: list[str] = []
        operation_ids: list[str] = []
        for pid in proposition_ids:
            chapter_ids.extend(indices.proposition_to_chapters.get(pid, []))
            regime_ids.extend(indices.proposition_to_regimes.get(pid, []))
            path_ids.extend(indices.proposition_to_paths.get(pid, []))
            argument_ids.extend(indices.proposition_to_arguments.get(pid, []))
            operation_ids.extend(indices.proposition_to_operations.get(pid, []))
        # usar argumentos locais, sem promover argumentos por API via ramo.
        for aid in argument_ids:
            chapter_ids.extend(indices.argument_to_chapters.get(aid, []))
            regime_ids.extend(indices.argument_to_regimes.get(aid, []))
            operation_ids.extend(indices.argument_to_operations.get(aid, []))
        chapter_ids = dedupe_preserve_order([c for c in chapter_ids if c in indices.chapter_ids])
        regime_ids = dedupe_preserve_order([r for r in regime_ids if r in indices.regime_ids])
        path_ids = dedupe_preserve_order([normalize_path_id(p) for p in path_ids if normalize_path_id(p) in indices.path_ids])
        corridor_ids = [corr for corr, props in indices.corridors.items() if len(set(props).intersection(proposition_ids)) >= 2]

        impact_effect = _safe_str(impacto_tree.get("efeito_principal_no_mapa")) or _safe_str(impact_payload_item.get("efeito_principal_no_mapa")) or "sem_impacto_relevante"
        final_dec = _safe_dict(impacto_tree.get("decisao_final")) or _safe_dict(impact_payload_item.get("decisao_final"))
        impact_action = _safe_str(final_dec.get("acao_recomendada_sobre_o_mapa")) or "sem_acao"
        impact_priority = _safe_str(final_dec.get("prioridade_editorial")) or "media"
        confidence_score = average([
            confidence_text_to_score(_safe_str(cad.get("confianca_cadencia")) or _safe_str(final_dec.get("confianca_da_analise"))),
            segmentation_confidence_to_score(_safe_str(item.get("confianca_segmentacao"))),
            semantic_integrity_to_score(_safe_str(integridade.get("grau"))),
        ])
        validation_state = _safe_str(tree_item.get("estado_validacao")) or "desconhecido"
        centrality = _safe_str(cad.get("centralidade")) or "auxiliar"

        record = FragmentRecord(
            fragment_id=fragment_id,
            source_mode=source_mode,
            text=text,
            proposition_weights=proposition_weights,
            proposition_ids=proposition_ids,
            chapter_ids=chapter_ids,
            regime_ids=regime_ids,
            path_ids=path_ids,
            argument_ids=dedupe_preserve_order([a for a in argument_ids if a in indices.argument_ids]),
            corridor_ids=dedupe_preserve_order(corridor_ids),
            operation_ids_inferred=dedupe_preserve_order([op for op in operation_ids if op]),
            impact_effect=impact_effect,
            impact_action=impact_action,
            impact_priority=impact_priority,
            confidence_score=confidence_score,
            validation_state=validation_state,
            centrality=centrality,
            source_labels=dedupe_preserve_order([
                _safe_str(tratamento.get("problema_filosofico_central")),
                _safe_str(tratamento.get("trabalho_no_sistema")),
                _safe_str(cad.get("zona_provavel_percurso")),
                _safe_str(item.get("tema_dominante_provisorio")),
            ]),
            metadata={
                "origem_id": _safe_str(origem.get("origem_id")) or _safe_str(item.get("origem_id")),
                "origem": origem,
                "texto_normalizado": _safe_str(item.get("texto_normalizado")),
                "texto_fonte_reconstituido": _safe_str(item.get("texto_fonte_reconstituido")),
                "segmentacao": segmentacao,
                "integridade_semantica": integridade,
                "confianca_segmentacao": _safe_str(item.get("confianca_segmentacao")),
                "requires_manual_review": review_flag or bool(_safe_dict(cad).get("necessita_revisao_humana")),
                "ramo_ids": dedupe_preserve_order([rid for rid in _safe_list(lig.get("ramo_ids")) if isinstance(rid, str)]),
                "microlinha_ids": _safe_list(lig.get("microlinha_ids")),
                "cadencia": cad,
            },
        )
        record = _merge_external_impact_weights(record, impact_by_fragment)
        records.append(record)

    if not records:
        raise FragmentBaseError("Nenhum fragmento utilizável foi carregado.")
    records.sort(key=lambda rec: rec.fragment_id)
    return records


# =============================================================================
# INFERÊNCIA DE OPERAÇÕES
# =============================================================================


def _infer_operations_from_paths(path_ids: Sequence[str], indices: NormativeIndices) -> list[str]:
    ops: list[str] = []
    for path_id in path_ids:
        ptype = normalize_path_type(indices.path_to_type.get(path_id, ""))
        if ptype == "axial_mediational":
            ops.extend(["OP_IDENTIFICACAO_MEDIACAO", "OP_DISTINCAO_APREENSAO_REPRESENTACAO"])
        elif ptype == "axial_epistemological":
            ops.extend(["OP_FIXACAO_CRITERIO", "OP_SUBMISSAO_REAL", "OP_IDENTIFICACAO_ADEQUACAO"])
        elif ptype == "axial_transitional":
            ops.extend(["OP_IDENTIFICACAO_DEPENDENCIA", "OP_RECONDUCAO_RELACIONAL"])
        elif ptype == "axial_critical_corrective":
            ops.extend(["OP_IDENTIFICACAO_DEGENERACAO", "OP_REINTEGRACAO_ONTOLOGICA"])
    return dedupe_preserve_order(ops)


def _infer_operations_from_regimes(regime_ids: Sequence[str], bundle: SourceBundle) -> list[str]:
    meta_indice = _safe_dict(bundle.data.get("meta_indice"))
    regimes = _safe_dict(_safe_dict(meta_indice.get("meta_indice")).get("regimes"))
    ops: list[str] = []
    for regime_id in regime_ids:
        ops.extend([op for op in _safe_list(_safe_dict(regimes.get(regime_id)).get("operacoes")) if isinstance(op, str)])
    return dedupe_preserve_order(ops)


def infer_fragment_operations(fragment: FragmentRecord, bundle: SourceBundle, indices: NormativeIndices) -> FragmentRecord:
    # Base principal: operações já ligadas localmente à proposição/argumento.
    inferred = list(fragment.operation_ids_inferred)
    # Reforços fracos: percurso e regime apenas acrescentam quando ainda não há massa suficiente.
    path_ops = _infer_operations_from_paths(fragment.path_ids, indices)
    regime_ops = _infer_operations_from_regimes(fragment.regime_ids, bundle)
    if len(inferred) < 3:
        inferred.extend(path_ops)
    if len(inferred) < 4:
        inferred.extend(regime_ops)
    fragment.operation_ids_inferred = dedupe_preserve_order([op for op in inferred if op])
    return fragment


# =============================================================================
# SCORING VETORIAL
# =============================================================================


def _fragment_altitude(fragment: FragmentRecord, indices: NormativeIndices) -> float:
    if not fragment.path_ids:
        return 0.0
    return average(PATH_TYPE_ALTITUDE.get(normalize_path_type(indices.path_to_type.get(pid, "unknown")), 0.0) for pid in fragment.path_ids)


def _expected_altitude_value(runtime: RuntimeConfig, indices: NormativeIndices) -> float:
    return PATH_TYPE_ALTITUDE.get(normalize_path_type(indices.cf_altitude_expectation.get(runtime.confronto_id, "unknown")), 0.0)


def compute_base_strength_score(fragment: FragmentRecord) -> float:
    proposition_mass = sum(fragment.proposition_weights.values())
    proposition_component = clamp(proposition_mass / 2.5)
    impact_component = average([
        IMPACT_EFFECT_SCORE.get(normalize_text(fragment.impact_effect), 0.35),
        IMPACT_ACTION_SCORE.get(normalize_text(fragment.impact_action), 0.30),
        PRIORITY_SCORE.get(normalize_text(fragment.impact_priority), 0.55),
    ])
    quality_component = average([
        fragment.confidence_score,
        validation_state_to_score(fragment.validation_state),
        centrality_to_score(fragment.centrality),
    ])
    text_component = clamp(len(fragment.text) / 900.0)
    return clamp((proposition_component * 0.42) + (impact_component * 0.28) + (quality_component * 0.20) + (text_component * 0.10))


def compute_nuclearity_score(fragment: FragmentRecord, center: AdmissibleConfrontCenter) -> float:
    return weighted_overlap_ratio(fragment.proposition_weights, center.promoted_proposition_ids)


def compute_mediationality_score(fragment: FragmentRecord, center: AdmissibleConfrontCenter, indices: NormativeIndices) -> float:
    path_score = clamp(len(set(fragment.path_ids).intersection(MEDIATIONAL_PATH_IDS)) / max(1, len(MEDIATIONAL_PATH_IDS)))
    corridor_score = clamp(1.0 if any(corr in {"P23_P30", "P25_P30", "P27_P34"} for corr in fragment.corridor_ids) else 0.0)
    chapter_score = clamp(sum(1 for cap in fragment.chapter_ids if cap in {"CAP_13_REPRESENTACAO", "CAP_14_LINGUAGEM_MEDIACAO", "CAP_15_CONSCIENCIA"}) / 3.0)
    nuclear_discount = compute_nuclearity_score(fragment, center) * 0.35
    return clamp((path_score * 0.40) + (corridor_score * 0.35) + (chapter_score * 0.25) - nuclear_discount)


def compute_epistemic_weight_score(fragment: FragmentRecord, center: AdmissibleConfrontCenter) -> float:
    path_score = clamp(1.0 if set(fragment.path_ids).intersection(EPISTEMOLOGICAL_PATH_IDS) else 0.0)
    prop_score = weighted_overlap_ratio(fragment.proposition_weights, CORRIDOR_DEFINITIONS.get("P33_P37", []))
    chapter_score = clamp(sum(1 for cap in fragment.chapter_ids if cap in {"CAP_17_ADEQUACAO", "CAP_18_CRITERIO", "CAP_19_VERDADE", "CAP_20_ERRO", "CAP_21_CORRECAO"}) / 5.0)
    nuclear_discount = compute_nuclearity_score(fragment, center) * 0.30
    return clamp((path_score * 0.35) + (prop_score * 0.40) + (chapter_score * 0.25) - nuclear_discount)


def compute_shared_background_score(fragment: FragmentRecord, center: AdmissibleConfrontCenter) -> float:
    return weighted_overlap_ratio(fragment.proposition_weights, center.background_proposition_ids)


_NEIGHBOR_CENTER_CACHE: dict[tuple[str, str], dict[str, dict[str, list[str]]]] = {}


def _parse_neighbor_centers(runtime: RuntimeConfig, indices: NormativeIndices) -> dict[str, dict[str, list[str]]]:
    cache_key = (str(runtime.project_root.resolve()), runtime.confronto_id)
    if cache_key in _NEIGHBOR_CENTER_CACHE:
        return _NEIGHBOR_CENTER_CACHE[cache_key]
    neighbors: dict[str, dict[str, list[str]]] = {}
    for neighbor_cf in indices.cf_neighbor_map.get(runtime.confronto_id, []):
        filename: Optional[Path] = None
        for candidate in DOSSIER_CANDIDATE_FILENAMES:
            located = find_file(runtime.project_root, candidate.format(cf=neighbor_cf))
            if located is not None:
                filename = located
                break
        if filename is None:
            continue
        text = read_text(filename)
        sections = parse_markdown_sections(text)
        strong: list[str] = []
        background: list[str] = []
        for section in sections:
            role = _section_role(section)
            ids = [pid for pid in extract_inline_ids(section.body, "proposicao", indices.proposition_ids)]
            if role == "strong":
                strong.extend(ids)
            elif role == "background":
                background.extend(ids)
        if not strong:
            for section in sections:
                if fuzzy_heading_key(section.heading) == "proposicoes_envolvidas":
                    strong.extend(extract_inline_ids(section.body, "proposicao", indices.proposition_ids))
        neighbors[neighbor_cf] = {
            "promoted": dedupe_preserve_order(strong),
            "background": dedupe_preserve_order([pid for pid in background if pid not in strong]),
        }
    _NEIGHBOR_CENTER_CACHE[cache_key] = neighbors
    return neighbors


def compute_neighbor_overlap_score(
    fragment: FragmentRecord,
    runtime: RuntimeConfig,
    bundle: SourceBundle,
    indices: NormativeIndices,
    neighbor_centers: Optional[dict[str, dict[str, list[str]]]] = None,
) -> float:
    del bundle
    neighbor_centers = neighbor_centers or _parse_neighbor_centers(runtime, indices)
    if not neighbor_centers:
        return 0.0
    return clamp(max(weighted_overlap_ratio(fragment.proposition_weights, neighbor["promoted"]) for neighbor in neighbor_centers.values()))


def compute_corridor_support_score(fragment: FragmentRecord, center: AdmissibleConfrontCenter) -> float:
    corridor_hit = 1.0 if set(fragment.corridor_ids).intersection(center.admissible_corridors) else 0.0
    expanded_hit = weighted_overlap_ratio(fragment.proposition_weights, center.nuclear_expanded_ids)
    return clamp((corridor_hit * 0.65) + (expanded_hit * 0.25))


def compute_corridor_capture_score(fragment: FragmentRecord, center: AdmissibleConfrontCenter, runtime: RuntimeConfig, indices: NormativeIndices) -> float:
    if not fragment.corridor_ids:
        return 0.0
    expected_altitude = _expected_altitude_value(runtime, indices)
    nuclearity = compute_nuclearity_score(fragment, center)
    scores: list[float] = []
    for corridor_id in fragment.corridor_ids:
        corridor_props = indices.corridors.get(corridor_id, [])
        overlap = weighted_overlap_ratio(fragment.proposition_weights, corridor_props)
        admissible_penalty = 0.0 if corridor_id in center.admissible_corridors else 0.22
        higher_penalty = 0.18 if _fragment_altitude(fragment, indices) > expected_altitude + 0.45 else 0.0
        capture = clamp(overlap + admissible_penalty + higher_penalty - (nuclearity * 0.35))
        scores.append(capture)
    return clamp(max(scores) if scores else 0.0)


def compute_higher_axis_capture_score(fragment: FragmentRecord, declared_state: DeclaredDossierState, runtime: RuntimeConfig, indices: NormativeIndices) -> float:
    expected = _expected_altitude_value(runtime, indices)
    actual = _fragment_altitude(fragment, indices)
    if expected <= 0 or actual <= 0:
        return 0.0
    if actual <= expected:
        return 0.0
    return clamp((actual - expected) / 2.2)


def compute_declared_alignment_score(fragment: FragmentRecord, declared_state: DeclaredDossierState, center: AdmissibleConfrontCenter) -> float:
    declared_core = dedupe_preserve_order(declared_state.proposicoes_nucleares_centrais + center.promoted_proposition_ids)
    declared_background = dedupe_preserve_order(declared_state.proposicoes_background + center.background_proposition_ids)
    rejected = dedupe_preserve_order(declared_state.proposicoes_rejeitadas + center.rejected_proposition_ids)
    core = weighted_overlap_ratio(fragment.proposition_weights, declared_core)
    background = weighted_overlap_ratio(fragment.proposition_weights, declared_background)
    rejected_ratio = weighted_overlap_ratio(fragment.proposition_weights, rejected)
    return clamp((core * 0.78) + (background * 0.18) - (rejected_ratio * 0.55))


def compute_overall_selection_score(vector: FragmentScoreVector, weights: ScoreWeights) -> float:
    overall = (
        (vector.base_strength * weights.base_strength)
        + (vector.nuclearity * weights.nuclearity)
        + (vector.declared_alignment * weights.declared_alignment)
        + (vector.corridor_support * 0.12)
        - (vector.mediationality * weights.mediationality_penalty)
        - (vector.epistemic_weight * weights.epistemic_penalty)
        - (vector.shared_background * weights.background_penalty)
        - (vector.neighbor_overlap * weights.neighbor_penalty)
        - (vector.corridor_capture * weights.corridor_capture_penalty)
        - (vector.higher_axis_capture * weights.higher_axis_penalty)
    )
    return round(clamp(overall, 0.0, 1.0), 6)


def score_fragment(
    fragment: FragmentRecord,
    center: AdmissibleConfrontCenter,
    declared_state: DeclaredDossierState,
    runtime: RuntimeConfig,
    bundle: SourceBundle,
    indices: NormativeIndices,
    neighbor_centers: Optional[dict[str, dict[str, list[str]]]] = None,
) -> FragmentScoreVector:
    try:
        base_strength = compute_base_strength_score(fragment)
        nuclearity = compute_nuclearity_score(fragment, center)
        mediationality = compute_mediationality_score(fragment, center, indices)
        epistemic_weight = compute_epistemic_weight_score(fragment, center)
        shared_background = compute_shared_background_score(fragment, center)
        neighbor_overlap = compute_neighbor_overlap_score(fragment, runtime, bundle, indices, neighbor_centers=neighbor_centers)
        corridor_support = compute_corridor_support_score(fragment, center)
        corridor_capture = compute_corridor_capture_score(fragment, center, runtime, indices)
        higher_axis_capture = compute_higher_axis_capture_score(fragment, declared_state, runtime, indices)
        declared_alignment = compute_declared_alignment_score(fragment, declared_state, center)
    except Exception as exc:
        raise ScoringError(f"Falha ao calcular score do fragmento {fragment.fragment_id}: {exc}") from exc

    vector = FragmentScoreVector(
        fragment_id=fragment.fragment_id,
        base_strength=base_strength,
        nuclearity=nuclearity,
        mediationality=mediationality,
        epistemic_weight=epistemic_weight,
        shared_background=shared_background,
        neighbor_overlap=neighbor_overlap,
        corridor_support=corridor_support,
        corridor_capture=corridor_capture,
        higher_axis_capture=higher_axis_capture,
        declared_alignment=declared_alignment,
        overall_selection_score=0.0,
    )
    vector.overall_selection_score = compute_overall_selection_score(vector, runtime.weights)
    if nuclearity >= 0.45:
        vector.categories.append("nuclear")
    if mediationality >= 0.40:
        vector.categories.append("mediational")
    if shared_background >= 0.35:
        vector.categories.append("background")
    if corridor_capture >= 0.40 or higher_axis_capture >= 0.40 or neighbor_overlap >= 0.40:
        vector.categories.append("capture_risk")
    if weighted_overlap_ratio(fragment.proposition_weights, center.rejected_proposition_ids) >= 0.25:
        vector.categories.append("contradictory")
    vector.rationale = dedupe_preserve_order([
        reason for reason, active in (
            ("forte base fragmentária", base_strength >= 0.60),
            ("overlap nuclear relevante", nuclearity >= 0.45),
            ("material mediacional relevante", mediationality >= 0.45),
            ("peso epistemológico deslocado", epistemic_weight >= 0.45),
            ("fundo partilhado relevante", shared_background >= 0.35),
            ("overlap relevante com dossier vizinho", neighbor_overlap >= 0.40),
            ("corredor opera como suporte", corridor_support >= 0.40),
            ("risco de captura de corredor", corridor_capture >= 0.45),
            ("pressão de eixo arquitetónico mais alto", higher_axis_capture >= 0.45),
            ("bom alinhamento declarado", declared_alignment >= 0.45),
        ) if active
    ])
    return vector


# =============================================================================
# SELEÇÃO DE SAMPLE
# =============================================================================


def _vector_by_fragment_id(vectors: Sequence[FragmentScoreVector]) -> dict[str, FragmentScoreVector]:
    return {vec.fragment_id: vec for vec in vectors}


def _pick_ranked(ranked_ids: Sequence[str], quota: int, selected: list[str], selected_set: set[str]) -> None:
    remaining = max(quota, 0)
    for fragment_id in ranked_ids:
        if remaining <= 0:
            break
        if fragment_id in selected_set:
            continue
        selected.append(fragment_id)
        selected_set.add(fragment_id)
        remaining -= 1


def select_sample(
    runtime: RuntimeConfig,
    fragments: Sequence[FragmentRecord],
    score_vectors: Sequence[FragmentScoreVector],
    center: AdmissibleConfrontCenter,
) -> SampleSelection:
    vector_map = _vector_by_fragment_id(score_vectors)
    ranked_vectors = sorted(score_vectors, key=lambda v: (-v.overall_selection_score, -v.base_strength, v.fragment_id))[: runtime.top_k_scoring]

    nuclear_candidates = [v.fragment_id for v in ranked_vectors if v.nuclearity >= 0.45 and v.corridor_capture < 0.60 and v.higher_axis_capture < 0.60]
    support_candidates = [v.fragment_id for v in ranked_vectors if v.corridor_support >= 0.35 and v.corridor_capture < 0.60 and v.neighbor_overlap < 0.60]
    background_candidates = [v.fragment_id for v in ranked_vectors if v.shared_background >= 0.35 and v.nuclearity >= 0.20]
    capture_candidates = [v.fragment_id for v in ranked_vectors if (v.corridor_capture >= 0.40 or v.higher_axis_capture >= 0.40 or v.neighbor_overlap >= 0.40)]
    contradictory_candidates = [v.fragment_id for v in ranked_vectors if "contradictory" in v.categories]

    selected: list[str] = []
    selected_set: set[str] = set()
    _pick_ranked(nuclear_candidates, max(5, runtime.sample_size // 2), selected, selected_set)
    _pick_ranked(support_candidates, max(2, runtime.sample_size // 4), selected, selected_set)
    _pick_ranked(background_candidates, min(2, max(1, runtime.sample_size // 6)), selected, selected_set)

    for vector in ranked_vectors:
        if len(selected) >= runtime.sample_size:
            break
        if vector.fragment_id in selected_set:
            continue
        if vector.corridor_capture >= 0.65 or vector.higher_axis_capture >= 0.65:
            continue
        selected.append(vector.fragment_id)
        selected_set.add(vector.fragment_id)

    coverage_summary = {
        "nuclear_count": sum(1 for fid in selected if fid in nuclear_candidates),
        "support_count": sum(1 for fid in selected if fid in support_candidates),
        "background_count": sum(1 for fid in selected if fid in background_candidates),
        "capture_risk_count": sum(1 for fid in selected if fid in capture_candidates),
        "contradictory_count": sum(1 for fid in selected if fid in contradictory_candidates),
        "selected_size": len(selected),
        "sample_size_target": runtime.sample_size,
    }

    ranked_payload = [
        {
            "fragment_id": vector.fragment_id,
            "overall_selection_score": vector.overall_selection_score,
            "base_strength": round(vector.base_strength, 6),
            "nuclearity": round(vector.nuclearity, 6),
            "mediationality": round(vector.mediationality, 6),
            "epistemic_weight": round(vector.epistemic_weight, 6),
            "corridor_capture": round(vector.corridor_capture, 6),
            "higher_axis_capture": round(vector.higher_axis_capture, 6),
            "categories": list(vector.categories),
            "rationale": list(vector.rationale),
        }
        for vector in ranked_vectors
    ]

    warnings: list[str] = []
    if coverage_summary["nuclear_count"] == 0:
        warnings.append("O sample representativo ficou sem fragmentos nucleares fortes; manter prudência máxima na adjudicação.")
    if coverage_summary["capture_risk_count"] == 0:
        warnings.append("O sample representativo não inclui fragmentos de risco; o diagnóstico usa os candidatos de contraste fora do sample principal.")

    excluded: list[dict[str, Any]] = []
    for vector in ranked_vectors:
        if vector.fragment_id in selected_set:
            continue
        if vector.fragment_id in capture_candidates or vector.fragment_id in contradictory_candidates:
            excluded.append({
                "fragment_id": vector.fragment_id,
                "score": vector.overall_selection_score,
                "reason": "retido apenas como contraste diagnóstico, não como sample representativo",
            })

    return SampleSelection(
        selected_fragment_ids=selected,
        ranked_fragments=ranked_payload,
        coverage_summary=coverage_summary,
        nuclear_fragments=[fid for fid in selected if fid in nuclear_candidates],
        mediational_fragments=[fid for fid in selected if fid in support_candidates],
        background_fragments=[fid for fid in selected if fid in background_candidates],
        capture_risk_fragments=dedupe_preserve_order(capture_candidates),
        contradictory_fragments=dedupe_preserve_order(contradictory_candidates),
        excluded_high_score_fragments_with_reason=excluded,
        selection_warnings=warnings,
    )


# =============================================================================
# CONSTRUÇÃO DO admissible_confront_center
# =============================================================================


def _adjudication_restricted_payload(adjudication_item: dict[str, Any]) -> dict[str, Any]:
    return _safe_dict(adjudication_item.get("adjudicacao_filosofica_restrita")) or _safe_dict(adjudication_item.get("adjudicacao_filosofica"))


def _collect_adjudication_structural_ids(payload: dict[str, Any], prefix: str) -> list[str]:
    return _flatten_structural_ids(payload, prefix)


def _weak_sample_proposition_support(fragments: Sequence[FragmentRecord]) -> dict[str, float]:
    weights: Counter[str] = Counter()
    for fragment in fragments:
        for pid, weight in fragment.proposition_weights.items():
            weights[pid] += max(weight, 0.0) * (0.50 + (fragment.confidence_score * 0.50))
    if not weights:
        return {}
    max_value = max(weights.values())
    if max_value <= 0:
        return {}
    return {pid: round(value / max_value, 6) for pid, value in weights.items()}


def _corridors_from_propositions(proposition_ids: Sequence[str], indices: NormativeIndices) -> list[str]:
    prop_set = set(proposition_ids)
    corridors: list[str] = []
    for corridor_id, props in indices.corridors.items():
        overlap = len(prop_set.intersection(props))
        if overlap >= 2:
            corridors.append(corridor_id)
    return dedupe_preserve_order(corridors)


def build_admissible_confront_center(
    runtime: RuntimeConfig,
    bundle: SourceBundle,
    indices: NormativeIndices,
    declared_state: DeclaredDossierState,
    fragments: Sequence[FragmentRecord],
) -> AdmissibleConfrontCenter:
    matrix = _safe_dict(indices.matrix_by_cf.get(runtime.confronto_id))
    adjudication = _safe_dict(indices.adjudication_by_cf.get(runtime.confronto_id))
    restricted_adj = _adjudication_restricted_payload(adjudication)

    source_contributions: list[dict[str, Any]] = []
    promoted_reasons: defaultdict[str, list[str]] = defaultdict(list)
    rejected_reasons: defaultdict[str, list[str]] = defaultdict(list)
    promote_score: Counter[str] = Counter()
    reject_score: Counter[str] = Counter()

    def promote(ids: Iterable[str], source: str, strength: float, reason: str) -> None:
        ids_clean = [i for i in ids if i in indices.proposition_ids]
        if ids_clean:
            source_contributions.append({"source": source, "strength": strength, "promoted_ids": ids_clean, "rejected_ids": [], "why": reason})
        for pid in ids_clean:
            promote_score[pid] += strength
            promoted_reasons[pid].append(reason)

    def reject(ids: Iterable[str], source: str, strength: float, reason: str) -> None:
        ids_clean = [i for i in ids if i in indices.proposition_ids]
        if ids_clean:
            source_contributions.append({"source": source, "strength": strength, "promoted_ids": [], "rejected_ids": ids_clean, "why": reason})
        for pid in ids_clean:
            reject_score[pid] += strength
            rejected_reasons[pid].append(reason)

    # Meta-norma do README paira acima da cadeia como critério de veto.
    source_contributions.append({
        "source": "meta_norm_readme",
        "strength": 1.10,
        "promoted_ids": [],
        "rejected_ids": [],
        "why": "O README da fase governa o modo de decisão: o sample nunca é soberano sobre o dossier reformulado e o real não pode ser substituído por corredores, sistemas ou eixos superiores.",
    })

    # 1) norma local soberana
    promote(declared_state.proposicoes_nucleares_centrais, "dossier_reformulado", 1.00, "Núcleo forte declarado no dossier reformulado.")
    reject(declared_state.proposicoes_rejeitadas, "dossier_reformulado", 1.00, "Proposições explicitamente descentradas ou rejeitadas no dossier reformulado.")

    # 2) baseline normativa: adjudicação restrita, apenas subsidiária
    promote(_safe_list(adjudication.get("proposicao_ids")), "adjudicacao_restrita_confronto", 0.60, "Baseline subsidiária da adjudicação restrita.")
    promote(_safe_list(restricted_adj.get("proposicoes_articulacao")), "adjudicacao_restrita_confronto", 0.48, "Articulação estrutural subsidiária da adjudicação restrita.")

    # 3) baseline normativa: matriz
    promote(_safe_list(matrix.get("proposicao_ids")), "matriz_confronto", 0.38, "Baseline fraca da matriz de confronto.")

    # 4) evidência fragmentária apenas como reforço fraco de IDs já admissíveis.
    weak_support = _weak_sample_proposition_support(fragments)
    admissible_pool = set(declared_state.proposicoes_nucleares_centrais) | set(_safe_list(adjudication.get("proposicao_ids"))) | set(_safe_list(matrix.get("proposicao_ids")))
    weak_promoted = [pid for pid, score in weak_support.items() if score >= 0.60 and pid in admissible_pool and pid not in declared_state.proposicoes_rejeitadas]
    promote(weak_promoted, "sample_fragmentario", 0.06, "O sample fragmentário só reforça IDs já admissíveis por fontes superiores.")

    background_ids = dedupe_preserve_order(declared_state.proposicoes_background)
    notes: list[str] = []

    if runtime.confronto_id == "CF03":
        cf03_required_core = ["P14", "P15", "P18", "P19", "P21", "P22"]
        promote(cf03_required_core, "dossier_reformulado", 1.00, "Regra CF03: núcleo obrigatório do dossier reformulado.")
        reject(["P02", "P05"], "dossier_reformulado", 1.00, "Regra CF03: P02 e P05 permanecem descentradas.")
        background_ids = dedupe_preserve_order([pid for pid in background_ids if pid not in set(cf03_required_core)] + ["P01", "P13"])
        notes.append("Regra CF03 aplicada: P14/P15/P18/P19/P21/P22 promovidas; P01/P13 fundo; P02/P05 descentradas.")

    promoted_ids = [pid for pid, score in promote_score.items() if score >= 0.60 and reject_score.get(pid, 0.0) < score]
    weak_ids = [pid for pid, score in promote_score.items() if 0.24 <= score < 0.60 and reject_score.get(pid, 0.0) < score]
    rejected_ids = [pid for pid, score in reject_score.items() if score >= promote_score.get(pid, 0.0)]

    promoted_ids = dedupe_preserve_order([pid for pid in promoted_ids if pid not in rejected_ids and pid not in background_ids])
    weak_ids = dedupe_preserve_order([pid for pid in weak_ids if pid not in promoted_ids and pid not in rejected_ids and pid not in background_ids])
    background_ids = dedupe_preserve_order([pid for pid in background_ids if pid not in promoted_ids and pid not in rejected_ids])

    if runtime.confronto_id == "CF03":
        promoted_ids = ["P14", "P15", "P18", "P19", "P21", "P22"]
        weak_ids = [pid for pid in weak_ids if pid not in {"P02", "P05"} and pid not in set(promoted_ids)]
        background_ids = dedupe_preserve_order(["P01", "P13"])
        rejected_ids = dedupe_preserve_order(rejected_ids + ["P02", "P05"])

    promoted_bridge_ids = dedupe_preserve_order(
        declared_state.pontes + [x for x in _safe_list(matrix.get("ponte_ids_relacionadas")) if isinstance(x, str)] + _collect_adjudication_structural_ids(restricted_adj, "PN")
    )
    promoted_anchorage_ids = dedupe_preserve_order(
        declared_state.ancoragens + [x for x in _safe_list(matrix.get("ancoragem_ids_relacionadas")) if isinstance(x, str)] + _collect_adjudication_structural_ids(restricted_adj, "AC")
    )
    promoted_field_ids = dedupe_preserve_order(
        declared_state.campos_do_real + [x for x in _safe_list(matrix.get("campo_ids_relacionados")) if isinstance(x, str)] + _collect_adjudication_structural_ids(restricted_adj, "CR")
    )

    promoted_chapter_ids: list[str] = []
    promoted_regime_ids: list[str] = []
    promoted_percurso_ids: list[str] = []
    promoted_argument_ids: list[str] = []
    for pid in promoted_ids + weak_ids:
        promoted_chapter_ids.extend(indices.proposition_to_chapters.get(pid, []))
        promoted_regime_ids.extend(indices.proposition_to_regimes.get(pid, []))
        promoted_percurso_ids.extend(indices.proposition_to_paths.get(pid, []))
        promoted_argument_ids.extend(indices.proposition_to_arguments.get(pid, []))
    promoted_chapter_ids = dedupe_preserve_order(promoted_chapter_ids + declared_state.capitulos)
    promoted_regime_ids = dedupe_preserve_order(promoted_regime_ids + declared_state.regimes)
    promoted_percurso_ids = dedupe_preserve_order([normalize_path_id(pid) for pid in (promoted_percurso_ids + declared_state.percursos)])
    promoted_argument_ids = dedupe_preserve_order(promoted_argument_ids + declared_state.argumentos)

    admissible_corridors = _corridors_from_propositions(promoted_ids + weak_ids, indices)
    rejected_corridors = _corridors_from_propositions(rejected_ids, indices)
    if runtime.confronto_id == "CF03":
        admissible_corridors = dedupe_preserve_order([corr for corr in admissible_corridors if corr != "P23_P30"] + ["P14_P22"])
        rejected_corridors = dedupe_preserve_order(rejected_corridors + ["P23_P30"])
        notes.append("Regra CF03 aplicada: P23_P30 proibido como centro soberano automático.")

    nuclear_expanded_ids = dedupe_preserve_order(promoted_ids + weak_ids)
    if not promoted_ids:
        raise AdmissibleCenterError("Não foi possível construir um centro admissível minimamente estável.")

    return AdmissibleConfrontCenter(
        confronto_id=runtime.confronto_id,
        promoted_proposition_ids=promoted_ids,
        promoted_weak_ids=weak_ids,
        nuclear_expanded_ids=nuclear_expanded_ids,
        background_proposition_ids=background_ids,
        rejected_proposition_ids=dedupe_preserve_order(rejected_ids),
        promoted_bridge_ids=promoted_bridge_ids,
        promoted_anchorage_ids=promoted_anchorage_ids,
        promoted_field_ids=promoted_field_ids,
        promoted_chapter_ids=promoted_chapter_ids,
        promoted_regime_ids=promoted_regime_ids,
        promoted_percurso_ids=promoted_percurso_ids,
        promoted_argument_ids=promoted_argument_ids,
        admissible_corridors=admissible_corridors,
        rejected_corridors=rejected_corridors,
        source_contributions=source_contributions,
        promoted_reasons={k: dedupe_preserve_order(v) for k, v in promoted_reasons.items()},
        rejected_reasons={k: dedupe_preserve_order(v) for k, v in rejected_reasons.items()},
        notes=notes,
    )


# =============================================================================
# DIAGNÓSTICO ARQUITETÓNICO
# =============================================================================


def _selected_fragment_objects(
    fragments: Sequence[FragmentRecord],
    score_vectors: Sequence[FragmentScoreVector],
    sample: SampleSelection,
) -> tuple[list[FragmentRecord], dict[str, FragmentScoreVector]]:
    fragment_map = {fragment.fragment_id: fragment for fragment in fragments}
    selected_fragments = [fragment_map[fid] for fid in sample.selected_fragment_ids if fid in fragment_map]
    vector_map = _vector_by_fragment_id(score_vectors)
    return selected_fragments, vector_map


def diagnose_dominant_sample_center(
    fragments: Sequence[FragmentRecord],
    score_vectors: Sequence[FragmentScoreVector],
    sample: SampleSelection,
    center: AdmissibleConfrontCenter,
) -> dict[str, Any]:
    selected_fragments, vector_map = _selected_fragment_objects(fragments, score_vectors, sample)
    prop_counter: Counter[str] = Counter()
    total = 0.0
    for fragment in selected_fragments:
        weight = max(vector_map[fragment.fragment_id].overall_selection_score, 0.0) + 0.01
        for pid, pweight in fragment.proposition_weights.items():
            prop_counter[pid] += pweight * weight
            total += pweight * weight
    top_props = [pid for pid, _ in prop_counter.most_common(8)]
    nuclear_ratio = clamp(sum(weight for pid, weight in prop_counter.items() if pid in set(center.nuclear_expanded_ids)) / total) if total else 0.0
    background_ratio = clamp(sum(weight for pid, weight in prop_counter.items() if pid in set(center.background_proposition_ids)) / total) if total else 0.0
    corridor_ratio = clamp(sum(weight for pid, weight in prop_counter.items() if pid in set(sum([CORRIDOR_DEFINITIONS.get(c, []) for c in center.admissible_corridors], []))) / total) if total else 0.0
    return {
        "dominant_props": top_props,
        "prop_weights": {pid: round(weight, 6) for pid, weight in prop_counter.items()},
        "nuclear_ratio": round(nuclear_ratio, 6),
        "background_ratio": round(background_ratio, 6),
        "admissible_corridor_ratio": round(corridor_ratio, 6),
    }


def diagnose_corridors(
    runtime: RuntimeConfig,
    fragments: Sequence[FragmentRecord],
    score_vectors: Sequence[FragmentScoreVector],
    sample: SampleSelection,
    center: AdmissibleConfrontCenter,
    indices: NormativeIndices,
) -> dict[str, Any]:
    selected_fragments, vector_map = _selected_fragment_objects(fragments, score_vectors, sample)
    corridor_counter: Counter[str] = Counter()
    total_selection_weight = 0.0
    for fragment in selected_fragments:
        selection_weight = max(vector_map[fragment.fragment_id].overall_selection_score, 0.0) + 0.01
        total_selection_weight += selection_weight
        for corridor_id in fragment.corridor_ids:
            corridor_counter[corridor_id] += selection_weight
    dominant_corridor = corridor_counter.most_common(1)[0][0] if corridor_counter else ""
    dominant_weight = corridor_counter[dominant_corridor] if dominant_corridor else 0.0
    corridor_ratio = clamp(dominant_weight / total_selection_weight) if total_selection_weight else 0.0
    nuclear_weight = sum((max(vector_map[fid].overall_selection_score, 0.0) + 0.01) * vector_map[fid].nuclearity for fid in sample.selected_fragment_ids if fid in vector_map)

    shared_with_neighbor = False
    if dominant_corridor:
        for neighbor_cf in indices.cf_neighbor_map.get(runtime.confronto_id, []):
            if dominant_corridor in indices.cf_sensitive_corridors.get(neighbor_cf, []):
                shared_with_neighbor = True
                break

    higher_altitude = False
    if dominant_corridor:
        dominant_fragment_altitudes = [_fragment_altitude(fragment, indices) for fragment in selected_fragments if dominant_corridor in fragment.corridor_ids]
        expected_altitude = _expected_altitude_value(runtime, indices)
        corridor_altitude = average(dominant_fragment_altitudes)
        higher_altitude = bool(expected_altitude and corridor_altitude > expected_altitude + 0.45)

    why: list[str] = []
    if not dominant_corridor:
        status = CorridorStatus.none
        why.append("Nenhum corredor dominou o sample selecionado.")
    elif dominant_corridor in center.admissible_corridors and corridor_ratio < 0.45:
        status = CorridorStatus.corridor_support
        why.append("O corredor dominante medeia o núcleo admissível sem o soberanizar.")
    elif corridor_ratio >= 0.45 and (dominant_corridor not in center.admissible_corridors) and (shared_with_neighbor or higher_altitude or dominant_weight > nuclear_weight):
        status = CorridorStatus.corridor_capture
        why.append("O corredor dominante concentrou peso suficiente para disputar o centro próprio do confronto.")
        if shared_with_neighbor:
            why.append("O corredor dominante é partilhado com dossiers vizinhos.")
        if higher_altitude:
            why.append("O corredor dominante opera em altitude arquitetónica superior à esperada.")
        if dominant_weight > nuclear_weight:
            why.append("O corredor pesa mais do que o núcleo admissível no sample.")
    else:
        status = CorridorStatus.corridor_support if dominant_corridor in center.admissible_corridors else CorridorStatus.none
        why.append("Há corredor dominante, mas sem condições formais de captura.")
    return {
        "dominant_corridor": dominant_corridor,
        "corridor_status": status,
        "corridor_ratio": round(corridor_ratio, 6),
        "corridor_weights": {cid: round(weight, 6) for cid, weight in corridor_counter.items()},
        "shared_with_neighbor": shared_with_neighbor,
        "higher_altitude": higher_altitude,
        "why": dedupe_preserve_order(why),
    }


def diagnose_neighbor_overlap(
    runtime: RuntimeConfig,
    fragments: Sequence[FragmentRecord],
    score_vectors: Sequence[FragmentScoreVector],
    sample: SampleSelection,
    center: AdmissibleConfrontCenter,
    indices: NormativeIndices,
) -> dict[str, Any]:
    selected_fragments, vector_map = _selected_fragment_objects(fragments, score_vectors, sample)
    neighbor_centers = _parse_neighbor_centers(runtime, indices)
    details: dict[str, Any] = {}
    sample_prop_weights: Counter[str] = Counter()
    total_prop_weight = 0.0
    for fragment in selected_fragments:
        selection_weight = max(vector_map[fragment.fragment_id].overall_selection_score, 0.0) + 0.01
        for proposition_id, weight in fragment.proposition_weights.items():
            sample_prop_weights[proposition_id] += selection_weight * weight
            total_prop_weight += selection_weight * weight
    top_neighbor_ratio = 0.0
    top_neighbor_id = ""
    for neighbor_cf, neighbor_data in neighbor_centers.items():
        overlap = sum(weight for proposition_id, weight in sample_prop_weights.items() if proposition_id in set(neighbor_data["promoted"]))
        ratio = clamp(overlap / total_prop_weight) if total_prop_weight else 0.0
        details[neighbor_cf] = {
            "overlap_weight": round(overlap, 6),
            "overlap_ratio": round(ratio, 6),
            "neighbor_promoted_ids": neighbor_data["promoted"],
        }
        if ratio > top_neighbor_ratio:
            top_neighbor_ratio = ratio
            top_neighbor_id = neighbor_cf
    nuclear_ratio = clamp(sum(weight for proposition_id, weight in sample_prop_weights.items() if proposition_id in set(center.nuclear_expanded_ids)) / total_prop_weight) if total_prop_weight else 0.0
    why: list[str] = []
    if top_neighbor_ratio >= 0.48 and nuclear_ratio < 0.22:
        status = NeighborStatus.neighbor_absorption
        why.append("O overlap com dossier vizinho ultrapassou o limiar de absorção e o núcleo diferencial enfraqueceu demasiado.")
    elif top_neighbor_ratio >= 0.24:
        status = NeighborStatus.shared_background
        why.append("Existe fundo partilhado relevante com dossier vizinho, mas ainda resta núcleo próprio diferenciável.")
    else:
        status = NeighborStatus.none
        why.append("O overlap com dossiers vizinhos ficou abaixo do limiar significativo.")
    return {
        "neighbor_status": status,
        "top_neighbor_cf": top_neighbor_id,
        "top_neighbor_ratio": round(top_neighbor_ratio, 6),
        "details": details,
        "why": dedupe_preserve_order(why),
    }


def diagnose_altitude(
    runtime: RuntimeConfig,
    fragments: Sequence[FragmentRecord],
    score_vectors: Sequence[FragmentScoreVector],
    sample: SampleSelection,
    indices: NormativeIndices,
) -> dict[str, Any]:
    selected_fragments, vector_map = _selected_fragment_objects(fragments, score_vectors, sample)
    altitudes: list[float] = []
    path_types: list[str] = []
    for fragment in selected_fragments:
        weight = max(vector_map[fragment.fragment_id].overall_selection_score, 0.0) + 0.01
        altitude = _fragment_altitude(fragment, indices)
        altitudes.extend([altitude] * max(1, int(math.ceil(weight * 3))))
        path_types.extend(indices.path_to_type.get(pid, "unknown") for pid in fragment.path_ids)
    dominant_altitude = average(altitudes)
    expected = _expected_altitude_value(runtime, indices)
    why: list[str] = []
    if expected <= 0 or dominant_altitude <= 0:
        status = AltitudeStatus.aligned_altitude
        why.append("Não havia altitude esperada suficientemente definida para medir captura vertical.")
    elif dominant_altitude > expected + 0.95:
        status = AltitudeStatus.higher_axis_capture
        why.append("A altitude dominante excede claramente a esperada e passa a governar o centro do sample.")
    elif dominant_altitude > expected + 0.35:
        status = AltitudeStatus.higher_axis_pressure
        why.append("Há pressão relevante de eixo arquitetónico mais alto sobre o sample.")
    elif dominant_altitude < expected - 0.60:
        status = AltitudeStatus.lower_axis_underreach
        why.append("O sample ficou abaixo da altitude arquitetónica esperada para o confronto.")
    else:
        status = AltitudeStatus.aligned_altitude
        why.append("A altitude dominante permaneceu alinhada com a expectativa arquitetónica do confronto.")
    return {
        "altitude_status": status,
        "dominant_altitude": round(dominant_altitude, 6),
        "expected_altitude": round(expected, 6),
        "dominant_path_types": dedupe_preserve_order(path_types),
        "why": dedupe_preserve_order(why),
    }


def diagnose_operations_profile(
    fragments: Sequence[FragmentRecord],
    score_vectors: Sequence[FragmentScoreVector],
    sample: SampleSelection,
) -> dict[str, Any]:
    selected_fragments, vector_map = _selected_fragment_objects(fragments, score_vectors, sample)
    counter: Counter[str] = Counter()
    inferable = False
    for fragment in selected_fragments:
        if fragment.argument_ids or fragment.regime_ids or fragment.path_ids or fragment.proposition_ids:
            inferable = True
        weight = max(vector_map[fragment.fragment_id].overall_selection_score, 0.0) + 0.01
        for op in fragment.operation_ids_inferred:
            counter[op] += max(1, int(math.ceil(weight * 3)))
    dominant_profile = [op for op, _ in counter.most_common(8)]
    return {
        "operations_counter": dict(counter),
        "dominant_operations_profile": dominant_profile,
        "inferable": inferable,
    }


def classify_alignment(
    declared_state: DeclaredDossierState,
    center_diag: dict[str, Any],
    corridor_diag: dict[str, Any],
    neighbor_diag: dict[str, Any],
    altitude_diag: dict[str, Any],
) -> tuple[AlignmentClassification, list[str]]:
    nuclear_overlap = float(center_diag.get("nuclear_ratio", 0.0))
    corridor_capture = corridor_diag.get("corridor_status") == CorridorStatus.corridor_capture
    neighbor_absorption = neighbor_diag.get("neighbor_status") == NeighborStatus.neighbor_absorption
    higher_axis_capture = altitude_diag.get("altitude_status") == AltitudeStatus.higher_axis_capture
    higher_axis_pressure = altitude_diag.get("altitude_status") == AltitudeStatus.higher_axis_pressure
    why: list[str] = []

    if higher_axis_capture or (corridor_capture and neighbor_absorption) or nuclear_overlap < 0.25:
        if nuclear_overlap < 0.25:
            why.append("O overlap nuclear ficou abaixo de 0.25.")
        if corridor_capture:
            why.append("O sample foi capturado por corredor não admissível como centro soberano.")
        if neighbor_absorption:
            why.append("O sample foi absorvido por núcleo vizinho já ocupado por outro dossier.")
        if higher_axis_capture:
            why.append("A altitude dominante capturou o centro do sample acima do esperado.")
        return AlignmentClassification.strongly_misaligned, dedupe_preserve_order(why)

    if nuclear_overlap >= 0.55 and not corridor_capture and not neighbor_absorption:
        why.append("Pelo menos 60% do peso do sample caiu no núcleo admissível, sem captura por corredor nem absorção vizinha.")
        if higher_axis_capture:
            why.append("Há altitude alta, mas o núcleo próprio manteve-se suficientemente dominante para impedir captura decisória.")
        return AlignmentClassification.aligned, dedupe_preserve_order(why)

    if nuclear_overlap >= 0.40 and not corridor_capture and not neighbor_absorption and not higher_axis_capture:
        why.append("Existe overlap relevante com o núcleo admissível, mas com pressão arquitetónica ou partilha de fundo ainda significativa.")
        if higher_axis_pressure:
            why.append("Há pressão de eixo arquitetónico mais alto, ainda sem captura plena.")
        return AlignmentClassification.pseudo_aligned, dedupe_preserve_order(why)

    why.append("O overlap nuclear ficou insuficiente para alinhamento estável do dossier vigente.")
    if corridor_capture:
        why.append("O centro dominante deslocou-se para corredor partilhado ou proibido.")
    if neighbor_absorption:
        why.append("O centro dominante coincide mais com dossier vizinho do que com o próprio confronto.")
    return AlignmentClassification.misaligned, dedupe_preserve_order(why)


def classify_autonomy(neighbor_diag: dict[str, Any], corridor_diag: dict[str, Any], center_diag: dict[str, Any], indices: NormativeIndices, runtime: RuntimeConfig) -> AutonomyClassification:
    if neighbor_diag.get("neighbor_status") == NeighborStatus.neighbor_absorption:
        return AutonomyClassification.neighbor_absorption
    nuclear_ratio = float(center_diag.get("nuclear_ratio", 0.0))
    background_ratio = float(center_diag.get("background_ratio", 0.0))
    expected = indices.cf_autonomy_expectation.get(runtime.confronto_id, "")
    if nuclear_ratio >= 0.48 and background_ratio <= 0.22:
        return AutonomyClassification.autonomous
    if nuclear_ratio >= 0.32 and background_ratio <= 0.35:
        return AutonomyClassification.autonomous_but_narrow
    if nuclear_ratio >= 0.22:
        return AutonomyClassification.shared_background_with_distinct_core
    return AutonomyClassification.indeterminate


def diagnose_architecture(
    runtime: RuntimeConfig,
    fragments: Sequence[FragmentRecord],
    score_vectors: Sequence[FragmentScoreVector],
    sample: SampleSelection,
    center: AdmissibleConfrontCenter,
    declared_state: DeclaredDossierState,
    indices: NormativeIndices,
) -> ArchitecturalDiagnosis:
    center_diag = diagnose_dominant_sample_center(fragments, score_vectors, sample, center)
    corridor_diag = diagnose_corridors(runtime, fragments, score_vectors, sample, center, indices)
    neighbor_diag = diagnose_neighbor_overlap(runtime, fragments, score_vectors, sample, center, indices)
    altitude_diag = diagnose_altitude(runtime, fragments, score_vectors, sample, indices)
    if altitude_diag.get("altitude_status") == AltitudeStatus.higher_axis_capture and float(center_diag.get("nuclear_ratio", 0.0)) >= 0.50 and corridor_diag.get("corridor_status") != CorridorStatus.corridor_capture:
        altitude_diag["altitude_status"] = AltitudeStatus.higher_axis_pressure
        altitude_diag["why"] = dedupe_preserve_order(_safe_list(altitude_diag.get("why")) + ["Apesar da altitude alta, o núcleo próprio manteve-se dominante; tratar como pressão e não como captura plena."])
    operations_diag = diagnose_operations_profile(fragments, score_vectors, sample)
    alignment, why_not_aligned = classify_alignment(declared_state, center_diag, corridor_diag, neighbor_diag, altitude_diag)
    autonomy = classify_autonomy(neighbor_diag, corridor_diag, center_diag, indices, runtime)

    notes: list[str] = []
    if runtime.confronto_id == "CF03" and "P23_P30" in corridor_diag.get("dominant_corridor", ""):
        notes.append("Guard CF03: corredor P23_P30 observado apenas como risco de captura, não como centro admissível.")
    if not operations_diag.get("operations_counter") and operations_diag.get("inferable"):
        notes.append("As operações estavam inferíveis, mas o contador veio vazio; isto exige warning/erro controlado na validação final.")

    return ArchitecturalDiagnosis(
        confronto_id=runtime.confronto_id,
        dominant_sample_center=center_diag.get("dominant_props", []),
        dominant_center_ratio=float(center_diag.get("nuclear_ratio", 0.0)),
        dominant_sample_props=center_diag.get("prop_weights", {}),
        corridor_status=corridor_diag["corridor_status"],
        dominant_corridor=_safe_str(corridor_diag.get("dominant_corridor")),
        neighbor_status=neighbor_diag["neighbor_status"],
        top_neighbor_cf=_safe_str(neighbor_diag.get("top_neighbor_cf")),
        top_neighbor_ratio=float(neighbor_diag.get("top_neighbor_ratio", 0.0)),
        altitude_status=altitude_diag["altitude_status"],
        dominant_altitude=float(altitude_diag.get("dominant_altitude", 0.0)),
        dominant_path_types=_safe_list(altitude_diag.get("dominant_path_types")),
        operations_counter={str(k): int(v) for k, v in _safe_dict(operations_diag.get("operations_counter")).items()},
        dominant_operations_profile=[x for x in _safe_list(operations_diag.get("dominant_operations_profile")) if isinstance(x, str)],
        alignment_classification=alignment,
        autonomy_classification=autonomy,
        why_not_aligned=[] if alignment == AlignmentClassification.aligned else dedupe_preserve_order(why_not_aligned),
        why_corridor_status=dedupe_preserve_order(_safe_list(corridor_diag.get("why"))),
        why_neighbor_status=dedupe_preserve_order(_safe_list(neighbor_diag.get("why"))),
        why_altitude_status=dedupe_preserve_order(_safe_list(altitude_diag.get("why"))),
        additional_notes=dedupe_preserve_order(notes + sample.selection_warnings),
    )


# =============================================================================
# ADJUDICAÇÃO METODOLÓGICA
# =============================================================================


def _decision_severity(decision: RecommendedMethodologicalDecision) -> int:
    order = {
        RecommendedMethodologicalDecision.preservar: 0,
        RecommendedMethodologicalDecision.preservar_com_restricoes: 1,
        RecommendedMethodologicalDecision.recentrar: 2,
        RecommendedMethodologicalDecision.substituir_estruturalmente: 3,
        RecommendedMethodologicalDecision.reabrir_com_revisao_humana: 4,
    }
    return order[decision]


def adjudicate_methodological_decision(
    runtime: RuntimeConfig,
    declared_state: DeclaredDossierState,
    center: AdmissibleConfrontCenter,
    diagnosis: ArchitecturalDiagnosis,
) -> MethodologicalDecision:
    rationale: list[str] = []
    why_not_preserve: list[str] = []
    decision_conflict_flag = False
    decision_conflict_reasons: list[str] = []

    if diagnosis.dominant_corridor and diagnosis.dominant_corridor in set(center.rejected_corridors):
        decision_conflict_flag = True
        decision_conflict_reasons.append("O corredor dominante do sample está explicitamente rejeitado pelo centro admissível do confronto.")

    if diagnosis.alignment_classification == AlignmentClassification.strongly_misaligned:
        decision = RecommendedMethodologicalDecision.substituir_estruturalmente
        rationale.append("O centro dominante já não coincide com o confronto vigente ou foi capturado por corredor/vizinho/eixo alto.")
        why_not_preserve.append("O dossier vigente não pode ser preservado porque o sample forte recai fora do seu centro admissível.")
    elif diagnosis.alignment_classification == AlignmentClassification.misaligned:
        if diagnosis.corridor_status == CorridorStatus.corridor_capture or diagnosis.neighbor_status == NeighborStatus.neighbor_absorption or diagnosis.altitude_status == AltitudeStatus.higher_axis_capture:
            decision = RecommendedMethodologicalDecision.substituir_estruturalmente
            rationale.append("O misalignment é agravado por captura estrutural, o que pede substituição em vez de simples recentramento.")
            why_not_preserve.append("A preservação manteria um enquadramento deslocado para corredor, vizinhança ou eixo superior.")
        else:
            decision = RecommendedMethodologicalDecision.recentrar
            rationale.append("Há material do confronto, mas o centro forte do dossier vigente precisa de recentramento explícito.")
            why_not_preserve.append("A preservação esconderia deslocação relevante do centro dominante.")
    elif diagnosis.alignment_classification == AlignmentClassification.pseudo_aligned:
        if diagnosis.corridor_status == CorridorStatus.corridor_capture or diagnosis.neighbor_status == NeighborStatus.neighbor_absorption or diagnosis.altitude_status == AltitudeStatus.higher_axis_capture:
            decision = RecommendedMethodologicalDecision.recentrar
            rationale.append("Existe núcleo próprio reconhecível, mas a pressão estrutural excede o que permite mera preservação restritiva.")
            why_not_preserve.append("Persistem pressões de captura incompatíveis com preservação simples do dossier vigente.")
        else:
            decision = RecommendedMethodologicalDecision.preservar_com_restricoes
            rationale.append("Existe núcleo próprio reconhecível, mas ainda com deslocações que exigem restrições e vigilância metodológica.")
            why_not_preserve.append("A preservação simples esconderia fundo partilhado, pressão de altitude ou necessidade de recentramento fino.")
    else:
        if diagnosis.autonomy_classification == AutonomyClassification.autonomous:
            decision = RecommendedMethodologicalDecision.preservar
            rationale.append("O sample ficou centrado no núcleo admissível do dossier vigente, sem sinais fortes de captura.")
        else:
            decision = RecommendedMethodologicalDecision.preservar_com_restricoes
            rationale.append("Há alinhamento aceitável com o dossier vigente, mas a autonomia é estreita ou o fundo partilhado continua alto.")
            why_not_preserve.append("Persistem constrições metodológicas que aconselham preservação com reservas.")

    confidence = 0.58
    confidence += 0.16 if diagnosis.alignment_classification in {AlignmentClassification.aligned, AlignmentClassification.strongly_misaligned} else 0.08
    confidence += 0.08 if not decision_conflict_flag else -0.06
    confidence = clamp(confidence)

    return MethodologicalDecision(
        confronto_id=runtime.confronto_id,
        recommended_methodological_decision=decision,
        confidence=round(confidence, 6),
        why_not_preserve=dedupe_preserve_order(why_not_preserve),
        decision_rationale=dedupe_preserve_order(rationale),
        decision_conflict_flag=decision_conflict_flag,
        decision_conflict_reasons=dedupe_preserve_order(decision_conflict_reasons),
        inferred_from_alignment=diagnosis.alignment_classification.value,
        preserved_nucleus_ids=list(center.promoted_proposition_ids),
    )


# =============================================================================
# VALIDAÇÃO INTERNA FINAL
# =============================================================================


def _build_central_projection(diagnosis: ArchitecturalDiagnosis, decision: MethodologicalDecision) -> dict[str, Any]:
    return {
        "alignment_classification": diagnosis.alignment_classification.value,
        "autonomy_classification": diagnosis.autonomy_classification.value,
        "recommended_methodological_decision": decision.recommended_methodological_decision.value,
        "dominant_corridor": diagnosis.dominant_corridor,
        "decision_conflict_flag": decision.decision_conflict_flag,
    }


def _render_core_projection_markdown(projection: dict[str, Any]) -> str:
    return (
        f"- alignment_classification: `{projection['alignment_classification']}`\n"
        f"- autonomy_classification: `{projection['autonomy_classification']}`\n"
        f"- recommended_methodological_decision: `{projection['recommended_methodological_decision']}`\n"
        f"- dominant_corridor: `{projection['dominant_corridor']}`\n"
        f"- decision_conflict_flag: `{projection['decision_conflict_flag']}`"
    )


def _render_core_projection_txt(projection: dict[str, Any]) -> str:
    return (
        f"alignment_classification={projection['alignment_classification']}\n"
        f"autonomy_classification={projection['autonomy_classification']}\n"
        f"recommended_methodological_decision={projection['recommended_methodological_decision']}\n"
        f"dominant_corridor={projection['dominant_corridor']}\n"
        f"decision_conflict_flag={projection['decision_conflict_flag']}"
    )


def validate_internal_consistency(
    runtime: RuntimeConfig,
    declared_state: DeclaredDossierState,
    center: AdmissibleConfrontCenter,
    diagnosis: ArchitecturalDiagnosis,
    decision: MethodologicalDecision,
) -> ConsistencyCheckResult:
    warnings: list[str] = []
    errors: list[str] = []
    conflict_flag = bool(decision.decision_conflict_flag)
    conflict_reasons: list[str] = list(decision.decision_conflict_reasons)

    # 1. corredor explicitamente rejeitado não pode governar silenciosamente a decisão.
    if diagnosis.dominant_corridor and diagnosis.dominant_corridor in set(center.rejected_corridors):
        conflict_flag = True
        conflict_reasons.append("O corredor dominante do sample foi explicitamente rejeitado pelo dossier/centro admissível.")

    # 2. corridor capture bloqueia qualquer preservação.
    if diagnosis.corridor_status == CorridorStatus.corridor_capture and decision.recommended_methodological_decision in {RecommendedMethodologicalDecision.preservar, RecommendedMethodologicalDecision.preservar_com_restricoes}:
        errors.append("Se corridor_status == corridor_capture, a decisão final não pode ser preservar nem preservar_com_restricoes.")

    # 3. higher axis capture bloqueia preservação.
    if diagnosis.altitude_status == AltitudeStatus.higher_axis_capture and decision.recommended_methodological_decision in {RecommendedMethodologicalDecision.preservar, RecommendedMethodologicalDecision.preservar_com_restricoes}:
        errors.append("Se altitude_status == higher_axis_capture, a decisão final não pode preservar o dossier.")

    # 4. neighbor absorption bloqueia preservação.
    if diagnosis.neighbor_status == NeighborStatus.neighbor_absorption and decision.recommended_methodological_decision in {RecommendedMethodologicalDecision.preservar, RecommendedMethodologicalDecision.preservar_com_restricoes}:
        errors.append("Se neighbor_status == neighbor_absorption, a preservação do dossier é proibida.")

    # 5. operations_counter vazio quando inferível.
    inferable = bool(diagnosis.dominant_operations_profile or diagnosis.operations_counter or center.promoted_argument_ids or center.promoted_regime_ids or center.promoted_percurso_ids or center.promoted_proposition_ids)
    if not diagnosis.operations_counter and inferable:
        msg = "operations_counter veio vazio apesar de existirem operações inferíveis a partir de regimes, argumentos, proposições ou percursos."
        warnings.append(msg)
        if runtime.strict_mode:
            errors.append(msg)

    # 6. tokens inválidos não podem contaminar campos canónicos.
    invalid_in_canonical = set(declared_state.invalid_id_tokens).intersection(
        set(declared_state.proposicoes_envolvidas)
        | set(declared_state.ancoragens)
        | set(declared_state.campos_do_real)
        | set(declared_state.pontes)
        | set(declared_state.capitulos)
        | set(declared_state.regimes)
        | set(declared_state.percursos)
        | set(declared_state.argumentos)
    )
    if invalid_in_canonical:
        errors.append(f"Tokens inválidos entraram em campos canónicos: {', '.join(sorted(invalid_in_canonical))}")

    # 7. strongly_misaligned não pode terminar em preservação.
    if diagnosis.alignment_classification == AlignmentClassification.strongly_misaligned and decision.recommended_methodological_decision in {RecommendedMethodologicalDecision.preservar, RecommendedMethodologicalDecision.preservar_com_restricoes}:
        errors.append("strongly_misaligned não pode terminar em preservar nem em preservar_com_restricoes.")

    # 8. conflito normativo explícito bloqueia preservação sem flag.
    if conflict_flag and not decision.decision_conflict_flag:
        decision.decision_conflict_flag = True
    if conflict_flag and decision.recommended_methodological_decision in {RecommendedMethodologicalDecision.preservar, RecommendedMethodologicalDecision.preservar_com_restricoes}:
        errors.append("Há conflito normativo explícito; a decisão não pode fechar em preservação sem reabertura/recentramento/substituição.")

    decision.decision_conflict_flag = conflict_flag
    decision.decision_conflict_reasons = dedupe_preserve_order(conflict_reasons)

    projection = _build_central_projection(diagnosis, decision)
    md_proj = _render_core_projection_markdown(projection)
    txt_proj = _render_core_projection_txt(projection)

    success = not errors
    if not success:
        raise InternalConsistencyError(" | ".join(errors))

    return ConsistencyCheckResult(
        success=success,
        warnings=dedupe_preserve_order(warnings),
        errors=errors,
        decision_conflict_flag=decision.decision_conflict_flag,
        decision_conflict_reasons=dedupe_preserve_order(decision.decision_conflict_reasons),
        central_projection=projection,
        markdown_projection=md_proj,
        txt_projection=txt_proj,
    )


# =============================================================================
# RENDERIZAÇÃO DE OUTPUTS
# =============================================================================


def _selected_vector_payload(sample: SampleSelection, vectors: Sequence[FragmentScoreVector]) -> list[dict[str, Any]]:
    vector_map = _vector_by_fragment_id(vectors)
    payload: list[dict[str, Any]] = []
    for fid in sample.selected_fragment_ids:
        vec = vector_map.get(fid)
        if vec is None:
            continue
        payload.append(
            {
                "fragment_id": fid,
                "base_strength": round(vec.base_strength, 6),
                "nuclearity": round(vec.nuclearity, 6),
                "mediationality": round(vec.mediationality, 6),
                "epistemic_weight": round(vec.epistemic_weight, 6),
                "shared_background": round(vec.shared_background, 6),
                "neighbor_overlap": round(vec.neighbor_overlap, 6),
                "corridor_support": round(vec.corridor_support, 6),
                "corridor_capture": round(vec.corridor_capture, 6),
                "higher_axis_capture": round(vec.higher_axis_capture, 6),
                "declared_alignment": round(vec.declared_alignment, 6),
                "overall_selection_score": round(vec.overall_selection_score, 6),
                "categories": list(vec.categories),
                "rationale": list(vec.rationale),
            }
        )
    return payload


def render_markdown_output(
    runtime: RuntimeConfig,
    declared_state: DeclaredDossierState,
    center: AdmissibleConfrontCenter,
    sample: SampleSelection,
    diagnosis: ArchitecturalDiagnosis,
    decision: MethodologicalDecision,
    consistency: ConsistencyCheckResult,
    self_checks: Optional[SelfCheckReport],
) -> str:
    try:
        lines = [
            f"# {runtime.confronto_id} — Diagnóstico metodológico v4",
            "",
            "## Projeção central",
            consistency.markdown_projection,
            "",
            "## Dossier declarado",
            f"- título: {declared_state.dossier_title}",
            f"- pergunta_central: {declared_state.question_central}",
            f"- redecision_class: `{declared_state.redecision_class.value}`",
            f"- proposicoes_nucleares_centrais: {', '.join(declared_state.proposicoes_nucleares_centrais) or '∅'}",
            f"- proposicoes_background: {', '.join(declared_state.proposicoes_background) or '∅'}",
            f"- proposicoes_rejeitadas: {', '.join(declared_state.proposicoes_rejeitadas) or '∅'}",
            f"- invalid_id_tokens: {', '.join(declared_state.invalid_id_tokens) or '∅'}",
            "",
            "## Centro admissível do confronto",
            f"- promovidas: {', '.join(center.promoted_proposition_ids) or '∅'}",
            f"- promovidas_fracas: {', '.join(center.promoted_weak_ids) or '∅'}",
            f"- fundo: {', '.join(center.background_proposition_ids) or '∅'}",
            f"- rejeitadas: {', '.join(center.rejected_proposition_ids) or '∅'}",
            f"- corredores_admissiveis: {', '.join(center.admissible_corridors) or '∅'}",
            f"- corredores_rejeitados: {', '.join(center.rejected_corridors) or '∅'}",
            "",
            "## Sample fragmentário",
            f"- selected_fragment_ids: {', '.join(sample.selected_fragment_ids) or '∅'}",
            f"- cobertura: {json.dumps(sample.coverage_summary, ensure_ascii=False)}",
            f"- nuclear_fragments: {', '.join(sample.nuclear_fragments) or '∅'}",
            f"- mediational_fragments: {', '.join(sample.mediational_fragments) or '∅'}",
            f"- background_fragments: {', '.join(sample.background_fragments) or '∅'}",
            f"- capture_risk_fragments: {', '.join(sample.capture_risk_fragments) or '∅'}",
            f"- contradictory_fragments: {', '.join(sample.contradictory_fragments) or '∅'}",
            "",
            "## Diagnóstico arquitetónico",
            f"- dominant_sample_center: {', '.join(diagnosis.dominant_sample_center) or '∅'}",
            f"- dominant_center_ratio: {diagnosis.dominant_center_ratio}",
            f"- corridor_status: `{diagnosis.corridor_status.value}`",
            f"- dominant_corridor: `{diagnosis.dominant_corridor}`",
            f"- neighbor_status: `{diagnosis.neighbor_status.value}`",
            f"- top_neighbor_cf: `{diagnosis.top_neighbor_cf}`",
            f"- top_neighbor_ratio: {diagnosis.top_neighbor_ratio}",
            f"- altitude_status: `{diagnosis.altitude_status.value}`",
            f"- dominant_altitude: {diagnosis.dominant_altitude}",
            f"- dominant_operations_profile: {', '.join(diagnosis.dominant_operations_profile) or '∅'}",
            f"- why_not_aligned: {json.dumps(diagnosis.why_not_aligned, ensure_ascii=False)}",
            f"- why_corridor_status: {json.dumps(diagnosis.why_corridor_status, ensure_ascii=False)}",
            f"- why_neighbor_status: {json.dumps(diagnosis.why_neighbor_status, ensure_ascii=False)}",
            f"- why_altitude_status: {json.dumps(diagnosis.why_altitude_status, ensure_ascii=False)}",
            "",
            "## Decisão metodológica",
            f"- recommended_methodological_decision: `{decision.recommended_methodological_decision.value}`",
            f"- confidence: {decision.confidence}",
            f"- why_not_preserve: {json.dumps(decision.why_not_preserve, ensure_ascii=False)}",
            f"- decision_rationale: {json.dumps(decision.decision_rationale, ensure_ascii=False)}",
            f"- decision_conflict_flag: {decision.decision_conflict_flag}",
            f"- decision_conflict_reasons: {json.dumps(decision.decision_conflict_reasons, ensure_ascii=False)}",
            "",
            "## Consistency checks",
            f"- warnings: {json.dumps(consistency.warnings, ensure_ascii=False)}",
            f"- errors: {json.dumps(consistency.errors, ensure_ascii=False)}",
        ]
        if self_checks is not None:
            lines.extend([
                "",
                "## Self-checks",
                f"- executed: {self_checks.executed}",
                f"- passed: {self_checks.passed}",
                f"- failures: {json.dumps(self_checks.failures, ensure_ascii=False)}",
                f"- warnings: {json.dumps(self_checks.warnings, ensure_ascii=False)}",
            ])
        return "\n".join(lines).strip() + "\n"
    except Exception as exc:
        raise OutputRenderingError(f"Falha ao renderizar Markdown: {exc}") from exc


def render_txt_output(
    runtime: RuntimeConfig,
    declared_state: DeclaredDossierState,
    center: AdmissibleConfrontCenter,
    sample: SampleSelection,
    diagnosis: ArchitecturalDiagnosis,
    decision: MethodologicalDecision,
    consistency: ConsistencyCheckResult,
    self_checks: Optional[SelfCheckReport],
) -> str:
    try:
        parts = [
            f"RELATÓRIO DIAGNÓSTICO METODOLÓGICO — {runtime.confronto_id}\n",
            consistency.txt_projection,
            "",
            f"redecision_class={declared_state.redecision_class.value}",
            f"promoted_center={','.join(center.promoted_proposition_ids)}",
            f"background_center={','.join(center.background_proposition_ids)}",
            f"rejected_center={','.join(center.rejected_proposition_ids)}",
            f"selected_fragment_ids={','.join(sample.selected_fragment_ids)}",
            f"coverage_summary={json.dumps(sample.coverage_summary, ensure_ascii=False)}",
            f"why_not_aligned={json.dumps(diagnosis.why_not_aligned, ensure_ascii=False)}",
            f"why_corridor_status={json.dumps(diagnosis.why_corridor_status, ensure_ascii=False)}",
            f"why_neighbor_status={json.dumps(diagnosis.why_neighbor_status, ensure_ascii=False)}",
            f"why_altitude_status={json.dumps(diagnosis.why_altitude_status, ensure_ascii=False)}",
            f"why_not_preserve={json.dumps(decision.why_not_preserve, ensure_ascii=False)}",
            f"decision_rationale={json.dumps(decision.decision_rationale, ensure_ascii=False)}",
            f"consistency_warnings={json.dumps(consistency.warnings, ensure_ascii=False)}",
            f"consistency_errors={json.dumps(consistency.errors, ensure_ascii=False)}",
        ]
        if self_checks is not None:
            parts.extend([
                f"self_checks_passed={self_checks.passed}",
                f"self_checks_failures={json.dumps(self_checks.failures, ensure_ascii=False)}",
            ])
        return "\n".join(parts).strip() + "\n"
    except Exception as exc:
        raise OutputRenderingError(f"Falha ao renderizar TXT: {exc}") from exc


def build_output_bundle(
    runtime: RuntimeConfig,
    bundle: SourceBundle,
    declared_state: DeclaredDossierState,
    center: AdmissibleConfrontCenter,
    sample: SampleSelection,
    score_vectors: Sequence[FragmentScoreVector],
    diagnosis: ArchitecturalDiagnosis,
    decision: MethodologicalDecision,
    consistency: ConsistencyCheckResult,
    self_checks: Optional[SelfCheckReport] = None,
) -> OutputBundle:
    json_payload = {
        "metadata": {
            "script_name": SCRIPT_NAME,
            "generated_at_utc": utc_now_iso(),
            "confronto_id": runtime.confronto_id,
            "mode": "local_auditavel_sem_api",
            "strict_mode": runtime.strict_mode,
            "sample_size": runtime.sample_size,
            "top_k_scoring": runtime.top_k_scoring,
        },
        "inputs_used": {
            key: relpath_str(path, runtime.project_root) for key, path in bundle.paths.items()
        },
        "normative_precedence": [{"source": src, "strength": strength} for src, strength in NORMATIVE_PRECEDENCE],
        "dossier_declared_state": dataclass_to_jsonable(declared_state),
        "admissible_confront_center": dataclass_to_jsonable(center),
        "fragment_sample": {
            **dataclass_to_jsonable(sample),
            "selected_fragment_vectors": _selected_vector_payload(sample, score_vectors),
        },
        "architectural_diagnosis": dataclass_to_jsonable(diagnosis),
        "methodological_decision": dataclass_to_jsonable(decision),
        "consistency_checks": dataclass_to_jsonable(consistency),
        "self_checks": dataclass_to_jsonable(self_checks) if self_checks is not None else None,
    }

    output_paths = {
        "json": runtime.output_dir / f"{runtime.confronto_id}_diagnostico_metodologico_v4.json",
        "md": runtime.output_dir / f"{runtime.confronto_id}_diagnostico_metodologico_v4.md",
        "txt": runtime.output_dir / f"relatorio_diagnostico_metodologico_{runtime.confronto_id}_v4.txt",
    }

    markdown_text = render_markdown_output(runtime, declared_state, center, sample, diagnosis, decision, consistency, self_checks)
    txt_text = render_txt_output(runtime, declared_state, center, sample, diagnosis, decision, consistency, self_checks)

    # Regra 7: os campos centrais coincidem porque nascem da mesma projeção validada.
    projection = consistency.central_projection
    if json_payload["architectural_diagnosis"]["alignment_classification"] != projection["alignment_classification"]:
        raise OutputRenderingError("O payload JSON divergiu da projeção central validada.")
    if json_payload["methodological_decision"]["recommended_methodological_decision"] != projection["recommended_methodological_decision"]:
        raise OutputRenderingError("A decisão JSON divergiu da projeção central validada.")

    return OutputBundle(json_payload=json_payload, markdown_text=markdown_text, txt_text=txt_text, output_paths=output_paths)


# =============================================================================
# ESCRITA DOS OUTPUTS
# =============================================================================


def write_outputs(bundle: OutputBundle) -> None:
    write_json(bundle.output_paths["json"], bundle.json_payload)
    write_text(bundle.output_paths["md"], bundle.markdown_text)
    write_text(bundle.output_paths["txt"], bundle.txt_text)


# =============================================================================
# SELF-CHECKS
# =============================================================================


def self_check_no_lexical_token_contamination() -> None:
    runtime = RuntimeConfig(
        confronto_id="CF03",
        project_root=Path("/tmp"),
        dossier_path=Path("/tmp/CF03_dossier.md"),
        output_dir=Path("/tmp/out"),
        config_path=None,
        base_fragment_path=None,
        strict_mode=False,
        run_self_checks=True,
        sample_size=10,
        top_k_scoring=20,
        weights=ScoreWeights(),
        verbose=False,
    )
    indices = NormativeIndices(
        proposition_ids={"P14", "P15"}, bridge_ids=set(), anchorage_ids=set(), field_ids=set(),
        chapter_ids=set(), regime_ids=set(), path_ids=set(), argument_ids=set(), cf_ids={"CF03"},
        proposition_to_chapters={}, proposition_to_regimes={}, proposition_to_paths={}, proposition_to_arguments={}, proposition_to_operations={},
        proposition_dependencies={}, chapter_to_regimes={}, chapter_to_paths={}, chapter_to_operations={},
        argument_to_operations={}, argument_to_regimes={}, argument_to_paths={}, argument_to_chapters={},
        path_to_type={}, path_to_required_paths={}, corridors=dict(CORRIDOR_DEFINITIONS), matrix_by_cf={}, adjudication_by_cf={},
        cf_neighbor_map=dict(DEFAULT_NEIGHBOR_DOSSIERS), cf_sensitive_corridors=dict(DEFAULT_SENSITIVE_CORRIDORS),
        cf_altitude_expectation=dict(DEFAULT_ALTITUDE_EXPECTATION), cf_autonomy_expectation=dict(DEFAULT_AUTONOMY_EXPECTATION),
        ramo_to_arguments={}, warnings=[]
    )
    bundle = SourceBundle(data={}, paths={}, warnings=[], optional_missing=[])
    state = parse_declared_dossier_state(runtime, "# CF03\n\n## Proposições envolvidas\nPassagem, Pergunta, Por, preservar_com_restricoes, precisa_revisao_humana, P14, P15\n", bundle, indices)
    assert state.proposicoes_envolvidas == ["P14", "P15"]
    assert "Passagem" in state.invalid_id_tokens
    assert "Pergunta" in state.invalid_id_tokens
    assert "preservar_com_restricoes" in state.invalid_id_tokens


def self_check_operations_counter_not_empty_when_inferable() -> None:
    fragment = FragmentRecord(
        fragment_id="FTEST_001", source_mode="self_check", text="texto", proposition_weights={"P14": 1.0}, proposition_ids=["P14"],
        chapter_ids=["CAP_15_CONSCIENCIA"], regime_ids=["REGIME_CRITICA_REFLEXIVIDADE"], path_ids=["P_EIXO_SIMBOLICO_MEDIACIONAL"],
        argument_ids=["ARG_TESTE"], corridor_ids=["P14_P22"], operation_ids_inferred=["OP_IDENTIFICACAO_MEDIACAO"], impact_effect="explicita",
        impact_action="densificar", impact_priority="alta", confidence_score=0.9, validation_state="valido", centrality="dominante", source_labels=[], metadata={}
    )
    vector = FragmentScoreVector("FTEST_001", 0.8, 0.7, 0.4, 0.1, 0.0, 0.0, 0.6, 0.1, 0.0, 0.7, 0.7)
    sample = SampleSelection(["FTEST_001"], [], {}, ["FTEST_001"], [], [], [], [], [], [])
    diag = diagnose_operations_profile([fragment], [vector], sample)
    assert diag["operations_counter"]
    assert diag["dominant_operations_profile"]


def self_check_corridor_capture_blocks_preserve() -> None:
    runtime = RuntimeConfig("CF03", Path("/tmp"), Path("/tmp/x"), Path("/tmp/y"), None, None, False, False, 10, 20, ScoreWeights(), False)
    declared = DeclaredDossierState(
        confronto_id="CF03", dossier_title="x", question_central="q", descricao_do_confronto="d", tese_canonica_provisoria="t",
        proposicoes_envolvidas=[], proposicoes_nucleares_centrais=[], proposicoes_background=[], proposicoes_rejeitadas=[],
        pontes=[], ancoragens=[], campos_do_real=[], capitulos=[], regimes=[], percursos=[], argumentos=[], declared_profiles=[],
        invalid_id_tokens=[], parsing_warnings=[], redecision_class=DecisionRedecisionClass.none, redecision_evidence=[],
        config_defaults={}, section_trace=[]
    )
    center = AdmissibleConfrontCenter("CF03", ["P14"], [], ["P14"], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [])
    diagnosis = ArchitecturalDiagnosis(
        confronto_id="CF03", dominant_sample_center=["P23"], dominant_center_ratio=0.1, dominant_sample_props={},
        corridor_status=CorridorStatus.corridor_capture, dominant_corridor="P23_P30", neighbor_status=NeighborStatus.shared_background,
        top_neighbor_cf="CF04", top_neighbor_ratio=0.3, altitude_status=AltitudeStatus.higher_axis_pressure, dominant_altitude=3.3,
        dominant_path_types=[], operations_counter={"OP_X": 1}, dominant_operations_profile=["OP_X"],
        alignment_classification=AlignmentClassification.pseudo_aligned, autonomy_classification=AutonomyClassification.shared_background_with_distinct_core,
        why_not_aligned=[], why_corridor_status=[], why_neighbor_status=[], why_altitude_status=[], additional_notes=[]
    )
    decision = MethodologicalDecision("CF03", RecommendedMethodologicalDecision.preservar_com_restricoes, 0.7, [], [], False, [], "pseudo_aligned", ["P14"])
    try:
        validate_internal_consistency(runtime, declared, center, diagnosis, decision)
    except InternalConsistencyError:
        return
    raise AssertionError("corridor_capture deveria bloquear preservar_com_restricoes")


def self_check_decision_conflict_flag_opens() -> None:
    runtime = RuntimeConfig("CF03", Path("/tmp"), Path("/tmp/x"), Path("/tmp/y"), None, None, False, False, 10, 20, ScoreWeights(), False)
    declared = DeclaredDossierState(
        confronto_id="CF03", dossier_title="x", question_central="q", descricao_do_confronto="d", tese_canonica_provisoria="t",
        proposicoes_envolvidas=["P14", "P15"], proposicoes_nucleares_centrais=["P14", "P15"], proposicoes_background=["P01"], proposicoes_rejeitadas=["P02", "P05"],
        pontes=[], ancoragens=[], campos_do_real=[], capitulos=[], regimes=[], percursos=[], argumentos=[], declared_profiles=[],
        invalid_id_tokens=[], parsing_warnings=[], redecision_class=DecisionRedecisionClass.structural_substitution, redecision_evidence=["explicita"],
        config_defaults={}, section_trace=[]
    )
    center = AdmissibleConfrontCenter(
        confronto_id="CF03",
        promoted_proposition_ids=["P14"], promoted_weak_ids=[], nuclear_expanded_ids=["P14"], background_proposition_ids=["P01"], rejected_proposition_ids=["P02"],
        promoted_bridge_ids=[], promoted_anchorage_ids=[], promoted_field_ids=[], promoted_chapter_ids=[], promoted_regime_ids=[], promoted_percurso_ids=[], promoted_argument_ids=[],
        admissible_corridors=["P14_P22"], rejected_corridors=["P23_P30"], source_contributions=[], promoted_reasons={}, rejected_reasons={}, notes=[]
    )
    diagnosis = ArchitecturalDiagnosis(
        confronto_id="CF03", dominant_sample_center=["P23"], dominant_center_ratio=0.1, dominant_sample_props={}, corridor_status=CorridorStatus.corridor_capture,
        dominant_corridor="P23_P30", neighbor_status=NeighborStatus.shared_background, top_neighbor_cf="CF04", top_neighbor_ratio=0.3, altitude_status=AltitudeStatus.higher_axis_pressure,
        dominant_altitude=3.3, dominant_path_types=[], operations_counter={"OP_X": 1}, dominant_operations_profile=["OP_X"],
        alignment_classification=AlignmentClassification.misaligned, autonomy_classification=AutonomyClassification.shared_background_with_distinct_core,
        why_not_aligned=[], why_corridor_status=[], why_neighbor_status=[], why_altitude_status=[], additional_notes=[]
    )
    decision = MethodologicalDecision("CF03", RecommendedMethodologicalDecision.recentrar, 0.6, [], [], False, [], "misaligned", ["P14"])
    result = validate_internal_consistency(runtime, declared, center, diagnosis, decision)
    assert result.decision_conflict_flag is True
    assert result.decision_conflict_reasons


def self_check_fragmentos_resegmentados_required() -> None:
    assert FILE_REQUIREMENTS.get("fragmentos_resegmentados", {}).get("required") is True


def self_check_path_alias_normalization() -> None:
    assert normalize_path_id("P_TRANSICAO_ANTROPOLOGIA_ONTOLOGICA") == "P_TRANSICAO_ANTROPOLOGICA_ONTOLOGICA"
    assert normalize_path_type("axial_transicional") == "axial_transitional"


def self_check_reformulated_dossier_can_align() -> None:
    declared = DeclaredDossierState(
        confronto_id="CF03", dossier_title="x", question_central="q", descricao_do_confronto="d", tese_canonica_provisoria="t",
        proposicoes_envolvidas=[], proposicoes_nucleares_centrais=["P14"], proposicoes_background=[], proposicoes_rejeitadas=[],
        pontes=[], ancoragens=[], campos_do_real=[], capitulos=[], regimes=[], percursos=[], argumentos=[], declared_profiles=[],
        invalid_id_tokens=[], parsing_warnings=[], redecision_class=DecisionRedecisionClass.structural_substitution, redecision_evidence=["explicita"],
        config_defaults={}, section_trace=[]
    )
    alignment, _ = classify_alignment(
        declared,
        {"nuclear_ratio": 0.72},
        {"corridor_status": CorridorStatus.corridor_support},
        {"neighbor_status": NeighborStatus.none},
        {"altitude_status": AltitudeStatus.aligned_altitude},
    )
    assert alignment in {AlignmentClassification.aligned, AlignmentClassification.pseudo_aligned}


def self_check_no_ad_hoc_tuples_in_core_pipeline() -> None:
    core_funcs = [
        build_runtime_config, load_source_bundle, build_normative_indices, parse_declared_dossier_state,
        load_fragment_records, build_admissible_confront_center, score_fragment, select_sample,
        diagnose_architecture, adjudicate_methodological_decision, validate_internal_consistency,
        build_output_bundle,
    ]
    for func in core_funcs:
        annotation = inspect.signature(func).return_annotation
        text = str(annotation)
        assert "tuple" not in text.lower() and "Tuple" not in text


def run_self_checks(runtime: RuntimeConfig) -> SelfCheckReport:
    checks: dict[str, bool] = {}
    failures: list[str] = []
    warnings: list[str] = []
    registry = {
        "self_check_no_lexical_token_contamination": self_check_no_lexical_token_contamination,
        "self_check_operations_counter_not_empty_when_inferable": self_check_operations_counter_not_empty_when_inferable,
        "self_check_corridor_capture_blocks_preserve": self_check_corridor_capture_blocks_preserve,
        "self_check_decision_conflict_flag_opens": self_check_decision_conflict_flag_opens,
        "self_check_no_ad_hoc_tuples_in_core_pipeline": self_check_no_ad_hoc_tuples_in_core_pipeline,
        "self_check_fragmentos_resegmentados_required": self_check_fragmentos_resegmentados_required,
        "self_check_path_alias_normalization": self_check_path_alias_normalization,
        "self_check_reformulated_dossier_can_align": self_check_reformulated_dossier_can_align,
    }
    for name, fn in registry.items():
        try:
            fn()
            checks[name] = True
        except Exception as exc:
            checks[name] = False
            failures.append(f"{name}: {exc}")
    passed = all(checks.values())
    if runtime.strict_mode and not passed:
        raise SelfCheckFailure(" | ".join(failures))
    return SelfCheckReport(executed=True, passed=passed, failures=failures, warnings=warnings, checks=checks)


# =============================================================================
# MAIN
# =============================================================================


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        # 1. parse_cli_args
        args = parse_cli_args(argv)
        # 2. build_runtime_config
        runtime = build_runtime_config(args)
        # 3. load_source_bundle
        source_bundle = load_source_bundle(runtime)
        # 4. build_normative_indices
        indices = build_normative_indices(runtime, source_bundle)
        # 5. read_dossier_text
        dossier_text = read_dossier_text(runtime)
        # 6. parse_declared_dossier_state
        declared_state = parse_declared_dossier_state(runtime, dossier_text, source_bundle, indices)
        # 7. load_fragment_records
        fragments = load_fragment_records(runtime, source_bundle, indices)
        # 8. infer_fragment_operations em cada fragmento
        fragments = [infer_fragment_operations(fragment, source_bundle, indices) for fragment in fragments]
        # 9. build_admissible_confront_center
        admissible_center = build_admissible_confront_center(runtime, source_bundle, indices, declared_state, fragments)
        # 10. score_fragment em cada fragmento
        neighbor_centers = _parse_neighbor_centers(runtime, indices)
        score_vectors = [
            score_fragment(fragment, admissible_center, declared_state, runtime, source_bundle, indices, neighbor_centers=neighbor_centers)
            for fragment in fragments
        ]
        # 11. select_sample
        sample = select_sample(runtime, fragments, score_vectors, admissible_center)
        # 12. diagnose_architecture
        diagnosis = diagnose_architecture(runtime, fragments, score_vectors, sample, admissible_center, declared_state, indices)
        # 13. adjudicate_methodological_decision
        decision = adjudicate_methodological_decision(runtime, declared_state, admissible_center, diagnosis)
        # 14. validate_internal_consistency
        consistency = validate_internal_consistency(runtime, declared_state, admissible_center, diagnosis, decision)
        # 15. build_output_bundle
        output_bundle = build_output_bundle(runtime, source_bundle, declared_state, admissible_center, sample, score_vectors, diagnosis, decision, consistency)
        # 16. write_outputs
        write_outputs(output_bundle)
        # 17. opcionalmente run_self_checks
        if runtime.run_self_checks:
            self_checks = run_self_checks(runtime)
            output_bundle = build_output_bundle(runtime, source_bundle, declared_state, admissible_center, sample, score_vectors, diagnosis, decision, consistency, self_checks=self_checks)
            write_outputs(output_bundle)
        # 18. return 0
        if runtime.verbose:
            print(f"[ok] JSON: {output_bundle.output_paths['json']}")
            print(f"[ok] MD:   {output_bundle.output_paths['md']}")
            print(f"[ok] TXT:  {output_bundle.output_paths['txt']}")
        return 0
    except DossierV4Error as exc:
        print(f"[erro] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - guarda final robusta
        print(f"[erro-interno] {exc}", file=sys.stderr)
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    raise SystemExit(main())