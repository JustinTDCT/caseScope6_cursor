#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="/opt/casescope/logs"
APP_DIR="/opt/casescope"
PY_ENV="$APP_DIR/venv"
OS_USER="casescope"
SERVICE_NAME="casescope"
exec 3>&1 1>>"${LOG_DIR}/install.log" 2>&1 || true

msg(){ echo "$(date -u +"%F %T") | $*" >&3; echo "$(date -u +"%F %T") | $*"; }

pre_checks(){
  sudo mkdir -p "$LOG_DIR"
  sudo touch "${LOG_DIR}/install.log"
  msg "Starting install..."
  if ! id -u "$OS_USER" >/dev/null 2>&1; then
    sudo useradd -r -s /usr/sbin/nologin -d "$APP_DIR" "$OS_USER" || true
  fi
  sudo mkdir -p "$APP_DIR"
  sudo chown -R "$OS_USER:$OS_USER" "$APP_DIR"
}

install_prereqs(){
  msg "Installing prerequisites"
  sudo apt update -y
  sudo apt install -y curl unzip python3-venv python3-pip openjdk-17-jre-headless
}

install_opensearch(){
  if [ ! -f /etc/apt/sources.list.d/opensearch.list ]; then
    msg "Installing OpenSearch repo"
    curl -fsSL https://artifacts.opensearch.org/publickeys/opensearch.pgp | sudo gpg --dearmor -o /usr/share/keyrings/opensearch-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/opensearch-keyring.gpg] https://artifacts.opensearch.org/releases/bundle/opensearch/2.x/apt stable main" | sudo tee /etc/apt/sources.list.d/opensearch.list
    sudo apt update -y
    sudo apt install -y opensearch
    sudo sed -i 's|^#\?network.host:.*|network.host: 127.0.0.1|' /etc/opensearch/opensearch.yml
    sudo sed -i 's|^#\?discovery.type:.*|discovery.type: single-node|' /etc/opensearch/opensearch.yml
    sudo systemctl enable --now opensearch
  fi
  sleep 5
  curl -k -s http://127.0.0.1:9200 | jq . >/dev/null || { msg "OpenSearch not healthy"; exit 1; }
  msg "OpenSearch is up"
}

setup_python(){
  msg "Setting up Python venv"
  sudo -u "$OS_USER" python3 -m venv "$PY_ENV"
  sudo -u "$OS_USER" "$PY_ENV/bin/pip" install --upgrade pip
  sudo -u "$OS_USER" "$PY_ENV/bin/pip" install -r "$APP_DIR/requirements.txt"
}

install_chainsaw_sigma(){
  msg "Installing Chainsaw and Sigma rules"
  CHAIN_DIR="$APP_DIR/tools/chainsaw"
  SIGMA_DIR="$APP_DIR/tools/sigma"
  sudo -u "$OS_USER" mkdir -p "$CHAIN_DIR" "$SIGMA_DIR"
  # Chainsaw
  if [ ! -f "$CHAIN_DIR/chainsaw" ]; then
    URL=$(curl -s https://api.github.com/repos/WithSecureLabs/chainsaw/releases/latest | jq -r '.assets[] | select(.name|test("linux.*zip$")) | .browser_download_url' | head -n1)
    curl -L "$URL" -o /tmp/chainsaw.zip
    sudo -u "$OS_USER" unzip -o /tmp/chainsaw.zip -d "$CHAIN_DIR"
    sudo chmod +x "$CHAIN_DIR"/chainsaw*
    sudo -u "$OS_USER" ln -sf "$CHAIN_DIR"/chainsaw* "$CHAIN_DIR/chainsaw"
  fi
  # Sigma rules
  if [ ! -d "$SIGMA_DIR/rules" ]; then
    sudo -u "$OS_USER" git clone https://github.com/SigmaHQ/sigma.git "$SIGMA_DIR/sigma_repo"
    sudo -u "$OS_USER" mkdir -p "$SIGMA_DIR/rules"
    sudo -u "$OS_USER" rsync -a "$SIGMA_DIR/sigma_repo/rules/" "$SIGMA_DIR/rules/"
  else
    sudo -u "$OS_USER" bash -c "cd $SIGMA_DIR/sigma_repo && git pull --rebase || true"
  fi
}

create_systemd(){
  msg "Creating systemd service"
  sudo tee /etc/systemd/system/${SERVICE_NAME}.service >/dev/null <<UNIT
[Unit]
Description=caseScope API
After=network.target opensearch.service

[Service]
User=${OS_USER}
Group=${OS_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${PY_ENV}/bin"
ExecStart=${PY_ENV}/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT
  sudo systemctl daemon-reload
  sudo systemctl enable --now ${SERVICE_NAME}.service
}

post_info(){
  msg "Install complete."
  msg "Service: systemctl status ${SERVICE_NAME}"
  msg "App:     http://SERVER_IP:8080"
  msg "Health:  curl -s http://127.0.0.1:8080/health"
}

pre_checks
install_prereqs
install_opensearch
setup_python
install_chainsaw_sigma
create_systemd
post_info
