from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import UserSubscription
from .whatsapp_utils import send_whatsapp_alert
from earthquakes.model_utils import predict_earthquake_risk
from cyclones.model_utils import predict_cyclone_risk
import requests
import json
from math import radians, sin, cos, sqrt, atan2
import logging

logger = logging.getLogger(__name__)

@shared_task
def test_email():
    """Test task to verify email configuration"""
    try:
        send_mail(
            subject='Disaster Prediction System - Test Email',
            message='This is a test email to verify that the email notification system is working correctly.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        logger.info("Test email sent successfully")
        return "Test email sent successfully"
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        raise

@shared_task
def check_disaster_predictions():
    """Check for potential disasters and send alerts to users in affected areas."""
    try:
        logger.info("Starting disaster prediction check")
        
        # Validate that we can access the database
        try:
            users_count = UserSubscription.objects.count()
            logger.info(f"Found {users_count} user subscriptions")
            
            if users_count == 0:
                logger.warning("No user subscriptions found - nothing to check")
                return "No user subscriptions found - nothing to check"
                
        except Exception as db_error:
            logger.error(f"Database access error: {str(db_error)}")
            return f"Database access error: {str(db_error)}"
        
        # Process each user subscription
        process_count = 0
        error_count = 0
        users = UserSubscription.objects.all()
        
        for user in users:
            try:
                process_count += 1
                logger.debug(f"Processing user {user.email} ({process_count}/{users_count})")
                
                # Check for cyclones
                cyclone_risk = check_cyclone_risk(user.latitude, user.longitude)
                if cyclone_risk['risk_level'] > 0:
                    logger.info(f"Cyclone risk detected for {user.email}: Level {cyclone_risk['risk_level']}")
                    send_disaster_alert(
                        user,
                        'Cyclone Alert',
                        f"Potential cyclone detected in your area!\nRisk Level: {cyclone_risk['risk_level']}\n{cyclone_risk['details']}"
                    )
                
                # Check for earthquakes
                earthquake_risk = check_earthquake_risk(user.latitude, user.longitude)
                if earthquake_risk['risk_level'] > 0:
                    logger.info(f"Earthquake risk detected for {user.email}: Level {earthquake_risk['risk_level']}")
                    send_disaster_alert(
                        user,
                        'Earthquake Alert',
                        f"Potential earthquake risk in your area!\nRisk Level: {earthquake_risk['risk_level']}\n{earthquake_risk['details']}"
                    )
                
            except Exception as user_error:
                error_count += 1
                logger.error(f"Error processing user {user.email}: {str(user_error)}")
                continue
        
        logger.info(f"Disaster prediction check completed. Processed {process_count} users with {error_count} errors.")
        return f"Disaster prediction check completed. Processed {process_count} users with {error_count} errors."
        
    except Exception as e:
        logger.error(f"Critical error in disaster prediction check: {str(e)}")
        return f"Critical error in disaster check: {str(e)}"

def check_cyclone_risk(lat, lon):
    """Check cyclone risk using weather API and XGBoost model predictions."""
    try:
        api_key = settings.OPENWEATHERMAP_API_KEY
        url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
        
        response = requests.get(url)
        data = response.json()
        
        # Extract weather features
        wind_speed = data.get('wind', {}).get('speed', 0)
        wind_deg = data.get('wind', {}).get('deg', 0)
        pressure = data.get('main', {}).get('pressure', 1013)
        humidity = data.get('main', {}).get('humidity', 50)
        temperature = data.get('main', {}).get('temp', 25)
        feels_like = data.get('main', {}).get('feels_like', temperature)
        temp_min = data.get('main', {}).get('temp_min', temperature - 2)
        temp_max = data.get('main', {}).get('temp_max', temperature + 2)
        visibility = data.get('visibility', 10000)
        clouds = data.get('clouds', {}).get('all', 0)
        
        # Get 5-day forecast for trend analysis
        forecast_url = f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric'
        forecast_response = requests.get(forecast_url)
        forecast_data = forecast_response.json()
        
        # Process forecast data
        forecast_entries = forecast_data.get('list', [])
        
        # Initialize forecast features
        forecast_temps = []
        forecast_pressures = []
        forecast_humidities = []
        forecast_wind_speeds = []
        forecast_wind_dirs = []
        
        # Get next 5 forecasts (roughly 15 hours)
        for entry in forecast_entries[:5]:
            forecast_temps.append(entry.get('main', {}).get('temp', temperature))
            forecast_pressures.append(entry.get('main', {}).get('pressure', pressure))
            forecast_humidities.append(entry.get('main', {}).get('humidity', humidity))
            forecast_wind_speeds.append(entry.get('wind', {}).get('speed', wind_speed))
            forecast_wind_dirs.append(entry.get('wind', {}).get('deg', wind_deg))
        
        # Calculate trends and averages
        temp_trend = sum(forecast_temps) / len(forecast_temps) if forecast_temps else temperature
        pressure_trend = sum(forecast_pressures) / len(forecast_pressures) if forecast_pressures else pressure
        humidity_trend = sum(forecast_humidities) / len(forecast_humidities) if forecast_humidities else humidity
        wind_speed_trend = sum(forecast_wind_speeds) / len(forecast_wind_speeds) if forecast_wind_speeds else wind_speed
        wind_dir_trend = sum(forecast_wind_dirs) / len(forecast_wind_dirs) if forecast_wind_dirs else wind_deg
        
        # Check immediate risk based on wind speed
        api_risk_level = 0
        api_details = []
        
        if wind_speed > 32.7:  # Hurricane force winds
            api_risk_level = 3
            api_details.append("Hurricane force winds detected!")
        elif wind_speed > 24.5:  # Storm force winds
            api_risk_level = 2
            api_details.append("Storm force winds detected!")
        elif wind_speed > 13.9:  # Near gale to gale force
            api_risk_level = 1
            api_details.append("Strong winds detected!")
            
        # Prepare features for ML model (30 features)
        features = [
            # Current conditions (10 features)
            wind_speed,
            wind_deg,
            pressure,
            humidity,
            temperature,
            feels_like,
            temp_min,
            temp_max,
            visibility,
            clouds,
            
            # Location features (2 features)
            lat,
            lon,
            
            # Forecast trends (5 features)
            temp_trend,
            pressure_trend,
            humidity_trend,
            wind_speed_trend,
            wind_dir_trend,
            
            # Individual forecast points (13 features to complete 30)
            *forecast_temps[:3],
            *forecast_pressures[:3],
            *forecast_humidities[:3],
            *forecast_wind_speeds[:2],
            *forecast_wind_dirs[:2]
        ]
        
        # Get ML model prediction
        ml_prediction = predict_cyclone_risk(features)
        ml_risk_level = ml_prediction['risk_level']
        
        if ml_risk_level > 0:
            api_details.append(ml_prediction['details'])
        
        # Combine risk assessments - take the higher risk level
        final_risk_level = max(api_risk_level, ml_risk_level)
        
        logger.info(f"Wind speed: {wind_speed}, Risk level: {final_risk_level}")
        
        return {
            'risk_level': final_risk_level,
            'details': "\n".join(api_details) if api_details else "No immediate cyclone risk",
            'weather_data': {
                'wind_speed': wind_speed,
                'pressure': pressure,
                'humidity': humidity,
                'temperature': temperature,
                'forecast_trend': {
                    'temp': temp_trend,
                    'pressure': pressure_trend,
                    'wind_speed': wind_speed_trend
                }
            },
            'ml_prediction': ml_prediction['raw_prediction']
        }
        
    except Exception as e:
        logger.error(f"Error checking cyclone risk: {str(e)}")
        return {'risk_level': 0, 'details': "Unable to check cyclone risk"}

def check_earthquake_risk(lat, lon):
    """Check earthquake risk using both USGS real-time data and ML model predictions."""
    try:
        # Get USGS real-time data (last month)
        url = f'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson'
        response = requests.get(url)
        data = response.json()
        
        # Process USGS data
        recent_quakes = []
        for feature in data.get('features', []):
            coords = feature.get('geometry', {}).get('coordinates', [])
            if len(coords) >= 2:
                eq_lon, eq_lat = coords[0], coords[1]
                magnitude = feature.get('properties', {}).get('mag', 0)
                distance = calculate_distance(lat, lon, eq_lat, eq_lon)
                
                if distance < 100:  # Focus on closer earthquakes for immediate risk
                    recent_quakes.append({
                        'distance': distance,
                        'magnitude': magnitude,
                        'time': feature.get('properties', {}).get('time', 0)
                    })
        
        # Calculate USGS-based risk metrics
        usgs_risk_level = 0
        usgs_details = []
        
        if recent_quakes:
            # Sort by magnitude and distance
            recent_quakes.sort(key=lambda x: (-x['magnitude'], x['distance']))
            strongest_quake = recent_quakes[0]
            
            # Check for immediate high-risk conditions
            if strongest_quake['magnitude'] >= 6.0 and strongest_quake['distance'] < 50:
                usgs_risk_level = 3
                usgs_details.append(f"USGS: Major earthquake M{strongest_quake['magnitude']:.1f} detected {strongest_quake['distance']:.1f}km away!")
            elif strongest_quake['magnitude'] >= 5.0 and strongest_quake['distance'] < 75:
                usgs_risk_level = 2
                usgs_details.append(f"USGS: Significant earthquake M{strongest_quake['magnitude']:.1f} detected {strongest_quake['distance']:.1f}km away")
            elif strongest_quake['magnitude'] >= 4.0 and strongest_quake['distance'] < 100:
                usgs_risk_level = 1
                usgs_details.append(f"USGS: Moderate earthquake M{strongest_quake['magnitude']:.1f} detected {strongest_quake['distance']:.1f}km away")
        
        # Prepare features for ML model
        features = [
            lat,  # location
            lon,
            len(recent_quakes),  # number of recent earthquakes
            max((q['magnitude'] for q in recent_quakes), default=0),  # max magnitude
            min((q['distance'] for q in recent_quakes), default=1000),  # closest distance
            sum(q['magnitude'] for q in recent_quakes)  # total seismic energy
        ]
        
        # Get ML model prediction
        ml_prediction = predict_earthquake_risk(features)
        ml_risk_level = ml_prediction['risk_level']
        
        if ml_risk_level > 0:
            usgs_details.append(f"ML Model: {ml_prediction['details']}")
        
        # Combine risk assessments - take the higher risk level
        final_risk_level = max(usgs_risk_level, ml_risk_level)
        
        # Prepare detailed response
        return {
            'risk_level': final_risk_level,
            'details': "\n".join(usgs_details) if usgs_details else "No immediate earthquake risk detected",
            'usgs_data': {
                'recent_earthquakes': len(recent_quakes),
                'strongest_magnitude': max((q['magnitude'] for q in recent_quakes), default=0),
                'closest_distance': min((q['distance'] for q in recent_quakes), default=None)
            },
            'ml_prediction': ml_prediction['raw_prediction']
        }
        
    except Exception as e:
        logger.error(f"Error checking earthquake risk: {str(e)}")
        return {'risk_level': 0, 'details': "Unable to check earthquake risk"}

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers using the Haversine formula."""
    try:
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance
    except Exception as e:
        logger.error(f"Error calculating distance: {str(e)}")
        return float('inf')

def send_disaster_alert(user, subject, message):
    """Send disaster alert via email and WhatsApp if enabled."""
    # Send email alert
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Email alert sent to {user.email}")
    except Exception as e:
        logger.error(f"Error sending email alert: {str(e)}")
    
    # Send WhatsApp alert if enabled
    if user.enable_whatsapp_alerts and user.whatsapp_phone_number:
        try:
            whatsapp_message = f"{subject}\n\n{message}"
            success = send_whatsapp_alert(user.whatsapp_phone_number, whatsapp_message)
            if success:
                logger.info(f"WhatsApp alert scheduled for {user.whatsapp_phone_number}")
            else:
                logger.warning(f"WhatsApp alert failed for {user.whatsapp_phone_number}")
        except Exception as e:
            logger.error(f"Error scheduling WhatsApp alert: {str(e)}")

@shared_task
def test_whatsapp():
    """Test task to verify WhatsApp configuration"""
    try:
        # Get a test user - perhaps the first one with WhatsApp enabled
        test_user = UserSubscription.objects.filter(enable_whatsapp_alerts=True).first()
        
        if not test_user:
            logger.warning("No users with WhatsApp alerts enabled found for testing")
            return "No test users available"
            
        message = "This is a test alert from your Disaster Prediction System. Please ignore."
        
        success = send_whatsapp_alert(test_user.whatsapp_phone_number, message)
        if success:
            logger.info(f"Test WhatsApp message scheduled for {test_user.whatsapp_phone_number}")
            return "Test WhatsApp message scheduled successfully"
        else:
            logger.error("Failed to schedule test WhatsApp message")
            return "Failed to schedule test WhatsApp message"
    except Exception as e:
        logger.error(f"Error in WhatsApp test: {str(e)}")
        return f"Error: {str(e)}" 