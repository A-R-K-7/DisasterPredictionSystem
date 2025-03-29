from django.shortcuts import render
from django.http import HttpResponse
import pywhatkit
import datetime
import time

# Create your views here.

def send_whatsapp_alert(phone_number, message):
    """
    Send WhatsApp alert using PyWhatKit
    """
    try:
        # Get current time to schedule message (send 1 minute from now)
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute + 1  # Send after 1 minute
        
        # Adjust hour if minute rolls over
        if minute >= 60:
            minute = minute % 60
            hour = (hour + 1) % 24
        
        # Remove any '+' from the phone number as pywhatkit doesn't need it
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        # Send the WhatsApp message
        pywhatkit.sendwhatmsg(f"+{phone_number}", message, hour, minute, wait_time=15)
        return {'success': True}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def earthquake_alert(request):
    """
    View to trigger an earthquake alert via WhatsApp
    """
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        magnitude = request.POST.get('magnitude')
        location = request.POST.get('location')
        
        # Format the message
        message = f"🚨 EARTHQUAKE ALERT 🚨\nMagnitude: {magnitude}\nLocation: {location}\nStay safe and follow local emergency protocols."
        
        result = send_whatsapp_alert(phone_number, message)
        
        if result.get('success'):
            return HttpResponse("WhatsApp alert scheduled successfully! The browser will open momentarily to send the message.")
        else:
            return HttpResponse(f"Failed to send WhatsApp alert: {result.get('error')}")
    
    return render(request, 'earthquakes/whatsapp_alert_form.html')
