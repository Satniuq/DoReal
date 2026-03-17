README — Fase atual: fecho canónico do mapa dedutivo
1. Objetivo desta fase

O objetivo desta fase não é voltar a analisar o projeto inteiro, nem refazer a história dos fragmentos, nem reconstruir de novo a arquitetura global do sistema.

O objetivo agora é este:

fechar canonicamente o mapa dedutivo já reconstruído, transformando o estado atual do mapa numa versão em que cada passo tenha:

formulação canónica estável;

justificação mínima suficiente;

mediação explícita quando o salto ainda existe;

objeção letal identificada e bloqueada;

eventual subpasso formal quando o passo não fecha sozinho;

continuidade dedutiva clara com o passo anterior e com o seguinte.

Nesta fase, a máquina deve trabalhar como instrumento de fecho localizado e auditável, e não como gerador de nova análise global.

2. Regra principal de trabalho

A regra central desta fase é simples:

não fazer análise global do projeto.

A máquina deve trabalhar apenas sobre:

um corredor de cada vez;

um passo de cada vez;

um problema de fecho de cada vez.

Sempre que possível, a máquina deve responder em formato estruturado e produzir diretamente ficheiros utilizáveis.

Ela não deve:

recontar a narrativa total do projeto;

repetir o enquadramento filosófico desde o início;

propor novas fases paralelas;

abrir novamente o problema da “árvore do pensamento”;

substituir o mapa atual por nova reconstrução geral.

3. Estado do projeto nesta fase

O projeto já dispõe de uma base suficiente para o fecho canónico.

Já existem:

ficheiros estruturais do sistema;

ficheiros de índice e argumentos;

camada fragmentária tratada;

mapa dedutivo reconstruído;

revisão estrutural do mapa;

matriz de inevitabilidades;

mapa pré-canónico;

relatório de fecho;

dossiês de corredores críticos.

Isto significa que o problema atual já não é descobrir o mapa.

O problema atual é:

fechar localmente as inevitabilidades que ainda ficaram abertas, quase fechadas ou mediacionalmente incompletas.

4. O que a máquina deve assumir como tarefa atual

A máquina deve assumir que está a trabalhar na seguinte missão:

produzir os ficheiros necessários para transformar o mapa dedutivo pré-canónico num mapa dedutivo canónico final.

Isso implica três níveis de trabalho:

a) Fecho por passo

Para cada passo, a máquina deve ser capaz de produzir:

formulação canónica final;

justificação mínima suficiente;

ponte de entrada;

ponte de saída;

razão pela qual o passo anterior não basta;

razão pela qual o passo não pode ser suprimido;

objeção letal;

bloqueio curto da objeção;

decisão sobre necessidade de subpasso.

b) Fecho por subpasso

Quando um passo não fecha sem mediação intermédia, a máquina deve decidir:

se é necessário subpasso;

qual a formulação do subpasso;

onde entra na cadeia;

que função dedutiva cumpre.

c) Fecho por corredor

No fim de cada corredor, a máquina deve decidir:

se a sequência mínima ficou realmente fechada;

que passos ainda têm de ser reabertos;

que subpassos são aprovados;

que formulações ficam fixadas.

5. Ordem correta de trabalho

A máquina não deve trabalhar o mapa inteiro de uma vez.

Deve seguir esta ordem:

P33–P37

P25–P30

P42–P48

P50

restantes passos ainda abertos ou quase fechados

Isto quer dizer que o primeiro piloto operacional desta fase é:

fecho do corredor P33–P37

Tudo o que for pedido à máquina nesta fase deve, por defeito, ser orientado primeiro para esse corredor, salvo instrução expressa em contrário.

6. Ficheiros de entrada obrigatórios

A máquina deve assumir como núcleo mínimo desta fase os seguintes ficheiros já existentes:

matriz_inevitabilidades_v4.json

mapa_dedutivo_precanonico_v4.json

relatorio_fecho_canonico_v4.json

dossier_corredor_P33_P37.json

dossier_corredor_P25_P30.json

dossier_corredor_P42_P48.json

dossier_corredor_P50.json

Pode também usar, quando necessário, estes ficheiros de apoio:

revisao_estrutural_do_mapa.json

02_mapa_dedutivo_arquitetura_fragmentos.json

argumentos_unificados.json

indice_por_percurso.json

impacto_fragmentos_no_mapa.json

tratamento_filosofico_fragmentos.json

7. Ficheiros que a máquina deve produzir nesta fase

A prioridade é produzir os seguintes ficheiros:

ficheiros de configuração

manifesto_fecho_canonico.json

schemas

schema_decisao_passo.json

schema_decisao_subpasso.json

schema_arbitragem_corredor.json

schema_decisoes_canonicas_intermedias.json

prompts

prompt_passo_nuclear.txt

prompt_subpasso_mediacional.txt

prompt_arbitragem_corredor.txt

prompt_argumento_complementar.txt

scripts

orquestrador_fecho_canonico_api.py

consolidador_fecho_canonico.py

outputs intermédios

decisoes_canonicas_intermedias.json

outputs finais

mapa_dedutivo_canonico_final.json

relatorio_final_de_inevitabilidades.json

8. Estrutura de pasta recomendada
15_fecho_canonico/
    README_fecho_canonico.md
    manifesto_fecho_canonico.json
    orquestrador_fecho_canonico_api.py
    consolidador_fecho_canonico.py
    prompts/
        prompt_passo_nuclear.txt
        prompt_subpasso_mediacional.txt
        prompt_arbitragem_corredor.txt
        prompt_argumento_complementar.txt
    schemas/
        schema_decisao_passo.json
        schema_decisao_subpasso.json
        schema_arbitragem_corredor.json
        schema_decisoes_canonicas_intermedias.json
    dados/
        matriz_inevitabilidades_v4.json
        mapa_dedutivo_precanonico_v4.json
        relatorio_fecho_canonico_v4.json
        dossier_corredor_P33_P37.json
        dossier_corredor_P25_P30.json
        dossier_corredor_P42_P48.json
        dossier_corredor_P50.json
    outputs/
        decisoes_canonicas_intermedias.json
        mapa_dedutivo_canonico_final.json
        relatorio_final_de_inevitabilidades.json
    logs/
    prompts_enviados/
    respostas_modelo/
9. Como a máquina deve responder

Sempre que lhe for pedido um ficheiro, a máquina deve:

entregar o ficheiro completo;

evitar explicações longas antes do conteúdo;

evitar reflexão filosófica extra não pedida;

evitar análise global do projeto;

usar apenas os ficheiros relevantes para a tarefa pedida;

escolher a melhor solução única quando houver várias;

responder de forma diretamente utilizável.

Formato preferido:

código completo, quando se tratar de .py;

JSON válido, quando se tratar de .json;

texto integral pronto a guardar, quando se tratar de .txt ou .md.

10. Instrução operacional para prompts futuros

Quando se pedir algo à máquina nesta fase, a formulação base deve ser esta:

Não quero análise global do projeto. Quero apenas [ficheiro ou tarefa], com base apenas em [ficheiros relevantes], no formato [formato pretendido].

Exemplo:

Não quero análise global do projeto. Quero apenas o ficheiro manifesto_fecho_canonico.json, com base em matriz_inevitabilidades_v4.json, mapa_dedutivo_precanonico_v4.json, relatorio_fecho_canonico_v4.json e dossier_corredor_P33_P37.json. Entrega apenas o JSON completo e válido.

11. Critério de sucesso desta fase

Esta fase só fica concluída quando existir:

um conjunto de decisões intermédias auditáveis;

um mapa canónico final consolidado;

um relatório final de inevitabilidades;

um pipeline capaz de fechar corredores sem voltar a abrir análise global do projeto.

12. Resumo executivo

Nesta fase, a máquina não deve pensar o projeto inteiro outra vez.

Deve fazer apenas isto:

fechar passos;

fechar subpassos;

arbitrar corredores;

consolidar decisões;

produzir o mapa dedutivo canónico final.

O primeiro alvo operativo é:

corredor P33–P37