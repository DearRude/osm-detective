from os import environ as env

country = env["BORDER"]
interval = int(env["INTERVAL"])

api_id = int(env["API_ID"])
api_hash = env["API_HASH"]
bot_token = env["BOT_TOKEN"]

gen_channel = env["GEN_CHANNEL"]
sus_channel = env["SUS_CHANNEL"]

proxy_host = env.get("PROXY_HOST", None)
proxy_port = env.get("PROXY_PORT", None)
proxy_port = int(proxy_port) if proxy_port else proxy_port