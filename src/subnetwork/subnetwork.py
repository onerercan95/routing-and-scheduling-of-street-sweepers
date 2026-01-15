import osmnx as ox
from src.routing.utils import *

# Extracts graph K from a given graph F based on sweepableness of streets. Regulations are applied here.
def extract_K(F, allowed_highways):
    # Extract GeoDataFrame edge graph of F
    edges = ox.graph_to_gdfs(F, nodes=False).reset_index()

    # Each edge holds | u | v | key | highway | length | geometry | etc.
    # Highway data can hold multiple types of tags like ["primary", "trunk"]. Normalize it so that it only holds the first tag.
    edges["highway_norm"] = edges["highway"].apply(normalize_highway)

    # Tag edges as sweepable or not based on the given regulation
    # edges["sweepable"] = edges["highway_norm"].apply(assign_regulation)
    edges["sweepable"] = edges["highway_norm"].apply(
        lambda h: h in allowed_highways
    )

    # Discard unavailable edges
    sweepable_edges = edges[edges["sweepable"]]

    # Extract subgraph from F based on seepable_edges
    K = F.edge_subgraph(list(zip(sweepable_edges["u"], sweepable_edges["v"], sweepable_edges["key"]))).copy()

    return K