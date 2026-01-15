import osmnx as ox
import matplotlib.pyplot as plt
import contextily as ctx
import folium
from folium.plugins import FeatureGroupSubGroup
from src.visualizing.highway_colors import *
import geopandas as gpd
from shapely.affinity import translate
from src.routing.utils import *
from src.routing.split_routes import *
import os

def plot_interactive_roads_hierarchical(G, output_path):
    nodes, edges = ox.graph_to_gdfs(G)

    edges["highway_norm"] = edges["highway"].apply(normalize_highway)

    center = nodes.geometry.unary_union.centroid

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=13,
        tiles="CartoDB positron"
    )

    roads_master = folium.FeatureGroup(
        name="Roads",
        show=True
    )
    roads_master.add_to(m)

    for highway_type, color in HIGHWAY_COLORS.items():
        subset = edges[edges["highway_norm"] == highway_type]
        if subset.empty:
            continue

        subgroup = FeatureGroupSubGroup(
            roads_master,
            name=f"Roads – {highway_type}"
        )

        folium.GeoJson(
            subset,
            style_function=lambda x, c=color: {
                "color": c,
                "weight": 3,
                "opacity": 0.9,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["name", "highway_norm"],
                aliases=["Street", "Type"],
                localize=True
            ),
        ).add_to(subgroup)

        subgroup.add_to(m)

    nodes_fg = folium.FeatureGroup(
        name="Nodes",
        show=False
    )

    for node_id, node in nodes.iterrows():
        folium.CircleMarker(
            location=[node.geometry.y, node.geometry.x],
            radius=2,
            color="red",
            fill=True,
            fill_opacity=0.8,
            popup=f"Node ID: {node_id}"
        ).add_to(nodes_fg)

    nodes_fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)

def plot_F_and_K(G, K, output_path):
    nodes_F, edges_F = ox.graph_to_gdfs(G)
    _, edges_K = ox.graph_to_gdfs(K)

    center = nodes_F.geometry.unary_union.centroid

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=13,
        tiles="CartoDB positron"
    )

    folium.GeoJson(
        edges_F.to_json(),
        name="F – All streets",
        style_function=lambda x: {
            "color": "gray",
            "weight": 1,
            "opacity": 0.4,
        },
    ).add_to(m)

    folium.GeoJson(
        edges_K.to_json(),
        name="K – Sweepable streets",
        style_function=lambda x: {
            "color": "#d73027",
            "weight": 3,
            "opacity": 0.9,
        },
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)

def plot_node_imbalance(G, imbalance_data, output_path):
    nodes, _ = ox.graph_to_gdfs(G)

    center = nodes.geometry.unary_union.centroid

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=13,
        tiles="CartoDB positron"
    )

    COLORS = {
        "balanced": "green",
        "supply": "red",
        "demand": "blue"
    }

    for node_id, row in nodes.iterrows():
        info = imbalance_data[node_id]
        node_type = info["type"]

        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=4 if node_type != "balanced" else 2,
            color=COLORS[node_type],
            fill=True,
            fill_opacity=0.9,
            popup=(
                f"Node {node_id}<br>"
                f"Type: {node_type}<br>"
                f"In: {info['in']}<br>"
                f"Out: {info['out']}"
            )
        ).add_to(m)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)

def plot_H_node_imbalance(H, imbalance_data, output_path):
    nodes, _ = ox.graph_to_gdfs(H)

    center = nodes.geometry.unary_union.centroid

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=13,
        tiles="CartoDB positron"
    )

    COLORS = {
        "balanced": "green",
        "supply": "red",
        "demand": "blue"
    }

    for node_id, row in nodes.iterrows():
        info = imbalance_data[node_id]
        node_type = info["type"]

        radius = 5 if node_type != "balanced" else 2

        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=radius,
            color=COLORS[node_type],
            fill=True,
            fill_opacity=0.9,
            popup=(
                f"Node {node_id}<br>"
                f"Type: {node_type}<br>"
                f"In: {info['in']}<br>"
                f"Out: {info['out']}<br>"
                f"Imbalance: {info['imbalance']}"
            )
        ).add_to(m)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)

ROUTE_COLORS = [
    "#e41a1c","#377eb8","#4daf4a","#984ea3",
    "#ff7f00","#ffff33","#a65628","#f781bf",
    "#999999","#66c2a5","#fc8d62","#8da0cb"
]

def draw_edge(E, u, v, k, color, group):
    data = E[u][v][k]

    if "geometry" in data and data["geometry"] is not None:
        folium.GeoJson(
            data["geometry"],
            style_function=lambda x, c=color: {
                "color": c,
                "weight": 4,
                "opacity": 0.9
            }
        ).add_to(group)
    else:
        p1 = (E.nodes[u]["y"], E.nodes[u]["x"])
        p2 = (E.nodes[v]["y"], E.nodes[v]["x"])
        folium.PolyLine([p1,p2], color=color, weight=4, opacity=0.9).add_to(group)


def visualize_tour_and_routes(E, tour, routes, output_path):

    nodes, edges = ox.graph_to_gdfs(E)

    center = nodes.geometry.unary_union.centroid
    m = folium.Map(location=[center.y, center.x], zoom_start=13, tiles="CartoDB positron")

    # Base roads
    base = folium.FeatureGroup(name="All Roads", show=True)
    folium.GeoJson(
        edges.to_json(),
        style_function=lambda x:{
            "color":"gray","weight":1,"opacity":0.3
        }
    ).add_to(base)
    base.add_to(m)

    # Giant tour
    tour_group = folium.FeatureGroup(name="Giant Tour", show=False)
    for u,v,k in tour:
        draw_edge(E,u,v,k,"red",tour_group)
    tour_group.add_to(m)

    # Master group for all routes
    routes_master = folium.FeatureGroup(name="All Subroutes", show=True)

    # Individual routes
    for i, route in enumerate(routes):
        color = ROUTE_COLORS[i % len(ROUTE_COLORS)]

        fg = folium.FeatureGroup(name=f"Route {i+1}", show=True)

        for u,v,k in route:
            draw_edge(E,u,v,k,color,fg)

        fg.add_to(routes_master)

    routes_master.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)

def visualize_giant_tour(E, tour, output_path):
    nodes, edges = ox.graph_to_gdfs(E)

    center = nodes.geometry.unary_union.centroid
    m = folium.Map(location=[center.y, center.x], zoom_start=13, tiles="CartoDB positron")

    # Draw base roads
    folium.GeoJson(
        edges.to_json(),
        name="All Roads",
        style_function=lambda x: {
            "color": "gray",
            "weight": 1,
            "opacity": 0.4
        },
    ).add_to(m)

    tour_group = folium.FeatureGroup(name="Giant Tour", show=True)

    for idx, (u, v, k) in enumerate(tour):
        data = E[u][v][k]

        if "geometry" in data and data["geometry"] is not None:
            folium.GeoJson(
                data["geometry"],
                style_function=lambda x: {
                    "color": "red",
                    "weight": 3,
                    "opacity": 0.9
                }
            ).add_to(tour_group)
        else:
            # fallback straight line
            p1 = (E.nodes[u]["y"], E.nodes[u]["x"])
            p2 = (E.nodes[v]["y"], E.nodes[v]["x"])
            folium.PolyLine([p1, p2], color="red", weight=3, opacity=0.9).add_to(tour_group)

    tour_group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)


METER_TO_KM = 1 / 1000
KPH_PER_MPH = 1.609344

def compute_fleet_requirements(E, routes):

    sweep_len = 0.0
    dead_len = 0.0

    for route in routes:
        for u,v,k in route:
            d = E[u][v][k]
            length_m = d.get("length", 0.0)

            if d.get("mode") == "SWEEP":
                sweep_len += length_m * METER_TO_KM
            else:
                dead_len += length_m * METER_TO_KM

    sweep_vehicles = sweep_len / (4.25 * KPH_PER_MPH * 3.7)
    dead_vehicles  = dead_len  / (8.0 * KPH_PER_MPH * 3.7)

    total_vehicles = sweep_vehicles + dead_vehicles
    total_len = sweep_len + dead_len
    sweep_pct = sweep_len * 100 / total_len
    dead_pct = dead_len * 100 / total_len

    return {
        "total_len": round(total_len, 2),
        "sweep_len": round(sweep_len, 2),
        "dead_len": round(dead_len, 2),
        "sweep_pct": round(sweep_pct, 2),
        "dead_pct": round(dead_pct, 2),
        "total_veh": round(total_vehicles, 2),
        "sweep_veh": round(sweep_vehicles, 2),
        "dead_veh": round(dead_vehicles, 2)
    }

def compute_stats(E, routes):
    total_sweep = 0
    total_dead = 0
    route_rows = []

    for i, r in enumerate(routes, start=1):
        s = route_stats(E, r)
        route_rows.append({
            "route": i,
            "total_time": s["total_time"],
            "sweep_time": s["sweep_time"],
            "deadhead_time": s["deadhead_time"],
            "deadhead_pct": s["deadhead_pct"] * 100
        })

        total_sweep += s["sweep_time"]
        total_dead += s["deadhead_time"]

    total = total_sweep + total_dead

    summary = {
        "Total sweep time": total_sweep,
        "Total deadhead time": total_dead,
        "Deadhead %": (total_dead / total * 100) if total > 0 else 0,
        "Vehicle count": len(routes),
        "Average route time": total / len(routes) if routes else 0
    }

    return summary, route_rows

def write_stats_html(summary, route_rows, title, output_path):

    def row(k,v):
        return f"<tr><td>{k}</td><td>{v:.2f}</td></tr>"

    summary_rows = "\n".join(row(k,v) for k,v in summary.items())

    route_rows_html = "\n".join(
        f"<tr><td>{r['route']}</td><td>{r['sweep_time']:.2f}</td>"
        f"<td>{r['deadhead_time']:.2f}</td><td>{r['total_time']:.2f}</td>"
        f"<td>{r['deadhead_pct']:.2f}%</td></tr>"
        for r in route_rows
    )

    html = f"""
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial; padding:20px }}
            table {{ border-collapse: collapse; width: 60%; margin-bottom:30px }}
            th, td {{ border:1px solid #aaa; padding:6px; text-align:center }}
            th {{ background:#f0f0f0 }}
        </style>
    </head>
    <body>

    <h2>{title} — Summary</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        {summary_rows}
    </table>

    <h2>{title} — Per Route</h2>
    <table>
        <tr>
            <th>Route</th>
            <th>Sweep Time</th>
            <th>Deadhead Time</th>
            <th>Total Time</th>
            <th>Deadhead %</th>
        </tr>
        {route_rows_html}
    </table>

    </body>
    </html>
    """

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path,"w+",encoding="utf-8") as f:
        f.write(html)