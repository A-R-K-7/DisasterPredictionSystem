from django.urls import path
from . import views

urlpatterns = [
    path('whatsapp-alert/', views.earthquake_alert, name='earthquake_whatsapp_alert'),
    # Add other URL patterns as needed
] 