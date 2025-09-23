import pandas as pd
import numpy as np
import networkx as nx
import warnings
import os
from datetime import date
from amadeus import Client, ResponseError

warnings.filterwarnings('ignore')

# --- 1. LOAD AND PROCESS DATA ---
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

    all_airports = sorted(list(G.nodes))
    print("Data loading complete.")
    DATA_LOADED_SUCCESSFULLY = True
except Exception as e:
    print(f"An error occurred during data loading: {e}")

# --- 2. AMADEUS API FUNCTION ---
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

# --- 3. A* ALGORITHM ---
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