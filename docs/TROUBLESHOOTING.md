# OpenVPN Wizard - Troubleshooting Guide

## Quick Diagnostics

```bash
# Run all checks
ovpn-status

# Or manually:
systemctl status openvpn-server@server
systemctl status haproxy
ss -tlnp | grep -E "443|1194|8443"
iptables -t nat -L POSTROUTING -n -v | grep 10.9
```

---

## Common Issues

### 1. Connection Drops After ~5 Minutes

**Symptoms:** VPN connects, works for ~5 minutes, then drops.

**Cause:** HAProxy default timeouts (300s) kill idle tunnels.

**Fix:**
```bash
grep timeout /etc/haproxy/haproxy.cfg
# Should show:
# timeout client 86400s
# timeout server 86400s
# timeout tunnel 86400s

# Fix:
sed -i 's/timeout client 300s/timeout client 86400s/' /etc/haproxy/haproxy.cfg
sed -i 's/timeout server 300s/timeout server 86400s/' /etc/haproxy/haproxy.cfg
systemctl reload haproxy
```

---

### 2. Connected But No Internet

**Symptoms:** VPN connects, IP shows 10.9.0.x, but no web access.

**Checklist:**
```bash
# 1. IP forwarding
cat /proc/sys/net/ipv4/ip_forward
# Must be 1

# 2. NAT rule exists
iptables -t nat -L POSTROUTING -n -v | grep 10.9
# Should show MASQUERADE rule with packets/bytes

# 3. Forward rules
iptables -L FORWARD -n -v | grep -E "tun|10.9"

# 4. Server can ping
ping -c 2 -I tun-tcp 1.1.1.1

# 5. Client routing
ip route | grep -E "tun0|10.9"
```

**Common Fixes:**
```bash
# Add missing NAT rule
iptables -t nat -I POSTROUTING 1 -s 10.9.0.0/24 -o eth0 -j MASQUERADE

# Add missing forward rules
iptables -I FORWARD -i tun+ -o eth0 -j ACCEPT
iptables -I FORWARD -i eth0 -o tun+ -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Save
netfilter-persistent save
```

---

### 3. Android "Waiting for Server" / Connection Timeout

**Symptoms:** OpenVPN Connect shows "Waiting for server" indefinitely.

**Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| IPv6 DNS resolution | Add `proto tcp4-client` to .ovpn |
| DNS resolves to IPv6 | Ensure domain has only A record |
| HAProxy SNI mismatch | Verify `cf.mhhdns.online` routes to `ovpn-tcp` |
| Port 443 blocked | Test `nc -zv server 443` |

**Force IPv4 in .ovpn:**
```
proto tcp4-client
```

**Verify DNS:**
```bash
dig +short your-domain.com A
dig +short your-domain.com AAAA
# AAAA should be empty
```

---

### 4. "Compression Settings Not Allowed" Error

**Symptoms:** Android shows "server pushed compression settings that are not allowed"

**Cause:** Server pushes `comp-lzo no` but client doesn't support it.

**Fix:** Remove compression push from server:
```bash
sed -i '/push "comp-lzo no"/d' /etc/openvpn/server/server.conf
sed -i '/comp-lzo no/d' /etc/openvpn/server/server.conf
systemctl restart openvpn-server@server
```

Client config should NOT have `comp-lzo` directive.

---

### 5. TLS Handshake Fails

**Symptoms:** `TLS Error: TLS key negotiation failed`

**Checklist:**
```bash
# 1. Certificates valid
openssl x509 -in /etc/openvpn/easy-rsa/pki/issued/server.crt -noout -dates

# 2. CA matches
openssl verify -CAfile /etc/openvpn/easy-rsa/pki/ca.crt /etc/openvpn/easy-rsa/pki/issued/server.crt

# 3. tls-crypt-v2 keys exist
ls -la /etc/openvpn/server/tls-crypt-v2-*.key

# 4. Client cert matches CA
openssl verify -CAfile /etc/openvpn/easy-rsa/pki/ca.crt /etc/openvpn/easy-rsa/pki/issued/01-JH.crt
```

**Common Fixes:**
```bash
# Regenerate tls-crypt-v2 client key
openvpn --tls-crypt-v2 /etc/openvpn/server/tls-crypt-v2-server.key \
        --genkey --tls-crypt-v2-client /etc/openvpn/server/tls-crypt-v2-01-JH.key

# Regenerate client cert
cd /etc/openvpn/easy-rsa
./easyrsa --batch build-client-full 01-JH nopass
```

---

### 6. HAProxy Stats Not Accessible

**Symptoms:** `https://server:8443/stats` returns 404 or connection refused.

**Fixes:**
```bash
# Check HAProxy config
haproxy -c -f /etc/haproxy/haproxy.cfg

# Check stats frontend
grep -A 10 "frontend stats" /etc/haproxy/haproxy.cfg

# Should have:
# frontend stats
#     bind *:8443
#     mode http
#     stats enable
#     stats uri /stats
#     stats auth admin:changeme

# Check service
systemctl status haproxy
journalctl -u haproxy -f
```

---

### 7. Certificate Expired / Expiring Soon

**Check:**
```bash
openssl x509 -in /etc/openvpn/easy-rsa/pki/ca.crt -noout -dates
openssl x509 -in /etc/openvpn/easy-rsa/pki/issued/server.crt -noout -dates
openssl x509 -in /etc/openvpn/easy-rsa/pki/issued/01-JH.crt -noout -dates
```

**Renew Server Cert:**
```bash
cd /etc/openvpn/easy-rsa
./easyrsa --batch renew server
./easyrsa --batch build-server-full server nopass
systemctl reload openvpn-server@server
```

**Renew Client Cert:**
```bash
cd /etc/openvpn/easy-rsa
./easyrsa --batch renew 01-JH
./easyrsa --batch build-client-full 01-JH nopass
# Regenerate client .ovpn
```

---

### 8. Slow Speeds / High Latency

**Checklist:**
```bash
# 1. BBR enabled
sysctl net.ipv4.tcp_congestion_control
# Should be bbr

# 2. Buffer sizes
sysctl net.core.rmem_max net.core.wmem_max
# Should be 67108864

# 3. MTU/MSS
grep -E "tun-mtu|mssfix" /etc/openvpn/server/server.conf
# tun-mtu 1500, mssfix 1360

# 4. Buffer sizes in OpenVPN
grep -E "sndbuf|rcvbuf" /etc/openvpn/server/server.conf
# 524288
```

**Optimize:**
```bash
# Enable BBR
echo "net.ipv4.tcp_congestion_control=bbr" > /etc/sysctl.d/99-bbr.conf
sysctl --system

# Increase buffers
echo "net.core.rmem_max=67108864" > /etc/sysctl.d/99-buffers.conf
echo "net.core.wmem_max=67108864" >> /etc/sysctl.d/99-buffers.conf
sysctl --system
```

---

### 9. Multiple Clients Can't Connect Simultaneously

**Symptoms:** Second client kicks first, or connection refused.

**Cause:** `duplicate-cn` not set, or `max-clients` too low.

**Fix:**
```bash
grep -E "duplicate-cn|max-clients" /etc/openvpn/server/server.conf
# Should have:
# duplicate-cn
# max-clients 500

# Add if missing:
sed -i '/^max-clients/a duplicate-cn' /etc/openvpn/server/server.conf
systemctl restart openvpn-server@server
```

---

### 10. Client Config Not Working on iOS/macOS

**Symptoms:** Import works but connection fails.

**Fixes:**
1. Ensure `auth-user-pass` is in config (not inline)
2. Use `auth-nocache`
3. Remove `explicit-exit-notify` for TCP
4. Use `persist-remote-ip`

**iOS-specific .ovpn additions:**
```
persist-remote-ip
# Remove explicit-exit-notify for TCP
```

---

## Log Analysis

### OpenVPN Logs
```bash
# Real-time
journalctl -u openvpn-server@server -f

# Recent
journalctl -u openvpn-server@server -n 100

# Since boot
journalctl -u openvpn-server@server -b
```

### HAProxy Logs
```bash
# Real-time
journalctl -u haproxy -f

# Stats via socket
echo "show stat" | socat stdio /run/haproxy/admin.sock
```

### Connection Tracking
```bash
# Active connections
conntrack -L -s 10.9.0.0/24

# Count
conntrack -C
```

---

## Debug Mode

### OpenVPN Verbose
```bash
# Edit server.conf
verb 4
# or
verb 5

systemctl restart openvpn-server@server
```

### HAProxy Debug
```bash
# Test config
haproxy -c -f /etc/haproxy/haproxy.cfg

# Debug mode (foreground)
haproxy -f /etc/haproxy/haproxy.cfg -d
```

### Network Debug
```bash
# Capture on tun interface
tcpdump -i tun-tcp -n

# Capture on eth0 for VPN traffic
tcpdump -i eth0 -n "net 10.9.0.0/24"

# Capture HAProxy traffic
tcpdump -i any -n port 443
```

---

## Getting Help

If issues persist:

1. Run `ovpn-status` and share output
2. Share relevant logs: `journalctl -u openvpn-server@server -n 50`
3. Share HAProxy stats: `echo "show stat" | socat stdio /run/haproxy/admin.sock`
4. Include: OS, OpenVPN version (`openvpn --version`), HAProxy version (`haproxy -v`)

GitHub Issues: https://github.com/yourname/openvpn-wizard/issues