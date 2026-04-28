$ErrorActionPreference = "Stop"

# O script está dentro de 02_bruto.
# Logo, a raiz do projeto é a pasta acima.
$Bruto = $PSScriptRoot
$Root = Split-Path $Bruto -Parent

$Meta = Join-Path $Root "19_Meta_Schema\instancia_total_dividida"
$Pipe = Join-Path $Root "00_Pipeline_fragmentos"

$RunName = "run_nao_processados_novos__20260427_225500"
$RunDir = Join-Path $Pipe "03_runs\$RunName"

$RunName = "run_nao_processados_novos__20260427_225500"
$RunDir = Join-Path $Pipe "03_runs\$RunName"

# --------------------------------------------------------------------
# 1. Criar estrutura
# --------------------------------------------------------------------

$Dirs = @(
    "$Pipe",
    "$Pipe\00_inbox_novos",
    "$Pipe\01_scripts",
    "$Pipe\02_base_referencia",
    "$Pipe\02_base_referencia\instancia_total_dividida",
    "$Pipe\03_runs",
    "$RunDir",
    "$RunDir\00_input",
    "$RunDir\01_match",
    "$RunDir\02_containers",
    "$RunDir\03_resegmentacao",
    "$RunDir\04_validacao",
    "$RunDir\05_relatorios",
    "$Pipe\04_outputs_prontos_para_integrar",
    "$Pipe\90_arquivo"
)

foreach ($Dir in $Dirs) {
    New-Item -ItemType Directory -Path $Dir -Force | Out-Null
}

# --------------------------------------------------------------------
# 2. Criar inbox inicial
# --------------------------------------------------------------------

$InboxFile = Join-Path $Pipe "00_inbox_novos\fragmentos_novos.md"

if (!(Test-Path $InboxFile)) {
    New-Item -ItemType File -Path $InboxFile -Force | Out-Null
}

# --------------------------------------------------------------------
# 3. Copiar scripts para a pasta central
# --------------------------------------------------------------------

Copy-Item "$Bruto\verificar_nao_processados_contra_processados.py" "$Pipe\01_scripts\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\gerar_run_containers_nao_resegmentados_v4.py" "$Pipe\01_scripts\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\resegmentar_containers_semanticos_v6_openai.py" "$Pipe\01_scripts\" -Force -ErrorAction SilentlyContinue

# --------------------------------------------------------------------
# 4. Copiar base de referência
# --------------------------------------------------------------------

Copy-Item "$Bruto\fragmentos.md" "$Pipe\02_base_referencia\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\fragmentos_ja_processados.md" "$Pipe\02_base_referencia\" -Force -ErrorAction SilentlyContinue

Copy-Item "$Meta\03_entidades_fragmentos__parte_001.json" "$Pipe\02_base_referencia\instancia_total_dividida\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Meta\03_entidades_fragmentos__parte_002.json" "$Pipe\02_base_referencia\instancia_total_dividida\" -Force -ErrorAction SilentlyContinue

# --------------------------------------------------------------------
# 5. Arquivar inputs/match da run atual
# --------------------------------------------------------------------

Copy-Item "$Bruto\fragmentos_nao_processados__apenas_novos.md" "$RunDir\00_input\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\fragmentos_nao_processados.md" "$RunDir\00_input\fragmentos_nao_processados__origem.md" -Force -ErrorAction SilentlyContinue

Copy-Item "$Bruto\relatorio_match_nao_processados_vs_processados.md" "$RunDir\01_match\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\match_nao_processados_vs_processados.json" "$RunDir\01_match\" -Force -ErrorAction SilentlyContinue

# --------------------------------------------------------------------
# 6. Arquivar containers da run atual
# --------------------------------------------------------------------

Copy-Item "$Bruto\$RunName.md" "$RunDir\02_containers\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\containers_segmentacao__$RunName.json" "$RunDir\02_containers\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\relatorio_validacao_containers__$RunName.json" "$RunDir\04_validacao\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\$RunName`__relatorio.txt" "$RunDir\05_relatorios\" -Force -ErrorAction SilentlyContinue

# --------------------------------------------------------------------
# 7. Arquivar resegmentação da run atual
# --------------------------------------------------------------------

Copy-Item "$Bruto\fragmentos_resegmentados__$RunName.json" "$RunDir\03_resegmentacao\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\estado_resegmentador__$RunName.json" "$RunDir\03_resegmentacao\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\falhas_resegmentador__$RunName.json" "$RunDir\03_resegmentacao\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\relatorio_validacao_fragmentos__$RunName.json" "$RunDir\04_validacao\" -Force -ErrorAction SilentlyContinue
Copy-Item "$Bruto\relatorio_resegmentador__$RunName.txt" "$RunDir\05_relatorios\" -Force -ErrorAction SilentlyContinue

# --------------------------------------------------------------------
# 8. Copiar output principal para pronto a integrar
# --------------------------------------------------------------------

Copy-Item "$Bruto\fragmentos_resegmentados__$RunName.json" "$Pipe\04_outputs_prontos_para_integrar\" -Force -ErrorAction SilentlyContinue

# --------------------------------------------------------------------
# 9. Criar README inicial
# --------------------------------------------------------------------

$Readme = @"
# README_PIPELINE_FRAGMENTOS

## Estatuto

Esta pasta centraliza o pipeline limpo de entrada, deduplicação, geração de containers, resegmentação, validação e preparação de fragmentos para integração na base canónica.

A pasta antiga `02_bruto` permanece como base histórica e arquivo operacional anterior.

## Fluxo de trabalho

1. Colocar fragmentos novos em:

   `00_inbox_novos/fragmentos_novos.md`

2. Comparar contra a base processada.

3. Gerar ficheiro `fragmentos_nao_processados__apenas_novos.md`.

4. Gerar run de containers.

5. Ressegmentar containers.

6. Validar fragmentos resegmentados.

7. Colocar output validado em:

   `04_outputs_prontos_para_integrar/`

8. Só depois integrar na base canónica.

## Estado da primeira run organizada

Run:

`run_nao_processados_novos__20260427_225500`

Estado:

- containers: válidos
- fragmentos resegmentados: válidos
- fragmentos gerados: 51
- erros: 0
- falhas: 0

## Regra de prudência

Nenhum fragmento novo entra diretamente na base final sem passar por:

- match contra processados;
- geração de containers;
- resegmentação;
- validação;
- futura limpeza textual;
- cadência;
- tratamento filosófico;
- impacto no mapa;
- eventual mapeamento capitular.
"@

$Readme | Set-Content -Path "$Pipe\README_PIPELINE_FRAGMENTOS.md" -Encoding UTF8

Write-Host "========================================================================"
Write-Host "00_Pipeline_fragmentos montado com sucesso"
Write-Host "========================================================================"
Write-Host "Pasta: $Pipe"
Write-Host "Run arquivada: $RunDir"
Write-Host "Output pronto para integração: $Pipe\04_outputs_prontos_para_integrar"
Write-Host "========================================================================"