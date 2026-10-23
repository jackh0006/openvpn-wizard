#!/usr/bin/env bash
# Quick install script for vpn-installer

set -euo pipefail

echo "🚀 OpenVPN-over-HAProxy Installer - Quick Install"
echo "=================================================="
echo ""

# Check root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Check Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
   echo "⚠️  This installer is designed for Ubuntu. Continue anyway? (y/N)"
   read -r response
   if [[ ! "$response" =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv /opt/vpn-installer
/opt/vpn-installer/bin/pip install --upgrade pip

# Install the package
echo "📥 Installing vpn-installer..."
cd /tmp
if [[ -d vpn-installer ]]; then
    rm -rf vpn-installer
fi
git clone https://github.com/jackh0006/vpn-installer.git
cd vpn-installer
/opt/vpn-installer/bin/pip install -e .

# Create symlink
ln -sf /opt/vpn-installer/bin/vpn-installer /usr/local/bin/vpn-installer

echo ""
echo "✅ Installation complete!"
echo ""
echo "Run the installer:"
echo "  sudo vpn-installer install"
echo ""
echo "Or run management:"
echo "  sudo vpn-installer manage"