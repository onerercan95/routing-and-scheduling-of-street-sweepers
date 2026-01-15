import os
import osmnx as ox

ox.settings.use_cache = True
ox.settings.cache_folder = "dat/raw/osmnx_cache"

def load_street_network(place_name: str):
    graph_path = "dat/raw/graph_cache/" + place_name
    if os.path.exists(graph_path):
        print(f"[INFO] Loading cached street network ({place_name}) from disk")
        return ox.load_graphml(graph_path)
        
    print(f"[INFO] Downloading street network ({place_name})")
    G = ox.graph_from_place(place_name, network_type="drive", simplify=True)
    
    G = ox.truncate.largest_component(G, strongly=True)

    ox.save_graphml(G, graph_path)
    print(f"[INFO] Loaded graph - Name ({place_name}) - Nodes ({len(G.nodes)}) - Edges ({len(G.edges)})")
    return G


def inspect_highway_tags(G):
    edges = ox.graph_to_gdfs(G, nodes=False)

    if "highway" not in edges.columns:
        raise RuntimeError("OSM data does NOT contain 'highway' tags")

    print("[INFO] Highway tag distribution:")
    print(edges["highway"].value_counts().head(10))

    return edges