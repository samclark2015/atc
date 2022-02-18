import io
import math
import sqlite3 as sq

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image
from sympy import *
from sympy.geometry import *


def get_points_at_distance(pt: Point, line: Ray2D, d: float):
    angle = float(math.atan(line.slope))
    print(angle)
    x_p = pt.x + d * math.sqrt(1 / (line.slope ** 2 + 1))
    x_m = pt.x - d * math.sqrt(1 / (line.slope ** 2 + 1))

    y_p = pt.y + d * line.slope * math.sqrt(1 / (line.slope ** 2 + 1))
    y_m = pt.y - d * line.slope * math.sqrt(1 / (line.slope ** 2 + 1))

    return (
        (Point(x_m, y_m), Point(x_p, y_p))
        if 1 / 2 * math.pi < angle < 2 / 3 * math.pi
        else (Point(x_p, y_p), Point(x_m, y_m))
    )


def get_bearing(lat1, long1, lat2, long2):
    dLon = long2 - long1
    x = math.cos(math.radians(lat2)) * math.sin(math.radians(dLon))
    y = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.cos(math.radians(dLon))
    brng = np.arctan2(x, y)
    brng = np.degrees(brng)

    return brng


def show(fig):
    buf = io.BytesIO()
    pio.write_image(fig, buf)
    img = Image.open(buf)
    img.show()


def get_star(name, rwy):
    with sq.connect("navdata.sqlite") as conn:
        crs = conn.cursor()
        q = "select distinct ident, lonx, laty from waypoint inner join approach_leg al on ident = al.fix_ident where al.approach_id = (select approach_id from approach where fix_ident = ? and arinc_name = ? and suffix = 'A') ORDER BY al.approach_leg_id ASC "
        return crs.execute(q, (name, rwy)).fetchall()


def get_sid(name, rwy):
    with sq.connect("navdata.sqlite") as conn:
        crs = conn.cursor()
        q = "select distinct ident, lonx, laty from waypoint inner join approach_leg al on ident = al.fix_ident where al.approach_id = (select approach_id from approach where fix_ident = ? and arinc_name = ? and suffix = 'D') ORDER BY al.approach_leg_id ASC "
        return crs.execute(q, (name, rwy)).fetchall()


def wpts_to_points(wpts):
    with sq.connect("navdata.sqlite") as conn:
        crs = conn.cursor()
        q = "select lonx, laty from waypoint where ident = ?"
        return [Point(crs.execute(q, (wpt,)).fetchone()) for wpt in wpts]


def parse_sb_route(dep_rwy, route, arr_rwy):
    legs = []
    segs = route.split(" ")
    for seg in segs:
        print(seg)
        if seg == "DCT":
            continue
        star = get_star(seg, arr_rwy)
        if star:
            legs += star
            continue
        sid = get_sid(seg, dep_rwy)
        if sid:
            legs += sid
            continue
        legs.append(seg)
    print(legs)
    return wpts_to_points(legs)


def calculate_vector(
    pt1: Point, hdg1: float, pt2: Point, hdg2: float, min_dist=5.0, max_dist=10.0
):
    vec = Line2D(pt1, pt2)

    incoming_line: Ray2D = Ray2D(pt1, angle=(math.pi - math.radians(hdg1)))
    final_line: Ray2D = Ray2D(pt2, angle=math.radians(hdg2))

    if -1 / 2 * math.pi <= float(final_line.angle_between(vec)) <= 1 / 2 * math.pi:
        # Already in the right direction
        return vec
    else:
        # We're coming in from an oblique angle
        perp = final_line.perpendicular_line(
            pt2
        )  # Line perpendicular to the final line at the final point
        intersection_points = incoming_line.intersection(perp)
        if intersection_points:
            intersection_point = intersection_points[0]
        else:
            # No intersection point, so we're going to have to use 2 vectors
            intersection_point = None

        if (
            not intersection_point
            or pt2.distance(intersection_point) < min_dist / 60.0
            or pt2.distance(intersection_point) > max_dist / 60.0
        ):
            l = min_dist / 60.0
            i_p, i_m = get_points_at_distance(pt2, perp, l)
            l_p = Ray(pt1, i_p)
            l_m = Ray(pt1, i_m)

            print(incoming_line.closing_angle(l_p), incoming_line.closing_angle(l_m))
            if incoming_line.closing_angle(l_p) > incoming_line.closing_angle(l_m):
                # Choose the leg that requires the least turn
                intersection_point = i_p
            else:
                intersection_point = i_m

            return [Line(pt1, intersection_point), Line(intersection_point, pt2)]


def plot_route(route: str):
    ...


if __name__ == "__main__":
    fig = go.Figure(go.Scattergeo())
    naper, rahnn, rekks = wpts_to_points(["NAPER", "RAHNN", "REKKS"])

    hdg_now = 91
    path = Ray(naper, angle=math.radians(hdg_now))
    pt, _ = get_points_at_distance(naper, path, 10 / 60.0)

    fig.add_scattergeo(
        lon=[float(naper.x), float(pt.x)],
        lat=[float(naper.y), float(pt.y)],
        mode="lines",
        name="path",
    )
    fig.add_scattergeo(
        lon=[float(naper.x)], lat=[float(naper.y)], mode="markers", name="naper"
    )
    fig.add_scattergeo(
        lon=[float(rahnn.x)], lat=[float(rahnn.y)], mode="markers", name="rahnn"
    )
    fig.add_scattergeo(
        lon=[float(rekks.x)], lat=[float(rekks.y)], mode="markers", name="rekks"
    )
    fig.add_scattergeo(
        lon=[float(rahnn.x), float(rekks.x)],
        lat=[float(rahnn.y), float(rekks.y)],
        mode="lines",
        name="final",
    )
    vecs = calculate_vector(Point(naper), hdg_now, Point(rahnn), 45)

    lons = [float(vecs[0].p1.x), float(vecs[0].p2.x)]
    lats = [float(vecs[0].p1.y), float(vecs[0].p2.y)]

    for vec in vecs[1:]:
        lons.append(float(vec.p2.x))
        lats.append(float(vec.p2.y))

    fig.add_scattergeo(
        lon=lons,
        lat=lats,
        mode="lines",
        name="vectors",
    )
    fig.show()
