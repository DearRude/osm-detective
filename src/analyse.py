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

class Analyse:
    def __init__(self, changeset_id):
        self.ch = Changeset(changeset_id)
        self.flags = {} # Flags assigning their grade level
        self.gr = 0  # Importance grade
    
    def do_analysis(self):
        self.__new_user(min_chset=10, chset_gr=2,
            min_expri_day=3, expri_gr=0.5,
            min_map_days=10, map_days_gr=0.5)
        self.__disputed_user(max_dis=10, dispute_gr=1,
            dispute_step_gr=0.1, max_blocks=1,
            blocks_gr=1, blocks_step_gr=0.5)
        self.__big_area(max_deg_area=10, area_gr=2)
        self.__id_warnings(max_warnings=1, war_gr=1)
        COMMON_EDITORS = ["iD", "JOSM", "Potlatch",
                          "StreetComplete", "Vespucci"]
        self.__editor(commons=COMMON_EDITORS,
            no_editor_gr=3, uncommon_editor_gr=3)
        self.__comment(sus_words=SUS_WORDS_COMMENT,
            no_comment_gr=1.5, sus_word_gr=3)
        self.__source(sus_words=SUS_WORDS_SOURCE,
            no_source_gr=1.5, sus_word_gr=3)
        self.__review_request(review_gr=3)
        self.__mass_deletion(max_del_per=0.8, max_del=40,
            percent_gr=3, top_thresh=150, top_thresh_gr=4,
            max_ent=15, max_ent_gr=4)
        self.__mass_modification(max_mod=150, max_mod_gr=4)
        self.__mass_creation(max_cre=200, max_cre_gr=3,
            max_ent=50, max_ent_gr=1)

    def __new_user(self, min_chset: int, chset_gr: float,
        min_expri_day: int, expri_gr: float,
        min_map_days: int, map_days_gr: float):
        """Given parameters, checks user total changesets,
        user account age and user mapping days
        """
        if self.ch.user.chset_count < min_chset:
            self.gr += chset_gr
            self.flag["changeset_count"] = self.ch.user.chset_count
        time_exprience = datetime.now() - self.ch.user.created_at
        if time_exprience.days < min_expri_day:
            self.gr += expri_gr
            self.flag["new_account"] = time_exprience.days
        map_days = self.ch.user.mapping_days
        if map_days < min_map_days:
            self.gr += map_days_gr
            self.flag["mapping_days"] = map_days

    def __disputed_user(self, max_dis: int, dispute_gr: float,
        dispute_step_gr: float, max_blocks: int,
        blocks_gr: float, blocks_step_gr: float):
        """Given parameters, calculates number of changesets in
        which user has comments on and number of blocks user had been
        received.
        """
        dis = self.ch.user.ch_discussion
        if dis >= max_dis:
            self.gr += dispute_gr
            self.flag["disputed_ch"] = dis
        if dis > max_dis:
            self.gr += (dis * dispute_step_gr)
        bl = self.ch.user.blocks
        if bl >= max_blocks:
            self.gr += blocks_gr
            self.flag["user_block"] = bl
        if bl > max_blocks:
            self.gr += (bl-1) * blocks_step_gr

    def __big_area(self, max_deg_area: float, area_gr: float):
        """Given changeset bbox, checks if its area (in degree) is
        too big.
        """
        lat = self.ch.bbox[2] - self.ch.bbox[0]
        lon = self.ch.bbox[3] - self.ch.bbox[1]
        if (lat * lon) >= max_deg_area:
            self.gr += area_gr
            self.flag["big_area"] = "yes"

    def __id_warnings(self, max_warnings: int, war_gr: float):
        """Given parameters, counts iD warning types and
        their occurrence.
        """
        wars = {k: v for k, v in self.ch.tags if k.startswith('warnings')}
        if len(wars.keys) >= max_warnings:
            self.gr += 1 + sum(wars.values)*war_gr
            [self.flags[k[9:]] = v for k, v in wars]

    def __editor(self, commons: list,
        no_editor_gr: float, uncommon_editor_gr: float):
        """Given common editors list, checks if editor is specified
        in changeset and if yes, whether it is common or not
        """
        if "created_by" not in self.ch.tags:
            self.gr += no_editor_gr
            self.flags["no_editor"] = "yes"
            return
        editor = self.ch.tags["created_by"]
        if not any([editor.startswith(nor) for nor in commons]):
            self.gr += uncommon_editor_gr
            self.flags["uncommon_editor"] = "yes"

    def __comment(self, sus_words: list,
        no_comment_gr: float, sus_word_gr: float):
        """Given suspicious words, verifies if changeset has
        comment and if there exists suspicious words in it
        """
        if "comment" not in self.ch.tags:
            self.gr += no_comment_gr
            self.flags["no_comment"] = "yes"
            return
        for sus_word in sus_words:
            if sus_word in self.ch.tags["comment"]:
                self.gr += sus_word_gr
                self.flags["sus_word_comment"] = "yes"

    def __source(self, sus_words: list,
        no_source_gr: float, sus_word_gr: float):
        """Given suspicious words, verifies if changeset has
        source and if there exists suspicious words in it
        """
        if "source" not in self.ch.tags:
            self.gr += no_source_gr
            self.flags["no_source"] = "yes"
            return
        for sus_word in SUS_WORDS_SOURCE:
            if sus_word in self.ch.tags["source"]:
                self.gr += sus_word_gr
                self.flags["sus_word_source"] = "yes"

    def __review_request(self, review_gr: float):
        """Checks if a changeset requests a review
        """
        if "review_requested" in self.ch.tags:
            self.gr += review_gr
            self.flags["review_requested"] = "yes"

    def __mass_deletion(self, max_del_per: float, max_del: int,
        percent_gr: float, top_thresh: int, top_thresh_gr: float,
        max_ent: int, max_ent_gr: float):
        """Given all deletion count and entity deletion count, calculates
        deletion percentage and checks if exceeds top threshold of deletion
        as well as entities seperately
        """
        all_del = self.ch.count_allchange[2]
        deletaion_percentage = all_del / self.ch.change_count
        if deletaion_percentage > max_del_per and all_del > max_del:
            self.gr += percent_gr
            self.flags["exceed_del_percen"] = 100 * deletaion_percentage
        if all_del > top_thresh:
            self.gr += top_thresh_gr + (all_del - top_thresh // top_thresh)
            self.flags["mass_deletaion"] = all_del
        entities = [self.ch.count_nodes[2], self.ch.count_ways[2],
                    self.ch.count_rels[2]]
        for ent_del in entities:
            if ent_del > max_ent:
                self.gr += max_ent_gr + (ent_del - max_ent // max_ent)
                self.flags["entity_mass_deletion"] = sum(entities)

    def __mass_modification(self, max_mod: int, max_mod_gr: float):
        """Given max modification numbers, counts if exceeds
        its threshold
        """
        all_mod = self.ch.count_allchange[1]
        if all_mod > max_mod:
            self.gr += max_mod_gr + (all_mod - max_mod_gr // max_mod_gr)
            self.flags["mass_modification"] = all_mod

    def __mass_creation(self, max_cre: int, max_cre_gr: float,
        max_ent: int, max_ent_gr: float):
        """Given max creation numbers, counts if exceeds
        its threshold and counts created buildings
        """
        all_cre = self.ch.count_allchange[0]
        if all_cre > max_cre:
            self.gr += max_cre_gr + (all_cre - max_cre // max_cre)
            self.flags["mass_creation"] = all_cre
        buildings = self.ch.count_building[0]
        if buildings > max_ent:
            self.gre += max_cre_gr
            self.flags["building_mass_creation"]
    #TODO: Checks entities by their name, tag and id
