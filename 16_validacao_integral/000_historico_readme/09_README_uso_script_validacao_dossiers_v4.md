# README — uso do script `selecionar_fragmentos_relevantes_dossier_v4.py`

## O que este script faz

Este script é um pipeline local, determinístico, auditável e sem API para validação integral de confrontos filosóficos por reabertura fragmentária.

Ele foi desenhado para:
- ler o dossier reformulado/consolidado do confronto;
- ler as fontes normativas e estruturais do projeto;
- construir um centro admissível do confronto sob precedência normativa explícita;
- carregar e enriquecer fragmentos a partir da base fragmentária específica e/ou do universo resegmentado e da árvore do pensamento;
- calcular scoring vetorial por fragmento;
- selecionar um sample representativo;
- diagnosticar alinhamento, corredor dominante, vizinhança, altitude e perfil operacional;
- adjudicar uma decisão metodológica;
- validar consistência interna;
- escrever outputs JSON, Markdown e TXT;
- executar self-checks opcionais.

## Relação do script com os dossiers

O script **não substitui o dossier**. O dossier reformulado/final é tratado como **norma local soberana** do confronto, enquanto o README da fase funciona como meta-norma metodológica geral. O sample fragmentário não é soberano acima do dossier.

Na prática, o script usa o dossier para extrair:
- pergunta central;
- descrição do confronto;
- tese canónica provisória;
- proposições nucleares centrais;
- proposições de fundo;
- proposições rejeitadas/descentradas;
- pontes, ancoragens, campos do real, capítulos e regimes quando declarados.

Depois compara isso com o material fragmentário e com a estrutura canónica do projeto, para testar se o sample efetivo continua fiel ao confronto reformulado.

## Relação com a tree e com as fontes do projeto

O script lê não apenas o dossier, mas também a base estrutural do projeto e a árvore do pensamento.

As fontes globais obrigatórias incluem, entre outras:
- README da fase de reabertura fragmentária;
- matriz de confronto;
- adjudicação restrita dos confrontos;
- proposições nucleares enriquecidas;
- mapa dedutivo final;
- mapa de arquitetura de fragmentos;
- impacto dos fragmentos no mapa;
- índice sequencial;
- mapa integral do índice;
- meta índice;
- meta referência do percurso;
- operações;
- todos os conceitos;
- argumentos unificados;
- árvore do pensamento em fecho superior;
- fragmentos resegmentados;
- proposições;
- conteúdo completo dos percursos.

Além disso, quando existir, o script lê:
- o `config_dossier_<CF>_v4.json` do confronto;
- a base fragmentária específica do confronto;
- a árvore v1 mais antiga;
- ficheiros auxiliares de revisão e diagnóstico.

A `arvore_do_pensamento_v1_fecho_superior.json` e `fragmentos_resegmentados.json` entram como bases centrais da camada fragmentária e de indexação estrutural.

## O que é obrigatório e o que é opcional

### Obrigatório para correr
- o argumento `confronto_id` no terminal (por exemplo `CF03`);
- o dossier reformulado/consolidado desse confronto;
- a raiz do projeto acessível pelo script;
- as fontes globais obrigatórias do projeto.

### Opcional, mas útil
- `config_dossier_<CF>_v4.json`;
- base fragmentária específica do confronto;
- `--run-self-checks`;
- `--strict`.

Se a config do confronto não existir, o script continua a correr; apenas perde parte da afinação local.

## O que o script gera

Para cada confronto, o script escreve três ficheiros principais:
- `<CF>_diagnostico_metodologico_v4.json`
- `<CF>_diagnostico_metodologico_v4.md`
- `relatorio_diagnostico_metodologico_<CF>_v4.txt`

Esses outputs incluem:
- estado declarado do dossier;
- centro admissível do confronto;
- sample fragmentário selecionado;
- diagnóstico arquitetónico;
- decisão metodológica;
- consistency checks;
- self-checks (quando pedidos).

## Como interpretar corretamente o output

O output deve ser usado como **ajuda de análise**, não como substituto completo da leitura do dossier.

O uso correto é:
1. correr o script para cada dossier;
2. ler o JSON/Markdown/TXT gerado;
3. verificar centro admissível, sample, warnings e decisão;
4. confirmar manualmente no dossier se o output respeitou o núcleo soberano do confronto.

## Limite atual de uso

O script já serve para **análise assistida séria** dos dossiers, mas ainda não deve ser tratado como árbitro metodológico final completamente autónomo sem revisão humana do output.

## Comando base

```powershell
python selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py CF03 --project-root C:\Users\vanes\DoReal_Casa_Local\DoReal
```

## Comandos um a um no terminal

Assumindo que estás em:

```powershell
cd C:\Users\vanes\DoReal_Casa_Local\DoReal\16_validacao_integral\scripts
```

### CF03
```powershell
python selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py CF03 --project-root C:\Users\vanes\DoReal_Casa_Local\DoReal
```

### CF04
```powershell
python selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py CF04 --project-root C:\Users\vanes\DoReal_Casa_Local\DoReal
```

### CF05
```powershell
python selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py CF05 --project-root C:\Users\vanes\DoReal_Casa_Local\DoReal
```

### CF06
```powershell
python selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py CF06 --project-root C:\Users\vanes\DoReal_Casa_Local\DoReal
```

### CF07
```powershell
python selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py CF07 --project-root C:\Users\vanes\DoReal_Casa_Local\DoReal
```

### CF08
```powershell
python selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py CF08 --project-root C:\Users\vanes\DoReal_Casa_Local\DoReal
```

## Variante com self-checks

```powershell
python selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py CF03 --project-root C:\Users\vanes\DoReal_Casa_Local\DoReal --run-self-checks
```

## Variante com modo estrito

```powershell
python selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py CF03 --project-root C:\Users\vanes\DoReal_Casa_Local\DoReal --strict --run-self-checks
```

## Template genérico

```powershell
python selecionar_fragmentos_relevantes_dossier_v4_pronto_local.py <CFXX> --project-root C:\Users\vanes\DoReal_Casa_Local\DoReal
```

## Nota final

Se quiseres correr vários dossiers, tens de fazer um loop externo no PowerShell ou `.bat`, porque o script aceita apenas **um `confronto_id` por execução**.
