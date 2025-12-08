from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash, session
import requests
from datetime import datetime, timedelta
import os
from dateutil import parser
import pytz
from .oauth import oauth
from .decorators import token_required
import uuid
from .models import db, User, Installation

main = Blueprint('main', __name__)

@main.route('/install')
def install():
    state = str(uuid.uuid4())
    redirect_uri = url_for('main.callback', _external=True)

    # Create a placeholder installation object to store the state
    installation = Installation(install_state=state)
    db.session.add(installation)
    db.session.commit()

    return oauth.trmnl.authorize_redirect(redirect_uri, state=state)

@main.route('/callback')
def callback():
    state = request.args.get('state')
    installation = Installation.query.filter_by(install_state=state).first_or_404()

    token = oauth.trmnl.authorize_access_token()
    resp = oauth.trmnl.get('account')
    resp.raise_for_status()
    profile = resp.json()

    user = User.query.filter_by(trmnl_id=profile['id']).first()
    if user is None:
        user = User(trmnl_id=profile['id'])
        db.session.add(user)

    installation.user = user
    installation.access_token = token['access_token']
    db.session.commit()

    return "Installation successful! Please wait for the webhook to finalize the installation."

@main.route('/webhook/installation_success', methods=['POST'])
def webhook_installation_success():
    data = request.json
    state = data.get('state')
    installation = Installation.query.filter_by(install_state=state).first_or_404()

    installation.trmnl_installation_id = data.get('id')
    installation.install_state = None # Clear the state
    db.session.commit()

    return jsonify({"status": "success"}), 200

@main.route('/webhook/uninstall', methods=['POST'])
def webhook_uninstall():
    data = request.json
    installation_id = data.get('id')
    if installation_id:
        installation = Installation.query.filter_by(trmnl_installation_id=installation_id).first()
        if installation:
            db.session.delete(installation)
            db.session.commit()
            return jsonify({"status": "success"}), 200
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField

class SettingsForm(FlaskForm):
    bus_stop = StringField('Bus Stop ATCO Code')
    bus_direction = StringField('Bus Direction (Optional)')
    train_station = StringField('Train Station CRS Code')
    train_destination = StringField('Train Destination (Optional)')
    min_train_time = IntegerField('Minimum Train Time (mins)')
    app_id = StringField('App ID')
    app_key = StringField('App Key')
    submit = SubmitField('Save Settings')

@main.route('/manage', methods=['GET', 'POST'])
@token_required
def manage(installation):
    form = SettingsForm(obj=installation)
    if form.validate_on_submit():
        form.populate_obj(installation)
        db.session.commit()
        flash('Settings saved successfully!')
        return redirect(url_for('main.manage'))
    return render_template('manage.html', installation=installation, form=form)

# Mock data for testing without keys
MOCK_BUS_DATA = {
    "departures": {
        "19": [
            {"line_name": "19", "direction": "East Garforth", "aimed_departure_time": "12:00", "operator_name": "First Leeds"},
            {"line_name": "19", "direction": "East Garforth", "aimed_departure_time": "12:30", "operator_name": "First Leeds"}
        ],
        "40": [
            {"line_name": "40", "direction": "Seacroft", "aimed_departure_time": "12:15", "operator_name": "First Leeds"},
            {"line_name": "40", "direction": "Seacroft", "aimed_departure_time": "12:45", "operator_name": "First Leeds"}
        ],
        "163": [
            {"line_name": "163", "direction": "Castleford", "aimed_departure_time": "12:10", "operator_name": "Arriva"} # Should be filtered out
        ]
    }
}

MOCK_TRAIN_DATA = {
    "departures": {
        "all": [
            {"destination_name": "London Liverpool Street", "aimed_departure_time": "12:00", "status": "ON TIME", "operator_name": "Greater Anglia"},
            {"destination_name": "Cambridge", "aimed_departure_time": "12:45", "status": "ON TIME", "operator_name": "Greater Anglia"}, # > 30 mins
            {"destination_name": "Norwich", "aimed_departure_time": "12:15", "status": "LATE", "operator_name": "Greater Anglia"},
             {"destination_name": "Stansted Airport", "aimed_departure_time": "12:05", "status": "ON TIME", "operator_name": "CrossCountry"} # Keep if user wants
        ]
    }
}

def fetch_bus_data(app_id, app_key, stop_id):
    if not app_id or not app_key:
        return MOCK_BUS_DATA
    
    url = f"https://transportapi.com/v3/uk/bus/stop_timetables/{stop_id}.json"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "group": "no", # Don't group by route, just get all? Actually 'no' might not be valid. 
        # "nextbuses": "yes" ?
        # Examples used default.
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching bus data: {e}")
        return None

def fetch_train_data(app_id, app_key, station_code):
    if not app_id or not app_key:
        return MOCK_TRAIN_DATA

    url = f"https://transportapi.com/v3/uk/train/station/{station_code}/live.json"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "darwin": "true",
        "train_status": "passenger"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching train data: {e}")
        return None

@main.route('/api/data', methods=['GET'])
@token_required
def get_data(installation):
    app_id = installation.app_id
    app_key = installation.app_key
    bus_stop_id = installation.bus_stop
    bus_direction = (installation.bus_direction or '').lower()
    train_station_code = installation.train_station
    train_destination = (installation.train_destination or '').lower()
    min_train_time = installation.min_train_time if installation.min_train_time is not None else 30
    
    # Ensure UK time for accurate comparison
    uk_tz = pytz.timezone('Europe/London')
    now = datetime.now(uk_tz)
    
    # If testing with mock data (no app_id), mock 'now' as 11:45 UK time
    if not app_id:
        # Create a naive datetime then localize it
        naive_mock_time = datetime.strptime("11:45", "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        now = uk_tz.localize(naive_mock_time)

    # Process Bus Data
    buses = []
    # If testing without app_id (mock mode), assume we want data even if bus_stop_id is missing or arbitrary
    if bus_stop_id or not app_id:
        bus_data = fetch_bus_data(app_id, app_key, bus_stop_id)
        if bus_data and 'departures' in bus_data:
            all_departures = []
            # departures is a dict keyed by line name
            for line, deps in bus_data['departures'].items():
                for dep in deps:
                    # Filter for First Bus
                    # Operator name might vary, check for "First"
                    op_name = dep.get('operator_name', '')
                    if 'First' in op_name:
                         # Filter by direction if specified
                         if bus_direction and bus_direction not in dep.get('direction', '').lower():
                             continue
                         all_departures.append(dep)
            
            # Sort by time
            # Time format is HH:MM
            def parse_time(t_str):
                try:
                    return datetime.strptime(t_str, "%H:%M").time()
                except:
                    return datetime.max.time()

            all_departures.sort(key=lambda x: parse_time(x['aimed_departure_time']))
            
            # Take top 3
            for dep in all_departures[:3]:
                buses.append({
                    "line": dep['line_name'],
                    "destination": dep['direction'],
                    "time": dep['aimed_departure_time']
                })

    # Process Train Data
    trains = []
    # If testing without app_id (mock mode), assume we want data
    if train_station_code or not app_id:
        train_data = fetch_train_data(app_id, app_key, train_station_code)
        if train_data and 'departures' in train_data:
            # departures might have keys 'all', or 'from', etc.
            # TransportAPI usually returns { "departures": { "all": [...] } }
            all_trains = train_data['departures'].get('all', [])
            
            filtered_trains = []
            for train in all_trains:
                # Filter operator: Greater Anglia/Trainline
                # "Trainline" is not an operator. Greater Anglia is.
                # But user said "train times from Greater Anglia/Trainline".
                # I will include all trains but maybe prioritize GA?
                # Or strict filter? "Train times from Greater Anglia".
                # Let's strict filter for now if it's easy, otherwise include all.
                # The prompt says "Bus info must be from First Bus company, and train times from Greater Anglia/Trainline."
                # This implies strict filtering.
                op_name = train.get('operator_name', '')
                # Check for Greater Anglia (might be abbreviated)
                if 'Greater Anglia' not in op_name and 'Trainline' not in op_name: # Trainline won't be there
                     # Wait, if user buys from Trainline, they see all trains.
                     # Maybe "Greater Anglia" is the operator they care about.
                     # I'll filter for "Greater Anglia".
                     # But to be safe, I'll comment this out or make it optional.
                     # The prompt is specific. I'll filter.
                     if 'Greater Anglia' not in op_name:
                         continue
                
                # Filter by destination if specified
                if train_destination and train_destination not in train.get('destination_name', '').lower():
                    continue

                # Time filtering
                # "only show train times after a set amount of time (default 30 mins)"
                aimed_time_str = train.get('aimed_departure_time') or train.get('expected_departure_time')
                if aimed_time_str:
                    try:
                        # TransportAPI returns HH:MM local time. We construct a timezone-aware datetime.
                        # Parse time string
                        t_obj = datetime.strptime(aimed_time_str, "%H:%M").time()
                        
                        # Combine with today's date and localize
                        train_time = uk_tz.localize(datetime.combine(now.date(), t_obj))
                        
                        # Handle midnight crossover? 
                        # If train_time is significantly in the past (e.g. > 12 hours ago), maybe it's actually tomorrow? 
                        # But simpler: if train_time < now, check if the difference is huge or small.
                        # However, usually lists are for near future.
                        # If train time is 00:10 and now is 23:50, train_time (today 00:10) < now.
                        # We should add a day.
                        if train_time < now and (now - train_time).total_seconds() > 43200: # 12 hours
                             train_time = train_time + timedelta(days=1)
                        
                        # Calculate minutes from now
                        diff = (train_time - now).total_seconds() / 60
                        
                        if diff >= min_train_time:
                            filtered_trains.append(train)
                    except ValueError:
                        pass
            
            # Sort filtered trains by time
            def parse_train_time(t_str):
                try:
                     return datetime.strptime(t_str, "%H:%M").time()
                except:
                     return datetime.max.time()

            filtered_trains.sort(key=lambda x: parse_train_time(x.get('aimed_departure_time') or x.get('expected_departure_time') or '23:59'))

            # Take top 3
            for train in filtered_trains[:3]:
                trains.append({
                    "destination": train['destination_name'],
                    "time": train.get('aimed_departure_time'),
                    "status": train.get('status'),
                    "platform": train.get('platform')
                })

    return jsonify({
        "buses": buses,
        "trains": trains
    })

