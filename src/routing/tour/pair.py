import math
import networkx as nx

def compute_local_pairings(E):
    pairing = {}

    for n in E.nodes():
        in_edges = list(E.in_edges(n, keys=True))
        out_edges = list(E.out_edges(n, keys=True))

        if len(in_edges) != len(out_edges):
            raise ValueError(
                f"Node {n} not balanced: in={len(in_edges)} out={len(out_edges)}. "
                "Transportation step must be balanced. H is not balanced."
            )

        m = len(in_edges)
        if m == 0:
            continue

        cost = [[0.0] * m for _ in range(m)]
        for i, ine in enumerate(in_edges):
            for j, oute in enumerate(out_edges):
                cost[i][j] = pairing_cost(E, ine, oute)

        assign = hungarian_min_cost(cost)

        for i, j in enumerate(assign):
            pairing[in_edges[i]] = out_edges[j]

    return pairing

def pairing_cost(E, in_edge, out_edge) -> float:
    u, n, ki = in_edge
    n2, v, ko = out_edge
    assert n == n2

    bin_ = _edge_bearing_in(E, u, n, ki)
    bout = _edge_bearing_out(E, n, v, ko)
    ang = _angle_diff_deg(bin_, bout)

    in_mode = E[u][n][ki].get("mode", None)
    out_mode = E[n][v][ko].get("mode", None)

    return turn_penalty(ang) + mode_switch_penalty(in_mode, out_mode)

def hungarian_min_cost(cost):
    n = len(cost)
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (n + 1)
        used = [False] * (n + 1)

        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(0, n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break

        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    assignment = [-1] * n
    for j in range(1, n + 1):
        assignment[p[j] - 1] = j - 1
    return assignment


def turn_penalty(angle_deg: float) -> float:
    if angle_deg >= 150:
        return 1000.0
    if angle_deg >= 120:
        return 20.0
    if angle_deg >= 90:
        return 10.0
    if angle_deg >= 45:
        return 3.0
    return 0.0


def mode_switch_penalty(in_mode: str, out_mode: str) -> float:
    if in_mode is None or out_mode is None:
        return 0.0
    return 2.0 if in_mode != out_mode else 0.0

def _bearing_deg(x1, y1, x2, y2) -> float:
    dx = x2 - x1
    dy = y2 - y1
    ang = math.degrees(math.atan2(dx, dy))  # note swap: atan2(E, N)
    return (ang + 360.0) % 360.0


def _edge_bearing_in(E, u, v, k) -> float:
    data = E[u][v][k]
    geom = data.get("geometry", None)

    if geom is not None and hasattr(geom, "coords") and len(geom.coords) >= 2:
        x1, y1 = geom.coords[-2]
        x2, y2 = geom.coords[-1]
        return _bearing_deg(x1, y1, x2, y2)

    # fallback: use node coordinates
    x1, y1 = E.nodes[u]["x"], E.nodes[u]["y"]
    x2, y2 = E.nodes[v]["x"], E.nodes[v]["y"]
    return _bearing_deg(x1, y1, x2, y2)


def _edge_bearing_out(E, u, v, k) -> float:
    data = E[u][v][k]
    geom = data.get("geometry", None)

    if geom is not None and hasattr(geom, "coords") and len(geom.coords) >= 2:
        x1, y1 = geom.coords[0]
        x2, y2 = geom.coords[1]
        return _bearing_deg(x1, y1, x2, y2)

    x1, y1 = E.nodes[u]["x"], E.nodes[u]["y"]
    x2, y2 = E.nodes[v]["x"], E.nodes[v]["y"]
    return _bearing_deg(x1, y1, x2, y2)


def _angle_diff_deg(a, b) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)