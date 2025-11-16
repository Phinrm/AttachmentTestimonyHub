from django.core.management.base import BaseCommand
from django.utils import timezone
from hub.models import Vacancy

class Command(BaseCommand):
    help = "Deactivate expired vacancies"

    def handle(self, *args, **options):
        today = timezone.now().date()
        expired = Vacancy.objects.filter(is_active=True, deadline__lt=today)
        count = expired.update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f"Archived {count} expired vacancies."))
