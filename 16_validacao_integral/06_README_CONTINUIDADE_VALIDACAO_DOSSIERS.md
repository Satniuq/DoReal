# README de Continuidade — Validação integral dos dossiers de confronto filosófico

## 1. Finalidade deste README

Este ficheiro serve para permitir que outro ambiente, outro chat ou outro operador retome **sem perda de contexto** a fase atual do projeto de validação integral dos dossiers de confronto filosófico.

Não é apenas um resumo do que foi feito. É um documento de continuidade operacional e metodológica. Deve permitir:

- perceber **o que mudou no método**;
- perceber **porque mudou**;
- saber **que dossiers já foram reavaliados** e com que resultado;
- saber **como deve ser abordado o próximo dossier**;
- e evitar regressos ao modelo anterior, em que o dossier era tratado como estrutura a preservar e os fragmentos como simples material ilustrativo.

O princípio de fundo agora em vigor é este:

> **os fragmentos validam a estrutura, não a estrutura os fragmentos.**

Este princípio é a síntese da viragem metodológica explicitada no README desta fase: a validação passou a medir fidelidade descritiva ao padrão real dos fragmentos, e não elegância abstrata da formulação anterior. fileciteturn15file18 fileciteturn15file6

---

## 2. O que mudou nesta fase do projeto

### 2.1. Modelo anterior

O modelo anterior tendia a partir do dossier já existente como se ele fosse, à partida, a melhor formulação do confronto. A reabertura fragmentária servia sobretudo para melhorar, completar ou afinar esse dossier.

### 2.2. Descoberta desta fase

A reabertura fragmentária mostrou que esse procedimento era insuficiente. Em vários casos, o dossier antigo não estava apenas incompleto ou pouco nítido: estava **mal centrado**. Noutros termos, descrevia o confronto num vocabulário mais alto, mais abstrato ou mais herdado da tradição do que o material realmente sustentava.

Foi por isso que esta fase deixou de ser apenas uma correção técnica de dossiers e passou a ser uma **aferição filosófica do próprio método**. O README metodológico já fixou expressamente esta descoberta: os dossiers falham quando substituem o real por construções mais abstratas do que o material permite; e valem quando descrevem fielmente os modos locais, mediados, relacionais e escalonados do real sem os separar do contínuo em que ocorrem. fileciteturn15file1

### 2.3. Nova regra de validação

Um dossier está agora mal posto quando:

- comprime o problema em categorias abstratas não dominantes no material;
- substitui padrões descritivos reais por fórmulas elegantes mas infiéis;
- impõe um centro teórico antes de identificar o centro fragmentário;
- mistura níveis ou regimes sem justificação;
- ou usa vocabulário herdado como se isso bastasse para identificar o problema real.

Um dossier está bem posto quando:

- a pergunta emerge naturalmente dos fragmentos;
- o vocabulário e as distinções nucleares são reconhecíveis no material forte;
- o centro do confronto coincide com o padrão dominante da base;
- e a formulação descreve fielmente o nó real sem achatamento prematuro.

O próprio README metodológico desta fase formula isto em termos ainda mais densos: um dossier só está validado quando a sua formulação preserva o padrão descritivo real dos fragmentos — incluindo manifestação local, mediação, relação, escala, persistência e formas de erro — sem o achatar numa explicação prematura, numa abstração genérica ou numa projeção não sustentada. fileciteturn15file7

---

## 3. Critérios filosóficos de fundo agora estabilizados

A fase atual consolidou vários critérios de fundo que devem governar todos os próximos dossiers.

### 3.1. Primado descritivo

O primeiro dever do dossier é descrever corretamente o padrão do real presente nos fragmentos. A explicação só pode vir depois. Sempre que a explicação se antecipa à descrição, cresce o risco de a estrutura impor ao material uma grelha inadequada. fileciteturn15file18

### 3.2. Submissão ao real

Nenhuma mediação — linguagem, sistema, representação, coerência interna, critério, instituição ou entidade metafísica — pode funcionar como instância autónoma que substitui o real. Vários núcleos do mapa e vários fragmentos fortes desta fase insistem justamente em que critério, verdade, normatividade e correção só valem quando permanecem submetidos ao real. fileciteturn15file18

### 3.3. Localidade e estabilização sem fechamento

As estabilizações locais são reais, mas não equivalem a fechamentos absolutos. Isto tornou-se especialmente importante nos dossiers que envolvem memória, representação, linguagem, consciência e sistema. Uma forma estabilizada pode adquirir persistência e articulação sem se autonomizar do contínuo do real. fileciteturn15file18

### 3.4. Invalidade de projeções entre escalas

Vários erros filosóficos surgem quando uma determinação válida num plano é projetada para outro e passa a governar o campo inteiro. Esta advertência tornou-se decisiva em dossiers sobre passagem entre níveis, consciência, linguagem, ética, normatividade e instituição. fileciteturn15file18

### 3.5. Persistência do anterior na passagem

As passagens não são criações ex nihilo. Mesmo quando há reconfiguração, há persistência do anterior na passagem. Este critério foi decisivo para desmontar certas abstrações sobre emergência, sujeito, identidade e consciência. fileciteturn15file18

---

## 4. Procedimento operativo que deve ser repetido em cada novo dossier

O procedimento agora estabilizado é o seguinte.

### Passo 1 — Ler o dossier atual

Identificar com rigor:

- pergunta central;
- descrição do confronto;
- tese canónica provisória;
- proposições envolvidas;
- estatuto arquitetónico;
- pontes, ancoragens e campo do real;
- distinções centrais;
- objeções fortes;
- decisão de adjudicação atual;
- sinais internos de fragilidade.

### Passo 2 — Reabrir a base fragmentária associada

Ler a base reaberta (`.json` e `.md`) para verificar:

- se há massa suficiente para validação séria;
- que proposições concentram o peso real;
- que vocabulário e que problemas reaparecem com recorrência;
- se o centro real coincide ou não com o centro declarado do dossier.

### Passo 3 — Fazer leitura conceptual preliminar

Antes do script, deve fazer-se um diagnóstico conceptual duro:

- que tipo de objeto é este confronto;
- qual o risco principal do dossier atual;
- com que casos anteriores este dossier se parece;
- e qual parece ser o modo correto de ataque.

### Passo 4 — Instrumentação técnica

Quando houver dúvida sobre o centro efetivo, deve criar-se um script adaptado, a partir da linha robusta estabilizada em `selecionar_fragmentos_relevantes_dossier_v3_2.py` e nos scripts específicos já produzidos para CF03, CF04, CF05 e CF06. O objetivo não é apenas “achar fragmentos relevantes”. O objetivo é medir:

- o `dossier_declared_profile`;
- o `dominant_profile`;
- o `second_profile`;
- o `mismatch_flag`;
- e a `alignment_classification`.

O README metodológico fixa o procedimento desta fase em oito momentos: ler o dossier, reabrir a base, separar perfis, comparar eixo declarado e eixo dominante, avaliar desalinhamento estrutural, reescrever pergunta e descrição, recolocar proposições e corredores, e só depois passar à redação substantiva. fileciteturn15file18 fileciteturn15file16

### Passo 5 — Redecisão metodológica final

Depois da instrumentação, deve decidir-se explicitamente:

- alinhado;
- parcialmente desalinhado;
- fortemente desalinhado.

E, a partir daí:

- preservar com restrições;
- reformular preservando o núcleo;
- reformular profundamente;
- substituir integralmente;
- ou, se necessário, recolher mais instrumentação.

### Passo 6 — Reescrita do dossier

Só depois da redecisão metodológica final se passa ao novo dossier reformulado.

---

## 5. Estatuto do CF08 como caso-modelo

O CF08 é o caso-modelo desta fase. O README metodológico fixa isso explicitamente. fileciteturn15file13

### 5.1. O que o CF08 mostrou

O dossier antigo do CF08 estava centrado em:

- emergência;
- passagem entre níveis;
- novidade qualitativa;
- critério de emergência legítima.

Mas a reabertura fragmentária mostrou que o material forte caía sobretudo em:

- consciência no real;
- mediação;
- representação;
- símbolo;
- erro categorial;
- crítica do dualismo/panpsiquismo.

### 5.2. Lição do CF08

O CF08 mostrou que:

- um dossier pode estar filosoficamente bem intencionado e ainda assim descrever mal o problema;
- a reabertura fragmentária pode revelar um centro completamente diferente do declarado;
- a correção não consiste em responder melhor ao dossier antigo, mas em substituí-lo;
- e o ganho é tanto metodológico como filosófico. fileciteturn15file13

A partir daqui, cada novo dossier passou a ser lido com a seguinte pergunta adicional: **há aqui substituição do real por uma grelha demasiado abstrata, técnica ou impositiva para o que os fragmentos mostram?** fileciteturn15file6

---

## 6. O que foi feito até agora nesta vaga de reformulação

Até ao momento desta continuidade, ficaram metodologicamente estabilizados ou reformulados os seguintes dossiers:

- CF08 — caso-modelo consolidado;
- CF07 — reformulado;
- CF03 — reformulado;
- CF04 — reformulado;
- CF05 — reformulado;
- CF06 — reformulado.

A árvore do projeto mostra que existem bases fragmentárias para CF01–CF18 e uma zona própria de dossiers reformulados, sendo esta a fase em que esses novos ficheiros devem passar a ser colocados e consolidados. fileciteturn15file5

---

## 7. Resultados por dossier já trabalhado

## 7.1. CF07 — caso de reformulação preservando núcleo

### Dossier declarado

O CF07 declarava-se sobretudo no eixo:

- adequação;
- critério;
- verdade;
- correção.

### O que a instrumentação mostrou

A instrumentação revelou que o perfil dominante dos fragmentos estava antes em:

- apreensão;
- representação;
- consciência;
- localidade;

com mediação, símbolo, linguagem e fechamento em segundo plano.

### Decisão

O CF07 não foi tratado como tema errado, mas como dossier que **epistemologizava cedo demais**. O resultado foi: **reformular preservando o núcleo**. Este caso tornou-se importante porque mostrou um padrão recorrente: muitos dossiers falham não por escolherem um tema inexistente, mas por começarem por uma camada derivada em vez de começarem pelo seu solo gerador.

---

## 7.2. CF03 — caso de recentramento profundo

### Dossier declarado

O CF03 declarava-se no eixo:

- vida;
- organismo;
- corpo;
- animalidade.

### O que a instrumentação mostrou

A instrumentação revelou que o perfil dominante real caía antes em:

- ser reflexivo;
- mediação;
- representação;
- passagem sem dualismo;

com apreensão, deteção, localidade e relação ao real em segundo lugar.

### Decisão

O resultado foi uma **reformulação estrutural profunda equivalente a novo dossier**. O caso mostrou que mesmo um dossier aparentemente muito “ontológico de base” pode estar a falhar o seu verdadeiro centro se não captar corretamente a passagem efetiva que os fragmentos descrevem.

---

## 7.3. CF04 — forte desalinhamento com recentramento para humano situado

### Dossier declarado

O CF04 declarava-se sobretudo em:

- consciência;
- autoconsciência;
- presença de si;
- reflexividade;
- sujeito.

### O que a instrumentação mostrou

O relatório do CF04 fechou em:

- `dominant_profile = humano_situado_localidade_apreensao`
- `second_profile = adequacao_verdade_erro_correcao_reinscricao_no_real`
- `dossier_declared_profile = consciencia_reflexiva_sujeito_presenca_de_si`
- `alignment_classification = strongly_misaligned` fileciteturn15file3 fileciteturn15file10

### O que se descobriu

O CF04 não estava realmente centrado no sujeito em sentido clássico. O material forte caía primeiro em:

- humano situado;
- localidade;
- apreensão;
- memória;
- representação;
- mediação;
- adequação ao real.

A consciência e a reflexividade apareciam como camada ulterior, não como ponto de partida.

### Decisão

Foi necessária **substituição integral do dossier anterior por reformulação estrutural profunda**. O novo centro passou a ser a constituição situada e mediada da reflexividade sob submissão ao real.

---

## 7.4. CF05 — forte desalinhamento e recentramento da memória

### Dossier declarado

O CF05 declarava-se sobretudo no eixo:

- tempo;
- memória;
- identidade;
- reflexividade.

### O que a instrumentação mostrou

O relatório do CF05 fechou em:

- `dominant_profile = humano_situado_localidade_apreensao`
- `second_profile = representacao_mediacao_simbolo_linguagem`
- `dossier_declared_profile = memoria_temporalidade_estabilizacao_interna`
- `alignment_classification = strongly_misaligned` fileciteturn15file2 fileciteturn15file8

### O que se descobriu

O CF05 não estava realmente centrado em identidade ou reflexividade temporal do sujeito. O material forte caía antes em:

- ente situado no real;
- humano reinscrito no real;
- apreensão localizada;
- memória como estabilização temporal interna da relação ao real;
- e forte puxão para representação e mediação.

A instrumentação mostrou ainda forte sobreposição com o solo do CF04, o que obrigou a perguntar se o CF05 ainda tinha centro próprio.

### Decisão

A decisão final foi manter o CF05, mas **apenas** sob reformulação estrutural profunda e substituição integral do dossier anterior. O seu centro autónomo deixou de ser “tempo, identidade e reflexividade” e passou a ser:

> **memória como estabilização temporal interna da relação ao real em ente localizado, anterior à representação plena e à reflexividade forte.**

---

## 7.5. CF06 — desalinhamento parcial com nó próprio preservável

### Dossier declarado

O CF06 declarava-se em torno de:

- linguagem;
- símbolo;
- sentido;
- mediação.

### O que a instrumentação mostrou

O relatório do CF06 fechou em:

- `dominant_profile = mediacao_transformacao_apreensao_representacao`
- `second_profile = consciencia_reflexiva_localizada`
- `dossier_declared_profile = linguisticismo_construtivismo_sentido`
- `alignment_classification = partially_misaligned` fileciteturn15file4 fileciteturn15file9

### O que se descobriu

O CF06 não caiu como caso de substituição total do tema. Linguagem, símbolo e mediação estão realmente na base. Mas o dossier atual sobre-semanticizava o confronto, formulando-o cedo demais em léxico de “linguagem e sentido”, quando o material forte caía antes em:

- mediação como transformação da apreensão em representação;
- consciência reflexiva localizada;
- representação, adequação, verdade e correção;
- com forte aproximação ao corredor P27–P34. fileciteturn15file4 fileciteturn15file12

### Decisão

O CF06 foi mantido como dossier autónomo, mas sob **reformulação estrutural profunda e substituição integral do dossier anterior**. O seu novo centro passou a ser:

> **estatuto funcional do símbolo e da linguagem como momentos de mediação e estabilização representacional sob submissão ao real.**

---

## 8. Padrões gerais descobertos nesta vaga

Esta vaga de reavaliação permitiu identificar padrões recorrentes que devem ser vigiados em todos os próximos dossiers.

### 8.1. Vários dossiers vinham “altos demais”

CF04, CF05 e CF06 mostraram que o dossier pode abrir demasiado cedo em:

- sujeito;
- identidade;
- reflexividade;
- linguagem;
- sentido;
- verdade;
- correção.

Mas o material forte costuma cair primeiro em:

- humano situado;
- localidade;
- apreensão;
- memória como estabilização interna;
- representação;
- mediação;
- adequação e reinscrição no real.

### 8.2. Há um corredor de fundo muito importante

A sequência **P25–P30** ficou decisiva para perceber várias reavaliações:

- memória;
- representação;
- símbolo;
- linguagem;
- mediação;
- consciência reflexiva.

E o prolongamento **P33–P37** também se revelou crucial:

- critério;
- verdade;
- distinção verdade/erro;
- erro como desadequação;
- correção como reinscrição no real.

Vários dossiers antigos estavam a recortar mal subzonas deste corredor, como se fossem centros autónomos já prontos.

### 8.3. O risco principal já não é só “tema errado”

Em muitos casos, o risco mais forte não é o dossier dizer algo completamente falso. É dizer algo **prematuro**. O erro é de hierarquia descritiva.

### 8.4. A reescrita tem de baixar o centro

Em quase todos os casos desta vaga, a solução não foi “responder melhor” ao tema antigo, mas **descer o centro do dossier** para o nível em que o material realmente começa a organizar-se.

---

## 9. Estado atual dos dossiers reavaliados

Estado de trabalho até agora:

- **CF08** — consolidado como caso-modelo e reformulado;
- **CF07** — reformulado preservando núcleo;
- **CF03** — reformulado profundamente;
- **CF04** — reformulado profundamente com novo centro em humano situado/apreensão/reflexividade situada;
- **CF05** — reformulado profundamente com novo centro em memória como estabilização temporal interna;
- **CF06** — reformulado profundamente com novo centro em símbolo/linguagem como momentos funcionais de mediação.

O **CF18** foi identificado como dossier sobretudo metodológico e transversal, e foi propositadamente adiado para o fim do ciclo, por não ser o melhor caso para manter continuidade local de análise nesta fase.

---

## 10. O que deve fazer o próximo ambiente ao pegar no dossier seguinte

Quando fores começar o próximo dossier, **não abras logo o script** e **não tentes logo reescrever**. A sequência correta é esta.

### 10.1. Primeiro: análise conceptual dirigida

Ler:

- `CFXX_dossier_confronto.md`
- `CFXX_base_fragmentaria.json`
- `CFXX_base_fragmentaria.md`

E usar, como contexto comparativo:

- `05_README_Reajuste_dossiers_por_reabertura_fragmentaria_SUBSTITUICAO.md`
- `CF08_dossier_confronto_FINAL_CONSOLIDADO.md`
- `CF07_dossier_confronto_REFORMULADO.md`
- `CF03_dossier_confronto_REFORMULADO.md`
- `CF04_dossier_confronto_REFORMULADO.md`
- `CF05_dossier_confronto_REFORMULADO.md`
- `CF06_dossier_confronto_REFORMULADO.md`

Objetivo desta fase:

- perceber que tipo de objeto é o confronto;
- identificar o risco principal do dossier atual;
- testar analogias com CF08, CF07, CF03, CF04, CF05 e CF06;
- decidir se o próximo passo deve ser instrumentação, redecisão ou reescrita.

### 10.2. Segundo: decidir se é preciso instrumentação

Regra prática:

- se o desalinhamento já for evidente e grosseiro, pode haver base para redecisão quase imediata;
- mas se houver dúvida entre vários centros possíveis, deve criar-se script adaptado.

### 10.3. Terceiro: construir script adaptado ao risco do dossier

Nunca usar cegamente um script anterior. Deve aproveitar-se a linha robusta dos scripts anteriores, mas adaptar:

- perfis concorrentes;
- hints;
- termos do dossier;
- perfis de sobreposição;
- e o risco metodológico específico do confronto em causa.

### 10.4. Quarto: interpretar o output com dureza metodológica

Não basta ver o `dominant_profile`. É preciso ler também:

- o `dossier_declared_profile`;
- o `second_profile`;
- o gap entre perfis;
- a quota do perfil dominante;
- os sinais de sobreposição arquitetónica;
- e os fragmentos de topo do sample global.

### 10.5. Quinto: fazer redecisão metodológica explícita

A redecisão final deve responder sempre a estas perguntas:

- o dossier está alinhado, parcialmente desalinhado ou fortemente desalinhado?
- faz sentido mantê-lo?
- em que termos?
- qual o seu centro novo?
- o que deve ser abandonado?
- o que deve ser preservado?
- qual é o seu estatuto arquitetónico revisto?

### 10.6. Sexto: só depois escrever o dossier reformulado

O novo dossier deve ser escrito já na nova chave, e não como remendo do antigo.

---

## 11. Erros que o próximo ambiente não deve cometer

1. **Não tomar o título do dossier como centro real do confronto.**
2. **Não confundir presença de um tema com dominância estrutural desse tema.**
3. **Não usar “sentido”, “sujeito”, “identidade”, “consciência”, “verdade” ou “linguagem” como palavras-guarda-chuva sem medir o solo real do material.**
4. **Não reescrever antes de fazer redecisão metodológica.**
5. **Não assumir que um dossier se salva porque o seu tema “em abstrato” é plausível.**
6. **Não esquecer os riscos de sobreposição com corredores já estabilizados.**
7. **Não deixar que mediação, linguagem, critério ou sistema passem a critério autónomo do real.**

---

## 12. Heurística prática para reconhecer o tipo de caso

### Caso tipo CF08

Quando o eixo declarado do dossier está num universo categorial que o material forte não confirma minimamente.

**Tratamento provável:** substituição integral.

### Caso tipo CF07

Quando o dossier toca material real, mas abre cedo demais por uma camada derivada, formal ou abstrata.

**Tratamento provável:** reformular preservando o núcleo ou reformulação profunda.

### Caso tipo CF03

Quando o dossier parece ontologicamente de base, mas o material revela outra passagem ou outro operador efetivo.

**Tratamento provável:** reformulação estrutural profunda.

### Caso tipo CF04/CF05

Quando sujeito, identidade, memória ou reflexividade aparecem no dossier como centro, mas o material cai primeiro em humano situado, localidade, apreensão e relação ao real.

**Tratamento provável:** recentrar para baixo e distinguir cuidadosamente camadas.

### Caso tipo CF06

Quando linguagem, símbolo, sentido ou sistema aparecem como centro, mas o material cai antes em mediação, representação e submissão ao real.

**Tratamento provável:** recortar funcionalmente o momento simbólico-linguístico e evitar a abstração de “sentido” como cabeça do confronto.

---

## 13. Ficheiros de referência recomendados para a continuação

### Metodologia

- `05_README_Reajuste_dossiers_por_reabertura_fragmentaria_SUBSTITUICAO.md` — documento metodológico-base desta fase. fileciteturn15file0

### Casos já reformulados

- `CF08_dossier_confronto_FINAL_CONSOLIDADO.md`
- `CF07_dossier_confronto_REFORMULADO.md`
- `CF03_dossier_confronto_REFORMULADO.md`
- `CF04_dossier_confronto_REFORMULADO.md`
- `CF05_dossier_confronto_REFORMULADO.md`
- `CF06_dossier_confronto_REFORMULADO.md`

### Scripts de referência

- `selecionar_fragmentos_relevantes_dossier_v3_2.py`
- `selecionar_fragmentos_relevantes_dossier_CF03_v1.py`
- `selecionar_fragmentos_relevantes_dossier_CF04_v1.py`
- `selecionar_fragmentos_relevantes_dossier_CF05_v1.py`
- `selecionar_fragmentos_relevantes_dossier_CF06_v1.py`

### Estruturas de apoio

- `proposicoes_nucleares_enriquecidas_v1.json`
- `matriz_confronto_filosofico_v1.json`
- `impacto_fragmentos_no_mapa.json`
- `mapa_dedutivo_canonico_final__vfinal_corrente.json`
- `02_mapa_dedutivo_arquitetura_fragmentos.json`

---

## 14. Fórmula final de continuidade

Se outro ambiente tiver de continuar este trabalho, deve partir desta fórmula e não recuar dela:

> **um dossier não vale porque o seu tema parece filosoficamente elevado; vale apenas quando a sua formulação coincide com o padrão dominante real dos fragmentos.**

E, por isso:

> **a cada novo confronto, a tarefa não é defender o dossier existente, mas testar se ele permanece submetido ao real que os fragmentos estão a tentar pensar.**

É esta a regra que deve orientar o próximo dossier.
