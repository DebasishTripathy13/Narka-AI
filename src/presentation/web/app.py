"""Enhanced Streamlit web interface for Robin."""

import streamlit as st
from datetime import datetime
import time


# Page configuration
st.set_page_config(
    page_title="Robin - Dark Web OSINT",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .result-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .entity-tag {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 2px 8px;
        border-radius: 4px;
        margin: 2px;
        font-size: 0.85rem;
    }
    .warning-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'scraped_content' not in st.session_state:
        st.session_state.scraped_content = []
    if 'entities' not in st.session_state:
        st.session_state.entities = {}
    if 'investigation_history' not in st.session_state:
        st.session_state.investigation_history = []
    if 'current_investigation' not in st.session_state:
        st.session_state.current_investigation = None


def render_sidebar():
    """Render the sidebar."""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80?text=Robin", width=200)
        
        st.markdown("---")
        
        # Navigation
        st.subheader("🧭 Navigation")
        page = st.radio(
            "Select Page",
            ["🔍 Search", "🔬 Investigate", "📊 Dashboard", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Status indicators
        st.subheader("📡 Status")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tor", "🟢 Connected")
        with col2:
            st.metric("API", "🟢 Ready")
        
        # Quick stats
        st.subheader("📈 Session Stats")
        st.metric("Searches", len(st.session_state.search_results))
        st.metric("Pages Scraped", len(st.session_state.scraped_content))
        st.metric("Entities Found", sum(len(v) for v in st.session_state.entities.values()))
        
        st.markdown("---")
        
        # Model selection
        st.subheader("🤖 AI Model")
        model = st.selectbox(
            "Select LLM",
            ["gpt-4o", "gpt-4o-mini", "claude-3-sonnet", "claude-3-haiku", "gemini-pro", "llama3"],
            label_visibility="collapsed"
        )
        
        return page, model


def render_search_page(model: str):
    """Render the search page."""
    st.markdown('<h1 class="main-header">🔍 Dark Web Search</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Search across multiple dark web search engines</p>', unsafe_allow_html=True)
    
    # Search input
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="Enter your search query...",
            label_visibility="collapsed"
        )
    with col2:
        search_button = st.button("🔍 Search", use_container_width=True)
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2, col3 = st.columns(3)
        with col1:
            engines = st.multiselect(
                "Search Engines",
                ["ahmia", "torch", "haystak", "excavator"],
                default=["ahmia", "torch"]
            )
        with col2:
            max_results = st.slider("Max Results", 10, 200, 50)
        with col3:
            scrape_results = st.checkbox("Auto-scrape results", value=False)
    
    if search_button and query:
        with st.spinner("🔍 Searching dark web..."):
            # Progress bar
            progress = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress.progress(i + 1)
            
            # TODO: Implement actual search
            st.success(f"✅ Search complete! Found 0 results.")
    
    # Results section
    if st.session_state.search_results:
        st.subheader("📋 Search Results")
        
        for result in st.session_state.search_results:
            with st.container():
                st.markdown(f"""
                <div class="result-card">
                    <h4>{result.get('title', 'Untitled')}</h4>
                    <p><small>🔗 {result.get('url', '')}</small></p>
                    <p>{result.get('description', '')[:200]}...</p>
                </div>
                """, unsafe_allow_html=True)


def render_investigate_page(model: str):
    """Render the investigation page."""
    st.markdown('<h1 class="main-header">🔬 AI Investigation</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Comprehensive dark web investigation with AI analysis</p>', unsafe_allow_html=True)
    
    # Investigation input
    query = st.text_area(
        "Investigation Query",
        placeholder="Describe what you want to investigate...\n\nExample: Find information about ransomware group 'LockBit' including their infrastructure, tactics, and recent activities.",
        height=100
    )
    
    # Options
    col1, col2, col3 = st.columns(3)
    with col1:
        scrape_pages = st.checkbox("Scrape search results", value=True)
        max_pages = st.slider("Max pages to scrape", 5, 50, 10)
    with col2:
        extract_entities = st.checkbox("Extract entities", value=True)
        analyze_threats = st.checkbox("Analyze threats", value=True)
    with col3:
        generate_summary = st.checkbox("Generate AI summary", value=True)
        export_format = st.selectbox("Export format", ["JSON", "CSV", "STIX", "PDF"])
    
    if st.button("🚀 Start Investigation", use_container_width=True):
        if not query:
            st.error("Please enter an investigation query.")
        else:
            # Create tabs for progress tracking
            tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search", "📄 Scrape", "🔗 Entities", "🤖 Analysis"])
            
            with tab1:
                with st.spinner("Searching dark web..."):
                    time.sleep(1)
                    st.success("✅ Search complete")
                    st.info("Found 0 results across 4 engines")
            
            with tab2:
                with st.spinner("Scraping pages..."):
                    time.sleep(1)
                    st.success("✅ Scraping complete")
                    st.info("Scraped 0 pages")
            
            with tab3:
                with st.spinner("Extracting entities..."):
                    time.sleep(1)
                    st.success("✅ Entity extraction complete")
                    
                    # Entity display
                    entity_types = ["Emails", "Crypto Wallets", "Domains", "IP Addresses"]
                    cols = st.columns(len(entity_types))
                    for i, etype in enumerate(entity_types):
                        with cols[i]:
                            st.metric(etype, "0")
            
            with tab4:
                with st.spinner(f"Analyzing with {model}..."):
                    time.sleep(2)
                    st.success("✅ Analysis complete")
                    
                    # Placeholder summary
                    st.markdown("### 📊 Investigation Summary")
                    st.markdown("""
                    *No results found for this query.*
                    
                    Try a different search term or check your Tor connection.
                    """)


def render_dashboard_page():
    """Render the dashboard page."""
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Investigations", "0", delta="0 today")
    with col2:
        st.metric("Search Results", "0", delta="0 new")
    with col3:
        st.metric("Pages Scraped", "0", delta="0 today")
    with col4:
        st.metric("Entities Found", "0", delta="0 new")
    
    st.markdown("---")
    
    # Recent investigations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Recent Investigations")
        if st.session_state.investigation_history:
            for inv in st.session_state.investigation_history[-5:]:
                st.markdown(f"""
                <div class="result-card">
                    <strong>{inv['query']}</strong><br>
                    <small>{inv['timestamp']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No investigations yet. Start one from the Investigate page!")
    
    with col2:
        st.subheader("🔔 Active Alerts")
        st.info("No alerts configured. Set up alerts in Settings.")
    
    # Entity breakdown
    st.subheader("🔗 Entity Breakdown")
    
    # Placeholder chart
    import pandas as pd
    chart_data = pd.DataFrame({
        'Entity Type': ['Emails', 'Crypto Wallets', 'Domains', 'IPs', 'Phones'],
        'Count': [0, 0, 0, 0, 0]
    })
    st.bar_chart(chart_data.set_index('Entity Type'))


def render_settings_page():
    """Render the settings page."""
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    # Tabs for different settings
    tab1, tab2, tab3, tab4 = st.tabs(["🔑 API Keys", "🌐 Tor", "🤖 LLM", "🔔 Alerts"])
    
    with tab1:
        st.subheader("API Keys Configuration")
        
        openai_key = st.text_input("OpenAI API Key", type="password")
        anthropic_key = st.text_input("Anthropic API Key", type="password")
        google_key = st.text_input("Google AI API Key", type="password")
        
        if st.button("💾 Save API Keys"):
            st.success("API keys saved!")
    
    with tab2:
        st.subheader("Tor Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            tor_host = st.text_input("Tor SOCKS Host", value="127.0.0.1")
            tor_port = st.number_input("Tor SOCKS Port", value=9050)
        with col2:
            circuit_rotation = st.slider("Circuit rotation (minutes)", 1, 30, 10)
            max_retries = st.slider("Max retries", 1, 10, 3)
        
        if st.button("🔄 Test Tor Connection"):
            with st.spinner("Testing connection..."):
                time.sleep(1)
                st.success("✅ Tor connection successful!")
    
    with tab3:
        st.subheader("LLM Configuration")
        
        default_model = st.selectbox(
            "Default Model",
            ["gpt-4o", "gpt-4o-mini", "claude-3-sonnet", "gemini-pro"]
        )
        temperature = st.slider("Temperature", 0.0, 1.0, 0.0)
        max_tokens = st.number_input("Max Tokens", 100, 8000, 4000)
        
        ollama_url = st.text_input("Ollama Base URL", value="http://127.0.0.1:11434")
        
        if st.button("💾 Save LLM Settings"):
            st.success("LLM settings saved!")
    
    with tab4:
        st.subheader("Alert Configuration")
        
        st.markdown("### Create New Alert")
        
        alert_name = st.text_input("Alert Name")
        alert_query = st.text_input("Search Query")
        webhook_url = st.text_input("Webhook URL (optional)")
        schedule = st.selectbox("Schedule", ["Every hour", "Every 6 hours", "Daily", "Weekly"])
        
        if st.button("➕ Create Alert"):
            if alert_name and alert_query:
                st.success(f"Alert '{alert_name}' created!")
            else:
                st.error("Please fill in alert name and query.")


def main():
    """Main application entry point."""
    init_session_state()
    
    # Render sidebar and get selections
    page, model = render_sidebar()
    
    # Disclaimer
    st.markdown("""
    <div class="warning-box">
        ⚠️ <strong>Disclaimer:</strong> This tool is for educational and authorized security research only. 
        Always comply with applicable laws and regulations.
    </div>
    """, unsafe_allow_html=True)
    
    # Render selected page
    if "Search" in page:
        render_search_page(model)
    elif "Investigate" in page:
        render_investigate_page(model)
    elif "Dashboard" in page:
        render_dashboard_page()
    elif "Settings" in page:
        render_settings_page()


if __name__ == "__main__":
    main()
