import json

def gerar_manuscrito_fiel(caminho_dados, caminho_saida):
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            lista_proposicoes = json.load(f)
    except FileNotFoundError:
        print(f"Erro: O ficheiro {caminho_dados} não foi encontrado.")
        return

    mapeamento_blocos = {
        "Ontologia fundamental": "BLOCO I - A FUNDAÇÃO", "Ciência": "BLOCO I - A FUNDAÇÃO", 
        "Antropologia": "BLOCO II - A MEDIAÇÃO", "Consciência": "BLOCO II - A MEDIAÇÃO", "Linguagem": "BLOCO II - A MEDIAÇÃO",
        "Filosofia": "BLOCO III - A PATOLOGIA", "Epistemologia": "BLOCO III - A PATOLOGIA",
        "Ética": "BLOCO IV - A REINTEGRAÇÃO", "Cultura": "BLOCO IV - A REINTEGRAÇÃO", 
        "Direito": "BLOCO IV - A REINTEGRAÇÃO", "Política": "BLOCO IV - A REINTEGRAÇÃO"
    }

    conteudo_organizado = {}
    total_processadas = 0

    for prop in lista_proposicoes:
        total_processadas += 1
        pid = prop.get("id_proposicao", "ID_???")
        texto_real = prop.get("texto_literal", "Texto não encontrado.")
        
        extracao = prop.get("extracao_ontologica", {})
        resumo = extracao.get("explicitação_minima", "Sem explicitação.")
        
        grau = prop.get("grau_de_integracao_ontologica", {})
        nivel = grau.get("nivel", "?")
        
        classif = prop.get("classificacao", {})
        temas = classif.get("camada_0_tema_de_incidencia", [])
        ops = classif.get("camada_1_operacao_ontologica", [])
        campos = classif.get("camada_2_campos_ontologicos", ["Geral"])
        lexico = classif.get("camada_3_termos_filosoficos_de_contacto", [])

        # Lógica de Bloco
        bloco_nome = "BLOCO IV - A REINTEGRAÇÃO"
        if any("erro" in op.lower() or "crítica" in op.lower() for op in ops):
            bloco_nome = "BLOCO III - A PATOLOGIA"
        else:
            for t in temas:
                if t in mapeamento_blocos:
                    bloco_nome = mapeamento_blocos[t]
                    break

        if bloco_nome not in conteudo_organizado:
            conteudo_organizado[bloco_nome] = {}

        subbloco = campos[0] if campos else "Geral"
        if subbloco not in conteudo_organizado[bloco_nome]:
            conteudo_organizado[bloco_nome][subbloco] = []
        
        conteudo_organizado[bloco_nome][subbloco].append({
            "id": pid,
            "nivel": nivel,
            "resumo": resumo,
            "texto": texto_real,
            "lexico": lexico
        })

    # Escrita do ficheiro
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("              MANUSCRITO INTEGRAL: ONTOLOGIA TOTAL          \n")
        f.write(f"              TOTAL DE PROPOSIÇÕES: {total_processadas}      \n")
        f.write("============================================================\n")

        for bloco in ["BLOCO I - A FUNDAÇÃO", "BLOCO II - A MEDIAÇÃO", "BLOCO III - A PATOLOGIA", "BLOCO IV - A REINTEGRAÇÃO"]:
            if bloco not in conteudo_organizado: continue
            
            f.write(f"\n\n{'#'*65}\n")
            f.write(f"  {bloco}\n")
            f.write(f"{'#'*65}\n")

            subs_ordenados = sorted(conteudo_organizado[bloco].items(), key=lambda x: len(x[1]), reverse=True)

            for subbloco, itens in subs_ordenados:
                f.write(f"\n\n[SUBBLOCO: {subbloco.upper()}] ({len(itens)} itens)\n")
                f.write("-" * 40 + "\n")
                
                for item in itens:
                    f.write(f"\nPROPOSIÇÃO {item['id']} | NÍVEL: {item['nivel']}\n")
                    f.write(f"SÍNTESE: {item['resumo']}\n")
                    f.write(f"LITERAL: {item['texto']}\n")
                    if item['lexico']:
                        f.write(f"CONTACTO FILOSÓFICO: {', '.join(item['lexico'])}\n")
                    f.write("." * 20 + "\n")

    print(f"\nCONCLUÍDO!")
    print(f"Foram processadas {total_processadas} proposições.")
    print(f"O ficheiro '{caminho_saida}' está pronto para revisão.")

# Execução
gerar_manuscrito_fiel('Classificados_Final.json', 'MANUSCRITO_REVISAO_FINAL.txt')