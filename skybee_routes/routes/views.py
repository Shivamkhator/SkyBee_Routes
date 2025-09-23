from django.shortcuts import render
from . import utils
import folium
import os
import google.generativeai as genai

# --- Configure the Gemini API ---
# IMPORTANT: Make sure your GEMINI_API_KEY is set as an environment variable
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
    # The list of airports for the dropdown now comes from the graph nodes in utils.py
    airport_list = utils.all_airports
    context = {'airport_list': airport_list}
    flight_suggestion = None 

    if request.method == 'POST':
        source = request.POST.get('source_airport')
        destination = request.POST.get('destination_airport')
        
        # Ensure both source and destination are provided before proceeding
        if source and destination:
            astar_result = utils.get_astar_path(source, destination)
            # Using A* again for speed, but you can swap in utils.get_rl_path if desired
            rl_result = utils.get_astar_path(source, destination)

            # --- Logic to handle valid vs. invalid paths ---
            # A valid path is a list of airport codes. 
            # An invalid one will be a list containing a single string like "No path found...".
            is_valid_path = astar_result['path'] and "No path" not in astar_result['path'][0]

            # Only attempt to create the map if a valid path was found.
            if is_valid_path:
                source_coords_df = utils.airports_df[utils.airports_df['IATA'] == source]
                if not source_coords_df.empty:
                    source_coords = source_coords_df[['Latitude', 'Longitude']].iloc[0]
                    m = folium.Map(location=[source_coords['Latitude'], source_coords['Longitude']], zoom_start=4)

                    # Get coordinates for the paths directly from the graph attributes
                    astar_points = [(utils.G.nodes[apt]['lat'], utils.G.nodes[apt]['lon']) for apt in astar_result['path']]
                    rl_points = [(utils.G.nodes[apt]['lat'], utils.G.nodes[apt]['lon']) for apt in rl_result['path']]

                    # Add the flight paths as lines on the map
                    folium.PolyLine(astar_points, color='blue', weight=2.5, opacity=1, tooltip="A* Path").add_to(m)
                    folium.PolyLine(rl_points, color='red', weight=2.5, opacity=0.8, tooltip="RL Path").add_to(m)
                    
                    # Add the generated map to the context for rendering
                    context['map'] = m._repr_html_()

            # Always add the results to the context, even if the path is invalid
            context['results'] = {
                'astar': astar_result,
                'rl': rl_result
            }

            # --- RAG Logic for AI Flight Suggestions ---
            # This will run even if no path is found, as direct flights might exist.
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