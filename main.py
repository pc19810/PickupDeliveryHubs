"""
Logistics Hub Analysis System - Main Entry Point

This script orchestrates the complete logistics hub analysis pipeline:
1. Process loads report files to aggregate city-level data
2. Create logistics hubs based on pickup/delivery patterns
3. Launch interactive visualization dashboard
"""

import sys
import argparse
from pathlib import Path

# Add project root to path for proper imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.utils import setup_logging
from src.data_processor import DataProcessor
from src.hub_creator import HubCreator
from src.visualization import HubVisualizer

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Logistics Hub Analysis System',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--process-data',
        action='store_true',
        help='Process loads report files and update city counts'
    )
    
    parser.add_argument(
        '--create-hubs',
        action='store_true',
        help='Create hubs based on city data'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Launch visualization dashboard'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run complete pipeline (process, create hubs, visualize)'
    )
    
    parser.add_argument(
        '--radius',
        type=float,
        default=50,
        help='Hub radius in miles (default: 50)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8050,
        help='Port for visualization server (default: 8050)'
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any([args.process_data, args.create_hubs, args.visualize, args.all]):
        parser.print_help()
        return
    
    # Setup
    Config.setup_directories()
    Config.HUB_RADIUS_MILES = args.radius
    Config.DASH_PORT = args.port
    
    logger = setup_logging(Config.LOGS_DIR / Config.LOG_FILE, Config.LOG_LEVEL)
    logger.info("=" * 70)
    logger.info("LOGISTICS HUB ANALYSIS SYSTEM")
    logger.info("=" * 70)
    
    try:
        # Process data
        if args.process_data or args.all:
            logger.info("\n>>> STEP 1: Processing loads report data")
            processor = DataProcessor(Config)
            processor.process_all()
        
        # Create hubs
        if args.create_hubs or args.all:
            logger.info("\n>>> STEP 2: Creating logistics hubs")
            hub_creator = HubCreator(Config)
            hub_creator.create_hubs()
        
        # Visualize
        if args.visualize or args.all:
            logger.info("\n>>> STEP 3: Launching visualization")
            visualizer = HubVisualizer(Config)
            visualizer.load_data()
            visualizer.prepare_summary_data()
            visualizer.create_app()
            visualizer.run()
        
        logger.info("\n" + "=" * 70)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"\n!!! ERROR: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()