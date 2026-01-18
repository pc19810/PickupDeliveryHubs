# Logistics Hub Analysis System

A comprehensive system for analyzing logistics pickup and delivery patterns, identifying optimal hub locations, and visualizing logistics networks across the United States.

## Overview

This system processes loads report data to:
1. **Extract and aggregate** city-level pickup and delivery counts from logistics data
2. **Identify optimal hubs** for pickup and delivery operations in each state
3. **Visualize the network** through an interactive web-based dashboard

The system identifies the city with the highest pickup volume and highest delivery volume in each state as hub locations, then calculates which cities fall within the specified radius of each hub.

## Features

- **Automated Data Processing**: Processes multiple CSV files with loads report data
- **Smart Address Extraction**: Handles various address formats and normalizes column names
- **Hub Identification**: Automatically identifies pickup and delivery hubs by state
- **Coverage Analysis**: Calculates which cities are within hub coverage radius
- **Interactive Visualization**: Web-based dashboard with map visualization and filtering
- **Geocoding**: Uses local city database for fast, reliable coordinate lookup

## Project Structure

```
PickupDeliveryHubs/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data/
│   ├── raw/               # Input CSV files (loads reports)
│   ├── processed/         # Processed data and hub coverage files
│   └── reference/         # Reference data (cities, states)
├── logs/                  # Application logs
├── src/
│   ├── config.py          # Configuration settings
│   ├── data_processor.py  # Data processing logic
│   ├── hub_creator.py     # Hub identification and coverage calculation
│   ├── visualization.py   # Dash web application
│   ├── geocoding_database.py  # City geocoding using local database
│   └── utils.py           # Utility functions (address extraction, logging)
└── deployment/
    ├── hub-visualizer.service  # Systemd service file
    └── deploy.sh          # Deployment script
```

## Requirements

- Python 3.8 or higher
- Ubuntu 18.04 or higher (for deployment)
- Required Python packages (see `requirements.txt`)

## Installation

### 1. Clone or Upload the Project

```bash
# If using git
git clone <repository-url>
cd PickupDeliveryHubs

# Or upload the project directory to your Ubuntu server
```

### 2. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Prepare Data Files

Place your loads report CSV files in the `data/raw/` directory. The system supports:
- Files named `loads-report-*.csv` (with hyphen)
- Files named `loads-report_*.csv` (with underscore)

**Expected CSV format:**
- Columns: `Pickup` (or `pickup`) and `Delivery` (or `delivery`) containing address strings
- Address format: `Street Address, City, ZIP Code, State` (e.g., `123 Main St, Los Angeles, 90001, CA`)

Ensure reference data files exist in `data/reference/`:
- `us_cities.csv` - City database with coordinates
- `us_states.csv` - State information with centroids

### 4. Configure the System

Edit `src/config.py` if you need to adjust:
- Hub radius (default: 50 miles)
- Server port (default: 8050)
- Logging level
- Directory paths

## Usage

### Command-Line Options

```bash
# Show help
python main.py

# Process data only
python main.py --process-data

# Create hubs only (requires processed data)
python main.py --create-hubs

# Launch visualization only (requires hub data)
python main.py --visualize

# Run complete pipeline (recommended for first run)
python main.py --all

# Customize hub radius and port
python main.py --all --radius 75 --port 8080
```

### Typical Workflow

1. **Initial Setup**: Process all data and create hubs
   ```bash
   python main.py --all
   ```

2. **Update Data**: When new loads reports are available
   ```bash
   # Place new CSV files in data/raw/
   python main.py --process-data --create-hubs
   ```

3. **Access Visualization**: The dashboard will be available at `http://localhost:8050` (or your server IP)

## How It Works

### Step 1: Data Processing (`--process-data`)

1. **File Discovery**: Scans `data/raw/` for loads report CSV files
2. **Column Normalization**: Converts all column names to lowercase for consistency
3. **Address Extraction**: Parses pickup and delivery addresses to extract:
   - City name
   - State code (2-letter abbreviation)
4. **Aggregation**: Counts pickup and delivery operations per city/state combination
5. **Geocoding**: Adds latitude/longitude coordinates using the local city database
6. **Output**: Saves `city_pickup_delivery_counts.csv` to `data/processed/`

### Step 2: Hub Creation (`--create-hubs`)

1. **Hub Identification**: For each state, identifies:
   - **Pickup Hub**: City with highest pickup count
   - **Delivery Hub**: City with highest delivery count
2. **Coverage Calculation**: For each hub, finds all cities within the specified radius (default: 50 miles)
3. **Distance Calculation**: Uses Haversine formula to calculate distances
4. **Output**: Generates two coverage files:
   - `pickup_hub_coverage.csv`
   - `delivery_hub_coverage.csv`

### Step 3: Visualization (`--visualize`)

1. **Data Loading**: Loads hub coverage data and state centroids
2. **Dashboard Creation**: Builds interactive Dash web application with:
   - Map visualization (using Plotly)
   - Hub-level and city-level views
   - Filtering by hub type (pickup/delivery)
   - Zoom-based auto-switching between views
   - Click-to-view hub details
3. **Web Server**: Launches web server on specified port (default: 8050)

## Deployment on Ubuntu

### Option 1: Manual Deployment

1. **Install Dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv -y
   ```

2. **Setup Application**:
   ```bash
   cd /path/to/PickupDeliveryHubs
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Initial Data Processing**:
   ```bash
   python3 main.py --process-data --create-hubs
   ```

4. **Run Visualization** (foreground, for testing):
   ```bash
   python3 main.py --visualize --port 8050
   ```

### Option 2: Deploy as System Service (Recommended)

This keeps the application running continuously and automatically starts on system boot.

1. **Follow Manual Deployment steps 1-3**

2. **Create Systemd Service**:
   ```bash
   sudo nano /etc/systemd/system/hub-visualizer.service
   ```

3. **Add the following content** (adjust paths as needed):
   ```ini
   [Unit]
   Description=Logistics Hub Visualization Service
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/PickupDeliveryHubs
   Environment="PATH=/path/to/PickupDeliveryHubs/venv/bin"
   ExecStart=/path/to/PickupDeliveryHubs/venv/bin/python3 /path/to/PickupDeliveryHubs/main.py --visualize --port 8050
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. **Enable and Start Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable hub-visualizer.service
   sudo systemctl start hub-visualizer.service
   ```

5. **Check Status**:
   ```bash
   sudo systemctl status hub-visualizer.service
   ```

6. **View Logs**:
   ```bash
   # Service logs
   sudo journalctl -u hub-visualizer.service -f

   # Application logs
   tail -f /path/to/PickupDeliveryHubs/logs/hub_analysis.log
   ```

### Option 3: Using Nginx as Reverse Proxy (Production)

1. **Install Nginx**:
   ```bash
   sudo apt install nginx -y
   ```

2. **Configure Nginx**:
   ```bash
   sudo nano /etc/nginx/sites-available/hub-visualizer
   ```

3. **Add configuration**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # or your-server-ip

       location / {
           proxy_pass http://127.0.0.1:8050;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **Enable and Restart**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/hub-visualizer /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Service Management

```bash
# Start service
sudo systemctl start hub-visualizer.service

# Stop service
sudo systemctl stop hub-visualizer.service

# Restart service
sudo systemctl restart hub-visualizer.service

# Check status
sudo systemctl status hub-visualizer.service

# Disable auto-start on boot
sudo systemctl disable hub-visualizer.service

# Enable auto-start on boot
sudo systemctl enable hub-visualizer.service
```

## Updating Data

When new loads report files are available:

1. **Place new CSV files** in `data/raw/`
2. **Process and update hubs**:
   ```bash
   python3 main.py --process-data --create-hubs
   ```
3. **Restart service** (if running as service):
   ```bash
   sudo systemctl restart hub-visualizer.service
   ```

The visualization will automatically reload with new data when accessed.

## Troubleshooting

### Port Already in Use

If port 8050 is already in use:
```bash
# Find process using the port
sudo lsof -i :8050
# Or
sudo netstat -tulpn | grep 8050

# Kill the process or change port in config
python3 main.py --visualize --port 8080
```

### Permission Errors

Ensure the user running the service has permissions:
```bash
sudo chown -R your-username:your-username /path/to/PickupDeliveryHubs
```

### Service Won't Start

Check logs:
```bash
sudo journalctl -u hub-visualizer.service -n 50
# And
cat /path/to/PickupDeliveryHubs/logs/hub_analysis.log
```

### Address Extraction Issues

If addresses aren't being extracted correctly:
- Check address format in CSV files
- Verify CSV has `Pickup` and `Delivery` columns (case-insensitive)
- Review logs for extraction statistics

### Geocoding Failures

If cities can't be geocoded:
- Verify `data/reference/us_cities.csv` exists and is populated
- Check city/state names match database format
- Review logs for missing cities

## Configuration

Key configuration options in `src/config.py`:

- `HUB_RADIUS_MILES`: Distance radius for hub coverage (default: 50)
- `DASH_HOST`: Server host (default: '0.0.0.0' - listen on all interfaces)
- `DASH_PORT`: Server port (default: 8050)
- `DASH_DEBUG`: Debug mode (default: True - set to False in production)
- `LOG_LEVEL`: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')

## Security Considerations

For production deployment:

1. **Set Debug Mode to False** in `src/config.py`:
   ```python
   DASH_DEBUG = False
   ```

2. **Use Firewall**:
   ```bash
   sudo ufw allow 8050/tcp
   # Or use Nginx reverse proxy and only allow 80/443
   ```

3. **Run as Non-Root User**: Always run the service as a regular user

4. **Use HTTPS**: Configure SSL/TLS certificate with Nginx or use a load balancer

## License

[Add your license information here]

## Support

For issues or questions, please review the logs in `logs/hub_analysis.log` or create an issue in the repository.
