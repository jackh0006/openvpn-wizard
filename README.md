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
  <a href="#architecture">Architecture</a> •
  <a href="#management">Management</a> •
  <a href="#security">Security</a> •
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
- **Termux ARM64** — Android native
- **OpenVPN Connect** — iOS/macOS/Windows
- **Single .ovpn file** — All certs/keys inline

---

## Quick Start

### Server (Ubuntu 22.04+/Debian 12+)

```bash
# One-line install
curl -fsSL https://raw.githubusercontent.com/yourname/openvpn-wizard/main/install.sh | sudo bash

# Or clone and run
git clone https://github.com/yourname/openvpn-wizard
cd openvpn-wizard
sudo ./install.sh
```

**That's it.** The script:
1. Updates system & installs dependencies
2. Hardens kernel (BBR, BBRv2, conntrack, BBR)
3. Generates ECDSA/secp384r1 PKI + tls-crypt-v2
4. Configures OpenVPN server (hardened systemd)
5. Configures HAProxy (SNI multiplexing, stats)
6. Configures UFW + iptables NAT
7. Generates client `.ovpn` with all certs inline
8. Creates management CLI tools

### Client (Linux)

```bash
# Auto-install on any distro
curl -fsSL https://your-server.com/openvpn-wizard-linux.sh | sudo bash
```

### Client (Android Termux)

```bash
# In Termux
curl -fsSL https://your-server.com/openvpn-wizard-termux.sh | bash
# Then:
openvpn-connect
openvpn-disconnect
```

### Client (iOS/macOS/Windows)

1. Download `.ovpn` from server: `https://your-server.com/01-JH-192.209.62.112.ovpn`
2. Import into OpenVPN Connect
3. Enter username: `MHH06` / password: `S271m31h41`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET (443)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  HAProxy (TCP/443)                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ SNI Routing                                             │   │
│  │  ├── *.mhhdns.online  → Xray/VLESS Reality             │   │
│  │  ├── cf.mhhdns.online   → OpenVPN TCP (non-TLS)        │   │
│  │  └── default             → Web/Caddy                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       ┌───────────────┐               ┌───────────────┐
       │ OpenVPN TCP   │               │ HAProxy Stats │
       │ 0.0.0.0:1194  │               │    :8443      │
       └───────────────┘               └───────────────┘
              │
              ▼
       ┌───────────────┐
       │  tun-tcp      │
       │ 10.9.0.0/24   │
       └───────────────┘
              │
              ▼
       ┌───────────────┐
       │   eth0        │────► Internet
       │  MASQUERADE   │
       └───────────────┘
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

# Manual service control
systemctl status openvpn-server@server
systemctl restart openvpn-server@server
journalctl -u openvpn-server@server -f

# HAProxy stats
echo "show stat" | socat stdio /run/haproxy/admin.sock
# Web UI: https://your-server:8443/stats (admin/changeme)
```

---

## Security

### Threat Model
| Threat | Mitigation |
|--------|------------|
| Passive DPI | HAProxy SNI + TLS 1.3 + tls-crypt-v2 |
| Active probing | No OpenVPN fingerprint on wire |
| Traffic correlation | Full tunnel, no split DNS |
| Key compromise | tls-crypt-v2, no renegotiation |
| IPv6 leaks | `block-ipv6` + `block-outside-dns` |
| DNS leaks | `block-outside-dns`, forced DNS |
| Quantum | secp384r1 > 128-bit classical security |

### Hardening Applied
- **OpenVPN**: systemd hardening (NoNewPrivileges, ProtectSystem=strict, CAP_DROP)
- **HAProxy**: chroot, user/group, stats socket ACL
- **Kernel**: BBR, conntrack max 1M, rp_filter=2, IP forwarding
- **Firewall**: UFW default-deny, iptables NAT + FORWARD rules

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

### Custom Client Config
```bash
# Add custom options to generated .ovpn
echo "route 10.0.0.0 255.0.0.0" >> /root/01-JH-192.209.62.112.ovpn
```

---

## File Structure

```
openvpn-wizard/
├── install.sh                    # Main installer
├── README.md                     # This file
├── LICENSE                       # MIT
├── scripts/
│   ├── ovpn-add-client           # Add client CLI
│   ├── ovpn-revoke-client        # Revoke client CLI
│   ├── ovpn-list-clients         # List clients CLI
│   └── ovpn-status               # Status CLI
├── templates/
│   ├── server.conf               # OpenVPN server template
│   ├── haproxy.cfg               # HAProxy template
│   ├── client.ovpn               # Client config template
│   └── vars                      # EasyRSA vars
├── systemd/
│   ├── openvpn-hardening.conf    # systemd hardening
│   └── openvpn-client@.service   # Client service
├── docs/
│   ├── ARCHITECTURE.md           # Detailed architecture
│   ├── SECURITY.md               # Security model
│   ├── TROUBLESHOOTING.md        # Common issues
│   └── TERMUX.md                 # Termux guide
├── assets/
│   └── logo.svg                  # Project logo
└── tests/
    └── integration.sh            # CI integration tests
```

---

## Troubleshooting

### Connection Drops After 5 Minutes
```bash
# Check HAProxy timeouts
grep timeout /etc/haproxy/haproxy.cfg
# Should be 86400s for client/server/tunnel
```

### No Internet Through VPN
```bash
# Check NAT
iptables -t nat -L POSTROUTING -n -v | grep 10.9
# Check forwarding
iptables -L FORWARD -n -v | grep tun
```

### Android "Waiting for Server"
```bash
# Force IPv4 only in .ovpn
proto tcp4-client
# Check DNS resolves to IPv4 only
dig +short cf.mhhdns.online A
dig +short cf.mhhdns.online AAAA  # Should be empty
```

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Code Style
- Shell: ShellCheck clean, `set -euo pipefail`
- Templates: Validated with `haproxy -c -f` / `openvpn --config`
- Documentation: Markdown, consistent headers

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [OpenVPN](https://openvpn.net/) — The VPN standard
- [HAProxy](https://www.haproxy.org/) — The load balancer
- [EasyRSA](https://github.com/OpenVPN/easy-rsa) — PKI management
- [tls-crypt-v2](https://github.com/OpenVPN/openvpn/blob/master/src/openvpn/tls_crypt_v2.c) — Post-quantum control channel

---

<p align="center">
  Made with ❤️ for privacy and freedom
</p>