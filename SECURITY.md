# SPDX-License-Identifier: MIT
# Security policy — OpenVPN Wizard

Report suspected vulnerabilities privately: open a **security advisory**
on GitHub or email the maintainer (see profile). Include version, impact,
and reproduction steps. Never paste private keys, `.ovpn` contents, or
server credentials. Do not open public issues for vulns.

## Supported versions

| Version | Supported |
| --- | --- |
| Current stable (see Releases) | Yes |
| Older | Best-effort — upgrade and re-test |

## Scope

- ✅ Installer bugs that silently open firewall ports, weaken crypto
  defaults, or leak keys.
- ✅ Defaults that phone home or fetch unverified remote code.
- ❌ The VPS provider seeing your traffic sizes/timing (inherent — see
  `PRIVACY.md`). ❌ OpenVPN upstream flaws (report to OpenVPN).

Threat model + crypto design: [`docs/SECURITY.md`](docs/SECURITY.md).
Needs an independent audit before high-risk reliance.
