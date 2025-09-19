#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="/opt/casescope/logs"
APP_DIR="/opt/casescope"
PY_ENV="$APP_DIR/venv"
OS_USER="casescope"
SERVICE_NAME="casescope"

sudo mkdir -p "$LOG_DIR"; sudo touch "${LOG_DIR}/install.log"
exec 3>&1; exec 1>>"${LOG_DIR}/install.log"; exec 2>&1
msg(){ echo "$(date -u +"%F %T") | $*" >&3; echo "$(date -u +"%F %T") | $*"; }

pre(){ msg "Starting install..."; id -u "$OS_USER" >/dev/null 2>&1 || sudo useradd -r -s /usr/sbin/nologin -d "$APP_DIR" "$OS_USER"; sudo mkdir -p "$APP_DIR"; sudo chown -R "$OS_USER:$OS_USER" "$APP_DIR"; }
prereq(){ msg "Installing prerequisites"; sudo apt update -y; sudo apt install -y curl unzip python3-venv python3-pip openjdk-17-jre-headless jq ca-certificates gnupg lsb-release rsync; }
kernel(){ msg "Setting vm.max_map_count"; echo 'vm.max_map_count=262144' | sudo tee /etc/sysctl.d/99-opensearch.conf >/dev/null; sudo sysctl -w vm.max_map_count=262144 >/dev/null; }

repo(){
  if [ ! -f /etc/apt/sources.list.d/opensearch.list ]; then
    msg "Installing OpenSearch repo"
    curl -fsSL https://artifacts.opensearch.org/publickeys/opensearch.pgp | sudo gpg --dearmor -o /usr/share/keyrings/opensearch-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/opensearch-keyring.gpg] https://artifacts.opensearch.org/releases/bundle/opensearch/2.x/apt stable main" | sudo tee /etc/apt/sources.list.d/opensearch.list
    sudo apt update -y
  fi
}

os_dirs(){
  sudo systemctl stop opensearch 2>/dev/null || true
  sudo mkdir -p /etc/opensearch /var/lib/opensearch /var/log/opensearch /run/opensearch
  sudo ln -sf /run/opensearch /var/run/opensearch
  id opensearch >/dev/null 2>&1 || sudo useradd --system --home-dir /var/lib/opensearch --shell /usr/sbin/nologin opensearch
  sudo chown -R opensearch:opensearch /var/lib/opensearch /var/log/opensearch /run/opensearch
  echo 'd /run/opensearch 0755 opensearch opensearch -' | sudo tee /etc/tmpfiles.d/opensearch.conf >/dev/null
  sudo systemd-tmpfiles --create
}

install_opensearch(){
  msg "Installing OpenSearch (demo disabled)"
  sudo DEBIAN_FRONTEND=noninteractive DISABLE_INSTALL_DEMO_CONFIGURATION=true apt install -y opensearch || true
  sudo sed -i '/^plugins\\.security\\.disabled/d;/^network\\.host:/d;/^discovery\\.type:/d' /etc/opensearch/opensearch.yml 2>/dev/null || true
  printf '%s\n%s\n%s\n' \
    'plugins.security.disabled: true' \
    'network.host: 127.0.0.1' \
    'discovery.type: single-node' | sudo tee -a /etc/opensearch/opensearch.yml >/dev/null
  sudo env DISABLE_INSTALL_DEMO_CONFIGURATION=true dpkg --configure -a || true
  sudo systemctl daemon-reload
  sudo systemctl enable --now opensearch || (sudo journalctl -u opensearch -n 200 --no-pager >&3; exit 1)
  sleep 5
  curl -s http://127.0.0.1:9200 >/dev/null || { msg "OpenSearch not healthy"; exit 1; }
  msg "OpenSearch is up"
}

venv(){
  msg "Setting up Python venv"
  sudo -u "$OS_USER" python3 -m venv "$PY_ENV"
  sudo -u "$OS_USER" "$PY_ENV/bin/pip" install --upgrade pip
  sudo -u "$OS_USER" "$PY_ENV/bin/pip" install -r "$APP_DIR/requirements.txt"
}

service(){
  msg "Creating API service"
  sudo tee /etc/systemd/system/${SERVICE_NAME}.service >/dev/null <<UNIT
[Unit]
Description=caseScope API
After=network.target opensearch.service

[Service]
User=${OS_USER}
Group=${OS_USER}
WorkingDirectory=${APP_DIR}
Environment=PATH=${PY_ENV}/bin
ExecStart=${PY_ENV}/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT
  sudo systemctl daemon-reload
  sudo systemctl enable --now ${SERVICE_NAME}.service
}

sync_repo(){
  # If run from cloned repo, sync into /opt
  if [ -d "$PWD/app" ]; then
    msg "Syncing repo -> ${APP_DIR}"
    sudo rsync -a --delete "$PWD/" "$APP_DIR/"
    sudo chown -R "$OS_USER:$OS_USER" "$APP_DIR"
  fi
}

pre; prereq; kernel; repo; sync_repo; os_dirs; install_opensearch; venv; service
msg "Install complete. App: http://SERVER_IP:8080  Health: curl -s http://127.0.0.1:8080/health"
