"""
Direct WhatsApp testing script.
This script provides a reliable way to test WhatsApp message sending.
"""

import os
import sys
import time
import logging
import pywhatkit
import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def direct_send_whatsapp(phone_number, message):
    """
    Send WhatsApp message with maximum reliability and detailed logging.
    """
    logger.info(f"Preparing to send WhatsApp message to {phone_number}")
    
    # Remove any '+' from the phone number if present
    if phone_number.startswith('+'):
        phone_number = phone_number[1:]
        logger.debug(f"Removed + from phone number, now: {phone_number}")
    
    # Format the full phone number with + for PyWhatKit
    full_number = f"+{phone_number}"
    logger.info(f"Formatted phone number: {full_number}")
    
    # Get current time
    now = datetime.datetime.now()
    logger.info(f"Current time: {now.strftime('%H:%M:%S')}")
    
    # Set time to send (1 minute from now)
    send_hour = now.hour
    send_minute = now.minute + 1
    
    # Adjust if minute rolls over
    if send_minute >= 60:
        send_minute = send_minute % 60
        send_hour = (send_hour + 1) % 24
    
    logger.info(f"Will attempt to send at: {send_hour}:{send_minute:02d}")
    logger.info(f"Message to send: {message}")
    
    # Try using the standard method first
    try:
        logger.info("Using standard sendwhatmsg method...")
        print("\n==================================================")
        print(f"SENDING WHATSAPP MESSAGE TO: {full_number}")
        print(f"TIME: {send_hour}:{send_minute:02d}")
        print(f"MESSAGE: {message}")
        print("==================================================")
        print("\nWATCH FOR BROWSER WINDOW - You may need to scan QR code if not already logged in")
        print("The message will be sent automatically after WhatsApp Web loads\n")
        
        pywhatkit.sendwhatmsg(
            full_number, 
            message, 
            send_hour, 
            send_minute, 
            wait_time=30,      # Wait 30 seconds for WhatsApp Web to load
            tab_close=True,    # Close the tab after sending
            close_time=5,      # Wait 5 seconds before closing the tab
            print_wait_time=True  # Print wait time information
        )
        logger.info("sendwhatmsg completed")
        return True
        
    except Exception as e:
        logger.error(f"Standard method failed: {str(e)}")
        
        # Try fallback method - instant send
        try:
            logger.info("Trying fallback method sendwhatmsg_instantly...")
            print("\n==================================================")
            print("USING FALLBACK METHOD - INSTANT SEND")
            print(f"SENDING WHATSAPP MESSAGE TO: {full_number}")
            print(f"MESSAGE: {message}")
            print("==================================================")
            print("\nWATCH FOR BROWSER WINDOW\n")
            
            pywhatkit.sendwhatmsg_instantly(
                full_number,
                message,
                wait_time=30,
                tab_close=True,
                close_time=5
            )
            logger.info("sendwhatmsg_instantly completed")
            return True
            
        except Exception as e2:
            logger.error(f"Fallback method also failed: {str(e2)}")
            
            # Try another fallback method - open web directly
            try:
                logger.info("Trying last resort - open WhatsApp Web directly...")
                print("\n==================================================")
                print("USING LAST RESORT METHOD - MANUAL ASSIST")
                print(f"Opening WhatsApp Web for: {full_number}")
                print("==================================================")
                
                # Open WhatsApp Web with the phone number
                whatsapp_web_url = f"https://web.whatsapp.com/send?phone={full_number}&text={message}"
                print(f"\nOpening: {whatsapp_web_url}")
                print("Please manually click Send when WhatsApp Web loads")
                
                import webbrowser
                webbrowser.open(whatsapp_web_url)
                logger.info("Opened WhatsApp Web URL directly")
                
                print("\nBrowser window should now be open. Please:")
                print("1. Wait for WhatsApp Web to load fully")
                print("2. Manually press the send button (green arrow)")
                print("3. Then close the browser tab when done\n")
                
                return True
                
            except Exception as e3:
                logger.error(f"All methods failed. Last error: {str(e3)}")
                return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Direct WhatsApp message sender with multiple fallback methods')
    parser.add_argument('--phone', type=str, help='Phone number with country code (e.g., 911234567890)')
    parser.add_argument('--message', type=str, help='Message to send')
    
    args = parser.parse_args()
    
    if not args.phone:
        # If not provided, use standard test
        try:
            import django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
            django.setup()
            
            from users.models import UserSubscription
            
            # Try to get a phone number from the database
            user = UserSubscription.objects.filter(enable_whatsapp_alerts=True, whatsapp_phone_number__isnull=False).first()
            if user:
                phone_number = user.whatsapp_phone_number
                print(f"Using phone number from database: {phone_number}")
            else:
                phone_number = input("Enter WhatsApp number with country code (e.g., 911234567890): ")
        except:
            phone_number = input("Enter WhatsApp number with country code (e.g., 911234567890): ")
    else:
        phone_number = args.phone
    
    if not args.message:
        message = "This is a direct test of the Disaster Prediction System WhatsApp alert functionality. If you're seeing this, the direct method works!"
    else:
        message = args.message
    
    result = direct_send_whatsapp(phone_number, message)
    
    if result:
        print("\nWhatsApp message process completed.")
    else:
        print("\nFailed to send WhatsApp message using all available methods.")
        
    input("\nPress Enter to exit...") 