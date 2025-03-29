from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserSubscription
import logging

# Add this line to define the logger
logger = logging.getLogger(__name__)

class UserSubscriptionForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    primary_location_name = forms.CharField(max_length=255, required=True)
    latitude = forms.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude = forms.DecimalField(max_digits=9, decimal_places=6, required=True)
    
    class Meta:
        model = UserSubscription
        fields = ['email', 'phone_number', 'primary_location_name', 'latitude', 'longitude']
    
    def save(self, user, commit=True):
        subscription = super().save(commit=False)
        subscription.user = user
        subscription.is_location_verified = True  # Auto-verify for now
        
        if commit:
            subscription.save()
        return subscription 

class UserProfileForm(forms.ModelForm):
    # Keep existing fields...
    
    enable_whatsapp_alerts = forms.BooleanField(
        required=False,
        label="Enable WhatsApp Alerts",
        help_text="Receive disaster alerts via WhatsApp"
    )
    
    whatsapp_phone_number = forms.CharField(
        max_length=15,
        required=False,
        label="WhatsApp Phone Number",
        help_text="Enter your WhatsApp number with country code (e.g., +1234567890)"
    )
    
    class Meta:
        model = UserSubscription
        fields = [
            # Your existing fields...
            'enable_whatsapp_alerts',
            'whatsapp_phone_number',
        ] 

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = UserSubscription
        fields = [
            'phone_number', 
            'email', 
            'primary_location_name', 
            'latitude', 
            'longitude',
            'enable_whatsapp_alerts',
            'whatsapp_phone_number'
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'primary_location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your location'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any',
                'placeholder': 'Latitude'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any',
                'placeholder': 'Longitude'
            }),
            'enable_whatsapp_alerts': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'whatsapp_phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'WhatsApp number with country code'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make WhatsApp phone number optional
        self.fields['whatsapp_phone_number'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Round latitude and longitude to avoid decimal place validation errors
        if 'latitude' in cleaned_data and cleaned_data['latitude']:
            cleaned_data['latitude'] = round(float(cleaned_data['latitude']), 6)
        
        if 'longitude' in cleaned_data and cleaned_data['longitude']:
            cleaned_data['longitude'] = round(float(cleaned_data['longitude']), 6)
        
        # Only require WhatsApp number if alerts are enabled
        enable_whatsapp = cleaned_data.get('enable_whatsapp_alerts')
        whatsapp_number = cleaned_data.get('whatsapp_phone_number')
        
        if enable_whatsapp and not whatsapp_number:
            self.add_error('whatsapp_phone_number', 'WhatsApp number is required when alerts are enabled')
        
        return cleaned_data 