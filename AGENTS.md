# SPDX-License-Identifier: MIT
# AGENTS.md — AI contributor guide for openvpn-wizard

You touch people's servers and network traffic. Be conservative.

## Hard rules

1. **Never break a working installer.** Shell changes must pass
   `shellcheck -S error` and `bash -n`. Prefer docs over code churn.
2. **No secrets in repo.** No private keys, `.ovpn` contents, API tokens.
   Test with throwaway VMs only.
3. **Honest DPI language.** TCP/443 + SNI multiplexing + decoy raise
   blocking cost; they do not make traffic invisible or anonymous. Never
   `unhackable / invisible / untraceable / NSA-proof`. Keep the README
   scoreboard's proof column accurate.
4. **`curl|bash` stays documented, never hidden.** Any install one-liner
   must sit next to a `git clone` + inspect alternative. Never add new
   remote fetches without checksums.
5. **Fail closed.** Firewall defaults deny; services bind localhost unless
   the operator opts into exposure. Never open ports silently.
6. **Version-proof texts.** No hardcoded versions in README/docs (use
   "current stable" + Releases page). Releases cut only by tag via
   `.github/workflows/release.yml` with canonical asset names.

## Workflow

- Small diffs, `bash -n` + `shellcheck` clean, tests noted.
- End every answer with: files changed, how to verify, open risks.
  If you cannot follow a rule, stop and ask the human.
