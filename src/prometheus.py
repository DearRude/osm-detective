from prometheus_client import Counter, Gauge, Summary

# General
cycle = Counter("fetch_cycles", "Total fetch cycles")
changesets = Counter("changesets", "Total changesets")
changeset_per_cycle = Gauge("changeset_per_cycle", "Number of changesets per cycle")

# Requests
requests = Counter("api_requests", "Total API requests", ["type"])
req_time = Summary("api_request_seconds", "Seconds waiting for request")

# Changes
creates = Counter("change_create", "Total creation changes", ["type"])
modifies = Counter("change_modify", "Total modification changes", ["type"])
deletes = Counter("change_deletes", "Total deletion changes", ["type"])
