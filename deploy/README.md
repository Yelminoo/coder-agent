# Deploy Directory

This directory contains everything needed to deploy the AI Coding Assistant to production servers.

## Files

### Service Configuration
- **ai-assistant.service** - Systemd service file for running the app as a system service
- **nginx.conf** - Nginx reverse proxy configuration

### Deployment Scripts
- **deploy.sh** - Automated deployment script (one-command setup)

## Quick Deploy

```bash
# 1. Upload your code to server
scp -r ai-coding-assistant user@YOUR_SERVER:~/

# 2. SSH into server
ssh user@YOUR_SERVER

# 3. Run deployment script
cd ~/ai-coding-assistant
bash deploy/deploy.sh
```

## What the Deployment Does

1. ✅ Updates system packages
2. ✅ Installs Python, Nginx, Ollama
3. ✅ Sets up virtual environment
4. ✅ Installs dependencies
5. ✅ Downloads Ollama model
6. ✅ Creates systemd service
7. ✅ Configures Nginx
8. ✅ Opens firewall ports
9. ✅ Starts application

## Manual Deployment

If you prefer manual control:

```bash
# Install dependencies
sudo apt install -y python3 python3-venv nginx

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Setup app
cd ~/ai-coding-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup service
sudo cp deploy/ai-assistant.service /etc/systemd/system/
sudo systemctl enable ai-assistant
sudo systemctl start ai-assistant

# Setup nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ai-assistant
sudo ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## Documentation

- **Full Guide**: [../docs/DIGITAL_OCEAN_DEPLOYMENT.md](../docs/DIGITAL_OCEAN_DEPLOYMENT.md)
- **Quick Start**: [../docs/QUICK_START_DEPLOY.md](../docs/QUICK_START_DEPLOY.md)

## Platform Support

These deployment files work on:
- ✅ Digital Ocean (Ubuntu 22.04)
- ✅ AWS EC2 (Ubuntu)
- ✅ Google Cloud Compute Engine
- ✅ Any Linux VPS with systemd

## Requirements

- **OS**: Ubuntu 22.04+ (or Debian-based)
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 20GB minimum
- **Network**: Public IP address

## After Deployment

```bash
# View logs
sudo journalctl -u ai-assistant -f

# Restart service
sudo systemctl restart ai-assistant

# Check status
sudo systemctl status ai-assistant

# Update app
cd ~/ai-coding-assistant
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ai-assistant
```

## Troubleshooting

See [../docs/DIGITAL_OCEAN_DEPLOYMENT.md#troubleshooting](../docs/DIGITAL_OCEAN_DEPLOYMENT.md#troubleshooting)
