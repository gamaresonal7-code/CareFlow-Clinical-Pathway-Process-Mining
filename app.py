
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="CareFlow",
    page_icon="🏥",
    layout="wide"
)

st.title("CareFlow: Clinical Pathway Process Mining")
st.caption("Prototype using synthetic sample data")

# Load the event log
@st.cache_data
def load_data():
    data = pd.read_csv("clinical_events.csv")
    data["timestamp"] = pd.to_datetime(
        data["timestamp"], errors="coerce"
    )
    data = data.dropna(
        subset=["case_id", "activity", "timestamp"]
    )
    return data.sort_values(["case_id", "timestamp"])


try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "clinical_events.csv must be in the same folder as app.py."
    )
    st.stop()

if df.empty:
    st.error("No valid data found.")
    st.stop()

# Calculate patient journey duration
case_times = df.groupby("case_id")["timestamp"].agg(
    ["min", "max"]
)
case_times["duration_minutes"] = (
    case_times["max"] - case_times["min"]
).dt.total_seconds() / 60

total_patients = df["case_id"].nunique()
total_events = len(df)
average_duration = case_times["duration_minutes"].mean()

# Dashboard metrics
col1, col2, col3 = st.columns(3)

col1.metric("Patient Cases", total_patients)
col2.metric("Recorded Activities", total_events)
col3.metric(
    "Average Journey Duration",
    f"{average_duration:.1f} minutes"
)

# Activity frequency chart
st.subheader("Activity Frequency")

activity_counts = (
    df["activity"]
    .value_counts()
    .rename_axis("Activity")
    .reset_index(name="Count")
)

fig1 = px.bar(
    activity_counts,
    x="Activity",
    y="Count",
    title="Number of Recorded Activities"
)

st.plotly_chart(fig1, use_container_width=True)

# Patient journey visualization
st.subheader("Patient Journey")

selected_case = st.selectbox(
    "Select a patient case",
    sorted(df["case_id"].unique())
)

patient_data = df[df["case_id"] == selected_case]

fig2 = px.scatter(
    patient_data,
    x="timestamp",
    y="activity",
    color="department",
    hover_data=["case_id"],
    title=f"Journey for {selected_case}"
)

fig2.update_traces(marker_size=12)
st.plotly_chart(fig2, use_container_width=True)

# Time between consecutive activities
st.subheader("Elapsed Time Between Activities")

df["next_activity"] = (
    df.groupby("case_id")["activity"].shift(-1)
)

df["next_timestamp"] = (
    df.groupby("case_id")["timestamp"].shift(-1)
)

df["elapsed_minutes"] = (
    df["next_timestamp"] - df["timestamp"]
).dt.total_seconds() / 60

transitions = df.dropna(
    subset=["next_activity", "elapsed_minutes"]
).copy()

if not transitions.empty:
    transitions["Transition"] = (
        transitions["activity"]
        + " → "
        + transitions["next_activity"]
    )

    summary = (
        transitions.groupby("Transition")["elapsed_minutes"]
        .mean()
        .reset_index()
        .sort_values("elapsed_minutes", ascending=False)
    )

    summary.columns = ["Transition", "Average Minutes"]

    st.dataframe(summary, use_container_width=True)

    fig3 = px.bar(
        summary,
        x="Transition",
        y="Average Minutes",
        title="Average Elapsed Time Between Activities"
    )

    st.plotly_chart(fig3, use_container_width=True)

# Display data
st.subheader("Event Log Data")
st.dataframe(df, use_container_width=True)

st.info(
    "This is a demonstration using synthetic data. "
    "Elapsed time between events is not necessarily actual "
    "waiting time. Validate findings with suitable real-world "
    "data before drawing clinical conclusions."
)
