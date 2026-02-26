# normalizar_e_validar_proposicoes.py
# v2 — Regimes múltiplos + warnings úteis + menos spam

import json
import os
import re
import difflib
from collections import defaultdict, Counter

BASE_DIR = r"C:\Users\vanes\DoReal_Casa_Local\DoReal\13_Meta_Indice"

PATH_PROPOSICOES_IN = os.path.join(BASE_DIR, "dados_base", "proposicoes.json")
PATH_INDICE = os.path.join(BASE_DIR, "dados_base", "indice_conceitos.json")
PATH_OPS = os.path.join(BASE_DIR, "dados_base", "operacoes.json")
PATH_META = os.path.join(BASE_DIR, "meta", "meta_indice.json")

PATH_OUT = os.path.join(BASE_DIR, "dados_base", "proposicoes_normalizadas.json")
PATH_REPORT = os.path.join(BASE_DIR, "dados_base", "relatorio_proposicoes.json")

MAX_LOGS_INDIVIDUAIS = 60          # só imprime detalhes para os primeiros N casos com warning/erro
MAX_AMOSTRAS_POR_TIPO = 12         # no relatório, amostras por tipo de warning/erro


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

def ok(msg): print(f"{C.GREEN}✔️ {msg}{C.RESET}")
def warn(msg): print(f"{C.YELLOW}⚠️ {msg}{C.RESET}")
def err(msg): print(f"{C.RED}❌ {msg}{C.RESET}")
def info(msg): print(f"{C.CYAN}ℹ️ {msg}{C.RESET}")
def head(msg): print(f"\n{C.BOLD}{msg}{C.RESET}")


# =========================
# IO
# =========================
def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# Normalização OP
# =========================
PT_TO_OP = {
    "Afirmação estrutural": "OP_AFIRMACAO_ESTRUTURAL",
    "Fixação de condição ontológica": "OP_FIXACAO_CONDICAO_ONTOLOGICA",
    "Fixação de limite ontológico": "OP_FIXACAO_LIMITE_ONTOLOGICO",
    "Exclusão de exterioridade": "OP_EXCLUSAO_EXTERIORIDADE",
    "Identificação de impossibilidade ontológica": "OP_IDENTIFICACAO_IMPOSSIBILIDADE_ONTOLOGICA",

    "Recondução relacional": "OP_RECONDUCAO_RELACIONAL",
    "Descrição estrutural": "OP_DESCRICAO_ESTRUTURAL",
    "Descrição de atualização": "OP_DESCRICAO_ATUALIZACAO",
    "Descrição atualização": "OP_DESCRICAO_ATUALIZACAO",
    "Identificação de dependência": "OP_IDENTIFICACAO_DEPENDENCIA",
    "Identificação de continuidade": "OP_IDENTIFICACAO_CONTINUIDADE",
    "Identificação de regularidade": "OP_IDENTIFICACAO_REGULARIDADE",

    "Diferenciação de níveis": "OP_DIFERENCIACAO_NIVEIS",
    "Identificação de escala": "OP_IDENTIFICACAO_ESCALA",
    "Identificação de campo": "OP_IDENTIFICACAO_CAMPO",
    "Identificação de mediação": "OP_IDENTIFICACAO_MEDIACAO",

    "Dessubstancialização": "OP_DESSUBSTANCIALIZACAO",
    "Reinscrição da consciência no real": "OP_REINSCRICAO_CONSCIENCIA_REAL",
    "Reinscrição consciência real": "OP_REINSCRICAO_CONSCIENCIA_REAL",
    "Limitação da reflexividade": "OP_LIMITACAO_REFLEXIVIDADE",
    "Distinção apreensão/representação": "OP_DISTINCAO_APREENSAO_REPRESENTACAO",
    "Identificação de ponto de vista": "OP_IDENTIFICACAO_PONTO_DE_VISTA",
    "Identificação de projeção do eu": "OP_IDENTIFICACAO_PROJECAO_EU",

    "Fixação de critério": "OP_FIXACAO_CRITERIO",
    "Identificação de adequação": "OP_IDENTIFICACAO_ADEQUACAO",
    "Submissão ao real": "OP_SUBMISSAO_REAL",
    "Identificação de erro descritivo": "OP_IDENTIFICACAO_ERRO_DESCRITIVO",
    "Identificação de erro categorial": "OP_IDENTIFICACAO_ERRO_CATEGORIAL",
    "Identificação de erro escala": "OP_IDENTIFICACAO_ERRO_ESCALA",
    "Identificação de erro de escala": "OP_IDENTIFICACAO_ERRO_ESCALA",

    "Identificação de cristalização sistémica": "OP_IDENTIFICACAO_CRISTALIZACAO_SISTEMICA",
    "Identificação de degeneração": "OP_IDENTIFICACAO_DEGENERACAO",
    "Identificação de substituição do real por sistema": "OP_IDENTIFICACAO_SUBSTITUICAO_REAL_SISTEMA",
    "Crítica de fechamento simbólico": "OP_CRITICA_FECHAMENTO_SIMBOLICO",

    "Reintegração ontológica": "OP_REINTEGRACAO_ONTOLOGICA",

    # PATCH do teu relatório:
    "Derivação do dever-ser a partir do ser": "OP_DERIVACAO_DEVER_SER",
    "Subordinação do dever-ser ao poder-ser": "OP_SUBORDINACAO_DEVER_SER",
    "Identificação de dano real": "OP_IDENTIFICACAO_DANO_REAL",
}

def norm_key(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def op_guess(label: str, valid_ops: set[str]) -> str | None:
    raw = norm_key(label)
    if not raw:
        return None
    if raw in valid_ops:
        return raw
    if raw in PT_TO_OP:
        return PT_TO_OP[raw]
    close = difflib.get_close_matches(raw, list(PT_TO_OP.keys()), n=1, cutoff=0.84)
    if close:
        return PT_TO_OP[close[0]]
    return None


# =========================
# Regimes
# =========================
def build_op_to_regimes(regimes: dict) -> dict[str, list[str]]:
    op_to_regs = defaultdict(list)
    for rid, r in regimes.items():
        for op in r.get("operacoes", []):
            op_to_regs[op].append(rid)
    return dict(op_to_regs)

def detect_regimes(ops: list[str], op_to_regs: dict[str, list[str]]) -> list[str]:
    regs = set()
    for op in ops:
        for r in op_to_regs.get(op, []):
            regs.add(r)
    return sorted(regs)

def pick_regime_principal(ops: list[str], op_to_regs: dict[str, list[str]]) -> str | None:
    # conta ocorrência por regime (uma op pode pertencer a 1 regime só no teu meta_indice; se mudar, isto ainda funciona)
    c = Counter()
    for op in ops:
        regs = op_to_regs.get(op, [])
        for r in regs:
            c[r] += 1
    if not c:
        return None
    return c.most_common(1)[0][0]


# =========================
# Validação + normalização
# =========================
def validate_one(p: dict, indice: dict, ops_db: dict, regimes: dict, op_to_regs: dict):
    errors = []
    warnings = []

    pid = p.get("id_proposicao") or p.get("id")
    if not isinstance(pid, str) or not pid.strip():
        errors.append("ID ausente.")
        pid = "SEM_ID"

    txt = p.get("texto_literal") or p.get("texto") or ""
    if not isinstance(txt, str) or not txt.strip():
        warnings.append("texto_literal vazio.")

    lv = p.get("localizacao_vertical", {})
    if not isinstance(lv, dict):
        errors.append("localizacao_vertical inválida.")
        lv = {}

    nivel = lv.get("nivel")
    campo = lv.get("campo_principal")
    secund = lv.get("campos_secundarios", [])
    if not isinstance(secund, list):
        secund = []
        warnings.append("campos_secundarios inválido; normalizado para [].")

    if campo and campo not in indice:
        errors.append(f"campo_principal inexistente no índice: {campo}")

    for s in secund:
        if s not in indice:
            errors.append(f"campo_secundario inexistente no índice: {s}")

    # nivel: IGNORA o valor que vem na proposição; deriva sempre do índice
    if campo in indice:
        nivel_ind = indice[campo].get("nivel")
        if nivel_ind is None:
            warnings.append(f"conceito sem nivel no índice: {campo}")
            nivel = None
        else:
            nivel = nivel_ind
    else:
        # campo inexistente no índice já está em errors
        nivel = None

    # ops normalize
    op_list = p.get("operacao_ontologica", [])
    if isinstance(op_list, str):
        op_list = [op_list]
    if not isinstance(op_list, list):
        op_list = []
        warnings.append("operacao_ontologica inválida; normalizado para [].")

    valid_ops = set(ops_db.keys())
    ops_norm = []
    unknown_ops = []
    for item in op_list:
        if not isinstance(item, str):
            continue
        g = op_guess(item, valid_ops)
        if g and g in valid_ops:
            ops_norm.append(g)
        else:
            unknown_ops.append(item)

    ops_norm = sorted(set(ops_norm))
    if unknown_ops:
        warnings.append(f"operações desconhecidas: {unknown_ops}")

    # regimes: detecta todos + escolhe principal
    regs = detect_regimes(ops_norm, op_to_regs)
    principal = pick_regime_principal(ops_norm, op_to_regs)

    if not regs:
        warnings.append("SEM_REGIME (nenhuma operação mapeada para regimes).")
    else:
        # só warning se houver OP que não pertence a nenhum regime (deveria ser 0 se meta_indice cobre tudo)
        ops_sem_regime = [op for op in ops_norm if op not in op_to_regs]
        if ops_sem_regime:
            warnings.append(f"operações sem regime no meta_indice: {ops_sem_regime}")

    # dependências: validar existência
    deps = p.get("dependencias", [])
    if isinstance(deps, str):
        deps = [deps]
    if not isinstance(deps, list):
        deps = []
        warnings.append("dependencias inválida; normalizado para [].")
    for d in deps:
        if d not in indice:
            errors.append(f"dependencia inexistente no índice: {d}")

    out = dict(p)
    out["id_proposicao"] = pid
    out["texto_literal"] = txt
    out["localizacao_vertical"] = {
        "nivel": nivel,
        "campo_principal": campo,
        "campos_secundarios": secund
    }
    out["operacao_ontologica"] = ops_norm
    out["regimes_detectados"] = regs
    out["regime_principal"] = principal

    # (opcional) remover campo antigo "regime" se existir para evitar ambiguidade
    if "regime" in out:
        del out["regime"]

    return out, errors, warnings


def main():
    head("================ NORMALIZAR + VALIDAR PROPOSICOES (v2) ================")

    propos = load_json(PATH_PROPOSICOES_IN)
    indice = load_json(PATH_INDICE)
    ops_db = load_json(PATH_OPS)
    meta = load_json(PATH_META)

    if propos is None: return err(f"Falta {PATH_PROPOSICOES_IN}")
    if indice is None: return err(f"Falta {PATH_INDICE}")
    if ops_db is None: return err(f"Falta {PATH_OPS}")
    if meta is None: return err(f"Falta {PATH_META}")

    regimes = meta.get("meta_indice", {}).get("regimes", {})
    if not regimes:
        return err("meta_indice.regimes vazio.")

    op_to_regs = build_op_to_regimes(regimes)

    info(f"Proposições: {len(propos)} | Conceitos: {len(indice)} | Ops: {len(ops_db)} | Regimes: {len(regimes)}")

    normalized = []
    report = {
        "total": len(propos),
        "ok": 0,
        "warnings_total": 0,
        "errors_total": 0,
        "contagem_regime_principal": defaultdict(int),
        "contagem_regimes_detectados": defaultdict(int),
        "top_tipos_warning": {},
        "top_tipos_erro": {},
        "amostras_warning": defaultdict(list),
        "amostras_erro": defaultdict(list),
        "por_operacao_desconhecida": defaultdict(int),
    }

    tipo_warning_counter = Counter()
    tipo_error_counter = Counter()

    logs_printed = 0

    for i, p in enumerate(propos, 1):
        pid = p.get("id_proposicao") or p.get("id") or f"IDX_{i:04d}"

        norm, errors, warnings = validate_one(p, indice, ops_db, regimes, op_to_regs)
        normalized.append(norm)

        # stats regimes
        rp = norm.get("regime_principal") or "SEM_REGIME"
        report["contagem_regime_principal"][rp] += 1

        regs = norm.get("regimes_detectados", [])
        if not regs:
            report["contagem_regimes_detectados"]["SEM_REGIME"] += 1
        else:
            for r in regs:
                report["contagem_regimes_detectados"][r] += 1

        # errors
        if errors:
            report["errors_total"] += 1
            for e in errors:
                tipo = e.split(":")[0]
                tipo_error_counter[tipo] += 1
                if len(report["amostras_erro"][tipo]) < MAX_AMOSTRAS_POR_TIPO:
                    report["amostras_erro"][tipo].append({"id": pid, "msg": e})

        # warnings
        if warnings:
            report["warnings_total"] += len(warnings)
            report["warnings_props"] += 1
            for w in warnings:
                tipo = w.split(":")[0]
                tipo_warning_counter[tipo] += 1
                if len(report["amostras_warning"][tipo]) < MAX_AMOSTRAS_POR_TIPO:
                    report["amostras_warning"][tipo].append({"id": pid, "msg": w})

                if w.startswith("operações desconhecidas:"):
                    m = re.search(r"\[(.*)\]", w)
                    if m:
                        raw = m.group(1)
                        for item in raw.split(","):
                            k = item.strip().strip("'").strip('"')
                            if k:
                                report["por_operacao_desconhecida"][k] += 1

        if not errors:
            report["ok"] += 1

        # logs compactos
        if (errors or warnings) and logs_printed < MAX_LOGS_INDIVIDUAIS:
            print(f"\n{C.BOLD}▶ {pid}{C.RESET}")
            if errors:
                err("ERROS:")
                for e in errors:
                    print(f"  - {e}")
            if warnings:
                warn("WARNINGS:")
                for w in warnings[:6]:
                    print(f"  - {w}")
                if len(warnings) > 6:
                    print(f"  - ... (+{len(warnings)-6})")
            logs_printed += 1

    report["top_tipos_warning"] = dict(tipo_warning_counter.most_common(30))
    report["top_tipos_erro"] = dict(tipo_error_counter.most_common(30))
    report["contagem_regime_principal"] = dict(report["contagem_regime_principal"])
    report["contagem_regimes_detectados"] = dict(report["contagem_regimes_detectados"])
    report["por_operacao_desconhecida"] = dict(report["por_operacao_desconhecida"])
    report["amostras_warning"] = dict(report["amostras_warning"])
    report["amostras_erro"] = dict(report["amostras_erro"])

    save_json(PATH_OUT, normalized)
    save_json(PATH_REPORT, report)

    head("================ RESUMO ================")
    ok(f"OK: {report['ok']}/{report['total']}")
    info(f"Warnings (proposições com warnings): {report['warnings_total']}")
    info(f"Erros (proposições com erros): {report['errors_total']}")
    info(f"Saída: {PATH_OUT}")
    info(f"Relatório: {PATH_REPORT}")

    if report["por_operacao_desconhecida"]:
        head("Top operações desconhecidas")
        for k, v in sorted(report["por_operacao_desconhecida"].items(), key=lambda x: x[1], reverse=True)[:25]:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()