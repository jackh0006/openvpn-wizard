# OpenVPN Wizard - Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### "Permission denied" when running installer
**Solution:** Run with `sudo`:
```bash
sudo vpn-installer install
```

#### "Port 443 already in use"
**Solution:** Stop the conflicting service:
```bash
sudo systemctl stop nginx apache2
sudo vpn-installer install
```

#### Package installation fails
**Solution:** Update package lists first:
```bash
sudo apt-get update
sudo vpn-installer install
```

#### 3X-UI database not found
**Solution:** The 3X-UI installer needs to run first to create the database. The installer handles this automatically.

### Connection Issues

#### Can't connect to VPN
**Checklist:**
1. Is port 443 open on your VPS firewall?
2. Is HAProxy running? `sudo systemctl status haproxy`
3. Is OpenVPN running? `sudo systemctl status openvpn@server`
4. Is your .ovpn profile correct?
5. Are your domain DNS records pointing to your VPS IP?

**Test:**
```bash
# Check if port 443 is reachable
telnet YOUR_VPS_IP 443

# Check HAProxy status
sudo systemctl status haproxy

# Check OpenVPN status
sudo systemctl status openvpn@server
```

#### Slow connection speeds
**Possible causes:**
1. VPS location far from you
2. Server overloaded
3. Encryption overhead
4. ISP throttling

**Solutions:**
1. Choose a VPS closer to your location
2. Try VLESS-TLS protocol instead of OpenVPN
3. Check server resource usage: `top` or `htop`
4. Contact your ISP

#### DNS leaks
**Check:**
1. Visit https://dnsleaktest.com/
2. If it shows your ISP's DNS, you have a leak

**Fix:**
The installer configures `block-outside-dns` and pushes DNS 1.1.1.1 / 8.8.8.8. If you still leak:
```bash
# Check OpenVPN config
grep "dhcp-option" /etc/openvpn/server.conf
# Should show: push "dhcp-option DNS 1.1.1.1" and push "dhcp-option DNS 8.8.8.8"
```

#### IPv6 leaks
**Check:**
1. Visit https://test-ipv6.com/
2. If it shows IPv6 connectivity, you may leak

**Fix:**
The installer disables IPv6 via sysctl. Verify:
```bash
cat /proc/sys/net/ipv6/conf/all/disable_ipv6
# Should return: 1
```

### Service Issues

#### HAProxy won't start
**Diagnosis:**
```bash
sudo systemctl status haproxy
sudo journalctl -u haproxy -n 50
haproxy -c -f /etc/haproxy/haproxy.cfg
```

**Common fixes:**
- Invalid config syntax → Check /etc/haproxy/haproxy.cfg
- Port already in use → Stop conflicting service
- Permission issues → Check file permissions

#### OpenVPN won't start
**Diagnosis:**
```bash
sudo systemctl status openvpn@server
sudo journalctl -u openvpn@server -n 50
openvpn --config /etc/openvpn/server.conf --verb 4 --dry-run
```

**Common fixes:**
- Missing certificates → Re-run PKI step
- Invalid config → Check /etc/openvpn/server.conf
- TUN device missing → `sudo modprobe tun`

#### 3X-UI won't start
**Diagnosis:**
```bash
sudo systemctl status x-ui
sudo journalctl -u x-ui -n 50
```

**Common fixes:**
- Database missing → Re-run X-UI step
- Port conflict → Check ports 10000, 10004, 443

### Profile Issues

#### .ovpn file won't import
**Check:**
1. File has all required sections: `<ca>`, `<cert>`, `<key>`, `<tls-crypt>`
2. File is not corrupted
3. Server IP in file matches your VPS IP

**Fix:**
Regenerate the profile:
```bash
sudo vpn-installer manage
# → 5 (Export Profile)
# → Select your user
```

#### Connected but no internet
**Check:**
1. IPv4 forwarding enabled: `cat /proc/sys/net/ipv4/ip_forward` (should be 1)
2. NAT rules: `iptables -t nat -L POSTROUTING -n -v`
3. Default gateway set correctly

**Fix:**
```bash
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o YOUR_INTERFACE -j MASQUERADE
```

## Getting Help

### Before Opening an Issue

1. Run the validation checklist:
   ```bash
   sudo vpn-installer validate
   ```
2. Check the logs:
   ```bash
   sudo journalctl -u haproxy -n 50
   sudo journalctl -u openvpn@server -n 50
   sudo journalctl -u x-ui -n 50
   ```
3. Search existing GitHub issues

### Opening a GitHub Issue

Include:
- Your Ubuntu version
- Your architecture (AMD64/ARM64)
- What you were trying to do
- What happened (error messages)
- What you expected to happen
- Steps to reproduce

**Email:** jackh109867@gmail.com
**GitHub:** https://github.com/jackh0006/OpenVPN-Wizard/issues