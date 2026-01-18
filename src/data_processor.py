import pandas as pd
import logging
from pathlib import Path
from typing import List
from collections import defaultdict
from .config import Config
from .utils import extract_city_state, get_coordinates

class DataProcessor:
    """Process loads report files and aggregate city-level pickup/delivery counts."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.coord_cache = {}
    
    def find_loads_files(self) -> List[Path]:
        """Find all loads-report CSV files in the raw data directory."""
        # Search for both underscore and hyphen variants
        files_hyphen = list(self.config.RAW_DATA_DIR.glob('loads-report-*.csv'))
        files_underscore = list(self.config.RAW_DATA_DIR.glob('loads-report_*.csv'))
        
        # Combine and deduplicate (in case a file matches both patterns)
        all_files = list(set(files_hyphen + files_underscore))
        
        self.logger.info(f"Found {len(all_files)} loads report files")
        return all_files
    
    def read_loads_files(self, files: List[Path]) -> pd.DataFrame:
        """Read and combine all loads report files."""
        dfs = []
        
        for file in files:
            try:
                df = pd.read_csv(file)
                # Normalize column names to lowercase (handle both 'Pickup' and 'pickup')
                df.columns = df.columns.str.lower().str.strip()
                dfs.append(df)
                self.logger.info(f"Loaded {len(df)} records from {file.name}")
            except Exception as e:
                self.logger.error(f"Error reading {file.name}: {e}")
        
        if not dfs:
            raise ValueError("No valid loads report files found")
        
        combined_df = pd.concat(dfs, ignore_index=True)
        self.logger.info(f"Combined total: {len(combined_df)} records")
        
        return combined_df
    
    def process_addresses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract city and state from pickup and delivery addresses."""
        self.logger.info("Extracting cities and states from addresses...")
        
        # Extract pickup city and state
        df[['pickup_city', 'pickup_state']] = df['pickup'].apply(
            lambda x: pd.Series(extract_city_state(x))
        )
        
        # Extract delivery city and state
        df[['delivery_city', 'delivery_state']] = df['delivery'].apply(
            lambda x: pd.Series(extract_city_state(x))
        )
        
        # Log extraction statistics
        pickup_success = df['pickup_city'].notna().sum()
        delivery_success = df['delivery_city'].notna().sum()
        
        self.logger.info(f"Successfully extracted {pickup_success}/{len(df)} pickup locations")
        self.logger.info(f"Successfully extracted {delivery_success}/{len(df)} delivery locations")
        
        return df
    
    def aggregate_city_counts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate pickup and delivery counts by city and state."""
        self.logger.info("Aggregating city-level counts...")
        
        # Count pickups by city/state
        pickup_counts = df[df['pickup_city'].notna()].groupby(
            ['pickup_city', 'pickup_state']
        ).size().reset_index(name='pickup_count')
        pickup_counts.columns = ['city', 'state', 'pickup_count']
        
        # Count deliveries by city/state
        delivery_counts = df[df['delivery_city'].notna()].groupby(
            ['delivery_city', 'delivery_state']
        ).size().reset_index(name='delivery_count')
        delivery_counts.columns = ['city', 'state', 'delivery_count']
        
        # Merge pickup and delivery counts
        city_counts = pd.merge(
            pickup_counts, 
            delivery_counts, 
            on=['city', 'state'], 
            how='outer'
        ).fillna(0)
        
        # Convert counts to integers
        city_counts['pickup_count'] = city_counts['pickup_count'].astype(int)
        city_counts['delivery_count'] = city_counts['delivery_count'].astype(int)
        
        self.logger.info(f"Aggregated data for {len(city_counts)} unique cities")
        
        return city_counts
    
    def add_coordinates(self, city_counts: pd.DataFrame) -> pd.DataFrame:
        """Add latitude and longitude coordinates using local database."""
        self.logger.info("Adding coordinates to cities using database...")
        
        # Import the database geocoder
        from .geocoding_database import CityGeocoder
        
        # Initialize geocoder with database
        geocoder = CityGeocoder('data/reference/us_cities.csv')
        
        # Get coordinates for each city
        coords = city_counts.apply(
            lambda row: pd.Series(geocoder.get_coordinates(row['city'], row['state'])),
            axis=1
        )
        
        city_counts['latitude'] = coords[0]
        city_counts['longitude'] = coords[1]
        
        # Count successful coordinate lookups
        valid_coords = city_counts[['latitude', 'longitude']].notna().all(axis=1).sum()
        self.logger.info(f"Successfully geocoded {valid_coords}/{len(city_counts)} cities")
        
        # Log cities that couldn't be geocoded
        missing = city_counts[city_counts['latitude'].isna()]
        if len(missing) > 0:
            self.logger.warning(f"Could not geocode {len(missing)} cities:")
            for _, row in missing.iterrows():
                self.logger.warning(f"  - {row['city']}, {row['state']}")
        
        # Drop rows without coordinates
        city_counts = city_counts.dropna(subset=['latitude', 'longitude'])
        
        return city_counts
    
    def save_city_counts(self, city_counts: pd.DataFrame):
        """Save aggregated city counts to CSV."""
        output_file = self.config.PROCESSED_DATA_DIR / self.config.CITY_COUNTS_FILE
        city_counts.to_csv(output_file, index=False)
        self.logger.info(f"Saved city counts to {output_file}")
    
    def process_all(self) -> pd.DataFrame:
        """Execute the complete data processing pipeline."""
        self.logger.info("Starting data processing pipeline...")
        
        # Find and read all loads files
        files = self.find_loads_files()
        if not files:
            raise ValueError(f"No files matching '{self.config.LOADS_REPORT_PATTERN}' found in {self.config.RAW_DATA_DIR}")
        
        df = self.read_loads_files(files)
        
        # Process addresses
        df = self.process_addresses(df)
        
        # Aggregate counts
        city_counts = self.aggregate_city_counts(df)
        
        # Add coordinates
        city_counts = self.add_coordinates(city_counts)
        
        # Save results
        self.save_city_counts(city_counts)
        
        self.logger.info("Data processing pipeline completed successfully")
        
        return city_counts