# OpenVPN Wizard - Complete User Guide

Welcome to OpenVPN Wizard! This guide will walk you through everything you need to know, from installation to daily use. We explain everything simply — like we're talking to a friend who's never used a VPN before.

---

## Table of Contents

1. [Before You Start](#before-you-start)
2. [Installation](#installation)
3. [Configuration Walkthrough](#configuration-walkthrough)
4. [Connecting Your Devices](#connecting-your-devices)
5. [Managing Users](#managing-users)
6. [Validation & Troubleshooting](#validation--troubleshooting)
7. [Uninstallation](#uninstallation)

---

## Before You Start

### What You Need

| Item | Why You Need It |
|------|----------------|
| Ubuntu VPS (22.04 or 24.04) | The server that runs your VPN |
| Root access (sudo) | To install software and configure the system |
| Three domain names | For routing different types of traffic (see below) |
| About 10-15 minutes | The wizard guides you through every step |

### Domain Names Explained

You need three domain names pointing to your VPS IP address:

| Domain | Purpose | Example |
|--------|---------|---------|
| Domain 1 | Routes to VLESS-TLS on port 10000 | `vpn1.yourdomain.com` |
| Domain 2 | Routes to VLESS-TLS on port 10004 | `vpn2.yourdomain.com` |
| Reality Domain | Routes to VLESS-Reality (stealth) | `example.com` (any popular site) |

**How to point domains:** Go to your domain registrar's DNS settings and create an "A record" pointing each domain to your VPS IP address.

---

## Installation

### Method 1: Quick Install Script

```bash
# Clone the repository
git clone https://github.com/jackh0006/OpenVPN-Wizard.git
cd OpenVPN-Wizard

# Make the script executable and run it
chmod +x quick_install.sh
sudo ./quick_install.sh
```

### Method 2: Manual Installation

```bash
# Install Python and dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# Clone the repository
git clone https://github.com/jackh0006/OpenVPN-Wizard.git
cd OpenVPN-Wizard

# Create virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Run the installer
sudo vpn-installer install
```

---

## Configuration Walkthrough

### Screen 1: Welcome
You'll see a welcome screen explaining what OpenVPN Wizard does and why privacy matters. Press **1** to continue or **2** to exit.

### Screen 2: Privacy Education
This screen shows you exactly what each entity (ISP, firewalls, websites, VPS provider) can and cannot see. Read through each section to understand how your privacy is protected. Press **1** to continue.

### Screen 3: Configuration
Fill in the following information:

| Field | Description | Example |
|-------|-------------|---------|
| Server IP | Your VPS public IPv4 address | `45.76.80.167` |
| Admin Username | Login for the 3X-UI control panel | `admin` |
| Admin Password | Strong password for the control panel | `MyStr0ngPass!` |
| VPN Username | Your VPN login name | `vpnuser` |
| VPN Password | Strong password for VPN connection | `MyVpnPass!` |
| Client Profile Name | Name shown in your VPN app | `01-JH` |
| Domain 1 | Your first domain (VLESS-TLS) | `vpn1.yourdomain.com` |
| Domain 2 | Your second domain (VLESS-TLS) | `vpn2.yourdomain.com` |
| Reality Domain | Popular site for stealth routing | `example.com` |

### Screen 4: Review Each Step
Before anything is installed, you'll see a list of all 10 installation steps. Each step shows:
- What it does
- Why it's needed
- What files will change
- How to undo it
- How long it takes

Review each step, then press **p** to proceed.

### Screen 5: Installation
Watch the progress bar as each step completes. You'll see live logs. You can pause or cancel at any time.

### Screen 6: Success
You'll receive:
- The path to your .ovpn profile file
- A web download URL
- A QR code (for mobile setup)
- Connection instructions

### Screen 7: Manage Users
You can add, remove, rename, or change passwords for VPN users at any time.

---

## Connecting Your Devices

### Download Your Profile

After installation, your profile is available at:

```
/etc/openvpn/profiles/YOUR_PROFILE_NAME.ovpn
```

Or download from the web:

```
http://YOUR_VPS_IP/YOUR_PROFILE_NAME.ovpn
```

### Connect on Different Devices

#### OpenVPN Connect (iOS/Android)
1. Download OpenVPN Connect from the App Store or Google Play
2. Import your .ovpn profile (scan the QR code or download the file)
3. Enter your VPN username and password
4. Tap Connect

#### OpenVPN GUI (Windows)
1. Download and install OpenVPN GUI
2. Copy your .ovpn file to `C:\Program Files\OpenVPN\config\`
3. Right-click the OpenVPN GUI icon → Connect
4. Enter your VPN username and password

#### TunnelBlick (Mac)
1. Download and install Tunnelblick
2. Double-click your .ovpn file to import
3. Click Connect in the Tunnelblick menu

#### Linux (Command Line)
```bash
sudo apt-get install openvpn
sudo openvpn --config your-profile.ovpn
# Enter username and password when prompted
```

### Verify Your Connection

After connecting, run these commands to verify:

```bash
# Check your public IP (should show your VPS IP, not your home IP)
curl ifconfig.me

# Test website access
curl -I https://example.com

# Check for DNS leaks
curl https://dnsleaktest.com/
```

---

## Managing Users

Run the management menu anytime:

```bash
sudo vpn-installer manage
```

### Available Actions

| Action | What It Does |
|--------|-------------|
| ➕ Add User | Create a new VPN user with certificate and profile |
| 🗑️ Remove User | Revoke a user's certificate and remove their access |
| 🔑 Change Password | Change a user's VPN password |
| ✏️ Rename | Change a user's profile display name |
| 📄 Export Profile | Regenerate/download a user's .ovpn file |
| 🔄 Refresh | Reload the user list |
| 🔙 Back | Return to main menu |

### Adding a New User

1. Run `sudo vpn-installer manage`
2. Select **1** (Add User)
3. Enter a profile name (e.g., `02-Alice`)
4. Enter a username (e.g., `alice`)
5. Enter a strong password (min 12 chars)
6. Confirm the password
7. Download the generated .ovpn profile

---

## Validation & Troubleshooting

### Run Validation

```bash
sudo vpn-installer validate
```

This checks 11 different things:
- HAProxy listening on port 443
- OpenVPN listening on 127.0.0.1:1194
- All VLESS inbounds active
- IPv4 forwarding enabled
- NAT rules configured
- OpenVPN config syntax valid
- Client profile exists and is complete
- Tunnel settings correct
- DNS leak protection active
- IPv6 disabled
- More...

### Common Issues

| Problem | Solution |
|---------|----------|
| Can't connect | Check that port 443 is open in your VPS firewall |
| Slow speeds | Try a different domain or protocol |
| DNS leaks | Ensure "block-outside-dns" is in your config |
| Profile won't import | Make sure the .ovpn file has all certificate sections |
| Services not running | Run `sudo systemctl status haproxy openvpn@server x-ui` |

### View Logs

```bash
# OpenVPN logs
sudo journalctl -u openvpn@server -f

# HAProxy logs
sudo journalctl -u haproxy -f

# 3X-UI logs
sudo journalctl -u x-ui -f
```

---

## Uninstallation

```bash
sudo vpn-installer uninstall
```

⚠️ **Warning:** This removes all VPN components and cannot be undone. Back up your data first.

---

## 📞 Support

- **Email:** jackh109867@gmail.com
- **Issues:** Open a GitHub issue at https://github.com/jackh0006/OpenVPN-Wizard/issues
- **Documentation:** https://github.com/jackh0006/OpenVPN-Wizard/docs

---

*Made with ❤️ by jackh0006 for digital freedom and privacy.*