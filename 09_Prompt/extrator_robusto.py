# extrator_robusto.py
# Compilador Ontológico Formal v3.2
# SDK alinhado com google.genai (2026-safe)

from google import genai
import json
import time
import re
import os
import numpy as np
from dotenv import load_dotenv
import hashlib

# ==========================================
# 0) CONFIGURAÇÃO
# ==========================================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY não encontrado no .env")

client = genai.Client(api_key=API_KEY)

MODELO_RACIOCINIO = "models/gemini-2.5-flash"
MODELO_EMBEDDING = "models/gemini-embedding-001"

FICHEIRO_MANUSCRITO = "data/06_01Texto_No_Indice_TXT.txt"
FICHEIRO_SAIDA = "data/extracao_ontologica_final.json"
FICHEIRO_FALHADOS = "data/falhados.json"

LIMITE_FRAGMENTOS_TESTE = None      # None para tudo
PAUSA_ENTRE_CHAMADAS = 1.2


# ==========================================
# 1) UTILITÁRIOS
# ==========================================
def limpar_json(texto: str) -> str:
    texto = re.sub(r"```(?:json)?\s*|\s*```", "", texto).strip()
    match = re.search(r"(\{.*\})", texto, re.DOTALL)
    return match.group(1) if match else texto


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
    return float(np.dot(a, b) / denom)


# ==========================================
# 2) CARREGAR IDS JÁ TRATADOS
# ==========================================
def carregar_ids_ignorados():
    ids = set()

    def carregar_ids_de_ficheiro(caminho):
        if not os.path.exists(caminho):
            return set()
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if not isinstance(dados, list):
                return set()
            return {
                d["id_proposicao"]
                for d in dados
                if isinstance(d, dict) and isinstance(d.get("id_proposicao"), str)
            }
        except Exception:
            return set()

    ids |= carregar_ids_de_ficheiro(FICHEIRO_SAIDA)
    ids |= carregar_ids_de_ficheiro(FICHEIRO_FALHADOS)

    return ids



# ==========================================
# 3) ECOSSISTEMA
# ==========================================
def carregar_ecossistema():
    with open("config/definicoes.json", "r", encoding="utf-8") as f:
        defs = json.load(f)
    with open("config/operacoes.json", "r", encoding="utf-8") as f:
        ops = json.load(f)
    with open("config/vetores_definicoes.json", "r", encoding="utf-8") as f:
        vetores = json.load(f)

    campo_para_id = {
        d["campo"]: d["id"]
        for d in defs
        if d.get("campo") and d.get("id")
    }

    for d in defs:
        d["depende_de"] = [campo_para_id.get(x, x) for x in d.get("depende_de", [])]
        d["exclui"] = [campo_para_id.get(x, x) for x in d.get("exclui", [])]

    grafo = {d["id"]: d for d in defs}
    return grafo, ops, vetores


# ==========================================
# 4) BUSCA VETORIAL
# ==========================================
def preparar_fragmento_para_embedding(frag: str) -> str:
    linhas = []
    for linha in frag.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        if linha.startswith(("ID:", "TAX:", "---", "===")):
            continue
        linhas.append(linha)
    return " ".join(linhas)


def buscar_candidatos(texto_frag, base_vetorial, top_n=6):
    texto_limpo = preparar_fragmento_para_embedding(texto_frag)

    response = client.models.embed_content(
        model=MODELO_EMBEDDING,
        contents=texto_limpo
    )

    v_frag = np.array(response.embeddings[0].values, dtype=np.float32)

    sims = []
    for item in base_vetorial:
        v_def = np.array(item["vetor"], dtype=np.float32)
        sims.append((item["id"], cosine_sim(v_frag, v_def)))

    sims.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in sims[:top_n]]


def expandir_ids(ids_candidatos, grafo):
    permitidos = set(ids_candidatos)
    for _ in range(2):
        novos = {
            dep
            for i in list(permitidos)
            if i in grafo
            for dep in grafo[i].get("depende_de", [])
            if dep in grafo
        }
        permitidos |= novos
    return sorted(permitidos)

def extrair_texto_literal(fr: str):
    """
    Extrai (id, texto_literal) a partir de uma linha do tipo:
    [n] ID: PXXXX | texto...
    """
    for linha in fr.splitlines():
        m = re.match(r"\[\d+\]\s+ID:\s*(P\d+)\s*\|\s*(.+)", linha)
        if m:
            return m.group(1), m.group(2)
    return None, None


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

# ==========================================
# 5) VALIDAÇÃO
# ==========================================
def validar_ficha(ficha, grafo, operacoes_validas, ids_permitidos):
    if isinstance(ficha, list) and ficha:
        ficha = ficha[0]
    if not isinstance(ficha, dict):
        return ["Resposta da IA não é JSON válido."]

    erros = []
    lv = ficha.get("localizacao_vertical", {})
    cp = lv.get("campo_principal")

    usados = (
        [cp]
        + lv.get("campos_secundarios", [])
        + ficha.get("dependencias", [])
        + ficha.get("gera", [])
    )

    for x in usados:
        if x and x not in grafo:
            erros.append(f"ID inexistente: {x}")
        elif x and x not in ids_permitidos:
            erros.append(f"ID fora da whitelist: {x}")

    try:
        n_decl = int(lv.get("nivel", -1))
        if cp in grafo and int(grafo[cp]["nivel"]) != n_decl:
            erros.append(f"Incoerência de nível em {cp}.")
    except Exception:
        erros.append("Nível inválido.")

    op_raw = ficha.get("operacao_ontologica", "")
    partes = [p.strip() for p in re.split(r"[;,\n]+", op_raw) if p.strip()]
    for p in partes:
        if p not in operacoes_validas:
            erros.append(f"Operação inválida: {p}")
    if not partes:
        erros.append("Operação ausente.")
    ficha["operacao_ontologica"] = partes

    if cp in grafo:
        deps_obrig = set(grafo[cp].get("depende_de", []))
        deps_decl = set(ficha.get("dependencias", []))

        # Explicitação forçada
        faltam = deps_obrig - deps_decl
        if faltam:
            ficha.setdefault("dependencias", [])
            ficha["dependencias"] = sorted(
                set(ficha.get("dependencias", [])) | faltam
            )

            # Revalidação defensiva
            if deps_obrig - set(ficha.get("dependencias", [])):
                erros.append(f"Faltam dependências para {cp}: {list(faltam)}")

    return erros


# ==========================================
# 6) PROMPT
# ==========================================
def construir_prompt(frag, ids_p, grafo, operacoes, erros=None):
    contexto = "\n".join(
        f"- {i}: {grafo[i]['definicao']} (Nível {grafo[i]['nivel']})"
        for i in ids_p if i in grafo
    )

    instrucao = "AGE COMO COMPILADOR ONTOLÓGICO RÍGIDO."
    if erros:
        instrucao = f"CORRIGE O JSON ANTERIOR. ERROS: {erros}"

    return f"""
{instrucao}

REGRAS:
1. Responde APENAS JSON puro.
2. campo_principal TEM de ser um dos IDs permitidos.
3. O nível TEM de coincidir exatamente.
4. Se o campo_principal tiver dependências ontológicas, estas devem constar explicitamente no campo "dependencias".


IDs PERMITIDOS:
{contexto}

OPERAÇÕES:
{operacoes}

FRAGMENTO:
{frag}

ESQUEMA:
{{
  "id_proposicao": "PXXXX",
  "texto_literal": "(preenchido automaticamente pelo sistema)",
  "localizacao_vertical": {{ "nivel": N, "campo_principal": "ID", "campos_secundarios": [] }},
  "operacao_ontologica": "OP1; OP2",
  "dependencias": [],
  "gera": [],
  "degeneracao_possivel": [],
  "reintegracao": [],
  "grau_de_integracao": {{ "nivel": 1, "descricao": "..." }}
}}
""".strip()


# ==========================================
# 7) REGISTO DE FALHAS
# ==========================================
def registar_falha(p_id, frag, erro):
    os.makedirs(os.path.dirname(FICHEIRO_FALHADOS), exist_ok=True)

    entrada = {
        "id_proposicao": p_id,
        "erro": str(erro),
        "fragmento": frag,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    dados = []
    if os.path.exists(FICHEIRO_FALHADOS):
        try:
            with open(FICHEIRO_FALHADOS, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if not isinstance(dados, list):
                dados = []
        except Exception:
            dados = []


    dados.append(entrada)

    with open(FICHEIRO_FALHADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


# ==========================================
# 8) LOOP PRINCIPAL
# ==========================================
def processar():
    print("=" * 60)
    print(" COMPILADOR ONTOLÓGICO v3.2")
    print("=" * 60)

    # 1) Inicialização de Contadores de Consumo
    total_input_tokens = 0
    total_output_tokens = 0

    ids_ignorados = carregar_ids_ignorados()
    if ids_ignorados:
        print(f"⏭️  A ignorar {len(ids_ignorados)} proposições já tratadas.")

    grafo, operacoes, vetores = carregar_ecossistema()
    os.makedirs(os.path.dirname(FICHEIRO_SAIDA), exist_ok=True)

    # 2) Carregamento de Fragmentos
    fragmentos = []
    txt_map = {}
    if not os.path.exists(FICHEIRO_MANUSCRITO):
        print(f"❌ Erro: Ficheiro {FICHEIRO_MANUSCRITO} não encontrado.")
        return

    with open(FICHEIRO_MANUSCRITO, "r", encoding="utf-8") as f:
        conteudo = f.read()

    for bloco in conteudo.split("----------"):
        bloco = bloco.strip()
        if not bloco:
            continue

        pid, texto = extrair_texto_literal(bloco)
        if not pid:
            continue

        # fonte canónica: 1 ID → 1 texto
        if pid not in txt_map:
            txt_map[pid] = texto

        if pid in ids_ignorados:
            continue

        fragmentos.append(bloco)

    if LIMITE_FRAGMENTOS_TESTE:
        print(f"🧪 Modo Teste Ativo: limitado a {LIMITE_FRAGMENTOS_TESTE} fragmentos.")
        fragmentos = fragmentos[:LIMITE_FRAGMENTOS_TESTE]

    resultados_map = {}
    if os.path.exists(FICHEIRO_SAIDA):
        try:
            with open(FICHEIRO_SAIDA, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, list):
                for d in dados:
                    if isinstance(d, dict) and isinstance(d.get("id_proposicao"), str):
                        resultados_map[d["id_proposicao"]] = d
        except:
            resultados_map = {}

    # 3) Loop de Processamento
    for i, frag in enumerate(fragmentos, 1):
        p_id = re.search(r"ID:\s*(P\d+)", frag).group(1)
        print(f"\n▶ [{i}/{len(fragmentos)}] {p_id}")

        ids_v = buscar_candidatos(frag, vetores)
        ids_p = expandir_ids(ids_v, grafo)

        prompt = construir_prompt(frag, ids_p, grafo, operacoes)
        tentativas = 0

        while tentativas < 3:
            try:
                # Chamada à API
                response = client.models.generate_content(
                    model=MODELO_RACIOCINIO,
                    contents=prompt
                )

                # Registo imediato de metadados (custo)
                meta = response.usage_metadata
                total_input_tokens += meta.prompt_token_count
                total_output_tokens += meta.candidates_token_count
                
                print(f"   [Tokens] In: {meta.prompt_token_count} | Out: {meta.candidates_token_count}")

                # Tratamento da Resposta
                texto_limpo = limpar_json(response.text)
                ficha = json.loads(texto_limpo)

                # --- FIXAÇÃO CANÓNICA ---
                ficha["id_proposicao"] = p_id
                ficha["texto_literal"] = txt_map[p_id]   # ← OBRIGATÓRIO

                # --- VALIDAÇÃO RÍGIDA ---
                erros = validar_ficha(ficha, grafo, operacoes, set(ids_p))
                if not erros:

                    # --- VINCULAÇÃO TEXTUAL (AQUI) ---
                    ficha["_vinculacao_textual"] = {
                        "hash_texto": sha256(ficha["texto_literal"]),
                        "hash_atributos": sha256(
                            json.dumps(
                                {
                                    k: v
                                    for k, v in ficha.items()
                                    if k not in ("texto_literal", "_vinculacao_textual")
                                },
                                ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":")
                            )
                        ),
                        "metodo": "sha256(texto)+sha256(atributos)",
                        "versao_extractor": "3.2-canonic"
                    }

                    resultados_map[p_id] = ficha
                    print("   ✅ Validado e Guardado")
                    break

                
                # Se houver erros, o prompt é reconstruído para a próxima tentativa
                print(f"   ⚠️ Erros de validação (Tentativa {tentativas+1}): {erros}")
                prompt = construir_prompt(frag, ids_p, grafo, operacoes, erros)
                tentativas += 1

            except Exception as e:
                print(f"   ❌ Erro técnico em {p_id}: {e}")
                registar_falha(p_id, frag, e)
                break

            time.sleep(PAUSA_ENTRE_CHAMADAS)

        # Gravação incremental (segurança contra quebras de energia/net)
        with open(FICHEIRO_SAIDA, "w", encoding="utf-8") as f_out:
            json.dump(list(resultados_map.values()), f_out, ensure_ascii=False, indent=2)

    # 4) Resumo Final de Custos e Execução
    print("\n" + "=" * 60)
    print(" 📊 RESUMO DE CONSUMO E CUSTOS")
    print("-" * 60)
    print(f"Total Tokens Entrada: {total_input_tokens:,}")
    print(f"Total Tokens Saída:   {total_output_tokens:,}")
    
    # Estimativa de custos (Baseada em Gemini 2.5 Pro - Fev 2026)
    # Preços aprox: $1.25/1M In | $10.00/1M Out (convertido para EUR)
    custo_est_eur = ((total_input_tokens / 1_000_000) * 1.15) + ((total_output_tokens / 1_000_000 * 9.30))
    
    print(f"Custo Estimado da Sessão: €{custo_est_eur:.2f}")
    
    if os.path.exists(FICHEIRO_FALHADOS):
        print(f"⚠️ Atenção: Verifica os erros em {FICHEIRO_FALHADOS}")

    print(f"Concluído com sucesso → {FICHEIRO_SAIDA}")
    print("=" * 60)


if __name__ == "__main__":
    processar()