# README — Estado atual do fecho canónico e transição para o fecho do mapa dedutivo

## 1. Situação em que o projeto se encontra

A fase de revisão localizada dos corredores críticos foi concluída.

Corredores fechados localmente:
- `P33_P37`
- `P25_P30`
- `P42_P48`
- `P50`

Depois desse fecho local, foi concluída a consolidação estrutural do ficheiro agregador intermédio de decisões canónicas.

Neste momento, o projeto **já não está** em fase de:
- reabertura de corredores;
- auditoria local de passos;
- decisão sobre criação ou rejeição de subpassos.

Neste momento, o projeto está **entre**:
1. o fecho filosófico-local dos corredores críticos; e
2. o fecho terminal do pipeline, isto é, a produção do mapa dedutivo canónico final e do relatório final de inevitabilidades.

---

## 2. O que já foi efetivamente fechado

Foi concluído o seguinte:
- fecho local dos quatro corredores críticos;
- substituição das arbitragens antigas por arbitragens compatíveis com os estados locais prevalecentes;
- consolidação estrutural do agregador intermédio;
- validação do agregador consolidado contra os schemas.

Resumo validado do agregador consolidado:
- `19` decisões por passo;
- `17` decisões por subpasso;
- `4` arbitragens de corredor;
- `19` passos fechados;
- `0` passos abertos;
- `1` subpasso aprovado;
- `16` subpassos rejeitados;
- `4` corredores fechados;
- `0` corredores para reabrir.

Isto significa que o problema remanescente **já não é local nem filosófico no mesmo sentido** em que foram os quatro corredores. O problema seguinte é de **consolidação terminal do sistema**: projetar as decisões intermédias já fechadas sobre o mapa pré-canónico para obter o mapa canónico final.

---

## 3. Ficheiro de referência atual

### Ficheiro normativo da fase atual
O ficheiro que deve ser tratado como **fonte de verdade desta fase** é:

- `outputs/decisoes_canonicas_intermedias_consolidado_final_intermedio.json`

Este é o agregador intermédio já consolidado e validado.

### Ficheiros anteriores que não devem ser usados como base principal
- `outputs/decisoes_canonicas_intermedias_copy_3 copy.json`  
  (base de trabalho anterior à consolidação)
- `outputs/decisoes_canonicas_intermedias.json`  
  (nome canónico previsto no manifesto para o output intermédio, mas não assumir como autoritativo enquanto não for explicitamente alinhado com a versão consolidada atual)

Regra prática: **para qualquer passo seguinte, usar como base o ficheiro `decisoes_canonicas_intermedias_consolidado_final_intermedio.json`**.

---

## 4. O que isto significa para o fecho do mapa dedutivo

O fecho dos corredores críticos deu ao projeto uma base intermédia consolidada de decisões canónicas.

Essa base ainda **não é** o mapa dedutivo canónico final.
Ela é o conjunto intermédio de decisões que deve agora governar a transformação do mapa pré-canónico no mapa final.

Por isso, o próximo salto do projeto já não é:
- fechar mais um corredor;
- rever passos localmente;
- discutir subpassos rejeitados.

O próximo salto é:
- tomar o agregador intermédio consolidado como norma de inserção;
- projetar essas decisões sobre o `mapa_dedutivo_precanonico_v4.json`;
- gerar o `mapa_dedutivo_canonico_final.json`;
- gerar o `relatorio_final_de_inevitabilidades.json`.

---

## 5. Ficheiros relevantes nesta fase e na transição para a fase seguinte

### A. Núcleo normativo da fase atual
- `manifesto_fecho_canonico.json`
- `outputs/decisoes_canonicas_intermedias_consolidado_final_intermedio.json`
- `relatorio_validacao_consolidacao.txt`
- `06_README — Estado atual do fecho canónico e passo seguinte_consolidacao.txt`
- `07_README_estado_atual_e_transicao_para_fecho_do_mapa.md`  
  (este README atualizado)

### B. Schemas de validação do agregador intermédio
- `schema_decisoes_canonicas_intermedias.json`
- `schema_decisao_passo.json`
- `schema_decisao_subpasso.json`
- `schema_arbitragem_corredor.json`

### C. Inputs nucleares que sustentam a transição para o mapa final
- `matriz_inevitabilidades_v4.json`
- `mapa_dedutivo_precanonico_v4.json`
- `relatorio_fecho_canonico_v4.json`

### D. Dossiers dos corredores críticos já fechados
- `dossier_corredor_P33_P37.json`
- `dossier_corredor_P25_P30.json`
- `dossier_corredor_P42_P48.json`
- `dossier_corredor_P50.json`

### E. Inputs secundários de apoio (usar apenas se o próximo passo realmente os exigir)
- `revisao_estrutural_do_mapa.json`
- `02_mapa_dedutivo_arquitetura_fragmentos.json`
- `argumentos_unificados.json`
- `indice_por_percurso.json`
- `impacto_fragmentos_no_mapa.json`
- `tratamento_filosofico_fragmentos.json`

### F. Prompts e utilitários já existentes
- `prompt_passo_nuclear.txt`
- `prompt_subpasso_mediacional.txt`
- `prompt_arbitragem_corredor.txt`
- `prompt_argumento_complementar.txt`
- `orquestrador_fecho_canonico_api.py`
- `patch_consolidacao_agregador.py`

### G. Ficheiros da fase terminal do pipeline
Previstos no manifesto:
- `consolidador_fecho_canonico.py`
- `outputs/mapa_dedutivo_canonico_final.json`
- `outputs/relatorio_final_de_inevitabilidades.json`

Nota: estes pertencem ao **fecho terminal do pipeline**. São o alvo da fase seguinte, não o centro da fase intermédia já fechada.

---

## 6. Leitura correta do estado atual

Neste momento, a leitura correta é esta:
- os corredores críticos estão fechados;
- o agregador intermédio está consolidado e validado;
- a fase de consolidação do agregador pode ser tratada como encerrada;
- o mapa dedutivo final ainda não foi materializado como output terminal do pipeline.

Em termos práticos, isso quer dizer:
- **o miolo crítico do fecho filosófico está resolvido**;
- **falta a consolidação terminal do sistema**.

---

## 7. Próximo passo recomendado

Abrir o próximo passo já com foco exclusivo em **fechar o mapa dedutivo**, e não em reabrir trabalho intermédio.

Formulação correta do objetivo seguinte:

> Tomar `outputs/decisoes_canonicas_intermedias_consolidado_final_intermedio.json` como base normativa intermédia e transformá-la, com apoio do `manifesto_fecho_canonico.json`, do `mapa_dedutivo_precanonico_v4.json`, da `matriz_inevitabilidades_v4.json` e do `relatorio_fecho_canonico_v4.json`, nos outputs finais previstos no manifesto: `outputs/mapa_dedutivo_canonico_final.json` e `outputs/relatorio_final_de_inevitabilidades.json`.

---

## 8. Regra operacional para o próximo chat / próximo passo

Ao abrir o passo seguinte, assumir sempre:
- que os quatro corredores críticos já estão fechados;
- que o agregador intermédio válido é `outputs/decisoes_canonicas_intermedias_consolidado_final_intermedio.json`;
- que o objetivo já não é discutir a correção local dos corredores;
- que o objetivo é passar do estado intermédio consolidado para os outputs finais do pipeline.

Evitar regressões para:
- reauditorias locais;
- reabertura de subpassos;
- verificação de suficiência documental da fase anterior;
- discussão entre versões antigas do agregador.

---

## 9. Pergunta-guia do próximo passo

A pergunta certa daqui para a frente é:

> Como transformar o agregador intermédio consolidado no mapa dedutivo canónico final e no relatório final de inevitabilidades, com base nos ficheiros normativos e nucleares já estabilizados?

