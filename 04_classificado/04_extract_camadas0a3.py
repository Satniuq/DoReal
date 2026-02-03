import json

def extrair_taxonomia_completa(caminho_entrada, caminho_saida):
    with open(caminho_entrada, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # Conjuntos para garantir termos únicos
    camada_0 = set()
    camada_1 = set()
    camada_2 = set()
    camada_3 = set()

    for prop in dados:
        classif = prop.get("classificacao", {})
        
        # Extração de cada camada
        camada_0.update(classif.get("camada_0_tema_de_incidencia", []))
        camada_1.update(classif.get("camada_1_operacao_ontologica", []))
        camada_2.update(classif.get("camada_2_campos_ontologicos", []))
        camada_3.update(classif.get("camada_3_termos_filosoficos_de_contacto", []))

    # Organização do dicionário final
    taxonomia = {
        "nome_do_sistema": "Ontologia Total - O Ser no Real",
        "total_proposicoes": len(dados),
        "estrutura": {
            "camada_0_dominios": sorted(list(camada_0)),
            "camada_1_operacoes": sorted(list(camada_1)),
            "camada_2_campos": sorted(list(camada_2)),
            "camada_3_lexico_contacto": sorted(list(camada_3))
        }
    }

    # Guardar o ficheiro de referência
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(taxonomia, f, ensure_ascii=False, indent=2)

    print(f"Taxonomia extraída com sucesso!")
    print(f"Domínios (C0): {len(camada_0)}")
    print(f"Operações (C1): {len(camada_1)}")
    print(f"Campos (C2): {len(camada_2)}")
    print(f"Léxico C3: {len(camada_3)}")
    print(f"Ficheiro gerado: {caminho_saida}")

# Execução
extrair_taxonomia_completa('classificados3_ONTOLOGIA_TOTAL.json', 'TAXONOMIA_ONTOLOGIA_TOTAL.json')