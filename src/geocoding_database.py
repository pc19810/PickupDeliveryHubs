import pandas as pd
import logging
from pathlib import Path
from typing import Tuple, Optional

class CityGeocoder:
    """Geocode cities using a local database."""
    
    def __init__(self, database_path: str = 'data/reference/us_cities.csv'):
        """
        Initialize with a city database.
        
        Database should have columns: city, state_id, lat, lng
        Download from: https://simplemaps.com/data/us-cities
        """
        self.logger = logging.getLogger(__name__)
        self.database_path = Path(database_path)
        self.cities_db = None
        self.cache = {}
        
        self._load_database()
    
    def _load_database(self):
        """Load the cities database."""
        if not self.database_path.exists():
            self.logger.warning(
                f"Cities database not found at {self.database_path}. "
                "Download from https://simplemaps.com/data/us-cities"
            )
            return
        
        try:
            self.cities_db = pd.read_csv(self.database_path)
            
            # Normalize column names
            self.cities_db.columns = self.cities_db.columns.str.lower().str.strip()
            
            # Expected columns: city, state_id, lat, lng
            required_cols = ['city', 'state_id', 'lat', 'lng']
            if not all(col in self.cities_db.columns for col in required_cols):
                self.logger.error(f"Database missing required columns: {required_cols}")
                self.cities_db = None
                return
            
            # Normalize city and state for matching
            self.cities_db['city_normalized'] = self.cities_db['city'].str.lower().str.strip()
            self.cities_db['state_normalized'] = self.cities_db['state_id'].str.upper().str.strip()
            
            self.logger.info(f"Loaded {len(self.cities_db)} cities from database")
            
        except Exception as e:
            self.logger.error(f"Error loading cities database: {e}")
            self.cities_db = None
    
    def get_coordinates(self, city: str, state: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Get coordinates for a city and state.
        
        Args:
            city: City name
            state: State code (2 letters)
            
        Returns:
            Tuple of (latitude, longitude) or (None, None)
        """
        if not city or not state:
            return None, None
        
        # Check cache first
        cache_key = f"{city.lower()},{state.upper()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self.cities_db is None:
            self.logger.warning("Cities database not loaded")
            return None, None
        
        # Normalize for matching
        city_norm = city.lower().strip()
        state_norm = state.upper().strip()
        
        # Try exact match first
        match = self.cities_db[
            (self.cities_db['city_normalized'] == city_norm) &
            (self.cities_db['state_normalized'] == state_norm)
        ]
        
        if len(match) > 0:
            # If multiple matches, take the one with highest population
            if 'population' in match.columns:
                match = match.nlargest(1, 'population')
            
            lat = match.iloc[0]['lat']
            lng = match.iloc[0]['lng']
            
            coords = (float(lat), float(lng))
            self.cache[cache_key] = coords
            return coords
        
        # No match found
        self.cache[cache_key] = (None, None)
        return None, None