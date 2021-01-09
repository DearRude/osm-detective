from apscheduler.schedulers.background import BackgroundScheduler

from src.tg_bot import app, chnl_loop
import src.conf as conf

scheduler = BackgroundScheduler()
scheduler.add_job(chnl_loop, "interval", minutes=conf.interval)

print("Scheduler set.")
scheduler.start()
print("Pyrogram starting...")
app.run()
