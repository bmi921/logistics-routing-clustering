"""Capacited Vehicles Routing Problem (CVRP)."""

import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import json
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix

cluster_id=1
df = pd.read_csv(f"../output/cluster{cluster_id:02d}.csv")
locations = df[['x', 'y']].values

# print(locations)

points = np.array(locations)
distance_matrix = distance_matrix(points, points).astype(int)
num_vehicles = math.ceil(len(locations) / 50)

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
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print(f"Total distance of all routes: {total_distance}m")
    print(f"Total load of all routes: {total_load}")

def create_geojson(data, manager, routing, solution):
    coordinates = []  
    features = []
    
    # Generate other points in a circle around the depot
    for i in range(0, len(data["distance_matrix"])):
        coord = df[['longitude','latitude']].values[i].tolist()
        coordinates.append(coord)
    
    # Add depot feature
    features.append({
        "type": "Feature",
        "properties": {
            "marker-color": "#FF0000",
            "marker-size": "large",
            "marker-symbol": "warehouse",
            "name": f"Depot {cluster_id}",
        },
        "geometry": {
            "type": "Point",
            "coordinates": coordinates[0]
        }
    })
    
    # Add customer features
    for i in range(1,len(data["distance_matrix"])):
        coord = coordinates[i]
        features.append({
            "type": "Feature",
            "properties": {
                "marker-color": "#00FF00",
                "marker-size": "small",
                "marker-symbol": "circle",
                "name": f"Customer {i}",
            },
            "geometry": {
                "type": "Point",
                "coordinates": coordinates[i]
            }
        })
    
    # Add route features
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
              "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
    
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_coords = []
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            # coord = coordinates[node_index]
            coord = df[['longitude','latitude']].values[node_index].tolist()
            route_coords.append([coord[0], coord[1]])
            previous_index = index
            index = solution.Value(routing.NextVar(index))
        
        # Add the last node
        node_index = manager.IndexToNode(index)
        coord = df[['longitude','latitude']].values[node_index].tolist()
        route_coords.append([coord[0], coord[1]])

        # Add route as LineString feature
        features.append({
            "type": "Feature",
            "properties": {
                "stroke": colors[cluster_id],
                "stroke-width": 2,
                "stroke-opacity": 1,
                "vehicle": vehicle_id,
                "type": "route"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": route_coords
            }
        })
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return geojson

def save_geojson(geojson, filename=f"../geojson/cluster{cluster_id:02d}.geojson"):
    with open(filename, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"GeoJSON saved to {filename}")

def main():
    """Solve the CVRP problem and save GeoJSON."""
    # Instantiate the data problem.
    data = create_data_model()

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Capacity constraint.
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

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(1)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution and save GeoJSON
    if solution:
        print_solution(data, manager, routing, solution)
        geojson = create_geojson(data, manager, routing, solution)
        save_geojson(geojson)
    else:
        print("No solution found!")

if __name__ == "__main__":
    main()