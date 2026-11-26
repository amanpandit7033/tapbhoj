"""
Geofencing utilities for point-in-polygon verification with GPS drift tolerance.
"""
import math
import hmac
import hashlib
import base64
from django.conf import settings


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in meters between two lat/lng coordinates."""
    r = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def encode_table_token(restaurant, table_number) -> str:
    """
    Generate an opaque, HMAC-signed token for a restaurant table URL (`?t=...`)
    so customers cannot guess or memorize `?table=1`.
    """
    t_str = str(table_number).strip()
    msg = f"{restaurant.id}:{restaurant.slug}:{t_str}".encode('utf-8')
    sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), msg, hashlib.sha256).hexdigest()[:10]
    payload = f"{t_str}.{sig}".encode('utf-8')
    return base64.urlsafe_b64encode(payload).decode('ascii').rstrip('=')


def decode_table_token(restaurant, token: str) -> str:
    """
    Verify and extract the table_number from an opaque `?t=...` token.
    Returns the verified table_number string, or '' if invalid/tampered.
    """
    if not token:
        return ''
    try:
        clean = token.strip()
        padded = clean + '=' * (-len(clean) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode('ascii')).decode('utf-8')
        t_str, sig = decoded.rsplit('.', 1)
        expected_msg = f"{restaurant.id}:{restaurant.slug}:{t_str}".encode('utf-8')
        expected_sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), expected_msg, hashlib.sha256).hexdigest()[:10]
        if hmac.compare_digest(sig, expected_sig):
            return t_str
    except Exception:
        pass
    return ''
