# Changelog

## [1.0.0] - 2026-10-23

### Added
- Complete OpenVPN-over-HAProxy installer with interactive TUI
- SNI-based multiplexing on port 443
- VLESS-TLS + xhttp (2 inbounds with random paths)
- VLESS-Reality + xhttp (stealth mode with X25519)
- OpenVPN with TLS-crypt v1, AES-256-GCM, TLS 1.3 only
- Easy-RSA PKI with RSA-4096 certificates
- PAM authentication for VPN users
- SQLite user management database
- Interactive TUI built with Rich and Textual
- Privacy education screens (what each entity sees/doesn't see)
- Step-by-step confirmation with rollback support
- Live installation progress with live logs
- Client .ovpn profile generation with embedded certificates
- QR code for mobile profile import
- Full user management (add/remove/change password/rename/export/list)
- 11-point post-install validation checklist
- AMD64 and ARM64 architecture support
- Ubuntu 22.04 and 24.04 support
- MIT License
- Quick install script
- Comprehensive documentation

### Changed
- N/A (initial release)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- All private keys stored with 600 permissions
- Services run with least privileges (nobody, nogroup, haproxy)
- IPv6 disabled to prevent leaks
- DNS leak protection built-in
- No telemetry or tracking code

---

## Release Planning

### [1.1.0] (Planned)
- Web GUI for remote management
- API for automated deployment
- Docker support
- Additional OS support (Debian, CentOS)
- WireGuard protocol option
- Two-factor authentication

### [2.0.0] (Planned)
- Complete rewrite with plugin architecture
- Multi-VPS support
- Centralized management dashboard
- Automated certificate renewal (Let's Encrypt)