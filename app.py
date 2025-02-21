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

# Load CSS
st.markdown("""
<style>
/* Main container */
.main {
    background-color: #1a1f2e;
    color: white;
}

/* Title styling */
.page-title {
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    color: white;
    text-align: center;
    margin: 2rem 0;
    font-size: 3.5rem;
    font-weight: 700;
}

.subtitle {
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #a0aec0;
    text-align: center;
    margin-bottom: 3rem;
    font-size: 1.5rem;
}

/* Button grid styling */
.stButton > button {
    width: 100%;
    background-color: rgba(255, 255, 255, 0.1) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    font-size: 1.2rem !important;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background-color: rgba(255, 255, 255, 0.15) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
    transform: translateY(-2px);
}

.button-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    display: block;
}

/* Chat container styling */
.chat-container {
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 2rem;
    margin-top: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.chat-title {
    color: white;
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    font-weight: 600;
}

.user-message {
    background-color: rgba(59, 130, 246, 0.1);
    color: white;
    padding: 1rem;
    border-radius: 12px;
    margin: 0.5rem 0;
    border: 1px solid rgba(59, 130, 246, 0.2);
}

.bot-message {
    background-color: rgba(255, 255, 255, 0.05);
    color: white;
    padding: 1rem;
    border-radius: 12px;
    margin: 0.5rem 0;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Chat input styling */
.stTextInput > div > div > input {
    background-color: rgba(255, 255, 255, 0.05) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: rgba(59, 130, 246, 0.5) !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
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
    st.markdown('<h1 class="page-title">TraffiQ</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Traffic Intelligence for Qatar</p>', unsafe_allow_html=True)

    # Create a container for better spacing
    main_container = st.container()
    
    with main_container:
        # 2x2 Button Grid with improved layout
        col1, col2 = st.columns(2)
        
        buttons = [
            ("🚑 Accidents", "accidents", "https://accidents.streamlit.app/"),
            ("🚔 Violations", "violations", "https://violations.streamlit.app/"),
            ("📇 License", "license", "https://license.streamlit.app/"),
            ("🚗 Vehicle", "vehicle", "https://vehicle.streamlit.app/")
        ]
        
        for i, (label, page, link) in enumerate(buttons):
            with col1 if i % 2 == 0 else col2:
                if st.button(label, key=f"btn_{page}"):
                    st.markdown(f'<script>window.open("{link}", "_blank");</script>', unsafe_allow_html=True)

        # Chat Interface
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        st.markdown('<div class="chat-title">🤖 Traffic Safety Assistant</div>', unsafe_allow_html=True)
        
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)

        # Chat input
        user_input = st.chat_input("Ask about Qatar traffic data, safety measures, or policy recommendations...")
        
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.spinner("Analyzing your query..."):
                response = process_query_with_rag(user_input)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            st.rerun()

def main():
    if st.session_state.page == 'home':
        home_page()

if __name__ == "__main__":
    main()