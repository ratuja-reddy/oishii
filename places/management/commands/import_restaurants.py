import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from places.models import Restaurant


class Command(BaseCommand):
    help = 'Import restaurants from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing restaurant data'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing restaurants instead of skipping them'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        update_existing = options['update']
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return

        imported_count = 0
        updated_count = 0
        skipped_count = 0

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                name = row.get('name', '').strip()
                cuisine = row.get('cuisine', '').strip()
                lat = row.get('lat', '').strip()
                lon = row.get('lon', '').strip()
                
                if not name:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping row with empty name: {row}')
                    )
                    skipped_count += 1
                    continue
                
                # Convert coordinates to float
                try:
                    lat_float = float(lat) if lat else None
                    lon_float = float(lon) if lon else None
                except ValueError:
                    self.stdout.write(
                        self.style.WARNING(f'Invalid coordinates for {name}: lat={lat}, lon={lon}')
                    )
                    lat_float = None
                    lon_float = None
                
                # Check if restaurant already exists
                existing_restaurant = Restaurant.objects.filter(name=name).first()
                
                if existing_restaurant:
                    if update_existing:
                        existing_restaurant.cuisine = cuisine
                        existing_restaurant.lat = lat_float
                        existing_restaurant.lng = lon_float
                        existing_restaurant.save()
                        updated_count += 1
                        self.stdout.write(f'Updated: {name}')
                    else:
                        skipped_count += 1
                        self.stdout.write(f'Skipped existing: {name}')
                else:
                    Restaurant.objects.create(
                        name=name,
                        cuisine=cuisine,
                        lat=lat_float,
                        lng=lon_float,
                        category='restaurant'  # Default category
                    )
                    imported_count += 1
                    self.stdout.write(f'Imported: {name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed: {imported_count} imported, '
                f'{updated_count} updated, {skipped_count} skipped'
            )
        )
