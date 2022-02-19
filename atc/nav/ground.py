from itertools import groupby

import networkx as nx

from ..db import get_parking_coords, get_runways, get_taxiways


def get_ground_network(icao: str):
    twys = get_taxiways(icao)
    G = nx.Graph()

    for twy in twys:
        G.add_edge(
            (twy["start_laty"], twy["start_lonx"]),
            (twy["end_laty"], twy["end_lonx"]),
            name=twy["name"],
        )

    return G


def find_path_coords(network: nx.Graph, start, end):
    start = min(
        network.nodes, key=lambda n: abs(start[0] - n[0]) + abs(start[1] - n[1])
    )
    end = min(network.nodes, key=lambda n: abs(end[0] - n[0]) + abs(end[1] - n[1]))
    path = nx.shortest_path(network, start, end)
    pg = nx.path_graph(path)
    twys = [network.get_edge_data(*edge)["name"] for edge in pg.edges]
    return [i[0] for i in groupby(twys)]


def find_path_parking(network: nx.Graph, start, icao: str, parking: str):
    coords = get_parking_coords(icao, parking)
    return find_path_coords(network, start, tuple(coords))


def find_path_runway(network: nx.Graph, start, icao: str, runway: str):
    rwys = get_runways(icao)
    try:
        rwy = next(rwy for rwy in rwys if rwy["name"] == runway)
    except StopIteration:
        return None
    return find_path_coords(network, start, (rwy["laty"], rwy["lonx"]))


if __name__ == "__main__":
    import plotly.graph_objects as go

    network = get_ground_network("KSYR")
    path = find_path_parking(network, (43.10846, -76.11813), "KSYR", "South Terminal A")
    path = find_path_runway(network, (43.10846, -76.11813), "KSYR", "28")
    print(path)

    twys = get_taxiways("KSYR")
    fig = go.Figure(go.Scattergeo())

    for name, segs in groupby(twys, lambda d: d["name"]):
        segs = list(segs)
        for seg in segs:
            fig.add_scattergeo(
                lon=[seg["start_lonx"], seg["end_lonx"]],
                lat=[seg["start_laty"], seg["end_laty"]],
                mode="lines",
                name=name,
            )
    fig.update_layout(mapbox_style="satellite")
    fig.update_geos(fitbounds="locations")
    fig.show()
