# OpenVPN Wizard - Privacy Policy

## What We Collect

**Nothing.** Zero. Nada.

We do not collect:
- Your IP address
- Your browsing history
- Your DNS queries
- Your personal information
- Any usage statistics
- Any telemetry data

## What We Send

**Nothing.** The installer never connects to any external server except:

1. **Package repositories (apt)** — To install required software packages on your VPS
2. **Your specified domains** — For SNI-based traffic routing (these are your own domains)

## What We Store

Everything stays on your VPS. Nothing is sent to us or any third party:

| Location | What's Stored |
|----------|--------------|
| `/etc/openvpn/` | VPN configuration, certificates, keys |
| `/etc/openvpn/pki/` | Certificate Authority, server/client certificates |
| `/etc/openvpn/users.db` | User database (encrypted password hashes) |
| `/etc/openvpn/profiles/` | Client .ovpn profile files |
| `/etc/haproxy/` | HAProxy routing configuration |
| `/etc/x-ui/` | 3X-UI panel configuration |

## Third-Party Services

**None.** We do not use:
- Analytics services
- Crash reporting
- Update checking
- Telemetry
- Advertising
- Tracking pixels

## Data Access

Only you (the VPS owner) have access to:
- Your VPN configuration
- Your user database
- Your certificates and keys
- Your traffic logs (if you enable them)

We (jackh0006) never have access to your data, your server, or your traffic.

## Your Rights

You have the right to:
- Inspect all source code (it's open source)
- Modify the software for your needs
- Uninstall at any time
- Delete all data by removing the software
- Export your user data at any time

## Contact

Privacy questions: jackh109867@gmail.com