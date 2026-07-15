# ManahAarogya Backend

This backend has two long-running processes:
- FastAPI API server
- LiveKit voice agent worker

## Local run

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Windows: copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run worker in a second terminal:

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m app.agents.voice_agent start
```

## Required environment variables

Copy `backend/.env.example` and set values:
- `DATABASE_URL`
- `CEREBRAS_API_KEY`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_PRIVATE_KEY`
- `FIREBASE_CLIENT_EMAIL`
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `SARVAM_API_KEY`
- `CRON_SECRET`

## EC2 deployment (recommended for this repo)

### 1) Launch EC2 instance
- Ubuntu 22.04 or 24.04
- Open security group ports: `22`, `80`, `443`

### 2) Clone project on server

```bash
sudo mkdir -p /opt/manaharogya
sudo chown -R ubuntu:ubuntu /opt/manaharogya
cd /opt/manaharogya
git clone <your-repo-url> .
```

### 3) Bootstrap dependencies and services

```bash
cd /opt/manaharogya/backend
chmod +x deploy/ec2/bootstrap_ubuntu.sh
sudo bash deploy/ec2/bootstrap_ubuntu.sh
```

### 4) Configure environment

```bash
cd /opt/manaharogya/backend
cp .env.example .env
nano .env
```

### 5) Start API + worker services

```bash
sudo systemctl restart manaharogya-api manaharogya-voice-worker
sudo systemctl status manaharogya-api manaharogya-voice-worker --no-pager
```

Systemd templates:
- `deploy/ec2/manaharogya-api.service`
- `deploy/ec2/manaharogya-voice-worker.service`

### 6) Configure Nginx reverse proxy

```bash
sudo cp /opt/manaharogya/backend/deploy/ec2/manaharogya.nginx.conf /etc/nginx/sites-available/manaharogya
sudo ln -s /etc/nginx/sites-available/manaharogya /etc/nginx/sites-enabled/manaharogya
sudo nginx -t
sudo systemctl reload nginx
```

Update `server_name` in `deploy/ec2/manaharogya.nginx.conf` before reload.

### 7) Enable HTTPS (Let's Encrypt)

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.example.com
```

### 8) Configure cron

Use entries from `deploy/ec2/cron.example`:

```bash
crontab -e
```

## Health and API checks

- `GET /health`
- `POST /internal/cron/heartbeat` with header `X-CRON-KEY: <CRON_SECRET>`
- `POST /api/v1/voice/token`

## Key process commands

- API: `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Worker: `python -m app.agents.voice_agent start`
- API heartbeat command: `python -m app.cron_tasks heartbeat`
- Worker heartbeat command: `python -m app.agents.cron_tasks heartbeat`
