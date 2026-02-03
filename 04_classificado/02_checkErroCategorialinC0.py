import json
from collections import Counter

def rastrear_erros_categoriais(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    print("=== MAPA DE CONTAMINAÇÃO: ERRO CATEGORIAL ===\n")
    
    distribuicao_temas = []
    distribuicao_campos = []

    for prop in dados:
        c1 = prop['classificacao']['camada_1_operacao_ontologica']
        # Procurar o termo na C1 ou na C2 (onde o script anterior o normalizou)
        tem_erro = any("Erro categorial" in op for op in c1) or \
                   any("Erro categorial" in campo for campo in prop['classificacao']['camada_2_campos_ontologicos'])
        
        if tem_erro:
            distribuicao_temas.extend(prop['classificacao']['camada_0_tema_de_incidencia'])
            distribuicao_campos.extend(prop['classificacao']['camada_2_campos_ontologicos'])

    print("--- Temas (C0) onde o Erro mais ocorre ---")
    for tema, freq in Counter(distribuicao_temas).most_common():
        print(f" {freq:3d} : {tema}")

    print("\n--- Campos (C2) associados ao Erro ---")
    for campo, freq in Counter(distribuicao_campos).most_common(10):
        if campo != "Erro categorial": # Filtrar o próprio termo
            print(f" {freq:3d} : {campo}")

rastrear_erros_categoriais('classificados3_ORDENADO_FINAL.json')