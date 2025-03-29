from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserSubscription
import random

class Command(BaseCommand):
    help = 'Creates a test user with subscription at specified location'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='testuser', help='Username for test user')
        parser.add_argument('--email', type=str, default='test@example.com', help='Email for test user')
        parser.add_argument('--password', type=str, default='testpassword', help='Password for test user')
        parser.add_argument('--lat', type=float, help='Latitude for test user')
        parser.add_argument('--lon', type=float, help='Longitude for test user')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        lat = options.get('lat')
        lon = options.get('lon')
        
        # Create random coordinates near a major city if not provided
        if lat is None or lon is None:
            # Sample coordinates for major cities
            cities = [
                {"name": "New York", "lat": 40.7128, "lon": -74.0060},
                {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
                {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
                {"name": "London", "lat": 51.5074, "lon": -0.1278},
                {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
            ]
            
            city = random.choice(cities)
            # Add small random offset (within ~10km)
            lat = city["lat"] + random.uniform(-0.1, 0.1)
            lon = city["lon"] + random.uniform(-0.1, 0.1)
            location_name = f"Near {city['name']}"
        else:
            location_name = f"Custom Location ({lat}, {lon})"
        
        # Create user if doesn't exist
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            self.stdout.write(self.style.WARNING(f'User {username} already exists'))
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Created user {username}'))
        
        # Create or update subscription
        subscription, created = UserSubscription.objects.update_or_create(
            user=user,
            defaults={
                'email': email,
                'phone_number': '1234567890',  # Dummy phone number
                'primary_location_name': location_name,
                'latitude': lat,
                'longitude': lon,
                'is_location_verified': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created subscription for {username} at {lat}, {lon}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated subscription for {username} at {lat}, {lon}')) 