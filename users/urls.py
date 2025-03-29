from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('subscribe/', views.subscription_form, name='subscription_form'),
    path('subscribe/success/', views.subscription_success, name='subscription_success'),
    path('debug-subscribe/', views.debug_subscription_form, name='debug_subscription_form'),
    path('force-create/', views.force_create_subscription, name='force_create_subscription'),
] 