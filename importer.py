import json
import sqlite3
import os

DB = "timeline.db"

if os.path.exists("timeline.db"):
    os.remove("timeline.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS visits(
    id INTEGER PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    latitude REAL,
    longitude REAL,
    place_id TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS activities(
    id INTEGER PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    start_lat REAL,
    start_lon REAL,
    end_lat REAL,
    end_lon REAL,
    activity_type TEXT,
    distance REAL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS path_points(
    id INTEGER PRIMARY KEY,
    activity_id INTEGER,
    sequence INTEGER,
    point_time TEXT,
    latitude REAL,
    longitude REAL
)
""")

cur.execute("""
CREATE INDEX IF NOT EXISTS idx_path_activity
ON path_points(activity_id)
""")



with open("timeline.json","r",encoding="utf-8") as f:
    data=json.load(f)

segments=data["semanticSegments"]

def parse_latlng(text):
    lat,lon=text.replace("°","").split(",")
    return float(lat),float(lon)

for s in segments:

    if "visit" in s:

        p=s["visit"]["topCandidate"]

        lat,lon=parse_latlng(
            p["placeLocation"]["latLng"]
        )

        cur.execute("""
        INSERT INTO visits(
            start_time,end_time,
            latitude,longitude,
            place_id
        )
        VALUES(?,?,?,?,?)
        """,
        (
            s["startTime"],
            s["endTime"],
            lat,
            lon,
            p.get("placeId","")
        ))

    if "activity" in s:

        a=s["activity"]

        slat,slon=parse_latlng(a["start"]["latLng"])
        elat,elon=parse_latlng(a["end"]["latLng"])

        cur.execute("""
INSERT INTO activities(
    start_time,
    end_time,
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    activity_type,
    distance
)
VALUES(?,?,?,?,?,?,?,?)
""",
(
    s["startTime"],
    s["endTime"],
    slat,
    slon,
    elat,
    elon,
    a["topCandidate"]["type"],
    a.get("distanceMeters",0)
))

activity_id = cur.lastrowid
cur.execute("CREATE INDEX IF NOT EXISTS idx_visit_start ON visits(start_time)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_start ON activities(start_time)")
conn.commit()
conn.close()

print("Database created.")
