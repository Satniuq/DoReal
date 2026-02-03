import json
from collections import Counter

def analisar_densidade(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    cruzamentos = []
    for prop in dados:
        c0_list = prop['classificacao']['camada_0_tema_de_incidencia']
        c1_list = prop['classificacao']['camada_1_operacao_ontologica']
        
        for c0 in c0_list:
            for c1 in c1_list:
                cruzamentos.append(f"{c0} -> {c1}")

    mais_comuns = Counter(cruzamentos).most_common(10)
    
    print("=== OS 10 PILARES DA TUA ESPINHA DORSAL ===")
    for cruzamento, freq in mais_comuns:
        percentagem = (freq / len(dados)) * 100
        print(f"{freq:4d} ocorrências ({percentagem:4.1f}%) : {cruzamento}")

analisar_densidade('classificados3_ORDENADO_FINAL.json')