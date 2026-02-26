# estatisticas_engracadas.py
# Extra stats "engraçadas" (standalone) para proposicoes_normalizadas.json
# Não mexe no normalizador — apenas lê e analisa.

import json
import os
import re
import math
import random
from collections import Counter, defaultdict
from statistics import mean, median, pstdev

# =========================
# CONFIG
# =========================
BASE_DIR = r"C:\Users\vanes\DoReal_Casa_Local\DoReal\13_Meta_Indice"

PATH_PROPOSICOES = os.path.join(BASE_DIR, "dados_base", "proposicoes_normalizadas.json")
PATH_INDICE = os.path.join(BASE_DIR, "dados_base", "indice_conceitos.json")
PATH_OPS = os.path.join(BASE_DIR, "dados_base", "operacoes.json")
PATH_META = os.path.join(BASE_DIR, "meta", "meta_indice.json")

# opcional: grava relatório
PATH_OUT_REPORT = os.path.join(BASE_DIR, "dados_base", "relatorio_estatisticas_engracadas.json")

TOP = 20
TOP_BIG = 35
SEED = 42
SAVE_REPORT = True

# =========================
# Helpers logs visuais
# =========================
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"

def head(msg): print(f"\n{C.BOLD}{msg}{C.RESET}")
def info(msg): print(f"{C.CYAN}ℹ️ {msg}{C.RESET}")
def ok(msg):   print(f"{C.GREEN}✔️ {msg}{C.RESET}")
def warn(msg): print(f"{C.YELLOW}⚠️ {msg}{C.RESET}")
def err(msg):  print(f"{C.RED}❌ {msg}{C.RESET}")

def snip(s: str, n=160):
    s = (s or "").strip().replace("\n", " ")
    s = re.sub(r"\s+", " ", s)
    return (s[:n] + "…") if len(s) > n else s

def bar(v, vmax, width=26):
    if vmax <= 0: return ""
    k = int(round((v / vmax) * width))
    return "█" * k

def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def entropy(counter: Counter) -> float:
    # Shannon entropy (base 2)
    total = sum(counter.values())
    if total <= 0: return 0.0
    ent = 0.0
    for v in counter.values():
        p = v / total
        if p > 0:
            ent -= p * math.log(p, 2)
    return ent

def signature_regimes(regs: list[str]) -> str:
    regs = sorted(set(regs or []))
    return "|".join(regs) if regs else "SEM_REGIME"

def density_score(p: dict) -> float:
    lv = p.get("localizacao_vertical", {}) or {}
    ops = p.get("operacao_ontologica", []) or []
    deps = p.get("dependencias", []) or []
    secs = lv.get("campos_secundarios", []) or []
    txt = p.get("texto_literal", "") or ""

    # score: pondera "estrutura" (ops/deps/sec) e um pouco o texto (log)
    return (
        2.0 * len(ops)
        + 1.6 * len(deps)
        + 1.2 * len(secs)
        + 0.35 * math.log(1 + len(txt), 2)
    )

def main():
    propos = load_json(PATH_PROPOSICOES)
    indice = load_json(PATH_INDICE, default={}) or {}
    ops_db = load_json(PATH_OPS, default={}) or {}
    meta = load_json(PATH_META, default={}) or {}
    regimes = meta.get("meta_indice", {}).get("regimes", {}) or {}

    if propos is None or not isinstance(propos, list):
        return err(f"Falta ou formato inválido: {PATH_PROPOSICOES}")

    total = len(propos)
    random.seed(SEED)

    # =========================
    # Coletores
    # =========================
    pair_cp_sec = Counter()
    pair_sec_sec = Counter()
    tri_ops = Counter()
    pair_ops = Counter()

    op_degree = Counter()  # "sociabilidade": quantas co-ocorrências (com peso)
    op_with = defaultdict(Counter)

    concept_as_secondary_in_fields = defaultdict(set)  # conceito secundário -> set de campos principais
    concept_sec_count = Counter()
    concept_cp_count = Counter()

    regimes_by_concept = defaultdict(Counter)  # campo_principal -> contagem por regime_principal
    signature_counts = Counter()
    cp_by_signature = defaultdict(Counter)

    lens = []
    by_regime_len = defaultdict(list)

    # regime principal -> top campos principais
    cp_by_regime = defaultdict(Counter)

    scored = []  # (score, pid, p)

    for p in propos:
        pid = p.get("id_proposicao")
        lv = p.get("localizacao_vertical", {}) or {}
        cp = lv.get("campo_principal")
        secs = list(dict.fromkeys(lv.get("campos_secundarios", []) or []))
        ops = list(dict.fromkeys(p.get("operacao_ontologica", []) or []))

        rp = p.get("regime_principal") or "SEM_REGIME"
        regs = p.get("regimes_detectados", []) or []
        sig = signature_regimes(regs)

        txt = p.get("texto_literal", "") or ""
        L = len(txt)
        lens.append(L)
        by_regime_len[rp].append(L)

        signature_counts[sig] += 1
        if cp:
            cp_by_signature[sig][cp] += 1
            cp_by_regime[rp][cp] += 1
            concept_cp_count[cp] += 1
            regimes_by_concept[cp][rp] += 1

        # cp x sec
        if cp:
            for s in secs:
                pair_cp_sec[(cp, s)] += 1
                concept_as_secondary_in_fields[s].add(cp)
                concept_sec_count[s] += 1

        # sec x sec (co-ocorrência)
        if len(secs) >= 2:
            for i in range(len(secs)):
                for j in range(i + 1, len(secs)):
                    a, b = sorted((secs[i], secs[j]))
                    pair_sec_sec[(a, b)] += 1

        # ops co-ocorrência
        if len(ops) >= 2:
            for i in range(len(ops)):
                for j in range(i + 1, len(ops)):
                    a, b = sorted((ops[i], ops[j]))
                    pair_ops[(a, b)] += 1
                    op_degree[a] += 1
                    op_degree[b] += 1
                    op_with[a][b] += 1
                    op_with[b][a] += 1

        # tríades de ops
        if len(ops) >= 3:
            ops_sorted = sorted(ops)
            # para não explodir: só conta combinações de 3 se <= 9 ops
            if len(ops_sorted) <= 9:
                for i in range(len(ops_sorted)):
                    for j in range(i + 1, len(ops_sorted)):
                        for k in range(j + 1, len(ops_sorted)):
                            tri_ops[(ops_sorted[i], ops_sorted[j], ops_sorted[k])] += 1

        # densidade
        s = density_score(p)
        scored.append((s, pid, p))

    # =========================
    # Derivados
    # =========================
    scored.sort(key=lambda x: x[0], reverse=True)

    mu = mean(lens)
    med = median(lens)
    sd = pstdev(lens) if total > 1 else 0.0

    # outliers por comprimento
    # "muito longos": > mu + 2sd ; "muito curtos": < max(0, mu - 2sd)
    thr_hi = mu + 2 * sd
    thr_lo = max(0, mu - 2 * sd)

    long_ids = [p.get("id_proposicao") for p in propos if len((p.get("texto_literal") or "")) > thr_hi]
    short_ids = [p.get("id_proposicao") for p in propos if len((p.get("texto_literal") or "")) < thr_lo]

    # conceitos ponte: secundários que aparecem em muitos campos diferentes
    bridge = []
    for s, fields in concept_as_secondary_in_fields.items():
        bridge.append((len(fields), concept_sec_count[s], s))
    bridge.sort(reverse=True)  # por nº de campos diferentes, depois contagem

    # entropia de regimes por conceito (campo_principal)
    concept_entropy = []
    for cp, c in regimes_by_concept.items():
        concept_entropy.append((entropy(c), sum(c.values()), cp, c))
    concept_entropy.sort(reverse=True)

    # =========================
    # PRINT
    # =========================
    head("================ ESTATÍSTICAS ENGRAÇADAS ================")
    info(f"Total proposições: {total}")
    info(f"Texto (chars): média={mu:.1f} | mediana={med:.0f} | sd={sd:.1f} | hi>{thr_hi:.1f} | lo<{thr_lo:.1f}")

    # --------- pares cp x sec ----------
    head("🥪 Top pares (campo_principal × secundário)")
    top_pairs = pair_cp_sec.most_common(TOP_BIG)
    vmax = top_pairs[0][1] if top_pairs else 1
    for (cp, s), v in top_pairs[:TOP]:
        cp_nome = (indice.get(cp, {}) or {}).get("nome", "")
        s_nome = (indice.get(s, {}) or {}).get("nome", "")
        tag = ""
        if cp_nome or s_nome:
            tag = f"{C.GRAY} — {cp_nome} × {s_nome}{C.RESET}"
        print(f"  {cp:<24} × {s:<24} {v:>4}  {bar(v, vmax)}{tag}")

    # --------- pares sec x sec ----------
    head("🧷 Top pares de secundários (co-ocorrência)")
    top_ss = pair_sec_sec.most_common(TOP_BIG)
    vmax = top_ss[0][1] if top_ss else 1
    for (a, b), v in top_ss[:TOP]:
        print(f"  {a:<24} + {b:<24} {v:>4}  {bar(v, vmax)}")

    # --------- ops: pares e tríades ----------
    head("🤝 PARES de operações mais comuns")
    top_op_pairs = pair_ops.most_common(TOP_BIG)
    vmax = top_op_pairs[0][1] if top_op_pairs else 1
    for (a, b), v in top_op_pairs[:TOP]:
        print(f"  {a:<36} + {b:<36} {v:>4}  {bar(v, vmax)}")

    head("🧬 TRÍADES de operações mais comuns (limitado)")
    top_tri = tri_ops.most_common(TOP_BIG)
    vmax = top_tri[0][1] if top_tri else 1
    for (a, b, c), v in top_tri[:min(14, len(top_tri))]:
        print(f"  ({a}, {b}, {c})  {v:>4}  {bar(v, vmax)}")

    # --------- ops "sociais" ----------
    head("🕸️ Operações mais 'sociais' (mais co-ocorrências)")
    top_social = op_degree.most_common(TOP)
    vmax = top_social[0][1] if top_social else 1
    for op, v in top_social:
        desc = (ops_db.get(op, {}) or {}).get("descricao", "")
        print(f"  {op:<40} {v:>4}  {bar(v, vmax)}")
        if desc:
            print(f"      {C.GRAY}{snip(desc, 120)}{C.RESET}")

    # --------- conceito ponte ----------
    head("🌉 Conceitos 'ponte' (secundário em muitos campos principais)")
    vmax = bridge[0][0] if bridge else 1
    for n_fields, n_occ, s in bridge[:TOP]:
        print(f"  {s:<28} campos={n_fields:>2}  occ={n_occ:>4}  {bar(n_fields, vmax)}")

    # --------- entropia de regimes por conceito ----------
    head("🎛️ Conceitos com uso mais 'misturado' (entropia de regime_principal)")
    # entropia máxima com 7 regimes ~ log2(7)=2.81 (aqui tens 7 principais)
    for ent, n, cp, c in concept_entropy[:TOP]:
        top2 = ", ".join([f"{k}:{v}" for k, v in c.most_common(2)])
        print(f"  {cp:<26} ent={ent:.2f}  n={n:>3}  {C.GRAY}{top2}{C.RESET}")

    # --------- assinaturas de regimes ----------
    head("🧾 Assinaturas (regimes_detectados como 'set') mais frequentes")
    top_sig = signature_counts.most_common(TOP)
    vmax = top_sig[0][1] if top_sig else 1
    for sig, v in top_sig:
        short_sig = sig if len(sig) <= 90 else (sig[:90] + "…")
        print(f"  {short_sig:<92} {v:>4}  {bar(v, vmax)}")
        # mostra o campo_principal mais comum nesta assinatura
        top_cp = cp_by_signature[sig].most_common(1)
        if top_cp:
            print(f"      {C.GRAY}campo_principal típico: {top_cp[0][0]} ({top_cp[0][1]}){C.RESET}")

    # --------- densidade ----------
    head("🔥 Top 12 por densidade ontológica (score)")
    for s, pid, p in scored[:12]:
        lv = p.get("localizacao_vertical", {}) or {}
        cp = lv.get("campo_principal")
        rp = p.get("regime_principal")
        ops = p.get("operacao_ontologica", []) or []
        deps = p.get("dependencias", []) or []
        secs = lv.get("campos_secundarios", []) or []
        txt = p.get("texto_literal", "") or ""
        print(f"\n{C.BOLD}▶ {pid}{C.RESET}  score={s:.2f}")
        print(f"  cp={cp} | nivel={lv.get('nivel')} | regime={rp} | ops={len(ops)} deps={len(deps)} sec={len(secs)} | len={len(txt)}")
        print(f"  texto: {C.GRAY}{snip(txt, 240)}{C.RESET}")

    # --------- outliers ----------
    head("🪐 Outliers de comprimento (texto)")
    info(f"Muito longos (> média+2sd): {len(long_ids)} | Muito curtos (< média-2sd): {len(short_ids)}")
    if long_ids:
        print(f"  Longos (amostra 10): {', '.join(long_ids[:10])}" + (" …" if len(long_ids) > 10 else ""))
    if short_ids:
        print(f"  Curtos (amostra 10): {', '.join(short_ids[:10])}" + (" …" if len(short_ids) > 10 else ""))

    # --------- por regime principal: top campos ----------
    head("🧭 Por regime_principal: top 8 conceitos (campo_principal)")
    for rp, _ in sorted(cp_by_regime.items(), key=lambda x: sum(x[1].values()), reverse=True):
        c = cp_by_regime[rp]
        top = c.most_common(8)
        if not top:
            continue
        total_rp = sum(c.values())
        print(f"\n{C.BOLD}{rp}{C.RESET}  {C.GRAY}(n={total_rp}){C.RESET}")
        vmax = top[0][1]
        for cp, v in top:
            print(f"  {cp:<26} {v:>4}  {bar(v, vmax)}")

    # =========================
    # Relatório opcional
    # =========================
    if SAVE_REPORT:
        report = {
            "total": total,
            "texto_stats": {
                "media": mu,
                "mediana": med,
                "sd": sd,
                "thr_hi": thr_hi,
                "thr_lo": thr_lo,
                "n_longos": len(long_ids),
                "n_curtos": len(short_ids),
                "longos_amostra_20": long_ids[:20],
                "curtos_amostra_20": short_ids[:20],
            },
            "top_pairs_cp_sec": [
                {"cp": cp, "sec": s, "count": v}
                for (cp, s), v in pair_cp_sec.most_common(80)
            ],
            "top_pairs_sec_sec": [
                {"a": a, "b": b, "count": v}
                for (a, b), v in pair_sec_sec.most_common(80)
            ],
            "top_op_pairs": [
                {"a": a, "b": b, "count": v}
                for (a, b), v in pair_ops.most_common(80)
            ],
            "top_op_triads": [
                {"a": a, "b": b, "c": c, "count": v}
                for (a, b, c), v in tri_ops.most_common(80)
            ],
            "top_social_ops": op_degree.most_common(80),
            "bridge_concepts": [
                {"sec": s, "fields": n_fields, "occ": n_occ}
                for (n_fields, n_occ, s) in bridge[:120]
            ],
            "concept_entropy_top": [
                {"cp": cp, "entropy": ent, "n": n, "dist": dict(c)}
                for (ent, n, cp, c) in concept_entropy[:80]
            ],
            "signature_counts": signature_counts.most_common(120),
            "top_density": [
                {
                    "id": pid,
                    "score": s,
                    "cp": (p.get("localizacao_vertical", {}) or {}).get("campo_principal"),
                    "regime_principal": p.get("regime_principal"),
                }
                for s, pid, p in scored[:120]
            ],
        }
        save_json(PATH_OUT_REPORT, report)
        ok(f"Relatório JSON gravado em: {PATH_OUT_REPORT}")

    head("================ FIM ================")
    ok("Feito.")


if __name__ == "__main__":
    main()