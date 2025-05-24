"""Capacited Vehicles Routing Problem (CVRP)."""

import math
from matplotlib import pyplot as plt
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import json
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix

# クラスターid
cluster_id = 7
results_limit_seconds = []
results_total_distance = []


df_center = pd.read_csv("output/centers.csv")
center = df_center[["x", "y"]].iloc[cluster_id - 1].values

df = pd.read_csv(f"output/cluster{cluster_id:02d}.csv")
cluster_points = df[["x", "y"]].values
locations = np.vstack([center.reshape(1, 2), cluster_points])
points = np.array(locations)

center = df_center[["longitude", "latitude"]].iloc[cluster_id - 1].values
cluster_points = df[["longitude", "latitude"]].values
locations_lon_lat = np.vstack([center.reshape(1, 2), cluster_points])

distance_matrix = distance_matrix(points, points).astype(int)
num_vehicles = math.ceil(len(locations - 1) / 50)


def create_data_model():
    data = {}
    data["distance_matrix"] = distance_matrix.tolist()
    data["demands"] = [0] + [1] * (len(data["distance_matrix"]) - 1)
    data["vehicle_capacities"] = [50] * num_vehicles
    data["num_vehicles"] = num_vehicles
    data["depot"] = 0
    return data


def print_solution(data, manager, routing, solution):
    print(f"Objective: {solution.ObjectiveValue()}")
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = f"Route for vehicle {vehicle_id}:\n"
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data["demands"][node_index]
            plan_output += f" {node_index} Load({route_load}) -> "
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
        plan_output += f" {manager.IndexToNode(index)} Load({route_load})\n"
        plan_output += f"Distance of the route: {route_distance}m\n"
        plan_output += f"Load of the route: {route_load}\n"
        # print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print(f"Total distance of all routes: {total_distance /1000}km")
    print(f"Total load of all routes: {total_load}")
    results_total_distance.append(total_distance / 1000)


def create_geojson(data, manager, routing, solution):
    features = []
    features.append(
        {
            "type": "Feature",
            "properties": {
                "marker-color": "#FF0000",
                "marker-size": "large",
                "marker-symbol": "warehouse",
                "name": f"Depot {cluster_id}",
            },
            "geometry": {"type": "Point", "coordinates": locations_lon_lat[0].tolist()},
        }
    )

    for i in range(1, len(data["distance_matrix"])):
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "marker-color": "#00FF00",
                    "marker-size": "small",
                    "marker-symbol": "circle",
                    "name": f"Customer {i}",
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": locations_lon_lat[i].tolist(),
                },
            }
        )

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = []

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if node_index < len(locations):
                route.append(locations_lon_lat[node_index].tolist())
            index = solution.Value(routing.NextVar(index))

        node_index = manager.IndexToNode(index)
        if node_index < len(locations):
            route.append(locations_lon_lat[node_index].tolist())

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "stroke": colors[cluster_id - 1],
                    "stroke-width": 2,
                    "stroke-opacity": 1,
                    "vehicle": vehicle_id,
                    "type": "route",
                },
                "geometry": {"type": "LineString", "coordinates": route},
            }
        )

    geojson = {"type": "FeatureCollection", "features": features}

    return geojson


def save_geojson(geojson, filename=f"geojson/cluster{cluster_id:02d}.geojson"):
    with open(filename, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"✅GeoJSON saved to {filename}")


def main(limit_seconds):
    """Solve the CVRP problem and save GeoJSON."""
    data = create_data_model()

    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        """Returns the demand of the node."""
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        data["vehicle_capacities"],
        True,
        "Capacity",
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(limit_seconds)

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        print_solution(data, manager, routing, solution)
        geojson = create_geojson(data, manager, routing, solution)
        save_geojson(geojson)
    else:
        print("❌No solution found.")


def print_graph():
    plt.figure(figsize=(8, 5))
    plt.plot(results_limit_seconds, results_total_distance, marker="o")
    plt.title("Total Distance vs Limit Seconds")
    plt.xlabel("Limit Seconds(s)")
    plt.ylabel("Total Distance(km)")
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(f"graph/limitSeconds/cluster{cluster_id:02d}.png")
    plt.show()
    plt.close()


if __name__ == "__main__":
    for t in range(1, 11):
        results_limit_seconds.append(t)
        main(limit_seconds=t)

    print(results_limit_seconds, results_total_distance)
    print_graph()
