"""
Test script to verify the risk detection algorithms for any location.
"""

import os
import sys
import logging

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Import necessary modules
import django
django.setup()

from users.tasks import check_cyclone_risk, check_earthquake_risk

def test_location_risk(latitude, longitude, location_name=None):
    """Test risk detection for a specific location."""
    location_name = location_name or f"Latitude: {latitude}, Longitude: {longitude}"
    
    print(f"\n=== Testing Risk Detection for {location_name} ===")
    print(f"Coordinates: {latitude}, {longitude}")
    print("--------------------------------------------------")
    
    # Check for cyclones
    print("\nChecking cyclone risk...")
    try:
        cyclone_risk = check_cyclone_risk(latitude, longitude)
        print(f"Cyclone risk level: {cyclone_risk['risk_level']}")
        print(f"Details: {cyclone_risk['details']}")
    except Exception as e:
        print(f"Error checking cyclone risk: {e}")
    
    # Check for earthquakes
    print("\nChecking earthquake risk...")
    try:
        earthquake_risk = check_earthquake_risk(latitude, longitude)
        print(f"Earthquake risk level: {earthquake_risk['risk_level']}")
        print(f"Details: {earthquake_risk['details']}")
    except Exception as e:
        print(f"Error checking earthquake risk: {e}")
    
    print("\n--------------------------------------------------")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test disaster risk detection for a specific location.')
    parser.add_argument('--lat', type=float, help='Latitude (e.g., 37.7749)')
    parser.add_argument('--lon', type=float, help='Longitude (e.g., -122.4194)')
    parser.add_argument('--name', type=str, help='Location name (optional)')
    
    args = parser.parse_args()
    
    if args.lat is None or args.lon is None:
        # Use some sample locations
        print("=== Testing Risk Detection on Sample Locations ===")
        
        # San Francisco (near major fault lines)
        test_location_risk(37.7749, -122.4194, "San Francisco, USA")
        
        # Tokyo, Japan (seismically active)
        test_location_risk(35.6762, 139.6503, "Tokyo, Japan")
        
        # Miami, Florida (hurricane-prone)
        test_location_risk(25.7617, -80.1918, "Miami, USA")
        
        # Your local coordinates from the database
        print("\nChecking configured user locations from database:")
        print("--------------------------------------------------")
        
        try:
            from users.models import UserSubscription
            users = UserSubscription.objects.all()
            for user in users:
                test_location_risk(user.latitude, user.longitude, user.primary_location_name)
        except Exception as e:
            print(f"Error accessing user locations: {e}")
    else:
        # Test with the provided coordinates
        test_location_risk(args.lat, args.lon, args.name)
    
    print("\nTesting completed!")
    input("Press Enter to exit...") 