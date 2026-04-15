# Schema completo de etiquetagem — fragmentos e containers — v1

## Estatuto

Este ficheiro separa três camadas:

1. **camada canónica fechada já existente no projeto**;
2. **camada canónica normativa aqui formalizada de modo compatível**;
3. **camada derivada de leitura lateral**, útil para a tua extração de crítica direcional.

A lógica é esta:
- a **cadência** já existe como schema JSON fechado;
- a **grelha mínima** já fixa as perguntas obrigatórias e os estatutos locais, mas não aparece no repositório como schema JSON fechado do mesmo tipo;
- a **camada de vetor crítico** abaixo é uma formalização compatível e subordinada, não uma soberania nova.

---

## I. Camada canónica fechada já existente

### A. Regimes canónicos

- `REGIME_INSCRICAO_REAL`
- `REGIME_DESCRICAO_ESTRUTURAL`
- `REGIME_DIFERENCIACAO_ONTOLOGICA`
- `REGIME_CRITICA_REFLEXIVIDADE`
- `REGIME_EPISTEMOLOGICO`
- `REGIME_ETICO_ONTOLOGICO`
- `REGIME_CRITICA_SISTEMICA`
- `REGIME_CORRETIVO`

### B. Operações canónicas

#### REGIME_INSCRICAO_REAL
- `OP_AFIRMACAO_ESTRUTURAL`
- `OP_FIXACAO_CONDICAO_ONTOLOGICA`
- `OP_FIXACAO_LIMITE_ONTOLOGICO`
- `OP_EXCLUSAO_EXTERIORIDADE`
- `OP_IDENTIFICACAO_IMPOSSIBILIDADE_ONTOLOGICA`

#### REGIME_DESCRICAO_ESTRUTURAL
- `OP_RECONDUCAO_RELACIONAL`
- `OP_DESCRICAO_ESTRUTURAL`
- `OP_DESCRICAO_ATUALIZACAO`
- `OP_IDENTIFICACAO_DEPENDENCIA`
- `OP_IDENTIFICACAO_CONTINUIDADE`
- `OP_IDENTIFICACAO_REGULARIDADE`

#### REGIME_DIFERENCIACAO_ONTOLOGICA
- `OP_DIFERENCIACAO_NIVEIS`
- `OP_IDENTIFICACAO_ESCALA`
- `OP_IDENTIFICACAO_CAMPO`
- `OP_IDENTIFICACAO_MEDIACAO`

#### REGIME_CRITICA_REFLEXIVIDADE
- `OP_DESSUBSTANCIALIZACAO`
- `OP_REINSCRICAO_CONSCIENCIA_REAL`
- `OP_LIMITACAO_REFLEXIVIDADE`
- `OP_DISTINCAO_APREENSAO_REPRESENTACAO`
- `OP_IDENTIFICACAO_PONTO_DE_VISTA`
- `OP_IDENTIFICACAO_PROJECAO_EU`

#### REGIME_EPISTEMOLOGICO
- `OP_IDENTIFICACAO_ADEQUACAO`
- `OP_FIXACAO_CRITERIO`
- `OP_SUBMISSAO_REAL`
- `OP_IDENTIFICACAO_ERRO_DESCRITIVO`
- `OP_IDENTIFICACAO_ERRO_CATEGORIAL`
- `OP_IDENTIFICACAO_ERRO_ESCALA`

#### REGIME_ETICO_ONTOLOGICO
- `OP_DERIVACAO_DEVER_SER`
- `OP_SUBORDINACAO_DEVER_SER`
- `OP_IDENTIFICACAO_RESPONSABILIDADE_ONTOLOGICA`
- `OP_IDENTIFICACAO_DANO_REAL`
- `OP_IDENTIFICACAO_BEM_COMO_ADEQUACAO`

#### REGIME_CRITICA_SISTEMICA
- `OP_IDENTIFICACAO_CRISTALIZACAO_SISTEMICA`
- `OP_IDENTIFICACAO_DEGENERACAO`
- `OP_IDENTIFICACAO_SUBSTITUICAO_REAL_SISTEMA`
- `OP_CRITICA_FECHAMENTO_SIMBOLICO`

#### REGIME_CORRETIVO
- `OP_REINTEGRACAO_ONTOLOGICA`

### C. Percursos canónicos utilizáveis como etiquetas

- `P_EIXO_ONTOLOGICO_NUCLEAR`
- `P_ESTRUTURA_OPERACIONAL_DO_REAL`
- `P_EIXO_CAMPO_E_LOCALIZACAO`
- `P_TRANSICAO_ANTROPOLOGICA_ONTOLOGICA`
- `P_EIXO_SIMBOLICO_MEDIACIONAL`
- `P_EIXO_EPISTEMOLOGICO`
- `P_EIXO_ESCALA_E_ERRO_DE_ESCALA`
- `P_EIXO_ETICO_NARRATIVO`
- `P_CRITICA_SISTEMICA_E_REINTEGRACAO_ONTOLOGICA`
- `P_PERCURSO_DO_ERRO_E_CORRECAO`
- `P_PERCURSO_DA_DEGENERACAO_ETICA`
- `P_PERCURSO_DO_ERRO_E_DA_DEGENERACAO`
- `P_PERCURSO_DA_VIDA_BOA`
- `P_PERCURSO_DA_VIDA_BOA_FILOSOFICA`
- `P_PERCURSO_DA_VIDA_BOA_FILOSOFICA_ESPIRAL`
- `P_PERCURSO_ONTOLOGICAMENTE_ESTERIL_POR_INVERSAO_DIRECIONAL`
- `P_PERCURSO_INTEGRAL_DO_REAL_A_VIDA_BOA`

### D. Cadência — enums fechados

#### `funcao_cadencia_principal` / `funcao_cadencia_secundaria`
- `abertura_de_problema`
- `formulacao_inicial`
- `distincao_conceptual`
- `desenvolvimento`
- `aprofundamento`
- `objecao`
- `resposta`
- `transicao`
- `consequencia`
- `sintese_provisoria`
- `aplicacao`
- `critica_de_erro`
- `reposicionamento_narrativo`
- `nota_de_apoio`

#### `direcao_movimento`
- `introduz`
- `prolonga`
- `desloca`
- `fecha`
- `retoma`
- `articula`
- `prepara`

#### `grau_de_abertura_argumentativa`
- `introducao`
- `desenvolvimento`
- `conclusao_local`
- `abertura_para_seguinte`

#### `centralidade`
- `nuclear`
- `auxiliar`
- `transitorio`
- `exploratorio`
- `estabilizador`
- `dispersivo_aproveitavel`
- `nota_de_apoio`

#### `estatuto_no_percurso`
- `pertence_a_zona`
- `ponte_entre_zonas`
- `solto_ainda_sem_encaixe`

#### `zona_provavel_percurso`
- `ontologia`
- `estrutura_operacional_do_real`
- `campo_e_localizacao`
- `transicao_antropologica`
- `mediacao_simbolica`
- `epistemologia`
- `escala_e_erro_de_escala`
- `etica_e_narrativa`
- `critica_sistemica_e_reintegracao`
- `percurso_do_erro_e_correcao`
- `percurso_da_degeneracao`
- `vida_boa`
- `metaestrutura_do_livro`
- `indefinida`

#### `familia_erro_provavel`
- `epistemologicos`
- `critica_reflexividade`
- `critica_sistemica`
- `deslocamentos_e_derivados`
- `nao_aplicavel`
- `null`

#### `erro_dominante_provavel`
- `erro_descritivo`
- `erro_categorial`
- `erro_de_escala`
- `substituicao_do_real_por_sistema`
- `fechamento_simbolico`
- `cristalizacao_sistemica`
- `degeneracao`
- `projecao_do_eu`
- `substancializacao_do_eu_ou_consciencia`
- `confusao_entre_apreensao_e_representacao`
- `deslocalizacao_do_ponto_de_vista`
- `subjetivacao_do_criterio`
- `nao_submissao_ao_real`
- `dogmatizacao`
- `moralizacao_indevida`
- `hipostase`
- `atomismo_ontologico`
- `substancialismo_isolacionista`
- `inversao_direcional`
- `null`

#### `dominio_contributivo_principal`
- `ontologia`
- `antropologia`
- `mediacao_simbolica`
- `epistemologia`
- `etica`
- `critica_de_erro`
- `aplicacao`
- `metaestrutura`

#### `tipo_fragmento_provavel`
- `afirmacao_estrutural`
- `fixacao_condicao_ontologica`
- `fixacao_limite_ontologico`
- `exclusao_exterioridade`
- `identificacao_impossibilidade_ontologica`
- `reconducao_relacional`
- `descricao_estrutural`
- `descricao_atualizacao`
- `identificacao_dependencia`
- `identificacao_continuidade`
- `regularidade_estrutural`
- `diferenciacao_niveis`
- `identificacao_escala`
- `identificacao_campo`
- `identificacao_mediacao`
- `dessubstancializacao`
- `reinscricao_consciencia_real`
- `limitacao_reflexividade`
- `distincao_apreensao_representacao`
- `identificacao_ponto_de_vista`
- `identificacao_projecao_eu`
- `identificacao_adequacao`
- `fixacao_criterio`
- `submissao_ao_real`
- `identificacao_erro_descritivo`
- `identificacao_erro_categorial`
- `identificacao_erro_escala`
- `derivacao_dever_ser`
- `subordinacao_dever_ser`
- `identificacao_responsabilidade_ontologica`
- `identificacao_dano_real`
- `identificacao_bem_como_adequacao`
- `identificacao_cristalizacao_sistemica`
- `identificacao_degeneracao`
- `identificacao_substituicao_real_sistema`
- `critica_fechamento_simbolico`
- `reintegracao_ontologica`
- `proposicao_fonte`
- `observacao_metodologica`
- `transicao_narrativa`
- `fragmento_intuitivo`
- `null`

#### `aproveitamento_editorial`
- `nucleo_de_capitulo`
- `apoio_argumentativo`
- `ponte_de_transicao`
- `nota_lateral_aproveitavel`
- `material_a_retrabalhar`

#### `confianca_cadencia`
- `alta`
- `media`
- `baixa`

---

## II. Camada canónica normativa aqui formalizada

Esta camada traduz em forma de schema aquilo que a **grelha mínima** já manda reconhecer.

### `objeto_real_em_causa`
- tipo: `string`
- natureza: **aberta**
- regra: dizer o foco efetivo do material no real, não o tema alto.

### `nivel_regime_campo_escala`
- `inscricao_ontologica`
- `descricao_estrutural`
- `diferenciacao_niveis_campo_escala`
- `reflexividade_e_mediacao`
- `regime_epistemologico`
- `regime_etico_ontologico`
- `diagnostico_critico_corretivo`
- `mistura_ainda_nao_limpa`

### `operacao_filosofica_dominante_ampla`
- `inscrever`
- `descrever`
- `diferenciar`
- `identificar_mediacao`
- `fixar_criterio`
- `submeter_ao_real`
- `derivar`
- `criticar`
- `reinscrever`
- `corrigir`

### `estagio_legitimo_de_entrada`
- `abertura_baixa`
- `desenvolvimento_medio`
- `dobradica`
- `terminal`
- `sem_estatuto_de_entrada`

### `desvio_dominante`
- `erro_categorial`
- `erro_de_escala`
- `substituicao_do_real_por_sistema`
- `autonomizacao_de_mediacao`
- `autonomizacao_de_criterio`
- `autonomizacao_de_normatividade`
- `abertura_por_camada_tardia`
- `indexacao_sem_objeto`
- `indeterminado`

### `estatuto_local`
- `centro`
- `apoio`
- `travao`
- `camada_derivada`
- `desvio`

---

## III. Camada derivada de vetor crítico

### `vetor_critico`
- `sem_vetor_critico`
- `projecao_para_fora`
- `regresso_ao_eu`
- `diagnostico_do_sistema`
- `devolucao_ao_agente`
- `mista`
- `indeterminada`

### `alvo_critico`
- `eu_reflexivo`
- `ponto_de_vista`
- `consciencia_reflexiva`
- `outro_concreto`
- `sistema_simbolico`
- `cultura`
- `instituicao`
- `linguagem_mediacao`
- `normatividade_autonomizada`
- `indeterminado`

### `movimento_corretivo_dominante`
- `nenhum`
- `submissao_ao_real`
- `limitacao_da_reflexividade`
- `reinscricao_da_consciencia_no_real`
- `reconducao_relacional`
- `reintegracao_ontologica`
- `devolucao_da_responsabilidade`
- `correcao_operativa`

### `grau_de_explicitude`
- `explicito`
- `implicito_forte`
- `implicito_fraco`
- `a_rever`

---

## IV. Schema integrado — nível fragmento

### Campos obrigatórios

- `id`
- `origem_id`
- `tipo_no`
- `objeto_real_em_causa`
- `nivel_regime_campo_escala`
- `regime_dominante`
- `operacao_filosofica_dominante_ampla`
- `operacao_ontologica_fina`
- `estagio_legitimo_de_entrada`
- `desvio_dominante`
- `estatuto_local`
- `cadencia`
- `vetor_critico`
- `alvo_critico`
- `movimento_corretivo_dominante`
- `grau_de_explicitude`

### Campo `regime_dominante`
- `REGIME_INSCRICAO_REAL`
- `REGIME_DESCRICAO_ESTRUTURAL`
- `REGIME_DIFERENCIACAO_ONTOLOGICA`
- `REGIME_CRITICA_REFLEXIVIDADE`
- `REGIME_EPISTEMOLOGICO`
- `REGIME_ETICO_ONTOLOGICO`
- `REGIME_CRITICA_SISTEMICA`
- `REGIME_CORRETIVO`

### Campo `operacao_ontologica_fina`
Usa uma das operações canónicas listadas na secção I.B.

### Campo `cadencia`
Usa integralmente os campos e enums da secção I.D.

---

## V. Schema integrado — nível container

### Regra
O container **não reordena** a arquitetura nem cria centro novo por afinidade; apenas **agrega prudentemente** os resultados dos fragmentos.

### Campos obrigatórios
- `container_id`
- `tipo_no`
- `fragmentos_filhos`
- `objeto_real_em_causa`
- `nivel_regime_campo_escala`
- `regime_dominante`
- `operacao_ontologica_fina_dominante`
- `estagio_legitimo_de_entrada`
- `desvio_dominante`
- `estatuto_local`
- `vetor_critico`
- `alvo_critico_predominante`
- `movimento_corretivo_dominante`
- `grau_de_explicitude`
- `regra_de_agregacao`
- `composicao_interna`

### `regra_de_agregacao`
- `dominancia_nitida`
- `misto_com_centro`
- `misto_sem_centro`
- `a_rever`

### `composicao_interna`
- `homogeneo`
- `heterogeneo_controlado`
- `heterogeneo_em_tensao`
- `a_rever`

### `alvo_critico_predominante`
Usa a mesma enum de `alvo_critico`.

### `operacao_ontologica_fina_dominante`
Usa a mesma enum de operações canónicas.

---

## VI. Regra de preenchimento

### Para fragmentos
1. fixar `objeto_real_em_causa`
2. atribuir `nivel_regime_campo_escala`
3. atribuir `regime_dominante`
4. atribuir `operacao_filosofica_dominante_ampla`
5. atribuir `operacao_ontologica_fina`
6. atribuir `estagio_legitimo_de_entrada`
7. atribuir `desvio_dominante`
8. só depois decidir `estatuto_local`
9. preencher `cadencia`
10. preencher `vetor_critico`, `alvo_critico`, `movimento_corretivo_dominante`, `grau_de_explicitude`

### Para containers
1. herdar os resultados fragmentários
2. testar se há dominância real
3. só subir a centro do container se a dominância resistir
4. marcar `misto` ou `a_rever` quando houver tensão real

---

## VII. Nota decisiva

O que é **fechado e já estável** no projeto é sobretudo:
- os **regimes**,
- as **operações**,
- a **cadência**,
- e o **estatuto local** mínimo.

O que fica aqui **formalizado de modo compatível**, mas não como schema canónico já fechado no repositório, é:
- a passagem da **grelha mínima** a campos de schema,
- e a camada de **vetor crítico**.
