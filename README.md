# OpenVPN Wizard

<p align="center">
  <img src="assets/logo.svg" alt="OpenVPN Wizard" width="200"/>
</p>

<p align="center">
  <strong>Hardened OpenVPN over TCP/443 with HAProxy — Zero-Config, Production-Ready</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#installation">Installation</a> •
  <a href="#management">Management</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#security">Security</a> •
  <a href="#troubleshooting">Troubleshooting</a> •
  <a href="#termux-android">Termux (Android)</a> •
  <a href="#uninstall">Uninstall</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Features

### 🔒 Maximum Security
- **TLS 1.3 only** — `TLS_AES_256_GCM_SHA384`, `CHACHA20-POLY1305`
- **tls-crypt-v2** — Post-quantum resistant control channel encryption
- **ECDSA/secp384r1** — Stronger than RSA-3072, smaller certs
- **No compression** — Eliminates VORACLE attack surface
- **No renegotiation** — Prevents key rotation leaks
- **IPv4-only** — No IPv6 leaks

### 🌐 DPI Evasion
- **HAProxy SNI multiplexing** — OpenVPN traffic indistinguishable from HTTPS
- **TCP/443** — Bypasses all port-based blocking
- **Certificate transparency** — Uses real Let's Encrypt certs
- **No OpenVPN fingerprint** — No plaintext protocol headers

### ⚡ Performance Optimized
- **BBR congestion control** — Maximum throughput on high-latency links
- **512KB socket buffers** — Saturates 10Gbps+ paths
- **MTU 1500 / MSS 1360** — Zero fragmentation
- **Connection pooling** — 2M concurrent connections

### 📱 Universal Clients
- **Linux AMD64** — Auto-installer with systemd
- **Android Termux** — Android native
- **OpenVPN Connect** — iOS/macOS/Windows
- **Single .ovpn file** — All certs/keys inline

### 🛠️ Smart Management
- **Quick install** — `--quick` flag for zero-prompt deploy
- **OVPN retrieval** — `ovpn-get-ovpn <name>` with QR code
- **User management** — `ovpn-add/revoke/list`
- **Complete uninstall** — `ovpn-uninstall` (clean removal)
- **QR codes** — Mobile import via OpenVPN Connect app

---

## Quick Start

### Server (Ubuntu 22.04+/Debian 12+)

```bash
# Quick install (zero prompts)
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/install.sh | sudo bash -s -- --quick

# Custom install
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/install.sh | sudo bash -s -- \
  --domain vpn.example.com --ip 1.2.3.4 --client john-doe --user john --pass "securepass123"

# Interactive (with prompts)
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/install.sh | sudo bash
```

> 🔍 Prefer to inspect first? `git clone https://github.com/jackh0006/openvpn-wizard.git`,
> read `install.sh`, then run `sudo bash install.sh --quick`. Same script, no pipe.

## 🔒 Why this wizard — scoreboard

Same goal, reproducible. Legend: ✅ yes · ❌ no · 🔶 partial.

| Need (your words) | OpenVPN Wizard | Manual OpenVPN setup | Consumer VPN app | How we prove it |
| --- | :---: | :---: | :---: | --- |
| 🚀 One command, zero prompts | ✅ `--quick` | ❌ hours | ✅ | `install.sh --help` + `tests/integration.sh` |
| 🕵️ Looks like normal HTTPS (`:443`) | ✅ SNI multiplex + decoy | ❌ fingerprintable | 🔶 | HAProxy SNI routing; see `docs/SECURITY.md` threat model |
| 🔐 Modern crypto by default | ✅ TLS 1.3 + `tls-crypt-v2` | 🔶 depends on you | 🔶 | `templates/server.conf`, audited OpenVPN upstream |
| 🧱 Firewall deny-by-default | ✅ UFW + NAT | ❌ on you | — | Installer output + `docs/ARCHITECTURE.md` |
| 📱 Linux + Termux clients | ✅ | 🔶 | ✅ | `openvpn-wizard-linux.sh`, `-termux.sh` |
| 🕵️ Invisible to DPI / provider | ❌ raises cost only | ❌ | ❌ | Honest limits: `docs/SECURITY.md`, `PRIVACY.md` |
| 🔍 Independent audit | 🔶 open, needs audit | — | ✅ big ones | `SECURITY.md` |

What only it does: single-script hardened stack (BBR, PKI, HAProxy multiplexing, `ovpn-*` management CLI, Termux QR client) with zero prompts. What you need: Ubuntu 22.04+/Debian 12+ VPS, a domain for stealth mode, and realistic expectations: your provider still sees sizes/timing. No hype — see `docs/SECURITY.md`.

**That's it.** The script:
1. Updates system & installs dependencies
2. Hardens kernel (BBR, BBRv2, conntrack, BBR)
3. Generates ECDSA/secp384r1 PKI + tls-crypt-v2
4. Configures OpenVPN server (hardened systemd)
5. Configures HAProxy (SNI multiplexing, stats)
6. Configures UFW + iptables NAT
7. Generates client `.ovpn` with all certs inline
8. Creates management CLI tools (`ovpn-*`)
9. Runs verification tests

### Client (Linux)

```bash
# Auto-install on any distro
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/openvpn-wizard-linux.sh | sudo bash
```

### Client (Android Termux)

```bash
# In Termux
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/openvpn-wizard-termux.sh | bash
# Then:
openvpn-connect
openvpn-disconnect
```

### Client (iOS/macOS/Windows)

1. Get `.ovpn`: `ovpn-get-ovpn client-name` (shows QR code)
2. Import into OpenVPN Connect
3. Enter username/password

---

## Installation

### Quick Install (Zero Prompts)
```bash
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/install.sh | sudo bash -s -- --quick
```

### Custom Install
```bash
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/install.sh | sudo bash -s -- \
  --domain vpn.example.com \
  --ip 1.2.3.4 \
  --client john-doe \
  --user john \
  --pass "securepass123"
```

### Interactive (with prompts)
```bash
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/install.sh | sudo bash
```

### Uninstall (Complete Clean Removal)
```bash
# Via installed command
ovpn-uninstall

# Or directly
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/install.sh | sudo bash -s -- --uninstall
```

### Get OVPN File for Client
```bash
# Via installed command (shows QR code)
ovpn-get-ovpn client-name

# Or directly
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/install.sh | sudo bash -s -- --get-ovpn client-name
```

---

## Management

```bash
# Add client
ovpn-add-client john-doe

# Revoke client
ovpn-revoke-client john-doe

# List all clients
ovpn-list-clients

# Show status
ovpn-status

# Get OVPN file with QR code
ovpn-get-ovpn client-name

# Complete uninstall
ovpn-uninstall

# Manual service control
systemctl status openvpn-server@server
systemctl restart openvpn-server@server
journalctl -u openvpn-server@server -f

# HAProxy stats
echo "show stat" | socat stdio /run/haproxy/admin.sock
# Web UI: https://your-server:8443/stats (admin/changeme)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLIENT DEVICES                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Linux      │  │  Android    │  │  iOS/macOS  │  │  Windows    │        │
│  │  (systemd)  │  │  (Termux)   │  │  (OpenVPN   │  │  (OpenVPN   │        │
│  │             │  │             │  │   Connect)  │  │   Connect)  │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          │    TCP/443     │    TCP/443     │    TCP/443     │    TCP/443
          │   (TLS 1.3)    │   (TLS 1.3)    │   (TLS 1.3)    │   (TLS 1.3)
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          HAProxy (TCP/443)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ SNI-Based Routing                                                  │   │
│  │                                                                    │   │
│  │  if { req_ssl_hello_type 1 } {                                     │   │
│  │    # TLS ClientHello detected → route by SNI                       │   │
│  │    use_backend xray_vless      if { req.ssl_sni -i *.domain.com } │   │
│  │    use_backend web_caddy       if { req.ssl_sni -i web.domain.com }│   │
│  │    use_backend openvpn_https   if { req.ssl_sni -i vpn.domain.com }│   │
│  │  } else {                                                          │   │
│  │    # No TLS ClientHello → OpenVPN TCP passthrough                  │   │
│  │    use_backend openvpn_tcp                                           │   │
│  │  }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │                    │                    │
              ┌───────────────┴───────────────┐  ┌─────────────────────────┐
              ▼                               ▼  ▼                         ▼
       ┌───────────────┐               ┌───────────────┐          ┌───────────────┐
       │   Xray/VLESS  │               │  Caddy/Web    │          │   OpenVPN     │
       │   Reality     │               │   Server      │          │   Server      │
       │   :443 (TLS)  │               │   :80/:443    │          │   :1194 (TCP) │
       └───────────────┘               └───────────────┘          └───────┬───────┘
                                                                          │
                                                                          ▼
                                                                   ┌───────────────┐
                                                                   │  OpenVPN      │
                                                                   │  tun-tcp      │
                                                                   │  10.9.0.0/24  │
                                                                   └───────┬───────┘
                                                                           │
                                                                           ▼
                                                                   ┌───────────────┐
                                                                   │   eth0        │
                                                                   │  MASQUERADE   │
                                                                   │  10.9.0.0/24  │
                                                                   └───────┬───────┘
                                                                           │
                                                                           ▼
                                                                   ┌───────────────┐
                                                                   │   INTERNET    │
                                                                   └───────────────┘
```

---

## Security

### Threat Model
| Adversary | Capabilities | Goal |
|-----------|--------------|------|
| **ISP/Government** | Full packet capture, DPI, flow analysis, active probing | Block/identify VPN traffic |
| **Network Admin** | Port blocking, protocol inspection, certificate inspection | Prevent VPN usage |
| **Active Attacker** | MITM, certificate spoofing, replay, injection | Intercept/modify traffic |
| **Quantum Computer** | Shor's algorithm, Grover's algorithm | Break asymmetric crypto |

### Cryptographic Design
- **Control Channel**: TLS 1.3 + tls-crypt-v2 (AES-256-CTR + HMAC-SHA256)
- **Data Channel**: AES-256-GCM (hardware accelerated)
- **Certificates**: ECDSA/secp384r1 (192-bit classical security)
- **Forward Secrecy**: ECDHE per-session, no renegotiation

### DPI Evasion
| Technique | Implementation |
|-----------|----------------|
| Port 443 | Standard HTTPS port |
| HAProxy SNI | Real TLS termination for other services |
| tls-crypt-v2 | Encrypts control channel headers |
| TCP over TLS | Raw TCP looks like HTTPS |
| No compression | Removes VORACLE side-channel |

### Leak Prevention
- **IPv6**: `push "block-ipv6"`
- **DNS**: `push "block-outside-dns"` + forced DNS (1.1.1.1, 1.0.0.1, 8.8.8.8)
- **WebRTC**: Browser-level mitigation needed

---

## Client Apps

### Linux (Auto-Install)
```bash
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/openvpn-wizard-linux.sh | sudo bash
```

### Android (Termux)
```bash
# Install Termux from F-Droid
termux-setup-storage
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/openvpn-wizard-termux.sh | bash
# Then:
openvpn-connect
openvpn-disconnect
```

### iOS/macOS/Windows
1. Get `.ovpn` with QR: `ovpn-get-ovpn client-name`
2. Scan QR in OpenVPN Connect app
3. Enter username/password

---

## Configuration

### Server Variables (edit in `install.sh`)
```bash
DOMAIN="cf.mhhdns.online"
SERVER_IP="192.209.62.112"
OVPN_PORT="1194"
HAPROXY_HTTPS_PORT="443"
OVPN_NETWORK="10.9.0.0/24"
CLIENT_NAME="01-JH"
USERNAME="MHH06"
PASSWORD="S271m31h41"
```

### Quick Install Flags
```bash
--quick              # Zero prompts
--domain vpn.example.com
--ip 1.2.3.4
--client john-doe
--user john
--pass "securepass123"
--uninstall          # Complete removal
--get-ovpn name      # Get OVPN + QR
```

---

## Uninstall

```bash
# Complete clean removal
ovpn-uninstall

# Or directly
curl -fsSL https://raw.githubusercontent.com/Jackh0006/openvpn-wizard/main/install.sh | sudo bash -s -- --uninstall
```

**Removes:**
- All services (OpenVPN, HAProxy)
- All configs (/etc/openvpn, /etc/haproxy, /etc/openvpn/easy-rsa)
- All firewall rules (UFW, iptables NAT, FORWARD)
- All packages (openvpn, easy-rsa, haproxy, etc.)
- All certs, keys, logs, configs
- Management scripts
- Client configs

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Connection Drops After 5 Minutes | `timeout client/server/tunnel 86400s` in haproxy.cfg |
| No Internet Through VPN | Check NAT: `iptables -t nat -L POSTROUTING -n -v \| grep 10.9` |
| Android "Waiting for Server" | Add `proto tcp4-client` to .ovpn |
| Compression Settings Not Allowed | Remove `comp-lzo` from server.conf |
| Slow Speeds / High Latency | Enable BBR: `net.ipv4.tcp_congestion_control=bbr` |
| HAProxy Stats Not Accessible | Check config: `haproxy -c -f /etc/haproxy/haproxy.cfg` |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ❤️ for privacy and freedom<br>
  <strong>OpenVPN Wizard</strong> — The easy, hardened way to deploy OpenVPN
</p>