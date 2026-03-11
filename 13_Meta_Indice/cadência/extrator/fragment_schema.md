# fragment_schema

## Finalidade
Este schema define a estrutura mínima e expandida de um fragmento no pipeline de ingestão, classificação e reinscrição no sistema.

Foi derivado da estrutura formal já existente no projeto, sobretudo de:
- `argumentos_unificados.json`
- `indice_sequencial.json`
- `meta_indice.json`
- `meta_referencia_do_percurso.json`
- `operacoes.json`

A regra geral é esta:
um fragmento deve poder ser lido ao mesmo tempo como unidade textual, unidade conceptual e unidade de integração estrutural.

---

## Princípio geral
Todo o fragmento deve poder responder, tanto quanto possível, às seguintes perguntas:

1. O que diz?
2. Sobre que zona do sistema recai?
3. Que operação realiza?
4. Que erro identifica, corrige ou evita?
5. Que papel pode desempenhar na montagem do livro?

---

## Schema mínimo obrigatório

### `fragment_id`
Identificador único do fragmento.

**Tipo:** string

**Exemplos:**
- `FRAG_0001`
- `FRAG_NOTA_2026_03_10_001`

---

### `texto_original`
Texto bruto do fragmento, sem normalização filosófica forte.

**Tipo:** string

---

### `origem`
Origem material do fragmento.

**Tipo:** object

**Campos sugeridos:**
- `tipo_origem`: string  
  Exemplos:
  - `conversa_chatgpt`
  - `nota_manual`
  - `documento_texto`
  - `ficheiro_md`
  - `ficheiro_txt`
  - `ficheiro_docx`
  - `audio_transcrito`
  - `fragmento_reconstruido`
- `ficheiro`: string | null
- `data`: string | null
- `contexto`: string | null

---

### `estado_processamento`
Estado técnico do fragmento no pipeline.

**Tipo:** string

**Valores operacionais:**
- `raw`
- `segmentado`
- `classificado`
- `revisto`
- `integrado`
- `arquivado`

---

## Schema estrutural principal

### `titulo_provisorio`
Nome curto atribuído ao fragmento para facilitar leitura e pesquisa.

**Tipo:** string | null

---

### `resumo_curto`
Resumo operacional do fragmento em 1–3 frases.

**Tipo:** string | null

---

### `tipo_fragmento`
Tipo funcional principal do fragmento.

**Tipo:** string

**Valores derivados do projeto e adaptados operacionalmente:**
- `afirmacao_estrutural`
- `fixacao_condicao_ontologica`
- `fixacao_limite_ontologico`
- `identificacao_impossibilidade_ontologica`
- `descricao_estrutural`
- `descricao_atualizacao`
- `identificacao_dependencia`
- `identificacao_continuidade`
- `diferenciacao_niveis`
- `identificacao_escala`
- `identificacao_campo`
- `identificacao_mediacao`
- `distincao_apreensao_representacao`
- `reinscricao_consciencia_real`
- `limitacao_reflexividade`
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
- `regularidade_estrutural`
- `observacao_metodologica`
- `transicao_narrativa`
- `proposicao_fonte`
- `fragmento_intuitivo`

---

### `zona_indice`
Zona estrutural principal do índice a que o fragmento pertence.

**Tipo:** string

**Valores esperados:**
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
- `P_PERCURSO_DO_ERRO_E_DA_DEGENERACAO`
- `P_PERCURSO_DA_DEGENERACAO_ETICA`
- `P_PERCURSO_DA_VIDA_BOA`
- `P_PERCURSO_DA_VIDA_BOA_FILOSOFICA`
- `P_PERCURSO_DA_VIDA_BOA_FILOSOFICA_ESPIRAL`
- `P_PERCURSO_INTEGRAL_DO_REAL_A_VIDA_BOA`
- `P_PERCURSO_ONTOLOGICAMENTE_ESTERIL_POR_INVERSAO_DIRECIONAL`

---

### `parte`
Parte principal do índice sequencial.

**Tipo:** string | null

**Valores esperados:**
- `PARTE_I`
- `PARTE_II`
- `PARTE_III`
- `PARTE_IV`
- `PARTE_V`
- `PARTE_VI`
- `PARTE_VII`

---

### `capitulo_sugerido`
Capítulo principal de inscrição do fragmento.

**Tipo:** string | null

**Valores possíveis:**
- `CAP_01_DISTINCAO`
- `CAP_02_ESTRUTURA_LIMITE`
- `CAP_03_DETERMINACAO_NAO_SER`
- `CAP_04_RELACAO_REAL_SER`
- `CAP_05_PODER_SER`
- `CAP_06_ATUALIZACAO_CONTINUIDADE`
- `CAP_07_REGULARIDADE_NECESSIDADE`
- `CAP_08_CAMPO`
- `CAP_09_ESCALA`
- `CAP_10_ESTABILIDADE_TEMPO`
- `CAP_11_LOCALIDADE`
- `CAP_12_SER_HUMANO`
- `CAP_13_REPRESENTACAO`
- `CAP_14_LINGUAGEM_MEDIACAO`
- `CAP_15_CONSCIENCIA`
- `CAP_16_LIBERDADE_SITUADA`
- `CAP_17_ADEQUACAO`
- `CAP_18_CRITERIO`
- `CAP_19_VERDADE`
- `CAP_20_ERRO`
- `CAP_21_CORRECAO`
- `CAP_22_CAMPO_POTENCIALIDADES`
- `CAP_23_RESPONSABILIDADE`
- `CAP_24_DIRECAO`
- `CAP_25_BEM_MAL`
- `CAP_26_DEVER_SER`
- `CAP_27_SISTEMA`
- `CAP_28_CULTURA`
- `CAP_29_INSTITUICAO`
- `CAP_30_TECNOLOGIA`

---

### `conceitos_centrais`
Conceitos explicitamente presentes ou fortemente implicados no fragmento.

**Tipo:** array[string]

---

### `conceito_alvo`
Conceito principal sobre o qual o fragmento opera.

**Tipo:** string | null

---

### `regime_principal`
Regime meta-índicial principal do fragmento.

**Tipo:** string | null

**Valores possíveis:**
- `REGIME_INSCRICAO_REAL`
- `REGIME_DESCRICAO_ESTRUTURAL`
- `REGIME_DIFERENCIACAO_ONTOLOGICA`
- `REGIME_CRITICA_REFLEXIVIDADE`
- `REGIME_CRITICA_SISTEMICA`
- `REGIME_EPISTEMOLOGICO`
- `REGIME_ETICO_ONTOLOGICO`
- `REGIME_CORRETIVO`

---

### `operacoes_chave`
Operações que o fragmento realiza ou mobiliza.

**Tipo:** array[string]

**Valores possíveis:** IDs de `operacoes.json`

---

### `erros_identificados`
Erros estruturais explicitamente identificados ou combatidos pelo fragmento.

**Tipo:** array[string]

**Valores possíveis:** ver `labels_erros.json`

---

### `estrutura_logica`
Como o fragmento funciona argumentativamente.

**Tipo:** array[string]

**Valores operacionais derivados do projeto:**
- `afirmacao`
- `deducao`
- `implicacao`
- `exclusao`
- `limitacao`
- `reducao_ao_absurdo`
- `distincao`
- `reinscricao`
- `subordinacao`
- `derivacao`
- `critica`
- `correcao`
- `transicao`

---

### `pressupostos_ontologicos`
Pressupostos ontológicos requeridos para o fragmento fazer sentido.

**Tipo:** array[string]

---

### `outputs_instalados`
O que o fragmento deixa instalado no sistema.

**Tipo:** array[string]

---

### `ligacoes_narrativas`
Ligações para outros capítulos, argumentos ou zonas.

**Tipo:** object

**Campos sugeridos:**
- `fundamenta`: array[string]
- `pressupoe`: array[string]
- `antecipa`: array[string]
- `corrige`: array[string]
- `contrasta_com`: array[string]

---

## Schema de maturidade filosófica

### `grau_maturidade`
Estado filosófico do fragmento.

**Tipo:** string

**Valores operacionais:**
- `bruto`
- `intuicao_relevante`
- `formulacao_promissora`
- `quase_formalizado`
- `nuclear`
- `auxiliar`
- `redundante`
- `descartar`

---

### `valor_estrutural`
Importância do fragmento para o sistema.

**Tipo:** string

**Valores sugeridos:**
- `fundacional`
- `estrutural`
- `operacional`
- `ilustrativo`
- `transicional`
- `marginal`

---

## Schema de revisão humana

### `validacao_humana`
Estado de validação pelo autor.

**Tipo:** string

**Valores:**
- `por_rever`
- `revisto`
- `validado`
- `reclassificado`
- `rejeitado`

---

### `notas_autor`
Notas livres do autor sobre o fragmento.

**Tipo:** string | null

---

## Objeto-exemplo

```json
{
  "fragment_id": "FRAG_0001",
  "texto_original": "Sem distinção não há algo.",
  "origem": {
    "tipo_origem": "nota_manual",
    "ficheiro": "notas_ontologia.md",
    "data": "2026-03-10",
    "contexto": "núcleo fundacional"
  },
  "estado_processamento": "classificado",
  "titulo_provisorio": "Distinção como condição mínima do algo",
  "resumo_curto": "O fragmento fixa a distinção como condição mínima para que algo possa ser.",
  "tipo_fragmento": "fixacao_condicao_ontologica",
  "zona_indice": "P_EIXO_ONTOLOGICO_NUCLEAR",
  "parte": "PARTE_I",
  "capitulo_sugerido": "CAP_01_DISTINCAO",
  "conceitos_centrais": ["distinção", "algo", "condição ontológica"],
  "conceito_alvo": "D_DISTINCAO",
  "regime_principal": "REGIME_INSCRICAO_REAL",
  "operacoes_chave": [
    "OP_FIXACAO_CONDICAO_ONTOLOGICA",
    "OP_AFIRMACAO_ESTRUTURAL"
  ],
  "erros_identificados": [],
  "estrutura_logica": ["afirmacao", "deducao"],
  "pressupostos_ontologicos": [],
  "outputs_instalados": ["distinção mínima como condição do algo"],
  "ligacoes_narrativas": {
    "fundamenta": ["ARG_DISTINCAO_MINIMA", "CAP_01_DISTINCAO"],
    "pressupoe": [],
    "antecipa": ["CAP_02_ESTRUTURA_LIMITE"],
    "corrige": [],
    "contrasta_com": []
  },
  "grau_maturidade": "nuclear",
  "valor_estrutural": "fundacional",
  "validacao_humana": "por_rever",
  "notas_autor": null
}