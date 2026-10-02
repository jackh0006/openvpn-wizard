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

# Download config from server
CONFIG_URL="https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/01-JH-192.209.62.112.ovpn"
log "Downloading OpenVPN config..."
if curl -fsSL "$CONFIG_URL" -o ~/.openvpn/client.ovpn; then
    ok "Config downloaded"
else
    warn "Could not download config. Please copy your .ovpn file to ~/.openvpn/client.ovpn manually"
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
echo "Credentials:"
echo "  Username: MHH06"
echo "  Password: S271m31h41"
EOF
chmod +x /root/openvpn-wizard/openvpn-wizard-termux.sh
ok "Termux script created"