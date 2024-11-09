import streamlit as st
import requests
import folium
from folium.plugins import BeautifyIcon
from streamlit_folium import st_folium

# Set your OpenWeatherMap API Key here
OPENWEATHER_API_KEY = 'some_api_key'
OSRM_SERVER_URL = "http://router.project-osrm.org"

# Function to get air quality from OpenWeatherMap API
def get_air_quality(lat, lon):
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['list'][0]['main']['aqi']  # Return AQI value
    else:
        return float('inf')  # Return high AQI on error

# Function to get routes from OSRM
def get_osrm_routes(start_coords, end_coords):
    osrm_url = f"{OSRM_SERVER_URL}/route/v1/foot/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}"
    params = {"overview": "full", "geometries": "geojson", "alternatives": "true"}
    response = requests.get(osrm_url, params=params)
    if response.status_code == 200:
        return response.json().get('routes', [])
    return []

# Function to calculate AQI along a route by sampling points
def calculate_route_aqi(route):
    path = route['geometry']['coordinates']
    total_aqi = 0
    sample_count = 0
    for coord in path[::10]:  # Sample every 10th point to reduce API calls
        lat, lon = coord[1], coord[0]
        aqi = get_air_quality(lat, lon)
        total_aqi += aqi
        sample_count += 1
    return total_aqi / sample_count if sample_count else float('inf')

# Initialize session state to store best route and AQI data
if 'best_route' not in st.session_state:
    st.session_state.best_route = None
    st.session_state.lowest_aqi = None

# Streamlit App
st.title("Least Polluted Route Finder")
st.write("Find the least polluted walking route based on real-time air quality data.")

# Input fields for start and end coordinates with defaults
start_lat = st.number_input("Enter Start Latitude:", value=0.0, format="%f")
start_lon = st.number_input("Enter Start Longitude:", value=0.0, format="%f")
end_lat = st.number_input("Enter End Latitude:", value=0.0, format="%f")
end_lon = st.number_input("Enter End Longitude:", value=0.0, format="%f")

# Store coordinates as tuples
start_coords = (start_lat, start_lon)
end_coords = (end_lat, end_lon)

# Button to find the route
if st.button("Find Least Polluted Route"):
    # Get multiple routes and calculate AQI for each
    routes = get_osrm_routes(start_coords, end_coords)
    best_route = None
    lowest_aqi = float('inf')

    for route in routes:
        avg_aqi = calculate_route_aqi(route)
        if avg_aqi < lowest_aqi:
            lowest_aqi = avg_aqi
            best_route = route

    # Store the best route and AQI in session state
    st.session_state.best_route = best_route
    st.session_state.lowest_aqi = lowest_aqi

# Display the map only if a route has been calculated
if st.session_state.best_route:
    st.write(f"Lowest average AQI: {st.session_state.lowest_aqi}")

    # Create Folium map centered at start location
    m = folium.Map(location=start_coords, zoom_start=14)

    # Add markers for start and end points
    folium.Marker(start_coords, popup="Start", icon=BeautifyIcon(icon="play", border_color="blue")).add_to(m)
    folium.Marker(end_coords, popup="End", icon=BeautifyIcon(icon="stop", border_color="red")).add_to(m)

    # Draw the best route on the map
    folium.GeoJson(
        st.session_state.best_route['geometry'],
        style_function=lambda feature: {'color': 'green', 'weight': 4, 'opacity': 0.8}
    ).add_to(m)

    # Display the map with Streamlit Folium
    st_folium(m, width=700, height=500)
else:
    st.write("No route calculated yet. Enter coordinates and click 'Find Least Polluted Route'.")
