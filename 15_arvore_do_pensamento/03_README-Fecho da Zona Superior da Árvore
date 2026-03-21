# 00_README — Fecho da Zona Superior da Árvore (v1)

## 1. Enquadramento

Esta fase corresponde ao **fecho estrutural da zona superior da árvore do pensamento v1**, especificamente no acoplamento:

```
ramo → percurso → argumento
```

O objetivo foi:

> eliminar permissividade semântica, estabilizar percursos e adjudicar argumentos de forma restritiva, evitando inflação e garantindo correspondência estrutural.

---

## 2. Problema inicial identificado

A árvore apresentava:

* **camada de microlinhas e ramos utilizável**, mas ainda granular;
* **percursos relativamente estáveis**;
* **argumentos inflacionados e heterogéneos**;

Sinais concretos:

* múltiplos argumentos por ramo (até 3+);
* avisos de plausibilidade;
* heterogeneidade estrutural;
* ramos sem argumento e argumentos sem ramos.

Diagnóstico central:

> o bloqueio estava no excesso de permissividade no acoplamento **ramo → argumento**, não na base da árvore.

---

## 3. Método adotado

Foi aplicado um método em três fases:

### (1) Triagem

Isolamento do universo de revisão da zona superior.

### (2) Estabilização de percursos

Revisão restritiva de ramo → percurso.

### (3) Adjudicação de argumentos

Fecho restritivo assistido por API dos casos ambíguos.

Princípio dominante:

> **na dúvida, não subir**

---

## 4. Execução realizada

### 4.1 Triagem — `triagem_fecho_superior_v1.py`

Output:

* `triagem_fecho_superior_v1.json`
* `relatorio_triagem_fecho_superior_v1.txt`

Resultado:

* Total ramos: 67
* Grupo A (rever argumento): 26
* Grupo B (rever percurso): 9
* Grupo C (sem subida): 23
* Grupo D (estáveis): 9

---

### 4.2 Revisão de percursos — `rever_percursos_superiores_v1.py`

Input:

* triagem

Output:

* `arvore_do_pensamento_v1_pos_percursos.json`
* `relatorio_revisao_percursos_superiores_v1.txt`

Resultado:

* Ramos analisados (Grupo B): 9
* Percursos confirmados: 3
* Percursos removidos: 6
* Revisão manual: 0

Estado:

> camada de percursos considerada **suficientemente estabilizada**

---

### 4.3 Revisão restritiva de argumentos — `rever_argumentos_restritivo_v1.py`

Resultado inicial:

* Ramos revistos: 29
* Todos ficaram sem argumento
* 26 ficaram em revisão manual

Conclusão:

> a heurística restritiva foi eficaz a limpar, mas insuficiente para decidir entre candidatos fortes

---

### 4.4 Adjudicação assistida por API — `adjudicar_argumentos_api_v1.py`

Output:

* `adjudicacao_argumentos_api_v1.json`
* `relatorio_adjudicacao_argumentos_api_v1.txt`
* `adjudicacao_argumentos_api_v1_estado.json`
* logs JSONL

Resultado final:

* Ramos considerados: 26
* Manter 1 argumento: 8
* Manter 2 argumentos (excecional): 6
* Manter 0 argumentos: 11
* Revisão humana: 1

---

## 5. Estado atual da árvore

### 5.1 Zona superior

A zona:

```
ramo → percurso → argumento
```

está:

> **materialmente fechada, com uma única pendência residual**

* apenas 1 ramo exige revisão humana;
* todos os restantes têm estado final definido.

---

### 5.2 Qualidade estrutural atingida

A árvore passou de:

* inflação argumentativa;
* associações permissivas;
* cobertura artificial;

para:

* **associações seletivas**
* **redução de heterogeneidade**
* **existência explícita de ramos sem argumento (quando apropriado)**
* **correspondência estrutural entre ramo e argumento**

---

### 5.3 Propriedade crítica atingida

> a árvore deixou de ser inflacionária e passou a ser **restritiva e discriminativa**

---

## 6. Ficheiros relevantes

### Árvore

* `arvore_do_pensamento_v1.json` (original)
* `arvore_do_pensamento_v1_pos_percursos.json`
* `arvore_do_pensamento_v1_fecho_superior.json`

### Triagem

* `triagem_fecho_superior_v1.json`
* `relatorio_triagem_fecho_superior_v1.txt`

### Percursos

* `relatorio_geracao_percursos_v1.txt`
* `relatorio_validacao_percursos_v1.txt`
* `relatorio_revisao_percursos_superiores_v1.txt`

### Argumentos

* `relatorio_geracao_argumentos_v1.txt`
* `relatorio_validacao_argumentos_v1.txt`
* `relatorio_revisao_argumentos_restritiva_v1.txt`

### Adjudicação

* `adjudicacao_argumentos_api_v1.json`
* `adjudicacao_argumentos_api_v1_estado.json`
* `adjudicacao_argumentos_api_v1_logs.jsonl`
* `relatorio_adjudicacao_argumentos_api_v1.txt`

---

## 7. O que falta (pendência residual)

* 1 ramo com:

  * `revisao_humana_necessaria`

Este caso deve ser:

* decidido manualmente;
* ou reprocessado com prompt ajustado, se necessário.

---

## 8. Próximo passo imediato

### 8.1 Aplicação das decisões à árvore

Criar script:

```
aplicar_adjudicacao_argumentos_v1.py
```

Função:

* ler adjudicação;
* atualizar `argumento_ids_associados`;
* gerar nova árvore final.

---

### 8.2 Opcional (recomendado)

Resolver o ramo pendente antes da aplicação final.

---

## 9. Próxima fase do projeto

Após aplicação:

### Entrada em nova fase:

👉 **convergências e relações globais**

Agora que:

* a árvore está limpa;
* o topo está estabilizado;
* as associações são fiáveis;

já é seguro:

* gerar convergências;
* mapear relações;
* iniciar integração global.

---

## 10. Conclusão

A fase de fecho da zona superior cumpriu o objetivo:

> transformar uma estrutura inflacionada numa estrutura seletiva, coerente e preparada para integração global.

A árvore v1 encontra-se agora:

* estruturalmente consistente;
* semanticamente restritiva;
* operacionalmente utilizável para a fase seguinte.

---

## 11. Fórmula final

> primeiro restringiu-se, depois estabilizou-se, depois adjudicou-se — e só então a árvore fechou.
