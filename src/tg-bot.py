from changeset import *
from os import environ
from pyrogram import Client, filters

def changeset_bot(ch_id: int) -> dict:
    change = osmcha.changeset.Analyse(ch_id)
    change.full_analysis()
    return {
        "id": change.id,
        "date": to_teh_time(change.date).strftime('%C'),
        "user": change.user,
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


border = gen_border()
bot_commands_dir = Path.cwd() / "src" / "texts" / "bot_commands"
iran_bbox = {"min_lon": 43.8574219, "max_lon": 63.6328125,
             "min_lat": 24.6869524, "max_lat": 40.3800284}
api = osmapi.OsmApi()

app = Client(
    "detective_bot",
    api_id=environ["API_ID"],
    api_hash=environ["API_HASH"],
    bot_token=environ["BOT_TOKEN"]
)

@app.on_message(filters.command(commands=["bebin", "b"]))
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
                ch_info["flags"])
    else:
        with open(bot_commands_dir / "not_sus.md", "r") as sus_text:
            response = sus_text.read().format(
                ch_info["id"], ch_info["date"], ch_info["user"], ch_info["user_url"], ch_info["added"],
                ch_info["modified"], ch_info["deleted"], ch_info["osm_url"],
                ch_info["osmcha_url"], ch_info["osmviz_url"], ch_info["achavi_url"])
        print(response)
    message.reply_text(response, parse_mode="md", disable_web_page_preview=True)



app.run()
