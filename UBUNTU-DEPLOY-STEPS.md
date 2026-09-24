# Ubuntu Deployment - Step by Step Guide

Follow these steps to deploy the Logistics Hub Analysis System on your Ubuntu server.

## Prerequisites Check

Before starting, make sure you're on your Ubuntu server and have:
- SSH access or direct terminal access
- Sudo/root privileges
- The repository cloned to a location (e.g., `~/PickupDeliveryHubs` or `/home/username/PickupDeliveryHubs`)

## Option 1: Automated Deployment (Recommended)

This is the fastest and easiest way to deploy.

### Step 1: Navigate to the Project Directory

```bash
cd ~/PickupDeliveryHubs
# Or wherever you cloned the repository
```

### Step 2: Make the Deployment Script Executable

```bash
chmod +x deployment/deploy.sh
```

### Step 3: Run the Deployment Script

```bash
sudo ./deployment/deploy.sh
```

The script will:
- Install required system packages (Python, pip, venv)
- Copy the application to `/opt/pickup-delivery-hubs`
- Create a Python virtual environment
- Install all Python dependencies
- Set up the systemd service
- Process initial data (if CSV files exist)
- Start the service automatically

### Step 4: Verify Deployment

```bash
# Check service status
sudo systemctl status hub-visualizer.service

# Check if it's accessible
curl http://localhost:8050
```

### Step 5: Access the Application

Open your web browser and go to:
- `http://your-server-ip:8050`
- Or `http://your-domain:8050`

That's it! Your application should be running.

---

## Option 2: Manual Deployment

If you prefer manual control or the automated script doesn't work for your setup.

### Step 1: Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### Step 2: Navigate to Project Directory

```bash
cd ~/PickupDeliveryHubs
# Or wherever you cloned the repository
```

### Step 3: Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Ensure Data Files Are Ready

```bash
# Check if you have CSV files in data/raw/
ls -la data/raw/

# If no CSV files, you can add them later
mkdir -p data/raw data/processed data/reference logs
```

**Important:** Place your loads report CSV files in `data/raw/` directory before processing.

### Step 5: Process Initial Data (Optional)

If you have CSV files ready:

```bash
source venv/bin/activate  # If not already activated
python3 main.py --process-data --create-hubs
```

If you don't have CSV files yet, you can do this step later.

### Step 6: Set Up Systemd Service

Create the service file:

```bash
sudo nano /etc/systemd/system/hub-visualizer.service
```

Copy and paste this content (adjust paths if needed):

```ini
[Unit]
Description=Logistics Hub Visualization Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/home/YOUR_USERNAME/PickupDeliveryHubs
Environment="PATH=/home/YOUR_USERNAME/PickupDeliveryHubs/venv/bin"
ExecStart=/home/YOUR_USERNAME/PickupDeliveryHubs/venv/bin/python3 /home/YOUR_USERNAME/PickupDeliveryHubs/main.py --visualize --port 8050
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Important:** Replace `YOUR_USERNAME` with your actual username (or use `/opt/pickup-delivery-hubs` if you prefer).

Save and exit (Ctrl+X, then Y, then Enter).

### Step 7: Enable and Start the Service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable hub-visualizer.service

# Start the service
sudo systemctl start hub-visualizer.service

# Check status
sudo systemctl status hub-visualizer.service
```

### Step 8: Configure Firewall (If Needed)

If you have a firewall enabled:

```bash
# Allow port 8050
sudo ufw allow 8050/tcp
sudo ufw reload
```

### Step 9: Verify Everything Works

```bash
# Check service is running
sudo systemctl status hub-visualizer.service

# Test locally
curl http://localhost:8050

# Check logs
sudo journalctl -u hub-visualizer.service -f
```

---

## Common Issues and Solutions

### Issue: "Permission denied" when running deploy.sh

**Solution:**
```bash
chmod +x deployment/deploy.sh
sudo ./deployment/deploy.sh
```

### Issue: Service fails to start

**Check logs:**
```bash
sudo journalctl -u hub-visualizer.service -n 50
```

**Common causes:**
- Wrong paths in service file - check WorkingDirectory and ExecStart paths
- Python virtual environment not activated - ensure venv exists and is accessible
- Missing data files - check if data/processed/ has required files

### Issue: Port 8050 already in use

**Solution:**
```bash
# Find what's using the port
sudo lsof -i :8050

# Kill the process or change port in src/config.py
# Then update service file with new port
```

### Issue: Can't access from network

**Solutions:**
1. Check firewall:
   ```bash
   sudo ufw status
   sudo ufw allow 8050/tcp
   ```

2. Check if service is listening on all interfaces (0.0.0.0):
   - Check `src/config.py` has `DASH_HOST = '0.0.0.0'`

3. Check server firewall/security groups if using cloud provider (AWS, Azure, etc.)

### Issue: No data showing in visualization

**Solution:**
You need to process the data first:
```bash
cd ~/PickupDeliveryHubs  # or your project directory
source venv/bin/activate
python3 main.py --process-data --create-hubs
sudo systemctl restart hub-visualizer.service
```

---

## Post-Deployment Tasks

### 1. Add Your Data Files

Place your loads report CSV files in:
- `data/raw/` (if using automated deployment: `/opt/pickup-delivery-hubs/data/raw/`)

Then process them:
```bash
cd ~/PickupDeliveryHubs  # or /opt/pickup-delivery-hubs
source venv/bin/activate
python3 main.py --process-data --create-hubs
sudo systemctl restart hub-visualizer.service
```

### 2. Set Up Nginx Reverse Proxy (Optional but Recommended)

For production, it's better to use Nginx as a reverse proxy:

```bash
# Install Nginx
sudo apt install -y nginx

# Copy configuration
sudo cp deployment/nginx-hub-visualizer.conf /etc/nginx/sites-available/hub-visualizer

# Edit configuration
sudo nano /etc/nginx/sites-available/hub-visualizer
# Update server_name with your domain/IP

# Enable site
sudo ln -s /etc/nginx/sites-available/hub-visualizer /etc/nginx/sites-enabled/

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Set Up SSL (Optional)

For HTTPS:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Service Management Commands

```bash
# Start service
sudo systemctl start hub-visualizer.service

# Stop service
sudo systemctl stop hub-visualizer.service

# Restart service
sudo systemctl restart hub-visualizer.service

# Check status
sudo systemctl status hub-visualizer.service

# View logs (real-time)
sudo journalctl -u hub-visualizer.service -f

# View application logs
tail -f ~/PickupDeliveryHubs/logs/hub_analysis.log
# or
tail -f /opt/pickup-delivery-hubs/logs/hub_analysis.log
```

---

## Updating the Application

When you pull new changes or need to update:

```bash
# Stop service
sudo systemctl stop hub-visualizer.service

# Navigate to project
cd ~/PickupDeliveryHubs  # or /opt/pickup-delivery-hubs

# Pull latest changes (if using git)
git pull

# Update dependencies if requirements.txt changed
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl start hub-visualizer.service
```

---

## Verification Checklist

After deployment, verify:

- [ ] Service is running: `sudo systemctl status hub-visualizer.service`
- [ ] Can access locally: `curl http://localhost:8050`
- [ ] Can access from network: `http://your-server-ip:8050`
- [ ] Logs show no errors: `sudo journalctl -u hub-visualizer.service`
- [ ] Data files are processed (if you had CSV files)
- [ ] Firewall allows port 8050 (if firewall is enabled)

---

## Getting Help

If you encounter issues:

1. Check service logs: `sudo journalctl -u hub-visualizer.service -n 50`
2. Check application logs: `tail -f ~/PickupDeliveryHubs/logs/hub_analysis.log`
3. Verify all paths in service file are correct
4. Ensure Python virtual environment exists and has all dependencies
5. Review the full documentation in `README.md` and `DEPLOYMENT.md`

---

## Quick Reference

**Access Application:**
- `http://your-server-ip:8050`

**Service Management:**
- Status: `sudo systemctl status hub-visualizer`
- Restart: `sudo systemctl restart hub-visualizer`
- Logs: `sudo journalctl -u hub-visualizer.service -f`

**Update Data:**
```bash
cd ~/PickupDeliveryHubs
source venv/bin/activate
python3 main.py --process-data --create-hubs
sudo systemctl restart hub-visualizer
```
