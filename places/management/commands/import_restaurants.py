import csv
import os
import requests
import time
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
        parser.add_argument(
            '--geocode',
            action='store_true',
            help='Geocode addresses to get coordinates'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip restaurants that already exist (default behavior)'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        update_existing = options['update']
        geocode_addresses = options['geocode']
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return

        imported_count = 0
        updated_count = 0
        skipped_count = 0
        geocoded_count = 0

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                name = row.get('name', '').strip()
                cuisine = row.get('cuisine', '').strip()
                lat = row.get('lat', '').strip()
                lon = row.get('lon', '').strip()
                address = row.get('address', '').strip()
                website = row.get('website', '').strip()
                price = row.get('price', '').strip()
                category = row.get('category', 'restaurant').strip()
                
                if not name:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping row with empty name: {row}')
                    )
                    skipped_count += 1
                    continue
                
                # Skip restaurants without addresses if geocoding is requested
                if geocode_addresses and not address:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping {name} - no address provided for geocoding')
                    )
                    skipped_count += 1
                    continue
                
                # Convert coordinates to float
                lat_float = None
                lon_float = None
                if lat and lon:
                    try:
                        lat_float = float(lat)
                        lon_float = float(lon)
                    except ValueError:
                        self.stdout.write(
                            self.style.WARNING(f'Invalid coordinates for {name}: lat={lat}, lon={lon}')
                        )
                
                # Extract city from address
                city = self.extract_city_from_address(address) if address else 'London'
                
                # Geocode address if requested and no coordinates
                if geocode_addresses and not lat_float and address:
                    lat_float, lon_float = self.geocode_address(address)
                    if lat_float:
                        geocoded_count += 1
                        self.stdout.write(f'Geocoded: {name} -> {lat_float}, {lon_float}')
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Failed to geocode: {name} at {address}')
                        )
                
                # Check if restaurant already exists
                existing_restaurant = Restaurant.objects.filter(name=name).first()
                
                if existing_restaurant:
                    if update_existing:
                        existing_restaurant.cuisine = cuisine
                        existing_restaurant.lat = lat_float
                        existing_restaurant.lng = lon_float
                        existing_restaurant.address = address
                        existing_restaurant.city = city
                        existing_restaurant.website = website
                        existing_restaurant.price = price
                        existing_restaurant.category = category
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
                        address=address,
                        city=city,
                        website=website,
                        price=price,
                        category=category
                    )
                    imported_count += 1
                    self.stdout.write(f'Imported: {name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed: {imported_count} imported, '
                f'{updated_count} updated, {skipped_count} skipped, '
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
        # Look for patterns like "City Name" or "City Name, Country"
        parts = address.split(',')
        if len(parts) >= 2:
            # Take the second-to-last part as potential city
            potential_city = parts[-2].strip()
            if potential_city and len(potential_city) > 2:
                return potential_city
        
        # Default to London if we can't determine
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
                # Small delay to respect rate limits
                time.sleep(0.1)
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
