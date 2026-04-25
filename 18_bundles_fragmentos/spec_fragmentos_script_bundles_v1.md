# SPEC_FRAGMENTOS_SCRIPT_BUNDLES_V1

## 1. Estatuto

Esta spec fixa a variante **fragment-first** do script de geração de bundles reais para limpeza.

O script:
- **itera fragmentos**, não containers nem ficheiros `.md` corridos;
- usa `fragmentos_resegmentados.json` como **fonte primária operativa**;
- usa `fragmentos.md` como **fonte primária de auditoria de origem**;
- trata `fragmentos_nao_processados.md` e `fragmentos_ja_processados.md` como **fontes auxiliares**.

Não chama ainda modelo.
Não limpa texto.
Não resegmenta.
Não reclassifica filosoficamente.
Não reabre a análise já feita.

A sua função é montar **bundles reais de entrada** para limpeza contextual posterior.

---

## 2. Unidade real do script

### 2.1 Unidade canónica
A unidade canónica é o objeto identificado por `fragment_id` em `fragmentos_resegmentados.json`.

Exemplos:
- `F0001_SEG_001`
- `F0018_A01_SEG_001`
- `F0021_SEG_002`

### 2.2 Porque não usar containers como unidade
O script não deve iterar diretamente `F0001`, `F0018`, `F0021`, etc., porque:
- um container pode gerar vários fragmentos;
- alguns fragmentos continuam outros;
- alguns fragmentos são respostas locais;
- alguns fragmentos incluem diálogo com IA.

### 2.3 Regra de seleção
Toda a seleção do lote deve partir de:
- `fragment_id`
- ou lista de `fragment_id`
- ou filtros aplicados sobre campos do objeto de fragmento

Nunca partir diretamente do texto corrido dos ficheiros `.md`.

---

## 3. Fontes e prioridade

## 3.1 Fonte primária operativa
`fragmentos_resegmentados.json`

Usos:
- iteração do universo
- identidade da unidade
- texto-base do fragmento
- segmentação
- flags locais
- continuidade local
- metadados de origem

## 3.2 Fonte primária de auditoria
`fragmentos.md`

Usos:
- confirmação do container de origem
- verificação de cabeçalho formal
- conferência de conteúdo bruto do container
- recuperação em caso de inconsistência do join

## 3.3 Fontes auxiliares
`fragmentos_nao_processados.md`
`fragmentos_ja_processados.md`

Usos:
- auditoria humana
- eventual deteção de material ainda fora da resegmentação
- comparação histórica
- suporte a relatórios

Não devem servir de base primária de join na v1.

---

## 4. Chaves e joins

## 4.1 Chave principal
`fragment_id`

## 4.2 Chaves de proveniência obrigatórias
- `origem.origem_id`
- `origem.header_original`
- `origem.ordem_no_ficheiro`
- `origem.blocos_fonte[].bloco_id`
- `origem.blocos_fonte[].paragrafos_origem[]`

## 4.3 Regra de join mínimo
Para um fragmento ser considerado **resolvido na origem**, o script tem de conseguir obter:
- o objeto completo em `fragmentos_resegmentados.json`
- o respetivo `origem_id`
- o respetivo `header_original`
- e localizar o container correspondente em `fragmentos.md`

## 4.4 Regra de falha
Se existir `fragment_id`, mas:
- faltar `origem_id`, ou
- faltar `header_original`, ou
- o container não puder ser localizado em `fragmentos.md`

então o script deve:
- marcar o fragmento como `join_origem_incompleto`
- não o promover a bundle final limpo
- enviá-lo para relatório de auditoria

---

## 5. Campos sobre que o script tem de incidir

## 5.1 Núcleo obrigatório do fragmento
Para cada `fragment_id`, o script deve recolher e transportar:

### identidade
- `fragment_id`

### proveniência
- `origem.ficheiro`
- `origem.origem_id`
- `origem.data`
- `origem.header_original`
- `origem.ordem_no_ficheiro`
- `origem.blocos_fonte`

### texto
- `texto_fragmento`
- `texto_normalizado`
- `texto_fonte_reconstituido`

### tipo de material
- `tipo_material_fonte`

### segmentação
- `segmentacao.tipo_unidade`
- `segmentacao.criterio_de_unidade`
- `segmentacao.houve_fusao_de_paragrafos`
- `segmentacao.houve_corte_interno`
- `segmentacao.container_tipo_segmentacao`

### forma local
- `funcao_textual_dominante`
- `tema_dominante_provisorio`
- `conceitos_relevantes_provisorios`

### qualidade local
- `integridade_semantica.grau`
- `confianca_segmentacao`
- `estado_revisao`

### continuidade
- `relacoes_locais.fragmento_anterior`
- `relacoes_locais.fragmento_seguinte`
- `relacoes_locais.continua_anterior`
- `relacoes_locais.prepara_seguinte`

### flags de pipeline
- `sinalizador_para_cadencia.pronto_para_extrator_cadencia`
- `sinalizador_para_cadencia.requer_revisao_manual_prioritaria`

### metadados técnicos
- `_metadados_segmentador`

---

## 6. Política para os três textos

## 6.1 Texto principal do bundle
O texto principal para limpeza deve ser:
1. `texto_fonte_reconstituido`, se existir e não estiver vazio;
2. caso contrário, `texto_fragmento`;
3. `texto_normalizado` nunca deve ser o texto principal por defeito.

## 6.2 Papel dos outros dois
- `texto_fragmento`: suporte de comparação
- `texto_normalizado`: suporte de hashing, deduplicação e busca

## 6.3 Regra de divergência
Se `texto_fonte_reconstituido` e `texto_fragmento` divergirem materialmente acima de um limiar configurável, o script deve:
- marcar `divergencia_textual_relevante=true`
- baixar o estado do bundle para `cautela`
- incluir ambos no output

---

## 7. Perfis de fragmento que o script tem de reconhecer

## 7.1 Pelo tipo de unidade
O script deve distinguir pelo menos:
- `afirmacao_curta`
- `distincao_conceptual`
- `resposta_local`
- `sequencia_argumentativa`
- `desenvolvimento_medio`
- `desenvolvimento_curto`
- `fragmento_intuitivo`

## 7.2 Pelo tipo de material fonte
O script deve distinguir pelo menos:
- `misto`
- `fragmento_editorial`
- `fragmento_reflexivo`
- `dialogo_com_ia`

## 7.3 Pelo risco local
A partir dos campos já existentes, o script deve classificar o fragmento em:
- `estavel`
- `cautela`
- `auditoria`

Regra sugerida:
- `estavel`: integridade alta/média, sem revisão manual prioritária, sem diálogo misto problemático
- `cautela`: continuidade ativa, integridade média/baixa, fusão/corte, diálogo parcial, divergência textual
- `auditoria`: origem incompleta, flags críticas, material demasiado híbrido ou fragmento explicitamente problemático

---

## 8. Política para fragmentos com continuidade

## 8.1 Regra
Se um fragmento vier com:
- `continua_anterior=true`
- ou `prepara_seguinte=true`

o script deve montar um **contexto local opcional**.

## 8.2 Conteúdo do contexto local
- `fragmento_anterior` se existir
- `fragmento_seguinte` se existir
- texto curto de ambos
- relação local
- justificação da inclusão

## 8.3 Limite
Na v1, o contexto local deve ser no máximo:
- 1 fragmento anterior
- 1 fragmento seguinte

Sem janelas maiores.

---

## 9. Política para `dialogo_com_ia`

## 9.1 Regra geral
Fragmentos com `tipo_material_fonte="dialogo_com_ia"` nunca devem ser tratados como fragmentos autorais puros.

## 9.2 Modos permitidos
O script deve suportar três modos configuráveis:

### `manter_dialogo`
Mantém o texto completo, com marcação de vozes.

### `extrair_voz_autor`
Tenta isolar apenas:
- `[Resposta do autor]`
- `[Autor]`
- `[Questão do autor]`

e elimina ou rebaixa o resto.

### `marcar_para_auditoria`
Não gera bundle limpável; apenas bundle auditável.

## 9.3 Modo default da v1
Default recomendado:
- `extrair_voz_autor` quando a marcação de voz for explícita
- `marcar_para_auditoria` quando a voz não puder ser separada com segurança

---

## 10. Estados operativos do bundle

Cada fragmento deve terminar num destes estados:

### `limpavel`
- texto principal resolvido
- origem resolvida
- sem ambiguidades graves
- pronto para limpeza posterior

### `limpavel_com_cautela`
- pronto, mas com riscos locais
- exige preservação de contexto local e flags

### `so_auditoria`
- não deve seguir para limpeza automática
- serve só para inspeção humana ou retrabalho

---

## 11. Campos adicionais que o script deve gerar

O script deve gerar por fragmento:

### `bundle_runtime`
- `texto_principal_escolhido`
- `fonte_texto_principal`
- `estado_bundle`
- `motivos_estado`
- `tem_contexto_local`
- `modo_dialogo_aplicado`
- `divergencia_textual_relevante`
- `join_origem_resolvido`
- `hash_texto_principal`

### `instrucao_de_limpeza_minima`
- `modo_limpeza`
- `preservar_voz_autoral`
- `preservar_ordem_argumentativa_local`
- `nao_subir_altitude_filosofica`
- `nao_introduzir_conteudo_novo`
- `nao_unificar_vozes_distintas`
- `tratar_oralidade`
- `tratar_repeticao`
- `tratar_cortes_e_elipses`
- `observacoes_especificas`

---

## 12. Modos de limpeza que o bundle deve suportar

Na v1, o script só precisa de marcar o modo, não executar.

Valores recomendados:
- `minima`
- `conservadora`
- `estrutural`
- `sintatica_local`
- `separacao_de_vozes`

Regra sugerida:
- `afirmacao_curta` → `minima`
- `distincao_conceptual` → `conservadora`
- `sequencia_argumentativa` → `estrutural`
- `dialogo_com_ia` → `separacao_de_vozes`

---

## 13. Outputs do script

## 13.1 Por fragmento
Um ficheiro JSON por `fragment_id`, por exemplo:
`bundles/fragmentos/F0001_SEG_001.bundle.json`

## 13.2 Por lote
- `manifesto_lote.json`
- `lote_bundles_fragmentos.json`
- `relatorio_lote_fragmentos.md`
- `erros_fragmentos.json`

## 13.3 Estrutura mínima do bundle por fragmento
- `identificacao`
- `unidade_base`
- `contexto_local_imediato`
- `bundle_runtime`
- `instrucao_de_limpeza_minima`
- `rastreabilidade`

Na v1 fragment-first, ainda não é obrigatório puxar contexto estrutural amplo do mapa; isso entra na fase seguinte.

---

## 14. CLI da variante fragment-first

### obrigatório
- `--project-root`
- `--fragmentos-resegmentados`
- `--fragmentos-md`
- `--output-dir`

### seleção
- `--fragment-id`
- `--ids-file`
- `--all`

### comportamento
- `--modo-dialogo`
- `--incluir-contexto-local`
- `--modo-falha` (`strict` | `soft`)
- `--max-fragmentos`

### auditoria
- `--fragmentos-nao-processados`
- `--fragmentos-ja-processados`

---

## 15. Regras de falha e recusa

## 15.1 Falha dura
Falhar imediatamente quando:
- `fragmentos_resegmentados.json` não carregar
- o objeto do fragmento não existir
- faltar `fragment_id`
- faltar qualquer dos três campos mínimos de proveniência:
  - `origem_id`
  - `header_original`
  - `ordem_no_ficheiro`

## 15.2 Falha suave
Gerar bundle em `cautela` quando:
- faltar `texto_fonte_reconstituido`
- houver divergência textual relevante
- houver continuidade local ativa
- houver `requer_revisao_manual_prioritaria=true`

## 15.3 Recusa de limpeza
Enviar para `so_auditoria` quando:
- o fragmento for diálogo com IA não separável
- o join com a origem falhar
- o texto principal ficar vazio
- o fragmento estiver estruturalmente corrompido

---

## 16. Ordem recomendada de implementação

### fase 1
- carregar `fragmentos_resegmentados.json`
- iterar `fragment_id`
- montar bundle mínimo
- escrever JSON por fragmento

### fase 2
- resolver auditoria com `fragmentos.md`
- ativar contexto local
- ativar política para `dialogo_com_ia`

### fase 3
- ligar relatório de lote
- ligar fontes auxiliares
- preparar ligação posterior ao contexto analítico e estrutural amplo

---

## 17. Resultado esperado

No fim da v1, o script deve conseguir dizer, por fragmento:
- **qual é a unidade real**
- **de onde vem**
- **qual o texto principal que segue para limpeza**
- **que tipo de fragmento é**
- **se é limpável, limpável com cautela ou só auditável**
- **que contexto local tem de acompanhar**
- **que instrução mínima de limpeza o bundle deve transportar**
