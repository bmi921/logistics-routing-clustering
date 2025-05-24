"""Capacited Vehicles Routing Problem (CVRP)."""

import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import json
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix

def create_data_model(locations, num_vehicles):
    """データモデルを作成"""
    points = np.array(locations)
    dist_matrix = distance_matrix(points, points).astype(int)
    
    data = {}
    data["distance_matrix"] = dist_matrix.tolist()
    data["demands"] = [0] + [1] * (len(data["distance_matrix"]) - 1)
    data["vehicle_capacities"] = [50] * num_vehicles
    data["num_vehicles"] = num_vehicles
    data["depot"] = 0
    return data

def print_solution(data, manager, routing, solution):
    """解を表示"""
    # print(f"Objective: {solution.ObjectiveValue()}")
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
    print(f"Total distance of all routes: {total_distance / 1000}km")
    print(f"Total load of all routes: {total_load}")

def create_geojson(data, manager, routing, solution, locations_lon_lat, cluster_id):
    """GeoJSONを作成"""
    features = []
    
    # デポのポイント
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
            "coordinates": locations_lon_lat[0].tolist()
        }
    })
    
    # 顧客のポイント
    for i in range(1, len(data["distance_matrix"])):
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
                "coordinates": locations_lon_lat[i].tolist()
            }
        })
    
    # ルートのライン
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
              "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
    
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = []
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if node_index < len(locations_lon_lat):
                route.append(locations_lon_lat[node_index].tolist())
            index = solution.Value(routing.NextVar(index))

        node_index = manager.IndexToNode(index)
        if node_index < len(locations_lon_lat):
            route.append(locations_lon_lat[node_index].tolist())

        features.append({
            "type": "Feature",
            "properties": {
                "stroke": colors[cluster_id - 1],  # クラスタIDに応じた色
                "stroke-width": 2,
                "stroke-opacity": 1,
                "vehicle": vehicle_id,
                "type": "route"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": route
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

def save_geojson(geojson, cluster_id):
    """GeoJSONを保存"""
    filename = f"geojson/cluster{cluster_id:02d}.geojson"
    with open(filename, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"✅GeoJSON saved to {filename}")

def main(cluster_id):
    """メイン処理"""
    print(f"\n=== 処理開始: クラスタ {cluster_id} ===")
    
    try:
        # データ読み込み
        df_center = pd.read_csv("output/centers.csv")
        df = pd.read_csv(f"output/cluster{cluster_id:02d}.csv")
        
        # 座標データ準備 (x,y座標系)
        center_xy = df_center[['x', 'y']].iloc[cluster_id - 1].values
        cluster_points_xy = df[['x', 'y']].values
        locations_xy = np.vstack([center_xy.reshape(1, 2), cluster_points_xy])
        
        # 座標データ準備 (経度緯度)
        center_lonlat = df_center[['longitude', 'latitude']].iloc[cluster_id - 1].values
        cluster_points_lonlat = df[['longitude', 'latitude']].values
        locations_lonlat = np.vstack([center_lonlat.reshape(1, 2), cluster_points_lonlat])
        
        # 車両数計算
        num_vehicles = math.ceil((len(locations_xy) - 1) / 50)
        print(f"Number of vehicles: {num_vehicles}")
        
        # データモデル作成
        data = create_data_model(locations_xy, num_vehicles)
        
        # ルーティングモデル設定
        manager = pywrapcp.RoutingIndexManager(
            len(data["distance_matrix"]), 
            data["num_vehicles"], 
            data["depot"]
        )
        routing = pywrapcp.RoutingModel(manager)
        
        # 距離コールバック
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data["distance_matrix"][from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # 需要コールバック
        def demand_callback(from_index):
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
        
        # 解法パラメータ設定
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.FromSeconds(1)
        
        # 問題解決
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            print_solution(data, manager, routing, solution)
            geojson = create_geojson(data, manager, routing, solution, locations_lonlat, cluster_id)
            save_geojson(geojson, cluster_id)
        else:
            print("❌No solution found.")
            
    except Exception as e:
        print(f"❌エラー発生: {str(e)}")
    finally:
        print(f"=== 処理完了: クラスタ {cluster_id} ===\n")

if __name__ == "__main__":
    for cluster_id in range(1, 11):  # クラスタ1～10を処理
        main(cluster_id)