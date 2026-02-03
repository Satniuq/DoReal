import json

def corrigir_camada_zero(caminho_entrada, caminho_saida):
    with open(caminho_entrada, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # MAPEAMENTO DE CORREÇÃO (Baseado no teu relatório de erros)
    # Podes ajustar o destino conforme a tua interpretação filosófica
    correcoes_map = {
        "Verdade": "Epistemologia",    # Verdade é critério, o domínio é o conhecimento
        "Sistemas": "Cultura",         # Sistemas são organizações simbólicas/culturais
        "Conhecimento": "Epistemologia",
        "Comunicação": "Linguagem",
        "Sociologia": "Cultura",       # Ou 'Antropologia', conforme preferires
        "Escala": "Ontologia fundamental" 
    }

    termos_oficiais = [
        "Ontologia fundamental", "Epistemologia", "Consciência", "Antropologia", 
        "Ética", "Política", "Direito", "Cultura", "Religião", "Educação", 
        "Linguagem", "Ciência", "Técnica", "Economia", "História", "Filosofia"
    ]

    alteracoes_feitas = 0

    for prop in dados:
        camada0 = prop.get("classificacao", {}).get("camada_0_tema_de_incidencia", [])
        nova_camada0 = []
        houve_mudanca_nesta_prop = False

        for termo in camada0:
            # Se o termo está no mapa de erros, substitui
            if termo in correcoes_map:
                substituto = correcoes_map[termo]
                if substituto not in nova_camada0:
                    nova_camada0.append(substituto)
                houve_mudanca_nesta_prop = True
            # Se o termo já é oficial, mantém
            elif termo in termos_oficiais:
                if termo not in nova_camada0:
                    nova_camada0.append(termo)
            # Se o termo é desconhecido e não está no mapa, movemos para 'Filosofia' por defeito ou avisamos
            else:
                print(f"Aviso: Termo desconhecido '{termo}' no ID {prop['id_proposicao']}. A converter para 'Filosofia'.")
                nova_camada0.append("Filosofia")
                houve_mudanca_nesta_prop = True

        if houve_mudanca_nesta_prop:
            prop["classificacao"]["camada_0_tema_de_incidencia"] = nova_camada0
            alteracoes_feitas += 1

    # Guardar o ficheiro corrigido
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"Sucesso! {alteracoes_feitas} proposições foram corrigidas e normalizadas.")

# Executar
corrigir_camada_zero('classificados3.json', 'classificados3_limpo_C0.json')