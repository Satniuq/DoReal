import json
from collections import defaultdict, Counter

def analisar_influencias_nos_eixos(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # Dicionário: Tema -> {Filósofo: Frequência}
    influencias_por_tema = defaultdict(list)
    # Dicionário: Operação -> {Filósofo: Frequência}
    influencias_por_operacao = defaultdict(list)

    for prop in dados:
        cls = prop['classificacao']
        temas = cls['camada_0_tema_de_incidencia']
        ops = cls['camada_1_operacao_ontologica']
        lexico = cls.get('camada_3_termos_filosoficos_de_contacto', [])

        if not lexico:
            continue

        for filosofo in lexico:
            for t in temas:
                influencias_por_tema[t].append(filosofo)
            for o in ops:
                influencias_por_operacao[o].append(filosofo)

    print("\n" + "="*70)
    print("      RAIO-X DAS INFLUÊNCIAS: QUEM 'PALA' EM CADA TERRENO")
    print("="*70)

    # Analisando os 8 temas principais
    temas_relevantes = ["Ontologia fundamental", "Filosofia", "Antropologia", "Consciência", "Epistemologia", "Ética", "Cultura", "Linguagem"]
    
    for tema in temas_relevantes:
        if tema in influencias_por_tema:
            top_fil = Counter(influencias_por_tema[tema]).most_common(2)
            fil_str = " | ".join([f"{f} ({c})" for f, c in top_fil])
            print(f"• {tema:22} | Interlocutores: {fil_str}")

    print("\n" + "="*70)
    print("      DIÁLOGO NAS OPERAÇÕES (QUEM AJUDA A FAZER O QUÊ)")
    print("="*70)
    
    ops_chave = Counter(influencias_por_operacao.keys())
    for op, _ in ops_chave.most_common(10):
        top_fil = Counter(influencias_por_operacao[op]).most_common(1)
        fil_str = top_fil[0][0] if top_fil else "N/A"
        print(f"• {op:45} -> {fil_str}")

    print("="*70)

analisar_influencias_nos_eixos('Classificados_Final.json')