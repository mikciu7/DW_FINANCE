#!/bin/bash
# EC2 setup script for MED backend
# Run as: bash ec2_setup.sh
# Tested on Ubuntu 22.04 (t2.micro)

set -e

APP_DIR="/home/ubuntu/med"
SERVICE_NAME="med-backend"

echo "=== Installing system dependencies ==="
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv nginx git

echo "=== Creating app directory ==="
mkdir -p "$APP_DIR"
cd "$APP_DIR"

echo "=== Setting up Python virtualenv ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "=== Creating systemd service ==="
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=MED Backend (FastAPI + uvicorn)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=${APP_DIR}/backend
ExecStart=${APP_DIR}/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment="PYTHONPATH=${APP_DIR}/backend"

[Install]
WantedBy=multi-user.target
EOF

echo "=== Configuring nginx ==="
sudo tee /etc/nginx/sites-available/med > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/med /etc/nginx/sites-enabled/med
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "=== Enabling and starting backend service ==="
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

echo ""
echo "=== Setup complete! ==="
echo "Next steps:"
echo "  1. Copy your project files to ${APP_DIR}/"
echo "  2. Run init_db: cd ${APP_DIR}/backend && ../venv/bin/python init_db.py"
echo "  3. Start service: sudo systemctl start ${SERVICE_NAME}"
echo "  4. Check logs: sudo journalctl -u ${SERVICE_NAME} -f"