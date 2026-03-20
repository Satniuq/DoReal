# Schema da Árvore do Pensamento v1

## Objeto
`arvore_do_pensamento`

## Versão
`1.0.0`

## Princípio arquitetural
A árvore do pensamento é um objeto normalizado por coleções paralelas, e não uma árvore recursiva pura.

Os fragmentos são o ponto de entrada obrigatório.
As camadas de cadência, tratamento filosófico e impacto no mapa ficam embutidas em cada fragmento.
Microlinhas e ramos são entidades geradas.
Percursos e argumentos são entidades importadas.
Convergências ficam em bloco próprio.
Exceções e validação ficam formalmente representadas.

## Estrutura de topo obrigatória

O ficheiro `arvore_do_pensamento_v1.json` deve conter sempre estes blocos de topo:

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

## Perfil mínimo v1

Na v1 mínima:
- todos os blocos de topo já existem;
- apenas os blocos indispensáveis têm conteúdo preenchido;
- os restantes podem existir vazios por desenho.

## Campos mínimos obrigatórios na v1

### `schema_meta`
- `schema_name`
- `schema_version`
- `objeto`
- `generated_at_utc`
- `lote_geracao_id`
- `politica_excecoes_version`

### `fontes`
Devem existir os 8 subblocos:
- `fragmentos_resegmentados`
- `cadencia_extraida`
- `cadencia_schema`
- `tratamento_filosofico_fragmentos`
- `impacto_fragmentos_no_mapa`
- `indice_por_percurso`
- `argumentos_unificados`
- `mapa_dedutivo_canonico_final`

Campos mínimos por subbloco:
- `ficheiro`
- `obrigatorio`
- `presente`

### `manifesto_cobertura`
- `arranque_permitido`
- `total_fragmentos_base`
- `total_fragmentos_com_cadencia`
- `total_fragmentos_com_tratamento`
- `total_fragmentos_com_impacto`
- `fragmentos_sem_tratamento_ids`
- `fragmentos_com_validacao_base_problemática_ids`

### `fragmentos`
Array obrigatório.
Pode começar vazio na estrutura-base inicial.

Quando houver fragmentos carregados, cada fragmento deve ter no mínimo:
- `id`
- `tipo_no`
- `origem_id`
- `ordem_no_ficheiro`
- `base_empirica`
- `cadencia`
- `tratamento_filosofico`
- `impacto_mapa`
- `ligacoes_arvore`
- `estado_validacao`
- `estado_excecao`
- `excecao_ids`

### `relacoes`
Array. Pode começar vazio.

### `microlinhas`
Array. Pode começar vazio.

### `ramos`
Array. Pode começar vazio.

### `percursos`
Array. Pode começar vazio.

### `argumentos`
Array. Pode começar vazio.

### `convergencias`
Array. Pode começar vazio.

### `excecoes`
Array. Pode começar vazio.
Só é obrigatório ter conteúdo quando existir fragmento com `tratamento_filosofico = null`.

### `validacao`
- `estado_validacao_global`
- `pronto_para_artefacto_operacional`
- `metricas`
- `excecao_ids_ativas`

Campos mínimos de `metricas`:
- `total_fragmentos`
- `total_relacoes`
- `total_microlinhas`
- `total_ramos`
- `total_percursos`
- `total_argumentos`
- `total_convergencias`
- `total_excecoes_ativas`

## Regras mínimas da v1

1. Nenhum bloco de topo pode faltar.
2. Coleções ainda não ativadas entram como `[]`.
3. `tratamento_filosofico` só pode ser `null` com exceção ativa correspondente.
4. O mapa canónico final é referencial externo obrigatório para futuras convergências.
5. A v1 pode existir como estrutura vazia válida antes do primeiro lote de fragmentos.

## Estado inicial recomendado

Antes do primeiro lote real de povoamento:
- `fragmentos = []`
- `relacoes = []`
- `microlinhas = []`
- `ramos = []`
- `percursos = []`
- `argumentos = []`
- `convergencias = []`
- `excecoes = []`

## Próximo passo após esta base
Preencher `arvore_do_pensamento_v1.json` com a estrutura vazia válida e só depois carregar o primeiro lote de fragmentos.