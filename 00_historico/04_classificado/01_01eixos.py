import json
from collections import Counter, defaultdict

def analisar_eixos_profundos(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    eixos_completos = []
    campos_por_tema = defaultdict(list)
    
    for prop in dados:
        cls = prop['classificacao']
        temas = cls['camada_0_tema_de_incidencia']
        operacoes = cls['camada_1_operacao_ontologica']
        campos = cls.get('camada_2_campos_ontologicos', ["(Sem campo)"])

        for t in temas:
            for o in operacoes:
                # Eixo Principal
                eixos_completos.append(f"{t:20} -> {o}")
                # Mapeamento de profundidade
                for c in campos:
                    campos_por_tema[t].append(c)

    # 1. Top 15 Eixos Estruturais
    mais_comuns = Counter(eixos_completos).most_common(15)
    
    print("\n" + "="*60)
    print("      MAPA DE DENSIDADE: OS 15 EIXOS ESTRUTURAIS")
    print("="*60)
    for i, (eixo, freq) in enumerate(mais_comuns, 1):
        print(f"{i:02d}. [{freq:4d} ocorr.] : {eixo}")

    # 2. Análise de Terreno (Onde cada tema 'pisa')
    print("\n" + "="*60)
    print("      ANÁLISE DE TERRENO (ONDE OS TEMAS HABITAM)")
    print("="*60)
    for tema in sorted(campos_por_tema.keys()):
        top_campos = Counter(campos_por_tema[tema]).most_common(3)
        campos_str = ", ".join([f"{c} ({f})" for c, f in top_campos])
        print(f"• {tema:22} | Campos principais: {campos_str}")

    print("\n" + "="*60)
    print(f"Total de proposições analisadas: {len(dados)}")
    print("="*60)

analisar_eixos_profundos('Classificados_Final.json')