# README — Estado atual da árvore do pensamento, artefactos criados e próximos passos

## 1. Estado atual

A fase da **árvore do pensamento** foi iniciada com sucesso e já ultrapassou a mera preparação documental.

Neste momento, a árvore já tem as seguintes camadas **geradas e validadas**:

- **fragmentos**
- **microlinhas**
- **ramos**
- **percursos**
- **argumentos**

Ainda **não** foram geradas:
- **convergências**
- **relações explícitas** (`relacoes`)

A árvore existe já como artefacto operativo em:

- `15_arvore_do_pensamento/01_dados/arvore_do_pensamento_v1.json`

---

## 2. Situação herdada antes desta fase

Antes de arrancar a árvore, ficou concluído e aceite o **fecho canónico do mapa dedutivo**.

Ficou estabelecido que:

- o mapa dedutivo canónico final está fechado;
- o relatório final de inevitabilidades ficou alinhado;
- o fecho terminal foi conferido e aceite;
- a versão final corrente foi congelada.

Outputs finais do fecho canónico:
- `14_mapa_dedutivo/02_fecho_canonico_mapa/outputs/mapa_dedutivo_canonico_final.json`
- `14_mapa_dedutivo/02_fecho_canonico_mapa/outputs/relatorio_final_de_inevitabilidades.json`
- `14_mapa_dedutivo/02_fecho_canonico_mapa/outputs/decisoes_canonicas_intermedias_consolidado_final_intermedio.json`

A árvore do pensamento passou então a ser a nova macrofase do projeto.

---

## 3. Objetivo da árvore do pensamento

A árvore do pensamento foi definida como a camada intermédia explícita entre:

- os **fragmentos de origem**
- a **dinâmica local do pensamento**
- os **agrupamentos intermédios** (microlinhas, ramos)
- os **percursos/argumentos**
- e a **convergência futura no mapa dedutivo canónico final**

Fórmula de trabalho:

**fragmentos → microlinhas → ramos → percursos/argumentos → convergências → mapa final**

---

## 4. Base documental fixada para a árvore

### Núcleo obrigatório
- `fragmentos_resegmentados.json`
- `cadencia_extraida.json`
- `cadencia_schema.json`
- `tratamento_filosofico_fragmentos.json`
- `impacto_fragmentos_no_mapa.json`
- `indice_por_percurso.json`
- `argumentos_unificados.json`
- `mapa_dedutivo_canonico_final.json`

### Apoio recomendado
- `relatorio_validacao_fragmentos.json`
- `cadencia_relatorio_validacao.json`
- `tratamento_filosofico_relatorio_validacao.json`
- `impacto_fragmentos_no_mapa_relatorio_validacao.json`
- `relatorio_validacao_indice_por_percurso.json`
- `relatorio_validacao_argumentos.json`

### Apoio opcional
- `meta_referencia_do_percurso.json`
- `indice_de_percursos.json`
- `conteudo_completo_percursos.txt`

### Ficheiros de outra fase, não nucleares para a árvore
- `revisao_estrutural_do_mapa.json`
- `02_mapa_dedutivo_arquitetura_fragmentos.json`
- `relatorio_final_de_inevitabilidades.json`
- `decisoes_canonicas_intermedias_consolidado_final_intermedio.json`

---

## 5. Exceções documentais conhecidas no arranque

Foram identificados 3 fragmentos presentes em cadência e impacto, mas ausentes em `tratamento_filosofico_fragmentos.json`:

- `F0001_SEG_001`
- `F0002_SEG_001`
- `F0003_SEG_001`

Diagnóstico fixado:
- `F0001_SEG_001` = omissão residual
- `F0002_SEG_001` = omissão residual
- `F0003_SEG_001` = omissão relevante, mas não bloqueante

A fase da árvore arrancou apesar disso, ficando essas lacunas representadas no bloco `excecoes`.

---

## 6. Estrutura criada para a nova fase

Criada a pasta:

- `15_arvore_do_pensamento/`

Estrutura inicial criada:

- `15_arvore_do_pensamento/00_especificacao/schema_arvore_do_pensamento_v1.md`
- `15_arvore_do_pensamento/01_dados/arvore_do_pensamento_v1.json`
- `15_arvore_do_pensamento/scripts/`

---

## 7. Arquitetura do schema fixada

Ficou fixado que a árvore não seria uma árvore recursiva pura, mas um objeto **normalizado por coleções paralelas**.

Blocos de topo do objeto:
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
- `validacao`

Decisões fixadas:
- `fragmentos` = ponto de entrada obrigatório
- `cadencia`, `tratamento_filosofico`, `impacto_mapa` = embutidos no fragmento
- `microlinhas` e `ramos` = entidades geradas
- `percursos` e `argumentos` = entidades importadas/associadas
- `convergencias` = bloco próprio, ainda não gerado
- `relacoes` = bloco próprio, ainda não gerado

---

## 8. Scripts criados nesta fase

Na pasta:
- `15_arvore_do_pensamento/scripts/`

foram criados e executados:

### Base da árvore
- `gerar_arvore_do_pensamento_v1.py`
- `validar_arvore_do_pensamento_v1.py`

### Microlinhas
- `gerar_microlinhas_v1.py`
- `validar_microlinhas_v1.py`

### Ramos
- `gerar_ramos_v1.py`
- `validar_ramos_v1.py`

### Percursos
- `gerar_percursos_v1.py`
- `validar_percursos_v1.py`

### Argumentos
- `gerar_argumentos_v1.py`
- `validar_argumentos_v1.py`

---

## 9. Resultados obtidos até agora

### 9.1 Árvore base
Execução de:
- `gerar_arvore_do_pensamento_v1.py`

Resultado:
- **538 fragmentos**
- **3 exceções**
- estado global inicial: `invalido_tolerado`

Validação por:
- `validar_arvore_do_pensamento_v1.py`

Resultado:
- **VALIDA COM EXCEÇÕES**

---

### 9.2 Microlinhas
Execução de:
- `gerar_microlinhas_v1.py`

Resultado:
- **194 microlinhas**
- **70 microlinhas unitárias**
- **2 microlinhas com exceções**

Validação por:
- `validar_microlinhas_v1.py`

Resultado:
- **VALIDA COM AVISOS**

Leitura:
- a camada é utilizável;
- a v1 é conservadora;
- há bastante granularidade local.

---

### 9.3 Ramos
Execução de:
- `gerar_ramos_v1.py`

Resultado:
- **67 ramos**
- **34 ramos unitários**
- **1 ramo com exceção**

Validação por:
- `validar_ramos_v1.py`

Resultado:
- **VALIDA COM AVISOS**

Leitura:
- os ramos estão estruturalmente consistentes;
- a v1 continua prudente e granular.

---

### 9.4 Percursos
Execução de:
- `gerar_percursos_v1.py`

Resultado:
- **17 percursos importados**
- **44 ramos** associados a pelo menos um percurso
- **23 ramos** sem percurso
- **9 percursos** sem ramos associados

Validação por:
- `validar_percursos_v1.py`

Resultado:
- **VALIDA COM AVISOS**

Leitura:
- a árvore já tem projeção em percursos;
- ainda há material macro-local sem bom encaixe.

---

### 9.5 Argumentos
Execução de:
- `gerar_argumentos_v1.py`

Resultado:
- **65 argumentos importados**
- **35 ramos** associados a pelo menos um argumento
- **32 ramos** sem argumento
- **37 argumentos** sem ramos associados

Validação por:
- `validar_argumentos_v1.py`

Resultado:
- **VALIDA COM AVISOS**
- **24 avisos de plausibilidade**

Leitura importante:
- a camada de argumentos está **estruturalmente válida**
- mas a heurística de associação está ainda **demasiado permissiva** em vários casos
- existem associações heterogéneas ou fracas
- por isso **não se deve ainda passar à geração de convergências**

---

## 10. Relatórios já produzidos

Na pasta:
- `15_arvore_do_pensamento/01_dados/`

existem já, entre outros, os seguintes relatórios:

- `relatorio_validacao_arvore_v1.txt`
- `relatorio_geracao_microlinhas_v1.txt`
- `relatorio_validacao_microlinhas_v1.txt`
- `relatorio_geracao_ramos_v1.txt`
- `relatorio_validacao_ramos_v1.txt`
- `relatorio_geracao_percursos_v1.txt`
- `relatorio_validacao_percursos_v1.txt`
- `relatorio_geracao_argumentos_v1.txt`
- `relatorio_validacao_argumentos_v1.txt`

---

## 11. Estado atual rigoroso

Neste momento, a árvore do pensamento está:

### Feito e validado
- estrutura-base do ficheiro
- fragmentos
- microlinhas
- ramos
- percursos
- argumentos

### Ainda por fazer
- refinamento da heurística dos argumentos
- convergências
- relações explícitas
- eventual visualização
- eventual exportação editorial/navegável

### Juízo técnico
A árvore já existe como artefacto real e consistente.
O pipeline **não está bloqueado**.
Mas a camada de argumentos ainda **não está suficientemente limpa** para passar diretamente a convergências.

---

## 12. Próximo passo recomendado

### Próximo passo certo
Criar uma versão mais restritiva do gerador de argumentos:

- `gerar_argumentos_v2.py`

### Objetivo de `gerar_argumentos_v2.py`
Tornar a associação ramo → argumento mais exigente, reduzindo:
- heterogeneidade excessiva;
- associações fracas;
- inflação de argumentos por ramo.

### Regras a apertar na v2
1. **1 argumento dominante por ramo**
2. no máximo **2** quando a evidência for forte
3. **3** apenas excecionalmente
4. exigir pelo menos **2 sinais independentes** para associação
5. penalizar fortemente dispersão de:
   - `parte`
   - `conceito_alvo`
   - `nivel_de_operacao`
   - `tipo_de_necessidade`

### Só depois disso
- voltar a correr `validar_argumentos_v1.py`
- comparar o número de avisos de plausibilidade
- e **só se os avisos baixarem claramente** passar para:
  - `gerar_convergencias_v1.py`

---

## 13. Próximos passos em ordem recomendada

1. `gerar_argumentos_v2.py`
2. correr `gerar_argumentos_v2.py`
3. voltar a correr `validar_argumentos_v1.py`
4. comparar:
   - número de ramos com argumento
   - número de argumentos vazios
   - número de avisos de plausibilidade
5. se a camada de argumentos ficar mais limpa:
   - `gerar_convergencias_v1.py`
6. depois:
   - `validar_convergencias_v1.py`

---

## 14. Regra de prudência fixada

**Não gerar convergências enquanto a camada de argumentos continuar estruturalmente válida mas semanticamente demasiado permissiva.**

---

## 15. Fórmula curta do estado atual

**Árvore v1 criada → fragmentos validados → microlinhas validadas → ramos validados → percursos validados → argumentos estruturalmente válidos mas ainda demasiado permissivos → próximo passo: refinar argumentos antes de convergências.**