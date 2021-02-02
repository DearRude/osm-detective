"""Implementation of changset.py in Pyrogram for Telegram"""

from pyrogram import Client, filters
import osmapi

from time import sleep

import src.analyse as ana
import src.changeset as cha
import src.conf as conf
from src.chart import gen_changestat_png


app = Client(
    "detective_bot",
    api_id=conf.api_id, api_hash=conf.api_hash,
    bot_token=conf.bot_token,
)

if conf.proxy_needed:
    app.proxy = {"hostname": conf.proxy_host,
                 "port": conf.proxy_port}


border, iran_bbox = cha.gen_border()
api = osmapi.OsmApi()

def chnl_loop():
    """A schedule loop which posts changesets to channels"""

    print("Query for changesets...")
    ch_sets = cha.query_changesets(api, iran_bbox, border, conf.interval)
    for ch_st in ch_sets:
        try:
            print(f"Analysing {ch_st}")
            ch_ana = ana.Analyse(ch_st)
            gen_changestat_png(ch_ana.ch)
            ch_info = cha.changeset_parse(ch_ana)
            app.send_photo(conf.gen_channel, "temp.png",
                ch_info)
            if ch_ana.gr >= 3:
                app.send_photo(conf.sus_channel, "temp.png",
                               ch_info)
            sleep(3)  # Avoid telegram api limit
        except Exception as e:
            raise(e)
            print("Something went wrong...")
            print(e)


@app.on_message(filters.command(["check", "c"]))
def bebin(client, message):
    """Query whether a changeset is sus or not; Bot command"""

    text = message.text.split(" ")[1:]
    if len(text) == 0:
        message.reply_text("Check what?")
        return

    print(f"Analysing {text[0]}")
    ch_ana = ana.Analyse(text[0])
    gen_changestat_png(ch_ana.ch)
    ch_info = cha.changeset_parse(ch_ana)
    message.reply_photo("temp.png", caption=ch_info)


@app.on_message(filters.command(["start"]) & filters.private)
def start_bot(client, message):
    """Bot start reply; Bot command"""

    message.reply_text("Hello!")

