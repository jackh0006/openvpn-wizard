# OpenVPN Wizard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Ubuntu 22.04+](https://img.shields.io/badge/Ubuntu-22.04+-orange.svg)](https://ubuntu.com/)
[![AMD64 & ARM64](https://img.shields.io/badge/Arch-AMD64%20%7C%20ARM64-green.svg)](https://wiki.ubuntu.com/)

## 🎯 OpenVPN Wizard

The world's easiest, safest, and most secure VPN installer for Linux Ubuntu VPS.

Deploy a stealthy, multiplexed VPN stack on port 443 in minutes — no networking degree required. We teach you everything as we go, with clear explanations and beautiful visuals.

🔒 **Maximum Security** • 🕵️ **Maximum Stealth** • 🎓 **Zero Experience Needed**  
📱 **Works on AMD64 & ARM64** • 🆓 **100% Open Source** • 🚫 **No Tracking**

---

## 📖 What Is This?

Imagine you want to send a secret letter to your friend, but you don't want anyone — not the mailman, not the school, not anyone — to know what's inside the letter or who you're sending it to.

Normally, the mailman (your internet company) can see the address on the envelope. The school (websites you visit) can see where the letter came from.

OpenVPN Wizard puts your letter inside a **magic steel box**. Then it puts that box inside **another box** that looks like a regular pizza delivery box. The mailman sees a pizza delivery — nothing suspicious. Your friend opens both boxes and reads your letter. Nobody in between knows what's inside.

That's what this installer does. It makes your internet traffic look like normal web browsing while actually being your secret VPN.

---

## ✨ What Exactly Does This Do?

| What It Does | How It Helps You |
|-------------|------------------|
| 🎯 Installs on your Ubuntu VPS | You own your VPN — no monthly subscription |
| 🌐 Runs on port 443 (HTTPS) | Looks like normal websites to everyone |
| 🔐 Uses TLS 1.3 + AES-256-GCM | Bank-grade encryption |
| 🕵️ Hides from ISP, DPI, firewalls | They can't tell you're using VPN |
| 👥 Lets you add/remove users | Share with family, friends, team |
| 📱 Works on phone & computer | Any device can connect |
| 📚 Teaches you as you go | No prior knowledge needed |
| 🆓 Completely free & open source | No hidden costs, no tracking |

---

## 🤔 Why You Need This

| Without OpenVPN Wizard | With OpenVPN Wizard |
|----------------------|-------------------|
| Your ISP sees every website you visit | Your ISP sees only encrypted connection to your VPS |
| Websites see your real IP address | Websites see only your VPS IP |
| Firewalls can block VPN traffic | Traffic looks like normal HTTPS browsing |
| You pay monthly for VPN service | You own the server, no subscription |
| Complex setup takes hours | Setup takes minutes with guided UI |
| No control over your data | You control everything |
| VPN providers can log your activity | No logs, no tracking, no phone-home |

---

## 📊 Comparison Table

| Feature | OpenVPN Wizard | Commercial VPN | Other Installers |
|---------|---------------|----------------|------------------|
| **Cost** | Free (you own VPS) | $5-15/month | Usually free |
| **Open Source** | ✅ Yes | ❌ No | Sometimes |
| **No Tracking** | ✅ Yes | ❌ They log you | Varies |
| **Stealth Mode** | ✅ Port 443 + SNI | ❌ Detectable | Rarely |
| **Multi-Protocol** | ✅ OpenVPN + VLESS + Reality | ❌ One protocol | Rarely |
| **User Management** | ✅ Built-in | ❌ Account-based | Rarely |
| **Privacy Education** | ✅ Teach-as-you-go | ❌ None | Rarely |
| **AMD64 + ARM64** | ✅ Both | ✅ Both | Varies |
| **Rollback Support** | ✅ Every step | ❌ None | Rarely |
| **Validation Checks** | ✅ 11 automated tests | ❌ None | Rarely |
| **QR Code Setup** | ✅ Mobile-friendly | ✅ App-based | Rarely |

---

## 🏗️ How It Works (Simple Version)

```
You (Phone/Laptop)
     ↓  Port 443 (looks like regular website)
HAProxy (The Traffic Cop - only thing on public internet)
     ↓  Decides where to send based on website name (SNI)
┌─────────────────────────────────────────────┐
│  No website name → OpenVPN (your secret VPN) │
│  your-domain1.com → VLESS-TLS (fast proxy)   │
│  your-domain2.com → VLESS-TLS (fast proxy)   │
│  popular-site.com → VLESS-Reality (stealth)  │
└─────────────────────────────────────────────┘
     ↓  Everything talks to 127.0.0.1 (private, not public)
```

---

## 🔍 What Each Entity Sees (And Doesn't See)

### 🏠 Your Internet Provider (ISP)

| ✅ SEES | ❌ DOESN'T SEE |
|---------|---------------|
| Encrypted connection to your VPS on port 443 | What websites you visit |
| How much data you use | Your DNS queries |
| When you connect | The actual content of your traffic |
| That you use port 443 (normal HTTPS) | That you're using a VPN |

### 🎯 Deep Packet Inspection (Firewalls, Censorship)

| ✅ SEES | ❌ DOESN'T SEE |
|---------|---------------|
| Standard TLS 1.3 handshake | OpenVPN protocol signatures |
| Packet sizes and timing | VLESS/Reality protocol fingerprints |
| Certificate exchange | Any application data (fully encrypted) |

### 🌐 Websites You Visit

| ✅ SEES | ❌ DOESN'T SEE |
|---------|---------------|
| Your VPS IP address | Your real home IP address |
| Standard browser headers | Your ISP or location |
| Normal TLS connection | That traffic is tunneled |

### 🖥️ Your VPS Provider (Hosting Company)

| ✅ SEES | ❌ DOESN'T SEE |
|---------|---------------|
| Encrypted traffic on port 443 | Your decrypted traffic content |
| Resource usage (CPU, RAM) | Your browsing history |
| Disk space used | Your passwords or keys |

---

## 🖥️ Supported Platforms

| Architecture | Ubuntu 22.04 | Ubuntu 24.04 | Other Ubuntu |
|-------------|-------------|-------------|-------------|
| **AMD64** (Intel/AMD 64-bit) | ✅ Fully Tested | ✅ Fully Tested | ✅ Supported |
| **ARM64** (Raspberry Pi, AWS Graviton, Apple Silicon) | ✅ Fully Tested | ✅ Fully Tested | ✅ Supported |
| **ARM32** (32-bit ARM) | ⚠️ Community Tested | ⚠️ Community Tested | ⚠️ Supported |
| **i386** (32-bit Intel) | ⚠️ Community Tested | ⚠️ Community Tested | ⚠️ Supported |

---

## 🚀 Quick Start (30 Seconds)

```bash
# 1. Clone the repository
git clone https://github.com/jackh0006/OpenVPN-Wizard.git
cd OpenVPN-Wizard

# 2. Run the quick installer
chmod +x quick_install.sh
sudo ./quick_install.sh

# 3. Run the wizard
sudo vpn-installer install
```

---

## 📋 Complete Step-by-Step Guide

### Step 1: Welcome
The wizard greets you with a beautiful screen explaining what we do and why privacy matters. No technical jargon.

### Step 2: Privacy Education
We show you exactly what your ISP, firewalls, websites, and VPS provider can and cannot see — using simple tables and analogies.

### Step 3: Configuration
We ask you for:
- Your VPS IP address
- Admin username and password (for the control panel)
- VPN username and password (for connecting)
- Three domain names you own (for routing different types of traffic)

We validate everything in real-time and explain why each field matters.

### Step 4: Review Each Step
Before we do anything, we show you:
- What this step does
- Why it's needed
- What files will change
- How to undo it if something goes wrong
- How long it takes

You confirm each step before we proceed.

### Step 5: Installation
Watch the progress bar with live logs. You can pause, cancel, or rollback at any time.

### Step 6: Success
You get your .ovpn profile file, a QR code for mobile setup, and instructions on how to connect.

### Step 7: Manage Users
Add, remove, rename, or change passwords for VPN users anytime.

---

## 🔐 Security Standards

| Component | Standard | Implementation |
|-----------|----------|---------------|
| Encryption | AES-256-GCM | Military-grade |
| Authentication | SHA384 | Strong integrity |
| TLS Version | TLS 1.3 only | Modern, secure |
| TLS Ciphers | TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256 | Best available |
| TLS-Crypt | v1 (pre-shared key) | Extra obfuscation |
| Certificates | RSA-4096 | Very strong |
| DH Parameters | 2048-bit FFDHE | Forward secrecy |
| Reality | X25519 + Short IDs | Undetectable |
| Passwords | SHA-512 crypt | System standard |
| File Permissions | 600 (owner only) | Keys protected |

---

## 📜 Policies

### Privacy Policy
- **No tracking:** We never phone home, never send data anywhere
- **No telemetry:** Zero analytics, zero usage reporting
- **No accounts:** No email required, no registration
- **Your data stays on your server:** Nothing leaves your VPS
- **Open source:** You can inspect every line of code

### Security Policy
- **Responsible disclosure:** Report security issues to jackh109867@gmail.com
- **No backdoors:** We promise there are no hidden access points
- **Regular updates:** Security patches released promptly
- **Key protection:** Private keys stored with 600 permissions
- **Memory safety:** Keys exist in memory only, never on disk unencrypted

---

## 🙏 Credits

**Made by jackh0006**  
📧 jackh109867@gmail.com

This installer is dedicated to digital freedom and privacy for everyone.

---

## 🗑️ Removing Other Repositories

If you have other repositories named "OpenVPN Wizard" or similar on your GitHub, please:
1. Navigate to each repository on GitHub
2. Go to Settings → General → Danger Zone → Delete this repository
3. Confirm deletion
4. Keep only this repository as the official OpenVPN Wizard