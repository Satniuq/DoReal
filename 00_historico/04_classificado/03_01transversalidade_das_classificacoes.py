import json
from collections import defaultdict

def gerar_mapa_transversal(caminho_dados, caminho_saida):
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            lista_proposicoes = json.load(f)
    except FileNotFoundError:
        print(f"Erro: O ficheiro {caminho_dados} não foi encontrado.")
        return

    mapeamento_blocos = {
        "Ontologia fundamental": "I. FUNDAÇÃO", "Ciência": "I. FUNDAÇÃO", 
        "Antropologia": "II. MEDIAÇÃO", "Consciência": "II. MEDIAÇÃO", "Linguagem": "II. MEDIAÇÃO",
        "Filosofia": "III. PATOLOGIA", "Epistemologia": "III. PATOLOGIA",
        "Ética": "IV. REINTEGRAÇÃO", "Cultura": "IV. REINTEGRAÇÃO", 
        "Direito": "IV. REINTEGRAÇÃO", "Política": "IV. REINTEGRAÇÃO"
    }

    # Estrutura: mapa[termo][bloco] = lista_de_ids
    mapa = defaultdict(lambda: defaultdict(list))

    for prop in lista_proposicoes:
        pid = prop.get("id_proposicao", "???")
        classif = prop.get("classificacao", {})
        temas = classif.get("camada_0_tema_de_incidencia", [])
        ops = classif.get("camada_1_operacao_ontologica", [])
        campos = classif.get("camada_2_campos_ontologicos", [])

        # Determinação do Bloco
        bloco_nome = "IV. REINTEGRAÇÃO"
        if any("erro" in op.lower() or "crítica" in op.lower() for op in ops):
            bloco_nome = "III. PATOLOGIA"
        else:
            for t in temas:
                if t in mapeamento_blocos:
                    bloco_nome = mapeamento_blocos[t]
                    break

        # Mapear cada termo da Camada 2 presente nesta proposição
        for termo in campos:
            mapa[termo][bloco_nome].append(pid)

    # Escrita do Relatório
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("============================================================\n")
        f.write("             MAPA DE TRANSVERSALIDADE CONCEITUAL            \n")
        f.write("      (Como os conceitos evoluem através dos Blocos)        \n")
        f.write("============================================================\n\n")

        # Ordenar termos pelo total de ocorrências (os mais importantes primeiro)
        termos_ordenados = sorted(mapa.items(), key=lambda x: sum(len(ids) for ids in x[1].values()), reverse=True)

        for termo, distribuicao in termos_ordenados:
            total_termo = sum(len(ids) for ids in distribuicao.values())
            if total_termo < 5: continue  # Ignorar termos muito raros para focar no essencial

            f.write(f"\nCONCEITO: {termo.upper()} (Total: {total_termo} ocorrências)\n")
            f.write("-" * 50 + "\n")

            for bloco in ["I. FUNDAÇÃO", "II. MEDIAÇÃO", "III. PATOLOGIA", "IV. REINTEGRAÇÃO"]:
                ids = distribuicao.get(bloco, [])
                if ids:
                    f.write(f"  [{bloco}]: {len(ids)} itens -> {', '.join(ids[:10])}")
                    if len(ids) > 10: f.write("... (e mais)")
                    f.write("\n")
            f.write("\n")

    print(f"Mapa de transversalidade gerado: {caminho_saida}")

# Execução
gerar_mapa_transversal('Classificados_Final.json', 'MAPA_TRANSVERSAL_CONCEITOS.txt')