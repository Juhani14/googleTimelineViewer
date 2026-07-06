import json
from collections import Counter

with open("timeline.json", "r", encoding="utf-8") as f:
    data = json.load(f)

activities = Counter()

for seg in data["semanticSegments"]:

    if "activity" in seg:

        act = seg["activity"]

        if "topCandidate" in act:
            activities[act["topCandidate"].get("type", "Unknown")] += 1

print(activities)
