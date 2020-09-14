from datetime import datetime, timedelta, timezone
from changeset import *



border = gen_border()

iran_bbox = {"min_lon": 43.8574219, "max_lon": 63.6328125,
             "min_lat": 24.6869524, "max_lat": 40.3800284}

offset = timezone(timedelta(hours=0))
time_period = datetime.now(offset) - timedelta(hours=5)


api = osmapi.OsmApi()

changesets = api.ChangesetsGet(**iran_bbox, closed_after=time_period, only_closed=True)
filter_changesets(changesets, border)

# key = 38857728
# print(f"Analyse {key}...")
# change = osmcha.changeset.Analyse(int(key))
# change.full_analysis()
# print(translate_flags(change.suspicion_reasons))


for key in changesets.keys():
    print(f"Analyse {key}...")
    change = osmcha.changeset.Analyse(int(key))
    change.full_analysis()
    print(translate_flags(change.suspicion_reasons))
