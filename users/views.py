from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserSubscription
from django.contrib.auth.decorators import login_required
from .forms import SubscriptionForm
import logging
import json
from django.http import JsonResponse
from .risk_heatmap import generate_risk_heatmap, get_risk_data

logger = logging.getLogger(__name__)

# Create your views here.

def subscription_form(request):
    # Check if user already has a subscription
    existing_subscription = None
    if request.user.is_authenticated:
        try:
            existing_subscription = UserSubscription.objects.get(user=request.user)
            logger.info(f"Found existing subscription for user {request.user.username}")
        except UserSubscription.DoesNotExist:
            logger.info(f"No existing subscription found for user {request.user.username}")
    
    if request.method == 'POST':
        logger.info(f"Received form submission with data: {request.POST}")
        
        # If user already has a subscription, use instance parameter to update it
        if existing_subscription and request.user.is_authenticated:
            form = SubscriptionForm(request.POST, instance=existing_subscription)
            logger.info("Updating existing subscription")
        else:
            form = SubscriptionForm(request.POST)
            logger.info("Creating new subscription")
        
        if form.is_valid():
            try:
                subscription = form.save(commit=False)
                
                # Set user if authenticated and not already set
                if request.user.is_authenticated and not subscription.user:
                    subscription.user = request.user
                
                # Save to database
                subscription.save()
                logger.info("Subscription saved successfully")
                
                success_message = "Subscription updated successfully!" if existing_subscription else "Subscription created successfully!"
                messages.success(request, f"{success_message} You will now receive disaster alerts.")
                return redirect('/users/subscribe/success/') # or any other URL
            except Exception as e:
                logger.error(f"Error saving subscription: {e}")
                messages.error(request, f"There was a problem saving your subscription: {e}")
        else:
            logger.warning(f"Form validation failed with errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    field_name = field.replace('_', ' ').title()
                    messages.error(request, f"{field_name}: {error}")
    else:
        # If user has an existing subscription, pre-populate the form with it
        if existing_subscription:
            form = SubscriptionForm(instance=existing_subscription)
            messages.info(request, "You already have a subscription. Changes you make will update your existing subscription.")
        else:
            form = SubscriptionForm()
    
    return render(request, 'users/subscription_form.html', {'form': form})

def subscription_success(request):
    return render(request, 'users/subscription_success.html')

def debug_subscription_form(request):
    """A simplified form for debugging submission issues"""
    if request.method == 'POST':
        # Log the POST data
        logger.info(f"Debug form submission with data: {request.POST}")
        
        try:
            # Manually create a subscription object
            subscription = UserSubscription(
                phone_number=request.POST.get('phone_number'),
                email=request.POST.get('email'),
                primary_location_name=request.POST.get('primary_location_name'),
                latitude=float(request.POST.get('latitude')),
                longitude=float(request.POST.get('longitude')),
                enable_whatsapp_alerts='enable_whatsapp_alerts' in request.POST,
                whatsapp_phone_number=request.POST.get('whatsapp_phone_number', '')
            )
            
            # Set user if authenticated
            if request.user.is_authenticated:
                subscription.user = request.user
            
            # Save to database
            subscription.save()
            logger.info(f"Debug subscription saved successfully with ID: {subscription.id}")
            
            messages.success(request, f"Success! Subscription created with ID: {subscription.id}")
        except Exception as e:
            logger.error(f"Error in debug form: {e}")
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, 'users/debug_form.html')

def force_create_subscription(request):
    """Debug view that deletes existing subscription before creating a new one"""
    if request.method == 'POST':
        logger.info(f"Force create subscription with data: {request.POST}")
        
        try:
            # If user is authenticated, delete their existing subscription first
            if request.user.is_authenticated:
                try:
                    existing = UserSubscription.objects.filter(user=request.user)
                    if existing.exists():
                        existing_id = existing.first().id
                        existing.delete()
                        logger.info(f"Deleted existing subscription {existing_id} for user {request.user.username}")
                except Exception as e:
                    logger.error(f"Error deleting existing subscription: {e}")
            
            # Create a new subscription
            subscription = UserSubscription(
                phone_number=request.POST.get('phone_number'),
                email=request.POST.get('email'),
                primary_location_name=request.POST.get('primary_location_name'),
                latitude=float(request.POST.get('latitude')),
                longitude=float(request.POST.get('longitude')),
                enable_whatsapp_alerts='enable_whatsapp_alerts' in request.POST,
                whatsapp_phone_number=request.POST.get('whatsapp_phone_number', '')
            )
            
            # Only set user if authenticated
            if request.user.is_authenticated:
                subscription.user = request.user
            
            # Save to database
            subscription.save()
            logger.info(f"Force created subscription with ID: {subscription.id}")
            
            messages.success(request, f"Success! New subscription created with ID: {subscription.id}")
        except Exception as e:
            logger.error(f"Error in force create: {e}")
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, 'users/force_create_form.html')

def anonymous_subscription(request):
    """Create a subscription without associating it with a user"""
    if request.method == 'POST':
        logger.info(f"Anonymous subscription with data: {request.POST}")
        
        try:
            # Create a new subscription without a user
            subscription = UserSubscription(
                phone_number=request.POST.get('phone_number'),
                email=request.POST.get('email'),
                primary_location_name=request.POST.get('primary_location_name'),
                latitude=float(request.POST.get('latitude')),
                longitude=float(request.POST.get('longitude')),
                enable_whatsapp_alerts='enable_whatsapp_alerts' in request.POST,
                whatsapp_phone_number=request.POST.get('whatsapp_phone_number', '')
                # No user field assigned
            )
            
            # Save to database
            subscription.save()
            logger.info(f"Created anonymous subscription with ID: {subscription.id}")
            
            messages.success(request, f"Success! Anonymous subscription created with ID: {subscription.id}")
        except Exception as e:
            logger.error(f"Error creating anonymous subscription: {e}")
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, 'users/anonymous_form.html')  # Create a similar template

def risk_heatmap_view(request):
    """View for displaying the risk heatmap."""
    return render(request, 'risk_heatmap.html', {
        'map_html': generate_risk_heatmap()
    })

def risk_data_api(request):
    """API endpoint for getting current risk data."""
    return JsonResponse(get_risk_data())

def home(request):
    return render(request, 'index.html')
