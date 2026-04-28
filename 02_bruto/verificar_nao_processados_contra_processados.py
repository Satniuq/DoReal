import json
import re
import unicodedata
import hashlib
import difflib
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent

NAO_PROCESSADOS = BASE / "fragmentos_nao_processados.md"

PROCESSADOS_MD = [
    BASE / "fragmentos.md",
    BASE / "fragmentos_ja_processados.md",
]

JSON_538 = [
    BASE.parent / "19_Meta_Schema" / "instancia_total_dividida" / "03_entidades_fragmentos__parte_001.json",
    BASE.parent / "19_Meta_Schema" / "instancia_total_dividida" / "03_entidades_fragmentos__parte_002.json",
]

OUT_JSON = BASE / "match_nao_processados_vs_processados.json"
OUT_RELATORIO = BASE / "relatorio_match_nao_processados_vs_processados.md"
OUT_NOVOS = BASE / "fragmentos_nao_processados__apenas_novos.md"
OUT_DUPLICADOS = BASE / "fragmentos_nao_processados__possiveis_duplicados.md"

HEADER_RE = re.compile(r"^##\s+(F\d{4}(?:_A\d{2})?)(?:\s+—\s+.*?)?\s*$", re.MULTILINE)


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKC", texto or "")
    texto = texto.casefold()
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"[#*_`>\[\]{}()]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def hash_norm(texto: str) -> str:
    return hashlib.sha1(normalizar(texto).encode("utf-8")).hexdigest()


def split_md(texto: str):
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    headers = list(HEADER_RE.finditer(texto))

    if headers:
        blocos = []
        for i, h in enumerate(headers):
            start = h.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(texto)
            fid = h.group(1)
            corpo = texto[start:end].strip()
            if corpo:
                blocos.append({
                    "id": fid,
                    "texto": corpo
                })
        return blocos

    partes = [p.strip() for p in re.split(r"\n\s*\n+", texto) if p.strip()]
    return [
        {
            "id": f"BLOCO_{i:04d}",
            "texto": p
        }
        for i, p in enumerate(partes, start=1)
    ]


def carregar_processados():
    corpus = []

    for path in JSON_538:
        if not path.exists():
            continue

        data = json.loads(path.read_text(encoding="utf-8"))
        for frag in data.get("fragmentos", []):
            fid = frag.get("fragment_id")
            textos = []

            emp = frag.get("camada_empirica", {})
            txt = frag.get("camada_textual_derivada", {})

            for key in ["texto_fragmento", "texto_normalizado", "texto_fonte_reconstituido"]:
                if emp.get(key):
                    textos.append(emp[key])

            if txt.get("texto_limpo"):
                textos.append(txt["texto_limpo"])

            corpus.append({
                "id": fid,
                "origem": path.name,
                "texto": "\n\n".join(textos),
                "norm": normalizar("\n\n".join(textos)),
            })

    for path in PROCESSADOS_MD:
        if not path.exists():
            continue

        blocos = split_md(path.read_text(encoding="utf-8"))
        for b in blocos:
            corpus.append({
                "id": b["id"],
                "origem": path.name,
                "texto": b["texto"],
                "norm": normalizar(b["texto"]),
            })

    return corpus


def score_match(a_norm, b_norm):
    if not a_norm or not b_norm:
        return 0.0

    if a_norm == b_norm:
        return 1.0

    if len(a_norm) > 120 and a_norm in b_norm:
        return 0.99

    if len(b_norm) > 120 and b_norm in a_norm:
        return min(0.98, len(b_norm) / max(1, len(a_norm)))

    tokens_a = set(re.findall(r"\w{4,}", a_norm))
    tokens_b = set(re.findall(r"\w{4,}", b_norm))

    if not tokens_a or not tokens_b:
        jaccard = 0.0
    else:
        jaccard = len(tokens_a & tokens_b) / max(1, len(tokens_a | tokens_b))

    if jaccard < 0.08:
        return jaccard

    ratio = difflib.SequenceMatcher(None, a_norm, b_norm).ratio()
    return max(jaccard, ratio)


def classificar(score):
    if score >= 0.95:
        return "ja_integrado"
    if score >= 0.72:
        return "possivel_duplicado"
    return "novo_provavel"


def main():
    if not NAO_PROCESSADOS.exists():
        raise SystemExit(f"Não existe: {NAO_PROCESSADOS}")

    processados = carregar_processados()

    if not processados:
        raise SystemExit("Não encontrei base processada. Verifica os caminhos no topo do script.")

    nao_blocos = split_md(NAO_PROCESSADOS.read_text(encoding="utf-8"))

    hashes_nao = defaultdict(list)
    for b in nao_blocos:
        hashes_nao[hash_norm(b["texto"])].append(b["id"])

    duplicados_internos = {
        h: ids for h, ids in hashes_nao.items()
        if len(ids) > 1
    }

    resultados = []

    for b in nao_blocos:
        n = normalizar(b["texto"])
        melhor = {
            "score": 0.0,
            "id": None,
            "origem": None,
        }

        for p in processados:
            s = score_match(n, p["norm"])
            if s > melhor["score"]:
                melhor = {
                    "score": s,
                    "id": p["id"],
                    "origem": p["origem"],
                }

        resultados.append({
            "id_nao_processado": b["id"],
            "chars": len(b["texto"]),
            "inicio": b["texto"][:180].replace("\n", " "),
            "melhor_match_id": melhor["id"],
            "melhor_match_origem": melhor["origem"],
            "score": round(melhor["score"], 4),
            "classe": classificar(melhor["score"]),
            "texto": b["texto"],
        })

    novos = [r for r in resultados if r["classe"] == "novo_provavel"]
    possiveis = [r for r in resultados if r["classe"] == "possivel_duplicado"]
    integrados = [r for r in resultados if r["classe"] == "ja_integrado"]

    OUT_JSON.write_text(
        json.dumps({
            "resumo": {
                "total_nao_processados": len(resultados),
                "ja_integrados": len(integrados),
                "possiveis_duplicados": len(possiveis),
                "novos_provaveis": len(novos),
                "duplicados_internos": list(duplicados_internos.values()),
                "total_processados_comparados": len(processados),
            },
            "resultados": resultados,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    linhas = []
    linhas.append("# Relatório — match de não processados contra processados\n")
    linhas.append("## Resumo\n")
    linhas.append(f"- Total em `fragmentos_nao_processados.md`: {len(resultados)}")
    linhas.append(f"- Já integrados: {len(integrados)}")
    linhas.append(f"- Possíveis duplicados: {len(possiveis)}")
    linhas.append(f"- Novos prováveis: {len(novos)}")
    linhas.append(f"- Duplicados internos: {len(duplicados_internos)}")
    linhas.append(f"- Base processada comparada: {len(processados)} blocos/fragmentos\n")

    if duplicados_internos:
        linhas.append("## Duplicados internos no ficheiro de não processados\n")
        for ids in duplicados_internos.values():
            linhas.append("- " + ", ".join(ids))
        linhas.append("")

    linhas.append("## Possíveis duplicados\n")
    if possiveis:
        for r in possiveis:
            linhas.append(
                f"- `{r['id_nao_processado']}` ≈ `{r['melhor_match_id']}` "
                f"({r['melhor_match_origem']}) — score {r['score']}"
            )
    else:
        linhas.append("- Nenhum.")
    linhas.append("")

    linhas.append("## Novos prováveis\n")
    for r in novos:
        linhas.append(f"- `{r['id_nao_processado']}` — {r['inicio']}")
    linhas.append("")

    OUT_RELATORIO.write_text("\n".join(linhas), encoding="utf-8")

    OUT_NOVOS.write_text(
        "\n\n".join(r["texto"] for r in novos).strip() + "\n",
        encoding="utf-8"
    )

    OUT_DUPLICADOS.write_text(
        "\n\n".join(r["texto"] for r in possiveis).strip() + ("\n" if possiveis else ""),
        encoding="utf-8"
    )

    print("=" * 72)
    print("MATCH CONCLUÍDO")
    print("=" * 72)
    print(f"Total não processados: {len(resultados)}")
    print(f"Já integrados:         {len(integrados)}")
    print(f"Possíveis duplicados:  {len(possiveis)}")
    print(f"Novos prováveis:       {len(novos)}")
    print(f"Duplicados internos:   {len(duplicados_internos)}")
    print("-" * 72)
    print(f"Relatório:             {OUT_RELATORIO.name}")
    print(f"JSON:                  {OUT_JSON.name}")
    print(f"Apenas novos:          {OUT_NOVOS.name}")
    print(f"Possíveis duplicados:  {OUT_DUPLICADOS.name}")
    print("=" * 72)


if __name__ == "__main__":
    main()