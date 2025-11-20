from datetime import datetime, timezone

import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from config import  MONGO_DB_URI, DB_NAME, COLLECTION_NAME
from lat_lon_parser import parse

client = MongoClient(MONGO_DB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Fetch all events
# Reference : https://www.w3schools.com/python/python_mongodb_find.asp
# Reference : https://stackoverflow.com/questions/17805304/how-can-i-load-data-from-mongodb-collection-into-pandas-dataframe
data = list(collection.find())

# Convert to pandas dataframe
df = pd.DataFrame(data)

# Clean coordinates. First split latitude and longitude by space, then use the parser
# Reference : https://pypi.org/project/lat-lon-parser/
df[['latitude', 'longitude']] = df['coordinates'].str.split(' ', expand=True)
df['latitude'] = df['latitude'].apply(parse)
df['longitude'] = df['longitude'].apply(parse)

# Convert time to datetime
# Reference : https://stackoverflow.com/questions/70099884/timestamp-string-to-datetime-python
timestamps = []
for t in df['time']:
    converted_timestamp = datetime.strptime(t, "%Y-%m-%d %H:%M:%S (UTC)")
    converted_timestamp = converted_timestamp.replace(tzinfo=timezone.utc)
    timestamps.append(converted_timestamp)

df['time'] = timestamps

# Clean magnitude
df['magnitude'] = df['magnitude'].str.extract(r'([0-9.]+)').astype(float)

# Reference : https://stackoverflow.com/questions/3743222/how-do-i-convert-a-datetime-to-date
# Add day column
df['day'] = df['time'].dt.date.astype('str')

# Day and time
# Reference : https://stackoverflow.com/questions/3743222/how-do-i-convert-a-datetime-to-date
df['datetime'] = df['time'].dt.strftime('%y-%m-%d %a %H:%M:%S')

# Reference : https://medium.com/@whyamit404/creating-your-first-streamlit-heatmap-6d1ec844431e
# Reference : https://docs.streamlit.io/develop/api-reference/charts
# dashboard display
st.set_page_config(layout="wide")
st.markdown("Interactive visualization of recent earthquakes with a heatmap and day-wise analysis.")
st.subheader("Earthquake Heatmap")

# heatmap
# Reference : https://plotly.com/python-api-reference/generated/plotly.express.density_mapbox.html
# Reference : https://plotly.com/python/density-heatmaps/
# Reference : https://datascience.stackexchange.com/questions/126444/is-there-a-way-to-achieve-a-transparent-basemap-with-px-density-mapbox
# Reference : https://plotly.com/python/tile-map-layers/
# Reference : https://medium.com/data-science/meet-plotly-mapbox-best-choice-for-geographic-data-visualization-599b514bcd9a
fig = px.density_mapbox(
    df,
    lat='latitude',
    lon='longitude',
    z='magnitude',
    radius=5,
    hover_name='title',
    hover_data={'datetime': True, 'depth': True, 'magnitude': True},
    mapbox_style='carto-positron',
    center={'lat': df['latitude'].mean(), 'lon': df['longitude'].mean()},
    zoom=2.0,
    height=700
)

fig.update_layout(title="Earthquake Heatmap", margin={"r": 0, "t": 30, "l": 0, "b": 0})
st.plotly_chart(fig, use_container_width=True)

# earthquake summary table
# Reference : https://docs.streamlit.io/develop/api-reference/data/st.dataframe
st.subheader("Recent Earthquakes")
# keep relevant columns
table_df = df[['time', 'datetime', 'title', 'coordinates', 'magnitude', 'depth', 'review status']].copy()
# rename col names
table_df = table_df.rename(columns={
    'time': 'Time',
    'datetime': 'Date & Time',
    'title': 'Location',
    'coordinates': 'Coordinates',
    'magnitude': 'Magnitude',
    'depth': 'Depth (km)',
    'review status': 'Review Status'
})

# sort by timestamp desc
table_df = table_df.sort_values(by='Time', ascending=False)

# hide timestamp, display only date and time
st.dataframe(table_df[['Date & Time', 'Location', 'Coordinates', 'Magnitude', 'Depth (km)', 'Review Status']])
