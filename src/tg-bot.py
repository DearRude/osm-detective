from changeset import *



border = gen_border()
iran_bbox = {"min_lon": 43.8574219, "max_lon": 63.6328125,
             "min_lat": 24.6869524, "max_lat": 40.3800284}
api = osmapi.OsmApi()




# key = 90866962
# print(f"Analyse {key}...")
# change = osmcha.changeset.Analyse(int(key))
# change.full_analysis()
# print(translate_flags(change.suspicion_reasons))
# print(to_teh_time(change.date))

changesets = query_changesets(api, iran_bbox, border)
for key in changesets.keys():
    print(f"Analyse {key}...")
    change = osmcha.changeset.Analyse(int(key))
    change.full_analysis()
    print(translate_flags(change.suspicion_reasons))
