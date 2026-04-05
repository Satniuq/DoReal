# CF02 — Diagnóstico metodológico v4

## Projeção central
- alignment_classification: `pseudo_aligned`
- autonomy_classification: `autonomous`
- recommended_methodological_decision: `preservar_com_restricoes`
- dominant_corridor: `P23_P30`
- decision_conflict_flag: `False`

## Dossier declarado
- título: CF02 — Manifestação, aparecer e presença
- pergunta_central: Como aparece o real e que estatuto têm manifestação, presença e apreensão?
- redecision_class: `none`
- proposicoes_nucleares_centrais: ∅
- proposicoes_background: ∅
- proposicoes_rejeitadas: ∅
- invalid_id_tokens: biologia_do_organismo, campo_de_articulacao, ciencia_cognitiva, cognicao_representacao_e_reflexividade, compatibilidade_geral, determinacao_material, determinacao_material_necessaria, ontologia_geral, por_preencher, suporte_empirico_relevante, vida_corporeidade_e_emergencia_cognitiva

## Centro admissível do confronto
- promovidas: P16, P23, P24
- promovidas_fracas: ∅
- fundo: ∅
- rejeitadas: ∅
- corredores_admissiveis: P23_P30
- corredores_rejeitados: ∅

## Sample fragmentário
- selected_fragment_ids: F0140_SEG_001, F0076_SEG_002, F0241_A23_SEG_002, F0240_SEG_001, F0193_SEG_001, F0171_SEG_001, F0081_SEG_001, F0116_SEG_004, F0241_A23_SEG_001, F0219_SEG_001, F0228_SEG_001, F0115_A02_SEG_002, F0221_SEG_001, F0083_SEG_001, F0241_A23_SEG_003
- representative_fragment_ids: F0140_SEG_001, F0076_SEG_002, F0241_A23_SEG_002, F0240_SEG_001, F0193_SEG_001, F0171_SEG_001, F0081_SEG_001, F0116_SEG_004, F0241_A23_SEG_001, F0219_SEG_001, F0228_SEG_001, F0115_A02_SEG_002, F0221_SEG_001, F0083_SEG_001, F0241_A23_SEG_003
- contrastive_fragment_ids: F0077_SEG_002, F0119_A02_SEG_002, F0121_A01_SEG_001, F0241_A24_SEG_001, F0241_A22_SEG_004, F0098_A01_SEG_003, F0115_A01_SEG_003
- support_fragment_ids: F0076_SEG_002, F0241_A23_SEG_002, F0240_SEG_001, F0116_SEG_004, F0241_A23_SEG_001, F0219_SEG_001, F0221_SEG_001, F0083_SEG_001
- cobertura: {"nuclear_count": 15, "support_count": 8, "background_count": 0, "capture_risk_count": 1, "contradictory_count": 0, "representative_zero_nuclearity_count": 0, "missing_promoted_count": 1, "selected_size": 15, "sample_size_target": 15}
- coverage_by_promoted_id: {"P16": 0.017255, "P23": 0.34074, "P24": 0.578289}
- missing_promoted_ids: P16
- nuclear_fragments: F0140_SEG_001, F0076_SEG_002, F0241_A23_SEG_002, F0240_SEG_001, F0193_SEG_001, F0171_SEG_001, F0081_SEG_001, F0116_SEG_004, F0241_A23_SEG_001, F0219_SEG_001, F0228_SEG_001, F0115_A02_SEG_002, F0221_SEG_001, F0083_SEG_001, F0241_A23_SEG_003
- mediational_fragments: ∅
- background_fragments: ∅
- capture_risk_fragments: F0083_SEG_001
- contradictory_fragments: ∅
- selection_quality_flags: ["missing_promoted_prop_coverage", "representative_sample_contains_capture_risk"]

## Diagnóstico arquitetónico
- dominant_sample_center: P24, P23, P28, P25, P33, P16, P49, P12
- dominant_center_ratio: 0.713055
- corridor_status: `corridor_support`
- dominant_corridor: `P23_P30`
- neighbor_status: `autonomous`
- top_neighbor_cf: ``
- top_neighbor_ratio: 0.0
- altitude_status: `aligned_altitude`
- dominant_altitude: 2.472727
- dominant_operations_profile: OP_IDENTIFICACAO_DEPENDENCIA, OP_RECONDUCAO_RELACIONAL, OP_DESSUBSTANCIALIZACAO, OP_FIXACAO_CRITERIO, OP_SUBMISSAO_REAL, OP_DERIVACAO_DEVER_SER, OP_AFIRMACAO_ESTRUTURAL, OP_IDENTIFICACAO_CRISTALIZACAO_SISTEMICA
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
- warnings: ["O sample representativo ainda contém fragmentos com risco estrutural de captura: F0083_SEG_001", "Cobertura insuficiente do núcleo promovido: P16", "selection_quality_flag::missing_promoted_prop_coverage", "selection_quality_flag::representative_sample_contains_capture_risk", "A decisão ficou mais benigna do que a qualidade do sample justifica; rever recentering/quality flags."]
- errors: []
