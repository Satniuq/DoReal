# limpeza_bundles_fragmentos_v2

Este script consome `lote_bundles_fragmentos.json` gerado pela v1 e produz saídas de limpeza por fragmento.

## O que faz
- lê `./output/lote_bundles_fragmentos.json` por omissão;
- processa por defeito apenas bundles em estado `limpavel` e `limpavel_com_cautela`;
- cria prompts diferentes para regime `direto` e `cautela`;
- escreve:
  - `./limpeza_output/fragmentos/*.prompt.json`
  - `./limpeza_output/fragmentos/*.limpo.json`
  - `./limpeza_output/manifesto_limpeza.json`
  - `./limpeza_output/limpezas_agregadas.json`
  - `./limpeza_output/relatorio_limpeza.md`
  - `./limpeza_output/erros_limpeza.json`

## Pré-requisitos
Instala o SDK oficial de Python:
```bash
pip install openai
```

Define a chave de API:
```powershell
setx OPENAI_API_KEY "a_tua_chave"
```

## Execução

### teste sem API
```bash
python limpar_bundles_fragmentos_v2.py --dry-run --max-items 10
```

### execução real
```bash
python limpar_bundles_fragmentos_v2.py
```

### só bundles cautela
```bash
python limpar_bundles_fragmentos_v2.py --only-state limpavel_com_cautela
```

### só alguns fragmentos
```bash
python limpar_bundles_fragmentos_v2.py --fragment-id F0021_SEG_001,F0021_SEG_002
```

### reprocessar ficheiros já existentes
```bash
python limpar_bundles_fragmentos_v2.py --overwrite
```

## Observações
- o modelo default é `gpt-5.4`, mas pode ser trocado com `--model` ou `OPENAI_MODEL`;
- `so_auditoria` fica fora por omissão;
- o script guarda também os prompts por fragmento para auditoria.
