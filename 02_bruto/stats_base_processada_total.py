from pathlib import Path
import re
import json
from statistics import mean, median
from collections import defaultdict

PASTA = Path(".")

RELATORIO_MD = Path("stats_base_processada_total.md")
RELATORIO_JSON = Path("stats_base_processada_total.json")

EXCLUIR_NOMES_CONTENDO = [
    "nao_processados",
    "não_processados",
    "possiveis_duplicados",
    "possíveis_duplicados",
    "apenas_novos",
    "relatorio_match",
    "match_nao_processados",
    "stats_",
    "falhas_",
    "estado_",
]

INCLUIR_MD_PREFERENCIA = [
    "fragmentos.md",
    "fragmentos_ja_processados.md",
]

INCLUIR_JSON_PREFIXOS = [
    "03_entidades_fragmentos",
    "containers_segmentacao",
    "fragmentos_resegmentados",
]


def deve_excluir(path: Path) -> bool:
    nome = path.name.lower()
    return any(x.lower() in nome for x in EXCLUIR_NOMES_CONTENDO)


def normalizar_espacos(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def contar_palavras(s: str) -> int:
    return len(re.findall(r"\w+", s or "", flags=re.UNICODE))


def extrair_blocos_md(path: Path):
    texto = path.read_text(encoding="utf-8", errors="replace")

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
                "origem": path.name,
                "tipo_origem": "md_header",
                "texto": bloco_texto,
                "chars": len(bloco_texto),
                "palavras": contar_palavras(bloco_texto),
                "inicio": normalizar_espacos(bloco_texto[:220]),
            })
    else:
        partes = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
        for i, parte in enumerate(partes, start=1):
            bloco_id = f"{path.stem}__BLOCO_{i:04d}"
            blocos.append({
                "id": bloco_id,
                "origem": path.name,
                "tipo_origem": "md_paragrafo",
                "texto": parte,
                "chars": len(parte),
                "palavras": contar_palavras(parte),
                "inicio": normalizar_espacos(parte[:220]),
            })

    return blocos


def procurar_texto_fragmento(obj):
    """
    Procura o melhor campo textual dentro de uma entidade JSON de fragmento.
    Ordem preferida:
    - camada_textual_derivada.texto_limpo
    - camada_empirica.texto_fragmento
    - texto_limpo
    - texto_fragmento
    - texto
    - texto_literal
    """

    if not isinstance(obj, dict):
        return ""

    camada_textual = obj.get("camada_textual_derivada")
    if isinstance(camada_textual, dict):
        if camada_textual.get("texto_limpo"):
            return camada_textual.get("texto_limpo")

    camada_empirica = obj.get("camada_empirica")
    if isinstance(camada_empirica, dict):
        if camada_empirica.get("texto_fragmento"):
            return camada_empirica.get("texto_fragmento")
        if camada_empirica.get("texto_normalizado"):
            return camada_empirica.get("texto_normalizado")

    for chave in ["texto_limpo", "texto_fragmento", "texto_normalizado", "texto", "texto_literal"]:
        if isinstance(obj.get(chave), str) and obj.get(chave).strip():
            return obj.get(chave)

    return ""


def encontrar_entidades_fragmento(obj, path: Path, encontrados):
    """
    Percorre JSON recursivamente e extrai entidades que pareçam fragmentos.
    """

    if isinstance(obj, dict):
        frag_id = None

        if isinstance(obj.get("fragment_id"), str):
            frag_id = obj.get("fragment_id")
        elif isinstance(obj.get("id"), str) and re.match(r"^F\d{4}", obj.get("id")):
            frag_id = obj.get("id")

        texto = procurar_texto_fragmento(obj)

        if frag_id and texto:
            encontrados.append({
                "id": frag_id,
                "origem": path.name,
                "tipo_origem": "json_fragmento",
                "texto": texto.strip(),
                "chars": len(texto.strip()),
                "palavras": contar_palavras(texto),
                "inicio": normalizar_espacos(texto[:220]),
            })

        for v in obj.values():
            encontrar_entidades_fragmento(v, path, encontrados)

    elif isinstance(obj, list):
        for item in obj:
            encontrar_entidades_fragmento(item, path, encontrados)


def extrair_blocos_json(path: Path):
    try:
        obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        return [{
            "id": f"ERRO_JSON__{path.name}",
            "origem": path.name,
            "tipo_origem": "erro_json",
            "texto": f"Erro ao ler JSON: {e}",
            "chars": 0,
            "palavras": 0,
            "inicio": f"Erro ao ler JSON: {e}",
        }]

    encontrados = []
    encontrar_entidades_fragmento(obj, path, encontrados)
    return encontrados


def escolher_ficheiros():
    md_files = []
    json_files = []

    for p in sorted(PASTA.glob("*.md")):
        if deve_excluir(p):
            continue

        if p.name in INCLUIR_MD_PREFERENCIA:
            md_files.append(p)

    for p in sorted(PASTA.glob("*.json")):
        if deve_excluir(p):
            continue

        nome = p.name.lower()
        if any(nome.startswith(pref.lower()) for pref in INCLUIR_JSON_PREFIXOS):
            json_files.append(p)

    return md_files, json_files


def assinatura_texto(texto: str) -> str:
    """
    Assinatura simples para detetar duplicados exatos ou quase exatos por normalização forte.
    """
    t = texto.lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\wÀ-ÿ ]+", "", t, flags=re.UNICODE)
    return t.strip()


def main():
    md_files, json_files = escolher_ficheiros()

    blocos = []

    for p in md_files:
        blocos.extend(extrair_blocos_md(p))

    for p in json_files:
        blocos.extend(extrair_blocos_json(p))

    blocos_validos = [b for b in blocos if b["chars"] > 0 and not b["id"].startswith("ERRO_JSON__")]

    por_origem = defaultdict(list)
    for b in blocos_validos:
        por_origem[b["origem"]].append(b)

    ids = [b["id"] for b in blocos_validos]
    ids_duplicados = sorted({x for x in ids if ids.count(x) > 1})

    ass_map = defaultdict(list)
    for b in blocos_validos:
        sig = assinatura_texto(b["texto"])
        if sig:
            ass_map[sig].append(b)

    duplicados_texto_exato = [
        grupos for grupos in ass_map.values()
        if len(grupos) > 1
    ]

    chars_por_bloco = [b["chars"] for b in blocos_validos]
    palavras_por_bloco = [b["palavras"] for b in blocos_validos]

    maiores = sorted(blocos_validos, key=lambda b: b["chars"], reverse=True)[:20]
    menores = sorted([b for b in blocos_validos if b["chars"] > 0], key=lambda b: b["chars"])[:20]

    resumo = {
        "ficheiros_md_usados": [p.name for p in md_files],
        "ficheiros_json_usados": [p.name for p in json_files],
        "total_blocos_extraidos": len(blocos_validos),
        "total_chars": sum(chars_por_bloco),
        "total_palavras": sum(palavras_por_bloco),
        "media_chars_por_bloco": round(mean(chars_por_bloco), 2) if chars_por_bloco else 0,
        "mediana_chars_por_bloco": median(chars_por_bloco) if chars_por_bloco else 0,
        "media_palavras_por_bloco": round(mean(palavras_por_bloco), 2) if palavras_por_bloco else 0,
        "mediana_palavras_por_bloco": median(palavras_por_bloco) if palavras_por_bloco else 0,
        "ids_duplicados": ids_duplicados,
        "duplicados_texto_exato_total_grupos": len(duplicados_texto_exato),
        "por_origem": {
            origem: {
                "total": len(items),
                "chars": sum(x["chars"] for x in items),
                "palavras": sum(x["palavras"] for x in items),
            }
            for origem, items in sorted(por_origem.items())
        },
        "maiores_blocos": [
            {
                "id": b["id"],
                "origem": b["origem"],
                "chars": b["chars"],
                "palavras": b["palavras"],
                "inicio": b["inicio"],
            }
            for b in maiores
        ],
        "menores_blocos": [
            {
                "id": b["id"],
                "origem": b["origem"],
                "chars": b["chars"],
                "palavras": b["palavras"],
                "inicio": b["inicio"],
            }
            for b in menores
        ],
        "duplicados_texto_exato": [
            [
                {
                    "id": b["id"],
                    "origem": b["origem"],
                    "chars": b["chars"],
                    "inicio": b["inicio"],
                }
                for b in grupo
            ]
            for grupo in duplicados_texto_exato[:50]
        ],
    }

    RELATORIO_JSON.write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    md = []
    md.append("# Stats — base processada total\n")

    md.append("## Ficheiros usados\n")
    md.append("### Markdown\n")
    if md_files:
        for p in md_files:
            md.append(f"- `{p.name}`")
    else:
        md.append("- Nenhum.")

    md.append("\n### JSON\n")
    if json_files:
        for p in json_files:
            md.append(f"- `{p.name}`")
    else:
        md.append("- Nenhum.")

    md.append("\n## Resumo\n")
    md.append(f"- Total de blocos/fragmentos extraídos: {resumo['total_blocos_extraidos']}")
    md.append(f"- Total de caracteres: {resumo['total_chars']}")
    md.append(f"- Total de palavras: {resumo['total_palavras']}")
    md.append(f"- Média de caracteres por bloco: {resumo['media_chars_por_bloco']}")
    md.append(f"- Mediana de caracteres por bloco: {resumo['mediana_chars_por_bloco']}")
    md.append(f"- Média de palavras por bloco: {resumo['media_palavras_por_bloco']}")
    md.append(f"- Mediana de palavras por bloco: {resumo['mediana_palavras_por_bloco']}")
    md.append(f"- IDs duplicados: {len(ids_duplicados)}")
    md.append(f"- Grupos de texto duplicado exato: {len(duplicados_texto_exato)}")

    md.append("\n## Totais por origem\n")
    for origem, dados in resumo["por_origem"].items():
        md.append(
            f"- `{origem}` — {dados['total']} blocos — "
            f"{dados['chars']} chars — {dados['palavras']} palavras"
        )

    if ids_duplicados:
        md.append("\n## IDs duplicados\n")
        for did in ids_duplicados:
            md.append(f"- `{did}`")

    md.append("\n## 20 maiores blocos\n")
    for b in maiores:
        md.append(
            f"- `{b['id']}` — `{b['origem']}` — "
            f"{b['chars']} chars — {b['palavras']} palavras — {b['inicio']}"
        )

    md.append("\n## 20 menores blocos\n")
    for b in menores:
        md.append(
            f"- `{b['id']}` — `{b['origem']}` — "
            f"{b['chars']} chars — {b['palavras']} palavras — {b['inicio']}"
        )

    if duplicados_texto_exato:
        md.append("\n## Duplicados de texto exato ou normalizado — primeiros 50 grupos\n")
        for i, grupo in enumerate(duplicados_texto_exato[:50], start=1):
            md.append(f"\n### Grupo {i}\n")
            for b in grupo:
                md.append(f"- `{b['id']}` — `{b['origem']}` — {b['inicio']}")

    RELATORIO_MD.write_text("\n".join(md), encoding="utf-8")

    print("=" * 72)
    print("STATS BASE PROCESSADA TOTAL CONCLUÍDOS")
    print("=" * 72)
    print(f"Ficheiros MD usados:       {len(md_files)}")
    print(f"Ficheiros JSON usados:     {len(json_files)}")
    print(f"Total blocos/fragmentos:   {resumo['total_blocos_extraidos']}")
    print(f"Total caracteres:          {resumo['total_chars']}")
    print(f"Total palavras:            {resumo['total_palavras']}")
    print(f"IDs duplicados:            {len(ids_duplicados)}")
    print(f"Duplicados texto exato:    {len(duplicados_texto_exato)}")
    print("-" * 72)
    print(f"Relatório:                 {RELATORIO_MD}")
    print(f"JSON:                      {RELATORIO_JSON}")
    print("=" * 72)


if __name__ == "__main__":
    main()