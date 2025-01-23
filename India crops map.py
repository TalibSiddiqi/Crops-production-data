import geopandas as gpd
import folium
from folium import Marker
from folium.plugins import FeatureGroupSubGroup
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from time import sleep
from google.colab import files  # For file upload in Colab

# File upload prompt
uploaded = files.upload()  # Allows user to upload the CSV file

# Assuming the uploaded file is named "crop_data.csv"
for filename in uploaded.keys():
    print(f"Uploaded file: {filename}")

# Load the uploaded crop dataset
crop_data = pd.read_csv(filename)

# Check the first few rows of the dataset
print("Preview of uploaded data:")
print(crop_data.head())

# Ensure the data includes required columns
required_columns = ['Crop', 'Crop_Year', 'Season', 'State', 'Area', 
                    'Production', 'Annual_Rainfall', 'Fertilizer', 
                    'Pesticide', 'Yield']
if not all(column in crop_data.columns for column in required_columns):
    raise ValueError("The uploaded CSV file must contain the following columns: "
                     f"{', '.join(required_columns)}")

# Geocode states using geopy with increased timeout and rate limiting
geolocator = Nominatim(user_agent="crop_geocoder", timeout=10)

# Cached state locations to avoid repeated geocoding
state_locations = {
    'Karnataka': [15.3173, 75.7139],
    'Kerala': [10.8505, 76.2711],
    'Punjab': [31.1471, 75.3412],
    # Add more pre-filled states if necessary
}

for state in crop_data['State'].unique():
    if state not in state_locations:
        try:
            print(f"Fetching coordinates for {state}...")
            location = geolocator.geocode(f"{state}, India")
            if location:
                state_locations[state] = [location.latitude, location.longitude]
                sleep(1)  # Rate limit to avoid overwhelming the server
            else:
                print(f"Warning: Could not find coordinates for {state}")
        except GeocoderUnavailable as e:
            print(f"Error fetching coordinates for {state}: {e}")

# Create a folium map
map_india = folium.Map(location=[22.0, 78.0], zoom_start=5)

# Add filterable layers for crops
crop_layers = {}
for crop in crop_data['Crop'].unique():
    layer = FeatureGroupSubGroup(map_india, crop)
    crop_layers[crop] = layer
    map_india.add_child(layer)

# Add markers with crop and season filtering
for _, row in crop_data.iterrows():
    state = row['State']
    crop = row['Crop']
    if state in state_locations:
        latitude, longitude = state_locations[state]
        Marker(
            location=[latitude, longitude],
            popup=(f"Crop: {row['Crop']}<br>"
                   f"Year: {row['Crop_Year']}<br>"
                   f"Season: {row['Season']}<br>"
                   f"Area: {row['Area']} hectares<br>"
                   f"Production: {row['Production']} metric tons<br>"
                   f"Rainfall: {row['Annual_Rainfall']} mm<br>"
                   f"Fertilizer Used: {row['Fertilizer']} kg/ha<br>"
                   f"Pesticide Used: {row['Pesticide']} L/ha<br>"
                   f"Yield: {row['Yield']} metric tons/ha"),
            tooltip=row['Season'],
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(crop_layers[crop])

# Add a legend
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 250px; height: auto; 
            background-color: white; z-index:9999; font-size:14px;
            border:2px solid grey; padding: 10px;">
<b>Legend:</b><br>
<ul>
  <li><span style="color: green;">Green Markers</span>: Crop Data</li>
  <li>Use layers to filter crops</li>
</ul>
</div>
'''
map_india.get_root().html.add_child(folium.Element(legend_html))

# Save and display the map
map_india.save('india_crops_map.html')
print("Map has been saved as 'india_crops_map.html'")

# Load the dataset from the GitHub repository
crop_data = pd.read_csv("crop_data.csv")

