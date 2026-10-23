# OpenVPN Wizard - Architecture

## Overview

OpenVPN Wizard deploys a hardened OpenVPN server behind HAProxy, multiplexing OpenVPN TCP traffic over port 443 alongside legitimate HTTPS traffic. This provides maximum DPI resistance while maintaining full OpenVPN functionality.

## Component Diagram

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
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Xray/VLESS    │  │  Caddy/Web      │  │   OpenVPN       │
│   Reality       │  │   Server        │  │   Server        │
│   :443 (TLS)    │  │   :80/:443      │  │   :1194 (TCP)   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
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

## Data Flow

### Client → Server (Outbound)
1. Client initiates TCP connection to `vpn.domain.com:443`
2. HAProxy receives connection on port 443
3. HAProxy inspects first packet:
   - **TLS ClientHello** → Routes by SNI to appropriate backend
   - **No TLS** (raw OpenVPN) → Routes to `openvpn_tcp` backend
4. OpenVPN server on `127.0.0.1:1194` receives proxied connection
5. TLS 1.3 handshake with tls-crypt-v2
6. Authentication (user/pass + certificate)
7. Push config: routes, DNS, MTU, cipher
8. Data channel established (AES-256-GCM)
9. Client traffic enters `tun-tcp` interface
10. Kernel routes via `eth0` with MASQUERADE

### Server → Client (Inbound)
1. Internet response arrives at `eth0`
2. Conntrack matches ESTABLISHED/RELATED
2. Forwarded to `tun-tcp` interface
3. OpenVPN encrypts and sends via TCP/443
4. HAProxy passes through (tunnel mode)
5. Client receives and decrypts

## Network Configuration

### IP Addressing
| Component | Network | Interface |
|-----------|---------|-----------|
| VPN Clients | 10.9.0.0/24 | tun-tcp |
| OpenVPN Server | 10.9.0.1 | tun-tcp |
| Docker | 172.17.0.0/16 | docker0 |
| WireGuard | 10.8.0.0/24 | tun-udp/awg0 |
| Physical | 192.209.62.0/24 | eth0 |

### Routing
```bash
# Client routes (pushed by server)
0.0.0.0/1       via 10.9.0.1 dev tun0
128.0.0.0/1     via 10.9.0.1 dev tun0
10.9.0.0/24     dev tun0
192.209.62.112  via 192.209.62.1 dev eth0  # VPN endpoint exception

# Server routes
10.9.0.0/24     dev tun-tcp
10.8.0.0/24     dev tun-udp
172.17.0.0/16   dev docker0
default         via 192.209.62.1 dev eth0
```

### NAT Rules
```bash
# POSTROUTING (outbound from VPN)
iptables -t nat -A POSTROUTING -s 10.9.0.0/24 -o eth0 -j MASQUERADE
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE

# FORWARD (bidirectional)
iptables -A FORWARD -i tun+ -o eth0 -j ACCEPT
iptables -A FORWARD -i eth0 -o tun+ -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i tun+ -o tun+ -j ACCEPT
```

## HAProxy Configuration Details

### Frontend Definitions
| Frontend | Port | Mode | Purpose |
|----------|------|------|---------|
| stats | 8443 | HTTP | HAProxy stats dashboard |
| https_in | 443 | HTTP | Legitimate HTTPS (Xray, Caddy) |
| ovpn_tcp | 443 | TCP | OpenVPN passthrough (non-TLS) |

### Backend Definitions
| Backend | Mode | Servers | Purpose |
|---------|------|---------|---------|
| openvpn_https | HTTP | 127.0.0.1:8080 | HTTPS services |
| openvpn_tcp | TCP | 127.0.0.1:1194 | OpenVPN server |

### SNI Routing Logic
```haproxy
frontend ovpn_tcp
    bind *:443
    mode tcp
    tcp-request inspect-delay 2s
    tcp-request content accept if { req_ssl_hello_type 1 }
    
    # TLS traffic → route by SNI
    use_backend xray_vless   if { req.ssl_sni -i xray.domain.com }
    use_backend web_caddy    if { req.ssl_sni -i web.domain.com }
    
    # Non-TLS → OpenVPN
    use_backend openvpn_tcp  if !{ req_ssl_hello_type 1 }
    
    default_backend openvpn_https
```

## Security Boundaries

### OpenVPN Server Hardening
```
┌─────────────────────────────────────────────────────────────┐
│                    OPENVPN SERVER PROCESS                   │
│  Capabilities: CAP_NET_ADMIN, CAP_NET_BIND_SERVICE,         │
│                CAP_DAC_OVERRIDE, CAP_SETGID, CAP_SETUID    │
│                                                             │
│  Namespaces: Restricted                                     │
│  System Calls: @system-service only                         │
│  Filesystem: ProtectSystem=strict, ProtectHome=yes          │
│  Network: CAP_NET_ADMIN (tun), CAP_NET_BIND_SERVICE (1194) │
└─────────────────────────────────────────────────────────────┘
```

### HAProxy Hardening
```
┌─────────────────────────────────────────────────────────────┐
│                    HAPROXY PROCESS                          │
│  User/Group: haproxy/haproxy                                │
│  Chroot: /var/lib/haproxy                                   │
│  Stats Socket: /run/haproxy/admin.sock (mode 660)          │
│  TLS: TLS 1.2+, secure ciphers only                         │
└─────────────────────────────────────────────────────────────┘
```

### Kernel Parameters
| Parameter | Value | Purpose |
|-----------|-------|---------|
| `net.ipv4.tcp_congestion_control` | `bbr` | Best throughput |
| `net.core.rmem_max` | `67108864` | 64MB receive buffer |
| `net.core.wmem_max` | `67108864` | 64MB send buffer |
| `net.netfilter.nf_conntrack_max` | `1048576` | 1M connections |
| `net.ipv4.tcp_fastopen` | `3` | TFO client+server |
| `net.ipv4.tcp_tw_reuse` | `1` | Fast TIME_WAIT reuse |

## Certificate Hierarchy

```
MHH-VPN-CA (ECDSA/secp384r1, 10yr)
├── Server Certificate (ECDSA/secp384r1, 2.25yr)
│   CN=server
│   EKU: TLS Web Server Authentication
├── Client Certificate: 01-JH (ECDSA/secp384r1, 2.25yr)
│   CN=01-JH
│   EKU: TLS Web Client Authentication
└── CRL (revocation list, 6mo)
```

### tls-crypt-v2 Keys
```
Server Key: tls-crypt-v2-server.key (256-bit)
├── Derives: Control channel encryption keys
└── Client Keys: tls-crypt-v2-01-JH.key (per-client)
```

## Performance Tuning

### OpenVPN
| Parameter | Value | Reason |
|-----------|-------|--------|
| `tun-mtu` | 1500 | Standard Ethernet MTU |
| `mssfix` | 1360 | Prevents fragmentation |
| `sndbuf/rcvbuf` | 524288 | 512KB buffers |
| `txqueuelen` | 1000 | High queue depth |
| `reneg-sec` | 0 | No renegotiation |

### HAProxy
| Parameter | Value | Reason |
|-----------|-------|--------|
| `timeout tunnel` | 86400s | 24h tunnel persistence |
| `maxconn` | 2000000 | High concurrency |
| `nbthread` | 4 | CPU utilization |
| `tune.bufsize` | 16384 | 16KB buffers |

### Kernel
| Parameter | Value | Reason |
|-----------|-------|--------|
| `net.core.somaxconn` | 65535 | Max listen queue |
| `net.ipv4.tcp_max_syn_backlog` | 65535 | SYN flood protection |
| `net.netfilter.nf_conntrack_max` | 1048576 | 1M tracked connections |

## Monitoring Endpoints

| Endpoint | Access | Purpose |
|----------|--------|---------|
| `https://server:8443/stats` | admin/changeme | HAProxy web stats |
| `socat stdio /run/haproxy/admin.sock` | root | HAProxy CLI stats |
| `/var/log/openvpn-status.log` | root | OpenVPN client list |
| `journalctl -u openvpn-server@server` | root | OpenVPN logs |
| `journalctl -u haproxy` | root | HAProxy logs |

## Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| OpenVPN crash | systemd restart | Auto-restart in 10s |
| HAProxy crash | systemd restart | Auto-restart in 10s |
| Kernel OOM | OOM killer | Process limits prevent |
| Port conflict | systemd socket activation | Dependency ordering |
| Cert expiry | CRL + monitoring | Auto-renewal (Let's Encrypt) |