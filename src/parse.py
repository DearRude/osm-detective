import osmapi
import osmcha.changeset

import src.changeset as cha

bot_commands_dir = cha.Path.cwd() / "assets" / "bot_commands"

def changeset_parse(ch_id: int) -> dict:
    """Gathers latest changests and exports info about them"""

    change = osmcha.changeset.Analyse(ch_id)
    change.full_analysis()
    cha.enhance_detection(change)
    return {
        "id": change.id,
        "uid": f"{change.uid}",
        "date": cha.to_teh_time(change.date).strftime('%C'),
        "user": change.user,
        "comment": cha.translation.get(change.comment, change.comment),
        "source": cha.translation.get(change.source, change.source),
        "user_url": "%20".join(f"https://www.osm.org/user/{change.user}".split()),
        "is_sus": change.is_suspect,
        "flags": "، ".join(cha.translate_flags(change.suspicion_reasons)),
        "added": change.create,
        "modified": change.modify,
        "deleted": change.delete,
        "osm_url": f"https://www.osm.org/changeset/{change.id}",
        "osmcha_url": f"https://osmcha.org/changesets/{change.id}",
        "osmviz_url": f"https://resultmaps.neis-one.org/osm-change-viz?c={change.id}",
        "achavi_url": f"https://overpass-api.de/achavi/?changeset={change.id}"
    }


def format_nor(ch_info: dict) -> str:
    """Format markdown output for normal changesets"""
    with open(bot_commands_dir / "new_ch.md", "r") as nor_text:
        return nor_text.read().format(
            ch_info["id"], ch_info["date"], ch_info["user"], ch_info["user_url"],
            ch_info["added"], ch_info["modified"], ch_info["deleted"],
            ch_info["osm_url"], ch_info["osmcha_url"], ch_info["osmviz_url"],
            ch_info["achavi_url"], ch_info["comment"], ch_info["uid"], ch_info["source"])


def format_sus(ch_info: dict) -> str:
    """Format markdown output for suspicious changesets"""
    with open(bot_commands_dir / "sus_found.md", "r") as sus_text:
        return sus_text.read().format(
            ch_info["id"], ch_info["date"], ch_info["user"], ch_info["user_url"],
            ch_info["added"], ch_info["modified"], ch_info["deleted"], ch_info["osm_url"],
            ch_info["osmcha_url"], ch_info["osmviz_url"], ch_info["achavi_url"],
            ch_info["flags"], ch_info["comment"], ch_info["uid"], ch_info["source"])
