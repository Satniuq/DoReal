# CF09 — Diagnóstico metodológico v4

## Projeção central
- alignment_classification: `pseudo_aligned`
- autonomy_classification: `autonomous`
- recommended_methodological_decision: `preservar_com_restricoes`
- dominant_corridor: ``
- decision_conflict_flag: `False`

## Dossier declarado
- título: CF09 — Ação e liberdade situada
- pergunta_central: O que é agir no real e em que consiste a liberdade de um agente situado?
- redecision_class: `none`
- proposicoes_nucleares_centrais: ∅
- proposicoes_background: ∅
- proposicoes_rejeitadas: ∅
- invalid_id_tokens: acao_normatividade_e_formas_sociais, acao_pratica, campo_pratico_normativo, compatibilidade_geral, derivacao_normativa, instanciacao_regional, normatividade_etica, ontologia_dinamica, ontologia_estrutural, organizacao_biologica_e_sistemica, por_preencher

## Centro admissível do confronto
- promovidas: P04, P05, P07, P08, P36, P38, P39, P40, P41, P48
- promovidas_fracas: ∅
- fundo: ∅
- rejeitadas: ∅
- corredores_admissiveis: ∅
- corredores_rejeitados: ∅

## Sample fragmentário
- selected_fragment_ids: F0107_SEG_002, F0088_A01_SEG_003, F0024_SEG_002, F0003_SEG_001, F0065_A01_SEG_002, F0015_SEG_001, F0057_SEG_001, F0139_SEG_001, F0063_A02_SEG_002, F0007_SEG_001, F0042_SEG_001, F0207_SEG_001, F0115_A02_SEG_001, F0204_SEG_001, F0096_SEG_003
- representative_fragment_ids: F0107_SEG_002, F0088_A01_SEG_003, F0024_SEG_002, F0003_SEG_001, F0065_A01_SEG_002, F0015_SEG_001, F0057_SEG_001, F0139_SEG_001, F0063_A02_SEG_002, F0007_SEG_001, F0042_SEG_001, F0207_SEG_001, F0115_A02_SEG_001, F0204_SEG_001, F0096_SEG_003
- contrastive_fragment_ids: F0241_A19_SEG_004, F0241_A18_SEG_002, F0057_SEG_002, F0208_SEG_001, F0096_SEG_002, F0073_SEG_002, F0187_SEG_001
- support_fragment_ids: ∅
- cobertura: {"nuclear_count": 15, "support_count": 0, "background_count": 0, "capture_risk_count": 0, "contradictory_count": 0, "representative_zero_nuclearity_count": 0, "missing_promoted_count": 8, "selected_size": 15, "sample_size_target": 15}
- coverage_by_promoted_id: {"P04": 0.164194, "P05": 0.0, "P07": 0.055481, "P08": 0.0, "P36": 0.243423, "P38": 0.23902, "P39": 0.299399, "P40": 0.361355, "P41": 0.109466, "P48": 0.0}
- missing_promoted_ids: P04, P05, P07, P08, P36, P38, P41, P48
- nuclear_fragments: F0107_SEG_002, F0088_A01_SEG_003, F0024_SEG_002, F0003_SEG_001, F0065_A01_SEG_002, F0015_SEG_001, F0057_SEG_001, F0139_SEG_001, F0063_A02_SEG_002, F0007_SEG_001, F0042_SEG_001, F0207_SEG_001, F0115_A02_SEG_001, F0204_SEG_001, F0096_SEG_003
- mediational_fragments: ∅
- background_fragments: ∅
- capture_risk_fragments: ∅
- contradictory_fragments: ∅
- selection_quality_flags: ["missing_promoted_prop_coverage"]

## Diagnóstico arquitetónico
- dominant_sample_center: P40, P39, P36, P38, P04, P12, P11, P41
- dominant_center_ratio: 0.634223
- corridor_status: `none`
- dominant_corridor: ``
- neighbor_status: `autonomous`
- top_neighbor_cf: ``
- top_neighbor_ratio: 0.0
- altitude_status: `aligned_altitude`
- dominant_altitude: 3.39375
- dominant_operations_profile: OP_FIXACAO_CRITERIO, OP_SUBMISSAO_REAL, OP_IDENTIFICACAO_ADEQUACAO, OP_DERIVACAO_DEVER_SER, OP_IDENTIFICACAO_CRISTALIZACAO_SISTEMICA, OP_AFIRMACAO_ESTRUTURAL, OP_DESCRICAO_ESTRUTURAL
- why_not_aligned: ["Pelo menos 60% do peso do sample caiu no núcleo admissível, sem captura por corredor nem absorção vizinha.", "O sample representativo ainda não cobre suficientemente o núcleo promovido ou continua com risco estrutural de captura."]
- why_corridor_status: ["Nenhum corredor dominou o sample selecionado."]
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
- warnings: ["Cobertura insuficiente do núcleo promovido: P04, P05, P07, P08, P36, P38, P41, P48", "selection_quality_flag::missing_promoted_prop_coverage", "A decisão ficou mais benigna do que a qualidade do sample justifica; rever recentering/quality flags."]
- errors: []

## Self-checks
- executed: True
- passed: True
- failures: []
- warnings: []
