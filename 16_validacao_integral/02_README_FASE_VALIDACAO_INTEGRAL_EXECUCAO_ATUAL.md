# README — Estado da execução da fase `16_validacao_integral`

## 1. Finalidade desta fase

A fase `16_validacao_integral` serve para transformar o material já extraído e organizado da árvore do pensamento numa arquitetura de validação auditável, separando explicitamente os diferentes regimes de teste do sistema: confronto filosófico, ancoragem científica, pontes entre níveis e cartografia dos campos do real. Esta lógica já estava prevista no README da fase pós-árvore e na documentação das matrizes derivadas. fileciteturn10file1turn10file4

O objetivo prático desta fase não é ainda escrever a versão final dos capítulos filosóficos, mas:

- identificar o que precisa de validação;
- regionalizar onde cada proposição opera;
- explicitar as passagens entre níveis;
- separar o que depende de ciência e o que depende de filosofia;
- preparar uma adjudicação disciplinada e redacionalmente usável. fileciteturn10file1turn10file2

---

## 2. O que foi feito nesta execução

Nesta ronda de trabalho foram executados e validados os seguintes passos principais.

### 2.1. Extração e enriquecimento das proposições nucleares
Foi gerado/atualizado o ficheiro base das proposições nucleares enriquecidas, que serve de input a toda a macrofase posterior. Esta etapa ficou concluída sem erros de validação, segundo o histórico de execução descrito na conversa e os ficheiros que serviram depois de fonte às matrizes seguintes.

### 2.2. Atribuição dos regimes de validação
As proposições passaram a estar marcadas por regime de validação, permitindo distinguir o que exige confronto filosófico, ancoragem científica, ponte entre níveis e cartografia de campo. Este passo ficou estabilizado antes da geração das matrizes derivadas e permitiu alimentar os passos seguintes. fileciteturn10file1turn10file2

### 2.3. Geração da matriz de pontes entre níveis
Foi gerada a matriz de pontes entre níveis, que passou a funcionar como peça de rastreabilidade das transições entre níveis do real e dos saltos que requerem mediação. Mais tarde, esta matriz foi absorvida pela matriz de confronto filosófico e pela adjudicação. A matriz de confronto mostra que 17 dos 18 confrontos mobilizam pontes entre níveis. fileciteturn10file1turn10file18

### 2.4. Geração da matriz de ancoragem científica
Foi gerada a matriz de ancoragem científica, separando onde o sistema toca domínios científicos e onde a ciência funciona como restrição ou compatibilidade. Na matriz de confronto filosófico, 15 dos 18 confrontos já aparecem com ancoragem científica associada. fileciteturn10file1turn10file18

### 2.5. Geração do mapa de campos do real
Foi criado o `mapa_campos_do_real_v1.json`, que regionaliza as proposições no espaço dos campos do real. O relatório respetivo mostra:

- 6 campos;
- 34 proposições mapeadas;
- 3 campos com revisão humana;
- 2 campos com incidência normativa;
- 5 campos multiescala. fileciteturn10file4turn10file16

Os campos marcados para revisão humana foram:

- `CR01` por agregar `P44`, `P46`, `P47`;
- `CR04` por agregar `P50`, `P51`;
- `CR05` por agregar `P30`. fileciteturn10file16

### 2.6. Construção do schema preliminar e do inventário preliminar de problemas filosóficos
Antes da matriz de confronto filosófico, foram preparados dois artefactos intermédios:

- `schema_confronto_filosofico_preliminar_v1.json`;
- `inventario_preliminar_de_problemas_filosoficos_v1.json`.

A função destes ficheiros foi fixar a unidade de confronto como **problema filosófico estruturado**, e não como mero elenco de autores.

### 2.7. Geração da matriz de confronto filosófico
Foi gerada a `matriz_confronto_filosofico_v1.json`. Os números principais desta matriz são:

- 18 confrontos;
- 18 problemas inventariados;
- 51 proposições que precisam de confronto filosófico;
- 51 proposições cobertas;
- 0 proposições sem cobertura;
- 9 confrontos com revisão humana;
- 18 confrontos com resposta canónica;
- 11 confrontos com capítulo próprio;
- 17 confrontos com pontes;
- 15 confrontos com ancoragem;
- 16 confrontos de risco alto ou crítico;
- 4 confrontos metaestruturais. fileciteturn10file1turn10file18

Esta matriz passou a ser a cartografia operacional da “batalha filosófica” do sistema. fileciteturn10file1

### 2.8. Adjudicação dos confrontos filosóficos
Foi gerada a `adjudicacao_confrontos_filosoficos_v1.json`, que transformou os confrontos por preencher em unidades redacionalmente operáveis. O relatório respetivo mostra:

- 18 confrontos adjudicados;
- 9 revistos;
- 9 preenchidos;
- 9 com revisão humana;
- 5 com decisão explícita de revisão humana;
- 9 de prioridade crítica;
- 15 com ciência articulada;
- 17 com pontes articuladas;
- média de confiança heurística 0,599. fileciteturn10file0turn10file2

As decisões de adjudicação distribuíram-se entre:

- `preservar_com_restricoes`: 5;
- `preservar_e_explicitar`: 8;
- `revisao_humana_necessaria`: 5. fileciteturn10file0turn10file2

### 2.9. Restrição redacional da adjudicação — v1 e v2
Houve duas iterações relevantes.

#### v1
A `v1` conseguiu restringir quantitativamente a adjudicação, mas na primeira tentativa houve erro de mapeamento de chaves; numa segunda iteração passou a validar, embora ainda achatasse algumas subestruturas em strings. Isso ficou evidente no histórico dos relatórios e no próprio JSON. fileciteturn10file8turn10file12turn10file17

#### v2
A `v2` é a versão boa e utilizável desta etapa. O relatório mostra:

- 18 confrontos restringidos;
- validação sem erros;
- preservação dos `confronto_id`;
- preservação das subestruturas como objetos/listas estruturadas. fileciteturn10file5turn10file15

A redução quantitativa da v2 foi a seguinte:

- autores: 139 → 77;
- tradições: 156 → 65;
- temas: 285 → 128;
- objeções fortes: 91 → 69;
- teses de sustentação: 83 → 69;
- objeções priorizadas: 88 → 52;
- checklist: 109 → 72;
- sequência de redação: 109 → 54;
- proposições em articulação: 100 → 67;
- pontes em articulação: 59 → 46;
- ancoragens em articulação: 23 → 21. fileciteturn10file11turn10file15

Esta é, neste momento, a melhor base para continuação do pipeline. fileciteturn10file5turn10file9

---

## 3. Ficheiros diretamente em causa

### 3.1. Ficheiros-base de dados

- `16_validacao_integral/01_dados/proposicoes_nucleares_enriquecidas_v1.json`
- `16_validacao_integral/01_dados/matriz_pontes_entre_niveis_v1.json`
- `16_validacao_integral/01_dados/matriz_ancoragem_cientifica_v1.json`
- `16_validacao_integral/01_dados/mapa_campos_do_real_v1.json` fileciteturn10file4

### 3.2. Ficheiros preliminares de confronto filosófico

- `16_validacao_integral/01_dados/schema_confronto_filosofico_preliminar_v1.json`
- `16_validacao_integral/01_dados/inventario_preliminar_de_problemas_filosoficos_v1.json`

### 3.3. Ficheiros principais gerados na batalha filosófica

- `16_validacao_integral/01_dados/matriz_confronto_filosofico_v1.json` fileciteturn10file1
- `16_validacao_integral/01_dados/adjudicacao_confrontos_filosoficos_v1.json` fileciteturn10file2
- `16_validacao_integral/01_dados/adjudicacao_confrontos_filosoficos_restrita_v2.json` fileciteturn10file5

### 3.4. Relatórios principais

- `16_validacao_integral/02_outputs/relatorio_geracao_mapa_campos_do_real_v1.txt` fileciteturn10file16
- `16_validacao_integral/02_outputs/relatorio_geracao_matriz_confronto_filosofico_v1.txt` fileciteturn10file1
- `16_validacao_integral/02_outputs/relatorio_adjudicacao_confrontos_filosoficos_v1.txt` fileciteturn10file0
- `16_validacao_integral/02_outputs/relatorio_restricao_adjudicacao_confrontos_filosoficos_v2.txt` fileciteturn10file15

### 3.5. Scripts produzidos/ajustados nesta ronda

- `gerar_mapa_campos_do_real_v1.py`
- `gerar_matriz_confronto_filosofico_v1.py`
- `adjudicar_confrontos_filosoficos_v1.py`
- `restringir_adjudicacao_confrontos_filosoficos_v1.py`
- `restringir_adjudicacao_confrontos_filosoficos_v2.py`

---

## 4. O que estamos a fazer, em termos metodológicos

Neste momento, o projeto já não está na fase de mera extração. Está numa fase intermédia entre:

- **cartografia auditável do sistema**;
- **adjudicação dos grandes problemas filosóficos**;
- **preparação da redação canónica**.

Em termos simples:

1. o sistema foi desdobrado em proposições nucleares;
2. essas proposições foram classificadas por regime de validação;
3. foram produzidas matrizes auxiliares que separam ciência, transições e campos;
4. foi construída a matriz de confronto filosófico;
5. os confrontos foram adjudicados;
6. a adjudicação foi restringida para ficar redacionalmente disciplinada e estruturalmente reaproveitável. fileciteturn10file1turn10file2turn10file5

Isto significa que a fase atual já não é “descobrir o que existe no corpus”, mas sim **transformar o que já foi descoberto numa arquitetura de redação e validação de alto nível**. fileciteturn10file2turn10file5

---

## 5. Estado atual da fase

O estado atual pode ser descrito assim:

### 5.1. O que está estabilizado

- proposições nucleares enriquecidas;
- regimes de validação;
- matriz de pontes entre níveis;
- matriz de ancoragem científica;
- mapa de campos do real;
- inventário preliminar de problemas filosóficos;
- matriz de confronto filosófico;
- adjudicação filosófica;
- restrição redacional v2. fileciteturn10file4turn10file1turn10file2turn10file5

### 5.2. O que ainda não está feito

Ainda não foi gerada a camada seguinte de trabalho aplicada à escrita, isto é:

- cadernos de redação por confronto;
- blocos de redação canónica já segmentados por confronto ou subcapítulo;
- integração final dos confrontos prioritários num texto filosófico corrido;
- eventual reintegração no mapa dedutivo mais amplo. 

### 5.3. Onde estão os centros de gravidade mais fortes

Pelos relatórios e pela restrição v2, os confrontos que pedem mais atenção imediata são:

- `CF08` — causalidade, emergência e passagem de níveis;
- `CF10` — dano, bem, mal e normatividade;
- `CF11` — responsabilidade, dignidade e vida boa;
- `CF14` — critério último e fecho do sistema;
- `CF16` — passagem entre regimes de validação. fileciteturn10file7turn10file15

Estes são os pontos onde o risco filosófico e o risco de fecho prematuro continuam mais altos. fileciteturn10file0turn10file2

---

## 6. Próximos passos imediatos

### 6.1. Gerar cadernos de redação por confronto
O próximo passo mais útil é criar um script do tipo:

- `gerar_cadernos_redacao_confrontos_v1.py`

Esse script deve ler preferencialmente a `adjudicacao_confrontos_filosoficos_restrita_v2.json` e, para cada confronto prioritário, produzir um caderno de redação com:

- pergunta central;
- tese central restringida;
- teses de sustentação;
- distinções mínimas;
- objeções priorizadas;
- articulação estrutural restrita;
- sequência de redação;
- checklist de fecho.

### 6.2. Começar pelos confrontos críticos
A ordem mais sensata é começar por:

1. `CF08`;
2. `CF10`;
3. `CF11`;
4. `CF14`;
5. `CF16`. fileciteturn10file7turn10file15

### 6.3. Decidir formato dos cadernos
Antes de automatizar demasiado, convém decidir se os cadernos vão sair:

- um ficheiro por confronto;
- um único JSON com todos os cadernos;
- um conjunto de Markdown files para redação humana.

A melhor solução, neste momento, tende a ser **Markdown por confronto** ou JSON + Markdown, porque a fase seguinte é claramente de redação assistida.

---

## 7. Próximos passos futuros

### 7.1. Redação canónica por confronto
Depois dos cadernos, o passo natural é gerar blocos de redação canónica, começando pelos confrontos críticos e estruturais.

### 7.2. Revisão humana filosófica focalizada
Os confrontos que já ficaram marcados como mais delicados devem receber revisão humana focalizada antes de qualquer integração final. Isto vale em especial para os confrontos de risco alto/crítico e para os campos `CR01`, `CR04` e `CR05`. fileciteturn10file16turn10file0

### 7.3. Integração em capítulos ou macroblocos
Depois da redação por confronto, será necessário reorganizar o material em unidades maiores, por exemplo:

- ontologia fundamental;
- manifestação e presença;
- vida, corpo e consciência;
- linguagem, sentido e verdade;
- normatividade, responsabilidade e vida boa;
- metaestrutura do sistema.

### 7.4. Eventual regresso controlado à extração
Só depois desta fase fará sentido avaliar se há lacunas reais que obriguem a regressar ao nível dos fragmentos ou argumentos. Neste momento, isso **não é o próximo passo**; apenas uma possibilidade futura, caso a redação detete zonas filosoficamente subextraídas.

### 7.5. Reintegração no sistema global
No futuro, será necessário articular esta fase com o mapa dedutivo mais amplo, para que a validação filosófica não fique apenas como camada lateral, mas seja reincorporada como justificação do próprio percurso do sistema.

---

## 8. Resumo executivo

Nesta execução, a fase `16_validacao_integral` avançou de forma substancial e consistente.

Foi concluído o encadeamento:

- proposições enriquecidas;
- regimes de validação;
- pontes entre níveis;
- ancoragem científica;
- mapa de campos do real;
- inventário e schema preliminares de confronto filosófico;
- matriz de confronto filosófico;
- adjudicação dos confrontos;
- restrição redacional v2. fileciteturn10file4turn10file1turn10file2turn10file5

O estado atual é bom: a arquitetura de validação está montada, a batalha filosófica está explicitada, e já existe uma base restringida e estruturalmente reaproveitável para a próxima fase.

O próximo passo imediato recomendado é:

- **gerar cadernos de redação por confronto**, começando por `CF08`, `CF10`, `CF11`, `CF14` e `CF16`. fileciteturn10file7turn10file15
