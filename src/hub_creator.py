import pandas as pd
import logging
from pathlib import Path
from collections import defaultdict
from haversine import haversine, Unit
from .config import Config

class HubCreator:
    """Create logistics hubs based on city pickup/delivery patterns."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def load_city_data(self) -> pd.DataFrame:
        """Load processed city pickup/delivery counts."""
        file_path = self.config.PROCESSED_DATA_DIR / self.config.CITY_COUNTS_FILE
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"City counts file not found: {file_path}. "
                "Run data processing first."
            )
        
        df = pd.read_csv(file_path)
        df.dropna(subset=['city', 'state', 'latitude', 'longitude'], inplace=True)
        
        self.logger.info(f"Loaded {len(df)} cities with valid coordinates")
        
        return df
    
    def identify_hubs(self, df: pd.DataFrame) -> tuple:
        """Identify pickup and delivery hubs for each state."""
        pickup_hubs = {}
        delivery_hubs = {}
        
        for state, group in df.groupby('state'):
            # Find city with maximum pickups
            pickup_hub = group.loc[group['pickup_count'].idxmax()]
            
            # Find city with maximum deliveries
            delivery_hub = group.loc[group['delivery_count'].idxmax()]
            
            pickup_hubs[state] = {
                'city': pickup_hub['city'],
                'lat': pickup_hub['latitude'],
                'lng': pickup_hub['longitude']
            }
            
            delivery_hubs[state] = {
                'city': delivery_hub['city'],
                'lat': delivery_hub['latitude'],
                'lng': delivery_hub['longitude']
            }
            
            self.logger.info(
                f"State {state}: Pickup Hub = {pickup_hub['city']}, "
                f"Delivery Hub = {delivery_hub['city']}"
            )
        
        return pickup_hubs, delivery_hubs
    
    def find_nearby_cities(
        self, 
        center_lat: float, 
        center_lng: float, 
        all_cities: pd.DataFrame, 
        hub_state: str, 
        count_type: str = 'pickup'
    ) -> list:
        """Find cities within radius of a hub."""
        nearby = []
        center_point = (center_lat, center_lng)
        
        # Filter to same state
        same_state_cities = all_cities[all_cities['state'] == hub_state]
        
        for _, row in same_state_cities.iterrows():
            point = (row['latitude'], row['longitude'])
            distance = haversine(center_point, point, unit=Unit.MILES)
            
            if distance <= self.config.HUB_RADIUS_MILES:
                city_data = {
                    'city': row['city'],
                    'state': row['state'],
                    'latitude': row['latitude'],
                    'longitude': row['longitude'],
                    'distance_miles': round(distance, 2)
                }
                
                if count_type == 'pickup':
                    city_data['pickup_count'] = row['pickup_count']
                elif count_type == 'delivery':
                    city_data['delivery_count'] = row['delivery_count']
                
                nearby.append(city_data)
        
        return nearby
    
    def build_hub_coverage(
        self, 
        hubs: dict, 
        df: pd.DataFrame, 
        count_type: str
    ) -> dict:
        """Build coverage regions for all hubs."""
        hub_regions = defaultdict(list)
        
        for state, hub in hubs.items():
            cities_near = self.find_nearby_cities(
                hub['lat'], 
                hub['lng'], 
                df, 
                state, 
                count_type
            )
            
            hub_regions[state] = cities_near
            
            self.logger.info(
                f"{count_type.capitalize()} Hub for {state} ({hub['city']}): "
                f"{len(cities_near)} cities within {self.config.HUB_RADIUS_MILES} miles"
            )
        
        return hub_regions
    
    def save_hub_coverage(
        self, 
        hub_regions: dict, 
        hubs: dict, 
        filename: str
    ):
        """Save hub coverage data to CSV."""
        records = []
        
        for state, cities in hub_regions.items():
            hub_city = hubs[state]['city']
            for city in cities:
                records.append({
                    'hub_state': state,
                    'hub_city': hub_city,
                    **city
                })
        
        df = pd.DataFrame(records)
        output_file = self.config.PROCESSED_DATA_DIR / filename
        df.to_csv(output_file, index=False)
        
        self.logger.info(f"Saved hub coverage to {output_file}")
    
    def create_hubs(self):
        """Execute the complete hub creation pipeline."""
        self.logger.info("Starting hub creation pipeline...")
        
        # Load city data
        df = self.load_city_data()
        
        # Identify hubs
        pickup_hubs, delivery_hubs = self.identify_hubs(df)
        
        # Build pickup hub coverage
        pickup_regions = self.build_hub_coverage(pickup_hubs, df, 'pickup')
        self.save_hub_coverage(
            pickup_regions, 
            pickup_hubs, 
            self.config.PICKUP_HUB_COVERAGE_FILE
        )
        
        # Build delivery hub coverage
        delivery_regions = self.build_hub_coverage(delivery_hubs, df, 'delivery')
        self.save_hub_coverage(
            delivery_regions, 
            delivery_hubs, 
            self.config.DELIVERY_HUB_COVERAGE_FILE
        )
        
        self.logger.info("Hub creation pipeline completed successfully")
