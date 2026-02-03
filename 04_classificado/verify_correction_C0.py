import json

def validar_contagem(orig, limpo):
    with open(orig, 'r', encoding='utf-8') as f:
        contagem_orig = len(json.load(f))
    with open(limpo, 'r', encoding='utf-8') as f:
        contagem_limpo = len(json.load(f))
    
    print(f"Objetos no original: {contagem_orig}")
    print(f"Objetos no corrigido: {contagem_limpo}")
    print(f"Diferença: {contagem_orig - contagem_limpo} objetos.")

validar_contagem('classificados3.json', 'classificados3_limpo_C0.json')