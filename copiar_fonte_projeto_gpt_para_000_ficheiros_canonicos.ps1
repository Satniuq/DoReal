$root = "C:\Users\vanes\DoReal_Casa_Local\DoReal"
$dest = "C:\Users\vanes\DoReal_Casa_Local\DoReal\000_ficheiros_canonicos"

New-Item -ItemType Directory -Force -Path $dest | Out-Null

$filenames = @(
    "proposicoes_nucleares_enriquecidas_v1.json",
    "matriz_confronto_filosofico_v1.json",
    "adjudicacao_confrontos_filosoficos_restrita_v2.json",
    "arvore_do_pensamento_v1.json",
    "impacto_fragmentos_no_mapa.json",
    "02_mapa_dedutivo_arquitetura_fragmentos.json",
    "mapa_dedutivo_canonico_final__vfinal_corrente.json",
    "arvore_do_pensamento_v1_fecho_superior.json",
    "adjudicacao_argumentos_api_v1.json",
    "relatorio_revisao_argumentos_restritiva_v1.txt",
    "grafo_resumo.txt",
    "argumentos_unificados.json",
    "D_TODOS_UNIFICADOS.txt",
    "indice_sequencial.json",
    "mapa_integral_do_indice.json",
    "meta_indice.json",
    "meta_referencia_do_percurso.json",
    "decisoes_canonicas_intermedias_consolidado_candidato.json",
    "operacoes.json",
    "todos_os_conceitos.json",
    "proposicoes.json",
    "indice_de_percursos.json",
    "conteudo_completo_percursos.txt",
    "fragmentos_resegmentados.json",
    "selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py",
    "CF04_diagnostico_metodologico_v4.md",
    "relatorio_diagnostico_metodologico_CF04_v4.txt",
    "CF04_dossier_confronto_REFORMULADO.md",
    "CF03_complemento_FECHO_LOCAL.md",
    "CF03_dossier_confronto_fino_v3.md",
    "CF04_dossier_confronto.md",
    "CF04_base_fragmentaria.md",
    "CF04_fragmentos_relevantes_dossier_v1__debug.txt",
    "CF04_fragmentos_relevantes_dossier_v1.md",
    "CF04_fragmentos_relevantes_dossier_v1.json",
    "CF03_metodo_local_de_validacao_fina.md",
    "CF03_ficha_gesto_estrutural.md",
    "CF03_mapa_minimo_pre_exposicao.md",
    "11_E_12_README_CICLO_LOCAL_VALIDACAO_E_CAMADA_INTERMEDIA_PRE_EXPOSICAO_DOSSIERS.md",
    "DOSSIERS_FINAIS_ESTABILIZADOS__MERGED.md",
    "tree_output.txt",
    "CONTEXTO_ESTRUTURAL_COMPACTO_DO_REAL.md",
    "ANEXOS_TECNICOS_RESUMIDOS_DO_REAL__V2.md",
    "CONTEXTO_ESTRUTURAL_COMPACTO_DO_REAL__V2.md"
)

$allFiles = Get-ChildItem -Path $root -Recurse -File

$copied = 0
$missing = 0

foreach ($name in $filenames) {
    $foundFiles = $allFiles | Where-Object { $_.Name -eq $name }

    if (-not $foundFiles) {
        Write-Host "[falta] $name" -ForegroundColor Yellow
        $missing++
        continue
    }

    foreach ($file in $foundFiles) {
        $relative = $file.FullName.Substring($root.Length).TrimStart('\')
        $target = Join-Path $dest $relative
        $targetDir = Split-Path $target -Parent

        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        Copy-Item -Path $file.FullName -Destination $target -Force

        Write-Host "[ok] $relative" -ForegroundColor Green
        $copied++
    }
}

Write-Host ""
Write-Host "Resumo:" -ForegroundColor Cyan
Write-Host "  Copiados: $copied"
Write-Host "  Em falta: $missing"
Write-Host "  Destino: $dest"