import sqlite3
from datetime import datetime

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

DB = "timeline.db"

COLORS = {
    "WALKING": "green",
    "IN_PASSENGER_VEHICLE": "blue",
    "IN_VEHICLE": "blue",
    "IN_BUS": "orange",
    "CYCLING": "purple",
    "MOTORCYCLING": "black",
    "FLYING": "red",
    "IN_TRAIN": "darkred",
    "IN_SUBWAY": "cadetblue",
    "IN_TRAM": "pink",
    "IN_FERRY": "darkgreen",
}

ICONS = {
    "WALKING": "🚶",
    "IN_PASSENGER_VEHICLE": "🚗",
    "IN_VEHICLE": "🚙",
    "IN_BUS": "🚌",
    "CYCLING": "🚴",
    "MOTORCYCLING": "🏍️",
    "FLYING": "✈️",
    "IN_TRAIN": "🚆",
    "IN_SUBWAY": "🚇",
    "IN_TRAM": "🚋",
    "IN_FERRY": "⛴️",
}


def parse_time(s):
    return datetime.fromisoformat(s)


def duration_minutes(start, end):
    return (parse_time(end) - parse_time(start)).total_seconds() / 60


st.set_page_config(
    page_title="Google Timeline Explorer",
    layout="wide"
)

st.title("🗺️ Google Timeline Explorer")

conn = sqlite3.connect(DB)

# --------------------------------------------------
# Dates
# --------------------------------------------------

dates = pd.read_sql("""
SELECT DISTINCT substr(start_time,1,10) AS d
FROM visits
ORDER BY d DESC
""", conn)

selected_day = st.selectbox(
    "Choose a day",
    dates["d"].tolist()
)

# --------------------------------------------------
# Read database
# --------------------------------------------------

visits = pd.read_sql("""
SELECT *
FROM visits
WHERE substr(start_time,1,10)=?
ORDER BY start_time
""", conn, params=(selected_day,))

activities = pd.read_sql("""
SELECT *
FROM activities
WHERE substr(start_time,1,10)=?
ORDER BY start_time
""", conn, params=(selected_day,))

# --------------------------------------------------
# Activity filter
# --------------------------------------------------

activity_types = ["ALL"]

if len(activities):
    activity_types += sorted(
        activities["activity_type"].unique().tolist()
    )

selected_activity = st.selectbox(
    "Activity type",
    activity_types
)

if selected_activity != "ALL":
    activities = activities[
        activities["activity_type"] == selected_activity
    ]

conn.close()

# --------------------------------------------------
# Statistics
# --------------------------------------------------

total_distance = activities["distance"].sum() / 1000

# --------------------------------------------------
# Map centre
# --------------------------------------------------

if len(visits):

    center = [
        visits.iloc[0]["latitude"],
        visits.iloc[0]["longitude"]
    ]

elif len(activities):

    center = [
        activities.iloc[0]["start_lat"],
        activities.iloc[0]["start_lon"]
    ]

else:

    center = [0, 0]

m = folium.Map(
    location=center,
    zoom_start=13
)

# --------------------------------------------------
# Visits
# --------------------------------------------------

for _, v in visits.iterrows():

    minutes = duration_minutes(
        v.start_time,
        v.end_time
    )

    folium.Marker(
        [v.latitude, v.longitude],
        popup=f"""
Visit

Start:
{v.start_time}

End:
{v.end_time}

Duration:
{minutes:.0f} min
""",
        icon=folium.Icon(
            color="red",
            icon="home"
        )
    ).add_to(m)

# --------------------------------------------------
# Activities
# --------------------------------------------------

for _, a in activities.iterrows():

    color = COLORS.get(
        a.activity_type,
        "gray"
    )

    minutes = duration_minutes(
        a.start_time,
        a.end_time
    )

    speed = 0

    if minutes > 0:
        speed = (
            a.distance / 1000
        ) / (
            minutes / 60
        )

    folium.PolyLine(
        [
            [a.start_lat, a.start_lon],
            [a.end_lat, a.end_lon]
        ],
        color=color,
        weight=5,
        tooltip=(
            f"{a.activity_type}\n"
            f"{a.distance:.0f} m\n"
            f"{minutes:.0f} min\n"
            f"{speed:.1f} km/h"
        )
    ).add_to(m)

# --------------------------------------------------
# Layout
# --------------------------------------------------

left, right = st.columns([1, 2])

# ==================================================
# LEFT PANEL
# ==================================================

with left:

    st.subheader("📊 Summary")

    st.metric("Visits", len(visits))
    st.metric("Activities", len(activities))
    st.metric("Distance", f"{total_distance:.1f} km")

    if len(activities):
        st.metric(
            "Average trip",
            f"{total_distance / len(activities):.1f} km"
        )

    st.divider()

    st.subheader("🕒 Timeline")

    events = []

    # Visits

    for _, v in visits.iterrows():

        minutes = duration_minutes(
            v.start_time,
            v.end_time
        )

        events.append({
            "time": v.start_time,
            "text": f"📍 Visit ({minutes:.0f} min)"
        })

    # Activities

    for _, a in activities.iterrows():

        minutes = duration_minutes(
            a.start_time,
            a.end_time
        )

        speed = 0

        if minutes > 0:
            speed = (
                a.distance / 1000
            ) / (
                minutes / 60
            )

        icon = ICONS.get(
            a.activity_type,
            "➡️"
        )

        events.append({
            "time": a.start_time,
            "text":
                f"{icon} {a.activity_type}\n"
                f"{a.distance:.0f} m   "
                f"{minutes:.0f} min   "
                f"{speed:.1f} km/h"
        })

    events.sort(
        key=lambda x: x["time"]
    )

    for e in events:

        st.write(
            f"**{e['time'][11:16]}**  {e['text']}"
        )

# ==================================================
# RIGHT PANEL
# ==================================================

with right:

    st_folium(
        m,
        width=900,
        height=700
    )