import streamlit as st
import pandas as pd
import json
import numpy as np
import requests

# Haversine function to calculate distance in miles
def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in miles
    R = 3958.8
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Difference in coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Haversine formula
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = R * c
    return distance

# Function to filter the second dataset
def filter_by_radius(df, center_lat, center_lon, radius):
    distances = df.apply(lambda row: haversine(center_lat, center_lon, row['lat'], row['lon']), axis=1)
    return df[distances <= radius]
    
# Title of the app
st.title('Ship Analysis')

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file with AIS Data", type="csv")

# Check if a file has been uploaded
if uploaded_file is not None:
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(uploaded_file)

    # Define the endpoint URL and authentication headers
    endpoint_url = "https://dbc-8db1117a-9cc7.cloud.databricks.com/serving-endpoints/ais/invocations"
    headers = {
                "Authorization": "Bearer dapi8fe99adebf16e4147a7dfe041f223a9f",  # Replace with your Databricks token
                "Content-Type": "application/json"
    }
    
    # Prepare input data
    # Convert DataFrame to JSON
    data_json = """{"dataframe_split":""" + df.to_json(orient='split') + """}"""
            
    # Send the request
    response = requests.post(endpoint_url, headers=headers, data=data_json)
    ais_df = pd.json_normalize(json.loads(response.text)['predictions'])
    ais_anomalies_df = ais_df[ais_df['preds_str'] == 'Anomaly']

    # Display the DataFrame
    st.write("AIS Anomalies:")
    st.dataframe(ais_anomalies_df)

   # Let the user select a specific row by displaying the DataFrame's index
    row_index = st.selectbox("Select a row:", df.index)

    # Display the selected row
    st.write("You selected row index:", row_index)
    st.write(df.loc[row_index])
    selected_row = df.loc[row_index]
    
    # Convert the selected row to a dictionary
    selected_row_dict = selected_row.to_dict()

    # Input for the radius
    radius = st.number_input("Enter the radius (in miles):", min_value=0.1, value=5.0, step=0.1)

    signals_data = pd.read_csv('sample_signals_data.csv')

    # Filter the second dataset based on the selected row's latitude and longitude and the specified radius
    if "latitude" in selected_row_dict and "longitude" in selected_row_dict:
        center_lat = selected_row_dict["latitude"]
        center_lon = selected_row_dict["longitude"]

        filtered_signals_data = filter_by_radius(signals_data, center_lat, center_lon, radius)

        # Display the filtered second dataset
        st.write("Filtered signals data within the specified radius:")
        st.dataframe(filtered_signals_data)
    else:
        st.write("The selected row does not contain 'latitude' and 'longitude' columns.")
