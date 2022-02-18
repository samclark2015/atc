import importlib.resources as rsc
import sqlite3 as sql

from . import resources


class MyRow(sql.Row):
    def __str__(self):
        return str(dict(self))

    def __repr__(self):
        return str(self)


with rsc.path(resources, "navdata.sqlite") as path:
    conn = sql.connect(path, check_same_thread=False)
    conn.row_factory = MyRow


def get_runways(airport: str):
    q = "select runway_end.*, runway.length from runway_end inner join runway on primary_end_id = runway_end_id or secondary_end_id = runway_end_id inner join airport on runway.airport_id = airport.airport_id where icao = ? and has_closed_markings != 1"
    return conn.execute(q, (airport,)).fetchall()


def get_sid_star(name, rwy):
    q = "select distinct ident, lonx, laty, alt_descriptor, altitude1, altitude2 from waypoint inner join approach_leg al on ident = al.fix_ident where al.approach_id = (select approach_id from approach where fix_ident = ? and runway_name = ? and (suffix = 'D' or suffix = 'A')) ORDER BY al.approach_leg_id ASC"
    return conn.execute(q, (name, rwy)).fetchall()


def waypoints_to_latlon(*wpts):
    q = "select ident, lonx, laty from waypoint where ident = ?"
    return [conn.execute(q, (wpt,)).fetchone() for wpt in wpts]


def get_taxiways(icao: str):
    q = "select * from taxi_path where airport_id = (select airport_id from airport where icao = ?)"
    return conn.execute(q, (icao,)).fetchall()


def get_parking_coords(icao: str, name: str):
    q = "select laty, lonx from parking where name = ? and airport_id = (select airport_id from airport where icao = ?)"
    return conn.execute(
        q,
        (
            name,
            icao,
        ),
    ).fetchone()


def get_airport_name(icao: str):
    return conn.execute("select name from airport where icao = ?", (icao,)).fetchone()[
        "name"
    ]


def get_approach(icao: str, rwy: str):
    q = "select al.fix_ident, al.alt_descriptor, al.altitude1, al.altitude2 from approach_leg al \
        where is_missed = 0 and \
        approach_id = (\
            select approach_id from approach where airport_ident = ? and runway_name = ? order by case type \
            when 'ILS' then 0 \
            when 'RNAV' then 1 \
            when 'GPS' then 2 \
            else 3 end \
        ) ORDER BY approach_leg_id ASC"
    return conn.execute(q, (icao, rwy)).fetchall()


if __name__ == "__main__":
    from pprint import pprint

    pprint(get_runways("KSYR"))
