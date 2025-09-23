import pandas as pd
import numpy as np
import networkx as nx
import warnings
import os
from datetime import date
from amadeus import Client, ResponseError

warnings.filterwarnings('ignore')

print("Loading and preparing data...")
DATA_LOADED_SUCCESSFULLY = False
all_airports = []
G = nx.Graph()
coords = {}
airports_df = pd.DataFrame() 

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    airports_path = os.path.join(base_dir, 'data', 'Airports.csv')
    routes_path = os.path.join(base_dir, 'data', 'Routes.csv')

    airports_df = pd.read_csv(airports_path)
    airports_df.rename(columns={'ID': 'IATA'}, inplace=True)
    routes_df = pd.read_csv(routes_path)
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(np.radians, [lat1, lon1, lat2, lon2])
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c

    coords = airports_df.set_index('IATA')[['Latitude', 'Longitude']].to_dict('index')

    for i, row in airports_df.iterrows():
        if row['IATA'] in coords:
            G.add_node(row['IATA'], lat=row['Latitude'], lon=row['Longitude'])

    for i, row in routes_df.iterrows():
        source, dest = row['Departure'], row['Destination']
        if source in G.nodes and dest in G.nodes:
            lat1, lon1 = coords[source]['Latitude'], coords[source]['Longitude']
            lat2, lon2 = coords[dest]['Latitude'], coords[dest]['Longitude']
            distance = haversine(lat1, lon1, lat2, lon2)
            G.add_edge(source, dest, Distance_km=distance)

    all_airports = sorted([node for node in G.nodes if len(node) == 3])
    print("Data loading complete.")
    DATA_LOADED_SUCCESSFULLY = True
except Exception as e:
    print(f"An error occurred during data loading: {e}")

def get_flight_deals(source_iata, destination_iata):
    """Fetches flight deals from the Amadeus API."""
    try:
        amadeus = Client(
            client_id=os.environ.get("AMADEUS_API_KEY"),
            client_secret=os.environ.get("AMADEUS_API_SECRET"),
        )
        
        # Search for flights using the system's current date
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=source_iata,
            destinationLocationCode=destination_iata,
            departureDate=date.today().strftime("%Y-%m-%d"), # <-- THIS LINE IS ADDED BACK
            adults=1,
            max=3 
        )
        
        deals = []
        for offer in response.data:
            price = f"{offer['price']['total']} {offer['price']['currency']}"
            deals.append({"price": price})
        return deals

    except ResponseError as error:
        print(f"Error fetching flight data from Amadeus: {error}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred with Amadeus API: {e}")
        return None

def get_astar_path(source, destination):
    """Calculates the shortest path using the A* algorithm."""
    if not DATA_LOADED_SUCCESSFULLY:
        return {'path': ['Data not loaded'], 'distance': 0}
    
    def astar_heuristic(u, v):
        lat1, lon1 = G.nodes[u]['lat'], G.nodes[u]['lon']
        lat2, lon2 = G.nodes[v]['lat'], G.nodes[v]['lon']
        return haversine(lat1, lon1, lat2, lon2)
    
    try:
        path = nx.astar_path(G, source, destination, weight='Distance_km', heuristic=astar_heuristic)
        distance = nx.astar_path_length(G, source, destination, weight='Distance_km', heuristic=astar_heuristic)
        return {'path': path, 'distance': distance}
    except (nx.NetworkXNoPath, KeyError):
        return {'path': [f"No path found from {source} to {destination}"], 'distance': 0}
    
def get_rl_path(source, destination):
    if not DATA_LOADED_SUCCESSFULLY:
        return {'path': ['Data not loaded'], 'distance': 0}
    
    routes_dict_rl = {u: {v: G.edges[u,v]['Distance_km'] for v in G.neighbors(u)} for u in G.nodes}
    actions_rl = {node: list(neighbors.keys()) for node, neighbors in routes_dict_rl.items()}

    alpha, gamma, epsilon, episodes = 0.4, 0.9, 1.0, 1000
    Q = {state: {action: 0 for action in actions_rl.get(state, [])} for state in G.nodes}

    def get_reward(current, next_state, dest):
        distance = routes_dict_rl.get(current, {}).get(next_state, 0)
        return 1000 if next_state == dest else -distance

    def find_path_with_distance_rl(start, end):
        state = start
        path = [state]
        total_distance = 0
        max_steps = 100 
        steps = 0
        while state != end and steps < max_steps:
            if not Q.get(state) or not actions_rl.get(state):
                return ["Dead end at " + str(state)], 0
            next_state = max(Q[state], key=Q[state].get, default=None)
            if next_state is None:
                return ["Could not find a path"], 0
            distance = routes_dict_rl.get(state, {}).get(next_state, 0)
            total_distance += distance
            path.append(next_state)
            state = next_state
            steps += 1
        if path[-1] != end:
            return ["Path incomplete"], 0
        return path, total_distance

    # Training loop: THIS IS VERY SLOW for a web request.
    for episode in range(episodes):
        state = random.choice(list(G.nodes))
        while state != destination:
            if not actions_rl.get(state): break
            if random.random() < epsilon:
                next_state = random.choice(actions_rl[state])
            else:
                if not Q.get(state): break
                next_state = max(Q[state], key=Q[state].get, default=None)
                if next_state is None: break
            
            reward = get_reward(state, next_state, destination)
            old_value = Q[state].get(next_state, 0)
            max_future = max(Q.get(next_state, {}).values()) if Q.get(next_state) else 0
            Q[state][next_state] = old_value + alpha * (reward + gamma * max_future - old_value)
            state = next_state
        
        min_epsilon, max_epsilon, decay_rate = 0.01, 1.0, 0.005
        epsilon = min_epsilon + (max_epsilon - min_epsilon) * np.exp(-decay_rate * episode)
    
    final_path, final_distance = find_path_with_distance_rl(source, destination)
    return {'path': final_path, 'distance': final_distance}
    