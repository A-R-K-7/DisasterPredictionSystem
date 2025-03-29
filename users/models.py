from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserSubscription(models.Model):
    # Make user field optional with null=True, blank=True
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='subscription',
        null=True,  # Allow NULL values in the database
        blank=True  # Allow blank in forms
    )
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    primary_location_name = models.CharField(max_length=255)
    
    # Simplified coordinate fields with reasonable precision
    latitude = models.FloatField(help_text="Latitude coordinate")
    longitude = models.FloatField(help_text="Longitude coordinate")
    
    is_location_verified = models.BooleanField(default=False)
    # WhatsApp fields
    enable_whatsapp_alerts = models.BooleanField(default=False)
    whatsapp_phone_number = models.CharField(max_length=15, blank=True, null=True, 
                                           help_text="WhatsApp number with country code (e.g., +1234567890)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"{self.user.username}'s subscription"
        return f"Subscription for {self.email}"

    class Meta:
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'
