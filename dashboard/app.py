import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client

# ---------------------------------
# Page configuration
# ---------------------------------
st.set_page_config(
    page_title="VibraTank Dashboard",
    page_icon="💧",
    layout="wide"
)

# ---------------------------------
# Custom design
# ---------------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0B1220, #111D32);
    color: #F8FAFC;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: #38BDF8 !important;
    font-weight: 700 !important;
}

p, label {
    color: #E2E8F0;
}

[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"] p {
    color: #CBD5E1 !important;
    opacity: 1 !important;
}

div[data-baseweb="select"] > div {
    background-color: #1E3350 !important;
    border: 1px solid #47749A !important;
    border-radius: 10px !important;
    color: white !important;
}

div[data-baseweb="select"] span {
    color: white !important;
}

div[role="listbox"] {
    background-color: #1E3350 !important;
}

div[role="option"] {
    color: white !important;
}

.sensor-card {
    background: #182A43;
    border: 1px solid #304966;
    padding: 22px;
    border-radius: 16px;
    margin-bottom: 15px;
}

.sensor-label {
    color: #CBD5E1;
    font-size: 15px;
    font-weight: 500;
}

.sensor-value {
    font-size: 32px;
    font-weight: 700;
    margin-top: 8px;
}

.status-card {
    padding: 18px;
    border-radius: 12px;
    margin: 12px 0 25px 0;
    font-weight: 600;
}

.normal {
    background: #103D39;
    color: #6EE7B7;
    border: 1px solid #10B981;
}

.warning {
    background: #4A202B;
    color: #FDA4AF;
    border: 1px solid #FB7185;
}

.waiting {
    background: #193653;
    color: #93C5FD;
    border: 1px solid #3B82F6;
}

.alert-box {
    background: #182A43;
    color: #CBD5E1;
    border-radius: 12px;
    padding: 18px;
    border: 1px solid #304966;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------
# Supabase connection
# ---------------------------------
SENSOR_COLUMNS = {
    "mic1": "Microphone 1",
    "mic2": "Microphone 2",
    "mic3": "Microphone 3",
    "mic4": "Microphone 4",
    "vibration": "Vibration Sensor"
}

sensor_colors = {
    "Microphone 1": "#38BDF8",
    "Microphone 2": "#A78BFA",
    "Microphone 3": "#F472B6",
    "Microphone 4": "#FBBF24",
    "Vibration Sensor": "#34D399"
}


@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def load_sensor_data():
    client = get_supabase_client()

    response = (
        client.table("sensor_readings")
        .select(
            "id,created_at,device_id,"
            "mic1,mic2,mic3,mic4,vibration,status"
        )
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )

    return pd.DataFrame(response.data or [])


# ---------------------------------
# Header
# ---------------------------------
st.title("VibraTank Dashboard")
st.subheader("Water Tank Leak Detection System")
st.write("Monitoring sound and vibration signals")

st.divider()

# ---------------------------------
# Load readings
# ---------------------------------
try:
    readings = load_sensor_data()
    connection_error = None

except Exception as error:
    readings = pd.DataFrame()
    connection_error = error

if connection_error is not None:
    st.error(
        "Unable to load sensor readings from Supabase. "
        "Check the connection settings and read permissions."
    )
    st.caption(
        "The dashboard is not showing live readings."
    )
    st.stop()

if readings.empty:
    st.info("No sensor readings are available yet.")
    st.stop()

readings["created_at"] = pd.to_datetime(
    readings["created_at"],
    errors="coerce",
    utc=True
)

readings = readings.sort_values(
    ["created_at", "id"],
    ascending=[True, True]
)

for column in SENSOR_COLUMNS:
    readings[column] = pd.to_numeric(
        readings[column],
        errors="coerce"
    )

latest = readings.iloc[-1]

# ---------------------------------
# System status
# ---------------------------------
st.header("System Status")

status = latest.get("status", "Waiting")

if status == "Normal":
    st.markdown(
        '<div class="status-card normal">'
        'System Normal - No leak detected'
        '</div>',
        unsafe_allow_html=True
    )

elif status == "Potential Leak":
    st.markdown(
        '<div class="status-card warning">'
        'Warning: Potential Leak Detected'
        '</div>',
        unsafe_allow_html=True
    )

else:
    st.markdown(
        '<div class="status-card waiting">'
        'Waiting for Sensor Data'
        '</div>',
        unsafe_allow_html=True
    )

device_id = latest.get("device_id", "Unknown")
reading_time = latest.get("created_at")

st.caption(f"Device: {device_id}")

if pd.notna(reading_time):
    st.caption(
        "Latest reading: "
        + reading_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    )

# ---------------------------------
# Sensor readings
# ---------------------------------
st.header("Sensor Readings")

cols = st.columns(4)

for index, (column, sensor) in enumerate(
    SENSOR_COLUMNS.items()
):
    value = latest[column]

    if pd.isna(value):
        display_value = "N/A"
    else:
        display_value = f"{value:.2f}"

    with cols[index % 4]:
        color = sensor_colors[sensor]

        st.markdown(
            f"""
            <div class="sensor-card">
                <div class="sensor-label">{sensor}</div>
                <div class="sensor-value"
                     style="color:{color};">
                    {display_value}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

if all(pd.isna(latest[column]) for column in SENSOR_COLUMNS):
    st.caption(
        "No numeric sensor values received yet."
    )

st.divider()

# ---------------------------------
# Signal charts
# ---------------------------------
st.header("Signal Charts")

fig = go.Figure()

has_chart_data = False

for column, sensor in SENSOR_COLUMNS.items():
    valid = readings[
        readings["created_at"].notna()
        & readings[column].notna()
    ]

    if valid.empty:
        continue

    has_chart_data = True

    fig.add_trace(
        go.Scatter(
            x=valid["created_at"],
            y=valid[column],
            mode="lines+markers",
            name=sensor,
            line=dict(
                color=sensor_colors[sensor],
                width=3
            ),
            marker=dict(size=6)
        )
    )

fig.update_layout(
    paper_bgcolor="#182A43",
    plot_bgcolor="#182A43",
    font=dict(color="#E2E8F0"),
    height=450,
    margin=dict(l=30, r=30, t=35, b=90),
    xaxis=dict(
        title="Reading Time (UTC)",
        gridcolor="#304966",
        zeroline=False
    ),
    yaxis=dict(
        title="Signal Value",
        gridcolor="#304966",
        zeroline=False
    ),
    legend=dict(
        orientation="h",
        y=-0.3,
        x=0,
        font=dict(color="#FFFFFF", size=13),
        bgcolor="rgba(0,0,0,0)"
    ),
    hovermode="x unified"
)

if has_chart_data:
    st.plotly_chart(
        fig,
        use_container_width=True
    )
else:
    st.info(
        "Waiting for numeric sensor readings "
        "to display the charts."
    )

st.divider()

# ---------------------------------
# Leak alerts
# ---------------------------------
st.header("Leak Alerts")

if status == "Potential Leak":
    st.markdown(
        '<div class="status-card warning">'
        'Potential leak detected. '
        'Please inspect the water tank.'
        '</div>',
        unsafe_allow_html=True
    )

elif status == "Normal":
    st.markdown(
        '<div class="status-card normal">'
        'No active leak alerts. '
        'System operating normally.'
        '</div>',
        unsafe_allow_html=True
    )

else:
    st.markdown(
        '<div class="alert-box">'
        'No active alerts - Waiting for sensor data.'
        '</div>',
        unsafe_allow_html=True
    )

st.caption(
    "Data source: Supabase / sensor_readings. "
    "Use Refresh in your browser to fetch new readings."
)