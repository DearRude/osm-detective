"""Implementation of changset.py in Pyrogram for Telegram"""

from pyrogram import Client, filters
import osmapi
import osmcha.changeset

from time import sleep

import changeset as cha
import src.parse as pa
import src.conf as conf

proxy = {"hostname": conf.proxy_host,
         "port": conf.proxy_port}

app = Client(
    "detective_bot",
    api_id=conf.api_id, api_hash=conf.api_hash,
    bot_token=conf.bot_token,
)

if proxy["hostname"] and proxy["port"]:
    app.proxy = proxy


border, iran_bbox = cha.gen_border()
api = osmapi.OsmApi()

def chnl_loop():
    """A schedule loop which posts changesets to channels"""

    ch_sets = cha.query_changesets(api, iran_bbox, border, interval)
    for ch_st in ch_sets:
        ch_info = pa.changeset_parse(ch_st)
        app.send_message(conf.gen_channel, pa.format_nor(ch_info),
                         parse_mode="md", disable_web_page_preview=True)
        if ch_info["is_sus"]:
            app.send_message(conf.sus_channel, pa.format_sus(ch_info),
                             parse_mode="md", disable_web_page_preview=True)
        sleep(3) # Avoid telegram api limit


@app.on_message(filters.command(["bebin", "b"]))
def bebin(client, message):
    """Query whether a changeset is sus or not; Bot command"""

    text = message.text.split(" ")[1:]
    if len(text) == 0:
        message.reply_text("چیو ببینم؟")
        return

    ch_info = pa.changeset_parse(int(text[0]))
    response = pa.format_sus(ch_info) if ch_info["is_sus"] else pa.format_nor(ch_info)

    message.reply_text(response, parse_mode="md",
                       disable_web_page_preview=True)


@app.on_message(filters.command(["start"]) & filters.private)
def start_bot(client, message):
    """Bot start reply; Bot command"""

    message.reply_text("سلام!")

