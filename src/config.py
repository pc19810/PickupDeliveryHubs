import os
from pathlib import Path

class Config:
    """Configuration settings for the logistics hub analysis system."""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / 'data'
    RAW_DATA_DIR = DATA_DIR / 'raw'
    PROCESSED_DATA_DIR = DATA_DIR / 'processed'
    REFERENCE_DATA_DIR = DATA_DIR / 'reference'
    LOGS_DIR = PROJECT_ROOT / 'logs'
    
    # File patterns and names
    LOADS_REPORT_PATTERN = 'loads-report-*.csv'
    CITY_COUNTS_FILE = 'city_pickup_delivery_counts.csv'
    PICKUP_HUB_COVERAGE_FILE = 'pickup_hub_coverage.csv'
    DELIVERY_HUB_COVERAGE_FILE = 'delivery_hub_coverage.csv'
    US_STATES_FILE = 'us_states.csv'
    
    # Hub creation parameters
    HUB_RADIUS_MILES = 50
    
    # Dash app parameters
    DASH_HOST = '0.0.0.0'
    DASH_PORT = 8050
    DASH_DEBUG = True  # Set to False in production for better performance
    
    # Logging
    LOG_FILE = 'hub_analysis.log'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories if they don't exist."""
        for directory in [cls.RAW_DATA_DIR, cls.PROCESSED_DATA_DIR, 
                         cls.REFERENCE_DATA_DIR, cls.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
