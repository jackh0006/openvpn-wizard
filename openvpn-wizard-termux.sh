#!/data/data/com.termux/files/usr/bin/bash
# OpenVPN Wizard v1.1.0 - Termux ARM64 Client Setup
# Run this on Android Termux to auto-configure OpenVPN

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

# Check if running in Termux
if [[ ! -d "/data/data/com.termux" ]]; then
    err "This script must run in Termux on Android"
    exit 1
fi

step "OpenVPN Wizard v1.1.0 - Termux Client Setup"

# Update packages
log "Updating Termux packages..."
pkg update -y && pkg upgrade -y

# Install OpenVPN
log "Installing OpenVPN..."
pkg install -y openvpn openssl curl wget qrencode

# Create config directory
mkdir -p ~/.openvpn

# Get server details
echo ""
read -p "Enter server domain or IP [cf.mhhdns.online]: " SERVER_DOMAIN
SERVER_DOMAIN="${SERVER_DOMAIN:-cf.mhhdns.online}"

read -p "Enter client name [01-JH]: " CLIENT_NAME
CLIENT_NAME="${CLIENT_NAME:-01-JH}"

read -p "Enter username [MHH06]: " USERNAME
USERNAME="${USERNAME:-MHH06}"

read -p "Enter password [S271m31h41]: " PASSWORD
PASSWORD="${PASSWORD:-S271m31h41}"

# Try to download config from server
CONFIG_URL="https://${SERVER_DOMAIN}/${CLIENT_NAME}-$(echo ${SERVER_DOMAIN} | sed 's/[^0-9.]//g').ovpn"
log "Attempting to download config from ${CONFIG_URL}..."
if curl -fsSL "$CONFIG_URL" -o ~/.openvpn/client.ovpn 2>/dev/null; then
    ok "Config downloaded from server"
else
    warn "Could not download config from server. Creating local config..."
    # Create basic config that will work with the server
    cat > ~/.openvpn/client.ovpn <<EOF
client
dev tun
proto tcp4-client
remote ${SERVER_DOMAIN} 443
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
verify-x509-name server name
cipher AES-256-GCM
auth SHA256
auth-user-pass
auth-nocache
explicit-exit-notify 1
verb 3
mute 10
keepalive 10 60
tun-mtu 1500
mssfix 1360
sndbuf 524288
rcvbuf 524288
txqueuelen 1000
reneg-sec 0
mute-replay-warnings
persist-remote-ip

<ca>
# CA certificate will be added by server
# Run 'ovpn-get-ovpn ${CLIENT_NAME}' on server to get full config
</ca>

<cert>
# Client certificate will be added by server
</cert>

<key>
# Client key will be added by server
</key>

<tls-crypt-v2>
# TLS-crypt-v2 key will be added by server
</tls-crypt-v2>
EOF
    warn "Created minimal config. Run 'ovpn-get-ovpn ${CLIENT_NAME}' on server to get full config with certs/keys."
fi

# Create shortcuts
mkdir -p ~/.shortcuts

cat > ~/.shortcuts/openvpn-connect <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# OpenVPN Connect Shortcut
cd ~/.openvpn
sudo openvpn --config client.ovpn --auth-user-pass <(echo -e "MHH06\nS271m31h41")
EOF
chmod +x ~/.shortcuts/openvpn-connect

cat > ~/.shortcuts/openvpn-disconnect <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
sudo pkill -f "openvpn.*client.ovpn"
echo "Disconnected"
EOF
chmod +x ~/.shortcuts/openvpn-disconnect

# Create status shortcut
cat > ~/.shortcuts/openvpn-status <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
echo "=== OpenVPN Status ==="
ip addr show tun0 2>/dev/null | grep inet || echo "Not connected"
echo ""
echo "Routes:"
ip route | grep tun0
echo ""
echo "Test connectivity:"
ping -c 2 1.1.1.1 2>&1 | tail -3
EOF
chmod +x ~/.shortcuts/openvpn-status

# Save credentials
cat > ~/.openvpn/credentials <<EOF
username: MHH06
password: S271m31h41
EOF
chmod 600 ~/.openvpn/credentials

ok "Termux setup complete!"
echo ""
echo "Usage:"
echo "  Connect:   openvpn-connect"
echo "  Disconnect: openvpn-disconnect"
echo "  Status:    openvpn-status"
echo "  Config:    ~/.openvpn/client.ovpn"
echo ""
echo "Add Termux:Widget to home screen for one-tap connect/disconnect"
echo ""
echo "Default Credentials:"
echo "  Username: MHH06"
echo "  Password: S271m31h41"
echo ""
echo "To get full config with certs/keys:"
echo "  Run on server: ovpn-get-ovpn 01-JH"
echo "  Then copy the generated .ovpn to ~/.openvpn/client.ovpn"
EOF
chmod +x /root/openvpn-wizard/openvpn-wizard-termux.sh
ok "Termux script created"