import json

def normalizar_camada_1(caminho_entrada, caminho_saida):
    with open(caminho_entrada, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # 1. MAPEAMENTO DE FUSÃO (Termos a serem "comidos")
    mapeamento_fusao = {
        "Exclusão de exterioridade ontológica": "Rejeição de exterioridade ontológica",
        "Descrição de pressuposto implícito": "Pressuposto ontológico implícito",
        "Descrição funcional": "Continuidade funcional",
        "Identificação de regularidade": "Descrição de regularidade",
        "Identificação de erro como falha de descrição": "Identificação do erro como falha de descrição",
        "Identificação de relação estrutural": "Relação estrutural",
        "Identificação de limite ontológico": "Fixação de limite ontológico",
        "Dissolução de confusão conceptual": "Desambiguação conceptual",
        "Dissolução de falso problema": "Correção de falso problema",
        "Recondução do direito à descrição": "Recondução da filosofia à ontologia aplicada",
        "Subordinação da ação a critério ontológico": "Subordinação do dever-ser ao poder-ser"
    }

    # 2. TERMOS QUE DEVEM FICAR (Serão integrados como novos oficiais)
    termos_que_ficam = [
        "Identificação de erro de escala",
        "Identificação de degeneração",
        "Ancoragem corporal",
        "Identificação de impossibilidade ontológica",
        "Recondução da consciência ao real",
        "Identificação de posição filosófica",
        "Identificação de problema filosófico",
        "Fundação ontológica",
        "Identificação de consequência ontológica"
    ]

    contagem_substituicoes = 0
    termos_mantidos_encontrados = set()

    for prop in dados:
        camada1 = prop.get("classificacao", {}).get("camada_1_operacao_ontologica", [])
        nova_camada1 = []
        alterou = False

        for termo in camada1:
            # Se for para ser comido:
            if termo in mapeamento_fusao:
                novo_termo = mapeamento_fusao[termo]
                if novo_termo not in nova_camada1:
                    nova_camada1.append(novo_termo)
                alterou = True
                contagem_substituicoes += 1
            
            # Se for para ficar:
            elif termo in termos_que_ficam:
                termos_mantidos_encontrados.add(termo)
                if termo not in nova_camada1:
                    nova_camada1.append(termo)
            
            # Se já for oficial ou outro:
            else:
                if termo not in nova_camada1:
                    nova_camada1.append(termo)

        if alterou:
            prop["classificacao"]["camada_1_operacao_ontologica"] = nova_camada1

    # Guardar ficheiro
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print("=== RELATÓRIO DE NORMALIZAÇÃO DA CAMADA 1 ===")
    print(f"Total de substituições (termos comidos): {contagem_substituicoes}")
    print(f"Termos 'promovidos' a oficiais encontrados: {len(termos_mantidos_encontrados)}")
    for t in sorted(termos_mantidos_encontrados):
        print(f"  [+] Mantido: {t}")
    print(f"\nFicheiro guardado como: {caminho_saida}")

# Execução
normalizar_camada_1('classificados3_limpo_C0.json', 'classificados3_limpo_C1.json')