# Earthquake Notifier

A Firebase Cloud Function that monitors earthquakes within 300km of Dhaka and sends notifications via Pushbullet.

## Features

- Monitors earthquakes (magnitude ≥ 2.5) within 300km of Dhaka
- Sends phone notifications via Pushbullet
- Updates every 10 minutes
- Hosted on Firebase for 24/7 operation
- Simple status webpage

## Deployment Instructions

1. Install Firebase CLI (if not already installed):
   ```
   npm install -g firebase-tools
   ```

2. Login to Firebase:
   ```
   firebase login
   ```

3. Initialize Firebase project:
   ```
   firebase init
   ```
   Select:
   - Functions (Python)
   - Hosting

4. Set up Pushbullet:
   - Get your Pushbullet API key from https://www.pushbullet.com/#settings/account
   - Set it as a Firebase environment variable:
   ```
   firebase functions:config:set pushbullet.api_key="YOUR_API_KEY"
   ```

5. Deploy to Firebase:
   ```
   firebase deploy
   ```

## How it Works

The application runs as a Firebase Cloud Function that:
- Checks the USGS Earthquake API every 10 minutes
- Filters earthquakes within 300km of Dhaka
- Sends notifications via Pushbullet for any new earthquakes
- Hosts a simple status page showing the monitoring parameters

## Configuration

- Location: Dhaka, Bangladesh (23.8103°N, 90.4125°E)
- Search Radius: 300 km
- Minimum Magnitude: 2.5
- Check Frequency: Every 10 minutes
