#!/bin/bash
# Quick deployment script for Digital Ocean
# Run as: bash deploy.sh

set -e  # Exit on error

echo "🚀 Starting AI Coding Assistant Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Do not run this script as root${NC}"
    echo "Run as regular user with sudo access"
    exit 1
fi

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install basic dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
sudo apt install -y python3 python3-pip python3-venv git nginx curl wget htop ufw

# Setup firewall
echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo "y" | sudo ufw enable

# Install Ollama
echo -e "${YELLOW}🤖 Installing Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    sudo systemctl enable ollama
    sudo systemctl start ollama
else
    echo "Ollama already installed"
fi

# Verify Ollama is running
sleep 3
if systemctl is-active --quiet ollama; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${RED}❌ Ollama failed to start${NC}"
    exit 1
fi

# Setup application directory
APP_DIR="$HOME/ai-coding-assistant"
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Application directory not found: $APP_DIR${NC}"
    echo "Please upload your application files first"
    exit 1
fi

cd "$APP_DIR"

# Create virtual environment
echo -e "${YELLOW}🐍 Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python packages...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Setup .env if not exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  Creating .env file...${NC}"
    cat > .env << EOF
# LLM CONFIGURATION
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
LLM_MODE=LOCAL_ONLY

# URL FETCHING
ENABLE_URL_FETCH=false

# CHAT STORAGE
CHAT_STORE_BACKEND=sqlite
CHAT_DB_PATH=data/chat_sessions.db
EOF
    echo -e "${GREEN}✅ Created .env file (edit as needed)${NC}"
fi

# Create data directory
mkdir -p data logs

# Download Ollama model
echo -e "${YELLOW}📥 Downloading Ollama model (this may take a while)...${NC}"
ollama pull llama3.2:latest

# Setup systemd service
echo -e "${YELLOW}⚙️  Setting up systemd service...${NC}"
sudo tee /etc/systemd/system/ai-assistant.service > /dev/null << EOF
[Unit]
Description=AI Coding Assistant FastAPI Server
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$APP_DIR/venv/bin/python web_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ai-assistant
sudo systemctl start ai-assistant

# Wait for app to start
sleep 3

# Check service status
if systemctl is-active --quiet ai-assistant; then
    echo -e "${GREEN}✅ Application service is running${NC}"
else
    echo -e "${RED}❌ Application service failed to start${NC}"
    echo "Check logs with: sudo journalctl -u ai-assistant -n 50"
    exit 1
fi

# Setup nginx
echo -e "${YELLOW}🌐 Configuring Nginx...${NC}"
SERVER_IP=$(curl -s ifconfig.me)

sudo tee /etc/nginx/sites-available/ai-assistant > /dev/null << EOF
server {
    listen 80;
    server_name $SERVER_IP _;

    client_max_body_size 10M;
    client_body_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
        proxy_cache off;
    }

    location /static {
        alias $APP_DIR/static;
        expires 30d;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default nginx page

# Test nginx config
if sudo nginx -t; then
    sudo systemctl restart nginx
    echo -e "${GREEN}✅ Nginx configured and running${NC}"
else
    echo -e "${RED}❌ Nginx configuration error${NC}"
    exit 1
fi

# Final summary
echo -e "\n${GREEN}=========================================="
echo "✅ Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "🌐 Access your application at:"
echo "   http://$SERVER_IP"
echo ""
echo "📊 Useful commands:"
echo "   View logs:          sudo journalctl -u ai-assistant -f"
echo "   Restart app:        sudo systemctl restart ai-assistant"
echo "   Check status:       sudo systemctl status ai-assistant"
echo "   Nginx logs:         sudo tail -f /var/log/nginx/access.log"
echo ""
echo "📝 Next steps:"
echo "   1. Visit http://$SERVER_IP to test"
echo "   2. Configure domain + SSL (see docs/DIGITAL_OCEAN_DEPLOYMENT.md)"
echo "   3. Edit .env for custom settings"
echo "   4. Monitor with: htop"
echo ""
echo "🎉 Happy coding!"
