import json
from matplotlib import path as geo_path
import osmapi
import osmcha.changeset
from pathlib import Path

from texts.text_changesets import *


def gen_border():
    # Parse GeoJSON
    with open(Path.cwd()/"assets"/"borders"/"ir-sim.geojson") as f:
        lim_border = json.load(f)
    # Shove it into matplotlib
    border_coords = lim_border["features"][0]["geometry"]["coordinates"]
    return geo_path.Path(border_coords, closed=True)

def in_border(area_coords, border):
    nodes = [[area_coords["min_lon"], area_coords["min_lat"]],
             [area_coords["min_lon"], area_coords["max_lat"]],
             [area_coords["max_lon"], area_coords["min_lat"]],
             [area_coords["max_lon"], area_coords["max_lat"]]]
    area_within_result = border.contains_points(nodes)
    return False if False in area_within_result else True


def filter_changesets(changesets, border):
    sel_keys = ["min_lon", "max_lon", "min_lat", "max_lat"]
    for ch_id in list(changesets.keys()):
        info_area = {c_key: changesets[ch_id][c_key] for c_key in sel_keys}
        if not in_border(info_area, border):
            del changesets[ch_id]

def translate_flags(flag_list):
    for idx, flag in enumerate(flag_list):
        flag_list[idx] = translation.get(flag, flag)
    return flag_list