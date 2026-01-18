import logging
import re
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def setup_logging(log_file: Path, log_level: str = 'INFO') -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        filename=log_file,
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, log_level)
    )
    
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, log_level))
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    return logging.getLogger(__name__)

def extract_city_state(address: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract city and state from address string.
    
    Expected format: "address, city, zipcode, state" or similar variations
    
    Args:
        address: Full address string
        
    Returns:
        Tuple of (city, state) or (None, None) if extraction fails
    """
    if not address or pd.isna(address):
        return None, None
    
    try:
        # Split by comma and clean
        parts = [p.strip() for p in address.split(',')]
        
        if len(parts) < 2:
            return None, None
        
        # State is typically the last part (2-letter code)
        state = None
        city = None
        
        # Look for 2-letter state code (start from end, work backwards)
        for i in range(len(parts) - 1, -1, -1):
            part = parts[i].strip()
            # Check if it's a 2-letter state code
            if len(part) == 2 and part.isalpha():
                state = part.upper()
                # City is typically before state
                if i > 0:
                    # Check if previous part is a zipcode (5 digits or extended format like 12345-6789)
                    prev_part = parts[i-1].strip()
                    # Check for standard 5-digit zipcode or extended format (12345-6789)
                    is_zipcode = (prev_part.isdigit() and len(prev_part) == 5) or \
                                (len(prev_part) == 10 and prev_part[:5].isdigit() and 
                                 prev_part[5] == '-' and prev_part[6:].isdigit())
                    
                    if is_zipcode and i > 1:
                        # Zipcode found, city is before zipcode
                        city = parts[i-2].strip()
                    else:
                        # No zipcode or zipcode is first part, so previous part is the city
                        city = prev_part
                break
        
        return city, state
    except Exception:
        return None, None

def get_coordinates(city: str, state: str, cache: dict = {}) -> Tuple[Optional[float], Optional[float]]:
    """
    Get latitude and longitude for a city and state.
    Uses caching to minimize API calls.
    
    Args:
        city: City name
        state: State code
        cache: Dictionary to cache results
        
    Returns:
        Tuple of (latitude, longitude) or (None, None) if lookup fails
    """
    if not city or not state:
        return None, None
    
    key = f"{city},{state}"
    
    if key in cache:
        return cache[key]
    
    try:
        geolocator = Nominatim(user_agent="logistics_hub_analyzer")
        location = geolocator.geocode(f"{city}, {state}, USA", timeout=10)
        
        if location:
            coords = (location.latitude, location.longitude)
            cache[key] = coords
            return coords
    except (GeocoderTimedOut, GeocoderServiceError):
        pass
    
    cache[key] = (None, None)
    return None, None