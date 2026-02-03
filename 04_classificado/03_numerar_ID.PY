import json

def padronizar_e_renumerar(caminho_entrada, caminho_saida):
    with open(caminho_entrada, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    print(f"A processar {len(dados)} proposições...")

    for i, prop in enumerate(dados, start=1):
        # 1. Renumeração Sequencial
        prop["id_proposicao"] = f"P{i:04d}"

        # 2. Padronização da Camada 3 (Garantir que é sempre Lista)
        classif = prop.get("classificacao", {})
        c3 = classif.get("camada_3_termos_filosoficos_de_contacto")
        
        # Se for um dicionário vazio ou qualquer coisa que não seja lista, converte
        if not isinstance(c3, list):
            classif["camada_3_termos_filosoficos_de_contacto"] = []

    # Guardar com formatação limpa
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"Concluído! Ficheiro santizado e ordenado: {caminho_saida}")

# Execução
padronizar_e_renumerar('classificados3_FINAL_ESTRUTURADO.json', 'classificados3_ONTOLOGIA_TOTAL.json')