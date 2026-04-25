# Meta-Schema Mestre DoReal — v0.2

## O que muda face ao v0.1

Esta versão corrige cinco limites do v0.1:

1. **`texto_limpo` sai da base empírica**  
   Passa para `camada_textual_derivada`, porque a limpeza é um artefacto posterior e não dado de origem.

2. **a validação deixa de ser só uma “camada terminal”**  
   Surge `arbitragem_transversal`, para modelar conflitos entre camadas, exceções ativas e suspensão de automatismos.

3. **cadência, tratamento filosófico e impacto no mapa deixam de ser recipientes genéricos**  
   Ganham tipagem mínima alinhada com as estruturas reais já existentes na fonte do projeto.

4. **entram as peças governativas como entidades próprias**  
   O schema passa a modelar prólogo, grelha, contexto estrutural compacto, notas de destinação e decisões de transição.

5. **entram arestas tipadas**  
   As relações deixam de ser listas secas de IDs e passam a admitir tipo, relevância, efeito, justificação, fonte e confiança.

---

## Estrutura geral

O schema organiza o projeto em:

- `meta_schema`
- `governanca`
- `manifesto_de_cobertura`
- `registro_de_fontes`
- `pecas_governativas`
- `entidades_canonicas`
- `arestas_tipadas`
- `arbitragem_transversal`
- `projecoes_regeneraveis`

---

## Camadas assumidas

A hierarquia de soberania passa a ser:

1. `empirica_base`
2. `textual_derivada`
3. `analitica_derivada`
4. `estrutural_canonica`
5. `expositiva_governativa`
6. `arbitragem_transversal`

Isto quer dizer:
- o texto de origem continua a mandar sobre leituras derivadas;
- a limpeza textual é derivada e nunca substitui a base empírica;
- a estrutura canónica continua a prevalecer sobre conveniência expositiva;
- e a arbitragem transversal existe para suspender automatismos quando as camadas entram em tensão.

---

## Observação metodológica central

Este schema não é um “JSON único achatado”.  
É um schema de **integração de camadas**, pensado para permitir reconstruir:

- o corpus fragmentário limpo,
- a árvore do pensamento,
- o mapa dedutivo,
- o grafo de dependências,
- a arquitetura capitular,
- e o contexto estrutural compacto,

sem colapsar a diferença entre:

- base empírica,
- leitura analítica,
- estrutura,
- governo expositivo,
- e arbitragem.

---

## Próximo passo recomendado

Depois deste v0.2, o próximo passo não é um v0.3 abstrato.

O próximo passo certo é criar uma **instância mínima real** do schema com:
- 5 a 10 fragmentos,
- 2 ou 3 proposições,
- 2 argumentos,
- 1 percurso,
- 1 capítulo,
- 1 faixa expositiva,
- e pelo menos 1 caso de arbitragem transversal.

Só depois disso se vê o que ainda falta fechar.
