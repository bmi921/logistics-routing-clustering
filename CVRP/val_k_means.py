# === 新しいmain関数を以下のように変更 ===
"""Capacited Vehicles Routing Problem (CVRP)."""

import math
import random
from matplotlib import pyplot as plt
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import json
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix
from calc_lat_lon import calc_lat_lon


def print_graph(x, y):
    plt.figure(figsize=(8, 5))

    # 最初の1点（赤・大きめ）
    plt.scatter(x[0], y[0], color="red", s=100, label="Start Point")
    plt.text(x[0], y[0], "0", fontsize=10, ha="right", va="bottom", color="red")

    # 残りの点（青）
    if len(x) > 1:
        plt.scatter(x[1:], y[1:], color="blue", s=30)
        for i in range(1, len(x)):
            plt.text(
                x[i], y[i], str(i), fontsize=9, ha="right", va="bottom", color="blue"
            )

    plt.title("Total Distance vs random distance")
    plt.xlabel("random distance(km)")
    plt.ylabel("Total Distance(km)")
    plt.grid(True)
    plt.tight_layout()

    # 画像保存
    plt.savefig(f"graph/centers/cluster{cluster_id:02d}.png")
    # plt.show()
    plt.close()


# クラスターidと何秒で解くか決める
cluster_id = 3
limit_seconds = 1

cluster_radius = 10  # km

# 結果を格納する変数
centers = []
results_total_distance = []

df_center = pd.read_csv("output/centers.csv")
original_center = df_center[["x", "y"]].iloc[cluster_id - 1].values
print("original_center", original_center)

centers.append(original_center)
for i in range(1, cluster_radius + 1):
    x = random.randint(0, int((1000 * i) / math.sqrt(2)))
    y = math.sqrt((1000 * i) ** 2 - x**2)

    sign_x = random.choice([-1, 1])
    sign_y = random.choice([-1, 1])

    offset = np.array([sign_x * x, sign_y * y])
    centers.append(original_center + offset)

results_x = [float(c[0]) for c in centers]
results_y = [float(c[1]) for c in centers]
print_graph(results_x, results_y)


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


def save_geojson(geojson, filename):
    with open(filename, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"✅GeoJSON saved to {filename}")


def main(center_index):
    global distance_matrix, locations, locations_lon_lat

    center = centers[center_index]
    print(f"Running CVRP for center {center_index}, center: {center}")

    df = pd.read_csv(f"output/cluster{cluster_id:02d}.csv")
    cluster_points = df[["x", "y"]].values
    locations = np.vstack([center.reshape(1, 2), cluster_points])
    points = np.array(locations)

    cluster_points = df[["longitude", "latitude"]].values
    locations_lon_lat = np.vstack([center.reshape(1, 2), cluster_points])

    center_lat, center_lon = calc_lat_lon(
        center.reshape(1, 2)[0][0], center.reshape(1, 2)[0][1], 36.0, 139 + 50.0 / 60
    )

    locations_lon_lat[0] = [center_lon, center_lat]

    # print("aaaaaaa", locations_lon_lat[0], locations_lon_lat[1])

    distance_mat = distance_matrix(points, points).astype(int)
    num_vehicles = math.ceil((len(locations) - 1) / 50)

    def create_data_model():
        data = {}
        data["distance_matrix"] = distance_mat.tolist()
        data["demands"] = [0] + [1] * (len(distance_mat) - 1)
        data["vehicle_capacities"] = [50] * num_vehicles
        data["num_vehicles"] = num_vehicles
        data["depot"] = 0
        return data

    data = create_data_model()
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index, 0, data["vehicle_capacities"], True, "Capacity"
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
        save_geojson(
            geojson,
            filename=f"geojson/move_center/cluster{cluster_id:02d}/center{center_index:02d}.geojson",
        )
        total_distance = solution.ObjectiveValue() / 1000  # km
        return total_distance
    else:
        print(f"❌No solution found for center {center_index}.")
        return None


# 距離行列の上書き用関数名変更
def distance_matrix_func(points1, points2):
    return distance_matrix(points1, points2)


# === 実行部分 ===
if __name__ == "__main__":
    for i in range(0, cluster_radius + 1):
        total_distance = main(i)
        if total_distance is not None:
            results_total_distance.append(total_distance)

    print(f"\n📊 All total distances for cluster {cluster_id}:")
    print(results_total_distance)
    print_graph(
        [distance_km for distance_km in range(0, len(results_total_distance))],
        results_total_distance,
    )
