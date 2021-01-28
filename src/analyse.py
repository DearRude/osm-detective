import requests as req
from lxml import etree

from datetime import datetime

from src.consts import *

reqs = req.Session()

class User:
    def __init__(self, user_id):
        self.id = user_id
        self.__xml = self.__request(OSM_USERS_API, "xml")
        self.__json = self.__request(MAPBOX_USERS_API, "json")
        self.__osm_api()
        self.__mapbox_api()

    def __request(self, link: str, type: str):
        url = link.format(user_id=self.id)
        try:
            request = reqs.get(url)
            request.raise_for_status()
            if type == "xml":
                return etree.XML(request.content)
            elif type == "json":
                return request.json()
        except req.exceptions.HTTPError as e:
            print(e.response.text)

    def __osm_api(self):
        self.display_name = self.__xml.xpath("user/@display_name")[0]
        self.created_at = datetime.strptime(
            self.__xml.xpath("user/@account_created")[0],
            "%Y-%m-%dT%H:%M:%SZ")
        self.chset_count = int(self.__xml.xpath("user/changesets/@count")[0])
        self.trace_count = int(self.__xml.xpath("user/traces/@count")[0])
        self.blocks = int(self.__xml.xpath("user/blocks/received/@count")[0])

    def __mapbox_api(self):
        self.first_edit = datetime.strptime(
            self.__json["first_edit"],
            "%Y-%m-%dT%H:%M:%S.%fZ")
        self.mapping_days = self.__json["extra"]["mapping_days"]
        self.ch_discussion = self.__json["extra"]["changesets_with_discussions"]

class Changeset:
    def __init__(self, id: int):
        self.id = id
        self.__meta = self.__request(OSM_CH_API)
        self.raw = self.__request(OSM_CHRAW_API)
        self.__extract_meta()
        self.user = User(self.uid)
        self.__extract_raw()

    def __request(self, link: str):
        url = link.format(ch_id=self.id)
        try:
            request = reqs.get(url)
            request.raise_for_status()
            return etree.XML(request.content)
        except req.exceptions.HTTPError as e:
            print(e.response.text)

    def __extract_meta(self):
        self.uid = int(self.__meta.xpath("changeset/@uid")[0])
        self.closed_at = datetime.strptime(
            self.__meta.xpath("changeset/@closed_at")[0],
            "%Y-%m-%dT%H:%M:%SZ")
        self.change_count = int(self.__meta.xpath("changeset/@changes_count")[0])
        self.bbox = [
            float(self.__meta.xpath("changeset/@min_lat")[0]),
            float(self.__meta.xpath("changeset/@min_lon")[0]),
            float(self.__meta.xpath("changeset/@max_lat")[0]),
            float(self.__meta.xpath("changeset/@max_lon")[0])
        ]
        tag_keys = self.__meta.xpath("changeset/tag/@k")
        tag_vals = self.__meta.xpath("changeset/tag/@v")
        self.tags = dict(zip(tag_keys, tag_vals))

    def __extract_raw(self):
        r = self.raw
        actions = ["create", "modify", "delete"]
        self.count_allchange = [r.xpath(f"count({action})")
            for action in actions]
        self.count_ref_nodes = [r.xpath(f"count({action}/node[count(tag)=0])")
            for action in actions]
        self.count_nodes = [r.xpath(f"count({action}/node[count(tag)>0])")
            for action in actions]
        self.count_ways = [r.xpath(f"count({action}/way)")
            for action in actions]
        self.count_rels = [r.xpath(f"count({action}/relation)")
            for action in actions]
        self.count_highway = [r.xpath(f"count({action}/*/tag[@k='highway']/..)")
            for action in actions]
        self.count_building = [r.xpath(f"count({action}/*/tag[@k='building']/..)")
            for action in actions]
