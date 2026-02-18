import json
import re
import hashlib
import copy
import difflib
from collections import defaultdict

# ==================================================
# CONFIG
# ==================================================

HASH_METHOD = "sha256"
EXCLUDED_FIELDS = {"id_proposicao", "texto_literal", "_vinculacao_textual"}
EXTRACTOR_VERSION = "v1.1"

# para remapeamento por "quase igual"
ENABLE_FUZZY_REMAP = True
FUZZY_THRESHOLD = 0.985  # ajusta se quiseres (0.99 mais exigente)

# ==================================================
# UTIL
# ==================================================

def extract_id_text(line):
    m = re.search(r"ID:\s*(P\d+)\s*\|\s*(.+)", line)
    if not m:
        return None
    return m.group(1), m.group(2).strip()

def stable_hash(obj):
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def similarity(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

def normalize_text(s: str) -> str:
    # normalização leve (não destrutiva) para matching por espaços/pontuação
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s

# ==================================================
# 1. LER TXT CANÓNICO
# ==================================================

def load_txt(path):
    txt_map = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parsed = extract_id_text(line)
            if parsed:
                pid, text = parsed
                txt_map[pid] = text
    return txt_map

def build_txt_indexes(txt_map):
    """
    Índices para matching por texto:
    - exact (texto literal)
    - normalized exact (espaços)
    """
    exact = {}
    norm = {}
    for pid, text in txt_map.items():
        exact[text] = pid
        norm[normalize_text(text)] = pid
    return exact, norm

# ==================================================
# 2. LER JSON RICO
# ==================================================

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# ==================================================
# 3. RECONSTRUIR + REMAPEAR
# ==================================================

def rebuild_and_remap(json_data, txt_map):
    txt_exact, txt_norm = build_txt_indexes(txt_map)

    rebuilt = []
    discarded = []             # objectos descartados (sem encaixe)
    remapped = []              # (id_origem, id_destino, motivo, score)

    for obj in json_data:
        if not isinstance(obj, dict):
            discarded.append({"id": None, "reason": "objeto_json_nao_dict"})
            continue

        pid = obj.get("id_proposicao")
        texto_obj = obj.get("texto_literal", "")
        texto_obj = "" if texto_obj is None else str(texto_obj)

        # Caso 1: ID existe no TXT -> fixar texto literal do TXT
        if pid in txt_map:
            obj_new = copy.deepcopy(obj)
            obj_new["texto_literal"] = txt_map[pid]
            rebuilt.append(obj_new)
            continue

        # Caso 2: ID não existe no TXT -> tentar remapear por texto exacto
        if texto_obj in txt_exact:
            target = txt_exact[texto_obj]
            obj_new = copy.deepcopy(obj)
            obj_new["id_proposicao"] = target
            obj_new["texto_literal"] = txt_map[target]
            rebuilt.append(obj_new)
            remapped.append((pid, target, "texto_exacto", 1.0))
            continue

        # Caso 3: tentar remapear por texto normalizado (espaços/pontuação simples)
        norm_obj = normalize_text(texto_obj)
        if norm_obj in txt_norm:
            target = txt_norm[norm_obj]
            obj_new = copy.deepcopy(obj)
            obj_new["id_proposicao"] = target
            obj_new["texto_literal"] = txt_map[target]
            rebuilt.append(obj_new)
            remapped.append((pid, target, "texto_normalizado", 1.0))
            continue

        # Caso 4: fuzzy remap (quase igual)
        if ENABLE_FUZZY_REMAP and texto_obj.strip():
            best_pid = None
            best_score = 0.0

            # nota: isto é O(n) por objecto; para 1k está ok
            for tpid, ttxt in txt_map.items():
                sc = similarity(normalize_text(texto_obj), normalize_text(ttxt))
                if sc > best_score:
                    best_score = sc
                    best_pid = tpid

            if best_pid and best_score >= FUZZY_THRESHOLD:
                obj_new = copy.deepcopy(obj)
                obj_new["id_proposicao"] = best_pid
                obj_new["texto_literal"] = txt_map[best_pid]
                rebuilt.append(obj_new)
                remapped.append((pid, best_pid, "fuzzy", best_score))
                continue

        # Caso 5: sem encaixe -> descartar
        discarded.append({
            "id": pid,
            "reason": "id_nao_existe_e_texto_nao_mapeia",
            "texto_snippet": texto_obj[:120]
        })

    return rebuilt, discarded, remapped

# ==================================================
# 4. DEDUPLICAÇÃO POR ID (mantém 1 objecto por ID)
# ==================================================

def attach_hashes(obj):
    obj2 = copy.deepcopy(obj)

    atributos = {k: v for k, v in obj2.items() if k not in EXCLUDED_FIELDS}

    obj2["_vinculacao_textual"] = {
        "hash_texto": stable_hash(obj2.get("texto_literal", "")),
        "hash_atributos": stable_hash(atributos),
        "metodo": HASH_METHOD,
        "versao_extractor": EXTRACTOR_VERSION
    }
    return obj2

def dedupe_by_id(objects, txt_map):
    groups = defaultdict(list)
    for obj in objects:
        pid = obj.get("id_proposicao")
        groups[pid].append(obj)

    final = []
    removed_dupes = []  # lista detalhada de removidos

    for pid, group in groups.items():
        if pid is None:
            # objectos sem id -> remover todos
            for o in group:
                removed_dupes.append({
                    "id": None,
                    "reason": "sem_id_proposicao"
                })
            continue

        if len(group) == 1:
            final.append(attach_hashes(group[0]))
            continue

        # escolher o "melhor" objecto a manter:
        # como o texto literal vai ser forçado ao TXT, a escolha é por completude de atributos
        # (mais campos preenchidos) como critério estável.
        def score_obj(o):
            # conta campos não vazios (excluindo id/texto/vinculação)
            score = 0
            for k, v in o.items():
                if k in EXCLUDED_FIELDS:
                    continue
                if v is None:
                    continue
                if isinstance(v, (list, dict, str)) and len(v) == 0:
                    continue
                score += 1
            return score

        best = max(group, key=score_obj)

        # aplicar texto canónico se existir no TXT
        if pid in txt_map:
            best = copy.deepcopy(best)
            best["texto_literal"] = txt_map[pid]

        final.append(attach_hashes(best))

        for o in group:
            if o is best:
                continue
            removed_dupes.append({
                "id": pid,
                "reason": "duplicado_mesmo_id",
                "kept_score": score_obj(best),
                "removed_score": score_obj(o)
            })

    return final, removed_dupes

# ==================================================
# 5. VERIFICAÇÃO FINAL BULLETPROOF
# ==================================================

def verify(final, txt_map):
    report = []
    errors = 0

    ids = [o.get("id_proposicao") for o in final]
    textos = [o.get("texto_literal") for o in final]

    report.append("VERIFICAÇÃO FINAL BULLETPROOF\n")
    report.append(f"Objetos JSON     : {len(final)}")
    report.append(f"IDs distintos    : {len(set(ids))}")
    report.append(f"Textos distintos : {len(set(textos))}")

    if len(ids) != len(set(ids)):
        raise RuntimeError("ERRO: IDs duplicados persistem")

    if len(textos) != len(set(textos)):
        raise RuntimeError("ERRO: textos duplicados persistem")

    for obj in final:
        pid = obj["id_proposicao"]
        texto = obj["texto_literal"]

        if pid not in txt_map:
            report.append(f"[ERRO] ID final não existe no TXT: {pid}")
            errors += 1
            continue

        if texto != txt_map[pid]:
            report.append(f"[ERRO] Texto divergente no ID {pid}")
            errors += 1

        atributos = {k: v for k, v in obj.items() if k not in EXCLUDED_FIELDS}
        vinc = obj.get("_vinculacao_textual", {})

        if vinc.get("hash_texto") != stable_hash(texto):
            report.append(f"[ERRO] Hash de texto inválido no ID {pid}")
            errors += 1

        if vinc.get("hash_atributos") != stable_hash(atributos):
            report.append(f"[ERRO] Hash de atributos inválido no ID {pid}")
            errors += 1

    if errors == 0:
        report.append("JSON BULLETPROOF: atributos formalmente vinculados ao texto")

    return report

# ==================================================
# 6. EXECUÇÃO
# ==================================================

TXT_PATH = "06_01Texto_No_Indice_TXT.CORRIGIDO.txt"
JSON_IN = "extracao_ontologica_final.json"
JSON_OUT = "extracao_ontologica_final.RECONSTRUIDO.json"
REPORT_OUT = "relatorio_reconstrucao_json.txt"

txt_map = load_txt(TXT_PATH)
json_data = load_json(JSON_IN)

rebuilt, discarded, remapped = rebuild_and_remap(json_data, txt_map)
final, removed_dupes = dedupe_by_id(rebuilt, txt_map)

report = verify(final, txt_map)

with open(JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

with open(REPORT_OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(report))

    f.write("\n\nREMAPEAMENTOS (ID_ORIGEM → ID_DESTINO):\n")
    if not remapped:
        f.write("- (nenhum)\n")
    else:
        for (src, dst, reason, score) in remapped:
            f.write(f"- {src} -> {dst} | {reason} | score={score:.6f}\n")

    f.write("\n\nDUPLICADOS REMOVIDOS (por ID):\n")
    if not removed_dupes:
        f.write("- (nenhum)\n")
    else:
        # resumo por id
        count_by_id = defaultdict(int)
        for r in removed_dupes:
            count_by_id[r["id"]] += 1
        for pid in sorted(count_by_id.keys(), key=lambda x: (x is None, x)):
            f.write(f"- {pid}: removidos={count_by_id[pid]}\n")

    f.write("\n\nDESCARTADOS (sem encaixe no TXT):\n")
    if not discarded:
        f.write("- (nenhum)\n")
    else:
        for d in discarded:
            f.write(f"- {d.get('id')} | {d.get('reason')} | {d.get('texto_snippet','')}\n")

print("JSON BULLETPROOF reconstruído com sucesso.")
print(f"- {JSON_OUT}")
print(f"- {REPORT_OUT}")
