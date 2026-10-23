# OpenVPN Wizard - Frequently Asked Questions

## General Questions

### Q: What is OpenVPN Wizard?
**A:** It's an installer that sets up a stealthy, multiplexed VPN on your Ubuntu VPS. It combines OpenVPN, VLESS-TLS, and VLESS-Reality on port 443 using HAProxy SNI routing. It's designed to be easy to use, secure, and private.

### Q: Is it really free?
**A:** Yes, the software is 100% free and open source (MIT license). You only pay for your VPS server (e.g., $5-10/month from a hosting provider).

### Q: Do I need to know networking?
**A:** No. The wizard guides you through every step with explanations. If you can copy and paste, you can use this.

### Q: Is it open source?
**A:** Yes, completely. MIT license. You can read, modify, and distribute the code.

### Q: Do you track users?
**A:** No. Zero tracking, zero telemetry, zero phone-home. Everything stays on your VPS.

---

## Technical Questions

### Q: What protocols does it use?
**A:** Three protocols on port 443:
1. **OpenVPN** (no SNI) — Traditional VPN with TLS-crypt v1
2. **VLESS-TLS + xhttp** (with SNI) — Fast proxy on your domains
3. **VLESS-Reality + xhttp** (with SNI) — Stealth mode mimicking popular websites

### Q: What encryption does it use?
**A:**
- Data: AES-256-GCM
- Authentication: SHA384
- TLS: Version 1.3 only
- Certificates: RSA-4096
- DH: 2048-bit FFDHE
- Reality: X25519

### Q: Can my ISP tell I'm using a VPN?
**A:** No. Your traffic looks like normal HTTPS web browsing on port 443. Your ISP sees only an encrypted connection to your VPS IP.

### Q: Can firewalls block it?
**A:** It's very difficult to block because it uses port 443 (HTTPS) and mimics normal web traffic. VLESS-Reality is specifically designed to be indistinguishable from regular website traffic.

### Q: Does it work on ARM64 (Raspberry Pi)?
**A:** Yes. AMD64 and ARM64 are both fully supported and tested.

### Q: Can I add multiple users?
**A:** Yes. The management menu lets you add, remove, rename, and change passwords for unlimited users.

### Q: Can I use it on Windows/Mac/iOS/Android?
**A:** Yes. The .ovpn profile works with OpenVPN Connect on all major platforms.

---

## Setup Questions

### Q: Do I need a domain name?
**A:** You need three domain names pointing to your VPS IP for the VLESS backends. OpenVPN works without domains (uses IP directly).

### Q: What if I don't have domains?
**A:** You can use any domains you own. For the Reality domain, you can use a popular site like example.com. OpenVPN will still work using your VPS IP directly.

### Q: How long does installation take?
**A:** About 10-15 minutes, mostly depending on your internet speed for package downloads.

### Q: Can I run this on a home server?
**A:** Yes, as long as it runs Ubuntu and has a public IPv4 address with port 443 accessible.

---

## Security Questions

### Q: Is it safe?
**A:** Yes. It uses industry-standard encryption (AES-256-GCM, TLS 1.3, RSA-4096) and follows security best practices (least privilege, secure file permissions, no secrets in code).

### Q: Can you (jackh0006) access my server?
**A:** No. The software runs entirely on your VPS. We never connect to your server, and we never see your data.

### Q: What if I lose my .ovpn file?
**A:** You can regenerate it anytime with `sudo vpn-installer manage` → Export Profile.

### Q: Can I revoke a user's access?
**A:** Yes. Use the management menu to remove a user. Their certificate is revoked and they cannot reconnect.

### Q: Is there a kill switch?
**A:** The OpenVPN config includes `block-outside-dns` and `redirect-gateway` which helps prevent leaks. For a full system kill switch, you would need additional firewall rules.

---

## Billing & Account Questions

### Q: Do I need to create an account?
**A:** No. No email, no registration, no account required.

### Q: Is there a subscription?
**A:** No. The software is free. You only pay your VPS hosting provider.

### Q: Can I use it on multiple VPS?
**A:** Yes. Install it on as many VPS as you like.

---

## Support Questions

### Q: How do I get help?
**A:**
1. Read the documentation in the `docs/` folder
2. Run `sudo vpn-installer validate` to check your installation
3. Check the logs: `sudo journalctl -u haproxy -f`
4. Open a GitHub issue
5. Email: jackh109867@gmail.com

### Q: Will you add feature X?
**A:** Maybe! Open a GitHub issue to request features. Pull requests are welcome.

### Q: Can I contribute?
**A:** Yes! See CONTRIBUTING.md for guidelines.

---

## Miscellaneous

### Q: Why is it called "OpenVPN Wizard"?
**A:** Because it makes setting up OpenVPN feel like magic — you just follow the wizard and everything works.

### Q: Who made this?
**A:** jackh0006 (jackh109867@gmail.com)

### Q: What's the philosophy behind this?
**A:** Privacy is a human right. Everyone should be able to run their own VPN easily, securely, and without being tracked.