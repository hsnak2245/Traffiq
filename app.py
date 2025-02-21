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
    background: #0f172a;
    color: #f8fafc;
}

.stApp {
    background: #0f172a;
}

/* Header styling */
.header {
    background: linear-gradient(to right, #1e293b, #0f172a);
    padding: 2rem 0;
    margin-bottom: 2rem;
    border-bottom: 1px solid #334155;
}

.logo {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(45deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 1rem;
}

/* Navigation */
.nav-container {
    display: flex;
    justify-content: center;
    gap: 1rem;
    padding: 1rem;
    flex-wrap: wrap;
}

.nav-button {
    background: rgba(51, 65, 85, 0.5);
    border: 1px solid #475569;
    color: #e2e8f0;
    padding: 0.75rem 1.5rem;
    border-radius: 0.75rem;
    font-weight: 500;
    transition: all 0.2s;
    backdrop-filter: blur(8px);
}

.nav-button:hover {
    background: rgba(51, 65, 85, 0.8);
    border-color: #60a5fa;
    transform: translateY(-2px);
}

/* Chat interface */
.chat-container {
    max-width: 800px;
    margin: 2rem auto;
    padding: 2rem;
    background: rgba(30, 41, 59, 0.5);
    border-radius: 1rem;
    border: 1px solid #334155;
    backdrop-filter: blur(12px);
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
    padding: 1rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2) !important;
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
    st.markdown('<div class="header">', unsafe_allow_html=True)
    st.markdown('<h1 class="logo">TraffiQ</h1>', unsafe_allow_html=True)
    
    # Navigation
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    nav_buttons = [
        ("🚑 Accidents", "https://accidents.streamlit.app/"),
        ("🚔 Violations", "https://violations.streamlit.app/"),
        ("📇 License", "https://license.streamlit.app/"),
        ("🚗 Vehicle", "https://vehicle.streamlit.app/")
    ]
    
    for label, link in nav_buttons:
        if st.button(label, key=f"nav_{link}", help=f"Navigate to {label}"):
            st.markdown(f'<script>window.open("{link}", "_blank");</script>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat Interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
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