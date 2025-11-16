#!/bin/bash

# LeadGen Pro - Automated Setup Script
# This script automatically sets up the entire application

set -e

echo "============================================"
echo "LeadGen Pro - Automated Setup"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${NC}ℹ $1${NC}"
}

# Check if MongoDB is running
print_info "Checking MongoDB..."
if ! pgrep -x "mongod" > /dev/null; then
    print_warning "MongoDB is not running. Starting MongoDB..."
    sudo systemctl start mongod || sudo service mongod start || mongod --fork --logpath /var/log/mongodb.log
    sleep 3
fi
print_success "MongoDB is running"

# Check if Redis is running
print_info "Checking Redis..."
if ! pgrep -x "redis-server" > /dev/null; then
    print_warning "Redis is not running. Starting Redis..."
    sudo systemctl start redis || sudo service redis start || redis-server --daemonize yes
    sleep 2
fi
print_success "Redis is running"

# Backend Setup
print_info "Setting up Backend..."
cd /app/backend

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
print_success "Python dependencies installed"

# Create necessary directories
mkdir -p /var/log/celery
mkdir -p /app/test_reports

# Frontend Setup
print_info "Setting up Frontend..."
cd /app/frontend

# Install Node dependencies
print_info "Installing Node dependencies (this may take a few minutes)..."
yarn install --silent > /dev/null 2>&1
print_success "Node dependencies installed"

# Setup Celery Workers
print_info "Setting up Celery workers..."

# Create Celery systemd service
sudo tee /etc/systemd/system/celery.service > /dev/null << EOF
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/app/backend
Environment="PATH=/root/.venv/bin"
ExecStart=/root/.venv/bin/celery -A celery_app worker --loglevel=info --logfile=/var/log/celery/worker.log --detach
ExecStop=/root/.venv/bin/celery -A celery_app control shutdown
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create Celery Beat (scheduler) service
sudo tee /etc/systemd/system/celerybeat.service > /dev/null << EOF
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/app/backend
Environment="PATH=/root/.venv/bin"
ExecStart=/root/.venv/bin/celery -A celery_app beat --loglevel=info --logfile=/var/log/celery/beat.log
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start services
sudo systemctl daemon-reload
sudo systemctl enable celery celerybeat
sudo systemctl restart celery celerybeat

print_success "Celery workers configured and started"

# Restart application services
print_info "Restarting application services..."
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
sleep 5

print_success "Services restarted"

# Check service status
print_info "Checking service status..."
if sudo supervisorctl status backend | grep -q "RUNNING"; then
    print_success "Backend is running"
else
    print_error "Backend failed to start. Check logs: tail -f /var/log/supervisor/backend.err.log"
fi

if sudo supervisorctl status frontend | grep -q "RUNNING"; then
    print_success "Frontend is running"
else
    print_error "Frontend failed to start. Check logs: tail -f /var/log/supervisor/frontend.err.log"
fi

# Display final information
echo ""
echo "============================================"
print_success "Setup Complete!"
echo "============================================"
echo ""
print_info "Application is ready!"
echo ""
print_info "API Endpoints:"
echo "  - Health Check: ${REACT_APP_BACKEND_URL}/api/health"
echo "  - API Docs: ${REACT_APP_BACKEND_URL}/docs"
echo ""
print_info "Services Status:"
echo "  - Backend: sudo supervisorctl status backend"
echo "  - Frontend: sudo supervisorctl status frontend"
echo "  - Celery Workers: sudo systemctl status celery"
echo ""
print_info "Logs:"
echo "  - Backend: tail -f /var/log/supervisor/backend.*.log"
echo "  - Frontend: tail -f /var/log/supervisor/frontend.*.log"
echo "  - Celery: tail -f /var/log/celery/worker.log"
echo ""
print_warning "Remember to configure SMTP credentials in /app/backend/.env for email functionality"
echo ""
