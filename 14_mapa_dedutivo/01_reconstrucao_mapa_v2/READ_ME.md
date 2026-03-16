# README — Fase atual do projeto: fecho canónico do mapa dedutivo

## 1. Em que fase o projeto está neste momento

Neste momento, o projeto já saiu claramente da fase de extração, classificação e diagnóstico estrutural. Também já saiu da fase de mera reconstrução dedutiva geral.

A fase atual é esta:

**fechar canonicamente o mapa dedutivo**, isto é, transformar a reconstrução já obtida numa arquitetura final em que cada passo tenha:

- formulação filosófica canónica;
- estatuto dedutivo claro;
- justificação mínima suficiente;
- objeção letal identificada e bloqueada;
- mediações explícitas onde o salto ainda subsiste;
- eventual subpasso formal quando a passagem não fecha sem ele.

Isto quer dizer que o projeto já não está a perguntar:

- que material existe;
- onde os fragmentos pressionam o sistema;
- qual é a espinha dorsal provável do mapa.

Agora está a perguntar:

- **como fechar cada passagem para que a linha inteira se torne inevitável**;
- **onde a dedução ainda depende de mediações subentendidas**;
- **que formulação final deve ficar como versão canónica de cada proposição**.

---

## 2. O que já foi feito e o que isso significa

### 2.1. Camada estrutural de base já existente

O projeto já tem uma base ontológica e metaestrutural suficientemente madura para suportar fecho canónico:

- `todos_os_conceitos.json`
- `operacoes.json`
- `meta_referencia_do_percurso.json`
- `meta_indice.json`

Estes ficheiros funcionam como **gramática do sistema**. Eles não devem comandar sozinhos a ordem final do mapa, mas continuam a servir para verificar coerência terminológica, regime de operações e enquadramento metaestrutural.

### 2.2. Camada de índice e argumentos já existente

O projeto já tem a arquitetura geral do sistema organizada em capítulos, percursos e argumentos:

- `indice_sequencial.json`
- `indice_por_percurso.json`
- `indice_argumentos.json`
- `argumentos_unificados.json`

Estes ficheiros são a **infraestrutura de dependência e articulação**. São importantes para perceber:

- a distribuição do sistema por percurso;
- as dependências argumentativas;
- o lugar de cada zona no todo.

### 2.3. Camada fragmentária já tratada

O corpus já foi suficientemente preparado para não exigir nova fase extrativa:

- `fragmentos_resegmentados.json`
- `cadencia_schema.json`
- `cadencia_extraida.json`
- `tratamento_filosofico_fragmentos.json`
- `impacto_fragmentos_no_mapa.json`
- `impacto_fragmentos_no_mapa_relatorio_validacao.json`

Esta camada serve agora sobretudo para:

- densificação justificativa;
- apoio editorial;
- bloqueio de objeções;
- confirmação de mediações.

Ela **já não deve comandar a arquitetura**. O projeto já mostrou que o impacto dominante dos fragmentos foi de explicitação e densificação, não de destruição arquitetónica. No relatório agregado anterior, os efeitos principais foram dominados por “explicita” e as ações recomendadas por “densificar”. fileciteturn3file1

### 2.4. Camada de mapa dedutivo e reconstrução já existente

Já foram produzidas e usadas as camadas de reconstrução e revisão:

- `02_mapa_dedutivo_arquitetura_fragmentos.json`
- `revisao_estrutural_do_mapa.json`
- `mapa_dedutivo_reconstrucao_inevitavel_v3.json`
- `relatorio_reconstrucao_inevitavel_v3.json`
- `fechador_canonico_mapa_v4.py`
- `matriz_inevitabilidades_v4.json`
- `mapa_dedutivo_precanonico_v4.json`
- `relatorio_fecho_canonico_v4.json`

Esta é a camada decisiva da fase atual.

O `relatorio_fecho_canonico_v4.json` mostra que, dos 51 passos, há **22 abertos, 22 quase fechados e 7 fechados**; as fragilidades dominantes são de **formulação (19)**, **mediação (18)** e **justificação (13)**; e os passos com subpasso sugerido são **P25, P28, P33, P36, P42, P47 e P50**. fileciteturn3file1

Isto significa que o problema atual já não é descobrir o mapa, mas **fechar as inevitabilidades locais**.

### 2.5. Camada de fecho local por corredor já existente

O projeto já tem fechos ou dossiês focados para as zonas críticas:

- `fecho_manual_corredor_P25_P30.json`
- `fecho_manual_corredor_P33_P37.json`
- `fecho_manual_corredor_P42_P48.json`
- `fecho_manual_corredor_P50.json`
- `dossier_corredor_P25_P30.json`
- `dossier_corredor_P33_P37.json`
- `dossier_corredor_P42_P48.json`
- `dossier_corredor_P50.json`

Os dossiês v4 confirmam que os corredores realmente críticos continuam a ser:

- **P25–P30**: 5 passos abertos e 1 quase fechado; subpassos em **P25** e **P28**. fileciteturn3file8
- **P33–P37**: 3 passos abertos e 2 quase fechados; subpassos em **P33** e **P36**. fileciteturn3file3
- **P42–P48**: 2 passos abertos e 5 quase fechados; subpassos em **P42** e **P47**. fileciteturn3file2
- **P50**: 1 passo quase fechado; subpasso em **P50**. fileciteturn3file9

---

## 3. O que se está a fazer agora, em termos exatos

A fase atual consiste em montar um **pipeline de fecho canónico assistido**.

Isto quer dizer que o trabalho agora é composto por três operações articuladas:

1. **saneamento estrutural** do mapa pré-canónico;
2. **fecho local das inevitabilidades** por passo e por corredor;
3. **consolidação final** das decisões canónicas aprovadas.

Em linguagem mais simples:

- o mapa já foi reconstruído;
- o fechador canónico já identificou onde ainda falta formulação, mediação e justificação;
- o próximo passo é usar essa informação para produzir as decisões finais que transformarão o mapa pré-canónico em mapa canónico final.

---

## 4. O que o estado atual dos ficheiros já mostra

### 4.1. O mapa não precisa de ser refeito de raiz

O estado atual não aponta para colapso arquitetónico. Aponta para **fecho fino localizado**.

### 4.2. O principal défice atual é mediacional e redacional

As fragilidades dominantes do v4 são:

- `formulacao`: 19
- `mediacao`: 18
- `justificacao`: 13

Há ainda texto meta-editorial detetado em vários passos, sobretudo nos corredores críticos e no fecho ético. fileciteturn3file1

### 4.3. Os corredores de maior trabalho estão confirmados

Os dossiês v4 deixam claro onde a energia do próximo ciclo deve ser gasta:

- **P25–P30**: apreensão, representação, linguagem, consciência, liberdade, reflexividade. fileciteturn3file8
- **P33–P37**: critério, verdade, erro, correção. fileciteturn3file3
- **P42–P48**: direção, bem, mal, dever-ser, normatividade. fileciteturn3file2
- **P50**: dignidade. fileciteturn3file9

### 4.4. O projeto já sabe o que precisa de subpasso

Os subpassos sugeridos não são marginais. Eles assinalam os sítios onde a dedução ainda salta:

- `P25`: distinguir apreensão de interpretação e de representação. fileciteturn3file8
- `P33`: mostrar por que um critério puramente interno não mede adequação ao real. fileciteturn3file3
- `P42`: explicitar a direção ontológica sem apelo moral externo. fileciteturn3file2
- `P50`: fechar a derivação da dignidade a partir do estatuto do ser reflexivo real. fileciteturn3file9

---

## 5. Objetivo da fase seguinte

O objetivo da fase seguinte é produzir um **mapa dedutivo canónico final**, ou muito próximo disso.

Esse resultado final deverá existir pelo menos em dois ficheiros:

- `mapa_dedutivo_canonico_final.json`
- `relatorio_final_de_inevitabilidades.json`

Idealmente, poderá também existir uma fonte intermédia de decisões aprovadas, por exemplo:

- `decisoes_canonicas_intermedias.json`

---

## 6. Arquitetura técnica recomendada a partir daqui

A arquitetura técnica recomendada é simples e controlável.

### 6.1. Número de scripts

A arquitetura recomendada é esta:

- **2 scripts principais**
- **1 biblioteca de prompts/templates**
- **1 conjunto de outputs intermédios**

Não é aconselhável fazer um único script monolítico. Também não é aconselhável criar muitos scripts dispersos.

A forma mais limpa é separar:

1. **orquestração da API e dos prompts**
2. **consolidação final das decisões**

### 6.2. Script 1 — orquestrador da API e dos prompts

Nome sugerido:

- `orquestrador_fecho_canonico_api.py`

Função:

- ler a matriz e os dossiês;
- escolher prioridades;
- montar o contexto do prompt;
- chamar a API do modelo;
- guardar cada resposta de forma auditável.

Este script **não deve alterar diretamente o mapa final**. Deve apenas produzir decisões candidatas.

#### Inputs principais do script 1

Obrigatórios:

- `matriz_inevitabilidades_v4.json`
- `mapa_dedutivo_precanonico_v4.json`
- `relatorio_fecho_canonico_v4.json`
- `dossier_corredor_P25_P30.json`
- `dossier_corredor_P33_P37.json`
- `dossier_corredor_P42_P48.json`
- `dossier_corredor_P50.json`

Secundários, para enriquecimento de contexto quando necessário:

- `revisao_estrutural_do_mapa.json`
- `02_mapa_dedutivo_arquitetura_fragmentos.json`
- `indice_por_percurso.json`
- `argumentos_unificados.json`
- `impacto_fragmentos_no_mapa.json`
- `tratamento_filosofico_fragmentos.json`

#### Outputs do script 1

Sugestão de outputs:

- `decisoes_canonicas_intermedias.json`
- pasta `prompts_enviados/`
- pasta `respostas_modelo/`
- pasta `logs_api/`

Cada resposta deve ser gravada com:

- identificador do passo/corredor;
- tipo de prompt usado;
- timestamp;
- input enviado;
- output recebido;
- estado de validação.

### 6.3. Script 2 — consolidador final

Nome sugerido:

- `consolidador_fecho_canonico.py`

Função:

- ler as decisões intermédias aprovadas;
- atualizar formulações canónicas;
- incorporar subpassos aceites;
- fechar campos do mapa;
- gerar a versão final consolidada.

#### Inputs principais do script 2

Obrigatórios:

- `mapa_dedutivo_precanonico_v4.json`
- `decisoes_canonicas_intermedias.json`

Secundários:

- `matriz_inevitabilidades_v4.json`
- `relatorio_fecho_canonico_v4.json`
- dossiês de corredor

#### Outputs do script 2

- `mapa_dedutivo_canonico_final.json`
- `relatorio_final_de_inevitabilidades.json`
- opcionalmente `mapa_dedutivo_canonico_final_legivel.json`

---

## 7. Arquitetura dos prompts

Os prompts não devem ser genéricos.

Devem existir como templates reutilizáveis, cada um com função única. A biblioteca de prompts pode ficar numa pasta `prompts/`.

### 7.1. Prompt de formulação canónica

Ficheiro sugerido:

- `prompts/prompt_formulacao_canonica.txt`

Objetivo:

- produzir formulação canónica curta, técnica e dedutiva;
- escolher a melhor formulação;
- limpar texto meta-editorial.

Usa sobretudo:

- `mapa_dedutivo_precanonico_v4.json`
- `matriz_inevitabilidades_v4.json`
- `revisao_estrutural_do_mapa.json`
- dossiê do corredor respetivo

### 7.2. Prompt de fecho mediacional

Ficheiro sugerido:

- `prompts/prompt_fecho_mediacional.txt`

Objetivo:

- descobrir a mediação em falta entre dois passos;
- decidir se é preciso subpasso;
- propor a formulação do subpasso.

Usa sobretudo:

- `matriz_inevitabilidades_v4.json`
- dossiê do corredor
- `02_mapa_dedutivo_arquitetura_fragmentos.json`
- `indice_por_percurso.json`

### 7.3. Prompt de fecho justificativo

Ficheiro sugerido:

- `prompts/prompt_fecho_justificativo.txt`

Objetivo:

- dizer por que o passo é necessário;
- por que o anterior não basta;
- por que não pode ser suprimido.

Usa sobretudo:

- `matriz_inevitabilidades_v4.json`
- `revisao_estrutural_do_mapa.json`
- `argumentos_unificados.json`

### 7.4. Prompt de objeção letal

Ficheiro sugerido:

- `prompts/prompt_objecao_letal.txt`

Objetivo:

- identificar a melhor objeção contra o passo;
- explicar por que ela parece plausível;
- mostrar por que falha;
- propor o texto curto de bloqueio.

Usa sobretudo:

- `matriz_inevitabilidades_v4.json`
- dossiê do corredor
- `impacto_fragmentos_no_mapa.json`
- `tratamento_filosofico_fragmentos.json`

### 7.5. Prompt de teste de supressão

Ficheiro sugerido:

- `prompts/prompt_teste_supressao.txt`

Objetivo:

- testar se o passo é realmente inevitável;
- verificar o que colapsa se o passo for retirado.

Usa sobretudo:

- `matriz_inevitabilidades_v4.json`
- `mapa_dedutivo_precanonico_v4.json`

### 7.6. Prompt de arbitragem de corredor

Ficheiro sugerido:

- `prompts/prompt_arbitragem_corredor.txt`

Objetivo:

- fechar a sequência mínima do corredor;
- validar subpassos;
- selecionar formulações finais do corredor;
- assinalar o que ainda exige decisão humana.

Usa sobretudo:

- `dossier_corredor_P25_P30.json`
- `dossier_corredor_P33_P37.json`
- `dossier_corredor_P42_P48.json`
- `dossier_corredor_P50.json`

---

## 8. Ordem recomendada de execução

A ordem de trabalho não deve ser P01–P51 em linha reta.

Deve seguir a criticidade já apurada pelos dossiês e pelo relatório v4.

### 8.1. Primeiro corredor: P33–P37

Razão:

- coração epistemológico do sistema;
- mistura formulação, mediação e justificação;
- subpassos em P33 e P36. fileciteturn3file3

### 8.2. Segundo corredor: P25–P30

Razão:

- fecha apreensão, representação, linguagem, consciência, liberdade e reflexividade;
- é uma das zonas mais abertas do mapa;
- subpassos em P25 e P28. fileciteturn3file8 fileciteturn3file7

### 8.3. Terceiro corredor: P42–P48

Razão:

- faz a transição da correção prática para bem, mal, dever-ser e normatividade;
- risco elevado de parecer moralização externa se mal fechado;
- subpassos em P42 e P47. fileciteturn3file2

### 8.4. Quarto passo isolado: P50

Razão:

- depende dos corredores anteriores para ficar filosoficamente firme;
- precisa de fecho da derivação da dignidade. fileciteturn3file9

### 8.5. Só depois regressar aos restantes passos abertos

Em particular os mais abertos por score, como P26, P25, P01, P35, P06, P07, P04, P16, P19 e P41. fileciteturn3file0

---

## 9. Ficheiros que devem estar na fonte do projeto

Se fores agora interromper o trabalho e quiseres retomá-lo depois sem perder o fio, estes são os ficheiros que deves garantir que ficam na fonte do projeto.

### 9.1. Núcleo obrigatório

Estes devem estar obrigatoriamente presentes:

- `todos_os_conceitos.json`
- `operacoes.json`
- `meta_referencia_do_percurso.json`
- `meta_indice.json`
- `indice_sequencial.json`
- `indice_por_percurso.json`
- `indice_argumentos.json`
- `argumentos_unificados.json`
- `fragmentos_resegmentados.json`
- `cadencia_schema.json`
- `cadencia_extraida.json`
- `tratamento_filosofico_fragmentos.json`
- `02_mapa_dedutivo_arquitetura_fragmentos.json`
- `impacto_fragmentos_no_mapa.json`
- `impacto_fragmentos_no_mapa_relatorio_validacao.json`
- `revisao_estrutural_do_mapa.json`
- `fecho_manual_corredor_P25_P30.json`
- `fecho_manual_corredor_P33_P37.json`
- `fecho_manual_corredor_P42_P48.json`
- `fecho_manual_corredor_P50.json`
- `mapa_dedutivo_reconstrucao_inevitavel_v3.json`
- `relatorio_reconstrucao_inevitavel_v3.json`
- `fechador_canonico_mapa_v4.py`
- `matriz_inevitabilidades_v4.json`
- `mapa_dedutivo_precanonico_v4.json`
- `relatorio_fecho_canonico_v4.json`
- `dossier_corredor_P25_P30.json`
- `dossier_corredor_P33_P37.json`
- `dossier_corredor_P42_P48.json`
- `dossier_corredor_P50.json`

### 9.2. Ficheiros a criar a seguir

Para a próxima fase, deves criar e depois manter:

- `orquestrador_fecho_canonico_api.py`
- `consolidador_fecho_canonico.py`
- `decisoes_canonicas_intermedias.json`
- `mapa_dedutivo_canonico_final.json`
- `relatorio_final_de_inevitabilidades.json`

### 9.3. Biblioteca de prompts a criar

Na fonte do projeto, convém criar uma pasta:

- `prompts/`

com estes templates:

- `prompt_formulacao_canonica.txt`
- `prompt_fecho_mediacional.txt`
- `prompt_fecho_justificativo.txt`
- `prompt_objecao_letal.txt`
- `prompt_teste_supressao.txt`
- `prompt_arbitragem_corredor.txt`

### 9.4. Pastas de outputs intermédios recomendadas

- `prompts_enviados/`
- `respostas_modelo/`
- `logs_api/`
- `decisoes_canonicas/`

---

## 10. Estrutura de pastas sugerida

```text
15_fecho_canonico/
    README_fase_fecho_canonico_e_pipeline.md
    orquestrador_fecho_canonico_api.py
    consolidador_fecho_canonico.py
    fechador_canonico_mapa_v4.py
    prompts/
        prompt_formulacao_canonica.txt
        prompt_fecho_mediacional.txt
        prompt_fecho_justificativo.txt
        prompt_objecao_letal.txt
        prompt_teste_supressao.txt
        prompt_arbitragem_corredor.txt
    dados/
        matriz_inevitabilidades_v4.json
        mapa_dedutivo_precanonico_v4.json
        relatorio_fecho_canonico_v4.json
        dossier_corredor_P25_P30.json
        dossier_corredor_P33_P37.json
        dossier_corredor_P42_P48.json
        dossier_corredor_P50.json
    prompts_enviados/
    respostas_modelo/
    logs_api/
    outputs/
        decisoes_canonicas_intermedias.json
        mapa_dedutivo_canonico_final.json
        relatorio_final_de_inevitabilidades.json
```

---

## 11. Resumo executivo

O projeto está neste momento na fase de **fecho canónico do mapa dedutivo**.

Já não falta análise de corpus. Já não falta reconstrução geral do mapa.

O que falta é:

- fechar formulações canónicas;
- explicitar mediações em falta;
- introduzir subpassos onde o salto ainda existe;
- consolidar as decisões num mapa final.

A arquitetura técnica recomendada para a fase seguinte é:

- **script 1**: `orquestrador_fecho_canonico_api.py`
- **script 2**: `consolidador_fecho_canonico.py`
- **biblioteca de prompts** em `prompts/`

A ordem recomendada de trabalho é:

1. `P33_P37`
2. `P25_P30`
3. `P42_P48`
4. `P50`
5. restantes passos abertos

O objetivo final já não é mais reconstrução, mas sim **transformar o mapa pré-canónico num mapa dedutivo canónico final, com todas as inevitabilidades relevantes explicitadas**.