# Proposições Nucleares Enriquecidas V1

## Finalidade

Este ficheiro é o artefacto-mãe da fase de validação integral pós-árvore.

A sua função é reunir, por proposição nuclear do mapa dedutivo, quatro tipos de informação:

1. identificação e posição no mapa;
2. rastreabilidade arquitetural na árvore do pensamento;
3. classificação inicial do tipo filosófico da proposição;
4. atributos de validação necessários para a fase pós-árvore.

O ficheiro não serve para guardar bibliografia extensa nem análise longa.  
Serve para indexação, decisão, priorização e geração de matrizes derivadas.

---

## Estrutura global

O ficheiro contém seis blocos de topo:

- `metadata`
- `fontes`
- `estatisticas`
- `enums_documentados`
- `regras_de_validacao`
- `proposicoes`

---

## Princípio metodológico

Cada proposição deve poder ser lida segundo quatro eixos:

- o que diz;
- de onde vem na arquitetura;
- de que tipo é;
- o que ainda lhe falta para validação integral.

---

## Regras de uso

### 1. Unidade de base
A unidade de base é a proposição nuclear do mapa dedutivo.

### 2. Não misturar níveis
Este ficheiro não deve confundir:
- dependência dedutiva,
- rastreabilidade arquitetural,
- confronto filosófico,
- ancoragem científica,
- cartografia de campo.

Cada dimensão tem lugar próprio.

### 3. Não usar este ficheiro como repositório bibliográfico
Bibliografia, leituras, papers, excertos e dossiers detalhados devem ficar em ficheiros derivados.

### 4. Justificações curtas e auditáveis
Campos textuais como `justificacao_atribuicao` e `motivo_revisao_humana` devem ser curtos, específicos e verificáveis.

---

## Ficheiros derivados esperados

A partir deste ficheiro deverão ser gerados, pelo menos, os seguintes artefactos:

- `matriz_confronto_filosofico_v1.json`
- `matriz_ancoragem_cientifica_v1.json`
- `matriz_pontes_entre_niveis_v1.json`
- `mapa_campos_do_real_v1.json`

---

## Campos mais importantes

### `arquitetura_origem`
Liga a proposição aos elementos já existentes da árvore:
- fragmentos
- microlinhas
- ramos
- percursos
- argumentos
- convergências
- relações

### `validacao_integral`
É o núcleo decisivo da fase pós-árvore.
Diz:
- que tipo de proposição é;
- que regime(s) de validação exige;
- se precisa de filosofia, ciência, ponte entre níveis, ou cartografia de campo.

### `pontes_entre_niveis`
Serve para marcar transições delicadas entre níveis, por exemplo:
- ontologia → biologia
- biologia → cognição
- estrutura do real → normatividade

### `estado_trabalho`
Serve para controlo operacional do pipeline.

---

## Fluxo recomendado

1. extrair proposições nucleares do mapa;
2. enriquecer com ligações à arquitetura;
3. atribuir classificações e necessidades de validação;
4. validar consistência interna do ficheiro;
5. gerar matrizes derivadas.

---

## Observação final

Este ficheiro é o centro de gravidade da fase pós-árvore.

Ele não substitui o mapa dedutivo nem a árvore.
Ele funciona como camada intermédia entre:
- a arquitetura já construída,
- e a futura validação filosófica, científica e integrativa do sistema.