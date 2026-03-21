1. Diagnóstico do estado da árvore

Diagnóstico: B — incompleta. Não está concluída porque faltam ainda convergências e relações explícitas, embora a árvore já tenha fragmentos, microlinhas, ramos, percursos e argumentos gerados e validados. As microlinhas estão suficientemente consistentes para uso estrutural, mas ainda granulares: são 194, das quais 70 unitárias. Os ramos também estão consistentes, mas mostram fragmentação excessiva: são 67, dos quais 34 unitários. A continuidade microlinha → ramo → percurso → argumento existe formalmente, mas ainda não fecha bem no topo: há 23 ramos sem percurso e 32 ramos sem argumento.

Isto significa que a árvore não está bloqueada, mas também não está saturada. Há ainda ganho estrutural relevante a obter; só que esse ganho já não está sobretudo em voltar atrás para mexer nas microlinhas, nem em continuar a acrescentar camadas novas por cima. O ganho dominante está em limpar o encaixe superior da árvore.

2. Principal fragilidade estrutural

A fragilidade dominante não é a mera ausência de convergências. É outra: o acoplamento ramo → argumento ainda está mal estabilizado. A validação da camada de argumentos reporta 24 avisos de plausibilidade, e o README sintetiza o problema como heurística demasiado permissiva, com associações heterogéneas ou fracas. Além disso, ficaram 37 argumentos sem ramos associados e 32 ramos sem argumento, o que mostra simultaneamente dispersão e cobertura incompleta.

Dito de forma mais seca: a árvore já sobe até argumentos, mas a camada argumentativa ainda não está a selecionar nem a discriminar bem o que cada ramo realmente sustenta.

3. Próximo passo necessário

O próximo passo necessário é: rever associações a argumentos.

4. Justificação da inevitabilidade

Isto é inevitável por quatro razões. Primeiro, microlinhas e ramos já estão em estado de utilização prudente: têm avisos, mas não falhas estruturais, e os próprios relatórios tratam-nos como camadas utilizáveis. Segundo, a camada de percursos, embora ainda incompleta, está mais limpa do que a de argumentos: há 44 ramos com percurso, contra 35 com argumento, e o relatório de percursos limita-se a avisos de cobertura, enquanto o de argumentos acrescenta avisos qualitativos de plausibilidade. Terceiro, gerar convergências agora seria fazer convergir material ainda semanticamente ruidoso. Quarto, gerar relações explícitas agora cristalizaria uma semântica associativa que o próprio estado atual ainda considera permissiva.

Por isso, entre as opções possíveis, não escolheria “consolidar microlinhas” nem “consolidar ramos” como passo dominante. Esses seriam passos de melhoria local. O passo inevitável é o que resolve o gargalo real da continuidade estrutural no topo.

5. Efeito esperado após execução

Depois de rever as associações a argumentos, o efeito esperado é este: a árvore passa a ter um topo menos inflacionado, menos heterogéneo e mais seletivo, com menos argumentos por ramo quando a evidência é fraca, menos associações espúrias e uma correspondência mais confiável entre ramos e argumentos. Só aí a geração de convergências deixará de ser prematura e passará a ser estruturalmente sensata.

Em fórmula curta: a árvore v1 já existe, mas ainda não fechou; o que falta não é mais agregação de base, é rigor no encaixe argumentativo do topo.

1. Diagnóstico do bloqueio atual

O bloqueio superior da árvore não está principalmente na falta de cobertura. Está numa combinação assimétrica de fatores, mas com um centro muito claro:

Os percursos estão relativamente estáveis e restritivos.
Tens 67 ramos, dos quais 44 ficaram associados a percurso e 23 ficaram sem percurso; mais importante: foram geradas 44 associações ramo→percurso, ou seja, na prática a camada de percursos fechou com um encaixe dominante por ramo associado, sem inflação relevante. Isto é um sinal de contenção estrutural, não de desordem. (relatorio_validacao_ramos_v1.txt, relatorio_validacao_percursos_v1.txt, relatorio_geracao_percursos_v1.txt)

Os argumentos é que estão a degradar o fecho.
Tens 35 ramos com pelo menos um argumento, 32 sem argumento, 37 argumentos sem ramos, e foram geradas 93 associações ramo→argumento. Isto significa que, nos ramos que sobem a argumento, a média é de cerca de 2,66 argumentos por ramo associado, o que é demasiado alto para uma camada que devia já estar a funcionar como fecho seletivo. (relatorio_validacao_argumentos_v1.txt, relatorio_geracao_argumentos_v1.txt)

O problema decisivo não é só cobertura insuficiente; é permissividade semântica excessiva.
A validação dos argumentos regista 24 avisos de plausibilidade, com repetição do mesmo padrão: heterogeneidade excessiva e, em pelo menos um caso, associação fraca por poucos sinais independentes. Isto mostra que o sistema atual tende a aceitar vários argumentos compatíveis em vez de discriminar o argumento dominante. (relatorio_validacao_argumentos_v1.txt)

A granularidade dos ramos pesa, mas não é o centro do bloqueio.
Há 34 ramos unitários em 67, o que confirma prudência e alguma fragmentação. Mas a validação dos ramos diz que eles estão estruturalmente consistentes; portanto, a granularidade é um fator de contexto, não o núcleo da falha atual. (relatorio_validacao_ramos_v1.txt, 01_README.md)

O diagnóstico, portanto, é este: o fecho superior está a falhar mais por excesso de admissibilidade no ramo→argumento do que por insuficiência do ramo→percurso.

2. Método dominante de fecho

O método dominante deve ser:

fecho por ordem sequencial, executado sob regra de restrição semântica.

Se eu tiver de escolher um método da tua lista, escolho o (5) fecho por ordem sequencial. Mas a sua forma correta não é neutra: tem de ser uma sequência restritiva, não de cobertura.

Porquê este método e não outro?

Porque, no estado atual, a dependência material já está desenhada assim:

o ramo→percurso é mais estável, mais parcimonioso e menos inflacionado;

o ramo→argumento já usa, no próprio gerador, o percurso do ramo como um dos sinais de associação;

logo, o argumento depende semanticamente do percurso, mas o percurso não depende do argumento. (gerar_percursos_v1.py, gerar_argumentos_v1.py)

Isto torna errado fechar tudo ao mesmo tempo ou começar pelo argumento. O fecho correto é:

primeiro estabilizar a subida do ramo ao percurso, e só depois permitir a subida do ramo ao argumento.

Não escolho “fecho por cobertura”, porque isso só mascararia o problema.
Não escolho “consolidação intermédia” como método dominante, porque os ramos ainda não estão num estado que justifique uma refusão global desta camada.
Não escolho “revisão semântica dos critérios” como método principal autónomo, porque ela é necessária, mas dentro da sequência correta, não no lugar dela.

3. Ordem correta de execução

A ordem correta é esta:

Primeiro: rever ramos

Mas não rever todos os ramos em massa. Rever apenas os ramos que, pela sua forma atual, impedem decisão superior fiável.
Isto significa: ramos unitários ou muito instáveis só quando a sua forma local torna impossível decidir se sobem, a que percurso sobem, ou se estão internamente misturados.

Ou seja: aqui não há consolidação geral; há apenas triagem dos ramos patologicamente ambíguos.

Depois: rever associações ramo→percurso

Isto vem a seguir porque é a primeira subida estrutural real da zona superior.
Aqui o objetivo não é maximizar cobertura, mas fixar o percurso dominante de cada ramo que tenha encaixe suficiente, aceitando que alguns fiquem sem percurso.

Depois: rever percursos

Só residualmente.
Os percursos são importados e a sua estrutura valida; o que pode precisar de revisão não é tanto o percurso em si, mas o diagnóstico de:

percursos estruturalmente demasiado vazios;

percursos demasiado genéricos;

percursos que estejam a funcionar como “caixa de restos”.

Mas isto vem depois da revisão das associações, não antes.

Depois: rever associações ramo→argumento

Só aqui.
Porque o argumento já é um fecho mais abstrato e depende de o ramo já estar razoavelmente estabilizado no seu percurso.
É nesta operação que tens de introduzir a maior restrição.

Por fim: rever argumentos

Também residualmente.
Os argumentos são importados; o problema atual não é principalmente o objeto “argumento”, mas a sua sobreassociação.
Portanto, a revisão dos argumentos vem no fim, para distinguir entre:

argumentos legitimamente ainda sem ramos;

argumentos demasiado abstratos para a árvore atual;

argumentos que só ganharão corpo mais tarde, já noutra fase.

Dependência correta:
ramo claro → percurso estabilizado → argumento seletivamente atribuído

Não ao contrário.

4. Critério central de associação

O critério dominante nesta fase deve ser:

função estrutural.

Não proximidade temática.
Não cobertura máxima.
Nem sequer afinidade semântica em abstrato.

O que deve mandar é isto:

O ramo deve ser associado ao percurso e ao argumento que melhor exprimem a função estrutural dominante que ele desempenha na árvore.

Em termos materiais, isso quer dizer:

que passo(s)-alvo o ramo realmente densifica;

que problema dominante trabalha;

que trabalho no sistema realiza;

em que regime conceptual/operativo está;

e, no caso dos argumentos, se a subida preserva o mesmo regime em vez de o deslocar artificialmente.

A proximidade lexical ou temática pode servir como sinal de entrada, mas não pode mandar.
O que manda é: o que este ramo está a fazer aqui?

Se o percurso ou argumento candidato não responde claramente a essa pergunta, a associação não deve ser feita.

Portanto, o critério central não é “parece relacionado”.
É: descreve de forma estruturalmente necessária o papel dominante do ramo?

5. Regra para casos ambíguos

Aqui a regra deve ser dura.

Quando um ramo parece encaixar em vários argumentos

Escolhe um argumento dominante.
Só admite um segundo se houver evidência independente adicional e se esse segundo argumento estiver no mesmo regime estrutural do primeiro.

Se os candidatos divergem em:

parte,

nivel_de_operacao,

tipo_de_necessidade,

conceito_alvo,

isso não é riqueza; isso é precisamente o padrão de heterogeneidade excessiva que o relatório já está a assinalar.
Nesses casos, corta.

Quando um ramo não encaixa claramente em nenhum argumento

Aceita que fique sem argumento.

Se tiver percurso estável, pode ficar fechado provisoriamente em percurso.
Se nem percurso tiver, então o ramo ainda não ganhou massa estrutural suficiente para subir.
Não se deve forçar a subida só para aumentar cobertura.

Quando um argumento parece demasiado abstrato para os ramos existentes

Deixa-o sem ramos associados.

Um argumento vazio nesta fase não é necessariamente defeito; pode ser apenas uma estrutura de referência ainda não instanciada pela árvore atual.
O erro seria puxar ramos para cima só para “preencher” o argumento.

Quando um percurso cobre parcialmente um ramo, mas não totalmente

Pergunta qual é a função dominante do ramo.

Se o percurso cobre essa função dominante, a associação pode manter-se.
Se cobre apenas uma face secundária do ramo, a associação deve cair.

Só em casos raros a cobertura parcial justifica rever o próprio ramo. E mesmo aí, só se a parcialidade revelar que o ramo está de facto a misturar duas funções estruturais distintas.

A regra geral é:

na dúvida, não subir.

6. Efeito esperado na árvore

Se aplicares este método, o efeito esperado é muito claro:

Menos associações, mas mais fiáveis.

A camada de percursos quase não sofrerá inflação adicional, porque já está relativamente contida.

A camada de argumentos ficará bastante mais limpa, com menos triplas artificiais por ramo.

Os ramos sem argumento deixarão de ser “falhas escondidas” e passarão a ser informação estrutural real: ou ainda não sobem, ou sobem só a percurso.

Os argumentos sem ramos deixarão de parecer ruído e passarão a ser reserva estrutural não ativada.

A árvore ficará muito mais bem preparada para a fase seguinte, porque as futuras convergências já não serão construídas sobre encaixes frouxos.

Em suma: o topo da árvore ficará menos cheio, mas muito mais verdadeiro.

7. Risco do método alternativo que não deve ser escolhido

O método que não deve ser escolhido é o fecho por cobertura.

Esse método produziria um falso ganho de completude, mas com três custos graves:

inflacionaria a camada de argumentos, que já está inflacionada;

apagaria a diferença entre encaixe forte e encaixe fraco;

contaminaria a fase seguinte, porque as convergências passariam a ser feitas a partir de associações semanticamente frouxas.

E isto não é um risco teórico. Já está a aparecer agora:
a camada de percursos gera 44 associações para 44 ramos associados;
a camada de argumentos gera 93 associações para 35 ramos associados;
e a validação já acusa 24 avisos de plausibilidade. (relatorio_geracao_percursos_v1.txt, relatorio_geracao_argumentos_v1.txt, relatorio_validacao_argumentos_v1.txt)

Portanto, o método a rejeitar é exatamente aquele que tentaria “resolver” os 32 ramos sem argumento e os 37 argumentos sem ramos por enchimento artificial.

A formulação mais curta do meu juízo é esta:

O fecho correto desta zona superior não é cobrir mais; é ordenar melhor a subida.
Primeiro fixa-se o percurso dominante do ramo; só depois se autoriza a sua subida argumentativa; e, em caso de dúvida, aceita-se a incompletude.

Baseei-me em: 01_README.md, relatorio_validacao_ramos_v1.txt, relatorio_validacao_percursos_v1.txt, relatorio_validacao_argumentos_v1.txt, relatorio_geracao_percursos_v1.txt, relatorio_geracao_argumentos_v1.txt, gerar_percursos_v1.py e gerar_argumentos_v1.py.