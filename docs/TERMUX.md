# OpenVPN Wizard - Termux (Android) Guide

## Prerequisites

- Android 7.0+ (API 24+)
- Termux from F-Droid (not Play Store - outdated)
- Storage permission granted: `termux-setup-storage`
- Root access (Magisk/KernelSU) for full functionality

## Installation

### Method 1: Auto-Install (Recommended)

```bash
# In Termux
curl -fsSL https://your-server.com/openvpn-wizard-termux.sh | bash
```

### Method 2: Manual Install

```bash
# 1. Update packages
pkg update && pkg upgrade -y

# 2. Install dependencies
pkg install -y openvpn openssl curl wget

# 3. Create config directory
mkdir -p ~/.openvpn

# 4. Download config from server
curl -fsSL https://your-server.com/01-JH-192.209.62.112.ovpn -o ~/.openvpn/client.ovpn

# 5. Create shortcuts
mkdir -p ~/.shortcuts

cat > ~/.shortcuts/openvpn-connect <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
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
```

---

## Usage

### Connect
```bash
# Via shortcut (requires Termux:Widget)
openvpn-connect

# Or manually
cd ~/.openvpn
sudo openvpn --config client.ovpn --auth-user-pass <(echo -e "MHH06\nS271m31h41")
```

### Disconnect
```bash
openvpn-disconnect
# Or:
sudo pkill -f "openvpn.*client.ovpn"
```

### Check Status
```bash
# Show interface
ip addr show tun0

# Show routes
ip route | grep tun0

# Test connectivity
ping -c 3 1.1.1.1
curl -s https://api.ipify.org
```

---

## Auto-Connect on Boot

### Termux:Boot (Recommended)

1. Install **Termux:Boot** from F-Droid
2. Create boot script:

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/openvpn-auto <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Auto-connect VPN on boot
sleep 10  # Wait for network
cd ~/.openvpn
sudo openvpn --config client.ovpn --auth-user-pass <(echo -e "MHH06\nS271m31h41") --daemon --log /data/data/com.termux/files/home/.openvpn/openvpn.log
EOF
chmod +x ~/.termux/boot/openvpn-auto
```

### systemd (Root + Termux:API)

```bash
# Requires root + Termux:API
pkg install termux-api

# Create service
cat > ~/.termux/boot/openvpn-service <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-notification --title "OpenVPN" --content "Connecting..." --ongoing
cd ~/.openvpn
sudo openvpn --config client.ovpn --auth-user-pass <(echo -e "MHH06\nS271m31h41") --daemon --log ~/.openvpn/openvpn.log
termux-notification --title "OpenVPN" --content "Connected" --ongoing
EOF
chmod +x ~/.termux/boot/openvpn-service
```

---

## Widget Setup (Termux:Widget)

1. Install **Termux:Widget** from F-Droid
2. Add widget to home screen
3. Select `openvpn-connect` and `openvpn-disconnect`
4. Tap to connect/disconnect

---

## Configuration Tuning

### Android-Specific .ovpn Additions

Add to your `.ovpn`:

```ovpn
# Android optimizations
persist-remote-ip
# Remove explicit-exit-notify for TCP
# auth-nocache prevents password caching
# mute-replay-warnings reduces log spam

# Battery optimization
# Keep screen on while connecting (Termux:API)
# termux-wake-lock before connect
# termux-wake-unlock after connect
```

### Battery Optimization

```bash
# Prevent Doze mode killing VPN
# Settings > Battery > App optimization > Termux > Don't optimize

# Or via ADB
adb shell dumpsys deviceidle whitelist +com.termux
```

---

## Troubleshooting

### "Waiting for Server" / Connection Timeout

```bash
# 1. Force IPv4
proto tcp4-client

# 2. Check DNS
dig +short your-domain.com A
dig +short your-domain.com AAAA  # Should be empty

# 3. Test connectivity
nc -zv your-server.com 443

# 4. Check logs
cat ~/.openvpn/openvpn.log
```

### "Compression Settings Not Allowed"

Remove from server config:
```bash
# On server
sed -i '/comp-lzo/d' /etc/openvpn/server/server.conf
systemctl restart openvpn-server@server
```

### VPN Connects But No Internet

```bash
# Check if tun0 exists
ip addr show tun0

# Check routes
ip route | grep tun0

# Test DNS
nslookup google.com 1.1.1.1

# Check server NAT
# (Run on server)
iptables -t nat -L POSTROUTING -n -v | grep 10.9
```

### Battery Drain

```bash
# Reduce keepalive
keepalive 30 120

# Disable wake lock when not needed
# Use Termux:API for smart wake locks
```

---

## Advanced: Split Tunneling

### Route Only Specific Apps (Requires Root)

```bash
# Route only specific UIDs through VPN
# Requires: iptables, root

# Mark packets from specific app
iptables -t mangle -A OUTPUT -m owner --uid-owner 10123 -j MARK --set-mark 0x1

# Route marked packets through VPN
ip rule add fwmark 0x1 lookup 100
ip route add default dev tun0 table 100
```

### Route Specific Networks Only

```ovpn
# In .ovpn - replace redirect-gateway
# route 10.0.0.0 255.0.0.0
# route 192.168.0.0 255.255.0.0
# route 172.16.0.0 255.240.0.0
```

---

## Logging & Debugging

### Enable Verbose Logging

```bash
# Add to .ovpn
verb 4
log ~/.openvpn/openvpn.log
```

### View Logs

```bash
# Real-time
tail -f ~/.openvpn/openvpn.log

# System logs (requires root)
logcat -s OpenVPN
```

### Debug Connection

```bash
# Test TLS handshake
openssl s_client -connect your-server.com:443 -servername your-domain.com

# Test OpenVPN port
nc -zv your-server.com 443
nc -zv your-server.com 1194
```

---

## Security Hardening

### Termux Hardening

```bash
# Disable unused packages
pkg uninstall nano vim htop  # Keep only needed

# Verify packages
pkg list-installed

# Update regularly
pkg update && pkg upgrade -y
```

### Android Hardening

1. **Disable USB Debugging** when not in use
2. **Lock Termux** with biometric (Termux settings)
3. **Use Strong Password** for sudo
4. **Disable USB Debugging** when not needed
5. **Encrypt Device** (Settings > Security)

### Network Hardening

```bash
# Block IPv6 (already in .ovpn)
# block-ipv6

# Block non-VPN DNS (already in .ovpn)
# block-outside-dns

# Verify no leaks
# https://dnsleaktest.com
# https://ipleak.net
```

---

## Updates

### Update Termux Packages

```bash
pkg update && pkg upgrade -y
```

### Update OpenVPN Config

```bash
# Re-download from server
curl -fsSL https://your-server.com/01-JH-192.209.62.112.ovpn -o ~/.openvpn/client.ovpn
```

### Update Server

```bash
# On server
cd /root/openvpn-wizard
git pull
sudo ./install.sh  # Re-runs with current config
```

---

## FAQ

**Q: Does this work without root?**
A: Yes, for basic connection. Root needed for: systemd service, firewall rules, split tunneling.

**Q: Does this work on Android 14?**
A: Yes, tested on Android 10-14.

**Q: How to change server?**
A: Re-download .ovpn from new server, replace `~/.openvpn/client.ovpn`

**Q: Multiple configs?**
A: Create multiple `.ovpn` files, use different shortcuts.

**Q: Kill switch?**
A: Not built-in. Use `iptables` rules or Android "Always-on VPN" (Settings > Network > VPN).

---

## Support

- Logs: `~/.openvpn/openvpn.log`
- Config: `~/.openvpn/client.ovpn`
- GitHub: https://github.com/yourname/openvpn-wizard/issues