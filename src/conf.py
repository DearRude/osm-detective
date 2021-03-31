import toml

with open("conf.toml", "r") as f:
    confs = toml.load(f)

## App
country = confs["app"]["border"]
interval = confs["app"]["fetch_intervals"]
language = confs["app"]["language"]
prom_enabled = True if confs["app"].get("prometheus_port") else False
if prom_enabled:
    prom_port = confs["app"]["prometheus_port"]

## Pyrogram
pyrogram_enabled = True if confs.get("pyrogram") else False
if pyrogram_enabled:
    api_id = confs["pyrogram"]["api_id"]
    api_hash = confs["pyrogram"]["api_hash"]
    bot_token = confs["pyrogram"]["bot_token"]

    gen_channel = confs["pyrogram"]["telegram_gen_channel"]
    sus_channel = confs["pyrogram"]["telegram_sus_channel"]
else:
    api_id, api_hash, bot_token = [None, None, None]
    gen_channel, sus_channel = [None, None]

proxy_needed = True if pyrogram_enabled and confs["pyrogram"].get("proxy") else False
if proxy_needed:
    proxy_host = confs["pyrogram"].get("proxy")["host"]
    proxy_port = confs["pyrogram"].get("proxy")["port"]

## Validator
common_editors = confs["validator"]["common_editors"]
comment_sus_words = confs["validator"]["comment_sus_words"]
source_sus_words = confs["validator"]["source_sus_words"]

important_ids = confs["validator"]["important_ids"]
important_tags = confs["validator"]["important_tags"]
important_tags = dict([tag.split("=") for tag in important_tags])
important_names = confs["validator"]["important_names"]


## APIs
osm_users_api = 'https://www.openstreetmap.org/api/0.6/user/{user_id}'
osm_changeset_api = "https://www.openstreetmap.org/api/0.6/changeset/{ch_id}"
osm_changeset_raw_api = "https://www.openstreetmap.org/api/0.6/changeset/{ch_id}/download"
nominatim_api = "https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"

if confs.get("api"):
    osm_users_api = confs["api"].get(osm_users_api, osm_users_api)
    osm_changeset_api = confs["api"].get(osm_changeset_api, osm_changeset_api)
    osm_changeset_raw_api = confs["api"].get(
        osm_changeset_raw_api, osm_changeset_raw_api)
    nominatim_api = confs["api"].get(nominatim_api, nominatim_api)
