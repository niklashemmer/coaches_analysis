import streamlit as st
import os
import datetime
import plotly.express as px
import pandas as pd
pd.set_option('display.max_columns', None)

###################### LOAD IN THE DATA ##########################

file_path = os.path.join(os.path.dirname(__file__), "data", "streamlit_22-12-17.csv")
df = pd.read_csv(file_path, index_col=None)
file_path2 = os.path.join(os.path.dirname(__file__), "data", "coaches_summary_22-12.17.csv")
df_summary = pd.read_csv(file_path2, index_col=None)
big_five = ["FRA-Ligue 1", "ESP-La Liga", "GER-Bundesliga", "ITA-Serie A", "ENG-Premier League"]

###################### CREATE STREAMLIT APP ##########################

st.set_page_config(page_title="Plus/Minus Rating of Coaches", layout="wide")

# --- SIDEBAR ---
st.sidebar.header("Please Filter here:")

# Get the current date and time
now = datetime.datetime.now()

# Format the date and time as a string
last_updated = now.strftime("%b %d, %Y %I:%M %p")

st.sidebar.write(f"Last updated: {last_updated}")

# Get leagues
league = st.sidebar.multiselect(
    "Select League:",
    options=df_summary["League"].unique(),
    default=big_five
)

# Get seasons
season = st.sidebar.multiselect(
    "Select Season:",
    options=df_summary["Season"].sort_values().unique(),
    default=df_summary["Season"].sort_values().unique()
)

# Filter new dataframe
df_summary_selection = df_summary.query(
    "League == @league & Season == @season"
)

# --- HEADER ---

# Set header and add explanation
st.title("Plus/Minus Rating of Coaches")
st.write("This tool compares the actual points of clubs to point predictions of FiveThirtyEight at the start of the season. Over- or underperformance is ascribed to the coaches. The data goes back to 2018/2019 and includes multiple leagues across Europe. The seasons and leagues can be filtered on the left side.") #The data table below shows coaches and their achievements per season. By checking the box, one can analyze coaches on an aggregated level of the past seasons. The chart at the bottom displays updated expectations over the course of one season.")
st.markdown('''##### <span style="color:black">Evaluate football coaches based on their over-/underperformance of expected points</span>
            ''', unsafe_allow_html=True)
#tab_coach, tab_season = st.tabs(["Coach total", "Coach per Season"])


# --- DATA TABLE ---

# Enable to aggregate based on coaches' career performance
coach_level = st.checkbox("Aggregated numbers (Check if you want to analyze coaches over their career instead of individual seasons)")

# Display an interactive table
if coach_level:
    df_summary_selection = df_summary_selection.groupby(["Name"]).agg({
        "Matches": "sum",
        "Expectation":"sum",
        "Result":"sum",
        "Difference":"sum"
    }).sort_values(by="Difference", ascending=False).reset_index()
else:
    df_summary_selection = df_summary_selection.sort_values(by="Difference", ascending=False).reset_index(drop=True)

st.dataframe(df_summary_selection.style.format(subset=['Difference', 'Expectation', 'Result'], formatter="{:.1f}"))

# Add space
st.write("##")


# --- SCATTER PLOT ---

# Enable to aggregate based on coaches' career performance
coach_scatter = st.checkbox("Scatterplot with aggregated numbers (Check if you want to analyze coaches over their career instead of individual seasons)")

# New datafame incl. filters
df_scatter_filter = df_summary.query(
    "League == @league & Season == @season"
)

if coach_scatter:
    df_scatter = df_scatter_filter.groupby(["Name"]).agg({
        "Matches": "sum",
        "Expectation":"sum",
        "Result":"sum",
        "Difference":"sum"
    }).sort_values(by="Difference", ascending=False).reset_index()
else:
    df_scatter = df_scatter_filter

# Plot scatter plot
x = df_scatter["Matches"]
y = df_scatter["Difference"].round(1)
fig = px.scatter(
    df_scatter,
    x=x,
    y=y,
    labels = {
        "Matches": "Number of matches",
        "y": "Over-/Underachievement",
        "Coach_ID":"Coach_ID"
    },
    #height=600,
    #title="<b>Over-/underachievement of expected points per coach</b>",
    template="plotly_white",
    hover_data=['Name'] if coach_scatter else ["Coach_ID"]
)

# Add red and green rectangle do highlight over-/underperformance
fig.add_hrect(y0=0, y1=df_scatter["Difference"].min()-3, line_width=0, fillcolor="red", opacity=0.07)
fig.add_hrect(y0=0, y1=df_scatter["Difference"].max()+3, line_width=0, fillcolor="green", opacity=0.07)

# Add annotation to the rectangles
if coach_scatter:
    fig.add_annotation(text="Overachieved expectations", x=df_scatter["Matches"].min()+18, 
                       y=df_scatter["Difference"].max()-3, showarrow=False, font=dict(color="green", size=12))
    fig.add_annotation(text="Underachieved expectations", x=df_scatter["Matches"].min()+18, 
                       y=df_scatter["Difference"].min()+3, showarrow=False, font=dict(color="red", size=12))
else:
    fig.add_annotation(text="Overachieved expectations", x=df_scatter["Matches"].min() + 4,
                       y=df_scatter["Difference"].max() - 1, showarrow=False, font=dict(color="green", size=12))
    fig.add_annotation(text="Underachieved expectations", x=df_scatter["Matches"].min() + 4,
                       y=df_scatter["Difference"].min() + 1, showarrow=False, font=dict(color="red", size=12))

# Add horizontal line
fig.add_hline(y=0)

# Change marker of scatter plot
fig.update_traces(marker_size=10, marker_color="#004CFF", marker_line_color="black")

fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(
        range=[0, x.max()+1]
    ),
    font=dict(size=12)
)

st.plotly_chart(fig, use_container_width=True, use_container_height=True)

st.markdown("---")


# --- PERFORMANCE LINE CHART ---

st.markdown('''##### <span style="color:black">Tracking Performance: Updated expected points over a season</span>
            ''', unsafe_allow_html=True)

# Filter for coaches with at least 10 games per season
df_10 = df.groupby("Coach_ID").agg({"Matches":"count"}).reset_index()
df_10 = df_10[df_10["Matches"] >= 10]
limit = df_10["Coach_ID"].tolist()
df_player_select = df[df["Coach_ID"].isin(limit)]

# Select a coach to be displayed
player = st.selectbox("Choose a Coach_ID: Coach-Club-Season", df_player_select["Coach_ID"].unique())

df_coach = df.query(
    "Coach_ID == @player"
).reset_index()

x2 = df_coach["Matches"]
y2 = df_coach["Points"]
constant = df_coach["Points"].iloc[0]

fig2 = px.line(
    x=x2,
    y=y2,
    labels = {
        "Matches": "Date",
        "Points": "Updated expected points",
        "Coach_ID":"Coach_ID",
        "x":"Date",
        "y":"Updated expected points"
    },
    markers=True
)

# Update layout
fig2.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(
        range=[constant-20, constant+20],
        tickmode="auto"
    ),
    font=dict(size=12)
)

fig2.update_traces(line=dict(color="black"))

# Add horizontal line to illustrate expectations at the beginning
fig2.add_hline(y=constant,
               annotation_text="Expected points\nat season start",
               annotation_position="bottom right",
               line_width=0.5)

st.plotly_chart(fig2, use_container_width=True, use_container_height=True)
