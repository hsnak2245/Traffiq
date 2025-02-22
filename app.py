import streamlit as st
import pandas as pd
from groq import Groq

# Initialize Groq client
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
groq_client = Groq(api_key=GROQ_API_KEY)

# Configure page
st.set_page_config(
    page_title="TraffiQ",
    page_icon="🚦",
    layout="wide"
)

# Modern UI styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Global styles */
body {
    font-family: 'Inter', sans-serif;
    color: #f8fafc;
    background-color: #0f172a;
    min-height: 100vh;
}

.main {
    position: relative;
    z-index: 2;
}

.stApp {
    background: transparent !important;
}

/* Background Effects */
.background-container {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 0;
    pointer-events: none;
}

/* Gradient background */
.gradient-bg {
    position: absolute;
    width: 100%;
    height: 100%;
    background: 
        radial-gradient(circle at 10% 0%, rgba(236, 72, 153, 0.3), transparent 50%),
        radial-gradient(circle at 90% 0%, rgba(59, 130, 246, 0.3), transparent 50%),
        radial-gradient(circle at 100% 100%, rgba(6, 182, 212, 0.3), transparent 50%);
}

/* Halftone pattern */
.halftone {
    position: absolute;
    width: 100%;
    height: 100%;
    background-image: 
        radial-gradient(circle at center,
            rgba(255, 255, 255, 0.1) 2px,
            transparent 2px
        );
    background-size: 24px 24px;
    background-position: 0 0;
    opacity: 0.4;
    mask-image: linear-gradient(to bottom,
        rgba(0, 0, 0, 1) 0%,
        rgba(0, 0, 0, 0.7) 50%,
        rgba(0, 0, 0, 0.5) 100%
    );
}

/* Header styling */
.header {
    padding: 2rem 0;
    margin-bottom: 2rem;
    position: relative;
    z-index: 2;
}

.logo {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(45deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 1rem;
    position: relative;
    z-index: 2;
    text-shadow: 
        0 0 10px rgba(56, 189, 248, 0.5),
        0 0 20px rgba(56, 189, 248, 0.3),
        0 0 30px rgba(129, 140, 248, 0.2);
    animation: glow 3s ease-in-out infinite alternate;
}

@keyframes glow {
    from {
        text-shadow: 
            0 0 10px rgba(56, 189, 248, 0.5),
            0 0 20px rgba(56, 189, 248, 0.3),
            0 0 30px rgba(129, 140, 248, 0.2);
    }
    to {
        text-shadow: 
            0 0 20px rgba(56, 189, 248, 0.6),
            0 0 30px rgba(56, 189, 248, 0.4),
            0 0 40px rgba(129, 140, 248, 0.3);
    }
}

/* Feature Grid */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 2.5rem;
    max-width: 1000px;
    margin: 2rem auto;
    padding: 2rem;
    position: relative;
    z-index: 2;
}

.feature-card {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 2rem;
    margin: 0.5rem;
    transition: all 0.3s ease;
    backdrop-filter: blur(12px);
    height: 100%;
    display: flex;
    flex-direction: column;
    position: relative;
    z-index: 2;
}

.feature-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(6, 182, 212, 0.15);
    border-color: rgba(6, 182, 212, 0.4);
}

.feature-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.feature-title {
    color: #38bdf8;
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.feature-description {
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.875rem;
    margin-bottom: 1rem;
    line-height: 1.4;
    flex-grow: 1;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.view-link {
    display: inline-block;
    background: linear-gradient(135deg, #0a4f6d 0%, #063c5a 100%);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 0.875rem;
    text-decoration: none;
    transition: all 0.3s ease;
    text-align: center;
    margin-top: auto;
}

.view-link:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(6, 182, 212, 0.3);
    text-decoration: none;
    color: white;
}

/* Chat interface */
.chat-container {
    max-width: 800px;
    max-height: 
    margin: 2rem auto;
    padding: 2rem;
    background: rgba(15, 23, 42, 0);
    border-radius: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(12px);
    position: relative;
    z-index: 2;
}

.message {
    margin: 1rem 0;
    padding: 1rem;
    border-radius: 0.75rem;
    line-height: 1.5;
}

.user-message {
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.2);
    margin-left: auto;
    width: 80%;
}

.bot-message {
    background: rgba(129, 140, 248, 0.1);
    border: 1px solid rgba(129, 140, 248, 0.2);
    margin-right: auto;
    width: 80%;
}

/* Input styling */
.stTextInput > div > div > input {
    background: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid #475569 !important;
    border-radius: 0.75rem !important;
    color: #f8fafc !important;
    font-size: 1rem !important;
    padding: 1.5rem !important;
    height: 3.5rem !important;
    box-shadow: 
        0 0 10px rgba(56, 189, 248, 0.1),
        0 0 20px rgba(56, 189, 248, 0.05) !important;
    transition: all 0.3s ease !important;
}

.stTextInput > div > div > input:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2) !important;
    box-shadow: 
        0 0 10px rgba(56, 189, 248, 0.2),
        0 0 20px rgba(56, 189, 248, 0.1),
        0 0 30px rgba(56, 189, 248, 0.05) !important;
    outline: none !important;
}
.stTextInput > div {
    padding: 0.5rem 0 !important;
}

/*Adding effects to the chatbox*/
/* Chat input container */
section[data-testid="stChatInputContainer"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    background: transparent !important;
    padding: 1rem !important;
    z-index: 100 !important;
}

/* Target the textarea wrapper */
.stChatInputContainer > div {
    background: transparent !important;
    padding: 0 !important;
}

/* Target the actual input element */
.stChatInputContainer textarea {
    background: transparent !important;
    border: 2px solid rgba(56, 189, 248, 0.3) !important;
    border-radius: 0.75rem !important;
    color: #f8fafc !important;
    font-size: 1rem !important;
    min-height: 60px !important;
    padding: 1rem !important;
    box-shadow: 
        0 0 10px rgba(56, 189, 248, 0.1),
        0 0 20px rgba(56, 189, 248, 0.05) !important;
    transition: all 0.3s ease !important;
}

/* Focus state */
.stChatInputContainer textarea:focus {
    border-color: #38bdf8 !important;
    box-shadow: 
        0 0 10px rgba(56, 189, 248, 0.2),
        0 0 20px rgba(56, 189, 248, 0.1),
        0 0 30px rgba(56, 189, 248, 0.05) !important;
    outline: none !important;
}

/* Send button container */
.stChatInputContainer > button {
    border-color: rgba(56, 189, 248, 0.3) !important;
    background: transparent !important;
    box-shadow: 
        0 0 10px rgba(56, 189, 248, 0.1),
        0 0 20px rgba(56, 189, 248, 0.05) !important;
}

/* Send button hover state */
.stChatInputContainer > button:hover {
    border-color: #38bdf8 !important;
    box-shadow: 
        0 0 10px rgba(56, 189, 248, 0.2),
        0 0 20px rgba(56, 189, 248, 0.1),
        0 0 30px rgba(56, 189, 248, 0.05) !important;
}

/* Hide Streamlit elements */
#MainMenu, footer, header {display: none !important;}

/* Spinner */
.stSpinner > div > div {
    border-color: #60a5fa !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: #1e293b;
}

::-webkit-scrollbar-thumb {
    background: #475569;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: #60a5fa;
}
</style>

<!-- Background container -->
<div class="background-container">
    <div class="gradient-bg"></div>
    <div class="halftone"></div>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

@st.cache_data
def load_knowledge_base():
    data = {
        'message': [
            "Qatar recorded a 15% decrease in traffic accidents in urban areas after implementing smart traffic systems.",
            "Recent policy changes require mandatory defensive driving courses for new license applicants in Qatar.",
            "Traffic safety indicators show peak accident times between 7-9 AM and 4-6 PM in major Qatar cities.",
            "New traffic policy focuses on reducing accidents through AI-powered traffic management and stricter enforcement.",
            "Qatar's road safety campaign resulted in 25% reduction in pedestrian accidents in residential areas.",
            "Annual Average Accidents (2020+): 197,800+ incidents/year",
            "Total Recorded Deaths: 976 fatalities",
            "Pedestrian Collision Deaths: 227 fatalities",
            "Total Accidents: 988,800+ incidents",
            "Annual Average: 197.8K+",
            "Fatality Statistics: 976 total deaths (227 pedestrian)",
            "Total Incident Volume: 988.8K+",
            "Accident Distribution by Nationality Groups",
            "Nationality Group Distribution: AFRIC: ~25,000 accidents, ARABI: ~225,000 accidents, ASIA: ~375,000 accidents, QATAR: ~150,000 accidents",
            "Severity Types Recorded: Death Injury, Heavy Injury, Light Injury, Simple, Non-Traffic Accident (Death/Heavy Injury)",
            "Types of Accidents: Collision Types: Animal: ~100,000 cases, Fixed object: ~10,000 cases, Vehicles: ~5,000 cases, Pedestrians: Present in data",
            "Other Incident Types: Fall from car, Inversion, Non-collision, Claim converted to accident",
            "Accident Reasons: Categories by Severity: Death: ~1,000 cases, Drunk: ~1,500 cases, Other: ~12,000 cases (Simple: ~7,000, Light injury: ~4,000, Heavy injury: ~1,000), Cost: Minimal cases",
            "Severity Distribution: Simple incidents: Majority, Light injuries: Second most common, Death and heavy injury: Less frequent but significant",
            "Age Distribution of Accidents: Mean Age: 37.4 years, Age Range: 20-80 years",
            "Age Group Distribution: Peak Frequency: Ages 35-40 (~6,000 accidents), Secondary Peak: Ages 30-35 (~5,500 accidents), Pattern: Low below 20, sharp increase 20-30, highest 35-40, decline 40-60, drop after 60, minimal after 80",
            "Geographical Distribution of Accidents (2020-2023): Zone Statistics by Year: 2024: Al Rayyan - Bu Hamour, Ain Khaled: 20,380 accidents, Al Rayyan - Fereej Al Soudan, Al Waab: 14,848 accidents, Umm Slal - Al Froosh, Al Khartiyat: 10,148 accidents, Doha - Industrial Area: 9,833 accidents, Al Wakra: 8,070 accidents",
            "2020-2023: Consistent high accidents in Al Rayyan - Bu Hamour, Ain Khaled; Al Rayyan - Fereej Al Soudan, Al Waab; Doha - Industrial Area; Al Rayyan - New Al Rayyan, Muaither; Umm Slal - Al Froosh, Al Khartiyat",
            "Key Areas: High accidents in major urban and industrial zones, dense population areas, and Al Rayyan district."
        ]
    }
    return pd.DataFrame(data)

def process_query_with_rag(query):
    try:
        social_updates_df = load_knowledge_base()
        relevant_updates = social_updates_df[
            social_updates_df['message'].str.contains('|'.join(query.split()), case=False, na=False)
        ]
        
        context = "\n".join(relevant_updates['message'].tolist())
        
        messages = [
            {"role": "system", "content": """You are TraffiQ, an AI traffic expert and statistician for Qatar. 
             Your role is to:
             1. Analyze traffic patterns and accident data
             2. Provide policy recommendations based on data
             3. Promote road safety and best practices
             4. Guide policymakers with data-driven insights
             
             Provide clear, accurate information based on available data."""},
            {"role": "user", "content": f"Context from traffic database:\n{context}\n\nUser Question: {query}"}
        ]
        
        try:
            response = groq_client.chat.completions.create(
                messages=messages,
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=6000,
                top_p=0.9
            )
            return response.choices[0].message.content
        except Exception as e:
            return "I apologize, but I'm having trouble connecting to the AI service. Please try again in a moment."
            
    except Exception as e:
        return "I apologize, but I encountered an error processing your query. Please try again."

def main():
    # Header
    st.markdown('<h1 class="logo">TraffiQ</h1>', unsafe_allow_html=True)
    
    # Feature Grid
    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    
    features = [
        {
            "icon": "🚑",
            "title": "Accident Analytics",
            "description": "Real-time accident data analysis with interactive visualizations and predictive insights for better emergency response.",
            "url": "https://accidents.streamlit.app/"
        },
        {
            "icon": "🚔",
            "title": "Traffic Analytics",
            "description": "Comprehensive tracking and analysis of traffic violations to improve enforcement and reduce infractions.",
            "url": "https://violations.streamlit.app/"
        },
        {
            "icon": "📇",
            "title": "License Analytics",
            "description": "Streamlined license processing system with verification tools and renewal tracking capabilities.",
            "url": "https://license.streamlit.app/"
        },
        {
            "icon": "🚗",
            "title": "Data to Campaign (Under Progress)",
            "description": "Data to Outreach in a click. Enable authorities to generates campaign ready graphics and social media content using their brand assets directly from their data.",
            "url": ""
        }
    ]
    
    # Create feature cards using columns
    cols = st.columns(2)
    for idx, feature in enumerate(features):
        with cols[idx % 2]:
            st.markdown(f'''
                <div class="feature-card">
                    <div class="feature-icon">{feature["icon"]}</div>
                    <div class="feature-title">{feature["title"]}</div>
                    <div class="feature-description">{feature["description"]}</div>
                    <a href="{feature["url"]}" target="_blank" class="view-link">View Dashboard</a>
                </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    
    # Display chat history
    for message in st.session_state.chat_history:
        message_class = "user-message" if message["role"] == "user" else "bot-message"
        icon = "👤" if message["role"] == "user" else "🤖"
        st.markdown(
            f'<div class="message {message_class}">{icon} {message["content"]}</div>',
            unsafe_allow_html=True
        )
    
    # Chat input
    user_input = st.chat_input(
        "Ask about Qatar traffic data, safety measures, or policy recommendations...",
        key="chat_input"
    )
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner("Processing your query..."):
            response = process_query_with_rag(user_input)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()