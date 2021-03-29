"""Declaring OSM user and changeset types as
well as analysis methods on them"""

from datetime import datetime

import requests as req
from lxml import etree
import backoff

from src import conf
from src import prometheus as prom

reqs = req.Session()
reqs.headers.update({"User-Agent": "osm-detective"})


@backoff.on_exception(backoff.expo,
                      req.exceptions.RequestException,
                      max_tries=10)
@prom.req_time.time()
def request(url: str, content_type: str = "xml"):
    prom.requests.labels(content_type).inc()
    reque = reqs.get(url)
    reque.raise_for_status()
    if content_type == "xml":
        return etree.XML(reque.content)
    elif content_type == "json":
        return reque.json()


class User:
    """OSM user class to be used in analysis"""
    def __init__(self, user_id):
        self.id = user_id
        self.__xml = request(conf.osm_users_api.format(user_id=user_id))
        self.__osm_api()

    def __osm_api(self):
        self.display_name = self.__xml.xpath("user/@display_name")[0]
        self.created_at = datetime.strptime(
            self.__xml.xpath("user/@account_created")[0],
            "%Y-%m-%dT%H:%M:%SZ")
        self.chset_count = int(self.__xml.xpath("user/changesets/@count")[0])
        self.trace_count = int(self.__xml.xpath("user/traces/@count")[0])
        self.blocks = int(self.__xml.xpath("user/blocks/received/@count")[0])

class Changeset:
    """OSM changeset class to be used in analysis"""
    def __init__(self, ch_id: int):
        self.id = ch_id
        self.__meta = request(conf.osm_changeset_api.format(ch_id=ch_id))
        self.raw = request(conf.osm_changeset_raw_api.format(ch_id=ch_id))
        self.__extract_meta()
        self.user = User(self.uid)
        self.__extract_raw()
        self.__extract_location()

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
        prom.creates.labels("all").inc(self.count_allchange[0])
        prom.modifies.labels("all").inc(self.count_allchange[1])
        prom.deletes.labels("all").inc(self.count_allchange[2])

        self.count_ref_nodes = [r.xpath(f"count({action}/node[count(tag)=0])")
            for action in actions]
        prom.creates.labels("ref_node").inc(self.count_ref_nodes[0])
        prom.modifies.labels("ref_node").inc(self.count_ref_nodes[1])
        prom.deletes.labels("ref_node").inc(self.count_ref_nodes[2])

        self.count_nodes = [r.xpath(f"count({action}/node[count(tag)>0])")
            for action in actions]
        prom.creates.labels("node").inc(self.count_nodes[0])
        prom.modifies.labels("node").inc(self.count_nodes[1])
        prom.deletes.labels("node").inc(self.count_nodes[2])

        self.count_ways = [r.xpath(f"count({action}/way)")
            for action in actions]
        prom.creates.labels("way").inc(self.count_ways[0])
        prom.modifies.labels("way").inc(self.count_ways[1])
        prom.deletes.labels("way").inc(self.count_ways[2])

        self.count_rels = [r.xpath(f"count({action}/relation)")
            for action in actions]
        prom.creates.labels("relation").inc(self.count_rels[0])
        prom.modifies.labels("relation").inc(self.count_rels[1])
        prom.deletes.labels("relation").inc(self.count_rels[2])

        self.count_highway = [r.xpath(f"count({action}/*/tag[@k='highway']/..)")
            for action in actions]
        prom.creates.labels("highway").inc(self.count_highway[0])
        prom.modifies.labels("highway").inc(self.count_highway[1])
        prom.deletes.labels("highway").inc(self.count_highway[2])

        self.count_building = [r.xpath(f"count({action}/*/tag[@k='building']/..)")
            for action in actions]
        prom.creates.labels("building").inc(self.count_building[0])
        prom.modifies.labels("building").inc(self.count_building[1])
        prom.deletes.labels("building").inc(self.count_building[2])

    def __extract_location(self):
        lat, lon = (self.bbox[0]+self.bbox[2])/2, (self.bbox[1]+self.bbox[3])/2
        nomi = request(conf.nominatim_api.format(
            lat=lat, lon=lon), "json")["address"]
        self.loc = " - ".join(
            [nomi.get("country", " "), nomi.get("state", " "), nomi.get("county", " ")])

class Analyse:
    def __init__(self, changeset_id):
        self.ch = Changeset(changeset_id)
        self.flags = {} # Flags assigning their grade level
        self.gr = 0  # Importance grade
        self.do_analysis()

    def do_analysis(self):
        """ Do full analysis with defined constants"""
        self.__new_user(min_chset=10, chset_gr=2,
            min_expri_day=3, expri_gr=0.5)
        self.__disputed_user(max_blocks=1,
            blocks_gr=1, blocks_step_gr=0.5)
        self.__big_area(max_deg_area=10, area_gr=2)
        self.__id_warnings(max_warnings=1, war_gr=1)
        self.__editor(commons=conf.common_editors,
            no_editor_gr=3, uncommon_editor_gr=3)
        self.__comment(sus_words=conf.comment_sus_words,
            no_comment_gr=1.5, sus_word_gr=3)
        self.__source(sus_words=conf.source_sus_words,
            no_source_gr=0.75, sus_word_gr=3)
        self.__review_request(review_gr=3)
        self.__mass_deletion(max_del_per=0.8, max_del=40,
            percent_gr=3, top_thresh=150, top_thresh_gr=4,
            max_ent=15, max_ent_gr=4)
        self.__mass_modification(max_mod=150, max_mod_gr=4)
        self.__mass_creation(max_cre=200, max_cre_gr=3,
            max_ent=50, max_ent_gr=1)
        self.__important_ids(ids=conf.important_ids, gr=5)
        self.__important_names(names=conf.important_names, gr=5)
        self.__important_tags(tags=conf.important_tags, gr=5)
        self.__versioned_entities(max_version=20, gr=2)

    def __new_user(self, min_chset: int, chset_gr: float,
        min_expri_day: int, expri_gr: float):
        """Given parameters, checks user total changesets
        and user account age
        """
        if self.ch.user.chset_count < min_chset:
            self.gr += chset_gr
            self.flags["changeset_count"] = self.ch.user.chset_count
        time_exprience = datetime.now() - self.ch.user.created_at
        if time_exprience.days < min_expri_day:
            self.gr += expri_gr
            self.flags["new_account"] = time_exprience.days

    def __disputed_user(self, max_blocks: int,
        blocks_gr: float, blocks_step_gr: float):
        """Given parameters, calculates number of blocks user had been
        received.
        """
        bl = self.ch.user.blocks
        if bl >= max_blocks:
            self.gr += blocks_gr
            self.flags["user_block"] = bl
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
            self.flags["big_area"] = "yes"

    def __id_warnings(self, max_warnings: int, war_gr: float):
        """Given parameters, counts iD warning types and
        their occurrence.
        """
        wars = {k: v for k, v in self.ch.tags.items() if k.startswith('warnings')}
        grades = [int(val) for val in wars.values()]
        if len(wars.keys()) >= max_warnings:
            self.gr += 1 + sum(grades)*war_gr
            for k, v in wars.items():
                self.flags[k[9:]] = v

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
            self.flags["uncommon_editor"] = editor

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
        for sus_word in sus_words:
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
            self.flags["exceed_del_percen"] = int(100 * deletaion_percentage)
        if all_del > top_thresh:
            self.gr += top_thresh_gr + (all_del - top_thresh // top_thresh)
            self.flags["mass_deletaion"] = all_del
        entities = [self.ch.count_nodes[2], self.ch.count_ways[2],
                    self.ch.count_rels[2]]
        for ent_del in entities:
            if ent_del > max_ent:
                self.gr += max_ent_gr + ((ent_del - max_ent) // max_ent)
                self.flags["entity_mass_deletion"] = sum(entities)

    def __mass_modification(self, max_mod: int, max_mod_gr: float):
        """Given max modification numbers, counts if exceeds
        its threshold
        """
        all_mod = self.ch.count_allchange[1]
        if all_mod > max_mod:
            self.gr += max_mod_gr + ((all_mod - max_mod_gr) // max_mod_gr)
            self.flags["mass_modification"] = all_mod

    def __mass_creation(self, max_cre: int, max_cre_gr: float,
        max_ent: int, max_ent_gr: float):
        """Given max creation numbers, counts if exceeds
        its threshold and counts created buildings
        """
        all_cre = self.ch.count_allchange[0]
        if all_cre > max_cre:
            self.gr += max_cre_gr + ((all_cre - max_cre) // max_cre)
            self.flags["mass_creation"] = all_cre
        buildings = self.ch.count_building[0]
        if buildings > max_ent:
            self.gr += max_cre_gr
            self.flags["building_mass_creation"] = buildings

    def __important_ids(self, ids: list, gr: float):
        """Given list of important ids of osm entities,
        checks if they are preset in changeset or not """
        for ent_id in ids:
            count_ids = self.ch.raw.xpath(f"count(//*[@id={ent_id}])")
            if count_ids >= 1:
                self.gr += gr
                self.flags["important_id"] = ent_id

    def __important_names(self, names: list, gr: float):
        """Given list of important names of osm entities,
        checks if they are preset in changeset or not """
        for ent_name in names:
            count_ids = self.ch.raw.xpath(f'count(//tag[@k="name"][contains(@v, "{ent_name}")])')
            if count_ids >= 1:
                self.gr += gr
                self.flags["important_name"] = ent_name

    def __important_tags(self, tags: dict, gr: float):
        """Given list of important tags of osm entities,
        checks if they are preset in changeset or not """
        for k, v in tags.items():
            count_ids = self.ch.raw.xpath(f'count(//tag[@k="{k}"][@v="{v}"])')
            if count_ids >= 1:
                self.gr += gr
                self.flags["important_tag"] = f"{k}={v}"

    def __versioned_entities(self, max_version: int, gr: float):
        """Given the max number of verisons, checks if
        someone has to do anything with them"""
        count = self.ch.raw.xpath(f"count(//*[@version > {max_version}])")
        if count > 0:
            self.gr += (gr * count)
            self.flags["versioned_entity"] = count
