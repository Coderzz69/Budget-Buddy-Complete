import uuid
from django.core.management.base import BaseCommand
from api.models import Category

class Command(BaseCommand):
    help = 'Seeds the database with universal categories used by the ML model.'

    def handle(self, *args, **options):
        universal_categories = [
            {'name': 'Food & Dining', 'icon': 'fork.knife', 'color': '#F87171'},
            {'name': 'Groceries', 'icon': 'cart.fill', 'color': '#FBBF24'},
            {'name': 'Shopping', 'icon': 'bag.fill', 'color': '#818CF8'},
            {'name': 'Travel', 'icon': 'car.fill', 'color': '#60A5FA'},
            {'name': 'Recharge & Bills', 'icon': 'bolt.fill', 'color': '#34D399'},
            {'name': 'Entertainment', 'icon': 'play.tv.fill', 'color': '#A78BFA'},
            {'name': 'Transfers', 'icon': 'arrow.up.arrow.down', 'color': '#94A3B8'},
            {'name': 'Others', 'icon': 'ellipsis.circle.fill', 'color': '#64748B'},
        ]

        count = 0
        for cat_data in universal_categories:
            # Create as global category (user=None)
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                user=None,
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color']
                }
            )
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat_data["name"]}'))
            else:
                # Update existing global category icon/color just in case
                category.icon = cat_data['icon']
                category.color = cat_data['color']
                category.save()
                self.stdout.write(f'Updated existing category: {cat_data["name"]}')

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} new universal categories.'))
