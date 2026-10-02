#!/usr/bin/env bash
# OpenVPN Wizard - Integration Tests
# Run after installation to verify everything works

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[TEST]${NC} $*"; }
pass() { echo -e "${GREEN}[PASS]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; }

TESTS=0
PASSED=0

run_test() {
    local name="$1"
    local cmd="$2"
    ((TESTS++))
    log "Testing: $name"
    if eval "$cmd" >/dev/null 2>&1; then
        pass "$name"
        ((PASSED++))
        return 0
    else
        fail "$name"
        return 1
    fi
}

echo "=========================================="
echo "OpenVPN Wizard - Integration Tests"
echo "=========================================="
echo ""

# System tests
run_test "OpenVPN service active" "systemctl is-active --quiet openvpn-server@server"
run_test "HAProxy service active" "systemctl is-active --quiet haproxy"
run_test "IP forwarding enabled" "[[ \$(cat /proc/sys/net/ipv4/ip_forward) -eq 1 ]]"

# Port tests
run_test "Port 443 listening (HAProxy)" "ss -tlnp | grep -q ':443.*haproxy'"
run_test "Port 1194 listening (OpenVPN)" "ss -tlnp | grep -q ':1194.*openvpn'"
run_test "Port 8443 listening (Stats)" "ss -tlnp | grep -q ':8443.*haproxy'"

# Config tests
run_test "OpenVPN config valid" "openvpn --config /etc/openvpn/server/server.conf --test-crypto 2>/dev/null"
run_test "HAProxy config valid" "haproxy -c -f /etc/haproxy/haproxy.cfg 2>/dev/null"

# Certificate tests
run_test "CA cert exists" "[[ -f /etc/openvpn/easy-rsa/pki/ca.crt ]]"
run_test "Server cert exists" "[[ -f /etc/openvpn/easy-rsa/pki/issued/server.crt ]]"
run_test "Server key exists" "[[ -f /etc/openvpn/easy-rsa/pki/private/server.key ]]"
run_test "Client cert exists" "[[ -f /etc/openvpn/easy-rsa/pki/issued/01-JH.crt ]]"
run_test "Client key exists" "[[ -f /etc/openvpn/easy-rsa/pki/private/01-JH.key ]]"
run_test "tls-crypt-v2 server key exists" "[[ -f /etc/openvpn/server/tls-crypt-v2-server.key ]]"
run_test "tls-crypt-v2 client key exists" "[[ -f /etc/openvpn/server/tls-crypt-v2-01-JH.key ]]"
run_test "CRL exists" "[[ -f /etc/openvpn/server/crl.pem ]]"

# NAT tests
run_test "NAT rule for VPN" "iptables -t nat -L POSTROUTING -n -v | grep -q '10.9.0.0/24'"

# Forward tests
run_test "Forward rule tun->eth0" "iptables -L FORWARD -n -v | grep -q 'tun.*eth0'"

# Client config
run_test "Client .ovpn exists" "[[ -f /root/01-JH-192.209.62.112.ovpn ]]"

# Management scripts
run_test "ovpn-add-client exists" "[[ -x /usr/local/bin/ovpn-add-client ]]"
run_test "ovpn-revoke-client exists" "[[ -x /usr/local/bin/ovpn-revoke-client ]]"
run_test "ovpn-list-clients exists" "[[ -x /usr/local/bin/ovpn-list-clients ]]"
run_test "ovpn-status exists" "[[ -x /usr/local/bin/ovpn-status ]]"

# Termux script
run_test "Termux script exists" "[[ -f /root/openvpn-wizard-termux.sh && -x /root/openvpn-wizard-termux.sh ]]"

# Linux client script
run_test "Linux client script exists" "[[ -f /root/openvpn-wizard-linux.sh && -x /root/openvpn-wizard-linux.sh ]]"

# Kernel params
run_test "BBR enabled" "[[ \$(sysctl -n net.ipv4.tcp_congestion_control) == 'bbr' ]]"
run_test "Conntrack max >= 1M" "[[ \$(sysctl -n net.netfilter.nf_conntrack_max) -ge 1000000 ]]"

# File permissions
run_test "Server key not world-readable" "[[ \$(stat -c '%a' /etc/openvpn/server/tls-crypt-v2-server.key) == '600' ]]"
run_test "Client keys not world-readable" "[[ \$(stat -c '%a' /etc/openvpn/easy-rsa/pki/private/01-JH.key) == '600' ]]"

echo ""
echo "=========================================="
echo "Results: $PASSED/$TESTS tests passed"
echo "=========================================="

if [[ $PASSED -eq $TESTS ]]; then
    echo -e "\033[0;32mAll tests passed!\033[0m"
    exit 0
else
    echo -e "\033[0;31m$((TESTS - PASSED)) test(s) failed\033[0m"
    exit 1
fi