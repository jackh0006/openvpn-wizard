# SPDX-License-Identifier: MIT
# OpenVPN Wizard — Privacy Policy

This installer sets up networking software on **your** server. It collects
nothing for the author.

## What leaves the device during install

- **Public IP discovery** (`ifconfig.me`, fallback `icanhazip.com`): reveals
  your server IP to those services so the installer can write client configs.
  Standard practice; skip by passing your IP explicitly if the installer
  supports `--ip`.
- **Package mirrors** (Ubuntu/Debian `apt`): see your IP + requested packages.
- **Let's Encrypt** (if you enable it): domain validation proves control of
  your domain; certificates are public in Certificate Transparency logs.

## What stays local

- OpenVPN PKI (`easy-rsa` keys/certs), `tls-crypt-v2` keys, client `.ovpn`
  files. Keep `/root/*.ovpn` and PKI `0600`, never commit or paste them.
- No analytics, no telemetry, no phone-home in these scripts
  (`grep -r curl install.sh` shows only IP discovery + documented install URL).

## Operator notes

- Your VPS provider sees VM, traffic sizes/timing, destination IPs of
  tunneled traffic (they always can). A VPN hides content from local
  networks/ISPs, not activity from the provider.
- DPI resistance (TCP/443 + SNI multiplexing + decoy site) raises the cost
  of blocking, it does not make traffic invisible — see README scoreboard.

Questions: open an issue (no secrets, no keys, no `.ovpn` contents).
