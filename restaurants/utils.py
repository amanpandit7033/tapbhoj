"""
Geofencing utilities for point-in-polygon verification.
"""

def is_point_inside_polygon(lat: float, lng: float, polygon: list) -> bool:
    """
    Check if a coordinate (lat, lng) is inside a polygon using the Ray-Casting algorithm.
    polygon is expected to be a list of dicts with 'lat' and 'lng' keys:
    [{'lat': ..., 'lng': ...}, {'lat': ..., 'lng': ...}, ...]
    """
    if not polygon or len(polygon) < 3:
        return True

    inside = False
    n = len(polygon)
    p1 = polygon[0]

    for i in range(1, n + 1):
        p2 = polygon[i % n]
        try:
            lat1, lng1 = float(p1.get('lat', 0)), float(p1.get('lng', 0))
            lat2, lng2 = float(p2.get('lat', 0)), float(p2.get('lng', 0))

            if min(lng1, lng2) < lng <= max(lng1, lng2):
                if lat <= max(lat1, lat2):
                    if lng1 != lng2:
                        x_inters = (lng - lng1) * (lat2 - lat1) / (lng2 - lng1) + lat1
                    else:
                        x_inters = lat1

                    if lat1 == lat2 or lat <= x_inters:
                        inside = not inside
        except (ValueError, TypeError):
            pass

        p1 = p2

    return inside
