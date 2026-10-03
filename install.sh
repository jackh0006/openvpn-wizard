#!/usr/bin/env bash
# OpenVPN Wizard v1.1.0 — Hardened OpenVPN over TCP/443 with HAProxy
# GitHub: https://github.com/Jackh0006/openvpn-wizard
# License: MIT

set -euo pipefail

# ============================================================
# VERSION
# ============================================================
VERSION="1.1.0"

# ============================================================
# CONFIGURATION — EDIT THESE BEFORE RUNNING
# ============================================================
DOMAIN="cf.mhhdns.online"
SERVER_IP="192.209.62.112"
OVPN_PORT="1194"
HAPROXY_HTTP_PORT="80"
HAPROXY_HTTPS_PORT="443"
HAPROXY_STATS_PORT="8443"
OVPN_NETWORK="10.9.0.0/24"
OVPN_SERVER_IP="10.9.0.1"
CLIENT_NAME="01-JH"
USERNAME="MHH06"
PASSWORD="S271m31h41"
CIPHER="AES-256-GCM"
AUTH="SHA256"
TLS_CIPHER="TLS-AES-256-GCM-SHA384:TLS-AES-128-GCM-SHA256:TLS-CHACHA20-POLY1305-SHA256"

# Quick install mode (skip prompts)
QUICK_INSTALL=false

# Colors for beautiful output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[${NC}$(date '+%H:%M:%S')${BLUE}]${NC} $*"; }
ok()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn(){ echo -e "${YELLOW}[!]${NC} $*"; }
err() { echo -e "${RED}[✗]${NC} $*"; }
step(){ echo -e "\n${MAGENTA}▶${NC} ${BOLD}$*${NC}\n"; }
info(){ echo -e "${CYAN}[i]${NC} $*"; }

# Spinner for long operations
spinner() {
    local pid=$1
    local msg=$2
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) % 10 ))
        printf "\r${CYAN}[%c]${NC} %s" "${spin:$i:1}" "$msg"
        sleep 0.1
    done
    printf "\r${GREEN}[✓]${NC} %s\n" "$msg"
}

# Progress bar
progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    printf "\r${CYAN}[${NC}"
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "${CYAN}]${NC} %3d%% (%d/%d)" "$percent" "$current" "$total"
}

# Check root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        err "This script must run as root"
        exit 1
    fi
}

# Detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        err "Cannot detect OS"
        exit 1
    fi
    log "Detected: $PRETTY_NAME"
}

# Quick install mode detection
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick|-q) QUICK_INSTALL=true; shift ;;
            --domain) DOMAIN="$2"; shift 2 ;;
            --ip) SERVER_IP="$2"; shift 2 ;;
            --client) CLIENT_NAME="$2"; shift 2 ;;
            --user) USERNAME="$2"; shift 2 ;;
            --pass) PASSWORD="$2"; shift 2 ;;
            --uninstall) uninstall_all; exit 0 ;;
            --get-ovpn) get_ovpn_file "$2"; exit 0 ;;
            --help|-h) show_help; exit 0 ;;
            *) err "Unknown option: $1"; show_help; exit 1 ;;
        esac
    done
}

show_help() {
    cat <<EOF
OpenVPN Wizard v${VERSION} - Hardened OpenVPN over TCP/443 with HAProxy

Usage: $0 [OPTIONS]

Options:
  --quick, -q              Quick install with defaults (no prompts)
  --domain DOMAIN          Set domain (default: cf.mhhdns.online)
  --ip IP                  Set server IP (default: auto-detect)
  --client NAME            Client name (default: 01-JH)
  --user USER              Username (default: MHH06)
  --pass PASS              Password (default: auto-generated)
  --uninstall              Complete uninstall (clean removal)
  --get-ovpn NAME          Get OVPN file for client
  --help, -h               Show this help

Examples:
  $0 --quick                           # Quick install with defaults
  $0 --domain vpn.example.com --ip 1.2.3.4
  $0 --uninstall                       # Complete clean uninstall
  $0 --get-ovpn 02-JH                  # Get OVPN file for client

Management Commands (after install):
  ovpn-add-client <name>     - Add new client
  ovpn-revoke-client <name>  - Revoke client
  ovpn-list-clients          - List all clients
  ovpn-status                - Show status
  ovpn-get-ovpn <name>       - Get OVPN file with QR code
  ovpn-uninstall             # Complete uninstall
EOF
}

# Uninstall everything
uninstall_all() {
    step "Uninstalling OpenVPN Wizard (Complete Clean Removal)"
    
    # Stop services
    log "Stopping services..."
    systemctl stop openvpn-server@server 2>/dev/null || true
    systemctl stop openvpn-server@warp1194-tcp 2>/dev/null || true
    systemctl stop openvpn-server@warp1194-udp 2>/dev/null || true
    systemctl stop haproxy 2>/dev/null || true
    
    # Disable services
    systemctl disable openvpn-server@server 2>/dev/null || true
    systemctl disable haproxy 2>/dev/null || true
    
    # Remove systemd overrides
    rm -rf /etc/systemd/system/openvpn-server@.service.d
    rm -f /etc/systemd/system/openvpn-client@.service
    systemctl daemon-reload
    
    # Remove packages
    log "Removing packages..."
    apt-get remove -y openvpn easy-rsa haproxy iptables-persistent ufw fail2ban 2>/dev/null || true
    apt-get autoremove -y 2>/dev/null || true
    
    # Remove configs
    log "Removing configurations..."
    rm -rf /etc/openvpn
    rm -rf /etc/haproxy
    rm -rf /etc/openvpn/easy-rsa
    rm -rf /etc/sysctl.d/99-openvpn-wizard.conf
    rm -rf /etc/sysctl.d/99-bbr.conf
    rm -rf /etc/sysctl.d/99-buffers.conf
    
    # Remove firewall rules
    iptables -t nat -D POSTROUTING -s 10.9.0.0/24 -o eth0 -j MASQUERADE 2>/dev/null || true
    iptables -t nat -D POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE 2>/dev/null || true
    iptables -D FORWARD -i tun+ -o eth0 -j ACCEPT 2>/dev/null || true
    iptables -D FORWARD -i eth0 -o tun+ -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
    iptables -D FORWARD -i tun+ -o tun+ -j ACCEPT 2>/dev/null || true
    netfilter-persistent save 2>/dev/null || true
    
    # Remove UFW
    ufw --force reset >/dev/null 2>&1 || true
    ufw --force disable >/dev/null 2>&1 || true
    
    # Remove management scripts
    rm -f /usr/local/bin/ovpn-*
    
    # Remove client configs
    rm -f /root/*.ovpn
    rm -rf /root/.hermes/cache/scratch/*.ovpn
    
    # Remove scripts
    rm -f /root/openvpn-wizard-termux.sh
    rm -f /root/openvpn-wizard-linux.sh
    
    # Remove easy-rsa
    rm -rf /etc/openvpn/easy-rsa
    
    # Remove logs
    rm -f /var/log/openvpn*.log
    rm -f /var/log/openvpn-status.log
    
    ok "Complete uninstall finished. System is clean."
    exit 0
}

# Get OVPN file for client
get_ovpn_file() {
    local client_name="${1:-$CLIENT_NAME}"
    local output_file="/root/${client_name}-${SERVER_IP}.ovpn"
    
    if [[ ! -f "/etc/openvpn/easy-rsa/pki/issued/${client_name}.crt" ]]; then
        err "Client ${client_name} not found. Use 'ovpn-list-clients' to see available clients."
        exit 1
    fi
    
    step "Generating OVPN file for ${client_name}"
    
    cat > "${output_file}" <<EOF
client
dev tun
proto tcp4-client
remote ${SERVER_IP} 443
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
verify-x509-name server name
cipher ${CIPHER}
auth ${AUTH}
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
$(cat /etc/openvpn/easy-rsa/pki/ca.crt)
</ca>

<cert>
$(cat /etc/openvpn/easy-rsa/pki/issued/${client_name}.crt)
</cert>

<key>
$(cat /etc/openvpn/easy-rsa/pki/private/${client_name}.key)
</key>

<tls-crypt-v2>
$(cat /etc/openvpn/server/tls-crypt-v2-${client_name}.key)
</tls-crypt-v2>
EOF

    # Generate QR code for easy mobile import
    if command -v qrencode >/dev/null 2>&1; then
        qrencode -t UTF8 < "${output_file}" 2>/dev/null || true
    fi
    
    ok "OVPN file generated: ${output_file}"
    info "Username: ${USERNAME}"
    info "Password: ${PASSWORD}"
    exit 0
}

# Update system
update_system() {
    step "Updating system packages"
    apt-get update -qq &
    spinner $! "Updating package index"
    apt-get upgrade -y -qq &
    spinner $! "Upgrading packages"
    ok "System updated"
}

# Install dependencies
install_deps() {
    step "Installing dependencies"
    
    # Pre-seed debconf for iptables-persistent to avoid interactive prompts
    echo "iptables-persistent iptables-persistent/autosave_v4 boolean true" | debconf-set-selections
    echo "iptables-persistent iptables-persistent/autosave_v6 boolean true" | debconf-set-selections
    
    local pkgs=(
        openvpn easy-rsa haproxy iptables iptables-persistent
        conntrack net-tools iproute2 curl wget gnupg2
        software-properties-common ca-certificates
        ufw fail2ban logrotate rsyslog qrencode
    )
    apt-get install -y -qq "${pkgs[@]}" &
    spinner $! "Installing packages"
    ok "Dependencies installed"
}

# Configure kernel parameters
configure_kernel() {
    step "Configuring kernel network parameters"
    cat > /etc/sysctl.d/99-openvpn-wizard.conf <<EOF
# OpenVPN Wizard - Network Optimization
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.core.rmem_default = 4194304
net.core.wmem_default = 4194304
net.core.optmem_max = 4194304
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.core.dev_weight = 64

net.ipv4.tcp_rmem = 4096 131072 67108864
net.ipv4.tcp_wmem = 4096 16384 67108864
net.ipv4.udp_rmem_min = 65536
net.ipv4.udp_wmem_min = 65536

net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_notsent_lowat = 16384
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_max_tw_buckets = 2000000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_keepalive_time = 60
net.ipv4.tcp_keepalive_intvl = 10
net.ipv4.tcp_keepalive_probes = 3

net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
net.ipv6.conf.default.forwarding = 1

net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 86400
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 30

fs.file-max = 2097152
fs.nr_open = 1048576

vm.min_free_kbytes = 65536
vm.swappiness = 10
EOF
    sysctl --system -q &
    spinner $! "Applying kernel parameters"
    ok "Kernel configured"
}

# Generate certificates
generate_certs() {
    step "Generating PKI certificates"
    
    local EASYRSA_DIR="/etc/openvpn/easy-rsa"
    make-cadir "$EASYRSA_DIR" 2>/dev/null || true
    cd "$EASYRSA_DIR"
    
    cat > vars <<EOF
set_var EASYRSA_REQ_COUNTRY    "AE"
set_var EASYRSA_REQ_PROVINCE   "Dubai"
set_var EASYRSA_REQ_CITY       "Dubai"
set_var EASYRSA_REQ_ORG        "OpenVPN Wizard"
set_var EASYRSA_REQ_EMAIL      "admin@${DOMAIN}"
set_var EASYRSA_REQ_OU         "VPN"
set_var EASYRSA_KEY_SIZE       384
set_var EASYRSA_ALGO           ec
set_var EASYRSA_CURVE          secp384r1
set_var EASYRSA_CA_EXPIRE      3650
set_var EASYRSA_CERT_EXPIRE    825
set_var EASYRSA_NS_SUPPORT     "no"
set_var EASYRSA_NS_COMMENT     "OpenVPN Wizard Certificate"
EOF

    ./easyrsa --batch init-pki &
    spinner $! "Initializing PKI"
    
    ./easyrsa --batch build-ca nopass &
    spinner $! "Building CA"
    
    ./easyrsa --batch build-server-full server nopass &
    spinner $! "Building server certificate"
    
    ./easyrsa --batch build-client-full "${CLIENT_NAME}" nopass &
    spinner $! "Building client certificate"
    
    ./easyrsa --batch gen-crl &
    spinner $! "Generating CRL"
    
    # tls-crypt-v2 keys
    openvpn --genkey --tls-crypt-v2 /etc/openvpn/server/tls-crypt-v2-server.key &
    spinner $! "Generating tls-crypt-v2 server key"
    
    openvpn --tls-crypt-v2 /etc/openvpn/server/tls-crypt-v2-server.key \
            --genkey --tls-crypt-v2-client /etc/openvpn/server/tls-crypt-v2-${CLIENT_NAME}.key &
    spinner $! "Generating tls-crypt-v2 client key"
    
    # Copy to server directory
    mkdir -p /etc/openvpn/server
    cp pki/ca.crt pki/issued/server.crt pki/private/server.key pki/crl.pem /etc/openvpn/server/
    cp /etc/openvpn/server/tls-crypt-v2-server.key /etc/openvpn/server/tls-crypt-v2-client.key 2>/dev/null || true
    
    chmod 600 /etc/openvpn/server/*.key
    chmod 644 /etc/openvpn/server/*.crt /etc/openvpn/server/crl.pem
    
    ok "Certificates generated"
}

# Configure OpenVPN server
configure_openvpn() {
    step "Configuring OpenVPN server"
    
    mkdir -p /etc/openvpn/server
    
    cat > /etc/openvpn/server/server.conf <<EOF
# OpenVPN Wizard - Hardened Server Config
dev tun
proto tcp-server
port ${OVPN_PORT}
local 0.0.0.0
topology subnet
server ${OVPN_NETWORK}

ca ca.crt
cert server.crt
key server.key
dh none
tls-crypt-v2 tls-crypt-v2-server.key
crl-verify crl.pem

cipher ${CIPHER}
data-ciphers ${CIPHER}:CHACHA20-POLY1305
data-ciphers-fallback ${CIPHER}
auth ${AUTH}

tls-version-min 1.3
tls-ciphersuites ${TLS_CIPHER}

allow-compression no
comp-lzo no
push "comp-lzo no"

keepalive 10 60
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 1.0.0.1"
push "dhcp-option DNS 8.8.8.8"
push "block-outside-dns"
push "block-ipv6"

tun-mtu 1500
mssfix 1360
sndbuf 524288
rcvbuf 524288
txqueuelen 1000

user openvpn
group openvpn
persist-key
persist-tun
status /var/log/openvpn-status.log 10
log-append /var/log/openvpn.log
verb 3
mute 20
reneg-sec 0
client-to-client
duplicate-cn
max-clients 500

# Management interface
management 127.0.0.1 7505
EOF

    # Create systemd override for hardening
    mkdir -p /etc/systemd/system/openvpn-server@.service.d
    cat > /etc/systemd/system/openvpn-server@.service.d/hardening.conf <<EOF
[Service]
# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
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
PrivateDevices=yes
ProtectClock=yes
ProtectProc=invisible
ProcSubset=pid
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_DAC_OVERRIDE CAP_SETGID CAP_SETUID
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
EOF

    systemctl daemon-reload
    systemctl enable openvpn-server@server
    systemctl restart openvpn-server@server &
    spinner $! "Starting OpenVPN server"
    ok "OpenVPN server configured and started"
}

# Configure HAProxy
configure_haproxy() {
    step "Configuring HAProxy"
    
    mkdir -p /etc/haproxy/certs
    
    # Generate self-signed cert for HAProxy stats (replace with Let's Encrypt in production)
    openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
        -keyout /etc/haproxy/certs/haproxy.key \
        -out /etc/haproxy/certs/haproxy.crt \
        -subj "/CN=${DOMAIN}" -batch 2>/dev/null
    cat /etc/haproxy/certs/haproxy.crt /etc/haproxy/certs/haproxy.key > /etc/haproxy/certs/${DOMAIN}.pem
    
    cat > /etc/haproxy/haproxy.cfg <<EOF
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
    stats timeout 30s
    user haproxy
    group haproxy
    daemon
    
    nbproc 1
    nbthread 4
    maxconn 2000000
    tune.ssl.default-dh-param 2048
    tune.bufsize 16384
    tune.maxrewrite 1024
    spread-checks 5
    tune.rcvbuf.client 65536
    tune.rcvbuf.server 65536
    tune.sndbuf.client 65536
    tune.sndbuf.server 65536
    
    ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305
    ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets
    ssl-default-server-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
    ssl-default-server-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
    ssl-default-server-options ssl-min-ver TLSv1.2

defaults
    log global
    mode tcp
    option dontlognull
    option tcp-smart-accept
    option tcp-smart-connect
    timeout connect 3s
    timeout client 86400s
    timeout server 86400s
    timeout tunnel 86400s
    timeout http-request 10s
    timeout http-keep-alive 5s
    timeout check 5s
    retries 3
    maxconn 2000000
    default-server init-addr last,libc,none

# Stats
frontend stats
    bind *:${HAPROXY_STATS_PORT}
    mode http
    stats enable
    stats uri /stats
    stats refresh 10s
    stats auth admin:changeme

# Main HTTPS frontend
frontend https_in
    bind *:${HAPROXY_HTTPS_PORT} ssl crt /etc/haproxy/certs/${DOMAIN}.pem alpn h2,http/1.1
    mode http
    option http-buffer-request
    maxconn 100000
    default_backend openvpn_https

# TCP frontend for OpenVPN (non-TLS passthrough)
frontend ovpn_tcp
    bind *:${HAPROXY_HTTPS_PORT}
    mode tcp
    tcp-request inspect-delay 2s
    tcp-request content accept if { req_ssl_hello_type 1 }
    maxconn 500000
    use_backend openvpn_tcp if !{ req_ssl_hello_type 1 }
    default_backend openvpn_https

# Backends
backend openvpn_https
    mode http
    server localhost 127.0.0.1:8080 check inter 5s rise 2 fall 3

backend openvpn_tcp
    mode tcp
    option tcp-check
    tcp-check connect
    server openvpn 127.0.0.1:${OVPN_PORT} check inter 10s rise 2 fall 3 maxconn 20000
EOF

    systemctl enable haproxy
    systemctl restart haproxy &
    spinner $! "Starting HAProxy"
    ok "HAProxy configured and started"
}

# Configure firewall
configure_firewall() {
    step "Configuring firewall (UFW + iptables)"
    
    ufw --force reset >/dev/null 2>&1
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow ${HAPROXY_HTTP_PORT}/tcp
    ufw allow ${HAPROXY_HTTPS_PORT}/tcp
    ufw allow ${HAPROXY_STATS_PORT}/tcp
    ufw --force enable >/dev/null
    
    # NAT for VPN clients
    iptables -t nat -I POSTROUTING 1 -s ${OVPN_NETWORK} -o eth0 -j MASQUERADE
    iptables -t nat -I POSTROUTING 1 -s 10.8.0.0/24 -o eth0 -j MASQUERADE 2>/dev/null || true
    
    # Forward rules
    iptables -I FORWARD -i tun+ -o eth0 -j ACCEPT
    iptables -I FORWARD -i eth0 -o tun+ -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    iptables -I FORWARD -i tun+ -o tun+ -j ACCEPT
    
    # Save
    netfilter-persistent save &
    spinner $! "Saving firewall rules"
    ok "Firewall configured"
}

# Generate client config
generate_client_config() {
    step "Generating client configuration"
    
    cat > "/root/${CLIENT_NAME}-${SERVER_IP}.ovpn" <<EOF
client
dev tun
proto tcp4-client
remote ${SERVER_IP} 443
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
verify-x509-name server name
cipher ${CIPHER}
auth ${AUTH}
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
$(cat /etc/openvpn/easy-rsa/pki/ca.crt)
</ca>

<cert>
$(cat /etc/openvpn/easy-rsa/pki/issued/${CLIENT_NAME}.crt)
</cert>

<key>
$(cat /etc/openvpn/easy-rsa/pki/private/${CLIENT_NAME}.key)
</key>

<tls-crypt-v2>
$(cat /etc/openvpn/server/tls-crypt-v2-${CLIENT_NAME}.key)
</tls-crypt-v2>
EOF

    cp "/root/${CLIENT_NAME}-${SERVER_IP}.ovpn" "/root/.hermes/cache/scratch/${CLIENT_NAME}-${SERVER_IP}.ovpn" 2>/dev/null || true
    ok "Client config generated: ${CLIENT_NAME}-${SERVER_IP}.ovpn"
}

# Create management scripts
create_management_scripts() {
    step "Creating management scripts"
    
    cat > /usr/local/bin/ovpn-add-client <<'EOF'
#!/usr/bin/env bash
# Add new OpenVPN client
set -euo pipefail
CLIENT_NAME="${1:-}"
[[ -z "$CLIENT_NAME" ]] && { echo "Usage: ovpn-add-client <name>"; exit 1; }
cd /etc/openvpn/easy-rsa
./easyrsa --batch build-client-full "$CLIENT_NAME" nopass
openvpn --tls-crypt-v2 /etc/openvpn/server/tls-crypt-v2-server.key --genkey --tls-crypt-v2-client /etc/openvpn/server/tls-crypt-v2-"$CLIENT_NAME".key
echo "Client $CLIENT_NAME added. Config: /root/${CLIENT_NAME}-$(curl -s ifconfig.me).ovpn"
EOF
    chmod +x /usr/local/bin/ovpn-add-client
    
    cat > /usr/local/bin/ovpn-revoke-client <<'EOF'
#!/usr/bin/env bash
# Revoke OpenVPN client
set -euo pipefail
CLIENT_NAME="${1:-}"
[[ -z "$CLIENT_NAME" ]] && { echo "Usage: ovpn-revoke-client <name>"; exit 1; }
cd /etc/openvpn/easy-rsa
./easyrsa --batch revoke "$CLIENT_NAME"
./easyrsa --batch gen-crl
cp pki/crl.pem /etc/openvpn/server/crl.pem
systemctl reload openvpn-server@server
echo "Client $CLIENT_NAME revoked."
EOF
    chmod +x /usr/local/bin/ovpn-revoke-client
    
    cat > /usr/local/bin/ovpn-list-clients <<'EOF'
#!/usr/bin/env bash
# List all OpenVPN clients
cd /etc/openvpn/easy-rsa
echo "=== Active Clients ==="
ls pki/issued/ | grep -v server | sed 's/.crt$//'
echo ""
echo "=== Revoked Clients ==="
openssl crl -in pki/crl.pem -noout -text | grep "Serial Number" | sed 's/.*Serial Number: //'
EOF
    chmod +x /usr/local/bin/ovpn-list-clients
    
    cat > /usr/local/bin/ovpn-status <<'EOF'
#!/usr/bin/env bash
# Show OpenVPN status
echo "=== OpenVPN Service ==="
systemctl status openvpn-server@server --no-pager | head -20
echo ""
echo "=== Connected Clients ==="
cat /var/log/openvpn-status.log 2>/dev/null | grep -A 100 "CLIENT_LIST" | head -30
echo ""
echo "=== HAProxy Stats ==="
echo "show stat" | socat stdio /run/haproxy/admin.sock 2>/dev/null | grep -E "openvpn|ovpn" | head -10
EOF
    chmod +x /usr/local/bin/ovpn-status
    
    # New: Get OVPN file with QR code
    cat > /usr/local/bin/ovpn-get-ovpn <<'EOF'
#!/usr/bin/env bash
# Get OVPN file for client with QR code
set -euo pipefail
CLIENT_NAME="${1:-}"
[[ -z "$CLIENT_NAME" ]] && { echo "Usage: ovpn-get-ovpn <name>"; exit 1; }

CONFIG_DIR="/etc/openvpn"
SERVER_IP=$(curl -s ifconfig.me)
OUTPUT_FILE="/root/${CLIENT_NAME}-${SERVER_IP}.ovpn"

if [[ ! -f "${CONFIG_DIR}/easy-rsa/pki/issued/${CLIENT_NAME}.crt" ]]; then
    echo "Client ${CLIENT_NAME} not found. Use 'ovpn-list-clients' to see available clients."
    exit 1
fi

cat > "${OUTPUT_FILE}" <<OVPEOF
client
dev tun
proto tcp4-client
remote ${SERVER_IP} 443
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
$(cat /etc/openvpn/easy-rsa/pki/ca.crt)
</ca>

<cert>
$(cat /etc/openvpn/easy-rsa/pki/issued/${CLIENT_NAME}.crt)
</cert>

<key>
$(cat /etc/openvpn/easy-rsa/pki/private/${CLIENT_NAME}.key)
</key>

<tls-crypt-v2>
$(cat /etc/openvpn/server/tls-crypt-v2-${CLIENT_NAME}.key)
</tls-crypt-v2>
OVPEOF

# Generate QR code
if command -v qrencode >/dev/null 2>&1; then
    echo ""
    echo "=== QR Code for Mobile Import ==="
    qrencode -t UTF8 < "${OUTPUT_FILE}" 2>/dev/null || true
fi

echo "OVPN file: ${OUTPUT_FILE}"
echo "Username: $(grep USERNAME /root/openvpn-wizard/config 2>/dev/null | cut -d= -f2 || echo 'MHH06')"
echo "Password: $(grep PASSWORD /root/openvpn-wizard/config 2>/dev/null | cut -d= -f2 || echo 'S271m31h41')"
EOF
    chmod +x /usr/local/bin/ovpn-get-ovpn
    
    # New: Uninstall script
    cat > /usr/local/bin/ovpn-uninstall <<'EOF'
#!/usr/bin/env bash
# Complete uninstall
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/install.sh | sudo bash -s -- --uninstall
EOF
    chmod +x /usr/local/bin/ovpn-uninstall
    
    ok "Management scripts created"
}

# Quick install mode
quick_install() {
    step "Quick Install Mode - Auto-configuring with defaults"
    info "Domain: ${DOMAIN}"
    info "Server IP: ${SERVER_IP}"
    info "Client: ${CLIENT_NAME}"
    info "User: ${USERNAME}"
    info "Password: ${PASSWORD}"
    echo ""
    
    update_system
    install_deps
    configure_kernel
    generate_certs
    configure_openvpn
    configure_haproxy
    configure_firewall
    generate_client_config
    create_management_scripts
    verify_installation
    print_summary
}

# Full interactive install
full_install() {
    step "Interactive Install Mode"
    
    # Auto-detect IP if not set
    if [[ -z "${SERVER_IP}" || "${SERVER_IP}" == "192.209.62.112" ]]; then
        SERVER_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "192.209.62.112")
    fi
    
    # Generate secure password if not set
    if [[ "${PASSWORD}" == "S271m31h41" ]]; then
        PASSWORD=$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-16)
    fi
    
    echo -e "${CYAN}Configuration:${NC}"
    echo "  Domain: ${DOMAIN}"
    echo "  Server IP: ${SERVER_IP}"
    echo "  Client: ${CLIENT_NAME}"
    echo "  Username: ${USERNAME}"
    echo "  Password: ${PASSWORD}"
    echo ""
    
    if [[ "${QUICK_INSTALL}" != "true" ]]; then
        read -p "Continue with these settings? [Y/n] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            err "Installation cancelled"
            exit 1
        fi
    fi
    
    quick_install
}

# Verify installation
verify_installation() {
    step "Verifying installation"
    
    local checks=0
    local passed=0
    
    # OpenVPN
    ((checks++))
    if systemctl is-active --quiet openvpn-server@server; then
        ((passed++))
        ok "OpenVPN server: running"
    else
        err "OpenVPN server: NOT running"
    fi
    
    # HAProxy
    ((checks++))
    if systemctl is-active --quiet haproxy; then
        ((passed++))
        ok "HAProxy: running"
    else
        err "HAProxy: NOT running"
    fi
    
    # Port 443
    ((checks++))
    if ss -tlnp | grep -q ':443.*haproxy'; then
        ((passed++))
        ok "Port 443: listening"
    else
        err "Port 443: NOT listening"
    fi
    
    # Port 1194
    ((checks++))
    if ss -tlnp | grep -q ':1194.*openvpn'; then
        ((passed++))
        ok "Port 1194: listening"
    else
        err "Port 1194: NOT listening"
    fi
    
    # IP forwarding
    ((checks++))
    if [[ $(cat /proc/sys/net/ipv4/ip_forward) -eq 1 ]]; then
        ((passed++))
        ok "IP forwarding: enabled"
    else
        err "IP forwarding: disabled"
    fi
    
    # Client config exists
    ((checks++))
    if [[ -f "/root/${CLIENT_NAME}-${SERVER_IP}.ovpn" ]]; then
        ((passed++))
        ok "Client config: exists"
    else
        err "Client config: missing"
    fi
    
    # Management scripts
    ((checks++))
    if [[ -x /usr/local/bin/ovpn-add-client && -x /usr/local/bin/ovpn-get-ovpn && -x /usr/local/bin/ovpn-uninstall ]]; then
        ((passed++))
        ok "Management scripts: installed"
    else
        err "Management scripts: missing"
    fi
    
    echo ""
    if [[ $passed -eq $checks ]]; then
        ok "All $checks checks passed!"
        return 0
    else
        err "$((checks - passed)) of $checks checks failed"
        return 1
    fi
}

# Print summary
print_summary() {
    echo ""
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC}  ${BOLD}OpenVPN Wizard v${VERSION} - Installation Complete${NC}                    ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}Server:${NC} $SERVER_IP"
    echo -e "${BOLD}Domain:${NC} $DOMAIN"
    echo -e "${BOLD}VPN Network:${NC} $OVPN_NETWORK"
    echo -e "${BOLD}Client:${NC} $CLIENT_NAME"
    echo -e "${BOLD}User/Pass:${NC} $USERNAME / $PASSWORD"
    echo ""
    echo -e "${BOLD}Ports:${NC}"
    echo "  443  → HAProxy (HTTPS + OpenVPN TCP passthrough)"
    echo "  1194 → OpenVPN direct (TCP)"
    echo "  8443 → HAProxy Stats (admin/changeme)"
    echo ""
    echo -e "${BOLD}Client Config:${NC}"
    echo "  /root/${CLIENT_NAME}-${SERVER_IP}.ovpn"
    echo "  /root/.hermes/cache/scratch/${CLIENT_NAME}-${SERVER_IP}.ovpn"
    echo ""
    echo -e "${BOLD}Management Commands:${NC}"
    echo "  ovpn-add-client <name>      - Add new client"
    echo "  ovpn-revoke-client <name>   - Revoke client"
    echo "  ovpn-list-clients           - List all clients"
    echo "  ovpn-status                 - Show status"
    echo "  ovpn-get-ovpn <name>        - Get OVPN file with QR code"
    echo "  ovpn-uninstall              - Complete uninstall"
    echo ""
    echo -e "${BOLD}Termux (Android):${NC}"
    echo "  /root/openvpn-wizard-termux.sh"
    echo ""
    echo -e "${BOLD}Linux Client Auto-Install:${NC}"
    echo "  /root/openvpn-wizard-linux.sh"
    echo ""
    echo -e "${BOLD}Quick Commands:${NC}"
    echo "  Get OVPN:  ovpn-get-ovpn <client-name>"
    echo "  Uninstall: ovpn-uninstall"
    echo ""
    echo -e "${GREEN}Installation complete!${NC} Copy the .ovpn file to your device."
    echo ""
    echo -e "${CYAN}=== QR Code for Mobile Import ===${NC}"
    if command -v qrencode >/dev/null 2>&1; then
        qrencode -t UTF8 < "/root/${CLIENT_NAME}-${SERVER_IP}.ovpn" 2>/dev/null || true
    fi
}

# Main
main() {
    parse_args "$@"
    
    clear
    echo -e "${MAGENTA}"
    cat <<'EOF'
    ██████╗  █████╗ ███████╗███████╗██╗  ██╗███████╗██████╗ 
    ██╔══██╗██╔══██╗██╔════╝██╔════╝██║  ██║██╔════╝██╔══██╗
    ██████╔╝███████║█████╗  █████╗  ███████║█████╗  ██║  ██║
    ██╔══██╗██╔══██║██╔══╝  ██╔══╝  ██╔══██║██╔══╝  ██║  ██║
    ██║  ██║██║  ██║███████╗███████╗██║  ██║███████╗██████╔╝
    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝╚═════╝ 
                                                            
    OpenVPN Wizard v1.1.0 — Hardened TCP/443 over HAProxy
EOF
    echo -e "${NC}"
    
    check_root
    detect_os
    
    if [[ "${QUICK_INSTALL}" == "true" ]]; then
        quick_install
    else
        full_install
    fi
}

main "$@"