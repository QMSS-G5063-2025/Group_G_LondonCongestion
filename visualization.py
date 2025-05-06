import streamlit as st
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import plotly.express as px
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import branca.colormap as cm
import datetime

# --- Page Configuration ---
st.set_page_config(page_title="MTA Congestion Visualization", page_icon="🗽", layout="wide")

# --- Hero Banner ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(CURRENT_DIR, "image", "mta_banner.jpg")
if os.path.exists(IMAGE_PATH):
    st.image(IMAGE_PATH, use_container_width=True)

st.markdown("""
<div style='text-align: right; font-size: 12px; color: gray;'>
Source: <a href='https://new.mta.info/' target='_blank'>MTA Official Website</a>
</div>
""", unsafe_allow_html=True)

# --- Load Data ---
df = pd.read_csv('MTA_Entries.csv')
df['Toll Hour'] = pd.to_datetime(df['Toll Hour'], format='%m/%d/%Y %I:%M:%S %p')
df['Toll Date'] = df['Toll Hour'].dt.date
df['Time'] = df['Toll Hour'].dt.strftime('%H:%M')
cutoff_date = pd.to_datetime('2025-02-05 12:59:59')
df = df[df['Toll Hour'] <= cutoff_date]

# --- Define Entry Point Locations ---
entry_points = {
    'Brooklyn Bridge': {'lat': 40.70563, 'lon': -73.99635},
    'Queensboro Bridge': {'lat': 40.759, 'lon': -73.955},
    'East 60th St': {'lat': 40.76305, 'lon': -73.96818},
    'Manhattan Bridge': {'lat': 40.7075, 'lon': -73.99077},
    'Lincoln Tunnel': {'lat': 40.760128, 'lon': -74.003065},
    'West Side Highway at 60th St': {'lat': 40.7714, 'lon': -73.9905},
    'Queens Midtown Tunnel': {'lat': 40.7407, 'lon': -73.9588},
    'Williamsburg Bridge': {'lat': 40.71369, 'lon': -73.97262},
    'Holland Tunnel': {'lat': 40.727399, 'lon': -74.021338},
    'Hugh L. Carey Tunnel': {'lat': 40.6958, 'lon': -74.0136},
}

# --- Sidebar Navigation ---
st.sidebar.title("📌 Navigation")
section = st.sidebar.radio(
    "Choose Section:",
    [
        "1. Project Overview",
        "2. Word Cloud of Entry Points",
        "3. Heatmaps of Entry Points",
        "4. Percentage of Entries by Detection Region",
        "5. Average Daily Entries by Vehicle Type",
        "6. Number of Entries by Time",
        "7. Congestion Relief Zone vs. Excluded Roadway Entries"
    ]
)

# --- Section 1: Project Overview ---
if section == "1. Project Overview":
    st.title("🚦 Project Overview")
    st.markdown("""
    This project visualizes the vehicle entry patterns into Manhattan's Congestion Relief Zone (CRZ) under the NYC congestion pricing policy (Jan 5 - Feb 5, 2025).  
    **Key Analyses:**  
    - Entry points distribution  
    - Vehicle type composition  
    - Temporal patterns (hourly, daily, peak/off-peak)  
    - CRZ vs. excluded roadway entries  
    """)
    st.dataframe(df.head())

# --- Section 2: Word Cloud of Entry Points ---
elif section == "2. Word Cloud of Entry Points":
    st.title("🗺️ Word Cloud of Vehicle Entry Points (Detection Groups)")
    st.markdown("""
    The word cloud highlights the most frequently used vehicle entry points into Manhattan’s CRZ. Larger words represent higher traffic volumes at crossings like the Brooklyn Bridge, Queensboro Bridge, and East 60th Street. 

    **Why it Matters?**
    Helps quickly identify major access points for targeted traffic management.            
    """)

    detection_counts = df["Detection Group"].value_counts()

    def generate_wordcloud():
        wordcloud = WordCloud(width=800, height=400, colormap="Blues").generate_from_frequencies(
            detection_counts.to_dict()
        )
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

    generate_wordcloud()
    
# --- Section 3: Heatmaps of Entry Points ---
elif section == "3. Heatmaps of Entry Points":
    st.title("🌉 Heatmaps of Vehicle Entry Points into Manhattan")
    st.markdown(""" 
    The heatmaps show traffic distribution across entry points, with deeper red indicating higher volume. Additional views include labels, markers, and bubble scaling for clarity.
    
    **Key Observation:** 
    Brooklyn Bridge, Queensboro Bridge, and Manhattan Bridge are major congestion hotspots. These entries contribute to increased congestion and longer travel times.

    **Recommended Policy Improvement:**
    Consider increasing the toll at the most congested entry points (Brooklyn, Queensboro, and Manhattan Bridges), instead of charging the same amount for every congested entry point. By using dynamic pricing or peak-time tolls, traffic at specific entry points could be reduced during rush hours.
    """)

    # Add Select View for Heatmap type
    heatmap_choice = st.radio(
        "Select Heatmap View:",
        ["Basic Heatmap", "Heatmap with Labels and Markers", "Bubble Map with Branca Colormap"]
    )

    # Prepare entry data
    entry_data = df.groupby('Detection Group')['CRZ Entries'].sum().reset_index()
    entry_data['lat'] = entry_data['Detection Group'].map(lambda x: entry_points.get(x, {}).get('lat'))
    entry_data['lon'] = entry_data['Detection Group'].map(lambda x: entry_points.get(x, {}).get('lon'))
    entry_data = entry_data.dropna(subset=['lat', 'lon'])

    # Basic Heatmap
    if heatmap_choice == "Basic Heatmap":
        st.subheader("🚗 Basic Heatmap: Traffic Volume at Entry Points")
        map1 = folium.Map(location=[40.758, -73.985], zoom_start=12)
        HeatMap([[row['lat'], row['lon'], row['CRZ Entries']] for _, row in entry_data.iterrows()]).add_to(map1)
        st_folium(map1, width=700, height=500)

    # Heatmap with Labels 
    elif heatmap_choice == "Heatmap with Labels and Markers":
        st.subheader("📍 Heatmap with Labels and Markers")
        map2 = folium.Map(location=[40.758, -73.985], zoom_start=12)
        HeatMap([[row['lat'], row['lon'], row['CRZ Entries']] for _, row in entry_data.iterrows()]).add_to(map2)
        for _, row in entry_data.iterrows():
            popup = folium.Popup(f"{row['Detection Group']}: {row['CRZ Entries']} entries", max_width=200)
            folium.Marker([row['lat'], row['lon']], popup=popup).add_to(map2)
        st_folium(map2, width=700, height=500)

    # Branca Colormap Bubble Map 
    elif heatmap_choice == "Bubble Map with Branca Colormap":
        st.subheader("🌐 Bubble Map with Branca Colormap")
        map3 = folium.Map(location=[40.758, -73.985], zoom_start=12)
        colormap = cm.LinearColormap(['blue', 'purple', 'orange', 'red'],
                                     vmin=entry_data['CRZ Entries'].min(),
                                     vmax=entry_data['CRZ Entries'].max())
        map3.add_child(colormap)
        for _, row in entry_data.iterrows():
            radius = int(np.sqrt(row['CRZ Entries']) / 35)
            color = colormap(row['CRZ Entries'])
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(f"{row['Detection Group']}: {row['CRZ Entries']} entries", max_width=200)
            ).add_to(map3)
        st_folium(map3, width=700, height=500)

# --- Section 4: Percentage of Entries by Detection Region ---
elif section == "4. Percentage of Entries by Detection Region":
    st.title("🗺️ Percentage of Entries by Detection Region")
    st.markdown("""
    This section shows the share of total entries by region. While East 60th Street is significant alone, regions like Brooklyn and Queens contribute larger combined volumes.

    **Why it Matters?**
    Supports region-level congestion management and policy focus. 

    **Key Insights:**
    Brooklyn contributes the highest percentage of entries (over 20%), followed by East 60th St and Queens, which also show substantial traffic volume. FDR Drive, New Jersey, and West 60th St have moderate entries, while West Side Highway has the least.

    **Recommended Policy Improvement:**
    For Brooklyn and Queens, policymakers might want to improve public transportation accessibility by enhancing bus and subway services. Offer subsidies or discounted fares for commuters who opt for public transport instead of driving.
    """)
    
    region_data = df.groupby('Detection Region')['CRZ Entries'].sum().reset_index()
    region_data['Percentage'] = (region_data['CRZ Entries'] / region_data['CRZ Entries'].sum()) * 100
    fig = px.bar(
    region_data,
    x='Detection Region',
    y='Percentage',
    color='Detection Region',
    title='Percentage of CRZ Entries by Detection Region',
    labels={'Percentage': 'Percentage of Entries (%)'}
)

    fig.update_layout(
    title=dict(y=0.9, x=0.45, xanchor="center", yanchor="top"),
    width=1200,
    height=600,
    xaxis_title='Detection Region',
    yaxis_title='Percentage of Entries (%)',
    template='simple_white',
    font=dict(family="Arial", size=14, color="black"),
    showlegend=False
)
    st.plotly_chart(fig, use_container_width=True)

# --- Section 5: Average Daily Entries by Vehicle Type ---
elif section == "5. Average Daily Entries by Vehicle Type":
    st.title("🚗 Average Daily Number of Entries by Vehicle Type")
    st.markdown("""
    The bar chart presents the average daily entries by vehicle category (cars, trucks, buses, etc.).

    **Why it Matters?**
    Understanding traffic composition helps evaluate the tolling policy’s impact across vehicle types.  
    
    **Key Insights:**
    Individual drivers like cars, pickups, and vans make up the vast majority of entries into the CRZ.

    **Recommended Policy Improvement:**
    The policy could offer discounted rates or incentives for high-occupancy vehicles to encourage ride-sharing, carpooling, or using electric vehicles.
    """)
    
    daily_avg = df.groupby(['Toll Date', 'Vehicle Class'])['CRZ Entries'].sum().reset_index()
    daily_avg = daily_avg.groupby('Vehicle Class')['CRZ Entries'].mean().reset_index(name='Average Daily Count')
    fig = px.bar(daily_avg, x='Vehicle Class', y='Average Daily Count',
                 title="Average Daily Number of Entries by Vehicle Type",
                 color='Vehicle Class')
    st.plotly_chart(fig, use_container_width=True)

# --- Section 6: Number of Entries by Time ---
elif section == "6. Number of Entries by Time":
    st.title("🕐 Number of Entries by Time")
    st.markdown("""
    This analysis compares entries during Peak vs. Off-Peak periods and across Days of the Week.

    **Policy Context:**
    Peak hours have higher toll rates to reduce congestion.

    **Why it Matters?**
    Focuses on the comparison between Peak vs. Off-Peak periods.
    
    **Key Insights:** 
    Peak hours during weekdays remain high volume of traffic, regardless of higher toll rates during peak hours. This could be because people who live out of Manhattan but work here have to drive to work during morning and evening commute times, regardless of the toll rates.

    **Recommended Policy Improvement:**
    We don’t think that keep increasing toll rates during peak hours on weekdays could help mitigate congestion during these periods. AND WE DON’T WANT TO DO THIS EITHER!!! Alternatively, ride-sharing programs and incentives for public transportation during weekdays, particularly on Thursday and Friday, when peak congestion is most intense, could help alleviate traffic volumes.
    """)

    # View Options
    view_choice = st.radio(
        "Select View:",
        ["Peak vs. Off-Peak", "By Day of the Week", "Average Daily Entries Over Time", "By Time of Day (10-minute increments)"]
    )

    if view_choice == "Peak vs. Off-Peak":
        daily_avg_detection = df.groupby(['Toll Date', 'Time Period', 'Detection Group'])['CRZ Entries'].sum().reset_index()
        daily_avg_detection = daily_avg_detection.groupby(['Time Period', 'Detection Group'])['CRZ Entries'].mean().reset_index()
        daily_avg_detection = daily_avg_detection.sort_values(by='CRZ Entries', ascending=True)
        pivot = daily_avg_detection.pivot(index='Detection Group', columns='Time Period', values='CRZ Entries').reset_index()
        pivot = pivot.sort_values(by='Peak', ascending=False)
        sorted_detection_groups = pivot['Detection Group'].tolist()

        detection_time_chart = px.bar(
            daily_avg_detection,
            x='CRZ Entries',
            y='Detection Group',
            color='Time Period',
            barmode='group',
            orientation='h',
            title='Average Daily Entries by Detection Group and Time Period',
            labels={'CRZ Entries': 'Count of Entries'},
            category_orders={'Detection Group': sorted_detection_groups, 'Time Period': ['Overnight', 'Peak']}
        )

        detection_time_chart.update_layout(
            title=dict(y=0.9, x=0.55, xanchor="center", yanchor="top"),
            xaxis_title="Entries",
            yaxis_title="Detection Group",
            template='simple_white',
            font=dict(family="Arial", size=14, color="black"),
            width=1000,
            height=600
        )
        st.plotly_chart(detection_time_chart, use_container_width=True)

    elif view_choice == "By Day of the Week":
        dow_avg = df.groupby(['Toll Date', 'Day of Week', 'Time Period'])['CRZ Entries'].sum().reset_index()
        dow_avg = dow_avg.groupby(['Day of Week', 'Time Period'])['CRZ Entries'].mean().reset_index()
        dow_avg = dow_avg.sort_values(['Day of Week', 'Time Period'])

        dow_chart = px.bar(
            dow_avg,
            x='Day of Week',
            y='CRZ Entries',
            color='Time Period',
            barmode='group',
            title='Average Daily Entries by Day of Week and Time Period',
            labels={'CRZ Entries': 'Average Daily Entries', 'Day of Week': 'Day of Week'},
            category_orders={'Day of Week': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                             'Time Period': ['Peak', 'Overnight']},
            color_discrete_sequence=['#EF553B', '#636EFA']
        )

        dow_chart.update_layout(
            title=dict(y=0.9, x=0.45, xanchor="center", yanchor="top"),
            template='simple_white',
            font=dict(family="Arial", size=14, color="black"),
            width=1000,
            height=600,
            legend_title="Time Period"
        )
        st.plotly_chart(dow_chart, use_container_width=True)

    elif view_choice == "Average Daily Entries Over Time":
        daily_totals = df.groupby(['Toll Date', 'Day of Week', 'Time Period'])['CRZ Entries'].sum().reset_index()
        daily_total = daily_totals.groupby(['Toll Date', 'Day of Week', 'Time Period'])['CRZ Entries'].mean().reset_index()
        daily_total['Toll Date'] = pd.to_datetime(daily_total['Toll Date'])

        time_chart = px.line(
            daily_total,
            x='Toll Date',
            y='CRZ Entries',
            color='Time Period',
            title='Average Daily Entries Over Time',
            labels={'CRZ Entries': 'Total Daily Entries', 'Toll Date': 'Date'},
            color_discrete_map={'Peak': '#EF553B', 'Overnight': '#636EFA'}
        )

        time_chart.update_layout(
            title=dict(y=0.9, x=0.45, xanchor="center", yanchor="top"),
            template='simple_white',
            font=dict(family="Arial", size=14, color="black"),
            width=1000,
            height=500,
            legend_title="Time Period"
        )
        time_chart.update_xaxes(tickmode='auto', nticks=13, tickformat='%m-%d')

        # Add shaded weekends
        weekend_dates = daily_total[daily_total['Day of Week'].isin(['Saturday', 'Sunday'])]['Toll Date'].unique()
        for date in weekend_dates:
            date = pd.to_datetime(date)
            next_date = date + pd.Timedelta(days=1)
            time_chart.add_shape(
                type="rect",
                x0=date,
                x1=next_date,
                y0=0,
                y1=1,
                yref="paper",
                fillcolor="lightgray",
                opacity=0.3,
                layer="below",
                line_width=0,
            )
        time_chart.add_annotation(
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.02,
            text="Gray areas indicate weekends",
            showarrow=False,
            font=dict(family="Arial", size=12, color="black"),
            bgcolor="white",
            borderwidth=1,
            borderpad=4,
            opacity=0.8
        )
        time_chart.update_traces(mode='lines+markers', marker=dict(size=6))
        st.plotly_chart(time_chart, use_container_width=True)

    elif view_choice == "By Time of Day (10-minute increments)":
        df['Time'] = pd.to_datetime(df['Toll Hour'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce').dt.strftime('%H:%M')
        time_sums = df.groupby(['Toll Date', 'Time'])['CRZ Entries'].sum().reset_index()
        df_avg_entries = time_sums.groupby('Time')['CRZ Entries'].mean().reset_index()
        df_avg_entries['Time'] = pd.to_datetime(df_avg_entries['Time'], format='%H:%M').dt.strftime('%H:%M')
        df_avg_entries = df_avg_entries.sort_values('Time')

        fig = px.line(
            df_avg_entries,
            x='Time',
            y='CRZ Entries',
            title='CRZ Entries by Time of Day (10-minute increments)',
            labels={'Time': 'Time of Day (10-minute increments)', 'CRZ Entries': 'Average CRZ Entries'},
            line_shape='linear'
        )

        # Add commute hour shading
        fig.add_vrect(x0="06:00", x1="10:00", fillcolor="lightblue", opacity=0.3, line_width=0,
                      annotation_text="Morning Commute Hours", annotation_position="top left")
        fig.add_vrect(x0="16:00", x1="20:00", fillcolor="lightblue", opacity=0.3, line_width=0,
                      annotation_text="Evening Commute Hours", annotation_position="top left")

        fig.update_layout(
            template='simple_white',
            title=dict(y=0.9, x=0.45, xanchor="center", yanchor="top"),
            xaxis_title='Time of Day (10-minute increments)',
            yaxis_title='Average CRZ Entries',
            font=dict(family="Arial", size=14, color="black"),
            width=1200,
            height=600,
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)

# --- Section 7: Congestion Relief Zone vs. Excluded Roadway Entries ---
elif section == "7. Congestion Relief Zone vs. Excluded Roadway Entries":
    st.title("🚧 CRZ vs. Excluded Roadway Entries")
    st.markdown("""
    Excluded Roadway Entries refer to trips solely on the **FDR Drive**, the **West Side Highway**, and/or any surface roadway portion of the **Hugh L. Carey Tunnel** connecting to West Street (the “Excluded Roadways”).

    **Why this Matters?**  
    - Understand traffic distribution between tolled CRZ entries and toll-free excluded routes.  
    - Evaluate the effectiveness of the congestion pricing policy.  
    - Identify potential congestion shifts to excluded roadways.  

    **Key Insights:**
    CRZ Entries, compared to Excluded Roadways, remain consistently high across all days, regardless of the toll rates.

    **Recommended Policy Improvement:**
    Considering the lower volume of Excluded Roadway Entries, the city could promote the use of these roads through incentives or temporary toll-free periods to help distribute traffic more evenly.
    """)

    # Filter for Jan 5 - Jan 25, 2025 (as per your original logic)
    df_filtered = df[
    (df['Toll Date'] >= datetime.date(2025, 1, 5)) &
    (df['Toll Date'] <= datetime.date(2025, 1, 25))
]

    # Group by 'Toll Date' and sum CRZ and Excluded Roadway entries
    daily_entries = df_filtered.groupby('Toll Date')[['CRZ Entries', 'Excluded Roadway Entries']].sum().reset_index()

    # Create the stacked bar chart
    fig = px.bar(
        daily_entries,
        x='Toll Date',
        y=['CRZ Entries', 'Excluded Roadway Entries'],
        title='Daily Entries to CRZ and Excluded Roadways (Jan 5 - Jan 25)',
        labels={'Toll Date': 'Date', 'value': 'Daily Entries', 'variable': 'Entry Type'},
        color_discrete_sequence=['#0074CC', '#C1D3F7']
    )

    # Customize layout
    fig.update_layout(
        barmode='stack',
        xaxis_title='Date',
        yaxis_title='Daily Entries',
        template='simple_white',
        width=1200,
        height=600,
        title=dict(y=0.9, x=0.45, xanchor="center", yanchor="top"),
        yaxis=dict(tickmode='array', tickvals=[0, 200000, 400000, 600000]),
        font=dict(family="Arial", size=14, color="black")
    )

    st.plotly_chart(fig, use_container_width=True)

st.caption("2025 MTA Congestion Data Visualization · Group_G")
