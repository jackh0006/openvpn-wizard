#!/usr/bin/env bash
# OpenVPN Wizard v1.1.0 - Linux AMD64 Client Auto-Installer
# Run as root: curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/openvpn-wizard-linux.sh | bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log() { echo -e "${BLUE}[${NC}$(date '+%H:%M:%S')${BLUE}]${NC} $*"; }
ok()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn(){ echo -e "${YELLOW}[!]${NC} $*"; }
err() { echo -e "${RED}[✗]${NC} $*"; }
step(){ echo -e "\n${CYAN}▶${NC} ${BOLD}$*${NC}\n"; }

[[ $EUID -ne 0 ]] && { err "Run as root"; exit 1; }

SERVER_IP="192.209.62.112"
CLIENT_NAME="01-JH"
CONFIG_URL="https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/${CLIENT_NAME}-${SERVER_IP}.ovpn"
CONFIG_DIR="/etc/openvpn"
CONFIG_FILE="${CONFIG_DIR}/client.conf"

step "OpenVPN Wizard v1.1.0 - Linux Client Auto-Install"

# Detect distro
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    log "Detected: $PRETTY_NAME"
else
    err "Cannot detect OS"
    exit 1
fi

# Install OpenVPN
step "Installing OpenVPN"
case $ID in
    ubuntu|debian) apt-get update -qq && apt-get install -y -qq openvpn resolvconf ;;
    fedora|rhel|centos|rocky|almalinux) dnf install -y openvpn ;;
    arch|manjaro) pacman -Sy --noconfirm openvpn ;;
    *) err "Unsupported distro: $ID"; exit 1 ;;
esac
ok "OpenVPN installed"

# Download config
step "Downloading configuration"
mkdir -p "$CONFIG_DIR"
if curl -fsSL "$CONFIG_URL" -o "$CONFIG_FILE"; then
    ok "Config downloaded to $CONFIG_FILE"
else
    err "Failed to download config from $CONFIG_URL"
    exit 1
fi

# Create systemd service
step "Creating systemd service"
cat > /etc/systemd/system/openvpn-client@.service <<EOF
[Unit]
Description=OpenVPN Client (%i)
Documentation=https://github.com/Jackh0006/openvpn-wizard
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
PrivateTmp=true
ProtectSystem=full
ProtectHome=yes
NoNewPrivileges=yes
PrivateTmp=true
ProtectSystem=full
ProtectHome=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
RestrictNamespaces=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
RemoveIPC=yes
ProtectClock=yes
ProtectProc=invisible
ProcSubset=pid
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_DAC_OVERRIDE CAP_SETGID CAP_SETUID
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE

ExecStart=/usr/sbin/openvpn --config %i --auth-user-pass /etc/openvpn/auth.txt
Restart=on-failure
RestartSec=10
KillMode=process
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
EOF

# Create auth file
cat > /etc/openvpn/auth.txt <<EOF
MHH06
S271m31h41
EOF
chmod 600 /etc/openvpn/auth.txt

# Enable and start
systemctl daemon-reload
systemctl enable openvpn-client@client
systemctl start openvpn-client@client

ok "OpenVPN client service started"

# Verify connection
sleep 3
if ip addr show tun0 >/dev/null 2>&1; then
    ok "VPN connected! Interface: tun0"
    ip addr show tun0 | grep inet
else
    warn "VPN may not be connected yet. Check: journalctl -u openvpn-client@client -f"
fi

echo ""
echo "=== Management ==="
echo "  Status:  systemctl status openvpn-client@client"
echo "  Logs:    journalctl -u openvpn-client@client -f"
echo "  Stop:    systemctl stop openvpn-client@client"
echo "  Restart: systemctl restart openvpn-client@client"
echo ""
echo "Credentials:"
echo "  Username: MHH06"
echo "  Password: S271m31h41"
EOF
chmod +x /root/openvpn-wizard/openvpn-wizard-linux.sh
ok "Linux installer created"