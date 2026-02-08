import json

def gerar_manuscrito_axiomatico(caminho_dados, caminho_saida):
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            proposicoes = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar ficheiro: {e}")
        return

    # --- FILTROS TAXONÓMICOS (Baseados na tua estrutura) ---
    operacoes_fundamentais = {
        "Afirmação ontológica primária",
        "Fundação ontológica",
        "Proposição ontológica básica",
        "Identificação de condição ontológica",
        "Identificação de critério ontológico",
        "Identificação de impossibilidade ontológica",
        "Núcleo ontológico",
        "Recondução da consciência ao real",
        "Recondução da verdade à descrição"
    }

    campos_fundamentais = {
        "Axioma",
        "Ser",
        "Factualidade",
        "Abertura do real",
        "Impossibilidade ontológica",
        "Verdade como descrição",
        "Necessidade",
        "Limites ontológicos",
        "Paridade ontológica"
    }

    def eh_verdade_necessaria(p):
        classif = p.get('classificacao', {})
        
        # Como as camadas são listas no teu JSON, verificamos a interseção
        ops_da_prop = set(classif.get('camada_1_operacao_ontologica', []))
        campos_da_prop = set(classif.get('camada_2_campos_ontologicos', []))
        
        # Critério: Se tiver uma operação fundamental OU um campo fundamental
        tem_op = any(op in operacoes_fundamentais for op in ops_da_prop)
        tem_campo = any(campo in campos_fundamentais for campo in campos_da_prop)
        
        # Também incluímos tudo o que for Nível 5 (Máxima integração)
        nivel = p.get('grau_de_integracao_ontologica', {}).get('nivel', 0)
        
        return tem_op or tem_campo or nivel == 5

    # --- ORGANIZAÇÃO DOS BLOCOS ---
    blocos = [
        ("I. ONTOLOGIA FUNDAMENTAL (SER E AXIOMAS)", ["Ser", "Axioma", "Factualidade", "Abertura do real"]),
        ("II. VERDADE E APREENSÃO", ["Verdade como descrição", "Necessidade", "Paridade ontológica"]),
        ("III. LIMITES E IMPOSSIBILIDADES", ["Impossibilidade ontológica", "Limites ontológicos"])
    ]

    ids_usados = set()

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("      EXTRAÇÃO: VERDADES ONTOLOGICAMENTE NECESSÁRIAS\n")
        f.write("="*60 + "\n\n")

        for titulo, campos_ref in blocos:
            # Seleciona props que passam no filtro e pertencem ao bloco
            selecao = [
                p for p in proposicoes 
                if eh_verdade_necessaria(p) and 
                any(c in p.get('classificacao', {}).get('camada_2_campos_ontologicos', []) for c in campos_ref)
            ]

            if selecao:
                f.write(f"\n{titulo}\n" + "-"*len(titulo) + "\n")
                selecao.sort(key=lambda x: x.get('id_proposicao'))
                for p in selecao:
                    f.write(f"ID: {p['id_proposicao']} | {p['texto_literal']}\n")
                    ids_usados.add(p['id_proposicao'])

        # --- RESÍDUO FUNDAMENTAL ---
        outras = [p for p in proposicoes if eh_verdade_necessaria(p) and p['id_proposicao'] not in ids_usados]
        if outras:
            f.write(f"\nOUTRAS DEFINIÇÕES AXIOMÁTICAS\n" + "-"*30 + "\n")
            for p in outras:
                f.write(f"ID: {p['id_proposicao']} | {p['texto_literal']}\n")

    print(f"Extração concluída: {len(ids_usados) + len(outras)} verdades encontradas.")

if __name__ == "__main__":
    # Ajustei para o caminho que indicaste anteriormente
    import os
    # Caminho absoluto para evitar erros de diretório
    entrada = r'C:\Users\vanes\DoReal_Casa_Local\DoReal\04_classificado\Classificados_Final.json'
    saida = 'VERDADES_NECESSARIAS.txt'
    
    gerar_manuscrito_axiomatico(entrada, saida)