# CORPUS PÓS-LIMPEZA — resumo

- Gerado em: `2026-04-25T17:51:18+00:00`
- Script: `pos_processar_limpeza_fragmentos_v1.py`
- Entradas limpas: `535`
- Aprováveis: `329`
- Revisão humana: `206`
- Auditoria remanescente: `3`
- Não processados fora da auditoria: `0`

## Critério

- **Aprováveis**: limpezas com `sinalizar_revisao_humana=false`.
- **Revisão humana**: limpezas com `sinalizar_revisao_humana=true`.
- **Auditoria remanescente**: bundles que ficaram em `so_auditoria` e não entraram na limpeza.
- **Não processados**: bundles não limpos e não marcados como `so_auditoria`.

## Ficheiros gerados

- `corpus_limpo_todos.json`
- `corpus_limpo_aprovavel.json`
- `corpus_limpo_revisao.json`
- `corpus_auditoria_remanescente.json`
- `corpus_nao_processado.json`
- `corpus_limpo_aprovavel.md`
- `corpus_limpo_revisao.md`
- `corpus_auditoria_remanescente.md`
- `corpus_nao_processado.md`
- `manifesto_pos_limpeza.json`
