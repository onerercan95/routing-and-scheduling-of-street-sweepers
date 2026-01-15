import networkx as nx
from src.routing.transportation import *
from src.routing.connectivity import *

def _total_pos_imbalance(E):
    return sum(max(0, E.in_degree(n) - E.out_degree(n)) for n in E.nodes())

def _add_directed_step(E, F, a, b, weight="cost"):
    if F.has_edge(a, b):
        k = pick_min_cost_edge_key(F, a, b, weight_attr=weight)
        data = F[a][b][k].copy()
        data["reversed_from_oneway"] = False
        E.add_edge(a, b, **data)
        return

    if F.has_edge(b, a):
        k = pick_min_cost_edge_key(F, b, a, weight_attr=weight)
        data = F[b][a][k].copy()
        data["reversed_from_oneway"] = True
        geom = data.get("geometry", None)
        if geom is not None and hasattr(geom, "coords"):
            try:
                coords = list(geom.coords)[::-1]
                data["geometry"] = type(geom)(coords)
            except Exception:
                pass
                
        data["mode"] = "DEADHEAD_FORCE"
        data["is_force_balance"] = True
        E.add_edge(a, b, **data)
        return

    raise nx.NetworkXNoPath(f"No edge in F between {a} and {b} in either direction.")

def force_balance(E, F, weight="cost", max_iters=100000):
    Fu = F.to_undirected(as_view=True)

    it = 0
    prev = _total_pos_imbalance(E)

    while prev > 0 and it < max_iters:
        it += 1

        supplies = [n for n in E.nodes() if E.in_degree(n) > E.out_degree(n)]
        demands  = [n for n in E.nodes() if E.out_degree(n) > E.in_degree(n)]

        if not supplies or not demands:
            break

        s = supplies[0]
        d = demands[0]

        try:
            node_path = nx.shortest_path(F, s, d, weight=weight)
            directed_used = True
        except nx.NetworkXNoPath:
            node_path = nx.shortest_path(Fu, s, d, weight=weight)
            directed_used = False

        for a, b in zip(node_path[:-1], node_path[1:]):
            _add_directed_step(E, F, a, b, weight=weight)

        now = _total_pos_imbalance(E)

        if now >= prev:
            break

        prev = now

    ensure_node_coordinates(E, F)
    return E