import requests as req
from lxml import etree

from datetime import datetime

from src.consts import *

reqs = req.Session()

class User:
    def __init__(self, user_id):
        self.id = user_id
        self.__osm_api()
        self.__mapbox_api()

    def __osm_api(self):
        url = OSM_USERS_API.format(user_id=self.id)
        try:
            request = reqs.get(url)
            request.raise_for_status()
            user_root = etree.XML(request.content)
        except req.exceptions.HTTPError as e:
            print(e.response.text)
        self.display_name = user_root.xpath("user/@display_name")[0]
        self.created_at = datetime.strptime(
            user_root.xpath("user/@account_created")[0],
            "%Y-%m-%dT%H:%M:%SZ")
        self.chset_count = int(user_root.xpath("user/changesets/@count")[0])
        self.trace_count = int(user_root.xpath("user/traces/@count")[0])
        self.blocks = int(user_root.xpath("user/blocks/received/@count")[0])

    def __mapbox_api(self):
        url = MAPBOX_USERS_API.format(user_id=self.id)
        try:
            request = reqs.get(url)
            request.raise_for_status()
            user = request.json()
        except req.exceptions.HTTPError as e:
            print(e.response.text)
        self.first_edit = datetime.strptime(
            user["first_edit"],
            "%Y-%m-%dT%H:%M:%S.%fZ")
        self.mapping_days = user["extra"]["mapping_days"]
        self.ch_discussion = user["extra"]["changesets_with_discussions"]
