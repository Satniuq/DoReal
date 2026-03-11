import os
import re
import json
import hashlib
from typing import List, Dict, Any, Tuple

FICHEIRO_MD = "fragmentos.md"
FICHEIRO_JSON = "containers_segmentacao.json"
FICHEIRO_RELATORIO = "relatorio_validacao_containers.json"

HEADER_RE = re.compile(r"^##\s+(F\d{4})(?:\s+—\s+(.*?))?\s*$", re.MULTILINE)


def normalizar_espacos(texto: str) -> str:
    texto = texto.replace("\u00A0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def separar_paragrafos(texto: str) -> List[str]:
    texto = texto.replace("\r\n", "\n").replace("\r", "\n").strip()
    blocos = re.split(r"\n\s*\n+", texto)
    return [b.strip() for b in blocos if b.strip()]


def sha1_texto(texto: str) -> str:
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()


def extrair_paragrafos_do_md(caminho: str) -> Tuple[List[Dict[str, Any]], int]:
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()

    conteudo = conteudo.replace("\r\n", "\n").replace("\r", "\n")
    headers = list(HEADER_RE.finditer(conteudo))
    n_headers = len(headers)

    paragrafos_extraidos = []

    if not headers:
        for i, p in enumerate(separar_paragrafos(conteudo), start=1):
            p_norm = normalizar_espacos(p)
            paragrafos_extraidos.append({
                "ordem_global": i,
                "texto": p,
                "texto_normalizado": p_norm,
                "hash": sha1_texto(p_norm)
            })
        return paragrafos_extraidos, n_headers

    ordem_global = 1

    # Prefixo antes do primeiro header
    inicio_primeiro = headers[0].start()
    prefixo = conteudo[:inicio_primeiro].strip()
    if prefixo:
        for p in separar_paragrafos(prefixo):
            p_norm = normalizar_espacos(p)
            paragrafos_extraidos.append({
                "ordem_global": ordem_global,
                "texto": p,
                "texto_normalizado": p_norm,
                "hash": sha1_texto(p_norm)
            })
            ordem_global += 1

    # Conteúdo de cada bloco
    for idx, h in enumerate(headers):
        start = h.end()
        end = headers[idx + 1].start() if idx + 1 < len(headers) else len(conteudo)
        corpo = conteudo[start:end].strip()

        for p in separar_paragrafos(corpo):
            p_norm = normalizar_espacos(p)
            paragrafos_extraidos.append({
                "ordem_global": ordem_global,
                "texto": p,
                "texto_normalizado": p_norm,
                "hash": sha1_texto(p_norm)
            })
            ordem_global += 1

    return paragrafos_extraidos, n_headers


def carregar_containers(caminho: str) -> List[Dict[str, Any]]:
    with open(caminho, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("containers_segmentacao.json tem de ser uma lista.")

    return data


def extrair_paragrafos_do_json(containers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    paragrafos = []
    ordem_global = 1

    for c in containers:
        cid = c.get("container_id")
        ps = c.get("paragrafos", [])
        for p in ps:
            txt = p.get("texto_normalizado") or normalizar_espacos(p.get("texto", ""))
            paragrafos.append({
                "ordem_global": ordem_global,
                "container_id": cid,
                "paragrafo_id": p.get("paragrafo_id"),
                "texto_normalizado": txt,
                "hash": sha1_texto(txt)
            })
            ordem_global += 1

    return paragrafos


def validar(caminho_md: str, caminho_json: str) -> Dict[str, Any]:
    paragrafos_md, n_headers_md = extrair_paragrafos_do_md(caminho_md)
    containers = carregar_containers(caminho_json)
    paragrafos_json = extrair_paragrafos_do_json(containers)

    erros = []
    avisos = []

    # 1. Containers vazios
    containers_vazios = []
    container_ids = []
    header_formais_json = 0

    for c in containers:
        cid = c.get("container_id")
        container_ids.append(cid)

        if c.get("tem_header_formal") is True:
            header_formais_json += 1

        ps = c.get("paragrafos", [])
        if not isinstance(ps, list) or len(ps) == 0:
            containers_vazios.append(cid)

    if containers_vazios:
        erros.append({
            "tipo": "containers_vazios",
            "containers": containers_vazios
        })

    # 2. IDs duplicados de container
    dup_container_ids = sorted({x for x in container_ids if container_ids.count(x) > 1})
    if dup_container_ids:
        erros.append({
            "tipo": "container_ids_duplicados",
            "container_ids": dup_container_ids
        })

    # 3. IDs duplicados de parágrafo
    paragrafo_ids = [p.get("paragrafo_id") for c in containers for p in c.get("paragrafos", [])]
    dup_par_ids = sorted({x for x in paragrafo_ids if paragrafo_ids.count(x) > 1})
    if dup_par_ids:
        erros.append({
            "tipo": "paragrafo_ids_duplicados",
            "paragrafo_ids": dup_par_ids
        })

    # 4. Número de headers
    if n_headers_md != header_formais_json:
        avisos.append({
            "tipo": "diferenca_numero_headers",
            "headers_md": n_headers_md,
            "containers_com_header_formal": header_formais_json
        })

    # 5. Cobertura por hash
    hashes_md = [p["hash"] for p in paragrafos_md]
    hashes_json = [p["hash"] for p in paragrafos_json]

    set_md = set(hashes_md)
    set_json = set(hashes_json)

    faltam_no_json = list(set_md - set_json)
    extras_no_json = list(set_json - set_md)

    if faltam_no_json:
        faltantes = [p for p in paragrafos_md if p["hash"] in set(faltam_no_json)]
        erros.append({
            "tipo": "paragrafos_em_falta_no_json",
            "total": len(faltantes),
            "exemplos": faltantes[:20]
        })

    if extras_no_json:
        extras = [p for p in paragrafos_json if p["hash"] in set(extras_no_json)]
        erros.append({
            "tipo": "paragrafos_a_mais_no_json",
            "total": len(extras),
            "exemplos": extras[:20]
        })

    # 6. Duplicação de conteúdo no JSON
        # 6. Duplicação indevida no JSON (comparada com o MD)
    freq_md = {}
    for h in hashes_md:
        freq_md[h] = freq_md.get(h, 0) + 1

    freq_json = {}
    for h in hashes_json:
        freq_json[h] = freq_json.get(h, 0) + 1

    duplicacoes_indevidas = []
    perdas_de_ocorrencia = []

    todos_hashes = set(freq_md.keys()) | set(freq_json.keys())

    for h in todos_hashes:
        n_md = freq_md.get(h, 0)
        n_json = freq_json.get(h, 0)

        if n_json > n_md:
            duplicacoes_indevidas.append({
                "hash": h,
                "ocorrencias_md": n_md,
                "ocorrencias_json": n_json
            })

        elif n_json < n_md:
            perdas_de_ocorrencia.append({
                "hash": h,
                "ocorrencias_md": n_md,
                "ocorrencias_json": n_json
            })

    if duplicacoes_indevidas:
        erros.append({
            "tipo": "duplicacoes_indevidas_no_json",
            "total": len(duplicacoes_indevidas),
            "exemplos": duplicacoes_indevidas[:20]
        })

    if perdas_de_ocorrencia:
        erros.append({
            "tipo": "perdas_de_ocorrencia_no_json",
            "total": len(perdas_de_ocorrencia),
            "exemplos": perdas_de_ocorrencia[:20]
        })

    # 7. Ordem global
    ordem_ok = True
    min_len = min(len(paragrafos_md), len(paragrafos_json))
    primeira_divergencia = None

    for i in range(min_len):
        if paragrafos_md[i]["hash"] != paragrafos_json[i]["hash"]:
            ordem_ok = False
            primeira_divergencia = {
                "indice": i + 1,
                "md": paragrafos_md[i],
                "json": paragrafos_json[i]
            }
            break

    if not ordem_ok:
        erros.append({
            "tipo": "ordem_divergente",
            "primeira_divergencia": primeira_divergencia
        })

    # 8. Contagens gerais
    resumo = {
        "ficheiro_md": os.path.basename(caminho_md),
        "ficheiro_json": os.path.basename(caminho_json),
        "n_headers_md": n_headers_md,
        "n_containers_json": len(containers),
        "n_paragrafos_md": len(paragrafos_md),
        "n_paragrafos_json": len(paragrafos_json),
        "cobertura_total_ok": len(faltam_no_json) == 0 and len(extras_no_json) == 0,
        "ordem_total_ok": ordem_ok,
        "ids_ok": len(dup_container_ids) == 0 and len(dup_par_ids) == 0,
        "containers_vazios_ok": len(containers_vazios) == 0
    }

    estado_final = "ok" if not erros else "com_erros"

    return {
        "estado_final": estado_final,
        "resumo": resumo,
        "erros": erros,
        "avisos": avisos
    }


def guardar_relatorio(caminho: str, relatorio: Dict[str, Any]) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)


def main():
    relatorio = validar(FICHEIRO_MD, FICHEIRO_JSON)
    guardar_relatorio(FICHEIRO_RELATORIO, relatorio)

    print("=" * 70)
    print("VALIDAÇÃO DE CONTAINERS")
    print("=" * 70)
    print(f"Estado final: {relatorio['estado_final']}")
    print(f"Parágrafos MD:   {relatorio['resumo']['n_paragrafos_md']}")
    print(f"Parágrafos JSON: {relatorio['resumo']['n_paragrafos_json']}")
    print(f"Headers MD:      {relatorio['resumo']['n_headers_md']}")
    print(f"Containers JSON: {relatorio['resumo']['n_containers_json']}")
    print(f"Cobertura OK:    {relatorio['resumo']['cobertura_total_ok']}")
    print(f"Ordem OK:        {relatorio['resumo']['ordem_total_ok']}")
    print(f"IDs OK:          {relatorio['resumo']['ids_ok']}")
    print(f"Containers OK:   {relatorio['resumo']['containers_vazios_ok']}")
    print(f"Relatório:       {FICHEIRO_RELATORIO}")
    print("=" * 70)

    if relatorio["erros"]:
        print("\nERROS DETETADOS:")
        for e in relatorio["erros"]:
            print(f"- {e['tipo']}")

    if relatorio["avisos"]:
        print("\nAVISOS:")
        for a in relatorio["avisos"]:
            print(f"- {a['tipo']}")


if __name__ == "__main__":
    main()