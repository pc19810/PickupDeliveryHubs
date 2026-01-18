# Quick Start Guide - Ubuntu Deployment

## Fastest Deployment Method

```bash
# 1. Upload project to Ubuntu server
# 2. Make deployment script executable
chmod +x deployment/deploy.sh

# 3. Run deployment script
sudo ./deployment/deploy.sh
```

That's it! The service will be running at `http://your-server-ip:8050`

## Manual Quick Setup

```bash
# 1. Install dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-venv

# 2. Setup project
cd /path/to/PickupDeliveryHubs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Process data
python3 main.py --all

# 4. Create systemd service
sudo nano /etc/systemd/system/hub-visualizer.service
# (Copy content from deployment/hub-visualizer.service and update paths)

# 5. Start service
sudo systemctl daemon-reload
sudo systemctl enable hub-visualizer.service
sudo systemctl start hub-visualizer.service

# 6. Check status
sudo systemctl status hub-visualizer.service
```

## Essential Commands

```bash
# Start service
sudo systemctl start hub-visualizer.service

# Stop service
sudo systemctl stop hub-visualizer.service

# Restart service
sudo systemctl restart hub-visualizer.service

# View logs
sudo journalctl -u hub-visualizer.service -f

# Update data
cd /opt/pickup-delivery-hubs
source venv/bin/activate
python3 main.py --process-data --create-hubs
sudo systemctl restart hub-visualizer.service
```

## Access Application

- Local: http://localhost:8050
- Network: http://your-server-ip:8050
- With Nginx: http://your-domain.com

For detailed instructions, see [DEPLOYMENT.md](../DEPLOYMENT.md) or [README.md](../README.md).
