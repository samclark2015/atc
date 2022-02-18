import math

R = 3443.92  # Radius of the Earth

def coord_dist(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    return c * R

def coord_bearing(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    lat1r = math.radians(lat1)
    lon1r = math.radians(lon1)
    lat2r = math.radians(lat2)
    lon2r = math.radians(lon2)

    dlon = lon2r - lon1r

    y = math.sin(dlon) * math.cos(lat2r)
    x = math.cos(lat1r) * math.sin(lat2r) - math.sin(lat1r) * math.cos(lat2r) * math.cos(dlon)

    brng = math.degrees(math.atan2(y, x))

    return (brng + 360) % 360

def coord_add(coord, ft, brg):
    lat, lon = coord
    brng = math.radians(brg)  # Bearing is 90 degrees converted to radians.
    d = ft * 0.000164579  # Distance in km

    lat1 = math.radians(lat)  # Current lat point converted to radians
    lon1 = math.radians(lon)  # Current long point converted to radians

    lat2 = math.asin(
        math.sin(lat1) * math.cos(d / R)
        + math.cos(lat1) * math.sin(d / R) * math.cos(brng)
    )

    lon2 = lon1 + math.atan2(
        math.sin(brng) * math.sin(d / R) * math.cos(lat1),
        math.cos(d / R) - math.sin(lat1) * math.sin(lat2),
    )

    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)

    return lat2, lon2
