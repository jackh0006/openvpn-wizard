# OpenVPN Wizard - Security Policy

## Supported Versions

| Version | Status |
|---------|--------|
| 1.0.x | ✅ Supported |
| < 1.0 | ❌ Not supported |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

**Email:** jackh109867@gmail.com

Please include:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if you have one)
- Your contact information (for credit)

## Our Response Timeline

1. **Acknowledgment:** Within 48 hours
2. **Investigation:** Within 5 business days
3. **Fix Development:** Within 14 days (depending on complexity)
4. **Patch Release:** As soon as the fix is tested
5. **Credit:** You will be credited (if you wish)

## Security Best Practices We Follow

### Cryptography

| Component | Standard | Implementation |
|-----------|----------|---------------|
| Data Encryption | AES-256-GCM | Military-grade |
| Authentication | SHA384 | Strong integrity |
| TLS Version | TLS 1.3 only | Modern, secure |
| TLS Ciphers | TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256 | Best available |
| TLS-Crypt | v1 (pre-shared key) | Extra obfuscation layer |
| Certificates | RSA-4096 | Very strong key size |
| DH Parameters | 2048-bit FFDHE | Forward secrecy |
| Reality Protocol | X25519 + Short IDs | Undetectable handshake |
| Password Hashing | SHA-512 crypt | System standard |

### File Permissions

| File/Directory | Permissions | Owner | Reason |
|---------------|-------------|-------|--------|
| Private keys | 600 | root | Only root can read |
| Certificates | 644 | root | Public, but integrity protected |
| User database | 600 | root | Contains password hashes |
| Client profiles | 600 | root | Contains private keys |
| PKI directory | 700 | root | Restricted access |

### Service Isolation

| Service | User | Group | Network Binding |
|---------|------|-------|-----------------|
| HAProxy | haproxy | haproxy | 0.0.0.0:443 (public) |
| OpenVPN | nobody | nogroup | 127.0.0.1:1194 (local only) |
| 3X-UI | root | root | 127.0.0.1:443, 0.0.0.0:10000,10004 |

### Network Security

- ✅ IPv4 only (no IPv6 leaks)
- ✅ DNS leak protection (block-outside-dns)
- ✅ NAT rules for VPN subnet
- ✅ Firewall rules restrict unnecessary access
- ✅ All non-public services bound to 127.0.0.1

### Code Security

- ✅ No secrets in source code
- ✅ Private keys generated on your machine only
- ✅ All dependencies pinned and hash-verified
- ✅ No telemetry or phone-home code
- ✅ Open source for public inspection

## Responsible Disclosure

We believe in responsible security research. By reporting vulnerabilities to us first:
- You give us time to fix before public disclosure
- You help protect our users
- You receive credit for your discovery
- You avoid potential legal issues

We will not take legal action against researchers who:
- Act in good faith
- Follow this disclosure policy
- Do not access user data without permission
- Do not disrupt service

## Contact

Security issues: jackh109867@gmail.com