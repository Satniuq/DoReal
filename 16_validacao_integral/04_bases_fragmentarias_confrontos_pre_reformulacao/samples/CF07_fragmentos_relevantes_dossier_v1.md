# CF07 — fragmentos relevantes para o dossier (CF07 v1)

- Gerado em: 2026-03-25T15:49:02+00:00
- Fonte base fragmentária: `C:\Users\JoseVitorinoQuintas\DoReal\16_validacao_integral\04_bases_fragmentarias_confrontos\CF07_base_fragmentaria.json`
- Nº fragmentos no sample global: 24

## Diagnóstico de alinhamento

- dominant_profile: apreensao_representacao_consciencia_localidade
- second_profile: mediacao_simbolo_linguagem_fechamento
- dossier_declared_profile: adequacao_criterio_verdade_correcao
- mismatch_flag: True
- alignment_classification: partially_misaligned
- O dossier declara sobretudo o eixo 'adequacao_criterio_verdade_correcao', mas o sample global pende para 'apreensao_representacao_consciencia_localidade'.
- Gap entre perfis no sample global=0.38; quota do perfil dominante=45.83%.
- Há desalinhamento, mas não suficientemente nítido para o classificar como forte.
- Perfil dominante dos fragmentos: apreensao_representacao_consciencia_localidade.
- Segundo perfil dos fragmentos: mediacao_simbolo_linguagem_fechamento.

### Estimativa do perfil declarado do dossier

```json
{
  "profile": "adequacao_criterio_verdade_correcao",
  "method": "weighted_snapshot_estimation",
  "section_scores": {
    "pergunta_central": {
      "adequacao_criterio_verdade_correcao": 25.7375,
      "apreensao_representacao_consciencia_localidade": 2.9,
      "mediacao_simbolo_linguagem_fechamento": 4.35,
      "substituicao_do_real_erro_categorial_erro_de_escala": 18.85
    },
    "descricao_do_confronto": {
      "adequacao_criterio_verdade_correcao": 24.0,
      "apreensao_representacao_consciencia_localidade": 6.9375,
      "mediacao_simbolo_linguagem_fechamento": 1.25,
      "substituicao_do_real_erro_categorial_erro_de_escala": 14.4375
    },
    "tese_canonica_provisoria": {
      "adequacao_criterio_verdade_correcao": 30.0,
      "apreensao_representacao_consciencia_localidade": 5.68,
      "mediacao_simbolo_linguagem_fechamento": 11.2,
      "substituicao_do_real_erro_categorial_erro_de_escala": 24.0
    },
    "articulacao_estrutural": {
      "adequacao_criterio_verdade_correcao": 3.0,
      "apreensao_representacao_consciencia_localidade": 1.5,
      "mediacao_simbolo_linguagem_fechamento": 0.0,
      "substituicao_do_real_erro_categorial_erro_de_escala": 3.0
    }
  },
  "raw_profile_scores": {
    "adequacao_criterio_verdade_correcao": 82.7375,
    "apreensao_representacao_consciencia_localidade": 17.0175,
    "mediacao_simbolo_linguagem_fechamento": 16.8,
    "substituicao_do_real_erro_categorial_erro_de_escala": 60.2875
  },
  "confidence": "high",
  "gap_to_second": 22.45
}
```

## Snapshot do dossier

```json
{
  "pergunta_central": "Como são possíveis verdade, erro, critério, correção e objetividade se o sistema exige real independente?",
  "descricao_do_confronto": "Problema epistemológico central do projeto: adequação e desadequação ao real, erro real, critério submetido ao real e correção de representação e ação.",
  "tese_canonica_provisoria": "Quanto a verdade, erro, critério e correção, a tese canónica provisória é a seguinte: Sem real independente e sem possibilidade de adequação, verdade, erro e correção degradam-se em circulação interna; o sistema exige critério submetido ao real.",
  "articulacao_estrutural": "proposições nucleares: P24, P25, P26, P30, P31, P32; pontes entre níveis: PN01, PN02, PN03; ancoragens científicas: AC01, AC02; campos do real: CR02, CR05"
}
```

## Queries derivadas do dossier

### Frases

- Como são possíveis verdade, erro, critério, correção e objetividade se o sistema exige real independente?
- Problema epistemológico central do projeto: adequação e desadequação ao real, erro real, critério submetido ao real e correção de representação e ação.
- Quanto a verdade, erro, critério e correção, a tese canónica provisória é a seguinte: Sem real independente e sem possibilidade de adequação, verdade, erro e correção degradam-se em circulação interna; o sistema exige critério submetido ao real.
- proposições nucleares: P24, P25, P26, P30, P31, P32; pontes entre níveis: PN01, PN02, PN03; ancoragens científicas: AC01, AC02; campos do real: CR02, CR05

### Termos

real, criterio, erro, correcao, verdade, adequacao, submetido, interna, consciencia, mediacao, independente, representacao, fechamento, objetividade, exige, apreensao, reflexiva, simbolica, simbolo, fecho, sistemico, simbolico, substituicao, autonomo, coerencia, possiveis, epistemologico, central, desadequacao, acao, quanto, tese, canonica, provisoria, seguinte, possibilidade, degradam, circulacao, proposicoes, nucleares, pontes, pn01, pn02, pn03, ancoragens, cientificas, ac01, ac02, cr02, cr05, localidade, local, linguagem, validade, categorial, escala

### Hints

verdade, erro, criterio, critério, correcao, correção, adequação, adequacao, objetividade, representação, representacao, apreensão, apreensao, consciência, consciencia, consciência reflexiva, consciencia reflexiva, localidade, local, mediação, mediacao, mediação simbólica, mediacao simbolica, símbolo, simbolo, linguagem, fechamento, fecho sistémico, fecho sistemico, fechamento simbólico, fechamento simbolico, validade interna, real independente, substituição do real, substituicao do real, erro categorial, erro de escala, sistema autónomo, sistema autonomo, coerência interna, coerencia interna, critério submetido ao real, criterio submetido ao real

## Estatísticas por perfil

### Adequação, critério, verdade e correção

- Candidatos acima do limiar: 24
- Média top10: 31.6257
- Máximo top10: 39.3201
- Sobreposição top10 com global: 4

### Apreensão, representação, consciência e localidade

- Candidatos acima do limiar: 24
- Média top10: 39.8518
- Máximo top10: 44.1196
- Sobreposição top10 com global: 2

### Mediação, símbolo, linguagem e fechamento

- Candidatos acima do limiar: 24
- Média top10: 35.5134
- Máximo top10: 40.3202
- Sobreposição top10 com global: 8

### Substituição do real, erro categorial e erro de escala

- Candidatos acima do limiar: 24
- Média top10: 25.1276
- Máximo top10: 29.8096
- Sobreposição top10 com global: 5

## Sample global

### 1. F0241_A24_SEG_003

- score global: 74.3884
- score base: 72.6784
- best profile: apreensao_representacao_consciencia_localidade (33.6519)
- second profile: adequacao_criterio_verdade_correcao (30.2206)
- profile scores: {'adequacao_criterio_verdade_correcao': 30.2206, 'apreensao_representacao_consciencia_localidade': 33.6519, 'mediacao_simbolo_linguagem_fechamento': 29.271, 'substituicao_do_real_erro_categorial_erro_de_escala': 13.8215}
- matched phrases: []
- matched terms: ['real', 'correcao', 'verdade', 'adequacao', 'interna', 'consciencia', 'apreensao', 'reflexiva', 'simbolica', 'simbolo', 'simbolico', 'coerencia', 'proposicoes', 'localidade', 'local']
- matched hints: ['verdade', 'correcao', 'correção', 'adequação', 'adequacao', 'apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, correcao, verdade, adequacao, interna, consciencia, apreensao, reflexiva', 'hints gerais: verdade, correcao, correção, adequação, adequacao, apreensão, apreensao, consciência', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=0.3', 'função textual=desenvolvimento']

Estou a conduzir, tiro as mãos do volante, vou andar, sei lá, 70, 80 kmh, ou seja, 100, 120, 130, tiro as mãos do volante, o carro continua. E já não estou com a mão no volante a manter a relação na regularidade da direção do carro, digamos assim dizer. Estou a olhar em frente, estou a ver a estrada, estou a olhar para um carro e a estrada começa a fazer uma ligeira curva, ou faz uma ligeira curva, a minha mão, a minha mão, ainda que esteja pousada em cima da porta, junto ao vidro, dá um toque, logo. Faz parte da própria constituição do ponto de vista subjetivo, experiencial que está a ter.
o que existe, as relações que existem nesta multiplicidade de eventos que existem nesta experiência de estar durante cinco segundos sem as mãos no volante mostram que as relações que já lá estavam continuam a estar. Aquilo que se atualizou continua a atualizar-se, a velocidade, a direção, a posição do corpo, a atenção, a orientação, a direção, no fundo, o contínuo tem uma direção. Essa direção que já está construída vai continuar a relacionar-se, quer a consciência entre ou não. Pois ela relaciona-se com este manter da relação, este biologismo, se quisermos assim dizer, este vivismo, este acontecer da vida da sua própria definição, únicas, únicas verdadeiras, como é óbvio.
E também teria que ser assim, porque a consciência é somente a relação que advém de um eu reflexivo, que, como já sabemos, é dependentemente um contínuo atualizado localmente. E a consciência, meta-reflexividade, que quisermos, opera porque há já uma estabilização perfeitamente adequada ao real, no fundo, que poderíamos dizer à estabilização da apreensão do eu no real, e opera somente pela coerência que os símbolos compacta, que os símbolos proporcionam, pela adequação da coerência interna imagética ao real que se está a ver, que se está a ouvir, que se está a cheirar, essa correspondência é que permite o contínuo da relação sem intervenção da consciência.

### 2. F0241_A08_SEG_001

- score global: 72.5311
- score base: 70.8211
- best profile: apreensao_representacao_consciencia_localidade (31.8024)
- second profile: mediacao_simbolo_linguagem_fechamento (28.9106)
- profile scores: {'adequacao_criterio_verdade_correcao': 23.271, 'apreensao_representacao_consciencia_localidade': 31.8024, 'mediacao_simbolo_linguagem_fechamento': 28.9106, 'substituicao_do_real_erro_categorial_erro_de_escala': 25.7215}
- matched phrases: []
- matched terms: ['real', 'criterio', 'adequacao', 'interna', 'mediacao', 'independente', 'apreensao', 'reflexiva', 'sistemico', 'coerencia', 'possiveis', 'quanto', 'possibilidade', 'localidade', 'local']
- matched hints: ['criterio', 'critério', 'adequação', 'adequacao', 'apreensão', 'apreensao', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica', 'fecho sistémico', 'fecho sistemico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'sistema autónomo', 'sistema autonomo', 'coerência interna', 'coerencia interna', 'critério submetido ao real', 'criterio submetido ao real']
- reasons: ['termos do dossier: real, criterio, adequacao, interna, mediacao, independente, apreensao, reflexiva', 'hints gerais: criterio, critério, adequação, adequacao, apreensão, apreensao, consciência reflexiva, consciencia reflexiva', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=0.3', 'função textual=desenvolvimento']

A moralidade, aquilo que, se sendo esse, bem sendo aquilo que melhor se situa no contínuo da localidade, assim é que é, no contínuo da localidade, em que se pode sequer colocar a questão de bem, somente quando do real advém um ser reflexivo. Só aí, porque o ser está a refletir sobre a realidade que o contém em si mesmo. O ser está a viver na mediação da apreensão e da realidade. Está a viver nessa relação. 
Relação de quê? Sempre de entre a apreensão e a realidade, a apreensão que inculta do estado interior, whatever, e a realidade. E quanto melhor for a apreensão depois a descrição do que o ser faz na realidade onde vive, melhor se vai posicionar no meio de todas as relações. Não é preciso recorrer a Deus para saber que num sistema relacional há aquilo que preserva e edifica a realidade, o conjunto de atualizações, e aquilo que destrói.

Mas o homem faz coisas tão más, é tão mauzão. Olha o Hitler. Claro. Hitler e qualquer outro massacre, qualquer outra guerra, que não falta por aí são guerras. Aquela foi com uma dimensão ridícula, mas ao.de extermínio. Mas outros extermínios também existiram, ainda que com dimensões menores. Mas independentemente da catástrofe, dizer como é que é possível... Nós sabemos como é que é possível. O homem faz, o homem tem comportamentos não bons para com outros seres. Até comportamentos ativamente destrutivos, impeditivos de florescer, vai ser mau. Se o sistema onde ele estiver inserido, onde ele viver, o sistema em que ele operar, o sistema em que ele apreender e descrever e agir, for um que justifica as ações que se mantêm independentemente de ser bom ou mau. Como o critério não está no real, o critério está no proprio sistema. Saber e fazer com que o outro, com estatuto ontológico igual a ele, que o contínuo das suas atualizações vai terminar, vai deixar de existir, vai deixar de estar enquadrado no potencial do ser, é justificado pela coerência interna de qualquer sistema, o homem  crê ser tão mau como o que for o por si apreendido como o homem que se é e num sistema de homens assim, ser assim nao ha de estar mal. Quanto menos gravosos forem, mais fácil de manter a coerência do sistema pela estabilizaçao dos utros homens no sistema. Quanto mais, mais intrincada vai ser, porque sempre afastado do real, no sistema da quebra com o real custa a posterior apreensao do real e nao da apreensao é custosa.

Ah, mas o teu critério é tão, é tão como vale tanto como outro qualquer outro critério. Vale, vale tanto? Como é que medes esse tanto? Ah, há de ser pela... Pois, amigo, há de ser pela adequação à realidade, adequação ao real. Mesmo no teu cenário fofo de possibilidade de algo ser somente porque há mais uma opção que, em abstrato, se poderia incluir nesse campo de possibilidades, é somente aprender mal o campo de possibilidades. Não é mais do que outra coisa. É aprender mal e descrever mal o ser, o poder e o dever ser.

### 3. F0214_SEG_001

- score global: 71.463
- score base: 69.753
- best profile: apreensao_representacao_consciencia_localidade (36.2519)
- second profile: adequacao_criterio_verdade_correcao (28.9978)
- profile scores: {'adequacao_criterio_verdade_correcao': 28.9978, 'apreensao_representacao_consciencia_localidade': 36.2519, 'mediacao_simbolo_linguagem_fechamento': 18.4715, 'substituicao_do_real_erro_categorial_erro_de_escala': 10.272}
- matched phrases: []
- matched terms: ['real', 'erro', 'verdade', 'adequacao', 'consciencia', 'objetividade', 'exige', 'apreensao', 'simbolica', 'simbolo', 'simbolico', 'degradam', 'proposicoes', 'localidade', 'local']
- matched hints: ['verdade', 'erro', 'adequação', 'adequacao', 'objetividade', 'apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fechamento simbólico', 'fechamento simbolico', 'real independente', 'substituição do real', 'substituicao do real', 'erro categorial', 'erro de escala']
- reasons: ['termos do dossier: real, erro, verdade, adequacao, consciencia, objetividade, exige, apreensao', 'hints gerais: verdade, erro, adequação, adequacao, objetividade, apreensão, apreensao, consciência', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=0.3', 'função textual=exploracao']

1 mas eu apreendo mal, a minha mãe que vive nas atualizações dos eus que lhe ocupam o local há de, ainda que não analiticamente, apreendo até melhor, não quero justificação teórica para fazer o que for que mantenha os meus filhos vivos, todos os outros filhos morrem se assim o fosse. O grau de adequação é verdadeiro. Não se exige ao homem o que se exige ao filósofo, o ato filosófico é encarnado pelo filósofo no contínuo de ser um filósofo. Ver mais além é para quem quer viver como vive mas mais além, não impede de se viver já como se vive, se I mais é permitido o que já existe não é contrariado, é melhor dizer mentira sobre equações do que sobre o ser como o pai analfabeto que melhor pai se foi no que eu acho que é ser bom pai, o enquadramento do conteúdo do símbolo é meu pela minha localidade e sem QQ esforço mental ou energético posso simplesmente querer não degradar a relação em que estou inserido, pai filho, irmão indivíduo, whatevs. Já nem sei a que estava a objetar. 2 nem percebi mentir é mal descrever propositadamente com intuito de negar, acho que será assim ou algo parecido, diferente de erro, de mal, as relações humanas são multidisciplinares tens de ter mais imaginação 3 não percebi 4 acho que sim é mesmo só falta de conhecimento teu, pensava que tinhas aqui nesta conversa os ficheiros todo do real, consciência ética etc etc, nem vou escrever mais

### 4. F0241_A14_SEG_003

- score global: 68.299
- score base: 66.589
- best profile: mediacao_simbolo_linguagem_fechamento (30.8215)
- second profile: apreensao_representacao_consciencia_localidade (25.0024)
- profile scores: {'adequacao_criterio_verdade_correcao': 13.3715, 'apreensao_representacao_consciencia_localidade': 25.0024, 'mediacao_simbolo_linguagem_fechamento': 30.8215, 'substituicao_do_real_erro_categorial_erro_de_escala': 17.072}
- matched phrases: []
- matched terms: ['real', 'verdade', 'interna', 'apreensao', 'simbolica', 'simbolo', 'sistemico', 'simbolico', 'possiveis', 'quanto', 'possibilidade', 'circulacao', 'localidade', 'local']
- matched hints: ['verdade', 'apreensão', 'apreensao', 'localidade', 'local', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fecho sistémico', 'fecho sistemico', 'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'sistema autónomo', 'sistema autonomo', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, verdade, interna, apreensao, simbolica, simbolo, sistemico, simbolico', 'hints gerais: verdade, apreensão, apreensao, localidade, local, mediação simbólica, mediacao simbolica, símbolo', 'perfil dominante no fragmento: mediacao_simbolo_linguagem_fechamento', 'funcao_textual=0.3', 'função textual=exploracao']

Daí a universalidade da religião, a necessidade de enquadramento da apreensão do real, do eu, do real no eu, essas coisas todas, a necessidade de enquadramento disso, no fundo da vida, daquilo que se está a viver, no círculo que o sequer possibilita, de modo a não exigir que se pense a vida de modo filosófico, verdadeiramente filosófico, porque isso seria não haver vida e impossível, porque altamente disfuncional, porque depois uma pessoa acaba por olhar para a relação do ser em cada interação e isso torna-se awkward. Mas obviamente que a resposta vai ser enquadrar no sistema o símbolo maior, pronto, o que quiser se chamar, o criador, o que se quiser chamar.

Depois, como é óbvio, esse símbolo vai ter o melhor ou pior descrição, claro, quanto mais ou menos afastada for do real. E quão mais afastada se torna do real, menos verdadeira se torna, e por isso vê-se que o porquê da morte de Deus. Não é porque se descobriu, não é porque a ciência levou a descrições mais verdadeiras, a um reenquadramento. Não, é por isso e porque o símbolo de Deus, que se foi fazendo de Deus, passou a estar em mais choque com as novas apreensões.

Claro que Deus morreu. Porque se foi descobrindo cada regularidade e isso foi entrando em choque com o símbolo anterior. E ao invés de procurar o melhor símbolo, procura-se a outra resposta também mais fácil de fazer, neste caso, que é dissolver. Dissolver o real e o eu, pela sua localidade e ponto de vista e perspectiva, passa a reenquadrar toda a apreensão.

### 5. F0104_A01_SEG_002

- score global: 65.9242
- score base: 64.2142
- best profile: apreensao_representacao_consciencia_localidade (33.6519)
- second profile: mediacao_simbolo_linguagem_fechamento (30.8215)
- profile scores: {'adequacao_criterio_verdade_correcao': 19.871, 'apreensao_representacao_consciencia_localidade': 33.6519, 'mediacao_simbolo_linguagem_fechamento': 30.8215, 'substituicao_do_real_erro_categorial_erro_de_escala': 17.072}
- matched phrases: []
- matched terms: ['real', 'verdade', 'adequacao', 'interna', 'consciencia', 'apreensao', 'reflexiva', 'simbolica', 'simbolo', 'sistemico', 'simbolico', 'localidade', 'local']
- matched hints: ['verdade', 'adequação', 'adequacao', 'apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fecho sistémico', 'fecho sistemico', 'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'sistema autónomo', 'sistema autonomo', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, verdade, adequacao, interna, consciencia, apreensao, reflexiva, simbolica', 'hints gerais: verdade, adequação, adequacao, apreensão, apreensao, consciência, consciencia, consciência reflexiva', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=0.3', 'função textual=desenvolvimento']

Se o modo de ser vive — não é, mas vive — e se o modo de ser consciente reflexivo vive pela apreensão como localidade, e se o modo de apreensão é simbólico, então estas ideias de que não precisamos de preencher as realidades com símbolos adequados não fazem sentido. O ser reflexivo tem sempre esta característica.

E tentar retirar essa dimensão ao ser reflexivo, descrevê-lo num sistema interno, para retirar o herói da equação, os arquétipos — todos os arquétipos que são descritivos são verdadeiros porque descrevem o real. Se não descrevem o real, então são sempre valorativos.

### 6. F0241_A04_SEG_001

- score global: 65.9242
- score base: 64.2142
- best profile: apreensao_representacao_consciencia_localidade (33.6519)
- second profile: adequacao_criterio_verdade_correcao (23.721)
- profile scores: {'adequacao_criterio_verdade_correcao': 23.721, 'apreensao_representacao_consciencia_localidade': 33.6519, 'mediacao_simbolo_linguagem_fechamento': 13.672, 'substituicao_do_real_erro_categorial_erro_de_escala': 22.172}
- matched phrases: []
- matched terms: ['real', 'criterio', 'verdade', 'interna', 'representacao', 'apreensao', 'reflexiva', 'sistemico', 'possiveis', 'possibilidade', 'proposicoes', 'localidade', 'local']
- matched hints: ['verdade', 'criterio', 'critério', 'representação', 'representacao', 'apreensão', 'apreensao', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'fecho sistémico', 'fecho sistemico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'sistema autónomo', 'sistema autonomo', 'coerência interna', 'coerencia interna', 'critério submetido ao real', 'criterio submetido ao real']
- reasons: ['termos do dossier: real, criterio, verdade, interna, representacao, apreensao, reflexiva, sistemico', 'hints gerais: verdade, criterio, critério, representação, representacao, apreensão, apreensao, consciência reflexiva', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=0.3', 'função textual=exploracao']

2 + 2 igual a 4 funciona como sua própria justificação, mas ainda se pode ir a elementos mais básicos, mais profundos, aos elementos axiomáticos de um sistema, e depois diz-se que ah, não, não há, porque a derivação é infinita. Claro, claro. Claro que sim, como é óbvio. Porque a domização de 2 + 2 ser 4 não é aquilo que compõe o 2 e o 2 e o 4 que faz com que seja verdade, mas é o facto de o 2 e o 2 serem 4, essa relação que existe, continuar a permanecer no contínuo da existência dentro do sistema que diz que 2 + 2 é 4, existe, é real, representa a realidade.

porque pende para encontrar as... pende não, faz parte, não é? Encontra-se as justificações, os axiomas, os fundamentos de uma qualquer proposição apenas em dois lados. São os únicos lados possíveis assim que algo existe, ou seja, assim que há. E esses dois lados são ou naquilo que há, na realidade, naquilo que é, ou então pela localidade de todos os seres reflexivos, é pela perspectiva em que está inserido e é por essa imposição de derivação do eu para o real que a comparação entre qualquer tipo de critério ou a justaposição entre qualquer tipo de critério dentro do quadro da apreensão do real pelo eu é no eu que reside a base, é no eu que reside o quadro lógico. Portanto, é normal, seja em um eu, é normal. Não assim assim tinha sido descoberta assim que o homem começou a pensar, não foi assim. É uma luta constante na apreensão, na boa apreensão do real, que obriga, como é óbvio, também à descrição do real. A apreensão por si só é pouca se não houver descrição energética, descrição ou representação, não houver representação, a representação não pode ser algo muito interno e descrição contém um interno e um externo, na relação entre o que existe.

### 7. F0202_SEG_001

- score global: 64.6599
- score base: 62.9499
- best profile: apreensao_representacao_consciencia_localidade (27.0126)
- second profile: mediacao_simbolo_linguagem_fechamento (25.5531)
- profile scores: {'adequacao_criterio_verdade_correcao': 16.5135, 'apreensao_representacao_consciencia_localidade': 27.0126, 'mediacao_simbolo_linguagem_fechamento': 25.5531, 'substituicao_do_real_erro_categorial_erro_de_escala': 22.364}
- matched phrases: []
- matched terms: ['real', 'criterio', 'interna', 'consciencia', 'mediacao', 'apreensao', 'reflexiva', 'sistemico', 'possiveis', 'possibilidade', 'circulacao', 'proposicoes']
- matched hints: ['criterio', 'critério', 'apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica', 'fecho sistémico', 'fecho sistemico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'sistema autónomo', 'sistema autonomo', 'coerência interna', 'coerencia interna', 'critério submetido ao real', 'criterio submetido ao real']
- reasons: ['termos do dossier: real, criterio, interna, consciencia, mediacao, apreensao, reflexiva, sistemico', 'hints gerais: criterio, critério, apreensão, apreensao, consciência, consciencia, consciência reflexiva, consciencia reflexiva', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=1.1', 'função textual=critica']

as sociedades democraticas europeias - e tmb nos usa embora o pensamento base seja eu no real, ao contrrio das europeia - afetam os recursos tirados a seres conscientes reflexivos, com grande amplitude de justificaçoes internas para o fazer, ainda que se gaste mais do que se arrecada, ainda que a mao do estado chegue a todos os cantos de um sitio ondem vivem seres conscientes reflexivos e onde atualize , o faça sempre pior do que se fosse qualquer outro sistema que quisesse permancer e que teria sempre um alinhamento com o real, com que quem o constituisse vive o problema , as possibilidades e alogo a melhor solucao, visse portanto o ser, o poder ser e o dever ser. o aumento do de vida - as barreiras levantadas ao ser reflexivo, à sua liberdadena exploração do real por imposiçao do homem e nao por qq outra questao, travestidas de uma qq proposiçao valorativa de finalidade, que há tantas, porque tem de ser assim porque devia ser assim, - hum ta, devia ser assim se for e puder ser assim, mas claro que nao é isto que é custoso nadar contra a maré - e vive se assim com um estado que arrecada dinheiro e que preenche o espaço comum, eleito mediante critérios de onde mais gastar, para voltar a ser eleito, até que se comece a desviar o real e modificar tal sistema, adeuqando-o ao real, ainda que se calhar pior do que sem ele, porque na analise do mal do sitema anterior tmb reside a parca descriçao, e acaba se a nem perceber o antes de ser e o porque da mudança, ha somente o que se apreende e o que cre dever ser, numa expansao dos modos de ser à expressão do pulso da sociedade, no ritma das respostas adquadas para o circulo proximo do ser reflexivo mas erradas nas relaçoes extra eu, em que o outro nao tocavel tem de ser equacionado

### 8. F0241_A03_SEG_001

- score global: 64.6349
- score base: 62.9249
- best profile: mediacao_simbolo_linguagem_fechamento (34.1601)
- second profile: apreensao_representacao_consciencia_localidade (31.0024)
- profile scores: {'adequacao_criterio_verdade_correcao': 18.0215, 'apreensao_representacao_consciencia_localidade': 31.0024, 'mediacao_simbolo_linguagem_fechamento': 34.1601, 'substituicao_do_real_erro_categorial_erro_de_escala': 6.872}
- matched phrases: []
- matched terms: ['real', 'correcao', 'consciencia', 'mediacao', 'independente', 'apreensao', 'reflexiva', 'simbolica', 'simbolo', 'simbolico', 'localidade', 'local', 'linguagem']
- matched hints: ['correcao', 'correção', 'apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'linguagem', 'fechamento simbólico', 'fechamento simbolico', 'real independente', 'substituição do real', 'substituicao do real']
- reasons: ['termos do dossier: real, correcao, consciencia, mediacao, independente, apreensao, reflexiva, simbolica', 'hints gerais: correcao, correção, apreensão, apreensao, consciência, consciencia, consciência reflexiva, consciencia reflexiva', 'perfil dominante no fragmento: mediacao_simbolo_linguagem_fechamento', 'funcao_textual=0.3', 'função textual=desenvolvimento']

Por que é que as pessoas amadurecem? Por que é que se tornam adultas? Porque ultrapassam o processo de apreensão do real. Por que é que a escolaridade incide durante a juventude e não quando se é adulto? Por que é que é mais difícil aprender línguas quando se é adulto? Como é óbvio, porque o modo de apreensão do real está... é o dominante. Pois venha, pois venha a suavização, como é óbvio, pelo seu próprio.de vista no horizonte da apreensão, que é local, sempre, por isso é que é um horizonte. E isto é para dizer o quê? Para dizer que era para dizer... Ah, era isso. E depois, quando se já se tem a apreensão, não é? Quando já se tem o símbolo cristalizado, quando já se tem, sei lá, de qualquer maneira queremos olhar para isto, todas elas são meras descrições, parcas descrições, porque a descrição correta é ontológica. Portanto, quando a repetição de apreensões se tornou num modo de ser do processo do aprender, quando eu olhei muitas vezes para uma bola e agora eu já sei que é uma bola, não pela bola em si, não por eu em mim, mas pela relação que existe, que é expressada pela apreensão, pela mediação que incorpora tudo. Só que a mediação é restritiva, neste caso tudo incorpora tudo.

Essa destruição depois é custosa, é custosa, claro, como é óbvio. Nós já não estamos no modo de cristalização da apreensão, mas já entramos agora na necessária destruição dos modos de ser, para ser outros modos de ser. Então isto leva à banalidade de que é tudo aquilo que se foi há um segundo atrás, como é óbvio, mas leva-nos também à conclusão de que, operando o ser consciente reflexivo num quadro em que ele é livre e pode escolher ou não, o caminho que o leva à melhor descrição do real manifesta-se como, depois, modo de ser que mal descrevem o real. Portanto, até um ponto em que, por exemplo, vivem mais no eu eu.

A destruição é necessária. As atualizações que se sobrepõem nas relações em que o ser é levam sempre a destruições, podem não são destruições físicas, mas são destruições de tipos de relações, destruções de continuidades de relações, se esta relação se permanece neste estado, com estas características, com estas envolvências, e agora vem outra atualização malandra e está a impor-se, como qualquer coisa, como esta parede que não sai da minha frente, está bem? O braço vai-se partir se não for contra a parede. Há a destruição daquela continuidade daquela relação, que no fundo, em que no fundo o homem vive, na continuidade da relação anterior. Mas independentemente disso, a destruição é, quer dizer, faz parte, porque senão tudo seria como seria, cristalizado e imutável. Seria uma contradição nos próprios termos, o que sabemos não ser.

### 9. F0035_SEG_001

- score global: 64.4601
- score base: 62.7501
- best profile: substituicao_do_real_erro_categorial_erro_de_escala (29.271)
- second profile: apreensao_representacao_consciencia_localidade (19.871)
- profile scores: {'adequacao_criterio_verdade_correcao': 19.0983, 'apreensao_representacao_consciencia_localidade': 19.871, 'mediacao_simbolo_linguagem_fechamento': 11.972, 'substituicao_do_real_erro_categorial_erro_de_escala': 29.271}
- matched phrases: []
- matched terms: ['real', 'criterio', 'erro', 'verdade', 'interna', 'consciencia', 'sistemico', 'autonomo', 'acao', 'circulacao', 'proposicoes', 'pontes', 'categorial']
- matched hints: ['verdade', 'erro', 'criterio', 'critério', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'fecho sistémico', 'fecho sistemico', 'validade interna', 'erro categorial', 'erro de escala', 'sistema autónomo', 'sistema autonomo', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, criterio, erro, verdade, interna, consciencia, sistemico, autonomo', 'hints gerais: verdade, erro, criterio, critério, consciência, consciencia, consciência reflexiva, consciencia reflexiva', 'perfil dominante no fragmento: substituicao_do_real_erro_categorial_erro_de_escala', 'funcao_textual=0.3', 'função textual=desenvolvimento']

Há proposições de maior e menor relevância conforme a sua aplicabilidade à base conceptual dos modos de ser concorrentes nesta realidade. Distingue-se entre proposições de circunscrição individual, com efeitos limitados, e proposições de amplitude alargada, cujos efeitos se propagam pelos círculos mais individuais. São dois tipos de proposições ontologicamente distintos. É nestes modos de ser que a vida se opera, onde emerge a complexidade das entidades conscientes e das suas relações. Em círculos maiores, esta contenda agrega-se. Reconhece-se que há verdade na utilidade do modo de ser de esquerda em contextos próximos, como relações familiares, mas esse modo é inadequado — por qualquer critério verdadeiro — para círculos nacionais, transnacionais ou supranacionais, tratando-se de um erro categorial. A ponte entre o ser, o poder-ser e o dever-ser não é a mesma em todos os planos. Apelos sentimentais são inadequados para relações entre Estados. Isto abrange análise, respostas, proposições, propostas de ação e implementação prática: trata-se de modos de exteriorização do ser. Esta verdade decorre da auto-evidência do sistema: sendo seres conscientes e sociais, operamos necessariamente em dois caminhos fundamentais — o da procura ou o do resguardo. Não há mais; as multiplicidades internas derivam desta divisão fundamental.

### 10. F0108_A02_SEG_001

- score global: 62.7776
- score base: 61.0676
- best profile: mediacao_simbolo_linguagem_fechamento (37.771)
- second profile: apreensao_representacao_consciencia_localidade (33.6519)
- profile scores: {'adequacao_criterio_verdade_correcao': 5.972, 'apreensao_representacao_consciencia_localidade': 33.6519, 'mediacao_simbolo_linguagem_fechamento': 37.771, 'substituicao_do_real_erro_categorial_erro_de_escala': 17.072}
- matched phrases: []
- matched terms: ['real', 'interna', 'consciencia', 'apreensao', 'simbolica', 'simbolo', 'sistemico', 'simbolico', 'quanto', 'circulacao', 'localidade', 'local', 'linguagem']
- matched hints: ['apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'linguagem', 'fecho sistémico', 'fecho sistemico', 'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'sistema autónomo', 'sistema autonomo', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, interna, consciencia, apreensao, simbolica, simbolo, sistemico, simbolico', 'hints gerais: apreensão, apreensao, consciência, consciencia, consciência reflexiva, consciencia reflexiva, localidade, local', 'perfil dominante no fragmento: mediacao_simbolo_linguagem_fechamento', 'funcao_textual=0.3', 'função textual=desenvolvimento']

Daí a importância da língua. Se cada consciência é um mundo local, interessa saber quantos mundos existem e como se repartem as estruturas. O discurso é um modo de transferência de localidades, de ampliação de minicírculos dentro do real.

O discurso existe como sistema: milhões de símbolos, cada um com estruturas próprias e relações normalizadas que permitem a apreensão do pensamento do outro. A manutenção dessas relações privilegia os círculos internos em detrimento do contacto com o externo.

### 11. F0044_SEG_001

- score global: 62.5707
- score base: 60.8607
- best profile: mediacao_simbolo_linguagem_fechamento (34.9197)
- second profile: adequacao_criterio_verdade_correcao (27.2706)
- profile scores: {'adequacao_criterio_verdade_correcao': 27.2706, 'apreensao_representacao_consciencia_localidade': 22.471, 'mediacao_simbolo_linguagem_fechamento': 34.9197, 'substituicao_do_real_erro_categorial_erro_de_escala': 10.272}
- matched phrases: []
- matched terms: ['real', 'verdade', 'adequacao', 'representacao', 'objetividade', 'simbolica', 'simbolo', 'simbolico', 'possiveis', 'possibilidade', 'circulacao', 'linguagem']
- matched hints: ['verdade', 'adequação', 'adequacao', 'objetividade', 'representação', 'representacao', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'linguagem', 'fechamento simbólico', 'fechamento simbolico', 'real independente', 'substituição do real', 'substituicao do real']
- reasons: ['termos do dossier: real, verdade, adequacao, representacao, objetividade, simbolica, simbolo, simbolico', 'hints gerais: verdade, adequação, adequacao, objetividade, representação, representacao, mediação simbólica, mediacao simbolica', 'perfil dominante no fragmento: mediacao_simbolo_linguagem_fechamento', 'funcao_textual=0.3', 'função textual=desenvolvimento']

O discurso público não é naturalmente direcionado à realidade, porque a sua própria característica é ser limitado e autorreferencial: fala de si mesmo e dos eventos imediatos, usando as ferramentas que o constituem. Não pode haver enraizamento no real sem que o seu círculo se expanda, o que só seria possível se ideias verdadeiras fossem mais “pegajosas” do que as ideias de esquerda — algo que exigiria sacrifício e, por isso, tende a ser evitado. Alguns filósofos compreenderam a autorreferencialidade, mas fixaram-se nos símbolos da linguagem. A realidade contém objetos, alguns animados, e ver é a melhor forma de navegar; esperar que os animais percecionem o mundo sem representação é incoerente. A complexidade humana deriva da experiência adaptativa: o ser humano é o animal de todos os nichos. Ver melhor o mundo — representar o mundo no cérebro de forma cada vez mais sofisticada — é uma necessidade ontológica imposta pelas condições ambientais de florescimento. O descrever vem depois do ver; historicamente, primeiro surge o objeto. Ainda que respostas emocionais de primeira ordem, adequadas a círculos próximos, tenham valor adaptativo, a sua verdade assenta sempre na realidade, nem que seja pelo seu fundamento biológico.

### 12. F0241_A13_SEG_001

- score global: 62.2237
- score base: 60.5137
- best profile: adequacao_criterio_verdade_correcao (32.3978)
- second profile: apreensao_representacao_consciencia_localidade (30.2206)
- profile scores: {'adequacao_criterio_verdade_correcao': 32.3978, 'apreensao_representacao_consciencia_localidade': 30.2206, 'mediacao_simbolo_linguagem_fechamento': 25.2715, 'substituicao_do_real_erro_categorial_erro_de_escala': 15.372}
- matched phrases: []
- matched terms: ['real', 'erro', 'correcao', 'verdade', 'interna', 'representacao', 'objetividade', 'apreensao', 'reflexiva', 'simbolica', 'simbolo', 'simbolico']
- matched hints: ['verdade', 'erro', 'correcao', 'correção', 'objetividade', 'representação', 'representacao', 'apreensão', 'apreensao', 'consciência reflexiva', 'consciencia reflexiva', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'erro categorial', 'erro de escala', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, erro, correcao, verdade, interna, representacao, objetividade, apreensao', 'hints gerais: verdade, erro, correcao, correção, objetividade, representação, representacao, apreensão', 'perfil dominante no fragmento: adequacao_criterio_verdade_correcao', 'funcao_textual=0.3', 'função textual=exploracao']

O que o filósofo faz é procurar o real, é procurar o homem dentro do real. Não é excluir o real e dizer, ok, e agora é só objetos, agora é só símbolos. Não! Porque esses símbolos estão lá por causa de outra coisa qualquer. E os símbolos podem se desviar tanto até que o real estica a corda.

Se eu mal representar a igualdade ontológica que existe em dois seres reflexivos, posso se calhar correr o erro de pensar que lhe posso mandar com um pau à cabeça. Posso achar isto? Isto existe somente por uma parca descrição do real. Não, os objetos existem, agora não existem, agora não há homem, não há mar, os objetos existem.

Os objetos não têm o mesmo estatuto, porque dependem de... Os objetos são dependentes. do modo de ser do ser reflexivo. É somente isto. E o modo de ser do ser reflexivo pode ser mais ou menos ajustado ao real, ao bem e à verdade.

E do real, e depende do real, não sei ouvir a tua resposta, mas depende da relação, da relação, da apreensão, porque só quem apreende, só o que apreende, ou só apreendendo, é que se pode sequer apreender. E só se refletindo é que se pode refletir. Pá, isto são daquelas coisas básicas, não é? Uma pedra não pode, não pode, não faz, não é, não tem, não sabe, não consegue, não existe sequer, é o real, é o real.

É o real, não tem relação, não tem um mecanismo racional interno de detecção, de apreensão do real, de representação e de instauração de uma coordenação das representações internas no contínuo da relação com o real.

### 13. F0070_SEG_002

- score global: 60.5047
- score base: 58.7947
- best profile: mediacao_simbolo_linguagem_fechamento (40.0197)
- second profile: adequacao_criterio_verdade_correcao (30.7873)
- profile scores: {'adequacao_criterio_verdade_correcao': 30.7873, 'apreensao_representacao_consciencia_localidade': 3.472, 'mediacao_simbolo_linguagem_fechamento': 40.0197, 'substituicao_do_real_erro_categorial_erro_de_escala': 25.7215}
- matched phrases: []
- matched terms: ['real', 'erro', 'verdade', 'objetividade', 'simbolica', 'simbolo', 'sistemico', 'simbolico', 'proposicoes', 'linguagem', 'validade', 'categorial']
- matched hints: ['verdade', 'erro', 'objetividade', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'linguagem', 'fecho sistémico', 'fecho sistemico', 'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'erro categorial', 'erro de escala', 'sistema autónomo', 'sistema autonomo']
- reasons: ['termos do dossier: real, erro, verdade, objetividade, simbolica, simbolo, sistemico, simbolico', 'hints gerais: verdade, erro, objetividade, mediação simbólica, mediacao simbolica, símbolo, simbolo, linguagem', 'perfil dominante no fragmento: mediacao_simbolo_linguagem_fechamento', 'funcao_textual=0.3', 'função textual=desenvolvimento']

A validade de uma proposição não pode ser aferida por um sistema que o homem cria. Esse é um erro categorial. A validade depende exclusivamente do real. Contudo, a questão da validade de uma proposição só se coloca quando a proposição pretende operar no registo do verdadeiro ou do falso. Fora desse objetivo, a pergunta perde sentido.

Os sons que o homem produz dependem de vibrações no ar. Essas vibrações são, em número e variedade, muito superiores às vibrações que efetivamente acertam no real de forma verdadeira. Por mera lógica probabilística, é mais provável errar do que acertar. Se não fosse assim, todos viveriam como santos.

A linguagem, enquanto sistema vibratório e simbólico, tem sempre maior capacidade de produzir variações do que o real tem de as validar. A verdade não nasce da proliferação proposicional, mas da sua coincidência efetiva com o real.

### 14. F0241_A20_SEG_004

- score global: 59.6964
- score base: 57.9864
- best profile: mediacao_simbolo_linguagem_fechamento (25.7215)
- second profile: apreensao_representacao_consciencia_localidade (25.0024)
- profile scores: {'adequacao_criterio_verdade_correcao': 9.372, 'apreensao_representacao_consciencia_localidade': 25.0024, 'mediacao_simbolo_linguagem_fechamento': 25.7215, 'substituicao_do_real_erro_categorial_erro_de_escala': 10.272}
- matched phrases: []
- matched terms: ['real', 'interna', 'apreensao', 'reflexiva', 'simbolica', 'simbolo', 'simbolico', 'possiveis', 'acao', 'possibilidade', 'localidade', 'local']
- matched hints: ['apreensão', 'apreensao', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, interna, apreensao, reflexiva, simbolica, simbolo, simbolico, possiveis', 'hints gerais: apreensão, apreensao, consciência reflexiva, consciencia reflexiva, localidade, local, mediação simbólica, mediacao simbolica', 'perfil dominante no fragmento: mediacao_simbolo_linguagem_fechamento', 'funcao_textual=0.3', 'função textual=desenvolvimento']

as definições no sentido da descrição completa do símbolo que se está a descrever. Se está a descrever sobre liberdade, então, na definição, tem de conter aquilo que é de facto a liberdade, que é somente o reflexo da reflexividade na ação, as possibilidades no campo das potencialidades de um ser reflexivo que existe localmente nesse campo, que interage com o campo na sua extensão, que amplia e que desfaz e que molda e que restringe, dependendo da apreensão relativamente ao real, que incluindo ele próprio, claro. É a descrição de todas as compartimentalizações daquilo de que se está a falar, que envolve, para além de tudo, envolve o homem.

### 15. F0108_A01_SEG_001

- score global: 59.6278
- score base: 57.9178
- best profile: apreensao_representacao_consciencia_localidade (38.8701)
- second profile: mediacao_simbolo_linguagem_fechamento (35.2202)
- profile scores: {'adequacao_criterio_verdade_correcao': 7.672, 'apreensao_representacao_consciencia_localidade': 38.8701, 'mediacao_simbolo_linguagem_fechamento': 35.2202, 'substituicao_do_real_erro_categorial_erro_de_escala': 13.672}
- matched phrases: []
- matched terms: ['real', 'interna', 'consciencia', 'representacao', 'apreensao', 'reflexiva', 'simbolica', 'simbolo', 'simbolico', 'seguinte', 'circulacao']
- matched hints: ['representação', 'representacao', 'apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, interna, consciencia, representacao, apreensao, reflexiva, simbolica, simbolo', 'hints gerais: representação, representacao, apreensão, apreensao, consciência, consciencia, consciência reflexiva, consciencia reflexiva', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=0.3', 'função textual=desenvolvimento']

A apreensão é o modo de significação das diferentes atualizações do ser. O símbolo é o enquadramento do real, o enquadramento daquilo que é. Pela própria estrutura da apreensão surgem interações entre o eu e o real, entre o eu e o eu, entre tudo isso.

Quando um símbolo representa um conceito maior — por exemplo, um 7 poder ser composto por 7 — isso decorre das diferenças dos tipos de apreensão, dos pontos de vista, dos constituintes, dos limites e dos círculos daquilo que está a atualizar. Dependendo do ponto de vista, pode-se ver um estágio que não é final, mas apenas o antecessor do seguinte.

O símbolo embarca o real conforme o ponto de vista, porque tem de incorporar estruturas lógicas necessárias. A lógica é a manutenção da inteligibilidade da relação eu–real. O real incorpora o eu, mas a lógica é a forma de explicitar isso de modo comum a todos os seres reflexivos.

Um símbolo é um conjunto. É uma representação que permite encontrar o comum entre as várias complexidades, pontos de vista e diferenças da apreensão do real. O comum não se refere à apreensão interna de cada um, mas àquilo que condiciona a própria apreensão.

O símbolo é quase uma tradução do real. Algo que pode ser apercebido. Mesmo com toda a liberdade do ser consciente, há algo comum a todos os seres reflexivos, e é por isso que é comum.

### 16. F0038_SEG_001

- score global: 58.3385
- score base: 56.6285
- best profile: adequacao_criterio_verdade_correcao (16.921)
- second profile: apreensao_representacao_consciencia_localidade (16.471)
- profile scores: {'adequacao_criterio_verdade_correcao': 16.921, 'apreensao_representacao_consciencia_localidade': 16.471, 'mediacao_simbolo_linguagem_fechamento': 11.972, 'substituicao_do_real_erro_categorial_erro_de_escala': 15.5215}
- matched phrases: []
- matched terms: ['real', 'correcao', 'verdade', 'interna', 'exige', 'reflexiva', 'sistemico', 'autonomo', 'possiveis', 'possibilidade', 'proposicoes']
- matched hints: ['verdade', 'correcao', 'correção', 'consciência reflexiva', 'consciencia reflexiva', 'fecho sistémico', 'fecho sistemico', 'validade interna', 'sistema autónomo', 'sistema autonomo', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, correcao, verdade, interna, exige, reflexiva, sistemico, autonomo', 'hints gerais: verdade, correcao, correção, consciência reflexiva, consciencia reflexiva, fecho sistémico, fecho sistemico, validade interna', 'perfil dominante no fragmento: adequacao_criterio_verdade_correcao', 'funcao_textual=0.3', 'função textual=exploracao']

É sobre os modos de ser que contêm modos de pensar, de agir, de estar e de se relacionar. Os modos de pensar são expressões internas desses modos de ser. A variedade humana é enorme em potencialidades, capacidades e possibilidades, sendo legítimo formular proposições verdadeiras sobre essas diferenças verificadas. Existe uma correspondência necessária entre capacidades e apropriação a determinados setores, algo que já fazemos implicitamente. A estrutura do universo revela-se na criação e transmissão do conhecimento: não basta descobrir algo, é necessário descrevê-lo de modo que outros o possam repetir, sob pena de a ideia desaparecer. A permanência cultural exige transmissibilidade. A avaliação de competências leva naturalmente à avaliação psicológica, pois o modo de ser condiciona a análise verdadeira dos problemas fundamentais da vida — quem sou, que tipo de pessoa quero ser, com quem me devo ligar, se devo ter filhos. Sem um modo de ser que imponha estas perguntas, elas nem sequer se colocam. A correção de percurso raramente é reflexiva; ocorre geralmente por trauma, devido à resistência natural à mudança e à inação corretiva. Quando a correção não é reflexiva, torna-se traumática. Tudo isto decorre de auto-evidências do próprio sistema: a realidade só pode ser assim, pois qualquer processo exige estrutura, continuidade e possibilidade de correção.

### 17. F0190_SEG_001

- score global: 58.2599
- score base: 56.5499
- best profile: apreensao_representacao_consciencia_localidade (27.7944)
- second profile: mediacao_simbolo_linguagem_fechamento (24.2135)
- profile scores: {'adequacao_criterio_verdade_correcao': 8.314, 'apreensao_representacao_consciencia_localidade': 27.7944, 'mediacao_simbolo_linguagem_fechamento': 24.2135, 'substituicao_do_real_erro_categorial_erro_de_escala': 13.864}
- matched phrases: []
- matched terms: ['real', 'independente', 'representacao', 'apreensao', 'simbolica', 'simbolo', 'sistemico', 'simbolico', 'proposicoes', 'localidade', 'local']
- matched hints: ['representação', 'representacao', 'apreensão', 'apreensao', 'localidade', 'local', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fecho sistémico', 'fecho sistemico', 'fechamento simbólico', 'fechamento simbolico', 'real independente', 'substituição do real', 'substituicao do real', 'sistema autónomo', 'sistema autonomo']
- reasons: ['termos do dossier: real, independente, representacao, apreensao, simbolica, simbolo, sistemico, simbolico', 'hints gerais: representação, representacao, apreensão, apreensao, localidade, local, mediação simbólica, mediacao simbolica', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=1.1', 'função textual=critica']

Ah, não, não sabes o que é que é socialismo. Não, isso não é socialismo. Principalmente em Portugal existe esta conversa, confunde socialismo com social, com orientado para o social, com integrar o outro num sistema de crenças, com essa conversa toda do fundo que radica apenas para uma atitude mais ou menos genérica de, pá, reconhecer que o outro existe. Depois vai ao nível mais absurdo e mais básico, depois permite tudo, como o outro existe qualquer coisa, irrelevante. Como o outro é, como nós somos, como aquilo que é, é, pronto. E independentemente destas coisas todas, já sabem como é que as coisas funcionam. Mas não, então socialismo é o quê? Quais é que receitas de tudo aquilo que caracteriza o socialismo? Porque tens uma representação com simbólica diferente daquilo que é o socialismo. Socialismo, falarem em si, dito, não, porque não é comunismo. Ah, não, não, não é autoritarismo. Não, não. É somente o quê? É somente o quê? É somente, eu digo-te o que é somente, é só na relação mais básica que está aqui, de maneira abrangente, é na proposição de uma qualquer coisa que não serve perante o real. É isto, é um dever ser que, porque canalizado pela própria apreensão da realidade, quando o real faz-se mostrar, faz-se evidenciar, não muda o modo de ser, o modo de pensar, o modo de dizer nada do proponente. É uma crença, é uma manifestação de um modo de ser, de um modo de agir, que cobre todas as decisões, todas as ações, todo o contínuo do ser no ser, que é a resposta mais básica, mais intuitiva, que cola mais rápido, que se manifesta no nosso modo relacional, nós não nos relacionamos, eu não me relaciono com pessoas da China, quer dizer, é local. E é aquilo que vem à primeira, à cabeça, assim que se pensa em qualquer tema, qualquer tema do real, há necessariamente logo um enquadramento na perspectiva do eu para o real.

### 18. F0241_A23_SEG_001

- score global: 57.4599
- score base: 55.7499
- best profile: mediacao_simbolo_linguagem_fechamento (25.871)
- second profile: substituicao_do_real_erro_categorial_erro_de_escala (23.9601)
- profile scores: {'adequacao_criterio_verdade_correcao': 12.9215, 'apreensao_representacao_consciencia_localidade': 21.4529, 'mediacao_simbolo_linguagem_fechamento': 25.871, 'substituicao_do_real_erro_categorial_erro_de_escala': 23.9601}
- matched phrases: []
- matched terms: ['real', 'adequacao', 'apreensao', 'reflexiva', 'simbolica', 'simbolo', 'simbolico', 'autonomo', 'coerencia', 'localidade', 'local']
- matched hints: ['adequação', 'adequacao', 'apreensão', 'apreensao', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fechamento simbólico', 'fechamento simbolico', 'real independente', 'substituição do real', 'substituicao do real', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, adequacao, apreensao, reflexiva, simbolica, simbolo, simbolico, autonomo', 'hints gerais: adequação, adequacao, apreensão, apreensao, consciência reflexiva, consciencia reflexiva, localidade, local', 'perfil dominante no fragmento: mediacao_simbolo_linguagem_fechamento', 'funcao_textual=0.3', 'função textual=desenvolvimento']

pelo facto de se ser homem, uma estrutura biológica que apreende, que vive na apreensão do real, que não vive, ou seja, em que o eu funciona não naquilo que o real é, mas na própria estrutura lógica do ser reflexivo que apreende o real, na adequação do real à realidade, na repetição da experiência apreensiva para se poder ter sequer uma estrutura que permita um símbolo onde o eu possa viver, isso apenas me diz que o que é, é algo que apreende o real e, na própria lógica evolutiva e da simples agregação da permanência de ser que os organismos biológicos têm, então, se o que o organismo faz é bem apreender o real para bem viver, de certo modo, ou somente viver, não poderia ser de outro modo, a reflexividade não poderia acontecer de outro modo que não fosse pela automatização da própria experiência para não se ter que se ter a dedicar cada momento à própria experiência. E quando a experiência fica automatizada, o que sobra é simplesmente a coerência. E é na coerência que pode brotar algo como reflexividade.

Empurrar para auto relação é trocar o auto por eu, para no fim dizer que o que diferencia é a perspetiva, que é o mesmo que dizer local, nem poderia ser de outro modo pá sem limite nem haveria reflexividade. Pelo que disse antes

Claro, o eu não pode ser extra-real, tem de ser sempre local, e só da localidade é que poderia nascer a reflexividade.

### 19. F0241_A25_SEG_002

- score global: 56.1707
- score base: 54.4607
- best profile: apreensao_representacao_consciencia_localidade (36.2519)
- second profile: mediacao_simbolo_linguagem_fechamento (24.171)
- profile scores: {'adequacao_criterio_verdade_correcao': 9.372, 'apreensao_representacao_consciencia_localidade': 36.2519, 'mediacao_simbolo_linguagem_fechamento': 24.171, 'substituicao_do_real_erro_categorial_erro_de_escala': 6.872}
- matched phrases: []
- matched terms: ['real', 'consciencia', 'representacao', 'apreensao', 'reflexiva', 'simbolica', 'simbolo', 'simbolico', 'localidade', 'local', 'linguagem']
- matched hints: ['representação', 'representacao', 'apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'linguagem', 'fechamento simbólico', 'fechamento simbolico', 'real independente', 'substituição do real', 'substituicao do real']
- reasons: ['termos do dossier: real, consciencia, representacao, apreensao, reflexiva, simbolica, simbolo, simbolico', 'hints gerais: representação, representacao, apreensão, apreensao, consciência, consciencia, consciência reflexiva, consciencia reflexiva', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=0.3', 'função textual=exploracao']

A questão é que eu não sei se síntese simbólica que se reconhece não é o mesmo que dizer síntese simbólica, porque para haver síntese simbólica já tem de haver reconhecimento, porque já tem de haver algo que sintetiza, algo que pode sequer sintetizar. Eh pá, eu não creio que um cão, quando vê e tem imagética na sua cabeça, portanto, faz 90% do que nós fazemos quando olhamos para uma coisa, que não conheça aquilo que está a ver e que está a representar. Agora, ele não conhece que conhece que está a ver e está a representar, mas isso também é porque ele não tem mãos, não tem pernas, não tem estrutura onde possa desenvolver uma fala, não pode construir, não pode fazer nada, isso é normal que não tenha.

Cuidado não! Cuidado não! Onde é que haveria de ser reflexivo sem um ser exploratório? Sem um ser que toca coisas, que apreende diretamente o local, o real? Não tenho a certeza que a experiência olfativa seja tão dada à relação com o real na sua boa descrição, que no fundo é isso que a consciência permite fazer, o ser conhecer-se a si no real, conhecendo o real, que pudesse alguma vez servir de fundamento para um ser reflexivo, se não existem. Também não tenho a certeza que apontar para, ah não, é a linguagem, ah não, não, o que é importante é a construção simbólica. Tá bem, mas existe porquê? Mas existe porquê? Existe que estava a estrutura, certo? Isso existe porque não ando com as quatro patas no chão, tenho dois livros para poder manusear o real.

### 20. F0110_A01_SEG_003

- score global: 55.7747
- score base: 54.0647
- best profile: mediacao_simbolo_linguagem_fechamento (35.7106)
- second profile: apreensao_representacao_consciencia_localidade (33.7701)
- profile scores: {'adequacao_criterio_verdade_correcao': 9.822, 'apreensao_representacao_consciencia_localidade': 33.7701, 'mediacao_simbolo_linguagem_fechamento': 35.7106, 'substituicao_do_real_erro_categorial_erro_de_escala': 17.2215}
- matched phrases: []
- matched terms: ['real', 'interna', 'mediacao', 'representacao', 'apreensao', 'simbolica', 'simbolo', 'simbolico', 'substituicao', 'acao', 'quanto']
- matched hints: ['representação', 'representacao', 'apreensão', 'apreensao', 'mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, interna, mediacao, representacao, apreensao, simbolica, simbolo, simbolico', 'hints gerais: representação, representacao, apreensão, apreensao, mediação, mediacao, mediação simbólica, mediacao simbolica', 'perfil dominante no fragmento: mediacao_simbolo_linguagem_fechamento', 'funcao_textual=0.3', 'função textual=desenvolvimento']

Dos filósofos que acompanham as ideias que ascendem da descoberta de que há algo: que eu faço, que eu durmo, que se vai tornando integrado pela quantidade ridiculamente gigante de campo apreensível. O eu quer, o eu vai fazer, integrar o eu.

Integrar o eu por necessário ser como eu–eu. No exterior está o que estaria para qualquer animal, mas é no interior que está o animal que, perante o mesmo real que os outros, apreende mais.

Não recebe apenas o mediado bruto da mediação puramente sensorial. Tem uma máquina biológica que filtra e uma biblioteca de símbolos criados pelo contínuo do ser, da ação humana.

Só nos podemos pensar porque temos símbolos. Nos animais vê-se por graduação diferente, mas o substrato está lá. Os símbolos são os portadores do que chamamos representação. São a relação com que o eu pode interagir.

### 21. F0094_A02_SEG_001

- score global: 55.3957
- score base: 53.6857
- best profile: apreensao_representacao_consciencia_localidade (29.4206)
- second profile: mediacao_simbolo_linguagem_fechamento (24.0215)
- profile scores: {'adequacao_criterio_verdade_correcao': 15.0715, 'apreensao_representacao_consciencia_localidade': 29.4206, 'mediacao_simbolo_linguagem_fechamento': 24.0215, 'substituicao_do_real_erro_categorial_erro_de_escala': 13.672}
- matched phrases: []
- matched terms: ['real', 'verdade', 'representacao', 'apreensao', 'simbolica', 'simbolo', 'sistemico', 'simbolico', 'possiveis', 'possibilidade']
- matched hints: ['verdade', 'representação', 'representacao', 'apreensão', 'apreensao', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fecho sistémico', 'fecho sistemico', 'fechamento simbólico', 'fechamento simbolico', 'real independente', 'substituição do real', 'substituicao do real', 'sistema autónomo', 'sistema autonomo']
- reasons: ['termos do dossier: real, verdade, representacao, apreensao, simbolica, simbolo, sistemico, simbolico', 'hints gerais: verdade, representação, representacao, apreensão, apreensao, mediação simbólica, mediacao simbolica, símbolo', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=0.3', 'função textual=desenvolvimento']

Wittgenstein enfrenta o mesmo problema: a incapacidade de reconciliar o real com aquilo que o apreende. O modo default do ser humano não é viver na descrição do que é, mas na simbolização do que é. Vive-se na representação.

O verdadeiro filósofo ajusta a representação às condições que a tornam possível. Não confunde o HTML com o funcionamento do sistema. Mas o modo default tem de ser assim — viver na representação — porque, caso contrário, a existência seria insuportável e não haveria relações humanas.

### 22. F0241_A22_SEG_004

- score global: 54.8491
- score base: 53.1391
- best profile: mediacao_simbolo_linguagem_fechamento (25.505)
- second profile: adequacao_criterio_verdade_correcao (21.8046)
- profile scores: {'adequacao_criterio_verdade_correcao': 21.8046, 'apreensao_representacao_consciencia_localidade': 13.0055, 'mediacao_simbolo_linguagem_fechamento': 25.505, 'substituicao_do_real_erro_categorial_erro_de_escala': 12.2055}
- matched phrases: []
- matched terms: ['criterio', 'adequacao', 'representacao', 'objetividade', 'reflexiva', 'simbolica', 'simbolo', 'simbolico', 'coerencia']
- matched hints: ['criterio', 'critério', 'adequação', 'adequacao', 'objetividade', 'representação', 'representacao', 'consciência reflexiva', 'consciencia reflexiva', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fechamento simbólico', 'fechamento simbolico', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: criterio, adequacao, representacao, objetividade, reflexiva, simbolica, simbolo, simbolico', 'hints gerais: criterio, critério, adequação, adequacao, objetividade, representação, representacao, consciência reflexiva', 'perfil dominante no fragmento: mediacao_simbolo_linguagem_fechamento', 'funcao_textual=0.65', 'função textual=distincao']

quando se olha para aquilo que se é, esse um ser reflexivo, que é um animal, pois que seres reflexivos, cumprindo os critérios, podem ser não sendo animais, mas aquilo que se conhece que é, é um ser reflexivo que a sua animalidade lhe permite ter a característica de refletir sobre ele próprio, enquadrar-se no seu ponto de vista, ver-se na sua continuidade, na apresentação meticulosa e representada simbolicamente, na sua adequação necessária para se poder sequer andar, sem tropeçar, para que permita o foco, para que permita que o foco seja o único objeto da integração, pois tudo o resto está enraizado na sua animalidade que todos os animais têm. A coerência é o que permite, e não a multiplicidade, e não a sermentes todos.

### 23. F0241_A02_SEG_002

- score global: 53.5383
- score base: 51.8283
- best profile: mediacao_simbolo_linguagem_fechamento (27.4215)
- second profile: apreensao_representacao_consciencia_localidade (15.5215)
- profile scores: {'adequacao_criterio_verdade_correcao': 7.672, 'apreensao_representacao_consciencia_localidade': 15.5215, 'mediacao_simbolo_linguagem_fechamento': 27.4215, 'substituicao_do_real_erro_categorial_erro_de_escala': 13.672}
- matched phrases: []
- matched terms: ['real', 'consciencia', 'reflexiva', 'simbolica', 'simbolo', 'sistemico', 'simbolico', 'quanto', 'circulacao', 'proposicoes']
- matched hints: ['consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fecho sistémico', 'fecho sistemico', 'fechamento simbólico', 'fechamento simbolico', 'real independente', 'substituição do real', 'substituicao do real', 'sistema autónomo', 'sistema autonomo']
- reasons: ['termos do dossier: real, consciencia, reflexiva, simbolica, simbolo, sistemico, simbolico, quanto', 'hints gerais: consciência, consciencia, consciência reflexiva, consciencia reflexiva, mediação simbólica, mediacao simbolica, símbolo, simbolo', 'perfil dominante no fragmento: mediacao_simbolo_linguagem_fechamento', 'funcao_textual=0.3', 'função textual=exploracao']

E a amplitude em que isto se vê de um lado e do outro na relação a ser mantida entre o ser reflexivo e os outros seres reflexivos, e depois o discurso, ou seja, os símbolos comuns que identificam discursos, e ver esta dinâmica depois também relativamente ao que cada ser consciente pensa sobre si, sobre o que se pensa sobre o ser, ou seja, aquilo que se diz sobre o que é isto, e depois, como é óbvio, o que deveria ser isto, que é o plano onde somente se opera, e ver a extensão das relações em como, depois, no que se manifesta, é sempre na criação de sistemas, qualquer modo e círculo de operação entre cada ser consciente contendo todas estas características, operam assim. E quão mais justificações se criam para cada proposição, normalmente é necessária quanto mais afastado do real cada proposição se dirigir.

E pode tentar viverá? Não! Porque isto da necessidade, qual necessidade? Porque se as condições atómicas fossem diferentes, então isto tudo isto podia ser diferente, está bem? Está certo, amigo? Está certo? Está certo? E aí a minha descrição estaria errada, porque, ao descrever o que isto é, ao descrever o real, estaria a descrever outra coisa que não aquilo que é. Mas, para descrever aquilo que poderia ter sido, e já há texto suficiente, o que sequer é descrever aquilo que é, e daquilo que é resulta a necessidade de sequer ser.

### 24. F0097_A02_SEG_001

- score global: 53.4
- score base: 51.69
- best profile: apreensao_representacao_consciencia_localidade (44.1196)
- second profile: mediacao_simbolo_linguagem_fechamento (25.7215)
- profile scores: {'adequacao_criterio_verdade_correcao': 14.6215, 'apreensao_representacao_consciencia_localidade': 44.1196, 'mediacao_simbolo_linguagem_fechamento': 25.7215, 'substituicao_do_real_erro_categorial_erro_de_escala': 10.272}
- matched phrases: []
- matched terms: ['real', 'verdade', 'interna', 'consciencia', 'representacao', 'apreensao', 'simbolica', 'simbolo', 'simbolico', 'acao']
- matched hints: ['verdade', 'representação', 'representacao', 'apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'fechamento simbólico', 'fechamento simbolico', 'validade interna', 'real independente', 'substituição do real', 'substituicao do real', 'coerência interna', 'coerencia interna']
- reasons: ['termos do dossier: real, verdade, interna, consciencia, representacao, apreensao, simbolica, simbolo', 'hints gerais: verdade, representação, representacao, apreensão, apreensao, consciência, consciencia, consciência reflexiva', 'perfil dominante no fragmento: apreensao_representacao_consciencia_localidade', 'funcao_textual=0.3', 'função textual=desenvolvimento']

A filosofia é a atividade do ser humano na sua relação com o real. Não faz sentido aspirar à verdade sem o real como termo da ação. A apreensão é contínua com o movimento do ser. Separar a consciência como algo que opera “por cima” do real é antirreal, fantasioso.

Os símbolos ontológicos — ser, não-ser, eu — são funcionais. São apreendidos por relação, não pela coisa em si. A apreensão é sempre tardia relativamente à atualização do real. As representações referem-se sempre ao real, ainda que internas.

## Sample por perfil — Adequação, critério, verdade e correção

### 1. F0211_SEG_001

- score do perfil: 39.3201
- hints do perfil: ['critério', 'criterio', 'correção', 'correcao', 'objetividade', 'adequação', 'adequacao', 'real independente', 'adequado ao real', 'submetido ao real', 'critério submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['criter', 'correc', 'adequ', 'objetiv']
- anti_hints do perfil: ['consciência reflexiva']
- score global: 46.9314

QQ coisa, o critério é com o real, o ser consciente reflexivo é um objeto do real se assim se quiser dizer, nós vemos as árvores e os animais e de tão diferentes que são conhecemos lhes regularidades de ser, que seria um animal que nos quisesse comer com enormes mandíbulas e ao mesmo tempo levar nos ao cinema, como se reconhece aos humanos, senão adeus psicanálise psicologia psiquiatria, as regularidades do homem são tanto que permitem que eu ainda posso dizer que há pessoas assim e assim e assado e cozido, nem o assado é oco de típico nem o cozido não tem sentido, tem  água que lhe coze o temperamento. A adequação ao real é o que sobra da análise global, de cima, á relação do eu no real. Vista por quem, que sorte, por quem pode de facto bem saber andar no mundo que é, que melhor se corresponder ao que criamos nas nossas cabeças, seguido pelo próprio movimento do contínuo do ser

### 2. F0241_A10_SEG_001

- score do perfil: 36.6978
- hints do perfil: ['verdade', 'erro', 'critério', 'criterio', 'correção', 'correcao', 'real independente', 'adequado ao real', 'submetido ao real', 'critério submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'erro', 'criter', 'correc']
- anti_hints do perfil: []
- score global: 49.5959

Estava a pensar no caminho da contradição... da contradição não, quer dizer, sim, é uma contradição, mas é apenas no caminho que o verdadeiro e o bom são, por necessidade, o resultado da melhor descrição e da melhor ação, da melhor apreensão no sentido de... em relação com o real, quão bem se é no real, relativamente ao real. E estava a pensar no ser que apreende e que vive na estrutura da apreensão, vive na apreensão e revela o real. Em tudo isso, como em tudo isso e todos os exemplos que têm dado, tudo tem falado, vai de uma ponta à outra. E na correção, estava a pensar na correção, mas a correção não é bem... não há nenhuma correção, há apenas o apontar para o caminho real, para o caminho bom, para o caminho verdadeiro.

O erro é somente o desvio, e daí o sentido de continuar, porque o erro não é uma quebra. O erro não é algo separado. O erro é somente a apreensão de um modo de ser que não inclui o real quando o poderia incluir, sabendo que o que se é normalmente é-se, o que se é naturalmente é-se, pela necessária relação da apreensão com o eu e com o real no eu, pela localidade do ponto de vista.

Tanto que qualquer produção, qualquer valor, qualquer, em cada das coisas, quaisquer direções que se inscrevam, que se manifestem no real, que se encarnem no real, quaisquer modos de ser, modos de ser que sendo são justificados somente por um critério interior, muito raramente intocável pelo real, e no outro que, ao incluir o real como pressuposto de tudo, impõe-se, permite-se na correção, e é na correção porquê? Pelo real, pelo que apreende.

### 3. F0241_A13_SEG_001

- score do perfil: 32.3978
- hints do perfil: ['verdade', 'erro', 'correção', 'correcao', 'objetividade', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'erro', 'correc', 'objetiv']
- anti_hints do perfil: ['consciência reflexiva', 'mediação simbólica']
- score global: 62.2237

O que o filósofo faz é procurar o real, é procurar o homem dentro do real. Não é excluir o real e dizer, ok, e agora é só objetos, agora é só símbolos. Não! Porque esses símbolos estão lá por causa de outra coisa qualquer. E os símbolos podem se desviar tanto até que o real estica a corda.

Se eu mal representar a igualdade ontológica que existe em dois seres reflexivos, posso se calhar correr o erro de pensar que lhe posso mandar com um pau à cabeça. Posso achar isto? Isto existe somente por uma parca descrição do real. Não, os objetos existem, agora não existem, agora não há homem, não há mar, os objetos existem.

Os objetos não têm o mesmo estatuto, porque dependem de... Os objetos são dependentes. do modo de ser do ser reflexivo. É somente isto. E o modo de ser do ser reflexivo pode ser mais ou menos ajustado ao real, ao bem e à verdade.

E do real, e depende do real, não sei ouvir a tua resposta, mas depende da relação, da relação, da apreensão, porque só quem apreende, só o que apreende, ou só apreendendo, é que se pode sequer apreender. E só se refletindo é que se pode refletir. Pá, isto são daquelas coisas básicas, não é? Uma pedra não pode, não pode, não faz, não é, não tem, não sabe, não consegue, não existe sequer, é o real, é o real.

É o real, não tem relação, não tem um mecanismo racional interno de detecção, de apreensão do real, de representação e de instauração de uma coordenação das representações internas no contínuo da relação com o real.

### 4. F0070_SEG_002

- score do perfil: 30.7873
- hints do perfil: ['verdade', 'erro', 'objetividade', 'real independente', 'adequado ao real', 'submetido ao real', 'validade', 'validação', 'validacao', 'acerto', 'erro real']
- boost_terms do perfil: ['verdad', 'erro', 'objetiv', 'valida']
- anti_hints do perfil: ['mediação simbólica']
- score global: 60.5047

A validade de uma proposição não pode ser aferida por um sistema que o homem cria. Esse é um erro categorial. A validade depende exclusivamente do real. Contudo, a questão da validade de uma proposição só se coloca quando a proposição pretende operar no registo do verdadeiro ou do falso. Fora desse objetivo, a pergunta perde sentido.

Os sons que o homem produz dependem de vibrações no ar. Essas vibrações são, em número e variedade, muito superiores às vibrações que efetivamente acertam no real de forma verdadeira. Por mera lógica probabilística, é mais provável errar do que acertar. Se não fosse assim, todos viveriam como santos.

A linguagem, enquanto sistema vibratório e simbólico, tem sempre maior capacidade de produzir variações do que o real tem de as validar. A verdade não nasce da proliferação proposicional, mas da sua coincidência efetiva com o real.

### 5. F0241_A24_SEG_003

- score do perfil: 30.2206
- hints do perfil: ['verdade', 'correção', 'correcao', 'adequação', 'adequacao', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'correc', 'adequ']
- anti_hints do perfil: ['consciência reflexiva', 'mediação simbólica']
- score global: 74.3884

Estou a conduzir, tiro as mãos do volante, vou andar, sei lá, 70, 80 kmh, ou seja, 100, 120, 130, tiro as mãos do volante, o carro continua. E já não estou com a mão no volante a manter a relação na regularidade da direção do carro, digamos assim dizer. Estou a olhar em frente, estou a ver a estrada, estou a olhar para um carro e a estrada começa a fazer uma ligeira curva, ou faz uma ligeira curva, a minha mão, a minha mão, ainda que esteja pousada em cima da porta, junto ao vidro, dá um toque, logo. Faz parte da própria constituição do ponto de vista subjetivo, experiencial que está a ter.
o que existe, as relações que existem nesta multiplicidade de eventos que existem nesta experiência de estar durante cinco segundos sem as mãos no volante mostram que as relações que já lá estavam continuam a estar. Aquilo que se atualizou continua a atualizar-se, a velocidade, a direção, a posição do corpo, a atenção, a orientação, a direção, no fundo, o contínuo tem uma direção. Essa direção que já está construída vai continuar a relacionar-se, quer a consciência entre ou não. Pois ela relaciona-se com este manter da relação, este biologismo, se quisermos assim dizer, este vivismo, este acontecer da vida da sua própria definição, únicas, únicas verdadeiras, como é óbvio.
E também teria que ser assim, porque a consciência é somente a relação que advém de um eu reflexivo, que, como já sabemos, é dependentemente um contínuo atualizado localmente. E a consciência, meta-reflexividade, que quisermos, opera porque há já uma estabilização perfeitamente adequada ao real, no fundo, que poderíamos dizer à estabilização da apreensão do eu no real, e opera somente pela coerência que os símbolos compacta, que os símbolos proporcionam, pela adequação da coerência interna imagética ao real que se está a ver, que se está a ouvir, que se está a cheirar, essa correspondência é que permite o contínuo da relação sem intervenção da consciência.

### 6. F0074_A02_SEG_003

- score do perfil: 29.8323
- hints do perfil: ['erro', 'correção', 'correcao', 'adequação', 'adequacao', 'desadequação', 'desadequacao', 'adequado ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['erro', 'correc', 'adequ']
- anti_hints do perfil: []
- score global: 31.181

E a questão era esta: proposições sábias. Sábias no sentido muito ático, como eu uso isto. Mas pronto, tentemos dizer assim: sábias no sentido de melhor adequadas à realidade. Ou seja, proposições que melhor descrevem a realidade.

E o erro mostra-se como desadequação daquilo que se está a propor. Não só da proposição, mas das correlações existentes. Dos meios e dos fins. Envolve tudo. No fundo, envolve o ser.

### 7. F0045_SEG_001

- score do perfil: 29.6126
- hints do perfil: ['verdade', 'correção', 'correcao', 'adequação', 'adequacao', 'desadequação', 'desadequacao', 'adequado ao real', 'correção de representação', 'correção de ação', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'correc', 'adequ']
- anti_hints do perfil: []
- score global: 51.6991

Este quadro permite propor frases verdadeiras sobre aquilo que não é o melhor modo de ser, aplicáveis a qualquer discussão ou dissenso. Os dissensos são, em geral, equívocos mútuos: não apenas sobre o que é dito ou ouvido, mas sobre o que se pensa estar em discussão, acrescidos de fatores primários que impedem a discussão de alguma vez ser verdadeira. Pensando em Camus, nos existencialistas e na alegoria de Sísifo, vê-se que essas respostas são dadas a um problema por eles próprios criado, resultante de um modo de análise limitado, incapaz de retirar valor do facto e de formular proposições verdadeiras sobre o significado da vida. Assim, recorre-se a ajustes comportamentais ou enquadramentos arbitrários do agir humano, como única direção justificável dentro do próprio absurdismo — o que é irrelevante. Mesmo que não se extraia valor do facto, o facto permanece, e é possível ver que estas posições não são verdadeiras: podem ter adequação literária ou funcionar em certos círculos, mas não produzem proposições verdadeiras. Se o fizessem, os modos de ser humanos seriam suicidas, exigindo racionalizar o não-matar-se. O mesmo se observa em pessimismos contemporâneos como o antinatalismo, que constroem justificações morais únicas a partir de enredos desadequados. Isto revela como o intelectualismo meramente formal — inteligente apenas no sentido corrente — produz excecionalismos falsos. Como todas as inteligências formais são colocadas em pé de igualdade no discurso académico e público, torna-se evidente a tendência de qualquer sistema que contenha seres humanos: assim que se institui uma “verdade”, constroem-se imediatamente sistemas formais em torno dela.

### 8. F0025_SEG_001

- score do perfil: 29.4206
- hints do perfil: ['verdade', 'correção', 'correcao', 'objetividade', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'correc', 'objetiv']
- anti_hints do perfil: []
- score global: 24.0029

A crença falsa do formalista da verdade consiste em não buscar a verdade, mas outras coisas, e por isso não propaga qualquer verdade. O intelectualista, o comentarista, qualquer pessoa com alcance comunicacional suficiente para implantar ideias de forma expressiva, incorre neste risco. O revés é que essa pessoa acaba por encarnar a crença que justifica formalmente — muitas vezes através de uma verborreia conceptual (frequentemente kantiana) que tenta enquadrar teorias com premissas erradas, exigindo autojustificações cada vez mais complexas. Assim, a pessoa passa a ser essa crença. O significado da vida encontra-se no tipo de vida que se tem, isto é, no modo de ser. Se o homem faz parte do que é, e é a única entidade conhecida que sabe que é dentro do que é, então o seu modo de ser tem de conformar-se ao real, sem permissões para justificações alternativas. Tudo o que existe são evidências; dualismos sem correspondência no objeto descrito carecem de sentido.

### 9. F0214_SEG_001

- score do perfil: 28.9978
- hints do perfil: ['verdade', 'erro', 'objetividade', 'adequação', 'adequacao', 'real independente', 'adequado ao real', 'submetido ao real', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'erro', 'adequ', 'objetiv']
- anti_hints do perfil: ['consciência reflexiva', 'mediação simbólica']
- score global: 71.463

1 mas eu apreendo mal, a minha mãe que vive nas atualizações dos eus que lhe ocupam o local há de, ainda que não analiticamente, apreendo até melhor, não quero justificação teórica para fazer o que for que mantenha os meus filhos vivos, todos os outros filhos morrem se assim o fosse. O grau de adequação é verdadeiro. Não se exige ao homem o que se exige ao filósofo, o ato filosófico é encarnado pelo filósofo no contínuo de ser um filósofo. Ver mais além é para quem quer viver como vive mas mais além, não impede de se viver já como se vive, se I mais é permitido o que já existe não é contrariado, é melhor dizer mentira sobre equações do que sobre o ser como o pai analfabeto que melhor pai se foi no que eu acho que é ser bom pai, o enquadramento do conteúdo do símbolo é meu pela minha localidade e sem QQ esforço mental ou energético posso simplesmente querer não degradar a relação em que estou inserido, pai filho, irmão indivíduo, whatevs. Já nem sei a que estava a objetar. 2 nem percebi mentir é mal descrever propositadamente com intuito de negar, acho que será assim ou algo parecido, diferente de erro, de mal, as relações humanas são multidisciplinares tens de ter mais imaginação 3 não percebi 4 acho que sim é mesmo só falta de conhecimento teu, pensava que tinhas aqui nesta conversa os ficheiros todo do real, consciência ética etc etc, nem vou escrever mais

### 10. F0241_A02_SEG_001

- score do perfil: 28.9706
- hints do perfil: ['verdade', 'correção', 'correcao', 'objetividade', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'correc', 'objetiv']
- anti_hints do perfil: ['consciência reflexiva']
- score global: 43.0784

A minha posição é a minha posição, é a posição de cada um. Qualquer posição que mal descreva esta obrigatoriedade de perspectiva na apreensão, quer dizer, o próprio ato de apreender, o próprio poder ser apreender, o próprio o ser consequente naquilo que se é ser apreender, o continuar a existir em cada continuar a existir nessa relação de um real, algo do real a apreender, o real, é que...
Os tipos de pensamento que se têm sobre isto, portanto, em cada tema, o que é que não sei quantas explica sobre isto? Quando se faz uma súmula da história da filosofia pelos seus grandes movimentos conceptuais, pela correspondência que tem com o que se percebe ser, e o ponto é que pode-se admitir, o ponto é que, normalmente, por detrás de um já sentido real, afirmado pela repetição durante milénios do ser que está a aprender, ou seja, do ser que está a ter essa ação na sua experiência repetida, moldada no canal, até como é óbvio, de onde brota a consciência,

E o pensamento, vamos chamá-lhe filosófico, pronto, é o pensamento que está a incidir sobre aquele tipo de objeto, sobre o que é, que está na pergunta, que está a trilhar a resposta, ou seja, está a pensar sobre a pergunta que é isto, o que é isto? E pronto, como já dissemos, Kant identifica aqui alguma estrutura, mas marca muito fracamente descrita e também, depois, como é óbvio, é consumido, a descrição dele é consumida por aquilo que ele acha, em vez de ser por aquilo que é. Deixa de haver uma descrição do que é, passa a haver outra coisa qualquer, ou seja, aquilo que o resto do discurso filosófico se torna.

Hipótese ou filosofia ter filosofia, se não for verdadeira, ou pelo menos a busca, a busca para que se diga aquilo que é verdade, e se verdade é o que é real e o modo de manifestar é através da melhor descrição do real, não há muita coisa que seja filosofia, mas também não é suposto haver muita coisa que seja filosofia.

### 11. F0072_SEG_002

- score do perfil: 27.5983
- hints do perfil: ['verdade', 'erro', 'correção', 'correcao', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'erro', 'correc']
- anti_hints do perfil: ['consciência reflexiva']
- score global: 39.7738

Para além disso, o modo como o mundo é apreendido constitui evidência suficiente. Quer se adote uma posição dualista, quer se dissolva a consciência ao ponto de a afastar, como em chesterton, quer se adote um panpsiquismo que identifica ser e consciência, o erro comum é ignorar a necessidade condicional do modo de apreensão.

Essas posições falham por não reconhecerem que a apreensão do real ocorre sempre dentro de um quadro determinado. A observação atribuída a Chesterton é decisiva: descrever corretamente um argumento oposto exige compreender o quadro em que ele opera. O contra-argumento verdadeiro não nega o conteúdo, mas rearranja o quadro.

É nessa simplicidade estrutural que reside a força do pensamento: mudar o quadro é alterar o sentido de tudo o que nele aparece. Assim, o modo de ser verdadeiro surge como o mais natural de todos, porque não há nada mais natural do que aquilo que é.

### 12. F0044_SEG_001

- score do perfil: 27.2706
- hints do perfil: ['verdade', 'objetividade', 'adequação', 'adequacao', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'adequ', 'objetiv']
- anti_hints do perfil: ['mediação simbólica']
- score global: 62.5707

O discurso público não é naturalmente direcionado à realidade, porque a sua própria característica é ser limitado e autorreferencial: fala de si mesmo e dos eventos imediatos, usando as ferramentas que o constituem. Não pode haver enraizamento no real sem que o seu círculo se expanda, o que só seria possível se ideias verdadeiras fossem mais “pegajosas” do que as ideias de esquerda — algo que exigiria sacrifício e, por isso, tende a ser evitado. Alguns filósofos compreenderam a autorreferencialidade, mas fixaram-se nos símbolos da linguagem. A realidade contém objetos, alguns animados, e ver é a melhor forma de navegar; esperar que os animais percecionem o mundo sem representação é incoerente. A complexidade humana deriva da experiência adaptativa: o ser humano é o animal de todos os nichos. Ver melhor o mundo — representar o mundo no cérebro de forma cada vez mais sofisticada — é uma necessidade ontológica imposta pelas condições ambientais de florescimento. O descrever vem depois do ver; historicamente, primeiro surge o objeto. Ainda que respostas emocionais de primeira ordem, adequadas a círculos próximos, tenham valor adaptativo, a sua verdade assenta sempre na realidade, nem que seja pelo seu fundamento biológico.

### 13. F0241_A07_SEG_001

- score do perfil: 25.871
- hints do perfil: ['correção', 'correcao', 'adequação', 'adequacao', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['correc', 'adequ']
- anti_hints do perfil: []
- score global: 37.2672

Toda a progressão do ser é, pela infância e juventude, contínuo da mecânica de relação com o real, necessária, em relação a quê? Ao real. O processo de um bebe para uma criança é a capacidade de entender, logo ser sujeito a, pensar sobre, expressar no, enquanto está de facto a viver na relação da vida. A direção do ser infante é, para o real, ou para o eu, claro que obrigatoriamente dominado pelo eu no início, claro faltava lhe o real, Depois descreve, que é representar, agir e apreender, o que está a acontecer, que real é este no qual eu lá vivo, . Todas as correções, as corretas claro, são se adequação ao ser, as representações, apreensões e acções corrigidas ao real o que se obriga a que quem corrige seja quem saiba o que é o que pode ser e o que deve ser,  o que infante é e pode ser pela condição do poder ser. Se infante usar telemóvel e ver videozinhos, claro que o real está relegado, e agora cada vez mais. É que é na infância que se bem apreende as bases para a reposta á pergunta de cada um o que é viver bem, mais tarde, já um corpo de auto justificaçoes do meio da apreensão e do ser do eu, cristalizado. Já há custo, logo só atingível se com intenção, e esta é subordinada ao modo de ser que se é, igual ao que se era ontem

### 14. F0113_A01_SEG_001

- score do perfil: 25.5706
- hints do perfil: ['verdade', 'critério', 'criterio', 'objetividade', 'real independente', 'adequado ao real', 'submetido ao real', 'critério submetido ao real', 'erro real']
- boost_terms do perfil: ['verdad', 'criter', 'objetiv']
- anti_hints do perfil: ['consciência reflexiva']
- score global: 53.2278

Toda a crítica é uma forma de apreensão pelo homem de qualquer coisa vinda de outro homem. É a apreensão, pelo eu, dos outros eus, daquilo que eles manifestam: pelas suas austeridades, pelas suas obras, pelos seus modos de ser.

A crítica é a colocação do modo de ser que é apreendido relativamente ao modo de ser que é verdadeiro. Porque o objeto da apreensão ocupa sempre uma posição relativamente ao que o incorpora: o real.

Cada atualização contém a relação interna, a relação com o campo de potencialidades, e a relação com outras atualizações. A obrigatoriedade de conceder passagem nasce quando outra atualização existe.

A consciência reflexiva, pela sua localidade, e pela capacidade de pensar o que pensa, o que o outro pensa, como ele é e como o outro é, impõe que o critério para qualquer coisa seja, antes de mais, o real.

### 15. F0092_SEG_002

- score do perfil: 24.6483
- hints do perfil: ['verdade', 'erro', 'adequação', 'adequacao', 'real independente', 'adequado ao real', 'submetido ao real', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'erro', 'adequ']
- anti_hints do perfil: []
- score global: 48.2128

Daí a pergunta: qual o melhor modo de adequação ao real? Onde está a verdade? O melhor modo verdadeiro há de estar sempre relacionado com isto. Quanto melhor for a descrição, maior a aproximação ao real; quanto maior o conhecimento do real, maior a possibilidade de interação, relação e conexão com o que existe e com o que eu sou.

Isto pode ser resumido assim: tu podes fazer tudo, és livre, mas há coisas que, se fizeres, serão mais reais. Sem apelar a utilitarismos, ontologismos ou outros ismos. Todas essas filosofias têm um artifício cifrado.

O que é necessário é uma limpeza: limpeza da falsa filosofia. Clarificação dos termos pelo que eles são, no seu ponto mais simples, simples mas abrangente. Nas conexões necessárias de cada afirmação, de cada coisa que se possa dizer.

O que se exige é o escrutínio não relativista da qualidade filosófica. Dizer: isto é o que é; isto é o porquê do que é; isto é o que os melhores filósofos dizem sobre isto que está a ser descrito. Onde é que erram? Onde é que convergem nos mesmos erros? Simplesmente por não seguirem o caminho do que já se sabe sobre o próprio real.

### 16. F0241_A18_SEG_004

- score do perfil: 24.6483
- hints do perfil: ['verdade', 'erro', 'objetividade', 'real independente', 'adequado ao real', 'submetido ao real', 'acerto', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'erro', 'objetiv']
- anti_hints do perfil: []
- score global: 30.1988

Há sempre verdades, num processo de extração de verdades, há sempre verdade para aquilo sobre aquilo que se está a falar. Se não, estamos a falar de outra coisa, qualquer, que não a relação com o real. Portanto, além das extrações de verdades, tem também de ser enquadrada a relação com o real na sua decomposição, em que a lógica será tentar descrever o que é o real, ao mesmo tempo que se tenta descrever como é que o homem pensante tem vindo a descrever o real, onde é que tem acertado, onde é que tem falhado, onde é que tem depois derivado para a sua busca contínua de sistemas autorreferenciais,

E a questão é, isso tem logo de ser ordenado, não só como já está a ser na camada zero e na camada um, mas logo pelo objeto, na sequência, logo na sequência de o que é que isto diz, em que é que isto descreve o real, qualquer realidade que esteja a descrever, e como é que se pende a descrever isto, quais são os modos do ser que incidem sobre a relação e como isso são erros, desvios à naturalidade do ser no caminho da boa descrição para a verdade e para o bem.

### 17. F0093_A01_SEG_001

- score do perfil: 24.3903
- hints do perfil: ['verdade', 'erro', 'critério', 'criterio', 'real independente', 'adequado ao real', 'submetido ao real', 'critério submetido ao real', 'erro real']
- boost_terms do perfil: ['verdad', 'erro', 'criter']
- anti_hints do perfil: ['consciência reflexiva']
- score global: 49.8976

Estava a ouvir o Sam Harris e a pergunta era se acabar com a guerra seria bom para todos e, logo, a coisa boa a fazer, porque somos seres conscientes e o que é bom para a sociedade é bom para o indivíduo. Quando questionado se o indivíduo que quer continuar a produzir e vender armas estaria errado nas suas preferências, a resposta foi que sim, porque visto de cima a sociedade não está tão boa como podia ser. E quando se pergunta o que fazer se esse indivíduo não quiser aderir à prescrição, responde-se que esse é um dos que se fecha da sociedade, indo mais longe ao dizer que, se houvesse uma máquina que mudasse o interruptor do homem para preferir estados alegres e bonitos, isso seria o que se deveria fazer.

Tantos erros em cada frase: suposições, egocentrismo, visão curta do campo das possibilidades, subjugação do real a um critério de verdade dependente da sociedade, afastando o homem do real e ficando apenas com o fluxo, a encarnação de viver no processo.

### 18. F0241_A18_SEG_003

- score do perfil: 24.363
- hints do perfil: ['critério', 'criterio', 'adequação', 'adequacao', 'real independente', 'adequado ao real', 'submetido ao real', 'critério submetido ao real', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['criter', 'adequ']
- anti_hints do perfil: []
- score global: 31.4351

Ah, mas o teu critério é tão, é tão como vale tanto como outro qualquer outro critério. Vale, vale tanto? Como é que medes esse tanto? Ah, há de ser pela... Pois, amigo, há de ser pela adequação à realidade, adequação ao real.

Mesmo no teu cenário fofo de possibilidade de algo ser somente porque há mais uma opção que, em abstrato, se poderia incluir nesse campo de possibilidades, é somente aprender mal o campo de possibilidades. Não é mais do que outra coisa. É aprender mal e descrever mal o ser, o poder e o dever ser.

### 19. F0087_A01_SEG_002

- score do perfil: 24.363
- hints do perfil: ['correção', 'correcao', 'objetividade', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['correc', 'objetiv']
- anti_hints do perfil: []
- score global: 25.9777

A crítica, quando deve ser feita, deve ser feita perguntando apenas: o que é que se está a dizer sobre o que é, neste livro, nesta ideia, neste artigo, nesta opinião? Porque os seres humanos vivem, de facto, nos seus círculos locais. Cabe à filosofia percorrer todo o espaço.

Antes de prescrever valores, a filosofia deveria olhar para o real e descrevê-lo com precisão: não apenas que há objetos, mas que objetos; não apenas que há relações, mas que tipos de relações; quantas relações correlacionadas existem; que tipos e modos de ser já descobrimos existir e conseguimos identificar como integrados na realidade.

Isso não existe. E por isso a crítica tem de começar por perguntar o que é que esta pessoa achava daquilo sobre o que falava — o que é, no fundo, insistir em olhar para as estrelas.

### 20. F0168_SEG_001

- score do perfil: 24.171
- hints do perfil: ['verdade', 'correção', 'correcao', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'correc']
- anti_hints do perfil: []
- score global: 33.0351

Isto é uma banalidade, mas ter mais, não, ter de um tipo de relações, de um tipo de apreensão do real, em que o que está a ser apreendido é o exterior ou o interior, isto não é bem assim, porque a apreensão torna tudo interior e, por própria necessidade do conteúdo da relação, a autojustificação é aquela que sai daquilo que é apreendido. Sendo esse apenas a ligação real, essa é a ligação real que leva a todo o tipo de depois ser o que existe no campo que é composto pelo campo de apreensão na correspondência com o real, na correspondência que é apreendida. verá, ah, o que se tem de ter, não se vivendo no modo ser, de ser do real, mas ser do eu, é que leva às necessidades, à necessidade de pensar-se que tudo que, como o campo é autojustificado, então que nada vale, que verdade, justiça, bem, que nada vale, que o real nada vale.

### 21. F0089_SEG_002

- score do perfil: 24.171
- hints do perfil: ['verdade', 'correção', 'correcao', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'correc']
- anti_hints do perfil: []
- score global: 27.6029

Por isso se chama leis às leis civilísticas. Depois, como é óbvio, tudo se quer abranger e tudo se chama lei, mas as leis civilísticas e as leis físicas são, no fundo, leis: descrições das regularidades dos modos de ser.

Um dos modos de ser do homem é comprar e vender, trocar, dar e receber, mutuar, emprestar. Isto é verdade desde o Código Civil napoleónico e continuará a ser verdade em todos os sistemas que preservem a liberdade e a dignidade. O sinalagma perfeito destas relações jurídicas traduz a correspondência do real com a liberdade e a dignidade.

Como poderia ser de outro modo? Se há paridade ontológica entre as pessoas que compõem uma sociedade, então há regularidade nos modos de ser entre modos de ser iguais. As posições filosóficas opostas teriam de aceitar, pela sua própria lógica, que não existissem arquétipos nem modos de ser estáveis.

### 22. F0093_A02_SEG_001

- score do perfil: 24.0298
- hints do perfil: ['verdade', 'erro', 'real independente', 'adequado ao real', 'submetido ao real', 'validade', 'validação', 'validacao', 'erro real']
- boost_terms do perfil: ['verdad', 'erro', 'valida']
- anti_hints do perfil: ['consciência reflexiva']
- score global: 28.1691

A crítica só é válida se for verdadeira. O realismo que exclui o homem só existe se não se colocar o homem no real. Porque este pensamento não existe? Porque ninguém junta as peças já conhecidas? Pelo formalismo da filosofia, pela compartimentalização do conhecimento, pela sombra da ciência, pela proliferação de professores que resumem filosofia, pelo barulho, pelo cinismo.

Os erros são fáceis de ver e inevitáveis ao ser reflexivo. A ausência de clareza espanta. Depois de visto, vê-se em todo o lado.

### 23. F0241_A04_SEG_001

- score do perfil: 23.721
- hints do perfil: ['verdade', 'critério', 'criterio', 'real independente', 'adequado ao real', 'submetido ao real', 'critério submetido ao real', 'correção de representação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'criter']
- anti_hints do perfil: ['consciência reflexiva']
- score global: 65.9242

2 + 2 igual a 4 funciona como sua própria justificação, mas ainda se pode ir a elementos mais básicos, mais profundos, aos elementos axiomáticos de um sistema, e depois diz-se que ah, não, não há, porque a derivação é infinita. Claro, claro. Claro que sim, como é óbvio. Porque a domização de 2 + 2 ser 4 não é aquilo que compõe o 2 e o 2 e o 4 que faz com que seja verdade, mas é o facto de o 2 e o 2 serem 4, essa relação que existe, continuar a permanecer no contínuo da existência dentro do sistema que diz que 2 + 2 é 4, existe, é real, representa a realidade.

porque pende para encontrar as... pende não, faz parte, não é? Encontra-se as justificações, os axiomas, os fundamentos de uma qualquer proposição apenas em dois lados. São os únicos lados possíveis assim que algo existe, ou seja, assim que há. E esses dois lados são ou naquilo que há, na realidade, naquilo que é, ou então pela localidade de todos os seres reflexivos, é pela perspectiva em que está inserido e é por essa imposição de derivação do eu para o real que a comparação entre qualquer tipo de critério ou a justaposição entre qualquer tipo de critério dentro do quadro da apreensão do real pelo eu é no eu que reside a base, é no eu que reside o quadro lógico. Portanto, é normal, seja em um eu, é normal. Não assim assim tinha sido descoberta assim que o homem começou a pensar, não foi assim. É uma luta constante na apreensão, na boa apreensão do real, que obriga, como é óbvio, também à descrição do real. A apreensão por si só é pouca se não houver descrição energética, descrição ou representação, não houver representação, a representação não pode ser algo muito interno e descrição contém um interno e um externo, na relação entre o que existe.

### 24. F0088_A02_SEG_002

- score do perfil: 23.721
- hints do perfil: ['verdade', 'correção', 'correcao', 'real independente', 'adequado ao real', 'submetido ao real', 'correção de representação', 'correção de ação', 'erro real', 'descrever corretamente']
- boost_terms do perfil: ['verdad', 'correc']
- anti_hints do perfil: ['consciência reflexiva']
- score global: 51.1635

O ser consciente reflexivo é o único que amplia o seu campo de possibilidades porque o conhece. Reconhecer a liberdade do homem não é uma necessidade interna, mas correspondência com o real. É uma proposição verdadeira porque corresponde ao que é.

## Sample por perfil — Apreensão, representação, consciência e localidade

### 1. F0097_A02_SEG_001

- score do perfil: 44.1196
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'humano situado', 'interioridade', 'apreender', 'representar', 'modo humano', 'situação humana', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'inter', 'human']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 53.4

A filosofia é a atividade do ser humano na sua relação com o real. Não faz sentido aspirar à verdade sem o real como termo da ação. A apreensão é contínua com o movimento do ser. Separar a consciência como algo que opera “por cima” do real é antirreal, fantasioso.

Os símbolos ontológicos — ser, não-ser, eu — são funcionais. São apreendidos por relação, não pela coisa em si. A apreensão é sempre tardia relativamente à atualização do real. As representações referem-se sempre ao real, ainda que internas.

### 2. F0094_A01_SEG_004

- score do perfil: 44.0014
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'interioridade', 'presença', 'presenca', 'apreender', 'representar', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'local', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 51.5916

A liberdade existe em cada decisão consciente, quando se interrompe o viver mecânico e se pergunta: “o que devo fazer?”. É um ajuste do eu ao ser, apreendido localmente. O ser inclui as características animais de preservação da comunidade, mesmo quando não coincidem com abstrações intelectuais.

Os modos de vida locais pedem respostas locais. Isso não invalida limites do real: não se pode voar. A liberdade é o campo da relação do ser reflexivo com o real, mediada pela representação.

Kant estava certo ao reconhecer a mediação da apreensão, mas errou ao conferir-lhe estatuto ontológico separado. Faltava-lhe o conhecimento biológico moderno. O espantoso é que, mesmo com o imaginário atual, os erros persistam.

### 3. F0203_SEG_001

- score do perfil: 42.3014
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'ponto de vista', 'interioridade', 'apreender', 'representar', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'local', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 40.5315

as consciencias tocam nas apreensoes estabilizadas internas, - no ato de fazer sentido , que é somente o ato de recber os inputs neurologicos que tornaram registados a informaçao captada e transmitida desde o sensor, que sabemos tao bem capaz de criar imagem, e creio que imagetica ha de ser tao identica a imagem, - e nas externas,  - aind que as externas filtradas pelo sensor, que se cre ser tao bom e tmb ninguem discute ja que a imagem que recebo ao olhar parecer ser de facto a imagem que é, daquela localidade e ponto de vista, - nao ha consciencia a tocar sem meio, ondas som telele, whatevi, sao so mais filtros irrelevantes, há no fim apenas um real - o outro - a filtrar um pensamento num meio inteligivel para que outro real, eu, passe a filtrar e a representar o que eu apreendi pela tua externalizaçao do teu pensamento. a ligaçao fisica é inegavel

### 4. F0241_A21_SEG_003

- score do perfil: 40.6014
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'interioridade', 'apreender', 'representar', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'local', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 47.0

Porque na apreensão que a apreensão acontece no eu, não é? É o eu que apreende. Os muitos eus, os muitos eus, claro, com as suas localidades, cada um, mas sendo a consciência uma das partes da relação do eu no real, essa primoração da relação do eu no real, estruturada pela própria apreensão, limitada pelo próprio campo que a apreensão, a apreensão, e depois, como é óbvio, porque a apreensão inclui a representação já, mas também, como é óbvio, também exercida na ação e na descrição, mas o campo das potencialidades, quer dizer, flutua à medida da finesa ou não da relação.

E a finesa pode ser em estado simples, a experiência certa, e pode ser em estado longo e inteiramente introspectivo, mas pode também estar certa. É só mais rara. A adequação natural ao real é aquilo que permite sequer o real interagir, por isso sim na própria representação, não é? Saber como é que o real é, tanto que sabe que se consegue mexer.

### 5. F0108_A01_SEG_001

- score do perfil: 38.8701
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'ponto de vista', 'interioridade', 'apreender', 'representar', 'modo humano', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 59.6278

A apreensão é o modo de significação das diferentes atualizações do ser. O símbolo é o enquadramento do real, o enquadramento daquilo que é. Pela própria estrutura da apreensão surgem interações entre o eu e o real, entre o eu e o eu, entre tudo isso.

Quando um símbolo representa um conceito maior — por exemplo, um 7 poder ser composto por 7 — isso decorre das diferenças dos tipos de apreensão, dos pontos de vista, dos constituintes, dos limites e dos círculos daquilo que está a atualizar. Dependendo do ponto de vista, pode-se ver um estágio que não é final, mas apenas o antecessor do seguinte.

O símbolo embarca o real conforme o ponto de vista, porque tem de incorporar estruturas lógicas necessárias. A lógica é a manutenção da inteligibilidade da relação eu–real. O real incorpora o eu, mas a lógica é a forma de explicitar isso de modo comum a todos os seres reflexivos.

Um símbolo é um conjunto. É uma representação que permite encontrar o comum entre as várias complexidades, pontos de vista e diferenças da apreensão do real. O comum não se refere à apreensão interna de cada um, mas àquilo que condiciona a própria apreensão.

O símbolo é quase uma tradução do real. Algo que pode ser apercebido. Mesmo com toda a liberdade do ser consciente, há algo comum a todos os seres reflexivos, e é por isso que é comum.

### 6. F0241_A11_SEG_004

- score do perfil: 38.0701
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'memória', 'memoria', 'apreender', 'representar', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'memor']
- anti_hints do perfil: []
- score global: 46.9314

Estava a pensar em como, quando se fala com alguém, se marca um encontro no dia seguinte, um dia qualquer, na semana seguinte, a uma hora qualquer, num sítio qualquer, como é que é lembrada essa memória? Porque a lembrança dessa memória importa, não só a retenção da memória, mas como a consciência dessa memória, o awareness dessa memória, ou pelo menos daquilo que a memória implica. E vê-se que é como, pelo que se é, e o que se é é não só o apreender de sons ou de imagens quando se fala com outra pessoa, e se marca algo, mas é a representação da relação que está a ser instituída, a representação de um espaço, de um sítio, de alguém, de algo que se vai atualizar num certo sítio e que está a ser representado por quem está naquela relação.

Toda a experiência apreensiva da relação da memória, que é o ato de a ter no momento, naquele momento, é a própria experiência vivida da continuidade do ser. Não haveria sequer memória. Memória é só isto.

Memória é a permanência da relação de ter a memória naquele contexto representacional, simbólico, mas não se limitando a ele próprio, porque contendo a cadência que estava a ser instituída na relação física e na relação mental, na apreensão que faz a memória. A memória é sempre fiel à cadência do ser, e o ser posiciona-se, ainda que dentro do real, relativamente ao real, mas limitado pelo real. Sendo a relação da apreensão com o real, a direção é sempre o real, a manutenção da relação que se tem estado a manter.

### 7. F0195_SEG_001

- score do perfil: 38.0701
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'memória', 'memoria', 'apreender', 'representar', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'memor']
- anti_hints do perfil: []
- score global: 28.8029

Porque o próprio método de aprender, que é apreender, representar, porque representando-se, cria-se o caminho para a permanência na memória, para a potencialidade da permanência na memória, para o acesso, para a padronização, para a junção das representações restantes da consciência, e aprendendo, e aprender é apreender o real, é representar o real, qualquer coisa que seja.

### 8. F0217_SEG_001

- score do perfil: 37.9519
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'apreender', 'representar', 'modo humano', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'local']
- anti_hints do perfil: []
- score global: 40.5315

E, tendo isto nisto a reconhecer isto, na perspectiva local e de horizonte de cada ser consciente reflexivo, até vai ser muito fronte e vê-se, é um evento, muito fronte com o real diz: «o que é isto?» «What is this?» «O que?» «What?» Primeiro, a primeira representação daquilo pela própria representação antes de se ir para isto diz, para o real, passa-se pela pergunta, a pergunta necessária que o filtro da própria apreensão passa pelo valor indutivo dela. Isso vê-se pelo modo como o homem funciona.

### 9. F0073_SEG_001

- score do perfil: 37.3621
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'ponto de vista', 'interioridade', 'apreender', 'representar', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 47.7314

A questão colocada por Thomas Nagel em “What Is It Like to Be a Bat?” interroga a relevância do ponto de vista subjetivo e se este obriga à separação ontológica da consciência. O argumento funda-se na impossibilidade de aceder ao “como é” de outra criatura, sugerindo uma interioridade inacessível ao real objetivo.

Contudo, o facto de um morcego — ou qualquer outro animal — ser capaz de representação não obriga à conclusão de que a consciência seja uma interioridade separada do real. Pelo contrário, essa capacidade aponta para a consciência como expressão das condições reais em que o ser opera.

A dificuldade apontada por Nagel resulta de absolutizar o ponto de vista como fronteira ontológica, em vez de o compreender como limitação condicional da apreensão. A consciência não está fora do real; é uma forma altamente complexa de relação com o real, condicionada pelo corpo, pelo meio e pelas possibilidades do ser.

### 10. F0241_A07_SEG_002

- score do perfil: 37.1701
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'interioridade', 'apreender', 'representar', 'modo humano', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 49.3062

O socialismo pode ser descrito de maneira ontológica, um sistema de crenças que depois se torna modo de ser, em que a relação eu-real é muito fraca, em que o plano do dever ser é sobreposto a qualquer plano do ser e do poder ser, especialmente do poder ser. É no plano da apreensão do real e do discurso sobre essa apreensão do real, é autojustificativo nos seus próprios termos.

Há um grau de projeção diferente, há prioridades diferentes do campo da relação que eu tenho comigo próprio e da relação que eu tenho com o real e com o real comigo próprio. O real é secundário na relação de mim comigo próprio, toda a sua apreensão interior, quase sem tocar o cortado fora.

Esquecemo-nos que o que eu sou, claro, é também o real, mas aí, consumido pela própria estrutura interna de responsabilidade, ela consegue manifestar-se no real, consegue atualizar-se a consciência pela quantidade de representações que tem pelos caminhos neurológicos dos neurónios pelo corpo inteiro que têm sobre a instância em que se está a operar no real, a apreensão é isto também, integra isto. Então, quando há essa quase possibilidade mesmo real de viver na apreensão do real, então já se vive no mundo do eu, no eu-eu e não no mundo do eu-real.

Começando a caminhada sobre a pergunta que é isto de viver bem e operar somente numa teoria qualquer, num quadro lógico qualquer, não fazê-lo operar no real. A norma é eu-eu, mas nesse eu-eu é igual, mas existe mais. As tuas regras de verificabilidade estão limitadas. Existe mais. Estão falsas. Há uma...

### 11. F0214_SEG_001

- score do perfil: 36.2519
- hints do perfil: ['apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'humano situado', 'apreender', 'modo humano', 'situação humana', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'consc', 'local', 'human']
- anti_hints do perfil: []
- score global: 71.463

1 mas eu apreendo mal, a minha mãe que vive nas atualizações dos eus que lhe ocupam o local há de, ainda que não analiticamente, apreendo até melhor, não quero justificação teórica para fazer o que for que mantenha os meus filhos vivos, todos os outros filhos morrem se assim o fosse. O grau de adequação é verdadeiro. Não se exige ao homem o que se exige ao filósofo, o ato filosófico é encarnado pelo filósofo no contínuo de ser um filósofo. Ver mais além é para quem quer viver como vive mas mais além, não impede de se viver já como se vive, se I mais é permitido o que já existe não é contrariado, é melhor dizer mentira sobre equações do que sobre o ser como o pai analfabeto que melhor pai se foi no que eu acho que é ser bom pai, o enquadramento do conteúdo do símbolo é meu pela minha localidade e sem QQ esforço mental ou energético posso simplesmente querer não degradar a relação em que estou inserido, pai filho, irmão indivíduo, whatevs. Já nem sei a que estava a objetar. 2 nem percebi mentir é mal descrever propositadamente com intuito de negar, acho que será assim ou algo parecido, diferente de erro, de mal, as relações humanas são multidisciplinares tens de ter mais imaginação 3 não percebi 4 acho que sim é mesmo só falta de conhecimento teu, pensava que tinhas aqui nesta conversa os ficheiros todo do real, consciência ética etc etc, nem vou escrever mais

### 12. F0241_A25_SEG_002

- score do perfil: 36.2519
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'apreender', 'representar', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc', 'local']
- anti_hints do perfil: []
- score global: 56.1707

A questão é que eu não sei se síntese simbólica que se reconhece não é o mesmo que dizer síntese simbólica, porque para haver síntese simbólica já tem de haver reconhecimento, porque já tem de haver algo que sintetiza, algo que pode sequer sintetizar. Eh pá, eu não creio que um cão, quando vê e tem imagética na sua cabeça, portanto, faz 90% do que nós fazemos quando olhamos para uma coisa, que não conheça aquilo que está a ver e que está a representar. Agora, ele não conhece que conhece que está a ver e está a representar, mas isso também é porque ele não tem mãos, não tem pernas, não tem estrutura onde possa desenvolver uma fala, não pode construir, não pode fazer nada, isso é normal que não tenha.

Cuidado não! Cuidado não! Onde é que haveria de ser reflexivo sem um ser exploratório? Sem um ser que toca coisas, que apreende diretamente o local, o real? Não tenho a certeza que a experiência olfativa seja tão dada à relação com o real na sua boa descrição, que no fundo é isso que a consciência permite fazer, o ser conhecer-se a si no real, conhecendo o real, que pudesse alguma vez servir de fundamento para um ser reflexivo, se não existem. Também não tenho a certeza que apontar para, ah não, é a linguagem, ah não, não, o que é importante é a construção simbólica. Tá bem, mas existe porquê? Mas existe porquê? Existe que estava a estrutura, certo? Isso existe porque não ando com as quatro patas no chão, tenho dois livros para poder manusear o real.

### 13. F0086_SEG_002

- score do perfil: 33.9621
- hints do perfil: ['representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'interioridade', 'memória', 'memoria', 'representar', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['repre', 'consc', 'inter', 'memor']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 38.2561

A crítica é ao hiperestruturalismo que nos faz perder o processo. Vê-se isso até na forma como se retrata o génio, como no filme sobre Oppenheimer: tenta-se mostrar que ele via algo que mais ninguém via, como se tivesse uma capacidade especial. Mas isso é falso. Ele via porque tinha o substrato das descobertas anteriores. Sem Bohr e a mecânica quântica, não teria concebido nada.

O conhecimento é cumulativo, depende da memória, da inscrição prévia. Não há pensamento sem repetição, sem caminhos desenhados, sem cadeias neuronais físicas. Mesmo a imaginação exige inscrição. Fora o trauma — que cria memória direta — todo o pensamento exige repetição.

Sem memória, não há consciência. Sem capacidade de transformar sensação exterior em representação interna, não há pensamento.

### 14. F0097_A02_SEG_002

- score do perfil: 33.8439
- hints do perfil: ['apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'interioridade', 'apreender', 'modo humano', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'consc', 'local', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 48.1595

A epistemologia de Kant não tem implicações ontológicas; quando bem descrita, confirma-as. O afastamento do real explica-se pelo modo de apreensão individual e gera formas cada vez mais distantes do real, como certas psicologias que deslocam o eu para uma esfera fantasmagórica.

O panpsiquismo é isto ao quadrado. O eu é um arranjo de atualizações estruturais com mecanismos de manutenção. Cortem-me e vejam: há células, não há universos internos. Cada localidade que me compõe é atualização de potencialidades dessa localidade. A consciência não absorve o real; é uma atualização local dele. Qualquer filosofia que faça o contrário é erro categorial.

### 15. F0110_A01_SEG_003

- score do perfil: 33.7701
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'humano situado', 'interioridade', 'apreender', 'representar', 'modo humano', 'situação humana', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'inter', 'human']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 55.7747

Dos filósofos que acompanham as ideias que ascendem da descoberta de que há algo: que eu faço, que eu durmo, que se vai tornando integrado pela quantidade ridiculamente gigante de campo apreensível. O eu quer, o eu vai fazer, integrar o eu.

Integrar o eu por necessário ser como eu–eu. No exterior está o que estaria para qualquer animal, mas é no interior que está o animal que, perante o mesmo real que os outros, apreende mais.

Não recebe apenas o mediado bruto da mediação puramente sensorial. Tem uma máquina biológica que filtra e uma biblioteca de símbolos criados pelo contínuo do ser, da ação humana.

Só nos podemos pensar porque temos símbolos. Nos animais vê-se por graduação diferente, mas o substrato está lá. Os símbolos são os portadores do que chamamos representação. São a relação com que o eu pode interagir.

### 16. F0241_A10_SEG_002

- score do perfil: 33.7359
- hints do perfil: ['apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'ponto de vista', 'interioridade', 'apreender', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'consc', 'local', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 49.3457

Sim, quer dizer, a quebra, a quebra acontece em qualquer atualização de um ser reflexivo. Ou, sim, porque o contínuo da relação do animal que procura comida e que foge dos predadores, esse contínuo está lá. Aquilo que o faz ser em relação a um real repetido torna-se um contínuo.

E os deterministas têm razão neste sentido. Claro, tudo é físico, tudo é uma relação de relação, tudo é... Ah, então não há consciência. Não, pá, pelo amor de Deus! Pelo amor de Deus! Aí fala-se outra coisa que não causalidade. Aí fala-se de algo que consegue operar sobre a própria relação. Portanto, fala-se do intérprete da relação, fala-se de ampliação do campo das potencialidades a um ponto que nunca seria o mesmo de uma relação causal que aparece somente pelo facto de se poder olhar para aquilo que é e não sendo aquilo que se tem vindo a ser.

O campo das potencialidades da relação não reflexiva não tem nada a ver com o campo das potencialidades da relação reflexiva. As atualizações que se podem relacionar num e no outro são ridiculamente distintos. A reflexividade sobre a própria, sobre o real, o facto de se permitir poder conceber outras atualizações e outros campos de atualizações e outras relações fora do local, fora da relação causal que manifestou essa própria concepção, aí diz tudo. Está-se a falar de outro plano, está-se a falar na curiosidade imagética, na curiosidade não, está-se a falar do mapeamento imagético do real, de tudo o que se apreende dele e se apreende no real.

E o mais cético, com os argumentos todosiros, quiser inventar para poder mandar embora a consciência, que é algo que se sabe que se é, esse mais cético, assim que tivesse proposto que a consciência não existia, assim que tivesse proposto que não existe reflexão sobre o real, então a seguir deveria ter cozido a boca, porque não podia nunca mais falar. Podemos discordar todos sobre consciência, os termos, o que quisermos, mas a reflexividade, essa característica que oferece...

### 17. F0241_A24_SEG_003

- score do perfil: 33.6519
- hints do perfil: ['apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'ponto de vista', 'interioridade', 'apreender', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'consc', 'local', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 74.3884

Estou a conduzir, tiro as mãos do volante, vou andar, sei lá, 70, 80 kmh, ou seja, 100, 120, 130, tiro as mãos do volante, o carro continua. E já não estou com a mão no volante a manter a relação na regularidade da direção do carro, digamos assim dizer. Estou a olhar em frente, estou a ver a estrada, estou a olhar para um carro e a estrada começa a fazer uma ligeira curva, ou faz uma ligeira curva, a minha mão, a minha mão, ainda que esteja pousada em cima da porta, junto ao vidro, dá um toque, logo. Faz parte da própria constituição do ponto de vista subjetivo, experiencial que está a ter.
o que existe, as relações que existem nesta multiplicidade de eventos que existem nesta experiência de estar durante cinco segundos sem as mãos no volante mostram que as relações que já lá estavam continuam a estar. Aquilo que se atualizou continua a atualizar-se, a velocidade, a direção, a posição do corpo, a atenção, a orientação, a direção, no fundo, o contínuo tem uma direção. Essa direção que já está construída vai continuar a relacionar-se, quer a consciência entre ou não. Pois ela relaciona-se com este manter da relação, este biologismo, se quisermos assim dizer, este vivismo, este acontecer da vida da sua própria definição, únicas, únicas verdadeiras, como é óbvio.
E também teria que ser assim, porque a consciência é somente a relação que advém de um eu reflexivo, que, como já sabemos, é dependentemente um contínuo atualizado localmente. E a consciência, meta-reflexividade, que quisermos, opera porque há já uma estabilização perfeitamente adequada ao real, no fundo, que poderíamos dizer à estabilização da apreensão do eu no real, e opera somente pela coerência que os símbolos compacta, que os símbolos proporcionam, pela adequação da coerência interna imagética ao real que se está a ver, que se está a ouvir, que se está a cheirar, essa correspondência é que permite o contínuo da relação sem intervenção da consciência.

### 18. F0104_A01_SEG_002

- score do perfil: 33.6519
- hints do perfil: ['apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'interioridade', 'apreender', 'modo humano', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'consc', 'local', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 65.9242

Se o modo de ser vive — não é, mas vive — e se o modo de ser consciente reflexivo vive pela apreensão como localidade, e se o modo de apreensão é simbólico, então estas ideias de que não precisamos de preencher as realidades com símbolos adequados não fazem sentido. O ser reflexivo tem sempre esta característica.

E tentar retirar essa dimensão ao ser reflexivo, descrevê-lo num sistema interno, para retirar o herói da equação, os arquétipos — todos os arquétipos que são descritivos são verdadeiros porque descrevem o real. Se não descrevem o real, então são sempre valorativos.

### 19. F0241_A04_SEG_001

- score do perfil: 33.6519
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'interioridade', 'apreender', 'representar', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'local', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 65.9242

2 + 2 igual a 4 funciona como sua própria justificação, mas ainda se pode ir a elementos mais básicos, mais profundos, aos elementos axiomáticos de um sistema, e depois diz-se que ah, não, não há, porque a derivação é infinita. Claro, claro. Claro que sim, como é óbvio. Porque a domização de 2 + 2 ser 4 não é aquilo que compõe o 2 e o 2 e o 4 que faz com que seja verdade, mas é o facto de o 2 e o 2 serem 4, essa relação que existe, continuar a permanecer no contínuo da existência dentro do sistema que diz que 2 + 2 é 4, existe, é real, representa a realidade.

porque pende para encontrar as... pende não, faz parte, não é? Encontra-se as justificações, os axiomas, os fundamentos de uma qualquer proposição apenas em dois lados. São os únicos lados possíveis assim que algo existe, ou seja, assim que há. E esses dois lados são ou naquilo que há, na realidade, naquilo que é, ou então pela localidade de todos os seres reflexivos, é pela perspectiva em que está inserido e é por essa imposição de derivação do eu para o real que a comparação entre qualquer tipo de critério ou a justaposição entre qualquer tipo de critério dentro do quadro da apreensão do real pelo eu é no eu que reside a base, é no eu que reside o quadro lógico. Portanto, é normal, seja em um eu, é normal. Não assim assim tinha sido descoberta assim que o homem começou a pensar, não foi assim. É uma luta constante na apreensão, na boa apreensão do real, que obriga, como é óbvio, também à descrição do real. A apreensão por si só é pouca se não houver descrição energética, descrição ou representação, não houver representação, a representação não pode ser algo muito interno e descrição contém um interno e um externo, na relação entre o que existe.

### 20. F0108_A02_SEG_001

- score do perfil: 33.6519
- hints do perfil: ['apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'interioridade', 'apreender', 'modo humano', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'consc', 'local', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 62.7776

Daí a importância da língua. Se cada consciência é um mundo local, interessa saber quantos mundos existem e como se repartem as estruturas. O discurso é um modo de transferência de localidades, de ampliação de minicírculos dentro do real.

O discurso existe como sistema: milhões de símbolos, cada um com estruturas próprias e relações normalizadas que permitem a apreensão do pensamento do outro. A manutenção dessas relações privilegia os círculos internos em detrimento do contacto com o externo.

### 21. F0113_A01_SEG_001

- score do perfil: 33.6519
- hints do perfil: ['apreensão', 'apreensao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'localidade', 'local', 'interioridade', 'apreender', 'modo humano', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'consc', 'local', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 53.2278

Toda a crítica é uma forma de apreensão pelo homem de qualquer coisa vinda de outro homem. É a apreensão, pelo eu, dos outros eus, daquilo que eles manifestam: pelas suas austeridades, pelas suas obras, pelos seus modos de ser.

A crítica é a colocação do modo de ser que é apreendido relativamente ao modo de ser que é verdadeiro. Porque o objeto da apreensão ocupa sempre uma posição relativamente ao que o incorpora: o real.

Cada atualização contém a relação interna, a relação com o campo de potencialidades, e a relação com outras atualizações. A obrigatoriedade de conceder passagem nasce quando outra atualização existe.

A consciência reflexiva, pela sua localidade, e pela capacidade de pensar o que pensa, o que o outro pensa, como ele é e como o outro é, impõe que o critério para qualquer coisa seja, antes de mais, o real.

### 22. F0241_A25_SEG_001

- score do perfil: 32.8206
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência', 'consciencia', 'consciência reflexiva', 'consciencia reflexiva', 'apreender', 'representar', 'modo humano', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'consc']
- anti_hints do perfil: []
- score global: 34.2351

Porque eu estou em casa, estou com os meus amigos, estou a jogar rugby, estou a passear no parque, estou com os meus filhos, estou no trabalho, estou já com a repetição dos modos de ser naquele contexto que já foi e que está a ser e que vai ser. Por que é que somos diferentes quando estamos com os nossos pais? Porque estamos a ser num contexto onde fomos quando éramos crianças. Por que é que às vezes se sente melhor estar ou em casa ou no trabalho, ou no trabalho ou em casa? Porque os modos de ser, as adequações às realidades apreensivas, do modo de ser na apreensão do real, existe dentro do contexto em que está inserido. E a consciência aqui entra como o meio entre a totalidade do que se é na apreensão do real. Na estrutura em que o ser vive, na estrutura da apreensão do real em que o ser vive, e não no real, a consciência serve como representação macrossimbólica daquilo que está a acontecer.

### 23. F0241_A05_SEG_002

- score do perfil: 32.8206
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência reflexiva', 'consciencia reflexiva', 'humano situado', 'apreender', 'representar', 'modo humano', 'situação humana', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'human']
- anti_hints do perfil: []
- score global: 30.6351

Quando se vê a diversidade da vida, a multiplicidade de variações em que, sei lá, veado tem aquelas coisas na cabeça, depois há um veado qualquer, não sei se é o iberico,ou é um qualquer, que já tem umas presas na boca, e como os gorilas têm umas presas enormes, mas não comem carne, e como não só a variedade, mas a vocação de cada ser, a capacidade de discrição, nem a capacidade, é o facto de ser na relação onde existe, nesta circularidade, mostra o próprio ontos, o próprio ontos da relação, das atualizações na relação, das atualizações relacional, nadas desrelacionáveis, em como cada animal tem o seu próprio nichozinho, em cada animal tem um campo limitado de potencialidade da sua própria atualização, como é óbvio, e que o ser humano opera na transversalidade de todos os nichos.

Na especificação de cada compartimentalização depois de cada nicho ao nível teórico, mas ao nível físico-biológico, opera no domínio de todos os nichos. Por isso, como é óbvio, não podia ser só carnívoro, nem podia ser só herbívoro, teria que ser ambos. Tinha que ser aquilo que abrangesse a totalidade.

Não quer dizer. Nós não temos presas, porque não lutamos com a boca. Não temos mãos esmagadoras, porque não temos de ter superioridade física. Porque quando a totalidade do ser abrange o ser e a potencialidade do ser, quando a potencialidade do ser é limitada, desculpe, então o ser tem um campo de movimentação também. E por isso os contactos nas relações, as graduações de força de contacto nas relações que medem o ser com ele próprio e com o real, nesta lógica de apreensão no ato senso, refletem isso mesmo. E o ser humano tem menos restrições de limitação de círculo pela capacidade de representar o real, todos os círculos.

### 24. F0241_A21_SEG_004

- score do perfil: 31.9206
- hints do perfil: ['apreensão', 'apreensao', 'representação', 'representacao', 'consciência reflexiva', 'consciencia reflexiva', 'ponto de vista', 'interioridade', 'apreender', 'representar', 'modo humano', 'consciência no real', 'consciencia no real']
- boost_terms do perfil: ['apree', 'repre', 'inter']
- anti_hints do perfil: ['coerência interna', 'coerencia interna']
- score global: 46.9314

A relação com o ser reflexivo tem no real, a espectador intervém, anda, fala, salta, viaja, fala, o que quiserem, qualquer coisa, qualquer coisa, qualquer coisa. É ela, é ela e nela, na relação que está, que teve, que vai ter, que está a ter, é nela que reside a ética, o valor, é nela que está inserido, porque é nela que está inserido o ser reflexivo.

Porque ena no modo de ser do ser reflexivo, que é um modo de ser que, antes de mais, apreende, pensa a si próprio, o que está a acontecer, apreende as suas regularidades, sempre, sempre, sempre com um ponto de vista, sempre com um ponto de vista contínuo, sempre com uma integração primária, primária não, básica, simples, do uso de símbolos grandes e largos, as próprias relações que os símbolos grandes e largos nas representações que fazem quando são manifestadas na própria apreensão real, concebe isso, não é? Concebe aquele modo de ser e o real que é apreendido. E essa mistura de símbolos diferentes na sua estrutura una naquilo que é, pode ser e deve ser que une o eu num próprio ponto de vista.

## Sample por perfil — Mediação, símbolo, linguagem e fechamento

### 1. F0026_SEG_001

- score do perfil: 40.3202
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'forma', 'formalismo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'fechamento sistémico', 'fechamento sistemico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'sistema de signos', 'representação simbólica', 'discurso formal']
- boost_terms do perfil: ['simbo', 'forma', 'formal']
- anti_hints do perfil: []
- score global: 46.9314

Kant tem razão ao extrair algumas verdades básicas do próprio sistema, errando no resto; Wittgenstein erra na extensão do jogo de palavras, pois não alcança o real. A questão do melhor modo de ser remete para a realidade: aquilo que existe e inclui as pessoas. A história fundamental é o progresso do desvelar da sofisticação do pensamento humano ao conhecer a realidade — o percurso das grandes ideias como aproximações sucessivas ao real. Tornar isso inteligível é necessário para que se torne crença; mas a inteligibilização é parca, porque depende da apreensão limitada que o inovador trouxe à luz ao simbolizar o real ainda não mapeado. É nesse intervalo — na apreensão da apreensão — que reside a importância da forma verdadeira e do risco da forma realmente falsa.

### 2. F0070_SEG_002

- score do perfil: 40.0197
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'linguagem', 'forma', 'formalismo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'fechamento sistémico', 'fechamento sistemico', 'validação interna', 'sistema de signos', 'representação simbólica', 'discurso formal']
- boost_terms do perfil: ['simbo', 'lingu', 'forma', 'formal']
- anti_hints do perfil: ['objetividade']
- score global: 60.5047

A validade de uma proposição não pode ser aferida por um sistema que o homem cria. Esse é um erro categorial. A validade depende exclusivamente do real. Contudo, a questão da validade de uma proposição só se coloca quando a proposição pretende operar no registo do verdadeiro ou do falso. Fora desse objetivo, a pergunta perde sentido.

Os sons que o homem produz dependem de vibrações no ar. Essas vibrações são, em número e variedade, muito superiores às vibrações que efetivamente acertam no real de forma verdadeira. Por mera lógica probabilística, é mais provável errar do que acertar. Se não fosse assim, todos viveriam como santos.

A linguagem, enquanto sistema vibratório e simbólico, tem sempre maior capacidade de produzir variações do que o real tem de as validar. A verdade não nasce da proliferação proposicional, mas da sua coincidência efetiva com o real.

### 3. F0108_A02_SEG_001

- score do perfil: 37.771
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'linguagem', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'fechamento sistémico', 'fechamento sistemico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'sistema de signos', 'representação simbólica', 'discurso formal']
- boost_terms do perfil: ['simbo', 'lingu']
- anti_hints do perfil: []
- score global: 62.7776

Daí a importância da língua. Se cada consciência é um mundo local, interessa saber quantos mundos existem e como se repartem as estruturas. O discurso é um modo de transferência de localidades, de ampliação de minicírculos dentro do real.

O discurso existe como sistema: milhões de símbolos, cada um com estruturas próprias e relações normalizadas que permitem a apreensão do pensamento do outro. A manutenção dessas relações privilegia os círculos internos em detrimento do contacto com o externo.

### 4. F0110_A01_SEG_003

- score do perfil: 35.7106
- hints do perfil: ['mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'mediações', 'mediacoes', 'representação simbólica']
- boost_terms do perfil: ['media', 'simbo']
- anti_hints do perfil: []
- score global: 55.7747

Dos filósofos que acompanham as ideias que ascendem da descoberta de que há algo: que eu faço, que eu durmo, que se vai tornando integrado pela quantidade ridiculamente gigante de campo apreensível. O eu quer, o eu vai fazer, integrar o eu.

Integrar o eu por necessário ser como eu–eu. No exterior está o que estaria para qualquer animal, mas é no interior que está o animal que, perante o mesmo real que os outros, apreende mais.

Não recebe apenas o mediado bruto da mediação puramente sensorial. Tem uma máquina biológica que filtra e uma biblioteca de símbolos criados pelo contínuo do ser, da ação humana.

Só nos podemos pensar porque temos símbolos. Nos animais vê-se por graduação diferente, mas o substrato está lá. Os símbolos são os portadores do que chamamos representação. São a relação com que o eu pode interagir.

### 5. F0107_SEG_003

- score do perfil: 35.3697
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'linguagem', 'forma', 'formalismo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'circuito interno', 'representação simbólica', 'discurso formal']
- boost_terms do perfil: ['simbo', 'lingu', 'forma', 'formal']
- anti_hints do perfil: []
- score global: 51.9386

Daí a facilidade com que se pensa a consciência como extra-real. Pensam-se relações como mini-realidades separadas. Mas qualquer criação ou inovação extra-círculo não é um círculo fora do círculo. É uma bolha que emerge do círculo, puxada pelo peso inteiro do próprio círculo.

Essa extra-localidade tem de se conter pelo círculo de onde emerge. O círculo integra a bolha, caracteriza-a simbolicamente segundo a sua linguagem, a sua lógica, o seu modo de ser.

O que a bolha fez — uma melhor descrição do real — é apreendido pelo círculo segundo a forma como o círculo a integra. Há um fio tradicional na apreensão do real. É isso que o filósofo faz, por necessidade do círculo maior.

### 6. F0108_A01_SEG_001

- score do perfil: 35.2202
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'forma', 'formalismo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'representação simbólica', 'discurso formal']
- boost_terms do perfil: ['simbo', 'forma', 'formal']
- anti_hints do perfil: []
- score global: 59.6278

A apreensão é o modo de significação das diferentes atualizações do ser. O símbolo é o enquadramento do real, o enquadramento daquilo que é. Pela própria estrutura da apreensão surgem interações entre o eu e o real, entre o eu e o eu, entre tudo isso.

Quando um símbolo representa um conceito maior — por exemplo, um 7 poder ser composto por 7 — isso decorre das diferenças dos tipos de apreensão, dos pontos de vista, dos constituintes, dos limites e dos círculos daquilo que está a atualizar. Dependendo do ponto de vista, pode-se ver um estágio que não é final, mas apenas o antecessor do seguinte.

O símbolo embarca o real conforme o ponto de vista, porque tem de incorporar estruturas lógicas necessárias. A lógica é a manutenção da inteligibilidade da relação eu–real. O real incorpora o eu, mas a lógica é a forma de explicitar isso de modo comum a todos os seres reflexivos.

Um símbolo é um conjunto. É uma representação que permite encontrar o comum entre as várias complexidades, pontos de vista e diferenças da apreensão do real. O comum não se refere à apreensão interna de cada um, mas àquilo que condiciona a própria apreensão.

O símbolo é quase uma tradução do real. Algo que pode ser apercebido. Mesmo com toda a liberdade do ser consciente, há algo comum a todos os seres reflexivos, e é por isso que é comum.

### 7. F0044_SEG_001

- score do perfil: 34.9197
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'linguagem', 'forma', 'formalismo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'circuito interno', 'representação simbólica', 'discurso formal']
- boost_terms do perfil: ['simbo', 'lingu', 'forma', 'formal']
- anti_hints do perfil: ['objetividade']
- score global: 62.5707

O discurso público não é naturalmente direcionado à realidade, porque a sua própria característica é ser limitado e autorreferencial: fala de si mesmo e dos eventos imediatos, usando as ferramentas que o constituem. Não pode haver enraizamento no real sem que o seu círculo se expanda, o que só seria possível se ideias verdadeiras fossem mais “pegajosas” do que as ideias de esquerda — algo que exigiria sacrifício e, por isso, tende a ser evitado. Alguns filósofos compreenderam a autorreferencialidade, mas fixaram-se nos símbolos da linguagem. A realidade contém objetos, alguns animados, e ver é a melhor forma de navegar; esperar que os animais percecionem o mundo sem representação é incoerente. A complexidade humana deriva da experiência adaptativa: o ser humano é o animal de todos os nichos. Ver melhor o mundo — representar o mundo no cérebro de forma cada vez mais sofisticada — é uma necessidade ontológica imposta pelas condições ambientais de florescimento. O descrever vem depois do ver; historicamente, primeiro surge o objeto. Ainda que respostas emocionais de primeira ordem, adequadas a círculos próximos, tenham valor adaptativo, a sua verdade assenta sempre na realidade, nem que seja pelo seu fundamento biológico.

### 8. F0241_A03_SEG_001

- score do perfil: 34.1601
- hints do perfil: ['mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'linguagem', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'mediações', 'mediacoes', 'representação simbólica']
- boost_terms do perfil: ['media', 'simbo', 'lingu']
- anti_hints do perfil: []
- score global: 64.6349

Por que é que as pessoas amadurecem? Por que é que se tornam adultas? Porque ultrapassam o processo de apreensão do real. Por que é que a escolaridade incide durante a juventude e não quando se é adulto? Por que é que é mais difícil aprender línguas quando se é adulto? Como é óbvio, porque o modo de apreensão do real está... é o dominante. Pois venha, pois venha a suavização, como é óbvio, pelo seu próprio.de vista no horizonte da apreensão, que é local, sempre, por isso é que é um horizonte. E isto é para dizer o quê? Para dizer que era para dizer... Ah, era isso. E depois, quando se já se tem a apreensão, não é? Quando já se tem o símbolo cristalizado, quando já se tem, sei lá, de qualquer maneira queremos olhar para isto, todas elas são meras descrições, parcas descrições, porque a descrição correta é ontológica. Portanto, quando a repetição de apreensões se tornou num modo de ser do processo do aprender, quando eu olhei muitas vezes para uma bola e agora eu já sei que é uma bola, não pela bola em si, não por eu em mim, mas pela relação que existe, que é expressada pela apreensão, pela mediação que incorpora tudo. Só que a mediação é restritiva, neste caso tudo incorpora tudo.

Essa destruição depois é custosa, é custosa, claro, como é óbvio. Nós já não estamos no modo de cristalização da apreensão, mas já entramos agora na necessária destruição dos modos de ser, para ser outros modos de ser. Então isto leva à banalidade de que é tudo aquilo que se foi há um segundo atrás, como é óbvio, mas leva-nos também à conclusão de que, operando o ser consciente reflexivo num quadro em que ele é livre e pode escolher ou não, o caminho que o leva à melhor descrição do real manifesta-se como, depois, modo de ser que mal descrevem o real. Portanto, até um ponto em que, por exemplo, vivem mais no eu eu.

A destruição é necessária. As atualizações que se sobrepõem nas relações em que o ser é levam sempre a destruições, podem não são destruições físicas, mas são destruições de tipos de relações, destruções de continuidades de relações, se esta relação se permanece neste estado, com estas características, com estas envolvências, e agora vem outra atualização malandra e está a impor-se, como qualquer coisa, como esta parede que não sai da minha frente, está bem? O braço vai-se partir se não for contra a parede. Há a destruição daquela continuidade daquela relação, que no fundo, em que no fundo o homem vive, na continuidade da relação anterior. Mas independentemente disso, a destruição é, quer dizer, faz parte, porque senão tudo seria como seria, cristalizado e imutável. Seria uma contradição nos próprios termos, o que sabemos não ser.

### 9. F0241_A14_SEG_003

- score do perfil: 30.8215
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'fechamento sistémico', 'fechamento sistemico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'sistema de signos', 'representação simbólica']
- boost_terms do perfil: ['simbo']
- anti_hints do perfil: []
- score global: 68.299

Daí a universalidade da religião, a necessidade de enquadramento da apreensão do real, do eu, do real no eu, essas coisas todas, a necessidade de enquadramento disso, no fundo da vida, daquilo que se está a viver, no círculo que o sequer possibilita, de modo a não exigir que se pense a vida de modo filosófico, verdadeiramente filosófico, porque isso seria não haver vida e impossível, porque altamente disfuncional, porque depois uma pessoa acaba por olhar para a relação do ser em cada interação e isso torna-se awkward. Mas obviamente que a resposta vai ser enquadrar no sistema o símbolo maior, pronto, o que quiser se chamar, o criador, o que se quiser chamar.

Depois, como é óbvio, esse símbolo vai ter o melhor ou pior descrição, claro, quanto mais ou menos afastada for do real. E quão mais afastada se torna do real, menos verdadeira se torna, e por isso vê-se que o porquê da morte de Deus. Não é porque se descobriu, não é porque a ciência levou a descrições mais verdadeiras, a um reenquadramento. Não, é por isso e porque o símbolo de Deus, que se foi fazendo de Deus, passou a estar em mais choque com as novas apreensões.

Claro que Deus morreu. Porque se foi descobrindo cada regularidade e isso foi entrando em choque com o símbolo anterior. E ao invés de procurar o melhor símbolo, procura-se a outra resposta também mais fácil de fazer, neste caso, que é dissolver. Dissolver o real e o eu, pela sua localidade e ponto de vista e perspectiva, passa a reenquadrar toda a apreensão.

### 10. F0104_A01_SEG_002

- score do perfil: 30.8215
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'fechamento sistémico', 'fechamento sistemico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'sistema de signos', 'representação simbólica']
- boost_terms do perfil: ['simbo']
- anti_hints do perfil: []
- score global: 65.9242

Se o modo de ser vive — não é, mas vive — e se o modo de ser consciente reflexivo vive pela apreensão como localidade, e se o modo de apreensão é simbólico, então estas ideias de que não precisamos de preencher as realidades com símbolos adequados não fazem sentido. O ser reflexivo tem sempre esta característica.

E tentar retirar essa dimensão ao ser reflexivo, descrevê-lo num sistema interno, para retirar o herói da equação, os arquétipos — todos os arquétipos que são descritivos são verdadeiros porque descrevem o real. Se não descrevem o real, então são sempre valorativos.

### 11. F0101_SEG_002

- score do perfil: 30.1202
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'forma', 'formalismo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'circuito interno', 'representação simbólica', 'discurso formal']
- boost_terms do perfil: ['simbo', 'forma', 'formal']
- anti_hints do perfil: []
- score global: 51.1635

A ciência é a descrição do real pelo processo, porque opera no físico, no apreensível. O discurso científico mistura-se com o discurso comum alargado, pois ambos operam no mesmo círculo. A distinção entre o académico, o eloquente e o corrente dissolve-se pela circulação do discurso científico, que é captado pelo discurso comum.

A ciência é representada no discurso, muitas vezes de forma incorreta, e como não descreve dever-ser, abre espaço à manutenção do mesmo tipo de ser valorativo, que vive no dever-ser porque o ser é conhecido intuitivamente pelos símbolos do real.

### 12. F0090_A01_SEG_003

- score do perfil: 29.9518
- hints do perfil: ['forma', 'formalismo', 'fechamento', 'fechamento simbólico', 'fechamento simbolico', 'fechamento sistémico', 'fechamento sistemico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'sistema de signos', 'discurso formal']
- boost_terms do perfil: ['fecha', 'forma', 'formal']
- anti_hints do perfil: []
- score global: 38.8374

A questão do melhor método de ensino é colocada como se fosse necessário conhecer todos os sistemas errados para se poder falar do correto, em vez de se afirmar a evidência tautológica: a criança sabe melhor se primeiro souber o que é isto que existe e o que é isto de eu existir.

Uma criança sem contacto com o real — que deveria ser dado pelo pai e pela mãe — sucumbirá a todos os modos de contacto dependentes apenas do eu. Cresce-se depois já deparado com uma compartimentalização definida com precisão terminológica, e pergunta-se como é que alguém não saberia nada.

O conhecimento humano é sempre compartimentalizado; não se pode querer fazer depender o real de respostas internas a domínios de conhecimento que nem sequer são tratados de forma integrada. Vê-se isso quando se discute Wittgenstein: as proposições fecham o discurso excluindo o real, e quando se tenta integrar o real diz-se que já é outra conversa.

### 13. F0241_A24_SEG_003

- score do perfil: 29.271
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'representação simbólica']
- boost_terms do perfil: ['simbo', 'coere']
- anti_hints do perfil: []
- score global: 74.3884

Estou a conduzir, tiro as mãos do volante, vou andar, sei lá, 70, 80 kmh, ou seja, 100, 120, 130, tiro as mãos do volante, o carro continua. E já não estou com a mão no volante a manter a relação na regularidade da direção do carro, digamos assim dizer. Estou a olhar em frente, estou a ver a estrada, estou a olhar para um carro e a estrada começa a fazer uma ligeira curva, ou faz uma ligeira curva, a minha mão, a minha mão, ainda que esteja pousada em cima da porta, junto ao vidro, dá um toque, logo. Faz parte da própria constituição do ponto de vista subjetivo, experiencial que está a ter.
o que existe, as relações que existem nesta multiplicidade de eventos que existem nesta experiência de estar durante cinco segundos sem as mãos no volante mostram que as relações que já lá estavam continuam a estar. Aquilo que se atualizou continua a atualizar-se, a velocidade, a direção, a posição do corpo, a atenção, a orientação, a direção, no fundo, o contínuo tem uma direção. Essa direção que já está construída vai continuar a relacionar-se, quer a consciência entre ou não. Pois ela relaciona-se com este manter da relação, este biologismo, se quisermos assim dizer, este vivismo, este acontecer da vida da sua própria definição, únicas, únicas verdadeiras, como é óbvio.
E também teria que ser assim, porque a consciência é somente a relação que advém de um eu reflexivo, que, como já sabemos, é dependentemente um contínuo atualizado localmente. E a consciência, meta-reflexividade, que quisermos, opera porque há já uma estabilização perfeitamente adequada ao real, no fundo, que poderíamos dizer à estabilização da apreensão do eu no real, e opera somente pela coerência que os símbolos compacta, que os símbolos proporcionam, pela adequação da coerência interna imagética ao real que se está a ver, que se está a ouvir, que se está a cheirar, essa correspondência é que permite o contínuo da relação sem intervenção da consciência.

### 14. F0241_A08_SEG_001

- score do perfil: 28.9106
- hints do perfil: ['mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica', 'fechamento sistémico', 'fechamento sistemico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'sistema de signos', 'mediações', 'mediacoes']
- boost_terms do perfil: ['media', 'coere']
- anti_hints do perfil: []
- score global: 72.5311

A moralidade, aquilo que, se sendo esse, bem sendo aquilo que melhor se situa no contínuo da localidade, assim é que é, no contínuo da localidade, em que se pode sequer colocar a questão de bem, somente quando do real advém um ser reflexivo. Só aí, porque o ser está a refletir sobre a realidade que o contém em si mesmo. O ser está a viver na mediação da apreensão e da realidade. Está a viver nessa relação. 
Relação de quê? Sempre de entre a apreensão e a realidade, a apreensão que inculta do estado interior, whatever, e a realidade. E quanto melhor for a apreensão depois a descrição do que o ser faz na realidade onde vive, melhor se vai posicionar no meio de todas as relações. Não é preciso recorrer a Deus para saber que num sistema relacional há aquilo que preserva e edifica a realidade, o conjunto de atualizações, e aquilo que destrói.

Mas o homem faz coisas tão más, é tão mauzão. Olha o Hitler. Claro. Hitler e qualquer outro massacre, qualquer outra guerra, que não falta por aí são guerras. Aquela foi com uma dimensão ridícula, mas ao.de extermínio. Mas outros extermínios também existiram, ainda que com dimensões menores. Mas independentemente da catástrofe, dizer como é que é possível... Nós sabemos como é que é possível. O homem faz, o homem tem comportamentos não bons para com outros seres. Até comportamentos ativamente destrutivos, impeditivos de florescer, vai ser mau. Se o sistema onde ele estiver inserido, onde ele viver, o sistema em que ele operar, o sistema em que ele apreender e descrever e agir, for um que justifica as ações que se mantêm independentemente de ser bom ou mau. Como o critério não está no real, o critério está no proprio sistema. Saber e fazer com que o outro, com estatuto ontológico igual a ele, que o contínuo das suas atualizações vai terminar, vai deixar de existir, vai deixar de estar enquadrado no potencial do ser, é justificado pela coerência interna de qualquer sistema, o homem  crê ser tão mau como o que for o por si apreendido como o homem que se é e num sistema de homens assim, ser assim nao ha de estar mal. Quanto menos gravosos forem, mais fácil de manter a coerência do sistema pela estabilizaçao dos utros homens no sistema. Quanto mais, mais intrincada vai ser, porque sempre afastado do real, no sistema da quebra com o real custa a posterior apreensao do real e nao da apreensao é custosa.

Ah, mas o teu critério é tão, é tão como vale tanto como outro qualquer outro critério. Vale, vale tanto? Como é que medes esse tanto? Ah, há de ser pela... Pois, amigo, há de ser pela adequação à realidade, adequação ao real. Mesmo no teu cenário fofo de possibilidade de algo ser somente porque há mais uma opção que, em abstrato, se poderia incluir nesse campo de possibilidades, é somente aprender mal o campo de possibilidades. Não é mais do que outra coisa. É aprender mal e descrever mal o ser, o poder e o dever ser.

### 15. F0030_SEG_001

- score do perfil: 28.0598
- hints do perfil: ['mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica', 'forma', 'formalismo', 'fechamento sistémico', 'fechamento sistemico', 'sistema de signos', 'mediações', 'mediacoes', 'discurso formal']
- boost_terms do perfil: ['media', 'forma', 'formal']
- anti_hints do perfil: []
- score global: 38.4672

É mais ao contrário: trata-se de evidenciar a evidência do sistema com mais um exemplo, neste caso o direito, que independentemente do que se creia ser, é-o em todas as sociedades. Se a verdade não fosse a busca, mesmo que implícita, não haveria direito. E não só a ordem jurídica: a ordem moral e social também são manifestações da verdade. O homem órfão tende a preferir a forma da estrutura à estrutura real; esquece-se da realidade e passa a viver no sistema que as ordens criaram, ofuscando-a e desintelectualizando-a de modo pretensamente intelectual. O mal existe precisamente porque, na liberdade de ser, se escolhe não ser livre. Como dizia Soljenítsin, algo nesse sentido. Não é óbvio que uma figura como Trump seja adorada por milhões? Num sistema de adoração da forma, basta alguém dizer uma verdade para ser visto como profeta — mesmo sendo formalmente repugnante. A apreensão mediata é preenchida pela forma, ficando silenciosa a dúvida — não requerida — sobre a verdade do real. Quando o sistema se intrinca sobre si mesmo e relega o real, nada como apontar uma luz ao real para que esse apontar crie a forma da verdade.

### 16. F0086_SEG_001

- score do perfil: 27.9702
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'forma', 'formalismo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'representação simbólica', 'discurso formal']
- boost_terms do perfil: ['simbo', 'forma', 'formal']
- anti_hints do perfil: ['objetividade']
- score global: 34.8672

Sabe-se hoje tanto sobre o mundo, sobre o pormenor das regularidades do modo de ser — que é a única coisa que permite um contínuo com estruturas complexas — que esse mesmo conhecimento difunde e dificulta a ligação entre a apreensão natural do homem e símbolos simples, curtos, gramaticalmente leves, que abarquem a realidade de forma inteligível.

A falha não está no modo de ser, que é o que é, mas na falta de conceitos simples que expliquem o mundo. Não preciso de saber matemática nem refazer o caminho de Einstein para perceber que objetos com massa têm energia e que distorcem o espaço por existirem.

### 17. F0213_SEG_001

- score do perfil: 27.6135
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'representação simbólica', 'discurso formal']
- boost_terms do perfil: ['simbo']
- anti_hints do perfil: []
- score global: 46.0952

O relativismo, o não considerar o real, destrói o símbolo, introduz mais além do que é suposto o símbolo conter, daí a confusão, o erro, pq todo discurso se torna sobre o que se acha que o símbolo é porque até o símbolo está sujeito a interpretação, como qualquer contemporaneanismo subjetivo e como qualquer clássico discurso sem real. O modo de apreensão e de discurso contém símbolos abertos a discussão, relega se a estrutura, a imitação para a matemática, e coloca se a potencialidade, pex., em símbolo de ilimitado pq tudo pode ser , sei lá se há fantasmas - não filósofo -, ou tudo pode ser consciência,  - pretenso filósofo, - o erro é transversal - faz se da filosofia a tristeza que hoje é,.  no confronto com o tipo de apreensão e discurso os símbolos encontram os seus limites, sem limites sem conteúdo, sem palavra sequer, gugu da da água, e quero dizer fogo, vou me afogar

### 18. F0241_A02_SEG_002

- score do perfil: 27.4215
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'fechamento sistémico', 'fechamento sistemico', 'circuito interno', 'sistema de signos', 'representação simbólica', 'discurso formal']
- boost_terms do perfil: ['simbo']
- anti_hints do perfil: []
- score global: 53.5383

E a amplitude em que isto se vê de um lado e do outro na relação a ser mantida entre o ser reflexivo e os outros seres reflexivos, e depois o discurso, ou seja, os símbolos comuns que identificam discursos, e ver esta dinâmica depois também relativamente ao que cada ser consciente pensa sobre si, sobre o que se pensa sobre o ser, ou seja, aquilo que se diz sobre o que é isto, e depois, como é óbvio, o que deveria ser isto, que é o plano onde somente se opera, e ver a extensão das relações em como, depois, no que se manifesta, é sempre na criação de sistemas, qualquer modo e círculo de operação entre cada ser consciente contendo todas estas características, operam assim. E quão mais justificações se criam para cada proposição, normalmente é necessária quanto mais afastado do real cada proposição se dirigir.

E pode tentar viverá? Não! Porque isto da necessidade, qual necessidade? Porque se as condições atómicas fossem diferentes, então isto tudo isto podia ser diferente, está bem? Está certo, amigo? Está certo? Está certo? E aí a minha descrição estaria errada, porque, ao descrever o que isto é, ao descrever o real, estaria a descrever outra coisa que não aquilo que é. Mas, para descrever aquilo que poderia ter sido, e já há texto suficiente, o que sequer é descrever aquilo que é, e daquilo que é resulta a necessidade de sequer ser.

### 19. F0241_A23_SEG_001

- score do perfil: 25.871
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'coerência interna', 'coerencia interna', 'representação simbólica']
- boost_terms do perfil: ['simbo', 'coere']
- anti_hints do perfil: []
- score global: 57.4599

pelo facto de se ser homem, uma estrutura biológica que apreende, que vive na apreensão do real, que não vive, ou seja, em que o eu funciona não naquilo que o real é, mas na própria estrutura lógica do ser reflexivo que apreende o real, na adequação do real à realidade, na repetição da experiência apreensiva para se poder ter sequer uma estrutura que permita um símbolo onde o eu possa viver, isso apenas me diz que o que é, é algo que apreende o real e, na própria lógica evolutiva e da simples agregação da permanência de ser que os organismos biológicos têm, então, se o que o organismo faz é bem apreender o real para bem viver, de certo modo, ou somente viver, não poderia ser de outro modo, a reflexividade não poderia acontecer de outro modo que não fosse pela automatização da própria experiência para não se ter que se ter a dedicar cada momento à própria experiência. E quando a experiência fica automatizada, o que sobra é simplesmente a coerência. E é na coerência que pode brotar algo como reflexividade.

Empurrar para auto relação é trocar o auto por eu, para no fim dizer que o que diferencia é a perspetiva, que é o mesmo que dizer local, nem poderia ser de outro modo pá sem limite nem haveria reflexividade. Pelo que disse antes

Claro, o eu não pode ser extra-real, tem de ser sempre local, e só da localidade é que poderia nascer a reflexividade.

### 20. F0241_A20_SEG_004

- score do perfil: 25.7215
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'representação simbólica']
- boost_terms do perfil: ['simbo']
- anti_hints do perfil: []
- score global: 59.6964

as definições no sentido da descrição completa do símbolo que se está a descrever. Se está a descrever sobre liberdade, então, na definição, tem de conter aquilo que é de facto a liberdade, que é somente o reflexo da reflexividade na ação, as possibilidades no campo das potencialidades de um ser reflexivo que existe localmente nesse campo, que interage com o campo na sua extensão, que amplia e que desfaz e que molda e que restringe, dependendo da apreensão relativamente ao real, que incluindo ele próprio, claro. É a descrição de todas as compartimentalizações daquilo de que se está a falar, que envolve, para além de tudo, envolve o homem.

### 21. F0097_A02_SEG_001

- score do perfil: 25.7215
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'representação simbólica']
- boost_terms do perfil: ['simbo']
- anti_hints do perfil: []
- score global: 53.4

A filosofia é a atividade do ser humano na sua relação com o real. Não faz sentido aspirar à verdade sem o real como termo da ação. A apreensão é contínua com o movimento do ser. Separar a consciência como algo que opera “por cima” do real é antirreal, fantasioso.

Os símbolos ontológicos — ser, não-ser, eu — são funcionais. São apreendidos por relação, não pela coisa em si. A apreensão é sempre tardia relativamente à atualização do real. As representações referem-se sempre ao real, ainda que internas.

### 22. F0241_A21_SEG_004

- score do perfil: 25.7215
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'representação simbólica']
- boost_terms do perfil: ['simbo']
- anti_hints do perfil: []
- score global: 46.9314

A relação com o ser reflexivo tem no real, a espectador intervém, anda, fala, salta, viaja, fala, o que quiserem, qualquer coisa, qualquer coisa, qualquer coisa. É ela, é ela e nela, na relação que está, que teve, que vai ter, que está a ter, é nela que reside a ética, o valor, é nela que está inserido, porque é nela que está inserido o ser reflexivo.

Porque ena no modo de ser do ser reflexivo, que é um modo de ser que, antes de mais, apreende, pensa a si próprio, o que está a acontecer, apreende as suas regularidades, sempre, sempre, sempre com um ponto de vista, sempre com um ponto de vista contínuo, sempre com uma integração primária, primária não, básica, simples, do uso de símbolos grandes e largos, as próprias relações que os símbolos grandes e largos nas representações que fazem quando são manifestadas na própria apreensão real, concebe isso, não é? Concebe aquele modo de ser e o real que é apreendido. E essa mistura de símbolos diferentes na sua estrutura una naquilo que é, pode ser e deve ser que une o eu num próprio ponto de vista.

### 23. F0202_SEG_001

- score do perfil: 25.5531
- hints do perfil: ['mediação', 'mediacao', 'mediação simbólica', 'mediacao simbolica', 'fechamento sistémico', 'fechamento sistemico', 'coerência interna', 'coerencia interna', 'circuito interno', 'validação interna', 'sistema de signos', 'mediações', 'mediacoes']
- boost_terms do perfil: ['media']
- anti_hints do perfil: []
- score global: 64.6599

as sociedades democraticas europeias - e tmb nos usa embora o pensamento base seja eu no real, ao contrrio das europeia - afetam os recursos tirados a seres conscientes reflexivos, com grande amplitude de justificaçoes internas para o fazer, ainda que se gaste mais do que se arrecada, ainda que a mao do estado chegue a todos os cantos de um sitio ondem vivem seres conscientes reflexivos e onde atualize , o faça sempre pior do que se fosse qualquer outro sistema que quisesse permancer e que teria sempre um alinhamento com o real, com que quem o constituisse vive o problema , as possibilidades e alogo a melhor solucao, visse portanto o ser, o poder ser e o dever ser. o aumento do de vida - as barreiras levantadas ao ser reflexivo, à sua liberdadena exploração do real por imposiçao do homem e nao por qq outra questao, travestidas de uma qq proposiçao valorativa de finalidade, que há tantas, porque tem de ser assim porque devia ser assim, - hum ta, devia ser assim se for e puder ser assim, mas claro que nao é isto que é custoso nadar contra a maré - e vive se assim com um estado que arrecada dinheiro e que preenche o espaço comum, eleito mediante critérios de onde mais gastar, para voltar a ser eleito, até que se comece a desviar o real e modificar tal sistema, adeuqando-o ao real, ainda que se calhar pior do que sem ele, porque na analise do mal do sitema anterior tmb reside a parca descriçao, e acaba se a nem perceber o antes de ser e o porque da mudança, ha somente o que se apreende e o que cre dever ser, numa expansao dos modos de ser à expressão do pulso da sociedade, no ritma das respostas adquadas para o circulo proximo do ser reflexivo mas erradas nas relaçoes extra eu, em que o outro nao tocavel tem de ser equacionado

### 24. F0241_A22_SEG_004

- score do perfil: 25.505
- hints do perfil: ['mediação simbólica', 'mediacao simbolica', 'símbolo', 'simbolo', 'simbólico', 'simbolico', 'fechamento simbólico', 'fechamento simbolico', 'coerência interna', 'coerencia interna', 'representação simbólica']
- boost_terms do perfil: ['simbo', 'coere']
- anti_hints do perfil: ['objetividade']
- score global: 54.8491

quando se olha para aquilo que se é, esse um ser reflexivo, que é um animal, pois que seres reflexivos, cumprindo os critérios, podem ser não sendo animais, mas aquilo que se conhece que é, é um ser reflexivo que a sua animalidade lhe permite ter a característica de refletir sobre ele próprio, enquadrar-se no seu ponto de vista, ver-se na sua continuidade, na apresentação meticulosa e representada simbolicamente, na sua adequação necessária para se poder sequer andar, sem tropeçar, para que permita o foco, para que permita que o foco seja o único objeto da integração, pois tudo o resto está enraizado na sua animalidade que todos os animais têm. A coerência é o que permite, e não a multiplicidade, e não a sermentes todos.

## Sample por perfil — Substituição do real, erro categorial e erro de escala

### 1. F0111_A01_SEG_004

- score do perfil: 29.8096
- hints do perfil: ['substituição do real', 'substituicao do real', 'erro de escala', 'mistura de escalas', 'troca de critério', 'sistema substitui o real', 'critério autónomo', 'criterio autonomo', 'validade interna', 'fecho interno', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real', 'formalismo desligado do real']
- boost_terms do perfil: ['escala']
- anti_hints do perfil: []
- score global: 37.2607

As manifestações em larga escala operam no quadro do processo. O que é bom, o que deve ser, o que não deve ser, quando desligado do real, passa a ser apenas ligação interna: interna, interna. Procura respostas nas regras do próprio círculo.

Assim, o bem e o mal deixam de estar no ato e passam a estar no processo. Torna-se então necessário integrar o eu. O critério deixa de ser aquilo que é e passa a ser aquilo que o sistema impõe que seja.

### 2. F0035_SEG_001

- score do perfil: 29.271
- hints do perfil: ['erro categorial', 'erro de escala', 'troca de critério', 'critério autónomo', 'criterio autonomo', 'validade interna', 'fecho interno', 'autonomização', 'autonomizacao', 'o sistema manda', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: ['catego', 'autono']
- anti_hints do perfil: []
- score global: 64.4601

Há proposições de maior e menor relevância conforme a sua aplicabilidade à base conceptual dos modos de ser concorrentes nesta realidade. Distingue-se entre proposições de circunscrição individual, com efeitos limitados, e proposições de amplitude alargada, cujos efeitos se propagam pelos círculos mais individuais. São dois tipos de proposições ontologicamente distintos. É nestes modos de ser que a vida se opera, onde emerge a complexidade das entidades conscientes e das suas relações. Em círculos maiores, esta contenda agrega-se. Reconhece-se que há verdade na utilidade do modo de ser de esquerda em contextos próximos, como relações familiares, mas esse modo é inadequado — por qualquer critério verdadeiro — para círculos nacionais, transnacionais ou supranacionais, tratando-se de um erro categorial. A ponte entre o ser, o poder-ser e o dever-ser não é a mesma em todos os planos. Apelos sentimentais são inadequados para relações entre Estados. Isto abrange análise, respostas, proposições, propostas de ação e implementação prática: trata-se de modos de exteriorização do ser. Esta verdade decorre da auto-evidência do sistema: sendo seres conscientes e sociais, operamos necessariamente em dois caminhos fundamentais — o da procura ou o do resguardo. Não há mais; as multiplicidades internas derivam desta divisão fundamental.

### 3. F0241_A08_SEG_001

- score do perfil: 25.7215
- hints do perfil: ['substituição do real', 'substituicao do real', 'troca de critério', 'sistema substitui o real', 'critério autónomo', 'criterio autonomo', 'validade interna', 'fecho interno', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: ['coere']
- anti_hints do perfil: []
- score global: 72.5311

A moralidade, aquilo que, se sendo esse, bem sendo aquilo que melhor se situa no contínuo da localidade, assim é que é, no contínuo da localidade, em que se pode sequer colocar a questão de bem, somente quando do real advém um ser reflexivo. Só aí, porque o ser está a refletir sobre a realidade que o contém em si mesmo. O ser está a viver na mediação da apreensão e da realidade. Está a viver nessa relação. 
Relação de quê? Sempre de entre a apreensão e a realidade, a apreensão que inculta do estado interior, whatever, e a realidade. E quanto melhor for a apreensão depois a descrição do que o ser faz na realidade onde vive, melhor se vai posicionar no meio de todas as relações. Não é preciso recorrer a Deus para saber que num sistema relacional há aquilo que preserva e edifica a realidade, o conjunto de atualizações, e aquilo que destrói.

Mas o homem faz coisas tão más, é tão mauzão. Olha o Hitler. Claro. Hitler e qualquer outro massacre, qualquer outra guerra, que não falta por aí são guerras. Aquela foi com uma dimensão ridícula, mas ao.de extermínio. Mas outros extermínios também existiram, ainda que com dimensões menores. Mas independentemente da catástrofe, dizer como é que é possível... Nós sabemos como é que é possível. O homem faz, o homem tem comportamentos não bons para com outros seres. Até comportamentos ativamente destrutivos, impeditivos de florescer, vai ser mau. Se o sistema onde ele estiver inserido, onde ele viver, o sistema em que ele operar, o sistema em que ele apreender e descrever e agir, for um que justifica as ações que se mantêm independentemente de ser bom ou mau. Como o critério não está no real, o critério está no proprio sistema. Saber e fazer com que o outro, com estatuto ontológico igual a ele, que o contínuo das suas atualizações vai terminar, vai deixar de existir, vai deixar de estar enquadrado no potencial do ser, é justificado pela coerência interna de qualquer sistema, o homem  crê ser tão mau como o que for o por si apreendido como o homem que se é e num sistema de homens assim, ser assim nao ha de estar mal. Quanto menos gravosos forem, mais fácil de manter a coerência do sistema pela estabilizaçao dos utros homens no sistema. Quanto mais, mais intrincada vai ser, porque sempre afastado do real, no sistema da quebra com o real custa a posterior apreensao do real e nao da apreensao é custosa.

Ah, mas o teu critério é tão, é tão como vale tanto como outro qualquer outro critério. Vale, vale tanto? Como é que medes esse tanto? Ah, há de ser pela... Pois, amigo, há de ser pela adequação à realidade, adequação ao real. Mesmo no teu cenário fofo de possibilidade de algo ser somente porque há mais uma opção que, em abstrato, se poderia incluir nesse campo de possibilidades, é somente aprender mal o campo de possibilidades. Não é mais do que outra coisa. É aprender mal e descrever mal o ser, o poder e o dever ser.

### 4. F0070_SEG_002

- score do perfil: 25.7215
- hints do perfil: ['substituição do real', 'substituicao do real', 'erro categorial', 'erro de escala', 'forma substitui o real', 'sistema substitui o real', 'validade interna', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real', 'formalismo desligado do real']
- boost_terms do perfil: ['catego']
- anti_hints do perfil: []
- score global: 60.5047

A validade de uma proposição não pode ser aferida por um sistema que o homem cria. Esse é um erro categorial. A validade depende exclusivamente do real. Contudo, a questão da validade de uma proposição só se coloca quando a proposição pretende operar no registo do verdadeiro ou do falso. Fora desse objetivo, a pergunta perde sentido.

Os sons que o homem produz dependem de vibrações no ar. Essas vibrações são, em número e variedade, muito superiores às vibrações que efetivamente acertam no real de forma verdadeira. Por mera lógica probabilística, é mais provável errar do que acertar. Se não fosse assim, todos viveriam como santos.

A linguagem, enquanto sistema vibratório e simbólico, tem sempre maior capacidade de produzir variações do que o real tem de as validar. A verdade não nasce da proliferação proposicional, mas da sua coincidência efetiva com o real.

### 5. F0241_A18_SEG_002

- score do perfil: 25.7215
- hints do perfil: ['substituição do real', 'substituicao do real', 'troca de critério', 'sistema substitui o real', 'critério autónomo', 'criterio autonomo', 'validade interna', 'fecho interno', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: ['coere']
- anti_hints do perfil: []
- score global: 40.842

O homem faz, o homem tem comportamentos não bons para com outros seres. Até comportamentos ativamente destrutivos, impeditivos de florescer, vai ser mau. Se o sistema onde ele estiver inserido, onde ele viver, o sistema em que ele operar, o sistema em que ele aprender e descrever e agir, é um que justifica as ações que se marrem, independentemente de ser bom ou mau. Comcritério não está no real, o critério não está nele próprio.

Saber que o outro, com estatuto ontológico igual a ele, que o contínuo das suas atualizações vai terminar, vai deixar de existir, vai deixar de estar enquadrado no potencial do ser, é justificado pela coerência interna de qualquer sistema. Quanto menos gravosos forem usados, mais fácil de manter a coerência do sistema. Quanto menos, mais intrincada vai ser, porque sempre afastado do real.

### 6. F0241_A07_SEG_002

- score do perfil: 24.0215
- hints do perfil: ['substituição do real', 'substituicao do real', 'sistema substitui o real', 'validade interna', 'fecho interno', 'projeção', 'projecao', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: ['projec']
- anti_hints do perfil: []
- score global: 49.3062

O socialismo pode ser descrito de maneira ontológica, um sistema de crenças que depois se torna modo de ser, em que a relação eu-real é muito fraca, em que o plano do dever ser é sobreposto a qualquer plano do ser e do poder ser, especialmente do poder ser. É no plano da apreensão do real e do discurso sobre essa apreensão do real, é autojustificativo nos seus próprios termos.

Há um grau de projeção diferente, há prioridades diferentes do campo da relação que eu tenho comigo próprio e da relação que eu tenho com o real e com o real comigo próprio. O real é secundário na relação de mim comigo próprio, toda a sua apreensão interior, quase sem tocar o cortado fora.

Esquecemo-nos que o que eu sou, claro, é também o real, mas aí, consumido pela própria estrutura interna de responsabilidade, ela consegue manifestar-se no real, consegue atualizar-se a consciência pela quantidade de representações que tem pelos caminhos neurológicos dos neurónios pelo corpo inteiro que têm sobre a instância em que se está a operar no real, a apreensão é isto também, integra isto. Então, quando há essa quase possibilidade mesmo real de viver na apreensão do real, então já se vive no mundo do eu, no eu-eu e não no mundo do eu-real.

Começando a caminhada sobre a pergunta que é isto de viver bem e operar somente numa teoria qualquer, num quadro lógico qualquer, não fazê-lo operar no real. A norma é eu-eu, mas nesse eu-eu é igual, mas existe mais. As tuas regras de verificabilidade estão limitadas. Existe mais. Estão falsas. Há uma...

### 7. F0241_A23_SEG_001

- score do perfil: 23.9601
- hints do perfil: ['substituição do real', 'substituicao do real', 'troca de critério', 'troca de regime', 'autonomização', 'autonomizacao', 'coerência sem real', 'critério sem real']
- boost_terms do perfil: ['autono', 'coere', 'troca']
- anti_hints do perfil: []
- score global: 57.4599

pelo facto de se ser homem, uma estrutura biológica que apreende, que vive na apreensão do real, que não vive, ou seja, em que o eu funciona não naquilo que o real é, mas na própria estrutura lógica do ser reflexivo que apreende o real, na adequação do real à realidade, na repetição da experiência apreensiva para se poder ter sequer uma estrutura que permita um símbolo onde o eu possa viver, isso apenas me diz que o que é, é algo que apreende o real e, na própria lógica evolutiva e da simples agregação da permanência de ser que os organismos biológicos têm, então, se o que o organismo faz é bem apreender o real para bem viver, de certo modo, ou somente viver, não poderia ser de outro modo, a reflexividade não poderia acontecer de outro modo que não fosse pela automatização da própria experiência para não se ter que se ter a dedicar cada momento à própria experiência. E quando a experiência fica automatizada, o que sobra é simplesmente a coerência. E é na coerência que pode brotar algo como reflexividade.

Empurrar para auto relação é trocar o auto por eu, para no fim dizer que o que diferencia é a perspetiva, que é o mesmo que dizer local, nem poderia ser de outro modo pá sem limite nem haveria reflexividade. Pelo que disse antes

Claro, o eu não pode ser extra-real, tem de ser sempre local, e só da localidade é que poderia nascer a reflexividade.

### 8. F0202_SEG_001

- score do perfil: 22.364
- hints do perfil: ['substituição do real', 'substituicao do real', 'troca de critério', 'sistema substitui o real', 'critério autónomo', 'criterio autonomo', 'validade interna', 'fecho interno', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: []
- anti_hints do perfil: []
- score global: 64.6599

as sociedades democraticas europeias - e tmb nos usa embora o pensamento base seja eu no real, ao contrrio das europeia - afetam os recursos tirados a seres conscientes reflexivos, com grande amplitude de justificaçoes internas para o fazer, ainda que se gaste mais do que se arrecada, ainda que a mao do estado chegue a todos os cantos de um sitio ondem vivem seres conscientes reflexivos e onde atualize , o faça sempre pior do que se fosse qualquer outro sistema que quisesse permancer e que teria sempre um alinhamento com o real, com que quem o constituisse vive o problema , as possibilidades e alogo a melhor solucao, visse portanto o ser, o poder ser e o dever ser. o aumento do de vida - as barreiras levantadas ao ser reflexivo, à sua liberdadena exploração do real por imposiçao do homem e nao por qq outra questao, travestidas de uma qq proposiçao valorativa de finalidade, que há tantas, porque tem de ser assim porque devia ser assim, - hum ta, devia ser assim se for e puder ser assim, mas claro que nao é isto que é custoso nadar contra a maré - e vive se assim com um estado que arrecada dinheiro e que preenche o espaço comum, eleito mediante critérios de onde mais gastar, para voltar a ser eleito, até que se comece a desviar o real e modificar tal sistema, adeuqando-o ao real, ainda que se calhar pior do que sem ele, porque na analise do mal do sitema anterior tmb reside a parca descriçao, e acaba se a nem perceber o antes de ser e o porque da mudança, ha somente o que se apreende e o que cre dever ser, numa expansao dos modos de ser à expressão do pulso da sociedade, no ritma das respostas adquadas para o circulo proximo do ser reflexivo mas erradas nas relaçoes extra eu, em que o outro nao tocavel tem de ser equacionado

### 9. F0104_A02_SEG_001

- score do perfil: 22.364
- hints do perfil: ['substituição do real', 'substituicao do real', 'troca de critério', 'sistema substitui o real', 'critério autónomo', 'criterio autonomo', 'validade interna', 'fecho interno', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: []
- anti_hints do perfil: []
- score global: 37.4098

Quanto mais um tipo de discurso tem o seu campo de aplicação centrado no eu, menos toca no real. E todos os critérios inventados nesses sistemas serão sempre internos, porque relegam o real.

As medidas prescritivas estão erradas quando são só eu-centradas. Mas aspirar ao contrário, a só real, destruiria a relação humana, que é sempre eu com eu.

### 10. F0032_SEG_001

- score do perfil: 22.3215
- hints do perfil: ['substituição do real', 'substituicao do real', 'erro categorial', 'forma substitui o real', 'sistema substitui o real', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real', 'formalismo desligado do real']
- boost_terms do perfil: ['catego']
- anti_hints do perfil: []
- score global: 26.4029

O discurso público, sobretudo dos setores com capacidade de o propagar, é por natureza formal. A sua utilidade e a sua justificação ontológica residem na procura do melhor modo de ser dentro da forma, e não na procura do melhor modo de ser pela busca da verdade. Sendo isto um facto, a consequência lógica é a preservação do modo de ser formal: defender instituições e usá-las como meios de imposição de crenças, pela sua abrangência e durabilidade. Em última instância, só há duas posições: conhecer a realidade ou não conhecer a realidade. Daqui resulta a proliferação de um modo de ser em detrimento do outro, com impactos que se tornam insustentáveis. Ao nível concreto, por exemplo na violência política, afirma-se formalmente que toda a violência é condenável, mas imputam-se sistematicamente atributos geradores de violência apenas a um dos lados. Essas categorias são nomes — palavras — usadas para posicionar e opor modos de ser. Assim, a defesa da forma e do sistema reduz-se à gestão de rótulos. O outro polo, orientado para o real, procura revelar algo que é real, ainda que à custa do eu. O combate a essa posição faz-se pela ocupação do espaço comunicacional; a alternativa é iluminar a capacidade de propagar, com a mesma naturalidade, crenças realistas do eu-real.

### 11. F0241_A04_SEG_001

- score do perfil: 22.172
- hints do perfil: ['substituição do real', 'substituicao do real', 'troca de critério', 'sistema substitui o real', 'critério autónomo', 'criterio autonomo', 'validade interna', 'fecho interno', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: []
- anti_hints do perfil: []
- score global: 65.9242

2 + 2 igual a 4 funciona como sua própria justificação, mas ainda se pode ir a elementos mais básicos, mais profundos, aos elementos axiomáticos de um sistema, e depois diz-se que ah, não, não há, porque a derivação é infinita. Claro, claro. Claro que sim, como é óbvio. Porque a domização de 2 + 2 ser 4 não é aquilo que compõe o 2 e o 2 e o 4 que faz com que seja verdade, mas é o facto de o 2 e o 2 serem 4, essa relação que existe, continuar a permanecer no contínuo da existência dentro do sistema que diz que 2 + 2 é 4, existe, é real, representa a realidade.

porque pende para encontrar as... pende não, faz parte, não é? Encontra-se as justificações, os axiomas, os fundamentos de uma qualquer proposição apenas em dois lados. São os únicos lados possíveis assim que algo existe, ou seja, assim que há. E esses dois lados são ou naquilo que há, na realidade, naquilo que é, ou então pela localidade de todos os seres reflexivos, é pela perspectiva em que está inserido e é por essa imposição de derivação do eu para o real que a comparação entre qualquer tipo de critério ou a justaposição entre qualquer tipo de critério dentro do quadro da apreensão do real pelo eu é no eu que reside a base, é no eu que reside o quadro lógico. Portanto, é normal, seja em um eu, é normal. Não assim assim tinha sido descoberta assim que o homem começou a pensar, não foi assim. É uma luta constante na apreensão, na boa apreensão do real, que obriga, como é óbvio, também à descrição do real. A apreensão por si só é pouca se não houver descrição energética, descrição ou representação, não houver representação, a representação não pode ser algo muito interno e descrição contém um interno e um externo, na relação entre o que existe.

### 12. F0097_A02_SEG_002

- score do perfil: 20.8135
- hints do perfil: ['substituição do real', 'substituicao do real', 'erro categorial', 'erro de escala', 'forma substitui o real', 'validade interna', 'fecho interno', 'coerência sem real', 'critério sem real', 'formalismo desligado do real']
- boost_terms do perfil: ['catego']
- anti_hints do perfil: []
- score global: 48.1595

A epistemologia de Kant não tem implicações ontológicas; quando bem descrita, confirma-as. O afastamento do real explica-se pelo modo de apreensão individual e gera formas cada vez mais distantes do real, como certas psicologias que deslocam o eu para uma esfera fantasmagórica.

O panpsiquismo é isto ao quadrado. O eu é um arranjo de atualizações estruturais com mecanismos de manutenção. Cortem-me e vejam: há células, não há universos internos. Cada localidade que me compõe é atualização de potencialidades dessa localidade. A consciência não absorve o real; é uma atualização local dele. Qualquer filosofia que faça o contrário é erro categorial.

### 13. F0073_SEG_001

- score do perfil: 20.8135
- hints do perfil: ['substituição do real', 'substituicao do real', 'forma substitui o real', 'validade interna', 'fecho interno', 'absolutização', 'absolutizacao', 'coerência sem real', 'critério sem real', 'formalismo desligado do real']
- boost_terms do perfil: ['absolu']
- anti_hints do perfil: []
- score global: 47.7314

A questão colocada por Thomas Nagel em “What Is It Like to Be a Bat?” interroga a relevância do ponto de vista subjetivo e se este obriga à separação ontológica da consciência. O argumento funda-se na impossibilidade de aceder ao “como é” de outra criatura, sugerindo uma interioridade inacessível ao real objetivo.

Contudo, o facto de um morcego — ou qualquer outro animal — ser capaz de representação não obriga à conclusão de que a consciência seja uma interioridade separada do real. Pelo contrário, essa capacidade aponta para a consciência como expressão das condições reais em que o ser opera.

A dificuldade apontada por Nagel resulta de absolutizar o ponto de vista como fronteira ontológica, em vez de o compreender como limitação condicional da apreensão. A consciência não está fora do real; é uma forma altamente complexa de relação com o real, condicionada pelo corpo, pelo meio e pelas possibilidades do ser.

### 14. F0180_SEG_001

- score do perfil: 20.8135
- hints do perfil: ['substituição do real', 'substituicao do real', 'sistema substitui o real', 'absolutização', 'absolutizacao', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: ['absolu']
- anti_hints do perfil: []
- score global: 44.3636

E o querer, só que a esquerda embate numa questão que é por querer, por ser no ser, viver nas, em todas as contingências possíveis e absolutas, em todas as viver no círculo da apreensão do ser excluindo o real, ou tendo em muito pouca conta o real, tende a tornar-se dominante porque a relação, porque todos apreendemos através de uma relação do tipo local eu para o real, vivendo no sistema de apreensão entre o eu sensor e o real, sendo aí que se inclui o ser, o dever ser, o valor.

### 15. F0090_A01_SEG_003

- score do perfil: 20.664
- hints do perfil: ['substituição do real', 'substituicao do real', 'forma substitui o real', 'sistema substitui o real', 'validade interna', 'fecho interno', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real', 'formalismo desligado do real']
- boost_terms do perfil: []
- anti_hints do perfil: []
- score global: 38.8374

A questão do melhor método de ensino é colocada como se fosse necessário conhecer todos os sistemas errados para se poder falar do correto, em vez de se afirmar a evidência tautológica: a criança sabe melhor se primeiro souber o que é isto que existe e o que é isto de eu existir.

Uma criança sem contacto com o real — que deveria ser dado pelo pai e pela mãe — sucumbirá a todos os modos de contacto dependentes apenas do eu. Cresce-se depois já deparado com uma compartimentalização definida com precisão terminológica, e pergunta-se como é que alguém não saberia nada.

O conhecimento humano é sempre compartimentalizado; não se pode querer fazer depender o real de respostas internas a domínios de conhecimento que nem sequer são tratados de forma integrada. Vê-se isso quando se discute Wittgenstein: as proposições fecham o discurso excluindo o real, e quando se tenta integrar o real diz-se que já é outra conversa.

### 16. F0026_SEG_001

- score do perfil: 20.472
- hints do perfil: ['substituição do real', 'substituicao do real', 'forma substitui o real', 'sistema substitui o real', 'validade interna', 'fecho interno', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real', 'formalismo desligado do real']
- boost_terms do perfil: []
- anti_hints do perfil: []
- score global: 46.9314

Kant tem razão ao extrair algumas verdades básicas do próprio sistema, errando no resto; Wittgenstein erra na extensão do jogo de palavras, pois não alcança o real. A questão do melhor modo de ser remete para a realidade: aquilo que existe e inclui as pessoas. A história fundamental é o progresso do desvelar da sofisticação do pensamento humano ao conhecer a realidade — o percurso das grandes ideias como aproximações sucessivas ao real. Tornar isso inteligível é necessário para que se torne crença; mas a inteligibilização é parca, porque depende da apreensão limitada que o inovador trouxe à luz ao simbolizar o real ainda não mapeado. É nesse intervalo — na apreensão da apreensão — que reside a importância da forma verdadeira e do risco da forma realmente falsa.

### 17. F0089_SEG_002

- score do perfil: 20.2611
- hints do perfil: ['substituição do real', 'substituicao do real', 'troca de critério', 'troca de regime', 'sistema substitui o real', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: ['troca']
- anti_hints do perfil: []
- score global: 27.6029

Por isso se chama leis às leis civilísticas. Depois, como é óbvio, tudo se quer abranger e tudo se chama lei, mas as leis civilísticas e as leis físicas são, no fundo, leis: descrições das regularidades dos modos de ser.

Um dos modos de ser do homem é comprar e vender, trocar, dar e receber, mutuar, emprestar. Isto é verdade desde o Código Civil napoleónico e continuará a ser verdade em todos os sistemas que preservem a liberdade e a dignidade. O sinalagma perfeito destas relações jurídicas traduz a correspondência do real com a liberdade e a dignidade.

Como poderia ser de outro modo? Se há paridade ontológica entre as pessoas que compõem uma sociedade, então há regularidade nos modos de ser entre modos de ser iguais. As posições filosóficas opostas teriam de aceitar, pela sua própria lógica, que não existissem arquétipos nem modos de ser estáveis.

### 18. F0094_A01_SEG_003

- score do perfil: 19.6096
- hints do perfil: ['substituição do real', 'substituicao do real', 'erro de escala', 'mistura de escalas', 'sistema substitui o real', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: ['escala']
- anti_hints do perfil: []
- score global: 37.2607

De onde não resultam prescrições? As prescrições são necessárias pelo próprio sistema: descrições do modo como qualquer ser reflexivo existe. Qualquer ser reflexivo vive nesta dualidade, pela sua própria estrutura. As sociedades, sendo feitas de pessoas, ampliam isto à escala macro.

A questão final é sempre: qual o modo de ser a adotar? Melhor dizendo, qual o melhor modo de ser que cada um deve adotar? Qualquer um que queira — sabendo que os modos contrários ao real serão piores por qualquer métrica. A única métrica objetiva é a correspondência com o real.

### 19. F0117_A01_SEG_003

- score do perfil: 19.6096
- hints do perfil: ['substituição do real', 'substituicao do real', 'erro de escala', 'mistura de escalas', 'sistema substitui o real', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: ['escala']
- anti_hints do perfil: []
- score global: 31.8286

O ser no ser é parco pela parca descrição.  
O ser no poder-ser é o verdadeiro processo ontológico pela apreensão do ser no contínuo do real.  
O ser no dever-ser é viver na descrição limitada do ser e não no poder-ser.

A verdadeira aprendizagem é a que coloca o ser no poder-ser. Viver nas potencialidades conduz às atualizações.

Hoje, em larga escala, o poder-ser é postergado. Ao homem cabe apenas caminhar no contínuo traçado pela engenharia dos sistemas que ele próprio cria. O poder-ser desaparece, fica a apreensão limitada e o mero desejo.

### 20. F0241_A01_SEG_002

- score do perfil: 19.1135
- hints do perfil: ['substituição do real', 'substituicao do real', 'erro categorial', 'forma substitui o real', 'validade interna', 'fecho interno', 'coerência sem real', 'critério sem real', 'formalismo desligado do real']
- boost_terms do perfil: ['catego']
- anti_hints do perfil: []
- score global: 45.2422

a educação é repetição pela apreensão do real, no real, como qualquer coisa, aprender qualquer coisa, confrontando-se com o real na sua repetição. Então, todas as tentativas de adaptar as palavras e o próprio método de aprendizagem para que não depois, depois, quando se for adulto, não, não, depois, quando se for não sei quê, aí sim, é que se trata do problema da sua forma mais técnica. Como mais técnica? Devia ser mais verdadeira e o ser mais verdadeiro percorre desde que se é bebé e se diz as coisas mais verdadeiras sem complexizar a frase.

Isto aqui é uma garrafa vermelha, digo só, garrafa e aponto. Não interessa, não interessa. Tenta-se fazer da especificidade técnica algo só atingível a certas categorias, como se fosse possível, como se fosse possível comparar isso com o real dizendo-se, não, para aprender bem o real, isso depois vais perceber, para aprender bem o real tem que se compreender isto, tem que aprender isto, tem que aprender isto, não tem que aprender isto, tem que aprender esta matemática, tem que aprender esta língua qualquer, deste autor, tem que... Como assim? Quais são as abordagens para o real? Quando é que se vai aprender? Quando não se estiver repetido ainda sobre o que se está a aprender?

### 21. F0103_A01_SEG_003

- score do perfil: 18.9215
- hints do perfil: ['substituição do real', 'substituicao do real', 'forma substitui o real', 'sistema substitui o real', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: ['substi']
- anti_hints do perfil: []
- score global: 26.4029

É por isso que andamos todos na escola a aprender coisas. Porque vivemos deste modo, em que temos de aprender temazinhos para depois conseguir aplicar. Porque nada faz sentido diretamente. Nada toca no real.

Se o real pudesse ser conhecido pela própria apreensão do real, não seriam precisos vinte anos de escola.

A matemática, a ciência, são substitutos da descrição do real. Operam pela lógica do próprio sistema, não pela apreensão do real.

### 22. F0113_A01_SEG_001

- score do perfil: 18.772
- hints do perfil: ['substituição do real', 'substituicao do real', 'troca de critério', 'forma substitui o real', 'critério autónomo', 'criterio autonomo', 'validade interna', 'fecho interno', 'coerência sem real', 'critério sem real', 'formalismo desligado do real']
- boost_terms do perfil: []
- anti_hints do perfil: []
- score global: 53.2278

Toda a crítica é uma forma de apreensão pelo homem de qualquer coisa vinda de outro homem. É a apreensão, pelo eu, dos outros eus, daquilo que eles manifestam: pelas suas austeridades, pelas suas obras, pelos seus modos de ser.

A crítica é a colocação do modo de ser que é apreendido relativamente ao modo de ser que é verdadeiro. Porque o objeto da apreensão ocupa sempre uma posição relativamente ao que o incorpora: o real.

Cada atualização contém a relação interna, a relação com o campo de potencialidades, e a relação com outras atualizações. A obrigatoriedade de conceder passagem nasce quando outra atualização existe.

A consciência reflexiva, pela sua localidade, e pela capacidade de pensar o que pensa, o que o outro pensa, como ele é e como o outro é, impõe que o critério para qualquer coisa seja, antes de mais, o real.

### 23. F0241_A10_SEG_001

- score do perfil: 18.772
- hints do perfil: ['substituição do real', 'substituicao do real', 'erro categorial', 'erro de escala', 'troca de critério', 'critério autónomo', 'criterio autonomo', 'validade interna', 'fecho interno', 'coerência sem real', 'critério sem real']
- boost_terms do perfil: []
- anti_hints do perfil: []
- score global: 49.5959

Estava a pensar no caminho da contradição... da contradição não, quer dizer, sim, é uma contradição, mas é apenas no caminho que o verdadeiro e o bom são, por necessidade, o resultado da melhor descrição e da melhor ação, da melhor apreensão no sentido de... em relação com o real, quão bem se é no real, relativamente ao real. E estava a pensar no ser que apreende e que vive na estrutura da apreensão, vive na apreensão e revela o real. Em tudo isso, como em tudo isso e todos os exemplos que têm dado, tudo tem falado, vai de uma ponta à outra. E na correção, estava a pensar na correção, mas a correção não é bem... não há nenhuma correção, há apenas o apontar para o caminho real, para o caminho bom, para o caminho verdadeiro.

O erro é somente o desvio, e daí o sentido de continuar, porque o erro não é uma quebra. O erro não é algo separado. O erro é somente a apreensão de um modo de ser que não inclui o real quando o poderia incluir, sabendo que o que se é normalmente é-se, o que se é naturalmente é-se, pela necessária relação da apreensão com o eu e com o real no eu, pela localidade do ponto de vista.

Tanto que qualquer produção, qualquer valor, qualquer, em cada das coisas, quaisquer direções que se inscrevam, que se manifestem no real, que se encarnem no real, quaisquer modos de ser, modos de ser que sendo são justificados somente por um critério interior, muito raramente intocável pelo real, e no outro que, ao incluir o real como pressuposto de tudo, impõe-se, permite-se na correção, e é na correção porquê? Pelo real, pelo que apreende.

### 24. F0241_A13_SEG_002

- score do perfil: 17.264
- hints do perfil: ['substituição do real', 'substituicao do real', 'sistema substitui o real', 'validade interna', 'fecho interno', 'o sistema manda', 'coerência sem real', 'sistema autónomo', 'sistema autonomo', 'critério sem real']
- boost_terms do perfil: []
- anti_hints do perfil: []
- score global: 37.0993

E aí o walkismo, qualquer política do sistema, contrária à política social, qualquer política que quer encarnar, a querer descobrir o melhor sistema, as melhores regras dentro do sistema, impor as limitações que se creem ser necessárias por causa do sistema, olhar para o Estado e querer ver nele a solução, porque o Estado é a instituição, o sistema em que vivemos, a ordem internacional, o suprasistema. Qualquer coisa, qualquer coisa. Vê-se como isso é andar no eu e não andar no real, vê-se como isso é andar na apreensão do real e não no real, que é a normalidade e por isso é que se vê os fenómenos que se vêem, por isso é que qualquer política relativista, modernista, neomodernista, qualquer coisa, qualquer coisa.

Por isso é que cada uma dessas políticas que não apreendem o real, não sabem descrever o real, querem acabar com o real, acabar com qualquer estrutura familiar, com qualquer estrutura local, qualquer estrutura biológica, as estruturas ontológicas, ou seja, aquilo que existe não existe, o que existe é apenas o sistema e depois como o eu se deveria conformar ao sistema. Claro que se vai focar depois, como se foca, mas tem vindo a focar, claro que se vai focar no indivíduo, na individualidade de cada um, no subjetivismo de cada um. Claro, porque se tudo o resto não existe, a única relação que existe é do próprio indivíduo com o sistema.

Claro que é para desintegrar a família, claro que é para desintegrar as regularidades do ser. Claro que sim, claro que sim. É todo um espectro, um espectro em que vai se apontando para aquilo que melhor encaixa dentro do sistema.
