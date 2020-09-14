from changeset import *
from texts.text_bot import *
from os import environ
from pyrogram import Client, filters

def changeset_bot(ch_id: int) -> dict:
    change = osmcha.changeset.Analyse(ch_id)
    change.full_analysis()
    return {
        "id": change.id,
        "date": to_teh_time(change.date),
        "user": change.user,
        "is_sus": change.is_suspect,
        "flags": " ،".join(translate_flags(change.suspicion_reasons))
        "added": change.create,
        "modified": change.modify,
        "deleted": change.delete,
        "osm_url": f"https://www.osm.org/changeset/{id}",
        "osmcha_url": f"https://osmcha.org/changesets/{id}",
        "osmviz_url": f"https://resultmaps.neis-one.org/osm-change-viz?c={id}",
        "achavi_url": f"https://overpass-api.de/achavi/?changeset={id}"
    }


border = gen_border()
iran_bbox = {"min_lon": 43.8574219, "max_lon": 63.6328125,
             "min_lat": 24.6869524, "max_lat": 40.3800284}
api = osmapi.OsmApi()

app = Client(
    "detective_bot",
    api_id=environ["API_ID"],
    api_hash=environ["API_HASH"],
    bot_token=environ["BOT_TOKEN"]
)

@app.on_message(
    Filters.command(commands=["bebin", "b"], prefix="/")
    & ~ Filters.create(reply_to_bot))
def bebin(client, message):
    text = message.text.split(" ")[1:]
    message.reply_text("چیو ببینم؟") if not len(text)  # Empty message
    ch_info = changeset_bot(int(text))
    


app.run()

# key = 90866962
# print(f"Analyse {key}...")
# change = osmcha.changeset.Analyse(int(key))
# change.full_analysis()
# print(translate_flags(change.suspicion_reasons))
# print(to_teh_time(change.date))

# changesets = query_changesets(api, iran_bbox, border)
# for key in changesets.keys():
#     print(f"Analyse {key}...")
#     change = osmcha.changeset.Analyse(int(key))
#     change.full_analysis()
#     print(translate_flags(change.suspicion_reasons))
