# OpenVPN Wizard - Security Model

## Threat Model

### Adversaries
| Adversary | Capabilities | Goal |
|-----------|--------------|------|
| **ISP/Government** | Full packet capture, DPI, flow analysis, active probing | Block/identify VPN traffic |
| **Network Admin** | Port blocking, protocol inspection, certificate inspection | Prevent VPN usage |
| **Active Attacker** | MITM, certificate spoofing, replay, injection | Intercept/modify traffic |
| **Quantum Computer** | Shor's algorithm, Grover's algorithm | Break asymmetric crypto |

### Assets Protected
- User identity and location
- Traffic content and metadata
- DNS queries
- Connection timestamps and patterns

---

## Cryptographic Design

### Control Channel (TLS 1.3 + tls-crypt-v2)
```
┌─────────────────────────────────────────────────────────────────┐
│                        TLS 1.3 Handshake                        │
├─────────────────────────────────────────────────────────────────┤
│  Key Exchange:   ECDHE (secp384r1)                             │
│  Authentication: ECDSA (secp384r1)                             │
│  Cipher Suite: TLS_AES_256_GCM_SHA384                          │
│  Cipher Suite: TLS_CHACHA20_POLY1305_SHA256                    │
│  Cipher Suite: TLS_AES_128_GCM_SHA256                          │
├─────────────────────────────────────────────────────────────────┤
│  tls-crypt-v2 (Post-Quantum Resistant Control Channel)         │
│  ├─ Key Derivation: HKDF-SHA256                                │
│  ├─ Encryption:   AES-256-CTR + HMAC-SHA256                    │
│  ├─ Replay Protection: 64-bit sequence numbers                 │
│  └─ Forward Secrecy: Per-session keys via ECDHE                │
└─────────────────────────────────────────────────────────────────┘
```

### Data Channel
```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Channel                             │
├─────────────────────────────────────────────────────────────────┤
│  Cipher: AES-256-GCM (Hardware accelerated on modern CPUs)    │
│  Fallback: CHACHA20-POLY1305 (When AES-NI unavailable)        │
│  Key Derivation: TLS-PRF (from control channel)               │
│  Peer ID: 0 (tls-crypt-v2 mode)                                │
│  IV: 64-bit counter (implicit)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Certificate Hierarchy
```
Root CA (ECDSA/secp384r1)
├── Validity: 10 years
├── Key Usage: Certificate Sign, CRL Sign
└── Extended Key Usage: None (CA only)

Server Cert (ECDSA/secp384r1)
├── Validity: 825 days (Let's Encrypt compatible)
├── Key Usage: Digital Signature, Key Encipherment
├── Extended Key Usage: TLS Web Server Authentication
└── Subject: CN=server

Client Cert (ECDSA/secp384r1)
├── Validity: 825 days
├── Key Usage: Digital Signature
├── Extended Key Usage: TLS Web Client Authentication
└── Subject: CN=<client-name>

CRL
├── Validity: 6 months
├── Algorithm: ECDSA-SHA256
└── Updated on every revocation
```

### Why secp384r1?
| Curve | Classical Security | Quantum Security | Performance |
|-------|-------------------|------------------|-------------|
| secp256r1 | 128-bit | 64-bit | Fastest |
| secp384r1 | 192-bit | 96-bit | Fast |
| secp521r1 | 256-bit | 128-bit | Slower |

**secp384r1** chosen for 192-bit classical security with good performance margin.

---

## DPI Evasion

### Traffic Classification Resistance

| Technique | Implementation | Effectiveness |
|-----------|----------------|---------------|
| **Port 443** | Standard HTTPS port | Bypasses port blocks |
| **HAProxy SNI** | Real TLS termination for other services | Blends with HTTPS |
| **tls-crypt-v2** | Encrypts control channel headers | No OpenVPN fingerprint |
| **TCP over TLS** | Raw TCP looks like HTTPS | Defeats protocol inspection |
| **No compression** | Removes VORACLE side-channel | No length oracle |

### Active Probing Resistance
```
Active Probe          │ Response
──────────────────────┼─────────────────────────────────────────
TLS ClientHello       │ Valid TLS 1.3 ServerHello with cert
HTTP GET /            │ 404 or redirect (via Caddy)
OpenVPN plaintext     │ TCP RST (no listener on raw port)
SSH banner            │ No response (port filtered)
```

---

## Leak Prevention

### IPv6 Leak Prevention
```openvpn
push "block-ipv6"
```
- Client OS disables IPv6 on tunnel interface
- No IPv6 routes pushed
- No IPv6 DNS servers pushed

### DNS Leak Prevention
```openvpn
push "block-outside-dns"
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 1.0.0.1"
push "dhcp-option DNS 8.8.8.8"
```
- Windows: Uses DNS API to block non-tunnel DNS
- Linux/macOS: resolvconf updates /etc/resolv.conf
- Android: Uses VpnService DNS override

### WebRTC Leak Prevention
Not prevented at VPN level. Mitigation:
- Browser: `media.peerconnection.enabled = false`
- Extension: uBlock Origin / WebRTC Control

### Traffic Fingerprinting
| Vector | Mitigation |
|--------|------------|
| Packet timing | TLS record padding (tls-crypt-v2) |
| Packet size | MTU 1500, fixed record sizes |
| Flow duration | Keepalive 10/60 masks idle patterns |
| Byte counts | AES-GCM constant-size records |

---

## Forward Secrecy

### Session Keys
```
Master Secret (from TLS handshake)
    │
    ├── Control Channel Keys (tls-crypt-v2)
    │   ├── Encryption Key (AES-256-CTR)
    │   ├── HMAC Key (SHA256)
    │   └── Replay Protection (64-bit counter)
    │
    └── Data Channel Keys
        ├── Client → Server (AES-256-GCM)
        └── Server → Client (AES-256-GCM)
```

**Key Properties:**
- ECDHE provides forward secrecy
- tls-crypt-v2 keys derived per-session
- No key reuse across sessions
- `reneg-sec 0` prevents key rotation (prevents rollback attacks)

---

## Post-Quantum Considerations

### Current State
| Algorithm | Quantum Risk | Mitigation |
|-----------|--------------|------------|
| ECDSA/secp384r1 | Broken by Shor's | None (classical only) |
| ECDHE/secp384r1 | Broken by Shor's | Ephemeral keys limit exposure |
| AES-256-GCM | Grover's (128-bit) | 256-bit key = 128-bit post-Q |
| SHA256 | Grover's (128-bit) | 256-bit = 128-bit post-Q |
| tls-crypt-v2 AES-256-CTR | Grover's (128-bit) | 256-bit key = 128-bit post-Q |

### Future Migration Path
1. **Hybrid KEM**: Add ML-KEM-768 (Kyber) alongside ECDHE
2. **Hybrid Signatures**: Add ML-DSA-65 (Dilithium) alongside ECDSA
3. **OpenVPN 2.7+**: Supports post-quantum KEMs natively

---

## Compliance

### Standards Alignment
| Standard | Alignment |
|----------|-----------|
| NIST SP 800-52r2 | TLS 1.3 only, approved ciphers |
| NIST SP 800-57 | secp384r1 ≥ 192-bit security |
| RFC 9325 | TLS 1.3, no compression, secure ciphers |
| RFC 9147 | tls-crypt-v2 spec compliance |
| GDPR Art. 32 | Encryption, pseudonymization |

### Audit Checklist
- [ ] TLS 1.3 only (no TLS 1.2 fallback)
- [ ] Certificate validation (CA, SAN, EKU, expiry)
- [ ] tls-crypt-v2 enabled
- [ ] No compression
- [ ] No renegotiation
- [ ] IPv6 blocked
- [ ] DNS forced
- [ ] IPv6 blocked on client
- [ ] DNS leaks tested
- [ ] WebRTC blocked in browser

---

## Incident Response

### Compromise Indicators
| Indicator | Detection | Response |
|-----------|-----------|----------|
| Unknown client in status | `ovpn-list-clients` | Revoke immediately |
| Certificate in CRL | `openssl crl -in crl.pem -text` | Investigate |
| Unusual traffic patterns | HAProxy stats, conntrack | Block IP, rotate certs |
| TLS handshake failures | HAProxy logs | Check cert validity |

### Key Rotation
```bash
# Rotate server cert (annually)
cd /etc/openvpn/easy-rsa
./easyrsa --batch renew server
./easyrsa --batch build-server-full server nopass
systemctl reload openvpn-server@server

# Rotate CA (every 10 years)
./easyrsa --batch build-ca nopass
# Requires full PKI rebuild
```

---

## Security Contacts

- **Security Issues**: security@openvpn-wizard.example.com
- **PGP Key**: Available on GitHub releases
- **Disclosure Policy**: 90-day coordinated disclosure