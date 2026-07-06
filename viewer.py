import sqlite3
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

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

DB = "timeline.db"

st.set_page_config(layout="wide")

st.title("Google Timeline Explorer")

conn = sqlite3.connect(DB)

dates = pd.read_sql("""
SELECT DISTINCT substr(start_time,1,10) AS d
FROM visits
ORDER BY d DESC
""", conn)

selected = st.selectbox(
    "Choose a day",
    dates["d"].tolist()
)

visits = pd.read_sql("""
SELECT *
FROM visits
WHERE substr(start_time,1,10)=?
""", conn, params=(selected,))

activities = pd.read_sql("""
SELECT *
FROM activities
WHERE substr(start_time,1,10)=?
""", conn, params=(selected,))

conn.close()

st.write(f"Visits: {len(visits)}")
st.write(f"Activities: {len(activities)}")

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

    center = [0,0]

m = folium.Map(
    location=center,
    zoom_start=13
)

for _,v in visits.iterrows():

    folium.Marker(
        [v.latitude,v.longitude],
        popup=v.start_time
    ).add_to(m)

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

st_folium(m,width=1000,height=700)
