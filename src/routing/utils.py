import osmnx as ox

def ensure_node_coordinates(H, F):
    for n in H.nodes:
        if "x" not in H.nodes[n] or "y" not in H.nodes[n]:
            if n in F.nodes:
                H.nodes[n]["x"] = F.nodes[n]["x"]
                H.nodes[n]["y"] = F.nodes[n]["y"]
            else:
                raise KeyError(f"Node {n} missing coordinates and not found in F")

def normalize_highway(value):
    if isinstance(value, list):
        return value[0]
    return value

def ensure_strong_component(F):
    return ox.truncate.largest_component(F, strongly=True)

def hours_between(start, end):
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))

    start_minutes = sh * 60 + sm
    end_minutes = eh * 60 + em

    return (end_minutes - start_minutes) / 60.0