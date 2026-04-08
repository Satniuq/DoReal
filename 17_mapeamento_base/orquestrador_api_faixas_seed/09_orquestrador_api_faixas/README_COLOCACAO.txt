PACOTE INICIAL — ORQUESTRADOR API FAIXAS

Onde copiar:
- copia a pasta `09_orquestrador_api_faixas` para dentro de:
  `16_validacao_integral/`

Estrutura mínima final esperada:
- `16_validacao_integral/09_orquestrador_api_faixas/00_config`
- `16_validacao_integral/09_orquestrador_api_faixas/01_catalogos`
- `16_validacao_integral/09_orquestrador_api_faixas/03_estado_runtime`
- `16_validacao_integral/09_orquestrador_api_faixas/04_prompts_gerados/templates`

O que tens de ajustar primeiro:
1. `00_config/settings_runtime.json`
   - altera `project_root_placeholder` para o caminho real da tua máquina.
2. `00_config/manifesto_fontes.json`
   - confirma os `path_candidates`.
   - onde a tua arrumação divergir, deixa o caminho correto como 1.º candidato.
3. `03_estado_runtime/estado_pipeline.json`
   - este ficheiro já vem semeado com o estado atual até à faixa 05.

Ordem de arranque sugerida:
1. validar caminhos do manifesto
2. correr auditoria das fontes
3. resolver estado
4. gerar transição 05→06
5. publicar, fazer merge, reindexar

Nota:
- este pacote é base de arranque.
- não reescreve os canónicos.
- não substitui o juízo filosófico local.
