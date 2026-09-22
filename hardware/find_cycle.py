import pathlib
from qiskit_quantuminspire.qi_provider import QIProvider

b = QIProvider().get_backend("Tuna-17")
bt = b.get_backend_type()
topo = bt.topology or []
edges = set()
for a, c in topo:
    edges.add((min(a, c), max(a, c)))
print("Tuna-17 無向邊數:", len(edges))
adj = {}
for a, c in edges:
    adj.setdefault(a, set()).add(c)
    adj.setdefault(c, set()).add(a)
print("節點:", sorted(adj))
for k in sorted(adj):
    print("  q%-3d -> %s" % (k, sorted(adj[k])))

# 找 5-環（Hamiltonian cycle on 5 distinct qubits）
import itertools
nodes = sorted(adj)
found = []
for comb in itertools.combinations(nodes, 5):
    # 在 induced subgraph 上找 5-cycle
    sub = {v: (adj[v] & set(comb)) for v in comb}
    if any(len(sub[v]) < 2 for v in comb):
        continue
    start = comb[0]
    # DFS 找 Hamiltonian cycle
    def dfs(path):
        if len(path) == 5:
            if path[0] in sub[path[-1]]:
                return path + [path[0]]
            return None
        for w in sorted(sub[path[-1]]):
            if w not in path:
                r = dfs(path + [w])
                if r: return r
        return None
    cyc = dfs([start])
    if cyc:
        found.append(cyc)
print()
print("找到 %d 個 5-環" % len(found))
for c in found[:10]:
    print("  ", c)
