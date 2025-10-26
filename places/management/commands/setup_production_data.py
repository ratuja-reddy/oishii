import os
import csv
import requests
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from places.models import Restaurant


class Command(BaseCommand):
    help = 'Setup production data - safe to run multiple times'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='scripts/london_trendy_restaurants_100_with_addresses.csv',
            help='Path to the CSV file containing restaurant data'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.WARNING(f'CSV file not found: {csv_file}. Skipping data import.')
            )
            return

        # Check if we already have restaurants
        existing_count = Restaurant.objects.count()
        if existing_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Restaurants already exist ({existing_count}). Skipping import.')
            )
            return

        self.stdout.write('Setting up production restaurant data...')
        
        imported_count = 0
        geocoded_count = 0

        with transaction.atomic():
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    name = row.get('name', '').strip()
                    cuisine = row.get('cuisine', '').strip()
                    address = row.get('address', '').strip()
                    website = row.get('website', '').strip()
                    price = row.get('price', '').strip()
                    category = row.get('category', 'restaurant').strip()
                    
                    if not name or not address:
                        continue
                    
                    # Extract city from address
                    city = self.extract_city_from_address(address)
                    
                    # Geocode address
                    lat_float, lon_float = self.geocode_address(address)
                    if not lat_float:
                        self.stdout.write(
                            self.style.WARNING(f'Failed to geocode: {name} at {address}')
                        )
                        continue
                    
                    geocoded_count += 1
                    
                    # Create restaurant
                    Restaurant.objects.create(
                        name=name,
                        cuisine=cuisine,
                        lat=lat_float,
                        lng=lon_float,
                        address=address,
                        city=city,
                        website=website,
                        price=price,
                        category=category
                    )
                    imported_count += 1
                    
                    # Small delay to respect rate limits
                    time.sleep(0.1)

        self.stdout.write(
            self.style.SUCCESS(
                f'Production setup completed: {imported_count} restaurants imported, '
                f'{geocoded_count} geocoded'
            )
        )

    def extract_city_from_address(self, address):
        """Extract city from address string"""
        if not address:
            return 'London'
        
        # Common London postcodes and areas
        london_indicators = [
            'London', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12', 'E13', 'E14', 'E15', 'E16', 'E17', 'E18', 'E20',
            'W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12', 'W13', 'W14',
            'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9', 'N10', 'N11', 'N12', 'N13', 'N14', 'N15', 'N16', 'N17', 'N18', 'N19', 'N20', 'N21', 'N22',
            'S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15', 'S16', 'S17', 'S18', 'S19', 'S20', 'S21', 'S22',
            'SW1', 'SW2', 'SW3', 'SW4', 'SW5', 'SW6', 'SW7', 'SW8', 'SW9', 'SW10', 'SW11', 'SW12', 'SW13', 'SW14', 'SW15', 'SW16', 'SW17', 'SW18', 'SW19', 'SW20',
            'SE1', 'SE2', 'SE3', 'SE4', 'SE5', 'SE6', 'SE7', 'SE8', 'SE9', 'SE10', 'SE11', 'SE12', 'SE13', 'SE14', 'SE15', 'SE16', 'SE17', 'SE18', 'SE19', 'SE20', 'SE21', 'SE22', 'SE23', 'SE24', 'SE25', 'SE26', 'SE27', 'SE28',
            'NW1', 'NW2', 'NW3', 'NW4', 'NW5', 'NW6', 'NW7', 'NW8', 'NW9', 'NW10', 'NW11',
            'EC1', 'EC2', 'EC3', 'EC4', 'EC1A', 'EC1M', 'EC1N', 'EC1R', 'EC1V', 'EC1Y',
            'WC1', 'WC2', 'WC1A', 'WC1B', 'WC1E', 'WC1H', 'WC1N', 'WC1R', 'WC1V', 'WC1X', 'WC2A', 'WC2B', 'WC2E', 'WC2H', 'WC2N', 'WC2R'
        ]
        
        # Check if address contains London indicators
        address_upper = address.upper()
        for indicator in london_indicators:
            if indicator.upper() in address_upper:
                return 'London'
        
        # If no London indicators found, try to extract city from end of address
        parts = address.split(',')
        if len(parts) >= 2:
            potential_city = parts[-2].strip()
            if potential_city and len(potential_city) > 2:
                return potential_city
        
        return 'London'

    def geocode_address(self, address):
        """Geocode an address using Google Maps Geocoding API"""
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            self.stdout.write(
                self.style.ERROR('GOOGLE_MAPS_API_KEY not set. Cannot geocode addresses.')
            )
            return None, None
        
        try:
            url = f'https://maps.googleapis.com/maps/api/geocode/json'
            params = {
                'address': address,
                'key': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return location['lat'], location['lng']
            else:
                self.stdout.write(
                    self.style.WARNING(f'Geocoding failed for "{address}": {data.get("status", "Unknown error")}')
                )
                return None, None
                
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'Geocoding request failed for "{address}": {e}')
            )
            return None, None
