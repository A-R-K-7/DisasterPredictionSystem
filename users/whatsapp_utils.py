import pywhatkit
import datetime
import time
import logging
import webbrowser
import pyautogui
import os
import urllib.parse
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)

def remove_emojis(text):
    """Remove emojis from text"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def send_whatsapp_alert(phone_number, message):
    """
    Send WhatsApp alert using direct web approach with Selenium
    """
    try:
        # Format phone number correctly
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        # Remove emojis and encode message
        clean_message = remove_emojis(message)
        encoded_message = urllib.parse.quote(clean_message)
        
        # Create WhatsApp Web URL
        whatsapp_url = f"https://web.whatsapp.com/send?phone={phone_number}&text={encoded_message}"
        
        try:
            # Use direct URL method first (faster)
            logger.info(f"Attempting to send WhatsApp message to {phone_number}")
            
            # Open WhatsApp Web
            webbrowser.open(whatsapp_url)
            
            # Wait for page to load and WhatsApp Web to initialize
            time.sleep(20)  # Reduced wait time
            
            # Press Enter to send
            pyautogui.press('enter')
            
            # Wait briefly to ensure message is sent
            time.sleep(3)
            
            # Close browser window
            pyautogui.hotkey('ctrl', 'w')
            
            logger.info(f"WhatsApp message sent successfully to {phone_number}")
            return True
            
        except Exception as direct_e:
            logger.error(f"Error with direct method: {str(direct_e)}")
            logger.info("Falling back to pywhatkit method...")
            
            # Get current time for scheduling
            now = datetime.datetime.now()
            hour = now.hour
            minute = (now.minute + 1) % 60
            if minute == 0:
                hour = (hour + 1) % 24
            
            # Try pywhatkit as fallback
            pywhatkit.sendwhatmsg(
                f"+{phone_number}",
                clean_message,
                hour,
                minute,
                wait_time=20,
                tab_close=True,
                close_time=3
            )
            
            logger.info(f"WhatsApp message sent via pywhatkit to {phone_number}")
            return True
    
    except Exception as e:
        logger.error(f"Error sending WhatsApp alert to {phone_number}: {str(e)}")
        logger.error("Please make sure you're logged into WhatsApp Web and have a stable internet connection")
        return False 