import json
import os
from collections import defaultdict, Counter, deque

# ==========
# Caminhos (ajusta se necessário)
# ==========
PATH_DEFINICOES = r"../09_Prompt/config/definicoes.json"
PATH_PROPOSICOES = r"../09_Prompt/data/extracao_ontologica_final.json"

OUT_DIR = r"data/grafo"
OUT_DOT = os.path.join(OUT_DIR, "grafo_dependencias.dot")
OUT_GRAPHML = os.path.join(OUT_DIR, "grafo_dependencias.graphml")
OUT_RESUMO = os.path.join(OUT_DIR, "grafo_resumo.txt")

# ==========
# Grafo simples (sem depender de networkx)
# ==========
class Digrafo:
    def __init__(self):
        self.adj = defaultdict(set)      # u -> {v}
        self.rev = defaultdict(set)      # v -> {u}
        self.nodes = {}                  # id -> attrs dict

    def add_node(self, n, **attrs):
        if n not in self.nodes:
            self.nodes[n] = {}
        self.nodes[n].update(attrs)

    def add_edge(self, u, v):

        # normalização defensiva
        if isinstance(u, dict):
            u = u.get("id") or u.get("campo_principal")
        if isinstance(v, dict):
            v = v.get("id") or v.get("campo_principal")

        if not isinstance(u, str) or not isinstance(v, str):
            return  # ignora lixo estrutural

        self.add_node(u)
        self.add_node(v)
        self.adj[u].add(v)
        self.rev[v].add(u)



    def indeg(self, n): return len(self.rev.get(n, set()))
    def outdeg(self, n): return len(self.adj.get(n, set()))

    def edges(self):
        for u, vs in self.adj.items():
            for v in vs:
                yield (u, v)

def ler_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ==========
# Detecção de ciclos (Kahn + extracção de SCC se necessário)
# ==========
def kahn_toposort(g: Digrafo):
    indeg = {n: g.indeg(n) for n in g.nodes}
    q = deque([n for n, d in indeg.items() if d == 0])
    ordem = []
    while q:
        n = q.popleft()
        ordem.append(n)
        for v in list(g.adj.get(n, [])):
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    ciclos = [n for n, d in indeg.items() if d > 0]
    return ordem, ciclos

# Kosaraju para SCC (componentes fortemente ligadas)
def scc_kosaraju(g: Digrafo):
    visited = set()
    order = []

    def dfs1(u):
        visited.add(u)
        for v in g.adj.get(u, []):
            if v not in visited:
                dfs1(v)
        order.append(u)

    for n in g.nodes:
        if n not in visited:
            dfs1(n)

    visited.clear()
    comps = []

    def dfs2(u, comp):
        visited.add(u)
        comp.append(u)
        for v in g.rev.get(u, []):
            if v not in visited:
                dfs2(v, comp)

    for n in reversed(order):
        if n not in visited:
            comp = []
            dfs2(n, comp)
            comps.append(comp)

    # devolve apenas SCCs com tamanho > 1 (ciclos reais)
    return [c for c in comps if len(c) > 1]

# ==========
# Export GraphViz DOT
# ==========
def export_dot(g: Digrafo, path: str):
    def esc(s):
        return str(s).replace('"', '\\"')

    with open(path, "w", encoding="utf-8") as f:
        f.write("digraph G {\n")
        f.write('  rankdir="LR";\n')
        f.write('  node [shape=box, fontsize=10];\n')

        # nós
        for n, attrs in g.nodes.items():
            label = attrs.get("label", n)
            ntype = attrs.get("type", "")
            nivel = attrs.get("nivel", "")
            # cor/shape simples por tipo
            if ntype == "def":
                shape = "ellipse"
            elif ntype == "prop":
                shape = "box"
            else:
                shape = "diamond"
            extra = []
            extra.append(f'label="{esc(label)}"')
            extra.append(f'shape={shape}')
            if nivel != "":
                extra.append(f'tooltip="nivel={esc(nivel)}"')
            f.write(f'  "{esc(n)}" [{", ".join(extra)}];\n')

        # arestas
        for u, v in g.edges():
            f.write(f'  "{esc(u)}" -> "{esc(v)}";\n')

        f.write("}\n")

# ==========
# Export GraphML (minimamente compatível com Gephi/yEd)
# ==========
def export_graphml(g: Digrafo, path: str):
    # GraphML mínimo com atributos de nó
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
        f.write('  <key id="d0" for="node" attr.name="label" attr.type="string"/>\n')
        f.write('  <key id="d1" for="node" attr.name="type" attr.type="string"/>\n')
        f.write('  <key id="d2" for="node" attr.name="nivel" attr.type="int"/>\n')
        f.write('  <graph id="G" edgedefault="directed">\n')

        # nós
        for n, attrs in g.nodes.items():
            label = attrs.get("label", n)
            ntype = attrs.get("type", "")
            nivel = attrs.get("nivel", -1)
            f.write(f'    <node id="{n}">\n')
            f.write(f'      <data key="d0">{label}</data>\n')
            f.write(f'      <data key="d1">{ntype}</data>\n')
            try:
                niv_int = int(nivel)
            except Exception:
                niv_int = -1
            f.write(f'      <data key="d2">{niv_int}</data>\n')
            f.write('    </node>\n')

        # arestas
        i = 0
        for u, v in g.edges():
            f.write(f'    <edge id="e{i}" source="{u}" target="{v}"/>\n')
            i += 1

        f.write('  </graph>\n')
        f.write('</graphml>\n')

# ==========
# Construção do grafo
# ==========
def construir_grafo():
    defs = ler_json(PATH_DEFINICOES)
    props = ler_json(PATH_PROPOSICOES)

    g = Digrafo()

    # ---- nós de definições
    id_por_campo = {}
    for d in defs:
        did = d["id"]
        campo = d.get("campo", did)
        id_por_campo[campo] = did
        g.add_node(did, type="def", nivel=d.get("nivel", ""), label=f'{did}:{campo}')

    # ---- arestas de definições (dependências + exclui como aresta separada opcional)
    for d in defs:
        did = d["id"]
        for dep in d.get("depende_de", []):
            # já devem estar em ID; se vierem como campo, tenta mapear
            dep_id = id_por_campo.get(dep, dep)
            g.add_edge(did, dep_id)
        # Se quiseres também modelar exclusões:
        # for ex in d.get("exclui", []):
        #     ex_id = id_por_campo.get(ex, ex)
        #     g.add_edge(did, ex_id)

    # ---- nós e arestas de proposições
    for p in props:
        pid = p.get("id_proposicao")
        if not pid:
            continue
        lv = p.get("localizacao_vertical", {}) or {}
        cp = lv.get("campo_principal")
        nivel = lv.get("nivel", "")

        g.add_node(pid, type="prop", nivel=nivel, label=pid)

        # ancoragem: proposição -> campo_principal (def)
        if cp:
            g.add_edge(pid, cp)

        # dependencias: proposição -> defs
        for dep in (p.get("dependencias") or []):
            g.add_edge(pid, dep)

        # gera / degeneracao / reintegracao (proposição -> defs)
        for dep in (p.get("gera") or []):
            g.add_edge(pid, dep)
        for dep in (p.get("degeneracao_possivel") or []):
            g.add_edge(pid, dep)
        for dep in (p.get("reintegracao") or []):
            g.add_edge(pid, dep)

    return g

def resumo(g: Digrafo):
    # estatísticas básicas
    total_nodes = len(g.nodes)
    total_edges = sum(len(vs) for vs in g.adj.values())
    tipos = Counter(attrs.get("type", "??") for attrs in g.nodes.values())

    # nós mais conectados (grau total)
    graus = []
    for n in g.nodes:
        graus.append((n, g.indeg(n) + g.outdeg(n), g.indeg(n), g.outdeg(n), g.nodes[n].get("type","")))
    graus.sort(key=lambda x: x[1], reverse=True)

    ordem, ciclos = kahn_toposort(g)
    sccs = scc_kosaraju(g) if ciclos else []

    linhas = []
    linhas.append("GRAFO DE DEPENDÊNCIAS — RESUMO\n")
    linhas.append(f"Nós: {total_nodes}")
    linhas.append(f"Arestas: {total_edges}")
    linhas.append(f"Tipos: {dict(tipos)}")
    linhas.append("")
    linhas.append(f"Toposort: {'OK (sem ciclos)' if not ciclos else 'CICLOS DETETADOS'}")
    if ciclos:
        linhas.append(f"Nós em ciclo (Kahn): {len(ciclos)}")
        linhas.append(f"SCCs (componentes fortemente ligadas) >1: {len(sccs)}")
        # mostra até 10 SCCs pequenas
        for i, comp in enumerate(sccs[:10], 1):
            linhas.append(f"  SCC {i} (tamanho {len(comp)}): {comp[:12]}{'...' if len(comp)>12 else ''}")
    linhas.append("")
    linhas.append("Top 30 nós por grau total (in+out):")
    for n, gt, gi, go, t in graus[:30]:
        label = g.nodes[n].get("label", n)
        linhas.append(f"  {n} [{t}] grau={gt} (in={gi}, out={go}) :: {label}")

    return "\n".join(linhas)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    g = construir_grafo()

    export_dot(g, OUT_DOT)
    export_graphml(g, OUT_GRAPHML)

    texto_resumo = resumo(g)
    with open(OUT_RESUMO, "w", encoding="utf-8") as f:
        f.write(texto_resumo)

    print("OK")
    print(f"- DOT:     {OUT_DOT}")
    print(f"- GraphML: {OUT_GRAPHML}")
    print(f"- Resumo:  {OUT_RESUMO}")

if __name__ == "__main__":
    main()
