from django.core.management.base import BaseCommand
from users.models import UserSubscription

class Command(BaseCommand):
    help = 'Enable WhatsApp alerts for a user'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, help='User ID')
        parser.add_argument('phone', type=str, help='WhatsApp phone number with country code')

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        phone = kwargs['phone']
        
        try:
            sub = UserSubscription.objects.get(user_id=user_id)
            sub.enable_whatsapp_alerts = True
            sub.whatsapp_phone_number = phone
            sub.save()
            self.stdout.write(self.style.SUCCESS(f'WhatsApp alerts enabled for {sub.user.username}'))
        except UserSubscription.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'No user subscription found with ID {user_id}')) 