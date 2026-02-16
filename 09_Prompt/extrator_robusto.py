# extrator_robusto.py
# Compilador Ontológico Formal v3.2
# Focado em: Rigor de Nível, Limpeza de Índice e Validação de Dependências

from google import genai
import json
import time
import re
import os
import numpy as np
from dotenv import load_dotenv

# ==========================================
# 0) CONFIGURAÇÃO E AMBIENTE
# ==========================================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY não encontrado no ficheiro .env")

MODELO_RACIOCINIO = "gemini-2.5-pro"
MODELO_EMBEDDING = "gemini-embedding-001"

# Caminhos de Ficheiros
FICHEIRO_MANUSCRITO = r"C:\Users\vanes\DoReal_Casa_Local\DoReal\04_classificado\06_01Texto_No_Indice_TXT.txt"
FICHEIRO_SAIDA = "data/extracao_ontologica_final.json"

# Configurações de Fluxo
LIMITE_FRAGMENTOS_TESTE = 5  # Muda para None para processar os 3000 fragmentos
PAUSA_ENTRE_CHAMADAS = 1.2    # Proteção contra Rate Limit

client = genai.Client(api_key=API_KEY)

# ==========================================
# 1) UTILITÁRIOS TÉCNICOS
# ==========================================
def limpar_json(texto: str) -> str:
    """Extrai apenas o objeto JSON entre chavetas, ignorando lixo da IA."""
    texto = re.sub(r"```(?:json)?\s*|\s*```", "", texto).strip()
    match = re.search(r"(\{.*\})", texto, re.DOTALL)
    if match:
        return match.group(1)
    return texto

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cálculo de similaridade sem dependências externas (scipy)."""
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
    return float(np.dot(a, b) / denom)

# ==========================================
# 2) CARREGAMENTO DO ECOSSISTEMA
# ==========================================
def carregar_ecossistema():
    with open("config/definicoes.json", "r", encoding="utf-8") as f:
        defs = json.load(f)
    with open("config/operacoes.json", "r", encoding="utf-8") as f:
        ops = json.load(f)
    with open("config/vetores_definicoes.json", "r", encoding="utf-8") as f:
        vetores = json.load(f)

    grafo = {d["id"]: d for d in defs}
    return grafo, ops, vetores

# ==========================================
# 3) BUSCA VETORIAL E EXPANSÃO DE GRAFO
# ==========================================
def buscar_candidatos(texto_frag, base_vetorial, top_n=6):
    """Descobre quais os campos ontológicos mais prováveis matematicamente."""
    res = client.models.embed_content(model=MODELO_EMBEDDING, contents=texto_frag)
    v_frag = np.array(res.embeddings[0].values, dtype=np.float32)

    sims = []
    for item in base_vetorial:
        v_def = np.array(item["vetor"], dtype=np.float32)
        sims.append((item["id"], cosine_sim(v_frag, v_def)))

    sims.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in sims[:top_n]]

def expandir_ids(ids_candidatos, grafo):
    """Adiciona as dependências obrigatórias dos IDs candidatos para evitar erros de validação."""
    permitidos = set(ids_candidatos)
    for _ in range(2):
        novos = {dep for i in list(permitidos) if i in grafo for dep in grafo[i].get("depende_de", []) if dep in grafo}
        permitidos |= novos
    return sorted(list(permitidos))

# ==========================================
# 4) VALIDAÇÃO DETERMINÍSTICA
# ==========================================
def validar_ficha(ficha, grafo, operacoes_validas, ids_permitidos):
    if isinstance(ficha, list) and len(ficha) > 0: ficha = ficha[0]
    if not isinstance(ficha, dict): return ["Resposta da IA não é um objeto JSON { }."]

    erros = []
    lv = ficha.get("localizacao_vertical", {})
    cp = lv.get("campo_principal")
    
    # IDs e Whitelist
    usados = [cp] + lv.get("campos_secundarios", []) + ficha.get("dependencias", []) + ficha.get("gera", [])
    for x in usados:
        if x and x not in grafo: erros.append(f"ID inexistente: {x}")
        elif x and x not in ids_permitidos: erros.append(f"ID fora da whitelist: {x}")

    # Rigor de Nível
    try:
        n_decl = int(lv.get("nivel", -1))
        if cp in grafo and int(grafo[cp]["nivel"]) != n_decl:
            erros.append(f"Incoerência: {cp} é Nível {grafo[cp]['nivel']}, não {n_decl}.")
    except: erros.append("Nível declarado inválido.")

    # Operações
    op_raw = ficha.get("operacao_ontologica", "")
    partes = [p.strip() for p in re.split(r"[;,\n]+", str(op_raw)) if p.strip()]
    for p in partes:
        if p not in operacoes_validas: erros.append(f"Operação inválida: {p}")
    if not partes: erros.append("Operação ausente.")
    ficha["operacao_ontologica"] = partes

    # Dependências Obrigatórias
    if cp in grafo:
        faltam = set(grafo[cp].get("depende_de", [])) - set(ficha.get("dependencias", []))
        if faltam: erros.append(f"Faltam dependências para {cp}: {list(faltam)}")

    return erros

# ==========================================
# 5) PROMPT REFORÇADO (CONTRACT-BASED)
# ==========================================
def construir_prompt(frag, ids_p, grafo, operacoes, erros=None):
    # Injetamos as definições no prompt para a IA não errar o nível
    contexto = "\n".join([f"- {i}: {grafo[i]['definicao']} (Nível {grafo[i]['nivel']})" for i in ids_p if i in grafo])
    
    instrucao = "AGE COMO COMPILADOR ONTOLÓGICO RÍGIDO."
    if erros: instrucao = f"CORRIGE O JSON ANTERIOR. ERROS: {erros}"

    return f"""
{instrucao}

REGRAS:
1. Responde APENAS JSON puro.
2. campo_principal TEM de ser um dos IDs permitidos abaixo.
3. O 'nivel' TEM de ser exatamente o nível indicado na lista abaixo.

IDs PERMITIDOS (Whitelist):
{contexto}

OPERAÇÕES DISPONÍVEIS:
{operacoes}

FRAGMENTO PARA EXTRAÇÃO:
{frag}

ESQUEMA OBRIGATÓRIO:
{{
  "id_proposicao": "PXXXX",
  "texto_literal": "...",
  "localizacao_vertical": {{ "nivel": N, "campo_principal": "ID", "campos_secundarios": [] }},
  "operacao_ontologica": "OP1; OP2",
  "dependencias": [], "gera": [], "degeneracao_possivel": [], "reintegracao": [],
  "grau_de_integracao": {{ "nivel": 1, "descricao": "..." }}
}}
""".strip()

# ==========================================
# 6) LOOP DE PROCESSAMENTO (COM FILTRO DE ÍNDICE)
# ==========================================
def processar():
    print("\n" + "="*60)
    print("      COMPILADOR ONTOLÓGICO v3.2 - MODO ÍNDICE")
    print("="*60)

    grafo, operacoes, vetores = carregar_ecossistema()
    os.makedirs(os.path.dirname(FICHEIRO_SAIDA), exist_ok=True)

    # 6.1 - Extração seletiva dos fragmentos do ficheiro
    with open(FICHEIRO_MANUSCRITO, "r", encoding="utf-8") as f:
        conteudo = f.read()
        fragmentos_raw = conteudo.split("----------")
        fragmentos_limpos = []
        for fr in fragmentos_raw:
            fr = fr.strip()
            # Só processa se contiver o padrão de ID da proposição
            if re.search(r"ID:\s*P\d+", fr):
                fragmentos_limpos.append(fr)

    if LIMITE_FRAGMENTOS_TESTE: fragmentos_limpos = fragmentos_limpos[:LIMITE_FRAGMENTOS_TESTE]
    
    print(f"Total de fragmentos válidos detetados: {len(fragmentos_limpos)}")

    resultados = []
    for i, frag in enumerate(fragmentos_limpos, 1):
        # Extrair o ID PXXXX para o Log
        id_match = re.search(r"ID:\s*(P\d+)", frag)
        p_id = id_match.group(1) if id_match else f"PROG_{i}"
        
        print(f"\n▶ [{i}/{len(fragmentos_limpos)}] Processando Proposição {p_id}...")
        
        # Vetorial e Expansão
        ids_v = buscar_candidatos(frag, vetores)
        ids_p = expandir_ids(ids_v, grafo)
        
        tentativas, sucesso = 0, False
        prompt = construir_prompt(frag, ids_p, grafo, operacoes)

        while tentativas < 3 and not sucesso:
            try:
                response = client.models.generate_content(model=MODELO_RACIOCINIO, contents=prompt)
                corpo_json = limpar_json(response.text)
                ficha = json.loads(corpo_json)
                
                # Garantir que o ID da proposição é o correto do texto
                ficha["id_proposicao"] = p_id
                
                erros = validar_ficha(ficha, grafo, operacoes, set(ids_p))
                
                if not erros:
                    cp = ficha['localizacao_vertical']['campo_principal']
                    print(f"  ⚡ IA ESCOLHEU: [{cp}] | Nível: {ficha['localizacao_vertical']['nivel']}")
                    print(f"  🛠 OPERAÇÃO: {ficha['operacao_ontologica']}")
                    resultados.append(ficha)
                    sucesso = True
                    print("  ✅ VALIDADO COM SUCESSO.")
                else:
                    print(f"  ⚠ FALHA NA VALIDAÇÃO: {erros}")
                    prompt = construir_prompt(frag, ids_p, grafo, operacoes, erros=erros)
                    tentativas += 1
            except Exception as e:
                print(f"  ❌ ERRO TÉCNICO NO FRAGMENTO {p_id}: {e}")
                break
            time.sleep(PAUSA_ENTRE_CHAMADAS)

        # Gravação Incremental
        with open(FICHEIRO_SAIDA, "w", encoding="utf-8") as f_out:
            json.dump(resultados, f_out, ensure_ascii=False, indent=2)

    print(f"\n" + "="*60)
    print(f"PROCESSAMENTO CONCLUÍDO. Resultados em: {FICHEIRO_SAIDA}")
    print("="*60)

if __name__ == "__main__":
    processar()