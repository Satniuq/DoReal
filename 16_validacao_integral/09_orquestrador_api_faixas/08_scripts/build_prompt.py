
from __future__ import annotations

from typing import Any


PROMPT_INTRO = """Tu és um continuador rigoroso do procedimento de faixas expositivas controladas deste projeto.
Cumpre estritamente a hierarquia metodológica, a cadência canónica e o estado atual da pasta real.
Não transformes a peça em narrativa, capítulo ou comentário lateral.
Entrega apenas o corpo final do ficheiro em markdown, sem explicações fora do ficheiro.
"""


def build_prompt_text(state: dict[str, Any], context_pack: dict[str, Any]) -> str:
    kind = state['next_artifact_kind']
    expected = state['expected_artifact']
    target_folder = state['expected_folder']

    task_map = {
        'transicao': f"Produz a decisão de transição seguinte para gerar o ficheiro `{expected}`.",
        'abertura': f"Produz a abertura da próxima faixa para gerar o ficheiro `{expected}`.",
        'ensaio': f"Produz um ensaio controlado v1 para gerar o ficheiro `{expected}`.",
        'decisao': f"Produz a decisão/limite local para gerar o ficheiro `{expected}`.",
        'consolidacao': f"Produz a consolidação da faixa para gerar o ficheiro `{expected}`.",
    }

    specific_rules = {
        'transicao': "- compara o estado já ganho com a próxima zona legítima;\n- fixa o próximo ficheiro e, se possível, a pasta de destino;\n- não abras a faixa seguinte dentro desta mesma peça.",
        'abertura': "- fixa solo real mínimo, centro próprio, falso centro a bloquear, travões e fronteiras;\n- não faças ensaio dentro da abertura.",
        'ensaio': "- testa apenas até ao uso máximo atualmente suportado;\n- interrompe antes de mudança de regime;\n- não decidas a faixa toda dentro do ensaio.",
        'decisao': "- fixa o que passou, o que não passou e o próximo passo prudente;\n- se o ensaio falhou como ganho positivo, preserva-o como teste negativo controlado.",
        'consolidacao': "- substitui abertura, ensaio e decisão por um único texto ativo;\n- fixa limite máximo admissível e condição mínima de reabertura futura.",
    }

    segments_text = []
    for seg in context_pack['segments']:
        segments_text.append(f"### FONTE: {seg['label']}\nPATH: {seg['path']}\n\n{seg['content']}")
    joined = "\n\n" + ("\n\n".join(segments_text)) + "\n\n"

    return (
        PROMPT_INTRO
        + "\n"
        + task_map[kind]
        + "\n\n"
        + f"Pasta canónica de destino prevista: `{target_folder}`.\n"
        + f"Tipo de peça: `{kind}`.\n"
        + "Regras específicas:\n"
        + specific_rules[kind]
        + "\n\n"
        + "Usa as fontes abaixo por ordem de autoridade factual e metodológica. Não inventes nomes de ficheiros nem pastas se a decisão de transição já os tiver fixado.\n"
        + joined
    )
