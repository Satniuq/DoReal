README OPERACIONAL — Continuidade do fecho canónico do mapa dedutivo
1. Onde estou neste momento

Estou na fase de fecho canónico do mapa dedutivo.

Isto significa que:

o mapa já foi reconstruído;

os corredores críticos já foram isolados;

o orquestrador já correu;

já existe um ficheiro intermédio com decisões candidatas;

já existem prompts enviados e respostas do modelo por corredor e por passo.

Nesta fase não devo voltar a pedir análise global do projeto.

Também não devo voltar a pedir uma nova arquitetura geral do sistema.

O trabalho agora é apenas este:

rever decisões intermédias;

corrigir passos fracos;

decidir subpassos;

arbitrar corredores;

consolidar o mapa final.

2. Pasta e ficheiros de trabalho desta fase

A pasta operacional atual é:

C:\Users\JoseVitorinoQuintas\DoReal\14_mapa_dedutivo\02_fecho_canonico_mapa

Ficheiros principais já existentes nesta pasta

manifesto_fecho_canonico.json

orquestrador_fecho_canonico_api.py

read_me_fecho_canonico.md

Pastas principais já existentes

prompts\

prompts_enviados\

respostas_modelo\

outputs\

logs\

Output intermédio principal já gerado

outputs\decisoes_canonicas_intermedias.json

Este ficheiro é agora o centro do trabalho.

3. Regra principal desta fase

A regra principal é esta:

não gerar tudo de novo; trabalhar apenas por revisão localizada.

Ou seja:

não repetir o orquestrador sem necessidade;

não pedir novos ficheiros grandes antes de rever os atuais;

não consolidar antes de arbitrar os corredores;

não reabrir o projeto inteiro.

4. Ordem obrigatória de trabalho

A ordem correta é esta:

Fase 1 — rever corredor P33_P37

Primeiro corredor a rever.

Fase 2 — rever corredor P25_P30

Segundo corredor.

Fase 3 — rever corredor P42_P48

Terceiro corredor.

Fase 4 — rever P50

Último fecho crítico.

Fase 5 — só depois consolidar

Só quando os corredores estiverem aceitáveis.

5. Cadência operacional exata

A cadência correta é esta:

Passo 1 — abrir o output intermédio

Abrir:

outputs\decisoes_canonicas_intermedias.json

Objetivo:

verificar o que saiu para cada passo;

perceber que campos estão bons;

perceber que campos ficaram fracos ou vagos.

Passo 2 — abrir os ficheiros do primeiro corredor

Abrir primeiro só estes:

respostas_modelo\P33_P37\passo_nuclear__P33.json
respostas_modelo\P33_P37\passo_nuclear__P34.json
respostas_modelo\P33_P37\passo_nuclear__P35.json
respostas_modelo\P33_P37\passo_nuclear__P36.json
respostas_modelo\P33_P37\passo_nuclear__P37.json

e, se necessário:

respostas_modelo\P33_P37\subpasso_mediacional__P33_SP01.json
respostas_modelo\P33_P37\subpasso_mediacional__P36_SP01.json
respostas_modelo\P33_P37\arbitragem_corredor__P33_P37.json

Passo 3 — classificar cada passo

Para cada passo, decidir:

bom

aceitável mas fraco

insuficiente

precisa de subpasso

precisa de nova arbitragem

Passo 4 — usar prompts de correção localizada

Só repromptar o que ficou fraco.

Passo 5 — arbitrar o corredor

Depois de corrigidos os passos desse corredor, fazer arbitragem do corredor.

Passo 6 — atualizar manualmente o output intermédio

Incorporar as correções em:

outputs\decisoes_canonicas_intermedias.json

Passo 7 — repetir para o corredor seguinte
Passo 8 — só no fim correr o consolidador

Só quando tudo estiver aceitável.

6. Critério de revisão de cada passo

Para cada passo, devo verificar se existem e se estão bons estes campos:

formulacao_v2_final

justificacao_expandida_final

ponte_entrada

ponte_saida

porque_o_anterior_nao_basta

porque_nao_pode_ser_suprimido

objecao_letal

bloqueio_curto

objecoes_bloqueadas_final

fragmentos_selecionados_finais

decisão sobre subpasso

validação estrutural mínima

Se um passo falhar em formulação, mediação ou justificação, deve ser revisto.

7. Fluxo prático quando eu retomar isto

Quando voltar a pegar nisto, devo fazer exatamente esta sequência:

7.1

Abrir:

outputs\decisoes_canonicas_intermedias.json

respostas_modelo\P33_P37\*.json

7.2

Começar por P33.

7.3

Usar prompts de revisão local apenas para os passos que ficaram fracos.

7.4

Depois de P33–P37 estar aceitável, passar para P25–P30.

7.5

Depois P42–P48.

7.6

Depois P50.

7.7

Só depois correr o consolidador final.

8. Prompts prontos a usar
Prompt A — revisão localizada de um passo

Usar quando um passo saiu fraco.

Não quero análise global do projeto.

Quero rever apenas o passo [PXX] do corredor [CORREDOR], com base apenas em:
- matriz_inevitabilidades_v4.json
- mapa_dedutivo_precanonico_v4.json
- relatorio_fecho_canonico_v4.json
- dossier_corredor_[CORREDOR].json
- decisão intermédia atual do passo [PXX]

Tarefa:
reescrever apenas os seguintes campos:
- formulacao_v2_final
- justificacao_expandida_final
- ponte_entrada
- ponte_saida
- porque_o_anterior_nao_basta
- porque_nao_pode_ser_suprimido
- objecao_letal
- bloqueio_curto

Critérios:
- formulação curta, técnica e dedutiva;
- sem texto meta-editorial;
- sem repetir o passo anterior;
- sem conceitos externos ao sistema;
- explicitar a mediação se houver salto.

Entrega apenas JSON válido para o passo [PXX].
Prompt B — decisão sobre subpasso mediacional

Usar quando o passo parece não fechar sozinho.

Não quero análise global do projeto.

Quero decidir apenas se o passo [PXX] exige subpasso mediacional.

Base:
- matriz_inevitabilidades_v4.json
- mapa_dedutivo_precanonico_v4.json
- dossier_corredor_[CORREDOR].json
- decisão intermédia atual do passo [PXX]

Responde apenas em JSON com:
- step_id
- precisa_subpasso
- justificacao_decisao
- subpasso_id
- formulacao_subpasso
- posicao_na_cadeia
- funcao_dedutiva
- porque_sem_ele_o_passo_salta

Sem análise global.
Sem explicações longas.
Prompt C — arbitragem de corredor

Usar quando os passos do corredor já foram revistos.

Não quero análise global do projeto.

Quero arbitrar apenas o corredor [CORREDOR], com base apenas em:
- dossier_corredor_[CORREDOR].json
- matriz_inevitabilidades_v4.json
- mapa_dedutivo_precanonico_v4.json
- relatorio_fecho_canonico_v4.json
- decisões intermédias atuais dos passos do corredor

Objetivo:
decidir se o corredor fecha canonicamente.

Entrega apenas JSON com:
- corredor_id
- estado_do_corredor
- passos_fechados
- passos_a_rever
- subpassos_aprovados
- formulacoes_fixadas
- falhas_remanescentes
- decisao_final

Critérios:
- testar continuidade mínima da cadeia;
- detetar saltos mediacionais;
- confirmar necessidade real de subpassos;
- dizer claramente se o corredor fecha ou não.
Prompt D — auditoria rápida do corredor

Usar antes de começar a rever, para perceber logo onde atacar.

Não quero análise global do projeto.

Quero auditar apenas o corredor [CORREDOR], com base em:
- decisões intermédias do corredor
- respostas do modelo do corredor
- arbitragem atual do corredor

Diz-me apenas, passo a passo:
1) quais estão bons;
2) quais estão aceitáveis mas fracos;
3) quais exigem revisão;
4) quais exigem subpasso;
5) qual é a ordem ótima de correção.

Máximo 15 linhas.
Sem reexplicar o projeto.
Prompt E — versão final de um passo já estabilizado

Usar quando um passo já está quase bom e queres só fixá-lo.

Não quero análise global do projeto.

Quero fixar a versão final do passo [PXX] do corredor [CORREDOR].

Base:
- decisão intermédia atual do passo
- eventuais correções já feitas
- subpasso aprovado, se existir

Entrega apenas JSON com:
- step_id
- formulacao_final_fixada
- justificacao_final_fixada
- ponte_entrada_final
- ponte_saida_final
- objecao_letal_final
- bloqueio_final
- estado_final_do_passo

Sem comentários.
Sem texto extra.
9. Ordem de uso dos prompts
Para o corredor P33_P37

Usar esta sequência:

Prompt D para auditoria rápida do corredor

Prompt A para revisão de P33

Prompt B para decidir subpasso de P33

Prompt A para revisão de P34

Prompt A para revisão de P35

Prompt A para revisão de P36

Prompt B para decidir subpasso de P36

Prompt A para revisão de P37

Prompt C para arbitragem final do corredor

Prompt E para fixar passos que já ficaram bons

Depois repetir a mesma lógica para os outros corredores.

10. Comandos locais que devo correr
Para voltar a correr o orquestrador, se necessário

Só se eu alterar prompts, manifesto ou lógica do script.

python orquestrador_fecho_canonico_api.py
Para correr o consolidador, no fim

Só depois de os corredores estarem revistos.

python consolidador_fecho_canonico.py
11. Regra de decisão importante
Não devo correr já o consolidador se:

P33–P37 ainda tiver saltos;

houver subpassos por decidir;

as arbitragens de corredor estiverem fracas;

decisoes_canonicas_intermedias.json ainda não estiver limpo.

Devo correr o consolidador apenas quando:

os corredores críticos estiverem aceitáveis;

as formulações já estiverem fixadas;

os subpassos necessários estiverem aprovados;

o output intermédio estiver coerente.

12. Resultado final esperado desta fase

No fim desta fase devo ter:

outputs\decisoes_canonicas_intermedias.json revisto e estável;

mapa_dedutivo_canonico_final.json;

relatorio_final_de_inevitabilidades.json.

13. Resumo executivo de continuidade

Quando eu voltar a pegar nisto, não devo pensar “o que era isto tudo outra vez?”.

Devo pensar só isto:

abrir decisoes_canonicas_intermedias.json

começar por P33_P37

rever os passos fracos com prompts localizados

arbitrar o corredor

repetir para os restantes corredores

só no fim consolidar

Se quiseres, no passo seguinte eu transformo isto numa versão ainda mais útil: um README com checklist de execução, com caixas tipo “feito / por fazer”, para ires marcando corredor a corredor.

quais ficheiros é importante por no fonte deste projeto indice?
Pensei durante alguns segundos

Para a fonte do projeto Índice, eu separaria assim: núcleo obrigatório, núcleo de fecho canónico, úteis mas não críticos, e não meter como fonte principal.

1. Núcleo obrigatório do projeto

Estes são os ficheiros que eu considero mesmo importantes para a fonte, porque sem eles perdes a espinha dorsal do sistema:

Base conceptual e metaestrutural

todos_os_conceitos.json

operacoes.json

meta_referencia_do_percurso.json

meta_indice.json

Estrutura do índice e argumentos

indice_sequencial.json

indice_por_percurso.json

indice_argumentos.json

argumentos_unificados.json

mapa_integral_do_indice.json

Camada fragmentária já tratada

fragmentos_resegmentados.json

cadencia_schema.json

cadencia_extraida.json

tratamento_filosofico_fragmentos.json

Camada de impacto e revisão

02_mapa_dedutivo_arquitetura_fragmentos.json

impacto_fragmentos_no_mapa.json

impacto_fragmentos_no_mapa_relatorio_validacao.json

revisao_estrutural_do_mapa.json

2. Núcleo obrigatório da fase atual de fecho canónico

Isto tem mesmo de estar na fonte se queres retomar o trabalho sem perder o fio:

Reconstrução e fecho

mapa_dedutivo_reconstrucao_inevitavel_v3.json

relatorio_reconstrucao_inevitavel_v3.json

matriz_inevitabilidades_v4.json

mapa_dedutivo_precanonico_v4.json

relatorio_fecho_canonico_v4.json

fechador_canonico_mapa.py

Fecho local por corredor

fecho_manual_corredor_P25_P30.json

fecho_manual_corredor_P33_P37.json

fecho_manual_corredor_P42_P48.json

fecho_manual_corredor_P50.json

Dossiês de corredor

dossier_corredor_P25_P30.json

dossier_corredor_P33_P37.json

dossier_corredor_P42_P48.json

dossier_corredor_P50.json

3. Ficheiros que também deves pôr na fonte porque pertencem ao pipeline novo

Como já começaste a fase 02_fecho_canonico_mapa, eu metia também:

Configuração e execução

manifesto_fecho_canonico.json

orquestrador_fecho_canonico_api.py

read_me_fecho_canonico.md

Prompts

prompt_passo_nuclear.txt

prompt_subpasso_mediacional.txt

prompt_arbitragem_corredor.txt

prompt_argumento_complementar.txt

Schemas

schema_decisao_passo.json

schema_decisao_subpasso.json

schema_arbitragem_corredor.json

schema_decisoes_canonicas_intermedias.json

Output intermédio importante

decisoes_canonicas_intermedias.json

Este último não é “fonte estrutural” no mesmo sentido dos outros, mas é fonte de trabalho da fase atual, por isso eu guardava.

4. Ficheiros úteis, mas secundários

Estes ajudam muito, mas se tiveres de priorizar, vêm depois:

fichas_v2_corredor_P25_P30.json

fichas_v2_corredor_P33_P37.json

fichas_v2_corredor_P42_P48.json

fichas_v2_corredor_P50.json

corredor_P25_P30_organizado.json

corredor_P33_P37_organizado.json

corredor_P42_P48_organizado.json

corredor_P50_organizado.json

resumo_extracao_corredores_criticos.json

resumo_montagem_fichas_v2.json

resumo_organizacao_fragmentos_por_funcao.json

resumo_preparacao_fecho_manual.json

5. O que eu não trataria como “fonte principal”

Isto deve existir no projeto, mas não é o que eu usaria como núcleo a preservar para retoma conceptual:

logs/

prompts_enviados/

respostas_modelo/

.raw.txt

ficheiros temporários de execução

outputs redundantes ou duplicados em várias pastas

Guardaria estes por auditoria, mas não como o centro da fonte.

6. Lista mínima mesmo essencial

Se quiseres a versão mais curta possível, os que eu diria “sem estes não vale a pena retomar” são:

todos_os_conceitos.json

operacoes.json

meta_referencia_do_percurso.json

meta_indice.json

indice_sequencial.json

indice_por_percurso.json

indice_argumentos.json

argumentos_unificados.json

fragmentos_resegmentados.json

cadencia_extraida.json

tratamento_filosofico_fragmentos.json

02_mapa_dedutivo_arquitetura_fragmentos.json

impacto_fragmentos_no_mapa.json

revisao_estrutural_do_mapa.json

mapa_dedutivo_reconstrucao_inevitavel_v3.json

relatorio_reconstrucao_inevitavel_v3.json

matriz_inevitabilidades_v4.json

mapa_dedutivo_precanonico_v4.json

relatorio_fecho_canonico_v4.json

dossier_corredor_P25_P30.json

dossier_corredor_P33_P37.json

dossier_corredor_P42_P48.json

dossier_corredor_P50.json

manifesto_fecho_canonico.json

orquestrador_fecho_canonico_api.py

decisoes_canonicas_intermedias.json

7. Regra prática

Se quiseres pensar isto de forma simples:

fonte conceptual → conceitos, operações, meta, índice, argumentos

fonte fragmentária tratada → resegmentação, cadência, tratamento

fonte dedutiva → mapa, impacto, revisão, reconstrução inevitável

fonte de fecho atual → matriz v4, mapa pré-canónico, relatório v4, dossiês, orquestrador, decisões intermédias

