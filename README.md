# TRMNL Transport Plugin

This plugin displays the next 3 bus times (First Bus) and 3 train times (Greater Anglia) on your TRMNL device.

## Features
- **Bus Times**: Fetches live departures for a specific bus stop, filtering for "First Bus" services.
- **Train Times**: Fetches live departures for a specific train station, filtering for "Greater Anglia".
- **Smart Filtering**: Option to only show trains departing after a certain time (e.g., 30 mins) to account for walking time.

## Setup

### 1. Prerequisites
- A [TransportAPI](https://developer.transportapi.com/) account (Free plan available).
- Get your `App ID` and `App Key`.

### 2. Backend Server
This plugin requires a backend server to fetch and process the data from TransportAPI. You can host this simple Python Flask app on any provider (e.g., Render, Fly.io, Heroku, or your own server).

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the server:
    ```bash
    python app.py
    ```
    The server will run on port 5000 (or `$PORT`).

### 3. TRMNL Configuration
1.  Go to your [TRMNL Dashboard](https://usetrmnl.com/).
2.  Create a new **Private Plugin**.
3.  **Polling URL**: Enter the URL of your deployed backend with the following parameters:
    ```
    https://your-app-url.com/api/data?app_id=YOUR_APP_ID&app_key=YOUR_APP_KEY&bus_stop=BUS_STOP_ATCO_CODE&train_station=TRAIN_STATION_CRS_CODE&min_train_time=30&bus_direction=Leeds&train_destination=Norwich
    ```
    - `bus_stop`: The ATCO Code of the bus stop (e.g., `450024834`). You can find this on TransportAPI or open data sites.
    - `bus_direction`: (Optional) Filter buses by direction/destination name (substring match).
    - `train_station`: The CRS Code of the train station (e.g., `LST` for London Liverpool Street).
    - `train_destination`: (Optional) Filter trains by destination name (substring match).
    - `min_train_time`: (Optional) Minimum minutes from now for train departures. Default is `30`.

4.  **Markup**: Copy the content of `markup.html` and paste it into the Markup section of your Private Plugin.

### Important: API Limits
The **TransportAPI Free Plan** typically allows only **30 requests per day**.
- Set your TRMNL polling interval accordingly (e.g., every 60 minutes or Manual Refresh only).
- If you poll every 15 minutes, you will hit the limit in ~7 hours.
- Consider upgrading your TransportAPI plan if you need more frequent updates.

## Customization
- **Operators**: The code currently filters for "First" (Bus) and "Greater Anglia" (Train). You can modify `app.py` to change these filters.
- **Layout**: Modify `markup.html` to change the appearance.
