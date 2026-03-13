import json
from pathlib import Path
from typing import Any, Dict, List


# ============================================================
# PATHS
# ============================================================

PASTA_SCRIPT = Path(__file__).resolve().parent
CAMINHO_MAPA = PASTA_SCRIPT / "mapa_integral_do_indice.json"
CAMINHO_SAIDA = PASTA_SCRIPT / "mapa_integral_do_indice_editorial.md"


# ============================================================
# UTILITÁRIOS
# ============================================================

def carregar_json(caminho: Path) -> Any:
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def guardar_texto(caminho: Path, texto: str) -> None:
    with caminho.open("w", encoding="utf-8") as f:
        f.write(texto)


def normalizar_lista(valor: Any) -> List[Any]:
    if valor is None:
        return []
    if isinstance(valor, list):
        return valor
    return [valor]


def texto(valor: Any, default: str = "—") -> str:
    if valor is None:
        return default
    if isinstance(valor, str):
        valor = valor.strip()
        return valor if valor else default
    return str(valor)


def juntar_lista(valores: Any, default: str = "—") -> str:
    itens = [texto(v, "") for v in normalizar_lista(valores)]
    itens = [x for x in itens if x]
    return ", ".join(itens) if itens else default


def titulo_md(nivel: int, conteudo: str) -> str:
    return f"{'#' * nivel} {conteudo}\n"


def bullets_simples(itens: List[str], default: str = "- —") -> str:
    if not itens:
        return default
    return "\n".join(f"- {item}" for item in itens)


# ============================================================
# RESUMOS EDITORIAIS
# ============================================================

def resumir_argumentos(argumentos: List[Dict[str, Any]], max_itens: int = 5) -> str:
    if not argumentos:
        return "- —"

    linhas = []
    for arg in argumentos[:max_itens]:
        linhas.append(
            f"- {texto(arg.get('argumento_id'))}: "
            f"{texto(arg.get('conceito_alvo'))} "
            f"[{texto(arg.get('natureza'))}; {texto(arg.get('nivel_de_operacao'))}]"
        )

    if len(argumentos) > max_itens:
        linhas.append(f"- … +{len(argumentos) - max_itens} argumento(s)")
    return "\n".join(linhas)


def resumir_capitulos_relacionados(
    itens: List[Dict[str, Any]],
    campo_via: str,
    max_itens: int = 5,
) -> str:
    if not itens:
        return "- —"

    linhas = []
    for item in itens[:max_itens]:
        via = texto(item.get(campo_via))
        base = f"{texto(item.get('capitulo_id'))} — {texto(item.get('titulo'))}"
        if via != "—":
            base += f" (via {via})"
        linhas.append(f"- {base}")

    if len(itens) > max_itens:
        linhas.append(f"- … +{len(itens) - max_itens} referência(s)")
    return "\n".join(linhas)


def resumir_subzonas(subzonas: List[Dict[str, Any]], max_itens: int = 4) -> str:
    if not subzonas:
        return "- —"

    linhas = []
    for sub in subzonas[:max_itens]:
        linhas.append(
            f"- {texto(sub.get('subzona'))}: "
            f"{texto(sub.get('total_fragmentos'))} fragmentos "
            f"(fortes={texto(sub.get('fortes'))}, "
            f"prováveis={texto(sub.get('provaveis'))}, "
            f"fracos={texto(sub.get('fracos'))}, "
            f"indefinidos={texto(sub.get('indefinidos'))})"
        )

    if len(subzonas) > max_itens:
        linhas.append(f"- … +{len(subzonas) - max_itens} subzona(s)")
    return "\n".join(linhas)


def resumir_fragmentos_exemplo(fragmentos: List[Dict[str, Any]], max_itens: int = 5) -> str:
    if not fragmentos:
        return "- —"

    linhas = []
    for frag in fragmentos[:max_itens]:
        linhas.append(
            f"- {texto(frag.get('fragment_id'))} | "
            f"grau={texto(frag.get('grau_de_pertenca_ao_indice'))} | "
            f"arg={texto(frag.get('argumento_canonico_relacionado'))} | "
            f"score={texto(frag.get('score'))} | "
            f"{texto(frag.get('descricao_funcional_curta'))}"
        )

    if len(fragmentos) > max_itens:
        linhas.append(f"- … +{len(fragmentos) - max_itens} fragmento(s)")
    return "\n".join(linhas)


def resumo_fragmentos_curto(resumo: Dict[str, Any]) -> str:
    if not resumo:
        return "- —"

    return (
        f"- total={texto(resumo.get('total_fragmentos_prioritarios'))}; "
        f"fortes={texto(resumo.get('fortes'))}; "
        f"prováveis={texto(resumo.get('provaveis'))}; "
        f"fracos={texto(resumo.get('fracos'))}; "
        f"indefinidos={texto(resumo.get('indefinidos'))}; "
        f"reconstruíveis={texto(resumo.get('reconstruiveis'))}"
    )


def resumir_apoio_percurso(apoio: Dict[str, Any]) -> str:
    if not apoio:
        return "- —"

    caps = normalizar_lista(apoio.get("caps_ids_no_percurso"))
    percursos_base = normalizar_lista(apoio.get("percursos_base"))

    return (
        f"- capítulos no percurso: {len(caps)} | "
        f"percursos base: {juntar_lista(percursos_base)}"
    )


def frase_editorial_do_capitulo(cap: Dict[str, Any]) -> str:
    cap_id = texto(cap.get("capitulo_id"))
    titulo = texto(cap.get("titulo"))
    percurso = texto(cap.get("percurso_axial"))
    regime = texto(cap.get("regime_principal"))
    estado = texto(cap.get("estado_instalacao"))
    campos = normalizar_lista(cap.get("campos"))

    if campos:
        return (
            f"{cap_id} organiza-se em torno de {titulo.lower()}, "
            f"inscrevendo-se no percurso {percurso}, sob regime principal {regime}, "
            f"com estatuto de instalação '{estado}'."
        )

    return (
        f"{cap_id} organiza-se em torno de {titulo.lower()}, "
        f"inscrevendo-se no percurso {percurso}, sob regime principal {regime}, "
        f"com estatuto de instalação '{estado}'."
    )


# ============================================================
# SECÇÕES
# ============================================================

def construir_visao_global(mapa: Dict[str, Any]) -> str:
    estrutura = mapa.get("estrutura_global", {})
    cobertura = mapa.get("resumo_cobertura", {})
    partes = normalizar_lista(estrutura.get("partes"))

    linhas = [
        titulo_md(1, "Mapa Integral do Índice — versão editorial"),
        "Versão reduzida e legível do mapa integral, orientada para leitura humana.",
        "",
        titulo_md(2, "Visão global"),
        f"- partes: {len(partes)}",
        f"- capítulos: {texto(estrutura.get('total_capitulos'))}",
        f"- argumentos: {texto(estrutura.get('total_argumentos'))}",
        f"- fragmentos tratados: {texto(estrutura.get('total_fragmentos_tratados'))}",
        f"- fragmentos fortes: {texto(estrutura.get('total_fragmentos_fortes'))}",
        f"- fragmentos prováveis: {texto(estrutura.get('total_fragmentos_provaveis'))}",
        f"- fragmentos fracos: {texto(estrutura.get('total_fragmentos_fracos'))}",
        f"- fragmentos indefinidos: {texto(estrutura.get('total_fragmentos_indefinidos'))}",
        "",
        titulo_md(2, "Cobertura geral"),
        f"- capítulos sem argumentos: {texto(cobertura.get('total_capitulos_sem_argumentos'))}",
        f"- capítulos sem fragmentos: {texto(cobertura.get('total_capitulos_sem_fragmentos'))}",
        f"- capítulos com cobertura forte: {texto(cobertura.get('total_capitulos_com_cobertura_forte'))}",
        f"- capítulos com cobertura apenas provável: {texto(cobertura.get('total_capitulos_com_cobertura_apenas_provavel'))}",
        "",
        titulo_md(2, "Partes"),
    ]

    for parte in partes:
        linhas.append(
            f"- {texto(parte.get('parte_id'))} "
            f"(ordem {texto(parte.get('ordem'))}) → "
            f"{juntar_lista(parte.get('capitulos_ids'))}"
        )

    linhas.append("")
    return "\n".join(linhas)


def construir_secao_capitulo(cap: Dict[str, Any]) -> str:
    linhas = [
        titulo_md(3, f"{texto(cap.get('capitulo_id'))} — {texto(cap.get('titulo'))}"),
        frase_editorial_do_capitulo(cap),
        "",
        f"- parte: {texto(cap.get('parte_id'))}",
        f"- ordem: {texto(cap.get('ordem'))}",
        f"- nível: {texto(cap.get('nivel'))}",
        f"- campos: {juntar_lista(cap.get('campos'))}",
        f"- regime principal: {texto(cap.get('regime_principal'))}",
        f"- regimes secundários: {juntar_lista(cap.get('regimes_secundarios'))}",
        f"- percurso axial: {texto(cap.get('percurso_axial'))}",
        f"- percursos participantes: {juntar_lista(cap.get('percursos_participantes'))}",
        f"- estado de instalação: {texto(cap.get('estado_instalacao'))}",
        "",
        "#### Apoio do percurso",
        resumir_apoio_percurso(cap.get("apoio_percurso", {})),
        "",
        "#### Capítulos anteriores pressupostos",
        resumir_capitulos_relacionados(
            normalizar_lista(cap.get("capitulos_anteriores_pressupostos")),
            "via_percurso",
        ),
        "",
        "#### Capítulos seguintes preparados",
        resumir_capitulos_relacionados(
            normalizar_lista(cap.get("capitulos_seguintes_preparados")),
            "via_argumento",
        ),
        "",
        "#### Argumentos canónicos",
        resumir_argumentos(normalizar_lista(cap.get("argumentos_canonicos"))),
        "",
        "#### Subzonas provisórias",
        resumir_subzonas(normalizar_lista(cap.get("subzonas_provisorias"))),
        "",
        "#### Cobertura de fragmentos",
        resumo_fragmentos_curto(cap.get("resumo_fragmentos_prioritarios", {})),
        "",
        "#### Fragmentos de exemplo",
        resumir_fragmentos_exemplo(normalizar_lista(cap.get("fragmentos_prioritarios_exemplo"))),
        "",
    ]

    return "\n".join(linhas)


def construir_documento_editorial(mapa: Dict[str, Any]) -> str:
    estrutura = mapa.get("estrutura_global", {})
    partes = normalizar_lista(estrutura.get("partes"))
    capitulos = normalizar_lista(mapa.get("capitulos"))

    capitulos_por_id = {
        cap.get("capitulo_id"): cap
        for cap in capitulos
        if cap.get("capitulo_id")
    }

    blocos = [construir_visao_global(mapa)]
    blocos.append(titulo_md(2, "Leitura editorial por partes"))

    for parte in partes:
        parte_id = texto(parte.get("parte_id"))
        ordem = texto(parte.get("ordem"))
        blocos.append(titulo_md(2, f"Parte {ordem} — {parte_id}"))

        for cap_id in normalizar_lista(parte.get("capitulos_ids")):
            cap = capitulos_por_id.get(cap_id)
            if cap:
                blocos.append(construir_secao_capitulo(cap))

    return "\n".join(blocos).strip() + "\n"


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    if not CAMINHO_MAPA.exists():
        raise FileNotFoundError(f"Não encontrei o ficheiro: {CAMINHO_MAPA}")

    mapa = carregar_json(CAMINHO_MAPA)
    saida = construir_documento_editorial(mapa)
    guardar_texto(CAMINHO_SAIDA, saida)

    print("=" * 100)
    print("MAPA INTEGRAL DO ÍNDICE — VERSÃO EDITORIAL")
    print("=" * 100)
    print(f"Input:  {CAMINHO_MAPA}")
    print(f"Output: {CAMINHO_SAIDA}")
    print("=" * 100)


if __name__ == "__main__":
    main()
