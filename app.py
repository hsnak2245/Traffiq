import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Custom CSS
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"]  {
        font-family: 'Space Grotesk', sans-serif;
        background-color: #000000;
        color: #00f7ff;
    }
    .stTextInput>div>div>input {
        color: #00f7ff;
        border-color: #00f7ff;
    }
    .st-bd {
        background-color: #000;
    }
    .stButton>button {
        border: 1px solid #00f7ff;
        color: #00f7ff;
        background: #000;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background: #001f24;
        color: #00f7ff;
        border-color: #00f7ff;
    }
    .metric {
        border: 1px solid #00f7ff;
        padding: 1rem;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'chat_open' not in st.session_state:
    st.session_state.chat_open = False

# Main App
def main():
    st.title("TraffiQ")
    st.markdown("### Traffic Intelligence for Qatar")

    # Chat Interface
    with st.container():
        st.markdown("<div style='text-align:center; margin: 2rem 0;'>", unsafe_allow_html=True)
        user_input = st.chat_input("Ask anything about traffic data...")
        st.markdown("</div>", unsafe_allow_html=True)

    # Analytics Buttons Grid
    cols = st.columns(5)
    buttons = [
        ("Accidents", "🚑", "#accidents"),
        ("Violations", "🚔", "#violations"),
        ("License", "📇", "#license"),
        ("Vehicle", "🚗", "#vehicle"),
        ("Environment", "🌳", "#environment")
    ]
    
    for col, (label, icon, _) in zip(cols, buttons):
        with col:
            st.button(f"{icon} {label}", use_container_width=True)

    # Key Stats Grid
    st.header("Key Statistics")
    stats_cols = st.columns(4)
    metrics = [("Total Accidents", "12,345"), ("Daily Violations", "892"), 
              ("Licenses Issued", "3,451"), ("CO2 Saved (tons)", "45,678")]
    
    for col, (label, value) in zip(stats_cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric">
                <h3>{label}</h3>
                <h1>{value}</h1>
            </div>
            """, unsafe_allow_html=True)

    # Dashboard Sections
    tab_labels = [f"{icon} {label}" for (label, icon, _) in buttons]
    tabs = st.tabs(tab_labels)
    
    # Generate Sample Plots
    for i, tab in enumerate(tabs):
        with tab:
            fig = go.Figure()
            x = ['2020', '2021', '2022', '2023']
            y = np.random.randint(1000, 5000, size=4)
            
            fig.add_trace(go.Bar(
                x=x, y=y,
                marker_color='#00f7ff',
                marker_line_color='#00f7ff',
                marker_line_width=1
            ))
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#00f7ff',
                title=f"{buttons[i][0]} Trends",
                xaxis_title="Year",
                yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Feedback Section
    st.header("Feedback & Trivia")
    with st.expander("Test Your Knowledge"):
        q1 = st.radio("Q1: Qatar has zero road fatalities in 2022", ["Fact", "Fiction"])
        q2 = st.radio("Q2: Doha has smart traffic light system", ["Fact", "Fiction"])
        q3 = st.radio("Q3: Electric vehicles are tax-free in Qatar", ["Fact", "Fiction"])

if __name__ == "__main__":
    main()
