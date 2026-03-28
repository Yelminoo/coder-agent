# Deploy to Digital Ocean - Step by Step Guide

## Prerequisites
- Digital Ocean account
- Domain name (optional, for SSL)
- SSH key configured

---

## Step 1: Create Digital Ocean Droplet

### 1.1 Choose Droplet Specs
**Recommended for Ollama:**
- **Image**: Ubuntu 22.04 LTS
- **Plan**: 
  - **Minimum**: CPU-Optimized, 8GB RAM ($48/month) - For 3B models
  - **Recommended**: CPU-Optimized, 16GB RAM ($96/month) - For 8B models
  - **GPU**: GPU Droplets ($500+/month) - For fast inference
- **Region**: Choose closest to your users
- **Add SSH Key**: Upload your public key

### 1.2 Create Droplet
```bash
# Via Web UI or API
doctl compute droplet create ai-assistant \
  --size c-8 \
  --image ubuntu-22-04-x64 \
  --region sfo3 \
  --ssh-keys YOUR_SSH_KEY_ID
```

### 1.3 Note Your IP Address
```bash
# Save the droplet IP address
export DROPLET_IP=YOUR_DROPLET_IP
```

---

## Step 2: Initial Server Setup

### 2.1 SSH Into Server
```bash
ssh root@$DROPLET_IP
```

### 2.2 Update System
```bash
apt update && apt upgrade -y
```

### 2.3 Create Non-Root User
```bash
adduser aiuser
usermod -aG sudo aiuser

# Copy SSH keys
rsync --archive --chown=aiuser:aiuser ~/.ssh /home/aiuser
```

### 2.4 Setup Firewall
```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## Step 3: Install Dependencies

### 3.1 Install Python 3.11+
```bash
apt install -y python3 python3-pip python3-venv
```

### 3.2 Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
systemctl enable ollama
systemctl start ollama

# Verify
ollama --version
```

### 3.3 Install Git
```bash
apt install -y git
```

---

## Step 4: Deploy Application

### 4.1 Switch to Application User
```bash
su - aiuser
```

### 4.2 Clone Repository
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/ai-coding-assistant.git
# OR upload via scp:
# scp -r C:\Users\User\Desktop\ai-coding-assistant aiuser@$DROPLET_IP:~/

cd ai-coding-assistant
```

### 4.3 Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4.4 Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.5 Configure Environment Variables
```bash
nano .env
```

Edit `.env`:
```env
# LLM CONFIGURATION
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
LLM_MODE=LOCAL_ONLY

# Disable URL fetching (optional)
ENABLE_URL_FETCH=false

# GITHUB OAUTH (Optional - only if you want authentication)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://YOUR_DOMAIN/auth/github/callback

# CHAT STORAGE
CHAT_STORE_BACKEND=sqlite
CHAT_DB_PATH=data/chat_sessions.db
```

### 4.6 Download Ollama Model
```bash
ollama pull llama3.2:latest
# This will download ~2GB

# Optional: Download other models
# ollama pull codellama:7b
# ollama pull llama3.1:8b
```

---

## Step 5: Setup Systemd Service

### 5.1 Create Service File (as root)
```bash
sudo nano /etc/systemd/system/ai-assistant.service
```

Paste this configuration:
```ini
[Unit]
Description=AI Coding Assistant
After=network.target ollama.service

[Service]
Type=simple
User=aiuser
WorkingDirectory=/home/aiuser/ai-coding-assistant
Environment="PATH=/home/aiuser/ai-coding-assistant/venv/bin"
ExecStart=/home/aiuser/ai-coding-assistant/venv/bin/python web_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.2 Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-assistant
sudo systemctl start ai-assistant

# Check status
sudo systemctl status ai-assistant

# View logs
sudo journalctl -u ai-assistant -f
```

---

## Step 6: Setup Nginx Reverse Proxy

### 6.1 Install Nginx
```bash
sudo apt install -y nginx
```

### 6.2 Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/ai-assistant
```

Paste this configuration:
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN.com;  # or use IP address

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For SSE streaming
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    location /static {
        alias /home/aiuser/ai-coding-assistant/static;
        expires 30d;
    }
}
```

### 6.3 Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 7: Setup SSL with Let's Encrypt (Optional)

### 7.1 Install Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 7.2 Obtain SSL Certificate
```bash
sudo certbot --nginx -d YOUR_DOMAIN.com

# Follow prompts
# Select: Redirect HTTP to HTTPS
```

### 7.3 Test Auto-Renewal
```bash
sudo certbot renew --dry-run
```

---

## Step 8: Configure Ollama for Production

### 8.1 Optimize Ollama Settings
```bash
sudo nano /etc/systemd/system/ollama.service.d/override.conf
```

Add:
```ini
[Service]
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_FLASH_ATTENTION=1"
```

### 8.2 Restart Ollama
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

---

## Step 9: Maintenance Commands

### View Application Logs
```bash
sudo journalctl -u ai-assistant -f
```

### View Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
sudo systemctl restart ai-assistant
sudo systemctl restart ollama
sudo systemctl restart nginx
```

### Update Application
```bash
cd ~/ai-coding-assistant
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ai-assistant
```

### Monitor System Resources
```bash
htop
free -h
df -h
```

---

## Step 10: Access Your Application

### Without Domain (IP only)
```
http://YOUR_DROPLET_IP
```

### With Domain + SSL
```
https://YOUR_DOMAIN.com
```

---

## Troubleshooting

### Application Won't Start
```bash
# Check service status
sudo systemctl status ai-assistant

# View detailed logs
sudo journalctl -u ai-assistant -n 50

# Check if port is in use
sudo netstat -tlnp | grep 8000
```

### Ollama Connection Failed
```bash
# Check Ollama status
sudo systemctl status ollama

# Test Ollama directly
curl http://localhost:11434/api/tags

# Restart Ollama
sudo systemctl restart ollama
```

### Nginx 502 Bad Gateway
```bash
# Check if app is running
sudo systemctl status ai-assistant

# Check Nginx config
sudo nginx -t

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Out of Memory
```bash
# Check memory usage
free -h

# Kill hung processes
sudo systemctl restart ai-assistant
sudo systemctl restart ollama

# Consider upgrading droplet size
```

---

## Performance Optimization

### 1. Enable Redis Caching (Optional)
```bash
sudo apt install -y redis-server
sudo systemctl enable redis-server
```

### 2. Use GPU Droplet for Faster Inference
- Switch to GPU-enabled droplet ($500+/month)
- Ollama will automatically detect and use GPU

### 3. Use Smaller Models
```bash
# If 8B model is too slow:
ollama pull llama3.2:1b
# Update .env: OLLAMA_MODEL=llama3.2:1b
```

### 4. Load Balancing (Multiple Droplets)
- Set up multiple droplets
- Use DigitalOcean Load Balancer
- Share database via managed PostgreSQL

---

## Cost Estimation

### Minimum Setup (CPU-Only)
- **8GB RAM Droplet**: $48/month
- **Total**: ~$50/month

### Recommended Setup (Better Performance)
- **16GB RAM Droplet**: $96/month
- **Total**: ~$100/month

### Premium Setup (GPU)
- **GPU Droplet**: $500-1000/month
- **Total**: $500-1000/month

---

## Security Checklist

✅ SSH key authentication only (disable password)
✅ UFW firewall enabled
✅ SSL certificate installed
✅ Regular system updates
✅ Non-root user for application
✅ Environment variables in .env (not committed to git)
✅ Rate limiting via nginx (optional)

---

## Quick Deployment Script

Save as `deploy.sh`:
```bash
#!/bin/bash
set -e

echo "🚀 Deploying AI Coding Assistant to Digital Ocean"

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv git nginx

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Setup application
cd ~/ai-coding-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download model
ollama pull llama3.2:latest

# Setup systemd service
sudo cp deploy/ai-assistant.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-assistant
sudo systemctl start ai-assistant

# Setup nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ai-assistant
sudo ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "✅ Deployment complete!"
echo "Access your app at: http://$(curl -s ifconfig.me)"
```

---

## Next Steps

1. ✅ **Monitor**: Set up monitoring with DigitalOcean Monitoring
2. ✅ **Backup**: Enable automated backups (Droplet Backups)
3. ✅ **Scaling**: Add load balancer if traffic increases
4. ✅ **CI/CD**: Setup GitHub Actions for auto-deployment

---

## Support

**Documentation**: See other docs in `/docs` folder
**Issues**: Check logs first, then troubleshoot section above
**Updates**: `git pull` regularly for latest features
