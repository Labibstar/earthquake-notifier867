from flask import Flask, render_template
import requests
from pushbullet import Pushbullet
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os
from dotenv import load_dotenv
from math import radians, sin, cos, sqrt, atan2

load_dotenv()

app = Flask(__name__)

# Initialize Pushbullet with your API key
pb = None
if os.getenv('PUSHBULLET_API_KEY'):
    pb = Pushbullet(os.getenv('PUSHBULLET_API_KEY'))

# Store the last notification time and magnitude to avoid duplicate notifications
last_notification = {
    'time': None,
    'id': None
}

# Constants for Dhaka's coordinates and search radius
DHAKA_LAT = 23.8103
DHAKA_LON = 90.4125
SEARCH_RADIUS_KM = 300

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

def check_earthquakes():
    """Check for significant earthquakes and send notifications"""
    # USGS API endpoint for all earthquakes in the past day within a bounding box around Dhaka
    # Adding a buffer to the bounding box to ensure we catch all earthquakes within 300km
    buffer = SEARCH_RADIUS_KM / 111  # rough conversion to degrees (1 degree ≈ 111 km)
    min_lat = DHAKA_LAT - buffer
    max_lat = DHAKA_LAT + buffer
    min_lon = DHAKA_LON - buffer
    max_lon = DHAKA_LON + buffer
    
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={datetime.now() - timedelta(days=1)}&endtime={datetime.now()}&minlatitude={min_lat}&maxlatitude={max_lat}&minlongitude={min_lon}&maxlongitude={max_lon}&minmagnitude=2.5"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        for feature in data['features']:
            quake = feature['properties']
            coordinates = feature['geometry']['coordinates']
            quake_id = feature['id']
            
            # Calculate distance from Dhaka
            quake_lon, quake_lat = coordinates[0], coordinates[1]
            distance = calculate_distance(DHAKA_LAT, DHAKA_LON, quake_lat, quake_lon)
            
            # Skip if earthquake is outside our radius or we've already notified about it
            if distance > SEARCH_RADIUS_KM or last_notification['id'] == quake_id:
                continue
                
            magnitude = quake['mag']
            place = quake['place']
            time = datetime.fromtimestamp(quake['time'] / 1000.0)
            
            # Create notification message
            message = (f"Magnitude {magnitude} earthquake detected {place} "
                      f"({distance:.1f} km from Dhaka) at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Send notification if Pushbullet is configured
            if pb:
                pb.push_note("Earthquake Alert near Dhaka!", message)
                last_notification['time'] = datetime.now()
                last_notification['id'] = quake_id
                print(f"Notification sent: {message}")
            else:
                print("Pushbullet not configured. Please set PUSHBULLET_API_KEY in .env file")
                
    except Exception as e:
        print(f"Error checking earthquakes: {str(e)}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_earthquakes, trigger="interval", minutes=5)
scheduler.start()

@app.route('/')
def home():
    return render_template('index.html', last_check=last_notification['time'])

if __name__ == '__main__':
    app.run(debug=True)
