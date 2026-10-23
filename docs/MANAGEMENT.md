# OpenVPN Wizard - User Management Guide

## Overview

The user management system lets you add, remove, rename, and manage VPN users without reinstalling. Access it anytime:

```bash
sudo vpn-installer manage
```

## User Management Actions

### 1. Add User

Creates a new VPN user with:
- A PAM system account
- A unique client certificate (Easy-RSA)
- A .ovpn profile file with embedded certificates
- A web-downloadable copy

**Steps:**
1. Select `1` (Add User) in the management menu
2. Enter profile name (e.g., `02-Alice`)
3. Enter username (e.g., `alice`)
4. Enter strong password (min 12 characters)
5. Confirm password
6. Download the generated .ovpn profile

### 2. Remove User

Revokes a user's access by:
- Revoking their certificate (Easy-RSA CRL)
- Deleting their PAM user account
- Marking them as revoked in the database
- Removing their .ovpn profile files

**Steps:**
1. Select `2` (Remove User)
2. Choose the user from the list
3. Confirm removal

### 3. Change Password

Changes a user's VPN password:
- Updates PAM password
- Updates password hash in database
- No need to regenerate certificates

**Steps:**
1. Select `3` (Change Password)
2. Choose the user from the list
3. Enter new strong password
4. Confirm new password

### 4. Rename User

Changes a user's profile display name:
- Updates the `name` column in the database
- Renames the .ovpn profile file
- Does NOT change the username or certificate

**Steps:**
1. Select `4` (Rename User)
2. Choose the user from the list
3. Enter new profile name

### 5. Export Profile

Regenerates a user's .ovpn profile file:
- Creates a fresh profile with current certificates
- Saves to `/etc/openvpn/profiles/`
- Copies to `/var/www/vpn-profiles/` for web download

**Steps:**
1. Select `5` (Export Profile)
2. Choose the user from the list
3. Download the profile from the displayed path

### 6. List Users

View all users with their status:
- Active users (green 🟢)
- Revoked users (red 🔴)
- Creation dates
- Usernames

## User Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,           -- Display name
    username TEXT UNIQUE NOT NULL,       -- PAM login name
    password_hash TEXT NOT NULL,         -- SHA-512 crypt hash
    client_cert TEXT,                     -- PEM certificate
    client_key TEXT,                      -- PEM private key
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT 0,           -- 0 = active, 1 = revoked
    cert_serial TEXT                      -- Certificate serial number
);
```

## Security Notes

- Passwords are hashed with SHA-512 crypt (never stored in plain text)
- Private keys are stored with 600 permissions
- Revoked certificates are added to the CRL (Certificate Revocation List)
- OpenVPN automatically reloads the CRL when it changes
- Removed users cannot reconnect even with old .ovpn files

## Example Workflow

```bash
# Add a new family member
sudo vpn-installer manage
# → 1 (Add User)
# → Name: 02-Mom
# → Username: mom
# → Password: StrongPass123!
# → Download: /etc/openvpn/profiles/02-Mom.ovpn

# Later, revoke access
sudo vpn-installer manage
# → 2 (Remove User)
# → Select: 02-Mom
# → Confirm: Yes
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| User not showing | Run `sudo vpn-installer manage` → 6 (List Users) |
| Can't connect after adding | Wait 30 seconds for services to reload |
| Password not working | Ensure PAM user was created correctly |
| Profile download fails | Check nginx is running: `systemctl status nginx` |