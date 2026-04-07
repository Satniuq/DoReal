# README — Fase de Validação Integral Pós-Árvore

## 1. Enquadramento

Esta fase começa **depois do fecho estrutural da árvore do pensamento**, quando a zona superior `ramo → percurso → argumento` já foi restringida, estabilizada e adjudicada. A árvore ficou materialmente fechada, com apenas uma pendência residual no fecho superior, e passou a estar preparada para uma nova macrofase: **confronto, validação, correção e reintegração**. 

A lógica metodológica já fixada para esta etapa é:

**extração → organização → formalização → confronto → reformulação → reintegração**. :contentReference[oaicite:1]{index=1}

---

## 2. O que esta fase é

Esta fase **já não serve para voltar a gerar a árvore**.

Ela serve para:

- pegar nas proposições nucleares do mapa final;
- ligá-las à arquitetura já construída;
- atribuir-lhes regimes de validação;
- separar o que exige:
  - confronto filosófico,
  - ancoragem científica,
  - ponte entre níveis,
  - cartografia de campos do real;
- gerar matrizes derivadas que permitam trabalhar o sistema de forma auditável. 

---

## 3. Estado atual desta fase

Nesta conversa, ficou criada a infraestrutura inicial da fase de validação integral.

### 3.1 Artefacto-mãe gerado

Foi gerado:

- `16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json`

e o respetivo relatório:

- `16_validacao_integral/02_outputs/relatorio_extracao_e_enriquecimento_proposicoes_v1.txt`

Resultado: **51 proposições**, distribuídas por **7 blocos**, com cobertura estrutural forte: **46** com fragmentos/microlinhas/ramos, **50** com percursos e **50** com argumentos. :contentReference[oaicite:3]{index=3}

### 3.2 Atribuição de regimes de validação

Foi depois atualizado o ficheiro-mãe com regimes iniciais de validação por proposição, através de:

- `16_validacao_integral/scripts/atribuir_regimes_de_validacao_v1.py`

e do relatório:

- `16_validacao_integral/02_outputs/relatorio_atribuicao_regimes_v1.txt`

Estado final desta atribuição:

- **51** proposições com confronto filosófico;
- **36** com necessidade de ancoragem científica;
- **31** com necessidade de ponte entre níveis;
- **34** com necessidade de cartografia de campo;
- **6** marcadas para revisão humana crítica:
  - `P30`
  - `P44`
  - `P46`
  - `P47`
  - `P50`
  - `P51` :contentReference[oaicite:4]{index=4}

### 3.3 Matriz de pontes entre níveis

Foi gerada:

- `16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json`

e o respetivo relatório:

- `16_validacao_integral/02_outputs/relatorio_geracao_matriz_pontes_entre_niveis_v1.txt`

Resultado:

- **5 pontes estruturais reais**;
- **34 proposições** cobertas;
- **4** pontes de risco alto/crítico;
- transições identificadas:
  - `ontologia_geral -> biologia_do_organismo`
  - `biologia_do_organismo -> ciencia_cognitiva`
  - `ciencia_cognitiva -> linguagem_simbolica`
  - `ontologia_estrutural -> ontologia_dinamica`
  - `acao_pratica -> normatividade_etica` :contentReference[oaicite:5]{index=5}

### 3.4 Matriz de ancoragem científica

Foi gerada:

- `16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json`

e o respetivo relatório:

- `16_validacao_integral/02_outputs/relatorio_geracao_matriz_ancoragem_cientifica_v1.txt`

Resultado:

- **36 proposições** mapeadas;
- **9 domínios científicos** implicados;
- **1** item com suporte empírico relevante;
- **1** item com determinação material necessária;
- **3** entradas marcadas para revisão humana:
  - `AC01`
  - `AC02`
  - `AC03` :contentReference[oaicite:6]{index=6}

---

## 4. O que foi feito antes e que esta fase herda

Esta fase depende diretamente do fecho anterior da árvore.

### 4.1 Fecho superior da árvore

A zona superior `ramo → percurso → argumento` foi fechada de forma restritiva:

- triagem;
- revisão de percursos;
- revisão restritiva de argumentos;
- adjudicação assistida por API. 

Resultado final do fecho superior:

- **67 ramos** considerados na árvore;
- adjudicação final nos casos ambíguos;
- apenas **1 ramo** em `revisao_humana_necessaria`;
- árvore semanticamente restritiva e discriminativa. 

### 4.2 Estado da árvore herdado para esta fase

A árvore ficou, enquanto artefacto, com blocos de topo fixados:

- `schema_meta`
- `fontes`
- `manifesto_cobertura`
- `fragmentos`
- `relacoes`
- `microlinhas`
- `ramos`
- `percursos`
- `argumentos`
- `convergencias`
- `excecoes`
- `validacao` :contentReference[oaicite:9]{index=9}

A árvore já tinha gerado e validado:

- fragmentos
- microlinhas
- ramos
- percursos
- argumentos

e ainda não tinha gerado:

- convergências
- relações explícitas. 

---

## 5. Estrutura desta fase no projeto

Os ficheiros que participam nesta fase — e que devem estar disponíveis num ambiente GPT do projeto — são os seguintes.

### 5.1 Fontes herdadas do meta-índice

#### Percursos
- `13_Meta_Indice/indice/indice_por_percurso.json`

#### Argumentos
- `13_Meta_Indice/indice/argumentos/argumentos_unificados.json`

---

### 5.2 Fontes herdadas do mapa dedutivo

#### Arquitetura e fecho canónico
- `14_mapa_dedutivo/02_mapa_dedutivo_arquitetura_fragmentos.json`
- `14_mapa_dedutivo/impacto_fragmentos_no_mapa.json`
- `14_mapa_dedutivo/02_fecho_canonico_mapa/outputs/versoes_finais/mapa_dedutivo_canonico_final__vfinal_corrente.json`

---

### 5.3 Fontes herdadas da árvore do pensamento

#### Árvore final útil para esta fase
- `15_arvore_do_pensamento/01_dados/arvore_do_pensamento_v1_fecho_superior.json`

#### Artefactos do fecho superior ainda relevantes
- `15_arvore_do_pensamento/01_dados/arvore_do_pensamento_v1.json`
- `15_arvore_do_pensamento/01_dados/arvore_do_pensamento_v1_pos_percursos.json`
- `15_arvore_do_pensamento/01_dados/triagem_fecho_superior_v1.json`

#### Relatórios de contexto úteis
- `15_arvore_do_pensamento/02_outputs/relatorio_triagem_fecho_superior_v1.txt`
- `15_arvore_do_pensamento/02_outputs/relatorio_geracao_percursos_v1.txt`
- `15_arvore_do_pensamento/02_outputs/relatorio_validacao_percursos_v1.txt`
- `15_arvore_do_pensamento/02_outputs/relatorio_revisao_percursos_superiores_v1.txt`
- `15_arvore_do_pensamento/02_outputs/relatorio_geracao_argumentos_v1.txt`
- `15_arvore_do_pensamento/02_outputs/relatorio_validacao_argumentos_v1.txt`
- `15_arvore_do_pensamento/02_outputs/relatorio_revisao_argumentos_restritiva_v1.txt`
- `15_arvore_do_pensamento/02_outputs/relatorio_adjudicacao_argumentos_api_v1.txt`

#### Artefactos de adjudicação ainda úteis
- `15_arvore_do_pensamento/01_dados/adjudicacao_argumentos_api_v1.json`
- `15_arvore_do_pensamento/01_dados/adjudicacao_argumentos_api_v1_estado.json`
- `15_arvore_do_pensamento/01_dados/adjudicacao_argumentos_api_v1_logs.jsonl`

---

### 5.4 Especificação da nova fase de validação integral

#### README e especificação
- `16_validacao_integral/README_FASE_VALIDACAO_INTEGRAL_POS_ARVORE.md` *(este ficheiro)*
- `16_validacao_integral/00_especificacao/schema_proposicoes_nucleares_enriquecidas_v1.json`
- `16_validacao_integral/00_especificacao/enums_documentados_proposicoes_nucleares_enriquecidas_v1.json`
- `16_validacao_integral/00_especificacao/regras_de_validacao_proposicoes_nucleares_enriquecidas_v1.json`
- `16_validacao_integral/00_especificacao/README_proposicoes_nucleares_enriquecidas_v1.md`
- `16_validacao_integral/00_especificacao/README_matrizes_derivadas_v1.md`

#### Ficheiro-mãe da fase
- `16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json`

#### Matrizes derivadas já geradas
- `16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json`
- `16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json`

#### Matrizes derivadas já previstas mas ainda não geradas
- `16_validacao_integral/01_dados/matriz_confronto_filosofico_v1.json`
- `16_validacao_integral/01_dados/mapa_campos_do_real_v1.json`

#### Scripts já criados nesta conversa
- `16_validacao_integral/scripts/extrair_e_enriquecer_proposicoes_nucleares_v1.py`
- `16_validacao_integral/scripts/atribuir_regimes_de_validacao_v1.py`
- `16_validacao_integral/scripts/gerar_matriz_pontes_entre_niveis_v1.py`
- `16_validacao_integral/scripts/gerar_matriz_ancoragem_cientifica_v1.py`

#### Scripts ainda por criar
- `16_validacao_integral/scripts/gerar_matriz_confronto_filosofico_v1.py`
- `16_validacao_integral/scripts/gerar_mapa_campos_do_real_v1.py`

#### Outputs já gerados nesta conversa
- `16_validacao_integral/02_outputs/relatorio_extracao_e_enriquecimento_proposicoes_v1.txt`
- `16_validacao_integral/02_outputs/relatorio_atribuicao_regimes_v1.txt`
- `16_validacao_integral/02_outputs/relatorio_geracao_matriz_pontes_entre_niveis_v1.txt`
- `16_validacao_integral/02_outputs/relatorio_geracao_matriz_ancoragem_cientifica_v1.txt`

---

## 6. O que estamos a fazer exatamente

Neste momento, estamos a construir a **infraestrutura auditável da validação integral**.

Mais precisamente:

### 6.1 Primeiro movimento
Extrair as proposições nucleares do mapa final e ligá-las à árvore já construída.

Resultado:
- ficheiro-mãe das proposições enriquecidas. :contentReference[oaicite:11]{index=11}

### 6.2 Segundo movimento
Atribuir a cada proposição o tipo de validação de que precisa.

Resultado:
- separação entre:
  - confronto filosófico,
  - ancoragem científica,
  - ponte entre níveis,
  - cartografia de campo. :contentReference[oaicite:12]{index=12}

### 6.3 Terceiro movimento
Reduzir a complexidade dispersa a matrizes derivadas mais tratáveis.

Resultado:
- **5 pontes estruturais** em vez de dezenas de transições dispersas; :contentReference[oaicite:13]{index=13}
- **3 grandes entradas científicas** em vez de ciência espalhada indistintamente. :contentReference[oaicite:14]{index=14}

---

## 7. O que ainda falta fazer nesta fase

Ainda falta gerar pelo menos duas matrizes decisivas.

### 7.1 Matriz de confronto filosófico
Ficheiro a gerar:

- `16_validacao_integral/01_dados/matriz_confronto_filosofico_v1.json`

Script previsto:

- `16_validacao_integral/scripts/gerar_matriz_confronto_filosofico_v1.py`

Função:
- agrupar proposições por problema filosófico;
- associar autores, tradições, tensões, convergências e insuficiências;
- preparar a fase de leitura comparativa.

### 7.2 Mapa dos campos do real
Ficheiro a gerar:

- `16_validacao_integral/01_dados/mapa_campos_do_real_v1.json`

Script previsto:

- `16_validacao_integral/scripts/gerar_mapa_campos_do_real_v1.py`

Função:
- regionalizar o real em campos;
- ligar proposições a campos, escalas e níveis;
- tornar mais concreta a articulação entre estrutura, potencialidade, atualização e domínio regional.

---

## 8. Ordem recomendada dos próximos passos

A ordem metodologicamente mais sensata, neste momento, é esta:

1. `gerar_matriz_confronto_filosofico_v1.py`
2. `gerar_mapa_campos_do_real_v1.py`
3. leitura humana das quatro matrizes em conjunto:
   - `proposicoes_nucleares_enriquecidas_v1.json`
   - `matriz_pontes_entre_niveis_v1.json`
   - `matriz_ancoragem_cientifica_v1.json`
   - `matriz_confronto_filosofico_v1.json`
   - `mapa_campos_do_real_v1.json`
4. abertura de dossiês específicos para os pontos críticos:
   - `P30`
   - `P44`
   - `P46`
   - `P47`
   - `P50`
   - `P51` 

---

## 9. O que ainda não estamos a fazer

Nesta fase **ainda não estamos**:

- a provar definitivamente o sistema;
- a fechar o confronto filosófico substantivo;
- a integrar bibliografia detalhada;
- a decidir a redação final do sistema;
- a produzir convergências da árvore;
- a gerar relações explícitas novas na árvore.

Isto é importante porque a função desta fase é **preparar o terreno de validação**, não fingir que a validação já está concluída. A própria documentação da fase pós-árvore diz expressamente que o confronto deve expor erros, fragilidades e obrigar a revisitar partes do sistema. :contentReference[oaicite:16]{index=16}

---

## 10. Regra de prudência desta fase

A regra de prudência que deve continuar a governar o trabalho é esta:

> **não misturar ontologia, ciência, normatividade e cartografia regional como se fossem o mesmo tipo de justificação**

Por isso:

- a ciência entra como compatibilidade, suporte empírico, restrição ou determinação material;
- a filosofia entra como confronto, clarificação e teste estrutural;
- as pontes entre níveis entram como mediações explícitas;
- os campos entram como regionalização do real;
- a reintegração só deve acontecer depois desta separação estar suficientemente trabalhada.

---

## 11. Fórmula curta do estado atual

**Árvore fechada no topo → proposições nucleares enriquecidas → regimes de validação atribuídos → matriz de pontes gerada → matriz de ancoragem científica gerada → próximos passos: confronto filosófico e mapa dos campos do real.** 