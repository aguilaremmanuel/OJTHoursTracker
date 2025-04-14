from django.core.management.base import BaseCommand
from OJTHoursTracker_app.models import User
from django.db.models import Count

class Command(BaseCommand):
    help = 'Clean up duplicate users'

    def handle(self, *args, **options):
        # Find duplicate emails
        duplicates = User.objects.values('email') \
            .annotate(email_count=Count('email')) \
            .filter(email_count__gt=1)

        for dup in duplicates:
            email = dup['email']
            self.stdout.write(f"Processing duplicates for {email}")
            
            # Keep the first user, delete others
            users = User.objects.filter(email=email).order_by('date_joined')
            keeper = users.first()
            
            for user in users[1:]:
                # Transfer any important data to keeper here
                self.stdout.write(f"Deleting duplicate user {user}")
                user.delete()