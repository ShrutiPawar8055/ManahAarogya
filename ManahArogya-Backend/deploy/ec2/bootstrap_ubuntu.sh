#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   sudo bash deploy/ec2/bootstrap_ubuntu.sh
#
# What this script does:
# 1) Installs Python/Nginx/system packages
# 2) Creates virtualenv
# 3) Installs backend requirements
# 4) Installs systemd units for API + worker

APP_ROOT="/opt/manaharogya"
BACKEND_DIR="${APP_ROOT}/backend"
SYSTEMD_DIR="/etc/systemd/system"

echo "Installing system packages..."
apt-get update
apt-get install -y python3 python3-venv python3-pip nginx curl git

if [[ ! -d "${BACKEND_DIR}" ]]; then
  echo "ERROR: ${BACKEND_DIR} not found. Clone repo to ${APP_ROOT} first."
  exit 1
fi

echo "Creating virtual environment..."
python3 -m venv "${BACKEND_DIR}/venv"

echo "Installing Python requirements..."
"${BACKEND_DIR}/venv/bin/pip" install --upgrade pip
"${BACKEND_DIR}/venv/bin/pip" install -r "${BACKEND_DIR}/requirements.txt"

if [[ ! -f "${BACKEND_DIR}/.env" ]]; then
  echo "WARNING: ${BACKEND_DIR}/.env not found."
  echo "Create it from ${BACKEND_DIR}/.env.example before starting services."
fi

echo "Installing systemd unit files..."
cp "${BACKEND_DIR}/deploy/ec2/manaharogya-api.service" "${SYSTEMD_DIR}/manaharogya-api.service"
cp "${BACKEND_DIR}/deploy/ec2/manaharogya-voice-worker.service" "${SYSTEMD_DIR}/manaharogya-voice-worker.service"

echo "Reloading systemd..."
systemctl daemon-reload

echo "Enabling services..."
systemctl enable manaharogya-api
systemctl enable manaharogya-voice-worker

echo "Done. After setting .env, run:"
echo "  sudo systemctl restart manaharogya-api manaharogya-voice-worker"
echo "  sudo systemctl status manaharogya-api manaharogya-voice-worker --no-pager"
