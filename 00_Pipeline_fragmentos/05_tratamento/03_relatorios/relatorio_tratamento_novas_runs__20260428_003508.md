# Relatório — tratamento incremental de fragmentos resegmentados

## Estado

- Estado: `incremental_tratado_nao_integrado_na_base_canonica`
- Gerado em UTC: `2026-04-27T23:35:08Z`

## Inputs

- `C:\Users\vanes\DoReal_Casa_Local\DoReal\00_Pipeline_fragmentos\04_outputs_prontos_para_integrar\fragmentos_resegmentados__run_fragmentos_novos__20260427_234128.json`
- `C:\Users\vanes\DoReal_Casa_Local\DoReal\00_Pipeline_fragmentos\04_outputs_prontos_para_integrar\fragmentos_resegmentados__run_nao_processados_novos__20260427_225500.json`

## Estatísticas

- Processados/atualizados: 3
- Ignorados: 0
- Cache: 0
- Chamadas API: 3
- Fallback local: 0
- Erros: 0

## Outputs

- `03_entidades_fragmentos__parte_003.json` — fragmentos: 3 — offsets: 538–541

## Fragmentos tratados/atualizados

- `F0335_SEG_001` — validação: `valido_com_cautela` — confiança: `media`
- `F0335_SEG_002` — validação: `valido_com_cautela` — confiança: `media`
- `F0335_SEG_003` — validação: `valido_com_cautela` — confiança: `alta`

## Nota

Esta saída ainda não substitui a instância canónica. Serve como parte incremental tratada, a validar antes de integração definitiva.