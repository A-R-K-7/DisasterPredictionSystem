from django.core.management.base import BaseCommand
from users.models import UserSubscription

class Command(BaseCommand):
    help = 'Create a test subscription'

    def handle(self, *args, **options):
        try:
            # Create a test subscription directly
            subscription = UserSubscription.objects.create(
                phone_number="9347153193",
                email="test@example.com",
                primary_location_name="Test Location",
                latitude=17.385044,
                longitude=78.486671,
                enable_whatsapp_alerts=True,
                whatsapp_phone_number="+919347153193"
            )
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created test subscription with ID: {subscription.id}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating test subscription: {str(e)}')) 