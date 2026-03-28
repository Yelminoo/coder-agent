# Quick Start - Deploy to Digital Ocean in 15 Minutes

## Option 1: Automated Deployment (Easiest)

### 1. Create Droplet
```bash
# Via Digital Ocean web UI:
- OS: Ubuntu 22.04 LTS
- Plan: 8GB RAM ($48/month minimum)
- Add your SSH key
```

### 2. Upload Files
```bash
# From your local machine:
cd C:\Users\User\Desktop\ai-coding-assistant
scp -r . root@YOUR_DROPLET_IP:~/ai-coding-assistant
```

### 3. Run Deployment Script
```bash
# SSH into server
ssh root@YOUR_DROPLET_IP

# Create user (if needed)
adduser aiuser
usermod -aG sudo aiuser
su - aiuser

# Move files
sudo mv /root/ai-coding-assistant ~/ 
cd ~/ai-coding-assistant

# Run deployment
bash deploy/deploy.sh
```

### 4. Access Your App
```
http://YOUR_DROPLET_IP
```

**Done! ✅**

---

## Option 2: Manual Step-by-Step

### 1. Create Droplet on Digital Ocean
- Login to DigitalOcean
- Click "Create" → "Droplets"
- Select Ubuntu 22.04
- Choose 8GB RAM plan ($48/month)
- Add SSH key
- Click "Create Droplet"

### 2. SSH and Update
```bash
ssh root@YOUR_DROPLET_IP
apt update && apt upgrade -y
```

### 3. Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:latest
```

### 4. Install Dependencies
```bash
apt install -y python3 python3-pip python3-venv git nginx
```

### 5. Upload Your Code
```bash
# From local Windows machine:
scp -r C:\Users\User\Desktop\ai-coding-assistant root@YOUR_DROPLET_IP:~/
```

### 6. Setup Application
```bash
cd ~/ai-coding-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7. Create Systemd Service
```bash
# Copy the service file
cp deploy/ai-assistant.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ai-assistant
systemctl start ai-assistant
```

### 8. Setup Nginx
```bash
cp deploy/nginx.conf /etc/nginx/sites-available/ai-assistant
ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 9. Open Firewall
```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 10. Access
```
http://YOUR_DROPLET_IP
```

---

## Troubleshooting

### App won't start?
```bash
sudo journalctl -u ai-assistant -n 50
```

### Ollama not working?
```bash
sudo systemctl status ollama
curl http://localhost:11434/api/tags
```

### Can't access via IP?
```bash
# Check firewall
sudo ufw status

# Check nginx
sudo nginx -t
sudo systemctl status nginx
```

---

## Costs

| Plan | RAM | CPU | Price/Month |
|------|-----|-----|-------------|
| Basic | 8GB | 4 vCPU | $48 |
| Better | 16GB | 8 vCPU | $96 |
| GPU | 16GB | 8 vCPU + GPU | $500+ |

**Recommendation**: Start with 8GB, upgrade if needed.

---

## Next Steps

1. **Add SSL**: Run `sudo certbot --nginx -d YOUR_DOMAIN.com`
2. **Monitor**: Check `htop` for resource usage
3. **Backup**: Enable DigitalOcean automated backups
4. **Update**: `git pull` to get latest features

---

For detailed guide, see: [docs/DIGITAL_OCEAN_DEPLOYMENT.md](DIGITAL_OCEAN_DEPLOYMENT.md)
