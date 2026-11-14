#!/usr/bin/env bash
# =============================================================================
# IKAS — OCI VM Setup Script
# Tested on: Oracle Linux 8 / Ubuntu 22.04 (ARM or AMD)
#
# Run once as opc (Oracle Linux) or ubuntu user with sudo privileges:
#   chmod +x setup.sh && ./setup.sh
# =============================================================================
set -euo pipefail

IKAS_DIR="/opt/ikas"
COMPOSE_VERSION="2.24.5"

echo "════════════════════════════════════════════════════════"
echo "  IKAS — OCI VM Setup"
echo "════════════════════════════════════════════════════════"

# ─── 1. System packages ───────────────────────────────────────────────────────
echo "▶ Installing system packages..."
if command -v apt-get &>/dev/null; then
    # Ubuntu / Debian
    sudo apt-get update -q
    sudo apt-get install -y -q \
        curl git unzip ca-certificates gnupg lsb-release \
        iptables-persistent ufw
    # Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -q
    sudo apt-get install -y -q docker-ce docker-ce-cli containerd.io
else
    # Oracle Linux / RHEL
    sudo dnf install -y curl git unzip ca-certificates firewalld
    sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io
fi

# ─── 2. Docker Compose plugin ────────────────────────────────────────────────
echo "▶ Installing Docker Compose v${COMPOSE_VERSION}..."
ARCH=$(uname -m)
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL \
    "https://github.com/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-linux-${ARCH}" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# ─── 3. Start and enable Docker ──────────────────────────────────────────────
echo "▶ Starting Docker..."
sudo systemctl enable --now docker
sudo usermod -aG docker "$(whoami)"

# ─── 4. Firewall — allow HTTP, HTTPS, SSH ────────────────────────────────────
echo "▶ Configuring firewall..."
if command -v ufw &>/dev/null; then
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
elif command -v firewall-cmd &>/dev/null; then
    sudo firewall-cmd --permanent --add-service=ssh
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --reload
fi

# ─── 5. OCI iptables fix (OCI VMs block traffic by default) ──────────────────
echo "▶ Patching OCI iptables rules..."
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
# Make persistent
if command -v netfilter-persistent &>/dev/null; then
    sudo netfilter-persistent save
fi

# ─── 6. Create IKAS directory ────────────────────────────────────────────────
echo "▶ Creating ${IKAS_DIR}..."
sudo mkdir -p "${IKAS_DIR}"
sudo chown "$(whoami)":"$(whoami)" "${IKAS_DIR}"

# ─── 7. Clone or copy repo ────────────────────────────────────────────────────
echo "▶ Copying deployment files..."
# If running from the repo directory, copy deploy files:
if [ -f "./docker-compose.prod.yml" ]; then
    cp docker-compose.prod.yml "${IKAS_DIR}/"
    cp nginx.conf "${IKAS_DIR}/"
    cp .env.production.example "${IKAS_DIR}/.env.production.example"
    echo "  Copied deploy files to ${IKAS_DIR}"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Copy your application code to ${IKAS_DIR}"
echo "     scp -r /path/to/IKAS opc@<VM_IP>:${IKAS_DIR}"
echo ""
echo "  2. Configure environment:"
echo "     cp ${IKAS_DIR}/.env.production.example ${IKAS_DIR}/.env.production"
echo "     nano ${IKAS_DIR}/.env.production   # fill in your secrets"
echo ""
echo "  3. Start containers:"
echo "     cd ${IKAS_DIR}"
echo "     docker compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "  4. Seed the Neo4j knowledge graph:"
echo "     ./seed.sh"
echo ""
echo "  NOTE: Log out and log back in for Docker group to take effect."
echo "════════════════════════════════════════════════════════"
