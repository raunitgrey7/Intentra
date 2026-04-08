from math import radians, cos, sin, asin, sqrt


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two points.
    """
    R = 6371  # Earth radius in km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))

    return R * c
