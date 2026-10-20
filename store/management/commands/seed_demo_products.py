from django.core.management import BaseCommand, call_command
from django.db import transaction

from store.models import Product


class Command(BaseCommand):
    help = 'Load the demo catalogue when no products exist.'

    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write('Product catalogue already has products; skipping demo data.')
            return

        with transaction.atomic():
            call_command('loaddata', 'figma_products', 'demo_category_products', verbosity=0)

        self.stdout.write(
            self.style.SUCCESS(f'Loaded {Product.objects.count()} demo products.')
        )
