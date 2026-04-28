from pathlib import Path
import re
import json
from statistics import mean, median

FICHEIRO = Path("fragmentos_ja_processados.md")

RELATORIO_MD = Path("stats_fragmentos_ja_processados.md")
RELATORIO_JSON = Path("stats_fragmentos_ja_processados.json")


def ler_texto(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro não encontrado: {path}")
    return path.read_text(encoding="utf-8")


def extrair_blocos(texto: str):
    """
    Tenta detetar blocos por cabeçalhos tipo:
    ## F0001
    ## F0241_A18_SEG_001
    BLOCO_0001
    Se não encontrar cabeçalhos suficientes, faz fallback por blocos separados por linhas em branco.
    """

    padrao_header = re.compile(
        r"(?m)^(?:#{1,6}\s*)?(F\d{4}(?:_[A-Z]\d+)?(?:_SEG_\d+)?|BLOCO_\d{4})\b.*$"
    )

    matches = list(padrao_header.finditer(texto))

    blocos = []

    if matches:
        for i, m in enumerate(matches):
            inicio = m.start()
            fim = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
            bloco_texto = texto[inicio:fim].strip()
            bloco_id = m.group(1)
            blocos.append({
                "id": bloco_id,
                "texto": bloco_texto,
                "chars": len(bloco_texto),
                "palavras": len(re.findall(r"\w+", bloco_texto, flags=re.UNICODE)),
            })
    else:
        partes = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
        for i, parte in enumerate(partes, start=1):
            blocos.append({
                "id": f"BLOCO_{i:04d}",
                "texto": parte,
                "chars": len(parte),
                "palavras": len(re.findall(r"\w+", parte, flags=re.UNICODE)),
            })

    return blocos


def main():
    texto = ler_texto(FICHEIRO)
    blocos = extrair_blocos(texto)

    total_blocos = len(blocos)
    total_chars = len(texto)
    total_palavras = len(re.findall(r"\w+", texto, flags=re.UNICODE))

    chars_por_bloco = [b["chars"] for b in blocos]
    palavras_por_bloco = [b["palavras"] for b in blocos]

    ids = [b["id"] for b in blocos]
    ids_duplicados = sorted({x for x in ids if ids.count(x) > 1})

    maiores = sorted(blocos, key=lambda b: b["chars"], reverse=True)[:10]
    maiores = sorted(blocos, key=lambda b: b["chars"], reverse=True)[:10]
    menores = sorted([b for b in blocos if b["chars"] > 0], key=lambda b: b["chars"])[:10]
    resumo = {
        "ficheiro": str(FICHEIRO),
        "total_blocos": total_blocos,
        "total_chars": total_chars,
        "total_palavras": total_palavras,
        "media_chars_por_bloco": round(mean(chars_por_bloco), 2) if chars_por_bloco else 0,
        "mediana_chars_por_bloco": median(chars_por_bloco) if chars_por_bloco else 0,
        "media_palavras_por_bloco": round(mean(palavras_por_bloco), 2) if palavras_por_bloco else 0,
        "mediana_palavras_por_bloco": median(palavras_por_bloco) if palavras_por_bloco else 0,
        "ids_duplicados": ids_duplicados,
        "maiores_blocos": [
            {"id": b["id"], "chars": b["chars"], "palavras": b["palavras"]}
            for b in maiores
        ],
        "menores_blocos": [
            {"id": b["id"], "chars": b["chars"], "palavras": b["palavras"]}
            for b in menores
        ],
    }

    RELATORIO_JSON.write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    md = []
    md.append("# Stats — fragmentos_ja_processados.md\n")
    md.append("## Resumo\n")
    md.append(f"- Total de blocos detetados: {total_blocos}")
    md.append(f"- Total de caracteres: {total_chars}")
    md.append(f"- Total de palavras: {total_palavras}")
    md.append(f"- Média de caracteres por bloco: {resumo['media_chars_por_bloco']}")
    md.append(f"- Mediana de caracteres por bloco: {resumo['mediana_chars_por_bloco']}")
    md.append(f"- Média de palavras por bloco: {resumo['media_palavras_por_bloco']}")
    md.append(f"- Mediana de palavras por bloco: {resumo['mediana_palavras_por_bloco']}")
    md.append(f"- IDs duplicados: {len(ids_duplicados)}")

    if ids_duplicados:
        md.append("\n## IDs duplicados\n")
        for did in ids_duplicados:
            md.append(f"- `{did}`")

    md.append("\n## 10 maiores blocos\n")
    for b in maiores:
        inicio = b["texto"][:180].replace("\n", " ")
        md.append(f"- `{b['id']}` — {b['chars']} chars — {b['palavras']} palavras — {inicio}")

    md.append("\n## 10 menores blocos\n")
    for b in menores:
        inicio = b["texto"][:180].replace("\n", " ")
        md.append(f"- `{b['id']}` — {b['chars']} chars — {b['palavras']} palavras — {inicio}")

    RELATORIO_MD.write_text("\n".join(md), encoding="utf-8")

    print("=" * 72)
    print("STATS CONCLUÍDOS")
    print("=" * 72)
    print(f"Ficheiro analisado:       {FICHEIRO}")
    print(f"Total blocos:             {total_blocos}")
    print(f"Total caracteres:         {total_chars}")
    print(f"Total palavras:           {total_palavras}")
    print(f"IDs duplicados:           {len(ids_duplicados)}")
    print("-" * 72)
    print(f"Relatório:                {RELATORIO_MD}")
    print(f"JSON:                     {RELATORIO_JSON}")
    print("=" * 72)


if __name__ == "__main__":
    main()