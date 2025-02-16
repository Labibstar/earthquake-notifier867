import firebase_admin
from firebase_admin import credentials
from firebase_functions import https_fn
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
import requests
from pushbullet import Pushbullet
import os
import json
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Firebase Admin SDK
try:
    firebase_admin.initialize_app()
except ValueError:
    pass  # Already initialized

# Constants for Dhaka's coordinates and search radius
DHAKA_LAT = 23.8103
DHAKA_LON = 90.4125
SEARCH_RADIUS_KM = 600

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

@https_fn.on_request()
def check_earthquakes(request: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud function to check for earthquakes near Dhaka"""
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return https_fn.Response('', 204, headers)

    # Set CORS headers for the main request
    headers = {'Access-Control-Allow-Origin': '*'}
    
    # Get Pushbullet API key
    pb_api_key = os.getenv('PUSHBULLET_API_KEY')
    
    try:
        pb = Pushbullet(pb_api_key)
        
        # Get earthquake data from USGS
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query"
        params = {
            'format': 'geojson',
            'starttime': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'endtime': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'latitude': DHAKA_LAT,
            'longitude': DHAKA_LON,
            'maxradiuskm': SEARCH_RADIUS_KM
        }
        
        logging.info(f"Requesting USGS API with parameters: {params}")
        response = requests.get(url, params=params)
        logging.info(f"Received response from USGS API: {response.json()}")
        
        if response.status_code != 200:
            logging.error(f"Error calling USGS API: {response.status_code} - {response.text}")
            return https_fn.Response(json.dumps({
                'status': 'error',
                'message': 'Failed to retrieve earthquake data from USGS API'
            }), 500, headers)
        
        data = response.json()
        
        earthquakes_found = []
        
        for feature in data['features']:
            props = feature['properties']
            coords = feature['geometry']['coordinates']
            
            # Calculate actual distance
            distance = calculate_distance(DHAKA_LAT, DHAKA_LON, coords[1], coords[0])
            
            if distance <= SEARCH_RADIUS_KM:
                earthquake_info = {
                    'magnitude': props['mag'],
                    'place': props['place'],
                    'time': datetime.fromtimestamp(props['time']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                    'distance': round(distance, 2)
                }
                earthquakes_found.append(earthquake_info)
        
        # Send notifications for found earthquakes
        for quake in earthquakes_found:
            message = f"Magnitude {quake['magnitude']} earthquake detected {quake['distance']} km from Dhaka at {quake['place']} on {quake['time']}"
            pb.push_note("Earthquake Alert near Dhaka!", message)
            print(f"Notification sent: {message}")
        
        return https_fn.Response(json.dumps({
            'status': 'success',
            'message': 'Earthquake check completed successfully',
            'earthquakes_found': earthquakes_found
        }), 200, headers)
        
    except Exception as e:
        error_message = str(e)
        print(f"Error checking earthquakes: {error_message}")
        return https_fn.Response(json.dumps({
            'status': 'error',
            'message': error_message
        }), 500, headers)
