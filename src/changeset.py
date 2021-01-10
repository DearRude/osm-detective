"""Some modules to work with changesets"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from khayyam import JalaliDatetime, TehranTimezone
from matplotlib import path as geo_path

from src.texts.text_changesets import translation
import src.conf as conf


def gen_border():
    """Generates border path and bbox out of geojson file"""

    # Parse GeoJSON
    country = conf.country
    print(f"Border {country} detected")
    with open(Path.cwd()/"assets"/"borders"/f"{country.lower()}.geojson") as bor:
        lim_border = json.load(bor)
    # Shove it into matplotlib
    border_coords = lim_border["features"][0]["geometry"]["coordinates"]
    point_list = np.array(border_coords)
    iran_bbox = {"min_lon": point_list[:, 0].min(), "max_lon": point_list[:, 0].max(),
                 "min_lat": point_list[:, 1].min(), "max_lat": point_list[:, 1].max()}

    print("Borders path generated")
    return geo_path.Path(border_coords, closed=True), iran_bbox


def bbox_in_border(area_coords, border) -> bool:
    """Determines whether a bbox is in parsed border or not"""

    nodes = [[area_coords["min_lon"], area_coords["min_lat"]],
             [area_coords["min_lon"], area_coords["max_lat"]],
             [area_coords["max_lon"], area_coords["min_lat"]],
             [area_coords["max_lon"], area_coords["max_lat"]]]
    area_within_result = border.contains_points(nodes)
    return False if False in area_within_result else True


def filter_changesets(changesets, border):
    """Filter changesets that are not in parsed border"""

    sel_keys = ["min_lon", "max_lon", "min_lat", "max_lat"]
    for ch_id in list(changesets.keys()):
        info_area = {c_key: changesets[ch_id][c_key] for c_key in sel_keys}
        if not bbox_in_border(info_area, border):
            del changesets[ch_id]


def translate_flags(flag_list) -> list:
    """Translates flags according to translation dict"""

    for idx, flag in enumerate(flag_list):
        flag_list[idx] = translation.get(flag, flag)
    return flag_list


def to_teh_time(date_time):
    """Converts datetime object to Jalali datetime object"""

    offset_hour = 4 if JalaliDatetime.now(TehranTimezone()).month <= 6 else 3
    date_time = date_time + timedelta(hours=offset_hour, minutes=30)
    return JalaliDatetime(date_time, TehranTimezone())


def query_changesets(api, iran_bbox, border, mins=10) -> dict:
    """Query latest changesets from osmapi"""

    utc_timezone = timezone(timedelta(0))
    time_period = datetime.now(utc_timezone) - timedelta(minutes=mins)
    try:
        changesets = api.ChangesetsGet(
            **iran_bbox, closed_after=time_period, only_closed=True)
    except Exception:
        return []
    filter_changesets(changesets, border)
    print(f"{len(changesets)} changsets found")
    return changesets


def enhance_detection(change):
    """Few tricks to enhance flag detection"""

    low_imprt = ["New mapper", "User has multiple blocks"]
    in_change = [flag in change.suspicion_reasons for flag in low_imprt]
    if len(change.suspicion_reasons) == 1 and (True in in_change):
        change.is_suspect = False
