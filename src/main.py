from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
from prometheus_client import start_http_server

from src.tg_bot import app, chnl_loop
import src.conf as conf

if conf.prom_enabled:
    print("Initializing prometheus endpoint")
    start_http_server(conf.prom_port)

# with app:
#     chnl_loop()

scheduler = BackgroundScheduler() if conf.pyrogram_enabled else BlockingScheduler()
scheduler.add_job(chnl_loop, "interval", minutes=conf.interval)
print("Scheduler set.")
scheduler.start()

if conf.pyrogram_enabled:
    print("Pyrogram starting...")
    app.run()
