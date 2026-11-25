"""
Geofencing utilities for point-in-polygon verification with GPS drift tolerance.
"""
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in meters between two lat/lng coordinates."""
    r = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def distance_to_segment(p_lat: float, p_lng: float, a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    """Approximate distance in meters from point P to line segment AB."""
    # Convert lat/lng to approximate local meters projection
    m_per_deg_lat = 111139.0
    m_per_deg_lng = 111139.0 * math.cos(math.radians(p_lat))

    px = (p_lng - a_lng) * m_per_deg_lng
    py = (p_lat - a_lat) * m_per_deg_lat
    bx = (b_lng - a_lng) * m_per_deg_lng
    by = (b_lat - a_lat) * m_per_deg_lat

    seg_len_sq = bx * bx + by * by
    if seg_len_sq == 0:
        return math.hypot(px, py)

    t = max(0.0, min(1.0, (px * bx + py * by) / seg_len_sq))
    proj_x = t * bx
    proj_y = t * by
    return math.hypot(px - proj_x, py - proj_y)


def is_point_inside_polygon(lat: float, lng: float, polygon: list, tolerance_meters: float = 5.0) -> bool:
    """
    Check if a coordinate (lat, lng) is inside a polygon, or within a tight tolerance buffer (default 5.0m)
    to handle minor indoor smartphone GPS drift without allowing orders outside the premises.
    """
    if not polygon or len(polygon) < 3:
        return True

    clean_poly = []
    for pt in polygon:
        try:
            clean_poly.append((float(pt['lat']), float(pt['lng'])))
        except (ValueError, TypeError, KeyError):
            pass

    if len(clean_poly) < 3:
        return True

    # 1. Standard Ray-Casting algorithm check
    inside = False
    n = len(clean_poly)
    p1_lat, p1_lng = clean_poly[0]

    for i in range(1, n + 1):
        p2_lat, p2_lng = clean_poly[i % n]
        if min(p1_lng, p2_lng) < lng <= max(p1_lng, p2_lng):
            if lat <= max(p1_lat, p2_lat):
                if p1_lng != p2_lng:
                    x_inters = (lng - p1_lng) * (p2_lat - p1_lat) / (p2_lng - p1_lng) + p1_lat
                else:
                    x_inters = p1_lat

                if p1_lat == p2_lat or lat <= x_inters:
                    inside = not inside
        p1_lat, p1_lng = p2_lat, p2_lng

    if inside:
        return True

    # 2. Check if point is within tolerance_meters of any polygon edge (absorbs natural indoor GPS jitter)
    if tolerance_meters > 0:
        for i in range(n):
            a_lat, a_lng = clean_poly[i]
            b_lat, b_lng = clean_poly[(i + 1) % n]
            dist = distance_to_segment(lat, lng, a_lat, a_lng, b_lat, b_lng)
            if dist <= tolerance_meters:
                return True

    return False
