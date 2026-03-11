from __future__ import annotations

import json
import re
import sys
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List, Tuple


# =========================================================
# CONFIG
# =========================================================

FICHEIRO_FRAGMENTOS = "fragmentos_resegmentados.json"
FICHEIRO_RELATORIO = "relatorio_validacao_fragmentos.json"

TIPOS_UNIDADE_VALIDOS = {
    "bloco_unico",
    "afirmacao_curta",
    "distincao_conceptual",
    "desenvolvimento_curto",
    "desenvolvimento_medio",
    "sequencia_argumentativa",
    "objecao_local",
    "resposta_local",
    "transicao_reflexiva",
    "fragmento_intuitivo",
}

CRITERIOS_UNIDADE_VALIDOS = {
    "container_atomico",
    "continuidade_tematica",
    "continuidade_argumentativa",
    "continuidade_definicional",
    "continuidade_reflexiva",
    "fecho_suficiente",
    "mudanca_de_tema",
    "mudanca_de_funcao",
    "quebra_de_escala",
    "quebra_de_objeto",
}

FUNCOES_TEXTUAIS_VALIDAS = {
    "afirmacao",
    "definicao",
    "desenvolvimento",
    "distincao",
    "objecao",
    "resposta",
    "transicao",
    "exploracao",
    "pergunta_reflexiva",
    "critica",
    "sintese_provisoria",
}

GRAUS_INTEGRIDADE_VALIDOS = {"baixo", "medio", "alto"}
CONFIANCA_VALIDA = {"baixa", "media", "alta"}

ESTADO_REVISAO_ESPERADO = "segmentado_auto"
TIPO_SEGMENTACAO_ESPERADO = "segmentacao_semantica_duas_fases"

PADRAO_FRAGMENT_ID = re.compile(r"^(.+?)_SEG_(\d{3})$")


# =========================================================
# UTILITÁRIOS
# =========================================================

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalizar_espacos(texto: str) -> str:
    texto = (texto or "").replace("\u00A0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()

def contar_frases_aprox(texto: str) -> int:
    texto = normalizar_espacos(texto)
    if not texto:
        return 0
    partes = re.split(r"[.!?]+(?:\s+|$)", texto)
    partes = [p.strip() for p in partes if p.strip()]
    return max(1, len(partes))

def densidade_aprox(texto: str) -> str:
    n = len(normalizar_espacos(texto))
    if n < 180:
        return "baixa"
    if n < 500:
        return "media"
    return "alta"

def sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()

def is_non_empty_str(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())

def add_erro(erros: List[Dict[str, Any]], fragment_id: str, codigo: str, detalhe: str) -> None:
    erros.append({
        "fragment_id": fragment_id,
        "codigo": codigo,
        "detalhe": detalhe
    })

def add_aviso(avisos: List[Dict[str, Any]], fragment_id: str, codigo: str, detalhe: str) -> None:
    avisos.append({
        "fragment_id": fragment_id,
        "codigo": codigo,
        "detalhe": detalhe
    })


# =========================================================
# VALIDAÇÃO DE UM FRAGMENTO
# =========================================================

def validar_fragmento(
    frag: Dict[str, Any],
    erros: List[Dict[str, Any]],
    avisos: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Devolve metadados úteis para validação transversal.
    """

    fragment_id = frag.get("fragment_id", "<sem_fragment_id>")
    meta: Dict[str, Any] = {
        "fragment_id": fragment_id,
        "container_id": None,
        "seq": None,
        "paragrafos_origem": [],
    }

    if not isinstance(frag, dict):
        add_erro(erros, fragment_id, "fragmento_nao_objeto", "O item de topo não é um objeto JSON.")
        return meta

    # -------------------------
    # fragment_id
    # -------------------------
    if not is_non_empty_str(frag.get("fragment_id")):
        add_erro(erros, fragment_id, "fragment_id_invalido", "fragment_id ausente ou inválido.")
    else:
        m = PADRAO_FRAGMENT_ID.match(frag["fragment_id"])
        if not m:
            add_erro(erros, fragment_id, "fragment_id_formato", "Formato esperado: <container_id>_SEG_001.")
        else:
            meta["container_id"] = m.group(1)
            meta["seq"] = int(m.group(2))

    # -------------------------
    # origem
    # -------------------------
    origem = frag.get("origem")
    if not isinstance(origem, dict):
        add_erro(erros, fragment_id, "origem_invalida", "Campo 'origem' ausente ou não-objeto.")
    else:
        origem_id = origem.get("origem_id")
        if meta["container_id"] is not None and origem_id != meta["container_id"]:
            add_erro(
                erros,
                fragment_id,
                "origem_id_diverge_fragment_id",
                f"origem.origem_id='{origem_id}' diverge do prefixo de fragment_id='{meta['container_id']}'."
            )

        if not is_non_empty_str(origem.get("ficheiro")):
            add_erro(erros, fragment_id, "origem_ficheiro_invalido", "origem.ficheiro ausente ou inválido.")

        if not is_non_empty_str(origem_id):
            add_erro(erros, fragment_id, "origem_id_invalido", "origem.origem_id ausente ou inválido.")

        if "ordem_no_ficheiro" not in origem:
            add_erro(erros, fragment_id, "ordem_no_ficheiro_ausente", "origem.ordem_no_ficheiro ausente.")

        blocos_fonte = origem.get("blocos_fonte")
        if not isinstance(blocos_fonte, list) or not blocos_fonte:
            add_erro(erros, fragment_id, "blocos_fonte_invalidos", "origem.blocos_fonte ausente ou inválido.")
        else:
            if len(blocos_fonte) != 1:
                add_aviso(
                    avisos,
                    fragment_id,
                    "blocos_fonte_multiplos",
                    "O gerador atual tende a criar exatamente 1 bloco_fonte por fragmento."
                )

            todos_paragrafos = []
            for i, bloco in enumerate(blocos_fonte, start=1):
                if not isinstance(bloco, dict):
                    add_erro(erros, fragment_id, "bloco_fonte_nao_objeto", f"bloco_fonte #{i} não é objeto.")
                    continue

                bloco_id = bloco.get("bloco_id")
                if origem_id and bloco_id != origem_id:
                    add_erro(
                        erros,
                        fragment_id,
                        "bloco_id_diverge_origem_id",
                        f"bloco_id='{bloco_id}' diverge de origem_id='{origem_id}'."
                    )

                pars = bloco.get("paragrafos_origem")
                if not isinstance(pars, list) or not pars or not all(isinstance(x, str) and x.strip() for x in pars):
                    add_erro(
                        erros,
                        fragment_id,
                        "paragrafos_origem_invalidos",
                        f"bloco_fonte #{i} sem paragrafos_origem válidos."
                    )
                    continue

                if len(set(pars)) != len(pars):
                    add_erro(
                        erros,
                        fragment_id,
                        "paragrafos_origem_repetidos_no_bloco",
                        f"bloco_fonte #{i} repete IDs de parágrafo."
                    )

                todos_paragrafos.extend(pars)

            meta["paragrafos_origem"] = todos_paragrafos

    # -------------------------
    # texto
    # -------------------------
    texto_fragmento = frag.get("texto_fragmento")
    texto_normalizado = frag.get("texto_normalizado")
    texto_fonte_reconstituido = frag.get("texto_fonte_reconstituido")

    if not isinstance(texto_fragmento, str):
        add_erro(erros, fragment_id, "texto_fragmento_invalido", "texto_fragmento ausente ou não-string.")
        texto_fragmento = ""

    if not isinstance(texto_normalizado, str):
        add_erro(erros, fragment_id, "texto_normalizado_invalido", "texto_normalizado ausente ou não-string.")
        texto_normalizado = ""

    if not isinstance(texto_fonte_reconstituido, str):
        add_erro(
            erros,
            fragment_id,
            "texto_fonte_reconstituido_invalido",
            "texto_fonte_reconstituido ausente ou não-string."
        )
        texto_fonte_reconstituido = ""

    texto_normalizado_recalc = normalizar_espacos(texto_fragmento)
    if texto_normalizado != texto_normalizado_recalc:
        add_erro(
            erros,
            fragment_id,
            "texto_normalizado_diverge",
            "texto_normalizado não coincide com a normalização de texto_fragmento."
        )

    if texto_fonte_reconstituido != texto_fragmento:
        add_erro(
            erros,
            fragment_id,
            "texto_fonte_reconstituido_diverge",
            "texto_fonte_reconstituido diverge de texto_fragmento."
        )

    # -------------------------
    # métricas derivadas
    # -------------------------
    paragrafos_agregados = frag.get("paragrafos_agregados")
    frases_aproximadas = frag.get("frases_aproximadas")
    n_chars_fragmento = frag.get("n_chars_fragmento")
    densidade = frag.get("densidade_aprox")

    if not isinstance(paragrafos_agregados, int) or paragrafos_agregados < 1:
        add_erro(erros, fragment_id, "paragrafos_agregados_invalido", "paragrafos_agregados inválido.")
    else:
        n_pars_real = len(meta["paragrafos_origem"])
        if n_pars_real and paragrafos_agregados != n_pars_real:
            add_erro(
                erros,
                fragment_id,
                "paragrafos_agregados_diverge",
                f"paragrafos_agregados={paragrafos_agregados} mas há {n_pars_real} parágrafos em origem."
            )

    frases_recalc = contar_frases_aprox(texto_fragmento)
    if not isinstance(frases_aproximadas, int) or frases_aproximadas < 0:
        add_erro(erros, fragment_id, "frases_aproximadas_invalido", "frases_aproximadas inválido.")
    elif frases_aproximadas != frases_recalc:
        add_erro(
            erros,
            fragment_id,
            "frases_aproximadas_diverge",
            f"frases_aproximadas={frases_aproximadas}, esperado={frases_recalc}."
        )

    n_chars_recalc = len(texto_normalizado_recalc)
    if not isinstance(n_chars_fragmento, int) or n_chars_fragmento < 0:
        add_erro(erros, fragment_id, "n_chars_fragmento_invalido", "n_chars_fragmento inválido.")
    elif n_chars_fragmento != n_chars_recalc:
        add_erro(
            erros,
            fragment_id,
            "n_chars_fragmento_diverge",
            f"n_chars_fragmento={n_chars_fragmento}, esperado={n_chars_recalc}."
        )

    densidade_recalc = densidade_aprox(texto_fragmento)
    if densidade not in {"baixa", "media", "alta"}:
        add_erro(erros, fragment_id, "densidade_invalida", "densidade_aprox fora dos valores válidos.")
    elif densidade != densidade_recalc:
        add_erro(
            erros,
            fragment_id,
            "densidade_diverge",
            f"densidade_aprox='{densidade}', esperado='{densidade_recalc}'."
        )

    # -------------------------
    # tipo_material_fonte
    # -------------------------
    if not is_non_empty_str(frag.get("tipo_material_fonte")):
        add_erro(erros, fragment_id, "tipo_material_fonte_invalido", "tipo_material_fonte ausente ou inválido.")

    # -------------------------
    # segmentacao
    # -------------------------
    segmentacao = frag.get("segmentacao")
    if not isinstance(segmentacao, dict):
        add_erro(erros, fragment_id, "segmentacao_invalida", "Campo 'segmentacao' ausente ou inválido.")
    else:
        tipo_unidade = segmentacao.get("tipo_unidade")
        criterio = segmentacao.get("criterio_de_unidade")
        houve_fusao = segmentacao.get("houve_fusao_de_paragrafos")
        houve_corte = segmentacao.get("houve_corte_interno")
        tipo_seg = segmentacao.get("container_tipo_segmentacao")

        if tipo_unidade not in TIPOS_UNIDADE_VALIDOS:
            add_erro(erros, fragment_id, "tipo_unidade_invalido", f"tipo_unidade inválido: {tipo_unidade}")
        if criterio not in CRITERIOS_UNIDADE_VALIDOS:
            add_erro(erros, fragment_id, "criterio_unidade_invalido", f"criterio_de_unidade inválido: {criterio}")
        if not isinstance(houve_fusao, bool):
            add_erro(erros, fragment_id, "houve_fusao_invalido", "houve_fusao_de_paragrafos deve ser bool.")
        if not isinstance(houve_corte, bool):
            add_erro(erros, fragment_id, "houve_corte_invalido", "houve_corte_interno deve ser bool.")
        if tipo_seg != TIPO_SEGMENTACAO_ESPERADO:
            add_erro(
                erros,
                fragment_id,
                "tipo_segmentacao_diverge",
                f"container_tipo_segmentacao='{tipo_seg}', esperado='{TIPO_SEGMENTACAO_ESPERADO}'."
            )

        if isinstance(houve_fusao, bool) and isinstance(paragrafos_agregados, int):
            esperado_fusao = paragrafos_agregados > 1
            if houve_fusao != esperado_fusao:
                add_erro(
                    erros,
                    fragment_id,
                    "houve_fusao_diverge",
                    f"houve_fusao_de_paragrafos={houve_fusao}, esperado={esperado_fusao}."
                )

    # -------------------------
    # campos enriquecidos
    # -------------------------
    funcao = frag.get("funcao_textual_dominante")
    if funcao not in FUNCOES_TEXTUAIS_VALIDAS:
        add_erro(erros, fragment_id, "funcao_textual_invalida", f"funcao_textual_dominante inválida: {funcao}")

    tema = frag.get("tema_dominante_provisorio")
    if not isinstance(tema, str):
        add_erro(erros, fragment_id, "tema_invalido", "tema_dominante_provisorio deve ser string.")
    else:
        tema_limpo = tema.strip()
        if tema != tema.lower():
            add_aviso(avisos, fragment_id, "tema_nao_minusculas", "tema_dominante_provisorio não está em minúsculas.")
        if len(tema_limpo.split()) > 5:
            add_erro(erros, fragment_id, "tema_longo", "tema_dominante_provisorio tem mais de 5 palavras.")

    conceitos = frag.get("conceitos_relevantes_provisorios")
    if not isinstance(conceitos, list) or not all(isinstance(x, str) for x in conceitos):
        add_erro(
            erros,
            fragment_id,
            "conceitos_invalidos",
            "conceitos_relevantes_provisorios deve ser lista de strings."
        )
    else:
        if len(conceitos) > 5:
            add_erro(erros, fragment_id, "conceitos_excesso", "Mais de 5 conceitos_relevantes_provisorios.")
        vistos = set()
        for c in conceitos:
            if c != c.lower():
                add_aviso(avisos, fragment_id, "conceito_nao_minusculas", f"Conceito não está em minúsculas: '{c}'.")
            key = c.strip().lower()
            if key in vistos:
                add_erro(erros, fragment_id, "conceito_repetido", f"Conceito repetido: '{c}'.")
            vistos.add(key)
            if len(c.strip().split()) > 4:
                add_erro(erros, fragment_id, "conceito_longo", f"Conceito com mais de 4 palavras: '{c}'.")

    integridade = frag.get("integridade_semantica")
    if not isinstance(integridade, dict):
        add_erro(erros, fragment_id, "integridade_invalida", "integridade_semantica ausente ou inválida.")
        grau = None
    else:
        grau = integridade.get("grau")
        if grau not in GRAUS_INTEGRIDADE_VALIDOS:
            add_erro(erros, fragment_id, "integridade_grau_invalido", f"grau inválido: {grau}")

    confianca = frag.get("confianca_segmentacao")
    if confianca not in CONFIANCA_VALIDA:
        add_erro(erros, fragment_id, "confianca_invalida", f"confianca_segmentacao inválida: {confianca}")
    elif grau in {"baixo", "medio"} and confianca == "alta":
        add_erro(
            erros,
            fragment_id,
            "confianca_incompativel_com_integridade",
            f"grau='{grau}' é incompatível com confianca_segmentacao='alta'."
        )

    # -------------------------
    # relacoes_locais
    # -------------------------
    rel = frag.get("relacoes_locais")
    if not isinstance(rel, dict):
        add_erro(erros, fragment_id, "relacoes_locais_invalidas", "relacoes_locais ausente ou inválido.")
    else:
        for k in ["fragmento_anterior", "fragmento_seguinte"]:
            if rel.get(k) is not None and not isinstance(rel.get(k), str):
                add_erro(erros, fragment_id, f"{k}_invalido", f"{k} deve ser string ou null.")
        for k in ["continua_anterior", "prepara_seguinte"]:
            if not isinstance(rel.get(k), bool):
                add_erro(erros, fragment_id, f"{k}_invalido", f"{k} deve ser bool.")

    # -------------------------
    # estado / sinalizador
    # -------------------------
    if frag.get("estado_revisao") != ESTADO_REVISAO_ESPERADO:
        add_erro(
            erros,
            fragment_id,
            "estado_revisao_diverge",
            f"estado_revisao='{frag.get('estado_revisao')}', esperado='{ESTADO_REVISAO_ESPERADO}'."
        )

    sinal = frag.get("sinalizador_para_cadencia")
    if not isinstance(sinal, dict):
        add_erro(
            erros,
            fragment_id,
            "sinalizador_invalido",
            "sinalizador_para_cadencia ausente ou inválido."
        )
    else:
        pronto = sinal.get("pronto_para_extrator_cadencia")
        requer = sinal.get("requer_revisao_manual_prioritaria")
        if pronto is not True:
            add_erro(
                erros,
                fragment_id,
                "pronto_para_extrator_invalido",
                "pronto_para_extrator_cadencia deve ser True."
            )
        if not isinstance(requer, bool):
            add_erro(
                erros,
                fragment_id,
                "requer_revisao_invalido",
                "requer_revisao_manual_prioritaria deve ser bool."
            )
        elif confianca in CONFIANCA_VALIDA:
            esperado = (confianca == "baixa")
            if requer != esperado:
                add_erro(
                    erros,
                    fragment_id,
                    "requer_revisao_diverge_confianca",
                    f"requer_revisao_manual_prioritaria={requer}, esperado={esperado} a partir da confiança."
                )

    # -------------------------
    # metadados
    # -------------------------
    md = frag.get("_metadados_segmentador")
    if not isinstance(md, dict):
        add_erro(
            erros,
            fragment_id,
            "metadados_invalido",
            "_metadados_segmentador ausente ou inválido."
        )
    else:
        if not is_non_empty_str(md.get("modelo")):
            add_erro(erros, fragment_id, "modelo_invalido", "_metadados_segmentador.modelo inválido.")
        if not is_non_empty_str(md.get("versao_segmentador")):
            add_erro(erros, fragment_id, "versao_invalida", "_metadados_segmentador.versao_segmentador inválido.")
        if not is_non_empty_str(md.get("timestamp")):
            add_erro(erros, fragment_id, "timestamp_invalido", "_metadados_segmentador.timestamp inválido.")

        hash_esperado = sha256(texto_normalizado_recalc)
        hash_real = md.get("hash_texto_normalizado")
        if hash_real != hash_esperado:
            add_erro(
                erros,
                fragment_id,
                "hash_texto_diverge",
                "hash_texto_normalizado não coincide com o hash do texto_normalizado recalculado."
            )

    return meta


# =========================================================
# VALIDAÇÃO TRANSVERSAL POR CONTAINER
# =========================================================

def validar_por_container(
    fragmentos: List[Dict[str, Any]],
    metas: List[Dict[str, Any]],
    erros: List[Dict[str, Any]],
    avisos: List[Dict[str, Any]],
) -> None:
    por_container: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for frag, meta in zip(fragmentos, metas):
        cid = meta.get("container_id")
        if cid:
            por_container[cid].append({
                "frag": frag,
                "meta": meta,
            })

    for cid, items in por_container.items():
        items.sort(key=lambda x: (x["meta"].get("seq") is None, x["meta"].get("seq")))

        # 1) sequência contínua 001..N
        seqs = [x["meta"]["seq"] for x in items if isinstance(x["meta"].get("seq"), int)]
        if seqs:
            esperadas = list(range(1, len(seqs) + 1))
            if seqs != esperadas:
                add_erro(
                    erros,
                    f"{cid}::*",
                    "sequencia_fragmentos_quebrada",
                    f"Sequência de fragmentos no container '{cid}' é {seqs}, esperado {esperadas}."
                )

        # 2) sem duplicação de parágrafos dentro do container
        paragrafos_vistos = []
        for x in items:
            paragrafos_vistos.extend(x["meta"].get("paragrafos_origem", []))

        repetidos = sorted({p for p in paragrafos_vistos if paragrafos_vistos.count(p) > 1})
        if repetidos:
            add_erro(
                erros,
                f"{cid}::*",
                "paragrafos_repetidos_no_container",
                f"Parágrafos repetidos entre fragmentos do mesmo container: {repetidos}"
            )

        # 3) relações locais coerentes
        total = len(items)
        for idx, x in enumerate(items, start=1):
            frag = x["frag"]
            fragment_id = frag.get("fragment_id", "<sem_fragment_id>")
            rel = frag.get("relacoes_locais", {})
            seg = frag.get("segmentacao", {})

            prev_esperado = f"{cid}_SEG_{idx-1:03d}" if idx > 1 else None
            next_esperado = f"{cid}_SEG_{idx+1:03d}" if idx < total else None

            if isinstance(rel, dict):
                if rel.get("fragmento_anterior") != prev_esperado:
                    add_erro(
                        erros,
                        fragment_id,
                        "relacao_anterior_diverge",
                        f"fragmento_anterior='{rel.get('fragmento_anterior')}', esperado='{prev_esperado}'."
                    )
                if rel.get("fragmento_seguinte") != next_esperado:
                    add_erro(
                        erros,
                        fragment_id,
                        "relacao_seguinte_diverge",
                        f"fragmento_seguinte='{rel.get('fragmento_seguinte')}', esperado='{next_esperado}'."
                    )
                if rel.get("continua_anterior") != (idx > 1):
                    add_erro(
                        erros,
                        fragment_id,
                        "continua_anterior_diverge",
                        f"continua_anterior={rel.get('continua_anterior')}, esperado={idx > 1}."
                    )
                if rel.get("prepara_seguinte") != (idx < total):
                    add_erro(
                        erros,
                        fragment_id,
                        "prepara_seguinte_diverge",
                        f"prepara_seguinte={rel.get('prepara_seguinte')}, esperado={idx < total}."
                    )

            # 4) houve_corte_interno coerente com nº total de fragmentos no container
            if isinstance(seg, dict):
                esperado = total > 1
                if seg.get("houve_corte_interno") != esperado:
                    add_erro(
                        erros,
                        fragment_id,
                        "houve_corte_interno_diverge",
                        f"houve_corte_interno={seg.get('houve_corte_interno')}, esperado={esperado}."
                    )


# =========================================================
# MAIN
# =========================================================

def main() -> int:
    base = Path(".")
    ficheiro_fragmentos = base / FICHEIRO_FRAGMENTOS
    ficheiro_relatorio = base / FICHEIRO_RELATORIO

    if not ficheiro_fragmentos.exists():
        print(f"ERRO: ficheiro não encontrado: {ficheiro_fragmentos}")
        return 2

    try:
        data = load_json(ficheiro_fragmentos)
    except Exception as e:
        print(f"ERRO ao ler JSON: {e}")
        return 2

    erros: List[Dict[str, Any]] = []
    avisos: List[Dict[str, Any]] = []

    if not isinstance(data, list):
        print("ERRO: a raiz de fragmentos_resegmentados.json tem de ser uma lista.")
        return 2

    metas: List[Dict[str, Any]] = []

    # 0) unicidade de fragment_id
    ids = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("fragment_id"), str):
            ids.append(item["fragment_id"])

    ids_repetidos = sorted({x for x in ids if ids.count(x) > 1})
    for rid in ids_repetidos:
        add_erro(erros, rid, "fragment_id_repetido", f"fragment_id repetido: {rid}")

    # 1) validação individual
    for item in data:
        meta = validar_fragmento(item, erros, avisos)
        metas.append(meta)

    # 2) validação transversal
    validar_por_container(data, metas, erros, avisos)

    # 3) relatório
    relatorio = {
        "ficheiro": str(ficheiro_fragmentos),
        "n_fragmentos": len(data),
        "n_erros": len(erros),
        "n_avisos": len(avisos),
        "valido": len(erros) == 0,
        "erros": erros,
        "avisos": avisos,
    }
    save_json(ficheiro_relatorio, relatorio)

    print("=" * 90)
    print("VALIDAÇÃO DE fragmentos_resegmentados.json")
    print("=" * 90)
    print(f"Fragmentos: {len(data)}")
    print(f"Erros:      {len(erros)}")
    print(f"Avisos:     {len(avisos)}")
    print(f"Relatório:  {ficheiro_relatorio}")
    print("=" * 90)

    if erros:
        print("\nPrimeiros erros:")
        for e in erros[:20]:
            print(f"- [{e['fragment_id']}] {e['codigo']}: {e['detalhe']}")
        return 1

    print("\n✅ Validação concluída sem erros.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())