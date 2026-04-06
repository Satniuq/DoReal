# CF11 — Diagnóstico metodológico v4

## Projeção central
- alignment_classification: `pseudo_aligned`
- autonomy_classification: `autonomous`
- recommended_methodological_decision: `preservar_com_restricoes`
- dominant_corridor: `P46_P49`
- decision_conflict_flag: `False`

## Dossier declarado
- título: CF11 — Responsabilidade, dignidade e vida boa
- pergunta_central: Porque responde o ser reflexivo pelas suas atualizações e que fundamento têm dignidade e vida boa?
- redecision_class: `none`
- proposicoes_nucleares_centrais: ∅
- proposicoes_background: ∅
- proposicoes_rejeitadas: ∅
- invalid_id_tokens: acao_normatividade_e_formas_sociais, acao_pratica, biologia_do_organismo, campo_historico_cultural, campo_pratico_normativo, compatibilidade_forte, compatibilidade_geral, derivacao_normativa, determinacao_material, instanciacao_regional, normatividade_etica, ontologia_dinamica, ontologia_estrutural, ontologia_geral, por_preencher, pratica_normatividade_e_formas_historicas, vida_corporeidade_e_organizacao

## Centro admissível do confronto
- promovidas: P46, P47, P49, P50, P51
- promovidas_fracas: ∅
- fundo: ∅
- rejeitadas: ∅
- corredores_admissiveis: P42_P48, P46_P49
- corredores_rejeitados: ∅

## Sample fragmentário
- selected_fragment_ids: F0063_A01_SEG_003, F0009_SEG_001, F0241_A06_SEG_001, F0173_SEG_001, F0241_A26_SEG_003, F0105_A02_SEG_001, F0088_A02_SEG_003, F0084_A01_SEG_003, F0114_A02_SEG_002, F0016_SEG_001, F0159_SEG_001, F0066_SEG_002, F0008_SEG_001, F0241_A22_SEG_002, F0004_SEG_001
- representative_fragment_ids: F0063_A01_SEG_003, F0009_SEG_001, F0241_A06_SEG_001, F0173_SEG_001, F0241_A26_SEG_003, F0105_A02_SEG_001, F0088_A02_SEG_003, F0084_A01_SEG_003, F0114_A02_SEG_002, F0016_SEG_001, F0159_SEG_001, F0066_SEG_002, F0008_SEG_001, F0241_A22_SEG_002, F0004_SEG_001
- contrastive_fragment_ids: F0068_SEG_001, F0050_SEG_001, F0089_SEG_003, F0066_SEG_001, F0124_SEG_001, F0067_SEG_002, F0052_SEG_001
- support_fragment_ids: F0063_A01_SEG_003, F0009_SEG_001, F0241_A06_SEG_001, F0241_A26_SEG_003, F0105_A02_SEG_001, F0088_A02_SEG_003, F0084_A01_SEG_003, F0114_A02_SEG_002, F0016_SEG_001, F0159_SEG_001, F0066_SEG_002, F0008_SEG_001, F0241_A22_SEG_002, F0004_SEG_001
- cobertura: {"nuclear_count": 15, "support_count": 14, "background_count": 0, "capture_risk_count": 0, "contradictory_count": 0, "representative_zero_nuclearity_count": 0, "missing_promoted_count": 2, "selected_size": 15, "sample_size_target": 15}
- coverage_by_promoted_id: {"P46": 1.0, "P47": 1.0, "P49": 0.195134, "P50": 0.325532, "P51": 0.014721}
- missing_promoted_ids: P49, P51
- nuclear_fragments: F0063_A01_SEG_003, F0009_SEG_001, F0241_A06_SEG_001, F0173_SEG_001, F0241_A26_SEG_003, F0105_A02_SEG_001, F0088_A02_SEG_003, F0084_A01_SEG_003, F0114_A02_SEG_002, F0016_SEG_001, F0159_SEG_001, F0066_SEG_002, F0008_SEG_001, F0241_A22_SEG_002, F0004_SEG_001
- mediational_fragments: ∅
- background_fragments: ∅
- capture_risk_fragments: ∅
- contradictory_fragments: ∅
- selection_quality_flags: ["missing_promoted_prop_coverage"]

## Diagnóstico arquitetónico
- dominant_sample_center: P47, P46, P50, P49, P48, P40, P39, P33
- dominant_center_ratio: 0.881512
- corridor_status: `corridor_support`
- dominant_corridor: `P46_P49`
- neighbor_status: `autonomous`
- top_neighbor_cf: ``
- top_neighbor_ratio: 0.0
- altitude_status: `aligned_altitude`
- dominant_altitude: 3.12
- dominant_operations_profile: OP_FIXACAO_CRITERIO, OP_SUBMISSAO_REAL, OP_IDENTIFICACAO_ADEQUACAO, OP_IDENTIFICACAO_DEPENDENCIA, OP_RECONDUCAO_RELACIONAL, OP_DERIVACAO_DEVER_SER, OP_DESSUBSTANCIALIZACAO
- why_not_aligned: ["Pelo menos 60% do peso do sample caiu no núcleo admissível, sem captura por corredor nem absorção vizinha.", "O sample representativo ainda não cobre suficientemente o núcleo promovido ou continua com risco estrutural de captura."]
- why_corridor_status: ["Há corredor dominante, mas sem condições formais de captura."]
- why_neighbor_status: ["O overlap com dossiers vizinhos ficou abaixo do limiar significativo."]
- why_altitude_status: ["Não havia altitude esperada suficientemente definida para medir captura vertical."]

## Decisão metodológica
- recommended_methodological_decision: `preservar_com_restricoes`
- confidence: 0.74
- why_not_preserve: ["A preservação simples esconderia fundo partilhado, pressão de altitude ou necessidade de recentramento fino."]
- decision_rationale: ["Existe núcleo próprio reconhecível, mas ainda com deslocações que exigem restrições e vigilância metodológica."]
- decision_conflict_flag: False
- decision_conflict_reasons: []

## Consistency checks
- warnings: ["Cobertura insuficiente do núcleo promovido: P49, P51", "selection_quality_flag::missing_promoted_prop_coverage", "A decisão ficou mais benigna do que a qualidade do sample justifica; rever recentering/quality flags."]
- errors: []

## Self-checks
- executed: True
- passed: True
- failures: []
- warnings: []
