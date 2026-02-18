import json
import re
from collections import defaultdict
from difflib import SequenceMatcher

# --------------------------------------------------
# Util
# --------------------------------------------------

def id_num(pid):
    return int(re.search(r"\d+", pid).group())

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
    entries = []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        for obj in data:
            if "id_proposicao" in obj and "texto_literal" in obj:
                entries.append((obj["id_proposicao"], obj["texto_literal"].strip()))
    return entries

# --------------------------------------------------
# Verificação
# --------------------------------------------------

def verify(txt_map, json_entries):
    report = defaultdict(list)

    txt_texts = list(txt_map.values())
    txt_norm_map = {pid: normalize_light(t) for pid, t in txt_map.items()}

    for jid, jtext in json_entries:
        jtext_norm = normalize_light(jtext)

        # Caso A — ID existe no TXT
        if jid in txt_map:
            ttext = txt_map[jid]
            ttext_norm = txt_norm_map[jid]

            if jtext == ttext:
                report["OK_LITERAL"].append(jid)
            elif jtext_norm == ttext_norm:
                report["DIF_ESPACOS_PONT"].append((jid, jtext, ttext))
            else:
                sim = similarity(jtext_norm, ttext_norm)
                if sim >= 0.95:
                    report["QUASE_IGUAL"].append((jid, sim, jtext, ttext))
                elif jtext_norm in ttext_norm or ttext_norm in jtext_norm:
                    report["SUBTEXTO"].append((jid, jtext, ttext))
                else:
                    report["ERRO_ID_TEXTO_DIF"].append((jid, jtext, ttext))

        # Caso B — ID não existe no TXT
        else:
            matched = False
            for pid, ttext in txt_map.items():
                sim = similarity(jtext_norm, normalize_light(ttext))
                if sim >= 0.95:
                    report["ID_ERRADO_TEXTO_EXISTE"].append((jid, pid, sim, jtext))
                    matched = True
                    break
            if not matched:
                report["TEXTO_NOVO_JSON"].append((jid, jtext))

    return report

# --------------------------------------------------
# Escrita de relatório
# --------------------------------------------------

def write_report(report, path):
    with open(path, "w", encoding="utf-8") as f:
        for sec, items in report.items():
            f.write("\n" + "="*90 + "\n")
            f.write(sec + "\n")
            f.write("="*90 + "\n")
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

txt_map = load_txt("06_01Texto_No_Indice_TXT.CORRIGIDO.txt")
json_entries = load_json("extracao_ontologica_final.json")

report = verify(txt_map, json_entries)
write_report(report, "relatorio_verificacao_json_vs_txt.txt")

print("Relatório gerado: relatorio_verificacao_json_vs_txt.txt")
