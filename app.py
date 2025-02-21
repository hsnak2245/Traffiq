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

# Load CSS with updated styling
# Update the CSS section with this improved styling
st.markdown("""
<style>
/* Main container */
.main {
    background: #0a0a2a;
    color: #ffffff;
}

/* Title styling */
.page-title {
    font-family: 'Space Grotesk', sans-serif;
    color: #00f3ff;
    text-align: center;
    margin: 1rem 0 2rem 0;
    font-size: 3rem;
    font-weight: 700;
    text-shadow: 0 0 15px #00f3ff;
}

/* Button grid styling */
.button-container {
    max-width: 800px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    padding: 0 1rem;
}

.stButton > button {
    width: 100%;
    background: linear-gradient(45deg, #00f3ff 0%, #ff00ff 50%, #d400ff 100%) !important;
    color: white !important;
    border: 2px solid rgba(0, 243, 255, 0.3) !important;
    border-radius: 12px !important;
    padding: 0.8rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.2);
    height: 80px !important;
    backdrop-filter: blur(5px);
}

.stButton > button:hover {
    box-shadow: 0 0 25px rgba(212, 0, 255, 0.4);
    transform: scale(1.05);
    background: linear-gradient(45deg, #d400ff 0%, #ff00ff 50%, #00f3ff 100%) !important;
}

/* Simplified Chat Container */
.chat-container {
    margin: 2rem auto;
    max-width: 800px;
    padding: 0 1rem;
}

.user-message {
    background: rgba(0, 243, 255, 0.1);
    color: white;
    padding: 1rem;
    border-radius: 12px;
    margin: 1rem 0;
    border: 1px solid #00f3ff;
    box-shadow: 0 0 10px rgba(0, 243, 255, 0.2);
}

.bot-message {
    background: rgba(212, 0, 255, 0.1);
    color: white;
    padding: 1rem;
    border-radius: 12px;
    margin: 1rem 0;
    border: 1px solid #d400ff;
    box-shadow: 0 0 10px rgba(212, 0, 255, 0.2);
}

/* Chat input styling */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.05) !important;
    color: white !important;
    border: 2px solid #d400ff !important;
    border-radius: 12px !important;
    padding: 0.8rem !important;
    font-size: 1rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #00f3ff !important;
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.3) !important;
}

/* Neon glow animations */
@keyframes button-glow {
    0% { box-shadow: 0 0 15px rgba(0, 243, 255, 0.3); }
    50% { box-shadow: 0 0 25px rgba(212, 0, 255, 0.4); }
    100% { box-shadow: 0 0 15px rgba(0, 243, 255, 0.3); }
}

.stButton > button {
    animation: button-glow 3s infinite;
}
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

@st.cache_data
def load_knowledge_base():
    data = pd.read_csv('info.md')
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

# Modified home_page function
def home_page():
    st.markdown('<h1 class="page-title">TraffiQ</h1>', unsafe_allow_html=True)

    # Button Grid
    with st.container():
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        
        buttons = [
            ("🚑 Accidents", "accidents", "https://accidents.streamlit.app/"),
            ("🚔 Violations", "violations", "https://violations.streamlit.app/"),
            ("📇 License", "license", "https://license.streamlit.app/"),
            ("🚗 Vehicle", "vehicle", "https://vehicle.streamlit.app/")
        ]
        
        for label, page, link in buttons:
            if st.button(label, key=f"btn_{page}"):
                st.markdown(f'<script>window.open("{link}", "_blank");</script>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Simplified Chat Interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input("Ask about Qatar traffic data...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner("Analyzing..."):
            response = process_query_with_rag(user_input)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    if st.session_state.page == 'home':
        home_page()

if __name__ == "__main__":
    main()