from django.core.management.base import BaseCommand
from social.models import Notification


class Command(BaseCommand):
    help = 'Clean up self-notifications (notifications for liking your own content)'

    def handle(self, *args, **options):
        # Find and delete self-notifications
        self_notifications = []
        
        # Check review like notifications
        for notification in Notification.objects.filter(notification_type='review_like'):
            if notification.like and notification.like.user == notification.user:
                self_notifications.append(notification)
        
        # Check comment like notifications
        for notification in Notification.objects.filter(notification_type='comment_like'):
            if notification.comment_like and notification.comment_like.user == notification.user:
                self_notifications.append(notification)
        
        deleted_count = len(self_notifications)
        
        if deleted_count > 0:
            self.stdout.write(f"Found {deleted_count} self-notifications to delete:")
            for notification in self_notifications:
                self.stdout.write(f"  - {notification}")
            
            # Delete them
            for notification in self_notifications:
                notification.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} self-notifications')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No self-notifications found')
            )
