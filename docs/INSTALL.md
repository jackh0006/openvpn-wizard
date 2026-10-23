# OpenVPN Wizard - Installation Guide

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| Architecture | AMD64 or ARM64 | AMD64 or ARM64 |
| RAM | 512 MB | 1 GB+ |
| CPU | 1 vCPU | 2+ vCPU |
| Disk | 10 GB | 20 GB+ |
| Network | Public IPv4 | Public IPv4 |
| Ports | 443 open | 443, 10000, 10004 open |

## Prerequisites

### 1. Get a VPS
Choose any VPS provider (DigitalOcean, Vultr, Linode, Hetzner, AWS, etc.) and create an Ubuntu 22.04 or 24.04 instance.

### 2. Point Your Domains
You need three domain names pointing to your VPS IP:

| Domain | DNS Record | Points To |
|--------|------------|-----------|
| Domain 1 | A record | Your VPS IP |
| Domain 2 | A record | Your VPS IP |
| Reality Domain | A record | Your VPS IP (or use any popular site) |

### 3. Open Firewall Ports
Ensure these ports are open on your VPS:

| Port | Protocol | Purpose |
|------|----------|---------|
| 22 | TCP | SSH (for management) |
| 443 | TCP | HAProxy (public traffic) |
| 10000 | TCP | VLESS-TLS inbound 1 |
| 10004 | TCP | VLESS-TLS inbound 2 |

## Installation Steps

### Step 1: Clone the Repository

```bash
git clone https://github.com/jackh0006/OpenVPN-Wizard.git
cd OpenVPN-Wizard
```

### Step 2: Run the Quick Installer

```bash
chmod +x quick_install.sh
sudo ./quick_install.sh
```

The quick installer will:
- Install Python 3 and pip
- Create a virtual environment
- Install all dependencies
- Set up the vpn-installer command

### Step 3: Run the Wizard

```bash
sudo vpn-installer install
```

Follow the on-screen prompts. The wizard will guide you through:
1. Welcome screen
2. Privacy education
3. Configuration (IP, passwords, domains)
4. Step-by-step confirmation
5. Installation with progress bar
6. Success with profile download

## Post-Installation

### Verify Installation

```bash
sudo vpn-installer validate
```

### Check Service Status

```bash
systemctl status haproxy openvpn@server x-ui
```

### Download Your Profile

```bash
# From the server
cat /etc/openvpn/profiles/YOUR_PROFILE_NAME.ovpn

# Or download via web
curl http://YOUR_VPS_IP/YOUR_PROFILE_NAME.ovpn -o profile.ovpn
```

## Architecture

```
Internet → Port 443 → HAProxy → SNI Routing → Backends (127.0.0.1)
                                    ├── OpenVPN (1194)
                                    ├── VLESS-TLS (10000)
                                    ├── VLESS-TLS (10004)
                                    └── VLESS-Reality (443 local)
```

## File Locations

| File | Purpose |
|------|---------|
| `/etc/haproxy/haproxy.cfg` | HAProxy configuration |
| `/etc/openvpn/server.conf` | OpenVPN server configuration |
| `/etc/openvpn/pki/` | Certificate authority and keys |
| `/etc/openvpn/users.db` | User database |
| `/etc/openvpn/profiles/*.ovpn` | Client profiles |
| `/etc/x-ui/x-ui.db` | 3X-UI database |
| `/var/www/vpn-profiles/` | Web-downloadable profiles |

## Troubleshooting Installation

| Issue | Solution |
|-------|----------|
| Permission denied | Run with `sudo` |
| Port 443 in use | Stop conflicting services first |
| Domain not resolving | Check DNS A records |
| Package install fails | Run `sudo apt-get update` first |
| 3X-UI not starting | Check `/etc/x-ui/x-ui.db` exists |

## Uninstalling

```bash
sudo vpn-installer uninstall
```

⚠️ This removes all VPN components and cannot be undone.