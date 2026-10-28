import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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

/* Dropdown */
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

/* Sensor cards */
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

/* Status cards */
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
# Header
# ---------------------------------
st.title("VibraTank Dashboard")
st.subheader("Water Tank Leak Detection System")
st.write("Monitoring sound and vibration signals")

st.divider()

# ---------------------------------
# System status
# ---------------------------------
st.header("System Status")

status = st.selectbox(
    "Select system status (Demo)",
    [
        "Waiting for Sensor Data",
        "Normal",
        "Potential Leak"
    ]
)

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

# ---------------------------------
# Sensor readings
# ---------------------------------
st.header("Sensor Readings")

sensor_values = {
    "Microphone 1": 0.42,
    "Microphone 2": 0.38,
    "Microphone 3": 0.45,
    "Microphone 4": 0.40,
    "Vibration Sensor": 0.15
}

sensor_colors = {
    "Microphone 1": "#38BDF8",
    "Microphone 2": "#A78BFA",
    "Microphone 3": "#F472B6",
    "Microphone 4": "#FBBF24",
    "Vibration Sensor": "#34D399"
}

cols = st.columns(4)

for index, (sensor, value) in enumerate(sensor_values.items()):
    with cols[index % 4]:
        color = sensor_colors[sensor]

        st.markdown(
            f"""
            <div class="sensor-card">
                <div class="sensor-label">{sensor}</div>
                <div class="sensor-value"
                     style="color:{color};">
                    {value:.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.caption("Demo values only - No sensors connected")

st.divider()

# ---------------------------------
# Signal charts
# ---------------------------------
st.header("Signal Charts")

data = pd.DataFrame({
    "Microphone 1": [
        0.20, 0.40, 0.30, 0.60, 0.38, 0.55, 0.70
    ],
    "Microphone 2": [
        0.18, 0.38, 0.28, 0.55, 0.35, 0.50, 0.65
    ],
    "Microphone 3": [
        0.25, 0.35, 0.42, 0.48, 0.40, 0.52, 0.60
    ],
    "Microphone 4": [
        0.15, 0.30, 0.28, 0.40, 0.32, 0.45, 0.55
    ],
    "Vibration Sensor": [
        0.10, 0.15, 0.12, 0.20, 0.16, 0.22, 0.25
    ]
})

fig = go.Figure()

for sensor in data.columns:
    fig.add_trace(
        go.Scatter(
            x=list(range(len(data))),
            y=data[sensor],
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
    margin=dict(l=30, r=30, t=35, b=35),
    xaxis=dict(
        title="Time Samples",
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
    y=-0.25,
    x=0,
    font=dict(
        color="#FFFFFF",
        size=15
    ),
    bgcolor="rgba(0,0,0,0)"
),
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.caption("Simulated signal data for demonstration only")

st.divider()

# ---------------------------------
# Leak alerts
# ---------------------------------
st.header("Leak Alerts")

if status == "Potential Leak":
    st.markdown(
        '<div class="status-card warning">'
        'Potential leak detected. Please inspect the water tank.'
        '</div>',
        unsafe_allow_html=True
    )

elif status == "Normal":
    st.markdown(
        '<div class="status-card normal">'
        'No active leak alerts. System operating normally.'
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