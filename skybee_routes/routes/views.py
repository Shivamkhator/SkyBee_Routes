from django.shortcuts import render
from . import utils
import folium
import os
import time
from datetime import date
import google.generativeai as genai

try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not found.")
    genai.configure(api_key=api_key)
    llm_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    llm_model = None


def find_route_view(request):
    airport_list = utils.all_airports
    context = {'airport_list': airport_list}
    flight_suggestion = None 

    if request.method == 'POST':
        source = request.POST.get('source_airport')
        destination = request.POST.get('destination_airport')
        
        if source and destination:
            start_time_astar = time.perf_counter()
            astar_result = utils.get_astar_path(source, destination)
            end_time_astar = time.perf_counter()
            astar_time = (end_time_astar - start_time_astar)*1000  # in milliseconds

            start_time_dijkstra = time.perf_counter()
            dijkstra_result = utils.get_dijkstra_path(source, destination)
            end_time_dijkstra = time.perf_counter()
            dijkstra_time = (end_time_dijkstra - start_time_dijkstra)*1000  # in milliseconds
            
            time_difference_percent = 0
            if dijkstra_time > 0:
                time_difference_percent = ((dijkstra_time - astar_time) / dijkstra_time) * 100
                
            context['time_difference_percent'] = time_difference_percent

            is_valid_path = astar_result['path'] and "No path" not in astar_result['path'][0]

            if is_valid_path:
                source_coords_df = utils.airports_df[utils.airports_df['IATA'] == source]
                if not source_coords_df.empty:
                    source_coords = source_coords_df[['Latitude', 'Longitude']].iloc[0]
                    m = folium.Map(location=[source_coords['Latitude'], source_coords['Longitude']], zoom_start=4)

                    # Get coordinates for the paths directly from the graph attributes
                    astar_points = [(utils.G.nodes[apt]['lat'], utils.G.nodes[apt]['lon']) for apt in astar_result['path']]

                    # Add the flight paths as lines on the map
                    folium.PolyLine(astar_points, color='blue', weight=2.5, opacity=1, tooltip="A* Path").add_to(m)

                    # Add the generated map to the context for rendering
                    context['map'] = m._repr_html_()

            # Always add the results to the context, even if the path is invalid
            context['results'] = {
                'astar': astar_result,
                'dijkstra': dijkstra_result
            }
            flight_deals = utils.get_flight_deals(source, destination)

            if flight_deals and llm_model:
                prompt = f"""
                You are a professional travel data analyst for the SkyBee Routes application.
                Your tone must be formal, clear, and informative. Do not use conversational language or slang.

                Based on the following flight data for a direct flight from {source} to {destination}, provide a concise summary of the available options.
                List the prices in a clear, bulleted format.

                Flight Data:
                {flight_deals}
                """
                try:
                    response = llm_model.generate_content(prompt)
                    flight_suggestion = response.text
                except Exception as e:
                    print(f"Error generating content from LLM: {e}")
                    flight_suggestion = "Sorry, AI-powered suggestions are currently unavailable."

            context['flight_suggestion'] = flight_suggestion

    return render(request, 'routes/index.html', context)
