"""Implementation of changset.py in Pyrogram for Telegram"""

from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, filters
import osmapi
import osmcha.changeset

import changeset as cha

app = Client(
    "detective_bot",
    api_id=cha.environ["API_ID"],
    api_hash=cha.environ["API_HASH"],
    bot_token=cha.environ["BOT_TOKEN"]
)
border, iran_bbox = cha.gen_border()
bot_commands_dir = cha.Path.cwd() / "src" / "texts" / "bot_commands"

api = osmapi.OsmApi()

gen_channel, sus_channel = cha.environ["GEN_CHANNEL"], cha.environ["SUS_CHANNEL"]


def changeset_bot(ch_id: int) -> dict:
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


def chnl_loop():
    """A schedule loop which posts changesets to channels"""

    ch_sets = cha.query_changesets(api, iran_bbox, border, interval)
    for ch_st in ch_sets:
        ch_info = changeset_bot(ch_st)
        with open(bot_commands_dir / "new_ch.md", "r") as sus_text:
            gen_response = sus_text.read().format(
                ch_info["id"], ch_info["date"], ch_info["user"], ch_info["user_url"],
                ch_info["added"], ch_info["modified"], ch_info["deleted"],
                ch_info["osm_url"], ch_info["osmcha_url"], ch_info["osmviz_url"],
                ch_info["achavi_url"], ch_info["comment"], ch_info["uid"], ch_info["source"])
        app.send_message(gen_channel, gen_response,
                         parse_mode="md", disable_web_page_preview=True)
        if ch_info["is_sus"]:
            with open(bot_commands_dir / "sus_found.md", "r") as sus_text:
                sus_response = sus_text.read().format(
                    ch_info["id"], ch_info["date"], ch_info["user"], ch_info["user_url"],
                    ch_info["added"], ch_info["modified"], ch_info["deleted"], ch_info["osm_url"],
                    ch_info["osmcha_url"], ch_info["osmviz_url"], ch_info["achavi_url"],
                    ch_info["flags"], ch_info["comment"], ch_info["uid"], ch_info["source"])
            app.send_message(sus_channel, sus_response,
                             parse_mode="md", disable_web_page_preview=True)


@app.on_message(filters.command(["bebin", "b"]))
def bebin(message):
    """Query whether a changeset is sus or not; Bot command"""

    text = message.text.split(" ")[1:]
    if len(text) != 0:
        message.reply_text("چیو ببینم؟")
        return
    ch_info = changeset_bot(int(text[0]))
    if ch_info["is_sus"]:
        with open(bot_commands_dir / "is_sus.md", "r") as sus_text:
            response = sus_text.read().format(
                ch_info["id"], ch_info["date"], ch_info["user"], ch_info["user_url"],
                ch_info["added"], ch_info["modified"], ch_info["deleted"], ch_info["osm_url"],
                ch_info["osmcha_url"], ch_info["osmviz_url"], ch_info["achavi_url"],
                ch_info["flags"], ch_info["comment"])
    else:
        with open(bot_commands_dir / "not_sus.md", "r") as sus_text:
            response = sus_text.read().format(
                ch_info["id"], ch_info["date"], ch_info["user"], ch_info["user_url"],
                ch_info["added"], ch_info["modified"], ch_info["deleted"],
                ch_info["osm_url"], ch_info["osmcha_url"], ch_info["osmviz_url"],
                ch_info["achavi_url"], ch_info["comment"])
        print(response)
    message.reply_text(response, parse_mode="md",
                       disable_web_page_preview=True)


@app.on_message(filters.command(["start"]) & filters.private)
def start_bot(message):
    """Bot start reply; Bot command"""

    message.reply_text("سلام!")


interval = int(cha.environ["INTERVAL"])
scheduler = BackgroundScheduler()
scheduler.add_job(chnl_loop, "interval", minutes=interval)

print("Scheduler set.")
scheduler.start()
print("Pyrogram starting...")
app.run()

# with app:
#     chnl_loop()
