from changeset import *
from os import environ
from pyrogram import Client, filters
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler

app = Client(
    "detective_bot",
    api_id=environ["API_ID"],
    api_hash=environ["API_HASH"],
    bot_token=environ["BOT_TOKEN"]
)
border = gen_border()
bot_commands_dir = Path.cwd() / "src" / "texts" / "bot_commands"
iran_bbox = {"min_lon": 43.8574219, "max_lon": 63.6328125,
             "min_lat": 24.6869524, "max_lat": 40.3800284}
api = osmapi.OsmApi()

gen_channel, sus_channel= environ["GEN_CHANNEL"], environ["SUS_CHANNEL"]

def changeset_bot(ch_id: int) -> dict:
    change = osmcha.changeset.Analyse(ch_id)
    change.full_analysis()
    enhance_detection(change)
    return {
        "id": change.id,
        "uid": f"#{change.uid}",
        "date": to_teh_time(change.date).strftime('%C'),
        "user": change.user,
        "comment": change.comment,
        "user_url": "%20".join(f"https://www.osm.org/user/{change.user}".split()),
        "is_sus": change.is_suspect,
        "flags": "، ".join(translate_flags(change.suspicion_reasons)),
        "added": change.create,
        "modified": change.modify,
        "deleted": change.delete,
        "osm_url": f"https://www.osm.org/changeset/{change.id}",
        "osmcha_url": f"https://osmcha.org/changesets/{change.id}",
        "osmviz_url": f"https://resultmaps.neis-one.org/osm-change-viz?c={change.id}",
        "achavi_url": f"https://overpass-api.de/achavi/?changeset={change.id}"
    }


def chnl_loop():
    ch_sets = query_changesets(api, iran_bbox, border, interval)
    for ch_st in ch_sets.keys():
        ch_info = changeset_bot(ch_st)
        with open(bot_commands_dir / "new_ch.md", "r") as sus_text:
            gen_response = sus_text.read().format(
                ch_info["id"], ch_info["date"], ch_info["user"], ch_info["user_url"],
                ch_info["added"], ch_info["modified"], ch_info["deleted"],
                ch_info["osm_url"], ch_info["osmcha_url"], ch_info["osmviz_url"],
                ch_info["achavi_url"], ch_info["comment"], ch_info["uid"])
        app.send_message(gen_channel, gen_response, parse_mode="md", disable_web_page_preview=True)
        if ch_info["is_sus"]:
            with open(bot_commands_dir / "sus_found.md", "r") as sus_text:
                sus_response = sus_text.read().format(
                    ch_info["id"], ch_info["date"], ch_info["user"], ch_info["user_url"], ch_info["added"],
                    ch_info["modified"], ch_info["deleted"], ch_info["osm_url"],
                    ch_info["osmcha_url"], ch_info["osmviz_url"], ch_info["achavi_url"],
                    ch_info["flags"], ch_info["comment"], ch_info["uid"])
            app.send_message(sus_channel, sus_response, parse_mode="md", disable_web_page_preview=True)


@app.on_message(filters.command(["bebin", "b"]))
def bebin(client, message):
    text = message.text.split(" ")[1:]
    if not len(text):
        message.reply_text("چیو ببینم؟")
        return
    ch_info = changeset_bot(int(text[0]))
    if ch_info["is_sus"]:
        with open(bot_commands_dir / "is_sus.md", "r") as sus_text:
            response = sus_text.read().format(
                ch_info["id"], ch_info["date"], ch_info["user"], ch_info["user_url"], ch_info["added"],
                ch_info["modified"], ch_info["deleted"], ch_info["osm_url"],
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
    message.reply_text(response, parse_mode="md", disable_web_page_preview=True)

@app.on_message(filters.command(["start"]) & filters.private)
def start_bot(client, message):
    message.reply_text("سلام!")



interval = 10
scheduler = BackgroundScheduler()
scheduler.add_job(chnl_loop, "interval", minutes=interval)

scheduler.start()
app.run()