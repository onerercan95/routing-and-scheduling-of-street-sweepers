from typing import List, Tuple, Dict, Any
import networkx as nx

Edge = Tuple[int, int, int]  # (u,v,key)

def edge_time_old(E: nx.MultiDiGraph, e: Edge, time_attr: str = "cost") -> float:
    u, v, k = e
    data = E[u][v][k]
    if time_attr in data and data[time_attr] is not None:
        return float(data[time_attr])
    if "travel_time" in data and data["travel_time"] is not None:
        return float(data["travel_time"])
    if "length" in data and data["length"] is not None:
        return float(data["length"]) / 10.0
    return 0.0

def edge_time(E, e, time_attr: str = "cost"):
    u,v,k = e
    d = E[u][v][k]
    length = d.get("length",0)

    if d.get("mode") == "SWEEP":
        speed = 1.9   # m/s
    elif d.get("mode") == "DEADHEAD":
        speed = 3.6   # m/s
    else:
        return length / 2.5

    return length / speed

def is_sweep(E: nx.MultiDiGraph, e: Edge) -> bool:
    u, v, k = e
    return E[u][v][k].get("mode", "").upper() == "SWEEP"

def split_giant_tour(
    E: nx.MultiDiGraph,
    tour: List[Edge],
    max_route_time: float,
    time_attr: str = "cost",
) -> List[List[Edge]]:
    routes: List[List[Edge]] = []
    cur: List[Edge] = []
    t = 0.0

    for e in tour:
        dt = edge_time(E, e)

        if cur and (t + dt) > max_route_time:
            routes.append(cur)
            cur = []
            t = 0.0

        cur.append(e)
        t += dt

    if cur:
        routes.append(cur)

    return routes

def route_stats(E: nx.MultiDiGraph, route: List[Edge], time_attr: str = "cost") -> Dict[str, Any]:
    sweep_t = 0.0
    dead_t = 0.0
    total_t = 0.0

    for e in route:
        dt = edge_time(E, e, time_attr=time_attr)
        total_t += dt
        if is_sweep(E, e):
            sweep_t += dt
        else:
            dead_t += dt

    return {
        "edges": len(route),
        "total_time": round(total_t / 3600, 2),
        "sweep_time": round(sweep_t / 3600, 2),
        "deadhead_time": round(dead_t / 3600, 2),
        "deadhead_pct": round((dead_t / total_t) if total_t > 0 else 0.0, 2),
    }
