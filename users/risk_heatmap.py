import folium
from folium import plugins
import numpy as np
from .tasks import check_earthquake_risk, check_cyclone_risk
from .models import UserSubscription
from datetime import datetime, timedelta
import requests
import json
import logging

logger = logging.getLogger(__name__)

def get_active_alerts():
    """Get active alerts from the database"""
    try:
        # Get subscriptions with recent alerts (using updated_at instead of last_alert_time)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        active_subscriptions = UserSubscription.objects.filter(
            updated_at__gte=one_hour_ago
        ).values('latitude', 'longitude', 'primary_location_name')
        
        # Format the alerts
        alerts = []
        for sub in active_subscriptions:
            # Get the latest risk assessments for this location
            eq_risk = check_earthquake_risk(sub['latitude'], sub['longitude'])
            cyc_risk = check_cyclone_risk(sub['latitude'], sub['longitude'])
            
            # Only include if there's an active risk
            if eq_risk['risk_level'] > 0 or cyc_risk['risk_level'] > 0:
                alert_details = []
                if eq_risk['risk_level'] > 0:
                    alert_details.append(f"Earthquake Risk Level: {eq_risk['risk_level']} - {eq_risk['details']}")
                if cyc_risk['risk_level'] > 0:
                    alert_details.append(f"Cyclone Risk Level: {cyc_risk['risk_level']} - {cyc_risk['details']}")
                
                alerts.append({
                    'latitude': sub['latitude'],
                    'longitude': sub['longitude'],
                    'primary_location_name': sub['primary_location_name'],
                    'last_alert_details': ' | '.join(alert_details)
                })
        return alerts
    except Exception as e:
        logger.error(f"Error fetching active alerts: {str(e)}")
        return []

def generate_risk_heatmap():
    """
    Generate a heatmap showing earthquake and cyclone risks across regions.
    Returns the HTML content of the map.
    """
    # Create base map centered on India
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=4)
    
    # Generate grid points across the region
    lat_range = np.linspace(8, 35, 50)  # Increased from 30 to 50 points
    lon_range = np.linspace(68, 97, 50)  # Increased from 30 to 50 points
    
    # Lists to store heatmap data
    earthquake_data = []
    cyclone_data = []
    
    # Get USGS earthquake data for the last month
    usgs_url = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson'
    try:
        response = requests.get(usgs_url, timeout=15)  # Increased timeout
        if response.status_code == 200:
            usgs_data = response.json()
            
            # Add USGS earthquake markers
            earthquake_layer = folium.FeatureGroup(name='Recent Earthquakes')
            for feature in usgs_data.get('features', []):
                try:
                    coords = feature['geometry']['coordinates']
                    properties = feature['properties']
                    magnitude = properties.get('mag')
                    
                    # Only proceed if we have valid magnitude and coordinates
                    if magnitude is not None and coords and len(coords) >= 2:
                        if float(magnitude) > 2.5:  # Only show significant earthquakes
                            # Format time
                            event_time = datetime.fromtimestamp(properties.get('time', 0)/1000)
                            time_str = event_time.strftime('%Y-%m-%d %H:%M:%S')
                            
                            folium.CircleMarker(
                                location=[coords[1], coords[0]],
                                radius=float(magnitude) * 2,
                                color='red',
                                fill=True,
                                popup=f"Magnitude: {magnitude}<br>Time: {time_str}<br>Depth: {coords[2]} km",
                                tooltip=f"M{magnitude} Earthquake"
                            ).add_to(earthquake_layer)
                except (KeyError, TypeError, ValueError) as e:
                    logger.warning(f"Error processing earthquake feature: {str(e)}")
                    continue
                
            earthquake_layer.add_to(m)
    except Exception as e:
        logger.error(f"Error fetching USGS data: {str(e)}")
    
    # Add active alerts
    active_alerts = get_active_alerts()
    if active_alerts:
        alert_layer = folium.FeatureGroup(name='Active Alerts')
        for alert in active_alerts:
            folium.CircleMarker(
                location=[alert['latitude'], alert['longitude']],
                radius=10,
                color='yellow',
                fill=True,
                popup=f"Active Alert: {alert['primary_location_name']}<br>{alert['last_alert_details']}",
                weight=2,
                tooltip=f"Alert: {alert['primary_location_name']}"
            ).add_to(alert_layer)
        alert_layer.add_to(m)
    
    # Calculate risk levels for grid points
    for lat in lat_range:
        for lon in lon_range:
            try:
                # Check earthquake risk
                eq_risk = check_earthquake_risk(lat, lon)
                if eq_risk['risk_level'] > 0:
                    weight = eq_risk['risk_level']  # Removed 0.33 multiplier
                    earthquake_data.append([lat, lon, weight])
                
                # Check cyclone risk
                cyc_risk = check_cyclone_risk(lat, lon)
                if cyc_risk['risk_level'] > 0:
                    weight = cyc_risk['risk_level']  # Removed 0.33 multiplier
                    cyclone_data.append([lat, lon, weight])
            except Exception as e:
                logger.error(f"Error calculating risk for {lat}, {lon}: {str(e)}")
                continue
    
    # Add earthquake heatmap layer
    if earthquake_data:
        plugins.HeatMap(
            earthquake_data,
            name='Earthquake Risk',
            min_opacity=0.4,  # Increased from 0.3
            max_zoom=12,      # Increased from 8
            radius=15,        # Decreased from 25 for better precision
            blur=10,          # Decreased from 15
            gradient={0.4: 'blue', 0.65: 'yellow', 0.9: 'red'}  # Adjusted gradient
        ).add_to(m)
    
    # Add cyclone heatmap layer
    if cyclone_data:
        plugins.HeatMap(
            cyclone_data,
            name='Cyclone Risk',
            min_opacity=0.4,  # Increased from 0.3
            max_zoom=12,      # Increased from 8
            radius=15,        # Decreased from 25
            blur=10,          # Decreased from 15
            gradient={0.4: 'green', 0.65: 'yellow', 0.9: 'red'}  # Adjusted gradient
        ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add legend with active alerts
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border: 2px solid grey; border-radius: 5px;">
        <h4>Risk Levels</h4>
        <p><span style="color: blue;">■</span> Low Risk</p>
        <p><span style="color: yellow;">■</span> Moderate Risk</p>
        <p><span style="color: red;">■</span> High Risk</p>
        <p><span style="color: red;">●</span> Recent Earthquakes (USGS)</p>
        <p><span style="color: yellow;">●</span> Active Alerts</p>
        <small class="text-muted">Last updated: {}</small>
    </div>
    '''.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m._repr_html_()

def get_risk_data():
    """
    Get JSON data of current risk levels for API endpoint
    """
    risk_data = {
        'timestamp': datetime.now().isoformat(),
        'earthquake_risks': [],
        'cyclone_risks': [],
        'active_alerts': get_active_alerts()
    }
    
    # Generate grid points across the region
    lat_range = np.linspace(8, 35, 15)  # Reduced points for API response
    lon_range = np.linspace(68, 97, 15)
    
    for lat in lat_range:
        for lon in lon_range:
            try:
                # Check earthquake risk
                eq_risk = check_earthquake_risk(lat, lon)
                if eq_risk['risk_level'] > 0:
                    risk_data['earthquake_risks'].append({
                        'lat': lat,
                        'lon': lon,
                        'risk_level': eq_risk['risk_level'],
                        'details': eq_risk['details']
                    })
                
                # Check cyclone risk
                cyc_risk = check_cyclone_risk(lat, lon)
                if cyc_risk['risk_level'] > 0:
                    risk_data['cyclone_risks'].append({
                        'lat': lat,
                        'lon': lon,
                        'risk_level': cyc_risk['risk_level'],
                        'details': cyc_risk['details']
                    })
            except Exception as e:
                logger.error(f"Error calculating risk for {lat}, {lon}: {str(e)}")
                continue
    
    return risk_data 