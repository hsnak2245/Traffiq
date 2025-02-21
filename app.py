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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cyberpunk CSS
st.markdown("""
<style>
:root {
    --neon-blue: #00f3ff;
    --neon-violet: #8a2be2;
    --alert-red: #ff0747;
    --dark-bg: #000000;
}

* {
    font-family: 'Space Mono', monospace;
}

.main {
    background-color: var(--dark-bg);
    color: white;
}

/* Gradient Title */
.page-title {
    background: linear-gradient(45deg, var(--neon-blue), var(--neon-violet));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-size: 4rem;
    text-align: center;
    text-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
    margin: 2rem 0;
    letter-spacing: -0.05em;
}

.subtitle {
    color: rgba(255, 255, 255, 0.7);
    text-align: center;
    font-size: 1.2rem;
    margin-bottom: 3rem;
    border-bottom: 1px solid var(--neon-blue);
    padding-bottom: 1rem;
    width: fit-content;
    margin-left: auto;
    margin-right: auto;
}

/* Holographic Button Grid */
.stButton > button {
    background: rgba(0, 0, 0, 0.7) !important;
    border: 1px solid var(--neon-blue) !important;
    border-radius: 8px !important;
    color: var(--neon-blue) !important;
    padding: 1.5rem !important;
    margin: 0.5rem;
    backdrop-filter: blur(12px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.2);
}

.stButton > button:hover {
    background: rgba(0, 243, 255, 0.1) !important;
    transform: translateY(-3px);
    box-shadow: 0 0 25px var(--neon-blue);
}

.button-icon {
    font-size: 2.5rem;
    filter: drop-shadow(0 0 5px var(--neon-blue));
}

/* Cyber Chat Interface */
.chat-container {
    background: linear-gradient(145deg, rgba(0, 243, 255, 0.05), rgba(138, 43, 226, 0.05));
    border: 1px solid var(--neon-blue);
    border-radius: 12px;
    padding: 2rem;
    margin: 2rem 0;
    box-shadow: 0 0 30px rgba(0, 243, 255, 0.1);
}

.chat-title {
    color: var(--neon-blue);
    font-size: 1.8rem;
    margin-bottom: 1.5rem;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.user-message {
    background: rgba(0, 243, 255, 0.08);
    border-left: 4px solid var(--neon-blue);
    color: rgba(255, 255, 255, 0.9);
    padding: 1.2rem;
    margin: 1rem 0;
    border-radius: 6px;
    animation: slideIn 0.3s ease;
}

.bot-message {
    background: rgba(138, 43, 226, 0.08);
    border-left: 4px solid var(--neon-violet);
    color: rgba(255, 255, 255, 0.9);
    padding: 1.2rem;
    margin: 1rem 0;
    border-radius: 6px;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { transform: translateX(20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* Cyber Input */
.stTextInput>div>div>input {
    background: rgba(0, 0, 0, 0.7) !important;
    color: var(--neon-blue) !important;
    border: 1px solid var(--neon-blue) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    font-size: 1.1rem !important;
}

.stTextInput>div>div>input:focus {
    box-shadow: 0 0 15px var(--neon-blue) !important;
}

/* Alert Highlights */
.red-alert {
    color: var(--alert-red);
    text-shadow: 0 0 10px rgba(255, 7, 71, 0.3);
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

/* Hide Streamlit elements */
#MainMenu, footer, .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
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
                max_tokens=500,
                top_p=0.9
            )
            return response.choices[0].message.content
        except Exception as e:
            return "I apologize, but I'm having trouble connecting to the AI service. Please try again in a moment."
            
    except Exception as e:
        return "I apologize, but I encountered an error processing your query. Please try again."

def home_page():
    st.markdown('<h1 class="page-title">TRAFFIQ</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">NEURAL TRAFFIC MANAGEMENT SYSTEM</p>', unsafe_allow_html=True)

    main_container = st.container()
    with main_container:
        col1, col2 = st.columns(2)
        
        buttons = [
            ("🚑", "ACCIDENT ANALYSIS", "#ff0747"),
            ("🚔", "VIOLATION RECORDS", "#00f3ff"),
            ("📇", "LICENSE VERIFICATION", "#8a2be2"),
            ("🚗", "VEHICLE REGISTRY", "#00f3ff")
        ]
        
        for i, (icon, text, color) in enumerate(buttons):
            with col1 if i < 2 else col2:
                st.markdown(f"""
                    <style>
                        .btn-{i} {{
                            --hover-color: {color}26;
                            --border-color: {color};
                        }}
                        .btn-{i}:hover {{
                            box-shadow: 0 0 25px {color} !important;
                        }}
                    </style>
                """, unsafe_allow_html=True)
                
                if st.button(
                    f'<div class="button-icon">{icon}</div><div>{text}</div>',
                    key=f"btn_{i}",
                    use_container_width=True
                ):
                    st.markdown(f'<script>window.open("{link}", "_blank");</script>', unsafe_allow_html=True)

        # Chat Interface
        with st.container():
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            st.markdown('<div class="chat-title">📡 LIVE QUERY INTERFACE</div>', unsafe_allow_html=True)
            
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f'<div class="user-message">📡 USER: {message["content"]}</div>', unsafe_allow_html=True)
                else:
                    content = message["content"].replace("urgent", '<span class="red-alert">URGENT</span>')
                    st.markdown(f'<div class="bot-message">🤖 TRAFFIQ: {content}</div>', unsafe_allow_html=True)

            user_input = st.chat_input("SYSTEM QUERY: Ask about traffic patterns, safety protocols, or policy updates...")
            
            if user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                with st.spinner("🌀 PROCESSING QUERY..."):
                    response = process_query_with_rag(user_input)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                st.rerun()

def main():
    if st.session_state.page == 'home':
        home_page()

if __name__ == "__main__":
    main()