# README — Cadernos de Confrontos Filosóficos

## 1. Finalidade

Esta pasta reúne os **cadernos de redação por confronto** da fase `16_validacao_integral`.

A sua função é transformar a base já estabilizada da fase atual — especialmente a `adjudicacao_confrontos_filosoficos_restrita_v2.json` — numa camada intermédia de trabalho **diretamente utilizável para redação filosófica assistida**. Nesta altura do projeto, já não estamos a descobrir a arquitetura global do sistema; estamos a convertê-la numa **arquitetura de escrita, teste e reformulação de alto nível**. fileciteturn1file6 fileciteturn1file17

Os cadernos não substituem:

- a matriz de confronto filosófico;
- a matriz de pontes entre níveis;
- a matriz de ancoragem científica;
- o mapa dos campos do real;
- a adjudicação filosófica restringida.

Servem antes para **recolher, concentrar e disciplinar**, em formato redacional humano, aquilo que essas camadas já tornaram rastreável. fileciteturn1file4 fileciteturn1file13

---

## 2. Lugar desta pasta no pipeline

A fase `16_validacao_integral` já estabilizou os seguintes níveis:

1. proposições nucleares enriquecidas;
2. regimes de validação;
3. matriz de pontes entre níveis;
4. matriz de ancoragem científica;
5. mapa de campos do real;
6. matriz de confronto filosófico;
7. adjudicação filosófica;
8. restrição redacional v2. fileciteturn1file7 fileciteturn1file5

O que **ainda não estava feito** era a camada seguinte aplicada à escrita:

- cadernos de redação por confronto;
- blocos de redação canónica;
- integração dos confrontos prioritários em texto filosófico corrido. fileciteturn1file1

Por isso, esta pasta corresponde ao **próximo passo imediato** recomendado na execução atual da fase. fileciteturn1file1 fileciteturn1file3

---

## 3. Fonte principal dos cadernos

A fonte principal desta subfase é:

- `16_validacao_integral/01_dados/adjudicacao_confrontos_filosoficos_restrita_v2.json`

Esta é, neste momento, a melhor base para continuação do pipeline, porque já preserva os `confronto_id` e as subestruturas relevantes como objetos/listas estruturadas, ao mesmo tempo que comprime o excesso redacional herdado da adjudicação anterior. fileciteturn1file5 fileciteturn1file14

Fontes complementares obrigatórias:

- `16_validacao_integral/01_dados/matriz_confronto_filosofico_v1.json`
- `16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json`
- `16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json`
- `16_validacao_integral/01_dados/mapa_campos_do_real_v1.json`
- `16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json` fileciteturn1file17

Sempre que necessário, os cadernos podem ainda recorrer aos artefactos herdados da árvore do pensamento, mas apenas de forma subordinada à fase atual. fileciteturn1file19

---

## 4. O que é um caderno de confronto

Um caderno de confronto é uma **unidade redacional intermédia** dedicada a um único `CFxx`.

Não é ainda um capítulo final. Não é também apenas um dump de JSON. É um artefacto híbrido, feito para:

- explicitar a pergunta central do confronto;
- fixar uma tese canónica provisória;
- reunir as teses de sustentação mínimas;
- ordenar objeções prioritárias;
- ligar o confronto às proposições, pontes, ancoragens e campos relevantes;
- preparar a redação humana disciplinada do confronto. fileciteturn1file1 fileciteturn1file4

Em termos metodológicos, estes cadernos situam-se entre:

- a **cartografia auditável do sistema**;
- a **adjudicação dos grandes problemas filosóficos**;
- a **preparação da redação canónica**. fileciteturn1file7

---

## 5. Formato recomendado

Nesta fase, o formato mais adequado é **Markdown por confronto**, eventualmente acompanhado mais tarde por um índice JSON. A própria documentação da execução atual indica que a melhor solução, neste momento, tende a ser **Markdown por confronto** ou **JSON + Markdown**, porque a fase seguinte é claramente de redação assistida. fileciteturn1file0

Regra prática:

- um ficheiro `.md` por confronto;
- um caderno por `CFxx`;
- estrutura fixa e repetível;
- texto curto, disciplinado e diretamente redacional.

---

## 6. Estrutura mínima de cada caderno

Cada ficheiro `CFxx_dossier_confronto.md` deve conter, pelo menos, as seguintes secções:

### 6.1. Identificação

- `confronto_id`
- título curto
- prioridade redacional
- grau de risco
- estado herdado
- decisão de adjudicação restrita
- necessidade de revisão humana

### 6.2. Pergunta central

Formulação explícita da pergunta filosófica a que o confronto responde.

### 6.3. Tese canónica provisória

Formulação curta da resposta que o sistema pretende sustentar, em versão ainda aberta a revisão.

### 6.4. Teses de sustentação

Lista curta das teses mínimas sem as quais a resposta não se sustenta.

### 6.5. Distinções mínimas

Distinções conceptuais necessárias para impedir mistura indevida entre níveis, domínios ou sentidos.

### 6.6. Objeções priorizadas

Objeções fortes que o confronto deve tratar logo, e não deixar para menção lateral. Esta exigência já vem explicitamente marcada na lógica da adjudicação restringida. fileciteturn1file11

### 6.7. Articulação estrutural

- proposições nucleares envolvidas;
- pontes entre níveis relacionadas;
- ancoragens científicas relacionadas;
- campos do real relacionados.

Esta articulação é importante porque a matriz de confronto não substitui as restantes matrizes; integra-as quando relevantes. fileciteturn1file8

### 6.8. Autores e tradições a mobilizar

Apenas os estritamente necessários para o confronto em causa.

### 6.9. Sequência mínima de redação

Sequência curta dos passos de exposição do confronto.

### 6.10. Checklist de fecho

Lista de controlo mínima para saber se o confronto ficou realmente tratável em redação canónica.

### 6.11. Notas de revisão humana

Espaço para reservas, reformulações pendentes, zonas de risco e dúvidas ainda abertas.

---

## 7. Convenção de nomes

Padrão recomendado:

- `CF01_dossier_confronto.md`
- `CF02_dossier_confronto.md`
- `CF03_dossier_confronto.md`
- ...
- `CF18_dossier_confronto.md`

Opcionalmente, pode acrescentar-se um sufixo temático curto, por exemplo:

- `CF08_dossier_confronto_causalidade_emergencia.md`
- `CF10_dossier_confronto_normatividade.md`

Mas o `confronto_id` deve aparecer sempre no início do nome do ficheiro.

---

## 8. Ordem recomendada de abertura dos cadernos

A ordem mais sensata, neste momento, é começar pelos confrontos mais críticos:

1. `CF08` — causalidade, emergência e passagem de níveis;
2. `CF10` — dano, bem, mal e normatividade;
3. `CF11` — responsabilidade, dignidade e vida boa;
4. `CF14` — critério último e fecho do sistema;
5. `CF16` — passagem entre regimes de validação. fileciteturn1file1 fileciteturn1file6

Estes confrontos são os centros de gravidade mais fortes da fase atual e os pontos onde o risco filosófico e o risco de fecho prematuro permanecem mais altos. fileciteturn1file6

---

## 9. Relação com os pontos críticos transversais

Além dos cadernos por confronto, esta fase deve manter atenção especial aos seguintes pontos críticos marcados para revisão humana:

- `P30`
- `P44`
- `P46`
- `P47`
- `P50`
- `P51` fileciteturn1file18

E às seguintes zonas críticas já assinaladas noutros artefactos:

- `CR01`
- `CR04`
- `CR05` no mapa dos campos do real; fileciteturn1file15
- `AC01`
- `AC02`
- `AC03` na ancoragem científica; fileciteturn1file18
- pontes estruturais de risco alto/crítico, sobretudo nas passagens entre níveis já identificadas pela fase pós-árvore. fileciteturn1file18

Os cadernos devem, por isso, ser redigidos de modo a **não perder estes nós transversais**, mesmo quando o foco principal seja um único confronto.

---

## 10. Regra metodológica de prudência

A regra de prudência desta subfase mantém-se a mesma da fase de validação integral:

> **não misturar ontologia, ciência, normatividade e cartografia regional como se fossem o mesmo tipo de justificação**. fileciteturn1file12

Por isso, em cada caderno:

- a filosofia entra como confronto, clarificação e teste estrutural;
- a ciência entra como compatibilidade, suporte, restrição ou determinação material;
- as pontes entram como mediações explícitas entre níveis;
- os campos entram como regionalização do real;
- a redação canónica só deve avançar quando esta separação estiver suficientemente clara. fileciteturn1file4 fileciteturn1file12

---

## 11. O que estes cadernos ainda não são

Esta pasta **não contém ainda**:

- capítulos finais do sistema;
- validação filosófica definitivamente concluída;
- bibliografia final integrada;
- reintegração final no mapa dedutivo global.

Essa etapa pertence à fase seguinte, em que os confrontos já trabalhados serão reorganizados em blocos maiores de redação canónica, por exemplo:

- ontologia fundamental;
- manifestação e presença;
- vida, corpo e consciência;
- linguagem, sentido e verdade;
- normatividade, responsabilidade e vida boa;
- metaestrutura do sistema. fileciteturn1file3

---

## 12. Resultado esperado desta pasta

No fim desta subfase, esta pasta deve permitir:

- abrir um dossier por confronto filosoficamente tratável;
- priorizar os confrontos mais críticos;
- concentrar neles a revisão humana onde ela é realmente necessária;
- preparar a transição para blocos de redação canónica;
- evitar regressos prematuros à extração, salvo se a redação detetar lacunas reais. fileciteturn1file3

Em fórmula curta:

**matriz de confronto + adjudicação restringida -> cadernos de confronto -> redação canónica por blocos -> reintegração disciplinada no sistema global**. fileciteturn1file3 fileciteturn1file6
