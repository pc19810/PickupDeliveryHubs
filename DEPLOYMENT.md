# Deployment Guide - Ubuntu Server

This guide provides step-by-step instructions for deploying the Logistics Hub Analysis System on Ubuntu.

## Prerequisites

- Ubuntu 18.04 or higher
- Root or sudo access
- Internet connection

## Quick Deployment (Automated)

The easiest way to deploy is using the automated deployment script:

```bash
# Make the script executable
chmod +x deployment/deploy.sh

# Run the deployment script (as root or with sudo)
sudo ./deployment/deploy.sh
```

The script will:
1. Install required system packages
2. Create application directory at `/opt/pickup-delivery-hubs`
3. Set up Python virtual environment
4. Install Python dependencies
5. Configure and enable systemd service
6. Start the visualization server

## Manual Deployment

### Step 1: Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### Step 2: Setup Application Directory

```bash
# Create application directory
sudo mkdir -p /opt/pickup-delivery-hubs
sudo chown $USER:$USER /opt/pickup-delivery-hubs

# Copy application files
cp -r /path/to/PickupDeliveryHubs/* /opt/pickup-delivery-hubs/
cd /opt/pickup-delivery-hubs
```

### Step 3: Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Prepare Data Files

```bash
# Ensure data directories exist
mkdir -p data/raw data/processed data/reference logs

# Place your loads report CSV files in data/raw/
# Copy reference files to data/reference/
```

### Step 5: Process Initial Data

```bash
source venv/bin/activate
python3 main.py --process-data --create-hubs
```

### Step 6: Create Systemd Service

```bash
# Copy and edit the service file
sudo cp deployment/hub-visualizer.service /etc/systemd/system/

# Edit the service file with your paths
sudo nano /etc/systemd/system/hub-visualizer.service
```

Update these values in the service file:
- `User`: Change to your user (e.g., `your-username` or `www-data`)
- `Group`: Change to your group
- `WorkingDirectory`: Should be `/opt/pickup-delivery-hubs`
- `Environment="PATH"`: Should point to `/opt/pickup-delivery-hubs/venv/bin`
- `ExecStart`: Should point to your venv Python and main.py

Example service file:
```ini
[Unit]
Description=Logistics Hub Visualization Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/pickup-delivery-hubs
Environment="PATH=/opt/pickup-delivery-hubs/venv/bin"
ExecStart=/opt/pickup-delivery-hubs/venv/bin/python3 /opt/pickup-delivery-hubs/main.py --visualize --port 8050
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 7: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable hub-visualizer.service

# Start the service
sudo systemctl start hub-visualizer.service

# Check status
sudo systemctl status hub-visualizer.service
```

### Step 8: Configure Firewall (Optional)

```bash
# Allow port 8050 through firewall
sudo ufw allow 8050/tcp
sudo ufw reload
```

### Step 9: Test Access

```bash
# Check if service is running
curl http://localhost:8050

# Or open in browser
# http://your-server-ip:8050
```

## Using Nginx as Reverse Proxy (Recommended for Production)

### Step 1: Install Nginx

```bash
sudo apt install -y nginx
```

### Step 2: Configure Nginx

```bash
# Copy configuration file
sudo cp deployment/nginx-hub-visualizer.conf /etc/nginx/sites-available/hub-visualizer

# Edit configuration
sudo nano /etc/nginx/sites-available/hub-visualizer
```

Update `server_name` with your domain or IP address.

### Step 3: Enable Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/hub-visualizer /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 4: Configure Firewall

```bash
# Allow HTTP and HTTPS (if using SSL)
sudo ufw allow 'Nginx Full'
# Or just HTTP
sudo ufw allow 'Nginx HTTP'
```

Now you can access the application at `http://your-domain.com` (port 80) instead of port 8050.

## SSL/HTTPS Setup (Optional)

### Using Let's Encrypt (Free SSL)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Certbot will automatically configure Nginx for HTTPS
```

After SSL setup, the application will be accessible at `https://your-domain.com`.

## Service Management

### Start Service
```bash
sudo systemctl start hub-visualizer.service
```

### Stop Service
```bash
sudo systemctl stop hub-visualizer.service
```

### Restart Service
```bash
sudo systemctl restart hub-visualizer.service
```

### Check Status
```bash
sudo systemctl status hub-visualizer.service
```

### View Logs
```bash
# Service logs
sudo journalctl -u hub-visualizer.service -f

# Application logs
tail -f /opt/pickup-delivery-hubs/logs/hub_analysis.log
```

### Enable/Disable Auto-start
```bash
# Enable auto-start on boot
sudo systemctl enable hub-visualizer.service

# Disable auto-start on boot
sudo systemctl disable hub-visualizer.service
```

## Updating the Application

### 1. Stop the Service
```bash
sudo systemctl stop hub-visualizer.service
```

### 2. Update Code
```bash
cd /opt/pickup-delivery-hubs
source venv/bin/activate

# Update code (git pull, or copy new files)
# Update dependencies if needed
pip install -r requirements.txt --upgrade
```

### 3. Update Data (if new CSV files)
```bash
# Place new CSV files in data/raw/
python3 main.py --process-data --create-hubs
```

### 4. Restart Service
```bash
sudo systemctl start hub-visualizer.service
```

## Troubleshooting

### Service Won't Start

1. Check service status:
```bash
sudo systemctl status hub-visualizer.service
```

2. Check logs:
```bash
sudo journalctl -u hub-visualizer.service -n 50
```

3. Check application logs:
```bash
cat /opt/pickup-delivery-hubs/logs/hub_analysis.log
```

4. Verify paths in service file:
```bash
sudo nano /etc/systemd/system/hub-visualizer.service
```

### Port Already in Use

```bash
# Find process using port 8050
sudo lsof -i :8050
# Or
sudo netstat -tulpn | grep 8050

# Kill process or change port in config
sudo nano /opt/pickup-delivery-hubs/src/config.py
# Change DASH_PORT = 8050 to another port
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/pickup-delivery-hubs

# Fix permissions
sudo chmod -R 755 /opt/pickup-delivery-hubs
```

### Nginx 502 Bad Gateway

1. Check if service is running:
```bash
sudo systemctl status hub-visualizer.service
```

2. Check Nginx error logs:
```bash
sudo tail -f /var/log/nginx/hub-visualizer-error.log
```

3. Verify proxy settings in Nginx config match service port

## Performance Optimization

### For Production

1. **Disable Debug Mode**: Edit `src/config.py`:
```python
DASH_DEBUG = False
```

2. **Use Production WSGI Server** (Optional): Consider using Gunicorn with Dash
```bash
pip install gunicorn
```

3. **Configure Log Rotation**: Edit `/etc/logrotate.d/hub-visualizer`:
```
/opt/pickup-delivery-hubs/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## Security Considerations

1. **Run as Non-Root User**: Service should run as a regular user (not root)
2. **Use Firewall**: Only open necessary ports
3. **Use HTTPS**: Configure SSL/TLS for production
4. **Regular Updates**: Keep system and dependencies updated
5. **Backup Data**: Regularly backup processed data and configuration

## Monitoring

### Check Service Health

```bash
# Check if service is running
systemctl is-active hub-visualizer.service

# Check service uptime
systemctl show hub-visualizer.service --property=ActiveEnterTimestamp

# Monitor logs in real-time
sudo journalctl -u hub-visualizer.service -f
```

### Resource Usage

```bash
# Check CPU and memory usage
top -p $(pgrep -f "hub-visualizer")
# Or
htop -p $(pgrep -f "hub-visualizer")
```

## Backup and Recovery

### Backup Important Data

```bash
# Create backup directory
mkdir -p /backup/hub-visualizer

# Backup processed data
tar -czf /backup/hub-visualizer/data-$(date +%Y%m%d).tar.gz \
    /opt/pickup-delivery-hubs/data/processed/

# Backup configuration
tar -czf /backup/hub-visualizer/config-$(date +%Y%m%d).tar.gz \
    /opt/pickup-delivery-hubs/src/config.py \
    /etc/systemd/system/hub-visualizer.service
```

### Restore from Backup

```bash
# Stop service
sudo systemctl stop hub-visualizer.service

# Restore data
tar -xzf /backup/hub-visualizer/data-YYYYMMDD.tar.gz -C /

# Restart service
sudo systemctl start hub-visualizer.service
```

## Support

For issues or questions:
1. Check logs: `/opt/pickup-delivery-hubs/logs/hub_analysis.log`
2. Check service logs: `sudo journalctl -u hub-visualizer.service`
3. Review README.md for application documentation
