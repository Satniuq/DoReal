import json
import re
from collections import defaultdict
from difflib import SequenceMatcher

# --------------------------------------------------
# Util
# --------------------------------------------------

def normalize_light(txt):
    txt = txt.strip().lower()
    txt = re.sub(r"\s+", " ", txt)
    txt = re.sub(r"\s+([.,;:?])", r"\1", txt)
    return txt

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# --------------------------------------------------
# Ler TXT canónico
# --------------------------------------------------

def load_txt(path):
    id_to_text = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.search(r"ID:\s*(P\d+)\s*\|\s*(.+)", line)
            if m:
                pid, text = m.group(1), m.group(2).strip()
                id_to_text[pid] = text
    return id_to_text

# --------------------------------------------------
# Ler JSON real
# --------------------------------------------------

def load_json(path):
    id_to_text = {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        for obj in data:
            if "id_proposicao" in obj and "texto_literal" in obj:
                id_to_text[obj["id_proposicao"]] = obj["texto_literal"].strip()
    return id_to_text

# --------------------------------------------------
# Validação inversa
# --------------------------------------------------

def validate_inverse(txt_map, json_map):
    report = defaultdict(list)

    json_norm_map = {jid: normalize_light(t) for jid, t in json_map.items()}

    for pid, ttext in txt_map.items():
        ttext_norm = normalize_light(ttext)

        # Caso A — ID existe no JSON
        if pid in json_map:
            jtext = json_map[pid]
            jtext_norm = json_norm_map[pid]

            if jtext == ttext:
                report["OK_LITERAL"].append(pid)
            elif jtext_norm == ttext_norm:
                report["DIF_ESPACOS_PONT"].append((pid, jtext, ttext))
            else:
                sim = similarity(jtext_norm, ttext_norm)
                if sim >= 0.95:
                    report["QUASE_IGUAL"].append((pid, sim, jtext, ttext))
                elif jtext_norm in ttext_norm or ttext_norm in jtext_norm:
                    report["SUBTEXTO"].append((pid, jtext, ttext))
                else:
                    report["ERRO_ID_TEXTO_DIF"].append((pid, jtext, ttext))

        # Caso B — ID não existe no JSON
        else:
            matched = False
            for jid, jtext in json_map.items():
                sim = similarity(ttext_norm, normalize_light(jtext))
                if sim >= 0.95:
                    report["ID_ERRADO_JSON_TEXTO_EXISTE"].append((pid, jid, sim, ttext))
                    matched = True
                    break
            if not matched:
                report["TEXTO_FALTA_NO_JSON"].append((pid, ttext))

    return report

# --------------------------------------------------
# Escrita de relatório
# --------------------------------------------------

SECOES = [
    "OK_LITERAL",
    "DIF_ESPACOS_PONT",
    "QUASE_IGUAL",
    "SUBTEXTO",
    "ERRO_ID_TEXTO_DIF",
    "ID_ERRADO_JSON_TEXTO_EXISTE",
    "TEXTO_FALTA_NO_JSON"
]

def write_report(report, path):
    with open(path, "w", encoding="utf-8") as f:
        for sec in SECOES:
            items = report.get(sec, [])
            f.write("\n" + "="*90 + "\n")
            f.write(f"{sec} ({len(items)})\n")
            f.write("="*90 + "\n")
            if not items:
                f.write("— sem ocorrências —\n")
            for item in items:
                if isinstance(item, tuple):
                    for part in item:
                        f.write(str(part) + "\n")
                    f.write("-"*40 + "\n")
                else:
                    f.write(str(item) + "\n")

# --------------------------------------------------
# Execução
# --------------------------------------------------

txt_map = load_txt("06_01Texto_No_Indice_TXT.txt")
json_map = load_json("extracao_ontologica_final.json")

report = validate_inverse(txt_map, json_map)
write_report(report, "relatorio_validacao_inversa_txt_vs_json.txt")

print("Relatório gerado: relatorio_validacao_inversa_txt_vs_json.txt")
