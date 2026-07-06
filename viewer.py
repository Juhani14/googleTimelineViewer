import sqlite3
import pandas as pd
import streamlit as st
import folium
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

st.set_page_config(
    page_title="Google Timeline Explorer",
    layout="wide"
)

st.title("🗺 Google Timeline Explorer")

conn = sqlite3.connect(DB)

# -------------------------------------------------
# Load available dates
# -------------------------------------------------

dates = pd.read_sql("""
SELECT DISTINCT substr(start_time,1,10) AS d
FROM visits
ORDER BY d DESC
""", conn)

selected = st.selectbox(
    "Choose a day",
    dates["d"].tolist()
)

# -------------------------------------------------
# Load data
# -------------------------------------------------

visits = pd.read_sql("""
SELECT *
FROM visits
WHERE substr(start_time,1,10)=?
ORDER BY start_time
""", conn, params=(selected,))

activities = pd.read_sql("""
SELECT *
FROM activities
WHERE substr(start_time,1,10)=?
ORDER BY start_time
""", conn, params=(selected,))

conn.close()

# -------------------------------------------------
# Map center
# -------------------------------------------------

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

# -------------------------------------------------
# Create map
# -------------------------------------------------

m = folium.Map(
    location=center,
    zoom_start=13
)

# Visits

for _, v in visits.iterrows():

    folium.Marker(
        [v.latitude, v.longitude],
        popup=f"""
        Visit

        {v.start_time}

        {v.end_time}
        """,
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

# Activities

for _, a in activities.iterrows():

    color = COLORS.get(a.activity_type, "gray")

    folium.PolyLine(
        [
            [a.start_lat, a.start_lon],
            [a.end_lat, a.end_lon]
        ],
        color=color,
        weight=5,
        tooltip=f"{a.activity_type} ({int(a.distance)} m)"
    ).add_to(m)

# -------------------------------------------------
# Layout
# -------------------------------------------------

left, right = st.columns([1, 2])

# =================================================
# LEFT PANEL
# =================================================

with left:

    st.subheader("📊 Summary")

    total_distance = activities["distance"].sum() / 1000

    st.metric("Visits", len(visits))
    st.metric("Activities", len(activities))
    st.metric("Distance", f"{total_distance:.1f} km")

    st.divider()

    st.subheader("🕒 Timeline")

    events = []

    # Visits

    for _, v in visits.iterrows():

        events.append({
            "time": v.start_time,
            "text": "📍 Visit"
        })

    # Activities

    ICONS = {
        "WALKING": "🚶",
        "IN_PASSENGER_VEHICLE": "🚗",
        "IN_VEHICLE": "🚙",
        "IN_BUS": "🚌",
        "CYCLING": "🚴",
        "MOTORCYCLING": "🏍",
        "FLYING": "✈️",
        "IN_TRAIN": "🚆",
        "IN_SUBWAY": "🚇",
        "IN_TRAM": "🚋",
        "IN_FERRY": "⛴️"
    }

    for _, a in activities.iterrows():

        icon = ICONS.get(a.activity_type, "➡️")

        events.append({
            "time": a.start_time,
            "text": f"{icon} {a.activity_type} ({int(a.distance)} m)"
        })

    events.sort(key=lambda x: x["time"])

    for e in events:

        t = e["time"][11:16]

        st.write(f"**{t}** &nbsp;&nbsp; {e['text']}")

# =================================================
# RIGHT PANEL
# =================================================

with right:

    st_folium(
        m,
        width=900,
        height=700
    )