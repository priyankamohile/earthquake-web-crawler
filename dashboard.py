from datetime import datetime, timezone

import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
MONGO_DB_URI = st.secrets["MONGO_DB_URI"]
DB_NAME = st.secrets["DB_NAME"]
COLLECTION_NAME = st.secrets["COLLECTION_NAME"]
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


# Reference : https://www.w3schools.com/python/ref_string_split.asp
# Split the title to display only place
df['location'] = df['title'].str.split(' - ', n=1).str[1]

# Convert time to datetime
# Reference : https://stackoverflow.com/questions/70099884/timestamp-string-to-datetime-python
timestamps = []
for t in df['time']:
    converted_timestamp = datetime.strptime(t, '%Y-%m-%d %H:%M:%S (UTC)')
    converted_timestamp = converted_timestamp.replace(tzinfo=timezone.utc)
    timestamps.append(converted_timestamp)

df['time'] = timestamps

# Clean magnitude
df['magnitude'] = df['magnitude'].str.extract(r'([0-9.]+)').astype(float)

# Clean depth
df['depth'] = df['depth'].str.extract(r'([0-9.]+)').astype(float)

# Reference : https://stackoverflow.com/questions/3743222/how-do-i-convert-a-datetime-to-date
# Add day column
df['day'] = df['time'].dt.date.astype('str')

# Day and time
# Reference : https://stackoverflow.com/questions/3743222/how-do-i-convert-a-datetime-to-date
# Reference : https://strftime.org/
df['date and time'] = df['time'].dt.strftime('%d %B, %Y %I:%M %p')

# Reference : https://medium.com/@whyamit404/creating-your-first-streamlit-heatmap-6d1ec844431e
# Reference : https://docs.streamlit.io/develop/api-reference/charts
# dashboard display
st.set_page_config(layout='wide')
st.markdown('# Global Earthquakes')


st.markdown('**Tip:** Hover on the map markers to view earthquake details. '
            'You can also click on the date and time, depth and magnitude headers in the table to sort ascending or '
            'descending.')

st.subheader('Scatter Map with Earthquake Epicentres')

# earthquake world map
# Reference : https://plotly.com/python-api-reference/generated/plotly.express.density_mapbox.html
# Reference : https://plotly.com/python/density-heatmaps/
# Reference : https://datascience.stackexchange.com/questions/126444/is-there-a-way-to-achieve-a-transparent-basemap-with-px-density-mapbox
# Reference : https://plotly.com/python/tile-map-layers/
# Reference : https://medium.com/data-science/meet-plotly-mapbox-best-choice-for-geographic-data-visualization-599b514bcd9a
# Updated to scatter_mapbox because I want to display colours by intensity, and not density/number pf occurrences in a region.
fig = px.scatter_mapbox(
    df,
    lat='latitude',
    lon='longitude',
    color='magnitude',
    size='magnitude',
    hover_name='location',
    # Reference : https://stackoverflow.com/questions/68752048/passing-multiple-attributes-to-hover-data-as-a-dictionary-in-dash-plotly
    hover_data={
        # Hide automatic cols
        'latitude': False,
        'longitude': False,
        'magnitude': False,

        # Customized
        'Date & Time': df['date and time'],
        'Depth (km)': df['depth'],
        'Magnitude': df['magnitude']
    },
    # Reference : https://matplotlib.org/stable/users/explain/colors/colormaps.html
    color_continuous_scale='YlOrRd',
    mapbox_style='carto-positron',
    zoom=2,
    height=700
)

fig.update_layout(margin={'r': 0, 't': 30, 'l': 0, 'b': 0})
st.plotly_chart(fig, use_container_width=True)


# earthquake summary table
# Reference : https://docs.streamlit.io/develop/api-reference/data/st.dataframe
st.subheader('Earthquake Summary')
# keep relevant columns
table_df = df[['time', 'date and time', 'location', 'coordinates', 'magnitude', 'depth', 'review status']].copy()
# rename col names
table_df = table_df.rename(columns={
    'time': 'Time',
    'date and time': 'Date & Time (UTC)',
    'location': 'Location',
    'coordinates': 'Coordinates',
    'magnitude': 'Magnitude',
    'depth': 'Depth (km)',
    'review status': 'Review Status'
})

# sort by timestamp desc
table_df = table_df.sort_values(by='Time', ascending=False)

# hide timestamp, display only date and time, also hide index (first col which is default)
# Reference : https://docs.streamlit.io/develop/api-reference/data/st.dataframe
st.dataframe(table_df[['Date & Time (UTC)', 'Location', 'Coordinates', 'Magnitude', 'Depth (km)', 'Review Status']], hide_index=True)
