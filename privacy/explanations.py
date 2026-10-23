"""
Privacy Explanations - Detailed what-each-entity-sees documentation.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class EntityExplanation:
    """Explanation for a single entity."""
    name: str
    icon: str
    description: str
    sees: List[str]
    doesnt_see: List[str]
    technical_details: List[str]
    analogy: str


PRIVACY_EXPLANATIONS = {
    "isp": EntityExplanation(
        name="Your ISP (Internet Service Provider)",
        icon="🏠",
        description="The company providing your internet connection.",
        sees=[
            "Encrypted TLS connection to YOUR VPS IP on port 443",
            "How much data you transfer (volume/bandwidth)",
            "When you connect and for how long (timing/metadata)",
            "That you're using port 443 (standard HTTPS port)",
        ],
        doesnt_see=[
            "What websites you visit (domain names)",
            "Your DNS queries (routed through tunnel to 1.1.1.1/8.8.8.8)",
            "The actual content of your traffic (fully encrypted)",
            "That you're using a VPN (indistinguishable from HTTPS)",
        ],
        technical_details=[
            "SNI is encrypted in TLS 1.3 with ECH (Encrypted Client Hello)",
            "OpenVPN packets are wrapped inside TLS - no VPN signatures on wire",
            "VLESS/Reality traffic mimics standard HTTPS/TLS 1.3",
            "No DPI signature can distinguish this from normal web browsing",
        ],
        analogy="Like mailing a sealed steel box via a courier. The courier (ISP) knows the destination address (VPS IP) and box weight (data volume), but cannot open the box to see what's inside.",
    ),

    "dpi": EntityExplanation(
        name="DPI / Firewalls (Deep Packet Inspection)",
        icon="🎯",
        description="Systems that inspect packet contents to classify/block traffic (GFW, corporate firewalls).",
        sees=[
            "TLS 1.3 ClientHello packet (standard handshake start)",
            "SNI (Server Name Indication) if not using ECH",
            "Packet sizes and timing patterns (statistical analysis)",
            "Certificate exchange (public keys only, no private data)",
        ],
        doesnt_see=[
            "OpenVPN protocol packets (hidden inside TLS record layer)",
            "VLESS / VMess / Trojan / Shadowsocks protocol signatures",
            "Reality handshake (mimics real Cloudflare TLS exactly)",
            "Any application-layer data (fully encrypted after handshake)",
        ],
        technical_details=[
            "TLS 1.3 encrypts almost all handshake after ServerHello",
            "Reality uses X25519 key exchange + short IDs - identical to Cloudflare",
            "xhttp transport makes VLESS look like HTTP/2 traffic on wire",
            "No packet fingerprinting can distinguish from normal web traffic",
            "TLS-crypt v1 adds extra obfuscation layer before TLS",
        ],
        analogy="Like a security guard checking IDs at a building entrance. They see people enter (TLS handshake) but can't read their private conversations inside (encrypted payload).",
    ),

    "website": EntityExplanation(
        name="Websites You Visit",
        icon="🌐",
        description="The destination servers you connect to (Google, GitHub, etc.).",
        sees=[
            "Your VPS IP address as the source (NOT your home IP)",
            "Standard browser headers (we spoof Chrome exactly)",
            "Normal TLS connection to their server",
            "Request paths, headers, cookies (if you send them)",
        ],
        doesnt_see=[
            "Your real home IP address",
            "Your ISP or geographic location",
            "That your traffic is tunneled through a VPN",
            "Any correlation to your real identity",
        ],
        technical_details=[
            "VLESS Reality inbound spoofs Chrome User-Agent and headers exactly",
            "xhttp transport uses realistic paths like /assets/v3/sync",
            "Websites see Cloudflare's IP if using Reality with Cloudflare SNI",
            "No VPN headers or markers in HTTP requests",
        ],
        analogy="Like wearing a perfect mask. The website sees the mask (VPS IP) and hears a normal voice (Chrome headers), but never sees your real face (home IP).",
    ),

    "vps": EntityExplanation(
        name="Your VPS Provider (Hosting Company)",
        icon="🖥️",
        description="The company hosting your VPS (Vultr, DigitalOcean, Hetzner, etc.).",
        sees=[
            "Encrypted traffic on port 443 (volume, timing, connections)",
            "Resource usage: CPU, RAM, disk I/O, network",
            "Config files on disk (but private keys are protected)",
            "System logs (connection counts, errors, service status)",
        ],
        doesnt_see=[
            "Your decrypted traffic content (TLS terminates in memory)",
            "Your browsing history or DNS queries",
            "Your passwords or encryption keys",
            "Client certificates (optionally encrypted at rest)",
        ],
        technical_details=[
            "Private keys stored with 600 permissions, owned by root only",
            "TLS session keys exist only in memory, never written to disk",
            "OpenVPN runs as 'nobody' user, chrooted for isolation",
            "HAProxy runs chrooted in /var/lib/haproxy",
            "3X-UI panel on separate high port (2083) behind auth",
        ],
        analogy="Like a hotel manager. They know which room you're in (VPS) and how much water/electricity you use (resources), but they don't have a key to your room and can't see what you're doing inside.",
    ),
}


def get_entity_explanation(entity: str) -> EntityExplanation:
    """Get explanation for an entity."""
    return PRIVACY_EXPLANATIONS.get(entity)


def get_all_explanations() -> Dict[str, EntityExplanation]:
    """Get all entity explanations."""
    return PRIVACY_EXPLANATIONS