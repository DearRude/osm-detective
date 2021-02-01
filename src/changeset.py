"""Some modules to work with changesets"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from khayyam import JalaliDatetime, TehranTimezone
from matplotlib import path as geo_path

import src.conf as conf
from src.analyse import Analyse
from src.texts.flags import langs


def gen_border():
    """Generates border path and bbox out of geojson file
    """
    # Parse GeoJSON
    country = conf.country
    print(f"Border {country} detected")
    with open(Path.cwd()/"assets"/"borders"/f"{country.lower()}.geojson") as bor:
        lim_border = json.load(bor)
    # Shove it into matplotlib
    border_coords = lim_border["features"][0]["geometry"]["coordinates"]
    point_list = np.array(border_coords)
    country_bbox = {"min_lon": point_list[:, 0].min(), "max_lon": point_list[:, 0].max(),
                 "min_lat": point_list[:, 1].min(), "max_lat": point_list[:, 1].max()}

    print("Borders path generated")
    return geo_path.Path(border_coords, closed=True), country_bbox


def bbox_in_border(area_coords, border) -> bool:
    """Determines whether a bbox is in parsed border or not
    """
    nodes = [[area_coords["min_lon"], area_coords["min_lat"]],
             [area_coords["min_lon"], area_coords["max_lat"]],
             [area_coords["max_lon"], area_coords["min_lat"]],
             [area_coords["max_lon"], area_coords["max_lat"]]]
    area_within_result = border.contains_points(nodes)
    return False if False in area_within_result else True


def filter_changesets(changesets, border):
    """Filter changesets that are not in parsed border
    """
    sel_keys = ["min_lon", "max_lon", "min_lat", "max_lat"]
    for ch_id in list(changesets.keys()):
        info_area = {c_key: changesets[ch_id][c_key] for c_key in sel_keys}
        if not bbox_in_border(info_area, border):
            del changesets[ch_id]


def translate_flags(flags: dict) -> list:
    """Translates flags according to translation dict
    """
    source = langs[conf.language]
    dest = []
    for flag, count in flags.items():
        if ":" in flag:
            key, val = flag.split(":")
            dest.append(source[key].format(v=count, n=val))
        else:
            dest.append(source[flag].format(v=count))
    return dest


def to_jalali(date_time):
    """Converts datetime object to Jalali datetime object
    """
    offset_hour = 4 if JalaliDatetime.now(TehranTimezone()).month <= 6 else 3
    date_time = date_time + timedelta(hours=offset_hour, minutes=30)
    return JalaliDatetime(date_time, TehranTimezone())


def changeset_parse(ana: Analyse) -> str:
    """Gathers latest changests and exports info about them"""
    parsed_date = ana.ch.closed_at.strftime('%c')
    if conf.language == "fa":
        jal_date = to_jalali(ana.ch.closed_at)
        parsed_date = jal_date.strftime('%C')
    with open(Path.cwd() / "assets" / "bot_commands" / f"{conf.language}.md", "r") as nor_text:
        return nor_text.read().format(
            ch_id=ana.ch.id,
            grade=ana.gr,
            flags="\n".join([f"- {flag}" for flag in translate_flags(ana.flags)]),
            date=parsed_date,
            location=ana.ch.loc,
            user_id=ana.ch.user.id,
            username=ana.ch.user.display_name,
            userlink="%20".join(
                f"https://www.osm.org/user/{ana.ch.user.display_name}".split()),
            comment=ana.ch.tags.get("comment"),
            source=ana.ch.tags.get("source"),
            osm_link=f"https://www.osm.org/changeset/{ana.ch.id}",
            osmcha_link=f"https://osmcha.org/changesets/{ana.ch.id}",
            osmvis_link=f"https://resultmaps.neis-one.org/osm-change-viz?c={ana.ch.id}",
            achavi_link=f"https://overpass-api.de/achavi/?changeset={ana.ch.id}"
        )


def query_changesets(api, country_bbox, border, mins=10) -> dict:
    """Query latest changesets from osmapi
    """
    utc_timezone = timezone(timedelta(0))
    time_period = datetime.now(utc_timezone) - timedelta(minutes=mins)
    try:
        changesets = api.ChangesetsGet(
            **country_bbox, closed_after=time_period, only_closed=True)
    except Exception:
        return []
    filter_changesets(changesets, border)
    print(f"{len(changesets)} changsets found")
    return changesets

