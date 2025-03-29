"""
Script to manually run a disaster check.
This will directly execute the disaster prediction logic without going through Celery.
"""

import os
import sys
import time
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

from users.models import UserSubscription
from users.tasks import check_cyclone_risk, check_earthquake_risk, send_disaster_alert

def run_disaster_check():
    """Run the disaster prediction check directly."""
    logger.info("Starting manual disaster prediction check...")
    
    # Get all user subscriptions
    users = UserSubscription.objects.all()
    logger.info(f"Found {users.count()} user subscriptions")
    
    if users.count() == 0:
        logger.warning("No user subscriptions found. Nothing to check.")
        return
    
    # Process each user subscription
    for user in users:
        logger.info(f"Checking user: {user.email} at location {user.primary_location_name}")
        
        # Check for cyclones
        logger.info(f"Checking cyclone risk at {user.latitude}, {user.longitude}...")
        cyclone_risk = check_cyclone_risk(user.latitude, user.longitude)
        logger.info(f"Cyclone risk level: {cyclone_risk['risk_level']}, details: {cyclone_risk['details']}")
        
        if cyclone_risk['risk_level'] > 0:
            logger.info(f"ALERT: Cyclone risk detected for {user.email}! Sending alert...")
            send_disaster_alert(
                user, 
                'Cyclone Alert', 
                f"Potential cyclone detected in your area!\nRisk Level: {cyclone_risk['risk_level']}\n{cyclone_risk['details']}"
            )
        
        # Check for earthquakes
        logger.info(f"Checking earthquake risk at {user.latitude}, {user.longitude}...")
        earthquake_risk = check_earthquake_risk(user.latitude, user.longitude)
        logger.info(f"Earthquake risk level: {earthquake_risk['risk_level']}, details: {earthquake_risk['details']}")
        
        if earthquake_risk['risk_level'] > 0:
            logger.info(f"ALERT: Earthquake risk detected for {user.email}! Sending alert...")
            send_disaster_alert(
                user, 
                'Earthquake Alert', 
                f"Potential earthquake risk in your area!\nRisk Level: {earthquake_risk['risk_level']}\n{earthquake_risk['details']}"
            )
    
    logger.info("Manual disaster check completed successfully!")

if __name__ == "__main__":
    print("=== Running Manual Disaster Prediction Check ===")
    print("This will check for potential disasters for all subscribed users")
    print("and send alerts if any risks are detected.")
    print("")
    
    run_disaster_check()
    
    print("")
    print("Disaster check completed!")
    input("Press Enter to exit...") 