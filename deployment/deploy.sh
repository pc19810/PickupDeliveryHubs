#!/bin/bash
# Deployment script for Logistics Hub Analysis System on Ubuntu
# Run this script as root or with sudo

set -e

echo "=========================================="
echo "Logistics Hub Analysis System - Deployment"
echo "=========================================="
echo ""

# Configuration
APP_DIR="/opt/pickup-delivery-hubs"
APP_USER="www-data"
SERVICE_NAME="hub-visualizer"
PORT=8050

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Update system
echo "Step 1: Updating system packages..."
apt-get update
apt-get install -y python3 python3-pip python3-venv

# Create application directory
echo ""
echo "Step 2: Setting up application directory..."
if [ -d "$APP_DIR" ]; then
    echo "Directory $APP_DIR already exists. Backing up..."
    mv "$APP_DIR" "${APP_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Copy application to /opt
echo "Copying application files to $APP_DIR..."
cp -r "$PROJECT_ROOT" "$APP_DIR"
cd "$APP_DIR"

# Create virtual environment
echo ""
echo "Step 3: Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "Step 4: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set permissions
echo ""
echo "Step 5: Setting permissions..."
chown -R $APP_USER:$APP_USER "$APP_DIR"
chmod +x main.py

# Create necessary directories
mkdir -p data/raw data/processed data/reference logs
chown -R $APP_USER:$APP_USER data logs

# Update service file with correct paths
echo ""
echo "Step 6: Configuring systemd service..."
sed "s|/opt/pickup-delivery-hubs|$APP_DIR|g" "$APP_DIR/deployment/hub-visualizer.service" > /tmp/hub-visualizer.service
sed -i "s|User=www-data|User=$APP_USER|g" /tmp/hub-visualizer.service
sed -i "s|Group=www-data|Group=$APP_USER|g" /tmp/hub-visualizer.service

# Install service file
cp /tmp/hub-visualizer.service /etc/systemd/system/$SERVICE_NAME.service

# Process initial data if CSV files exist
echo ""
if [ "$(ls -A $APP_DIR/data/raw/*.csv 2>/dev/null)" ]; then
    echo "Step 7: Processing initial data..."
    sudo -u $APP_USER bash -c "cd $APP_DIR && source venv/bin/activate && python3 main.py --process-data --create-hubs"
else
    echo "Step 7: Skipping data processing (no CSV files found in data/raw/)"
    echo "   Place your loads report CSV files in $APP_DIR/data/raw/ and run:"
    echo "   sudo -u $APP_USER bash -c 'cd $APP_DIR && source venv/bin/activate && python3 main.py --process-data --create-hubs'"
fi

# Enable and start service
echo ""
echo "Step 8: Enabling and starting service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME.service
systemctl start $SERVICE_NAME.service

# Wait a moment for service to start
sleep 3

# Check service status
echo ""
echo "Step 9: Checking service status..."
if systemctl is-active --quiet $SERVICE_NAME.service; then
    echo "✓ Service is running successfully!"
    echo ""
    echo "Service Status:"
    systemctl status $SERVICE_NAME.service --no-pager -l
else
    echo "✗ Service failed to start. Check logs with:"
    echo "  sudo journalctl -u $SERVICE_NAME.service -n 50"
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Service Management:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME.service -f"
echo ""
echo "Application Logs:"
echo "  tail -f $APP_DIR/logs/hub_analysis.log"
echo ""
echo "Access the dashboard at:"
echo "  http://localhost:$PORT"
echo "  or http://$(hostname -I | awk '{print $1}'):$PORT"
echo ""
echo "To update data:"
echo "  1. Place new CSV files in $APP_DIR/data/raw/"
echo "  2. Run: sudo -u $APP_USER bash -c 'cd $APP_DIR && source venv/bin/activate && python3 main.py --process-data --create-hubs'"
echo "  3. Restart service: sudo systemctl restart $SERVICE_NAME"
echo ""
