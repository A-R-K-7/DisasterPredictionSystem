import joblib
import numpy as np
import pandas as pd
import logging
from django.conf import settings
import os
from datetime import datetime
import math

logger = logging.getLogger(__name__)

# Load the XGBoost model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'baseline_xgboost_model.pkl')
try:
    xgb_model = joblib.load(MODEL_PATH)
    logger.info("XGBoost cyclone model loaded successfully")
except Exception as e:
    logger.error(f"Error loading XGBoost model: {str(e)}")
    xgb_model = None

def calculate_wind_components(wind_speed, wind_direction):
    """Calculate U and V components of wind"""
    wind_direction_rad = math.radians(wind_direction)
    wind_u = -wind_speed * math.sin(wind_direction_rad)
    wind_v = -wind_speed * math.cos(wind_direction_rad)
    return wind_u, wind_v

def is_monsoon_season(month):
    """Check if current month is in monsoon season (June to September)"""
    return 6 <= month <= 9

def is_cyclone_season(month):
    """Check if current month is in cyclone season (April-June or September-December)"""
    return month in [4, 5, 6, 9, 10, 11, 12]

def check_location(lat, lon):
    """Check if location is in Bay of Bengal or Arabian Sea"""
    in_bay_of_bengal = (85 <= lon <= 95) and (10 <= lat <= 22)
    in_arabian_sea = (60 <= lon <= 75) and (10 <= lat <= 22)
    return in_bay_of_bengal, in_arabian_sea

def predict_cyclone_risk(features):
    """
    Predict cyclone risk using the XGBoost model.
    
    Args:
        features (list): List of weather features
        
    Returns:
        dict: Dictionary containing risk level and details
    """
    try:
        if xgb_model is None:
            return {'risk_level': 0, 'details': 'Model not available', 'raw_prediction': None}
        
        # Extract basic features
        wind_speed = features[0]
        wind_direction = features[1]
        pressure = features[2]
        humidity = features[3]
        temperature = features[4]
        lat = features[10]
        lon = features[11]
        
        # Get current time components
        now = datetime.now()
        month = now.month
        day = now.day
        hour = now.hour
        
        # Calculate cyclical time features
        sin_month = math.sin(2 * math.pi * month / 12)
        cos_month = math.cos(2 * math.pi * month / 12)
        sin_day = math.sin(2 * math.pi * day / 31)
        cos_day = math.cos(2 * math.pi * day / 31)
        sin_hour = math.sin(2 * math.pi * hour / 24)
        cos_hour = math.cos(2 * math.pi * hour / 24)
        
        # Calculate wind components
        wind_u, wind_v = calculate_wind_components(wind_speed, wind_direction)
        
        # Location checks
        in_bay_of_bengal, in_arabian_sea = check_location(lat, lon)
        abs_latitude = abs(lat)
        
        # Calculate derived features
        temp_pressure_ratio = temperature / pressure if pressure != 0 else 0
        wind_pressure_interaction = wind_speed * pressure / 1000
        humid_temp_index = humidity * temperature / 100
        precip_temp_humid = features[8] * temperature * humidity / 1000  # using visibility as proxy for precipitation
        wind_fluctuation = abs(wind_speed - features[15])  # using wind_speed_trend
        
        # Create feature array in exact order expected by model
        feature_array = np.array([
            temperature,           # temperature_2m
            humidity,             # relative_humidity_2m
            wind_speed,           # wind_speed_10m
            wind_direction,       # wind_direction_10m
            pressure,             # pressure_msl
            features[9],          # cloud_cover
            features[8] / 1000,   # precipitation (from visibility)
            wind_u,              # wind_u
            wind_v,              # wind_v
            lat,                 # final_lat
            lon,                 # final_lon
            abs_latitude,        # abs_latitude
            month,               # month
            day,                 # day
            hour,               # hour
            sin_month,          # sin_month
            cos_month,          # cos_month
            sin_day,            # sin_day
            cos_day,            # cos_day
            sin_hour,           # sin_hour
            cos_hour,           # cos_hour
            int(is_monsoon_season(month)),     # is_monsoon
            int(is_cyclone_season(month)),     # is_cyclone_season
            int(in_bay_of_bengal),            # in_bay_of_bengal
            int(in_arabian_sea),              # in_arabian_sea
            temp_pressure_ratio,              # temp_pressure_ratio
            wind_pressure_interaction,        # wind_pressure_interaction
            humid_temp_index,                # humid_temp_index
            precip_temp_humid,               # precip_temp_humid
            wind_fluctuation                 # wind_fluctuation
        ]).reshape(1, -1)
        
        # Create DataFrame with correct column names
        columns = [
            'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'wind_direction_10m',
            'pressure_msl', 'cloud_cover', 'precipitation', 'wind_u', 'wind_v', 'final_lat',
            'final_lon', 'abs_latitude', 'month', 'day', 'hour', 'sin_month', 'cos_month',
            'sin_day', 'cos_day', 'sin_hour', 'cos_hour', 'is_monsoon', 'is_cyclone_season',
            'in_bay_of_bengal', 'in_arabian_sea', 'temp_pressure_ratio', 'wind_pressure_interaction',
            'humid_temp_index', 'precip_temp_humid', 'wind_fluctuation'
        ]
        X = pd.DataFrame(feature_array, columns=columns)
        
        # Get model prediction
        raw_prediction = float(xgb_model.predict_proba(X)[0][1])
        
        # Convert probability to risk level
        if raw_prediction > 0.75:
            risk_level = 3
            details = "High cyclone risk predicted by ML model"
        elif raw_prediction > 0.5:
            risk_level = 2
            details = "Moderate cyclone risk predicted by ML model"
        elif raw_prediction > 0.25:
            risk_level = 1
            details = "Low cyclone risk predicted by ML model"
        else:
            risk_level = 0
            details = "No immediate cyclone risk predicted by ML model"
            
        return {
            'risk_level': risk_level,
            'details': details,
            'raw_prediction': raw_prediction
        }
        
    except Exception as e:
        logger.error(f"Error in cyclone prediction: {str(e)}")
        return {'risk_level': 0, 'details': 'Error in prediction', 'raw_prediction': None} 