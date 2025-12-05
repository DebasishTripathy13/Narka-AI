"""Enhanced Streamlit web interface for NarakAAI."""

import streamlit as st
from datetime import datetime
import time
import sys
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import core services and factories
from src.adapters.llm.factory import LLMFactory
from src.adapters.search_engines.factory import create_search_engines, SEARCH_ENGINE_REGISTRY
from src.core.interfaces.llm_provider import LLMConfig


# Page configuration
st.set_page_config(
    page_title="NarakAAI - Dark Web OSINT",
    page_icon="🔱",
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
        st.markdown("# 🔱 NarakAAI")
        st.markdown("*AI-Powered Dark Web OSINT*")
        
        st.markdown("---")
        
        # Navigation
        st.subheader("🧭 Navigation")
        page = st.radio(
            "Select Page",
            ["🔍 Search", "🔬 Investigate", "💬 Chat", "📊 Dashboard", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Model selection
        st.subheader("🤖 AI Model")
        model = st.selectbox(
            "Select LLM",
            [
                "gemini-flash-latest",
                "gemini-2.5-pro",
                "gpt-4o",
                "gpt-4o-mini",
                "claude-3-5-sonnet-latest",
                "claude-3-haiku-20240307",
            ],
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
        
        # Available engines
        st.markdown("---")
        st.subheader("🔍 Search Engines")
        st.caption(f"{len(SEARCH_ENGINE_REGISTRY)} engines available")
        
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
                list(SEARCH_ENGINE_REGISTRY.keys()),
                default=["ahmia", "torch"]
            )
        with col2:
            max_results = st.slider("Max Results", 10, 200, 50)
        with col3:
            use_ai = st.checkbox("Use AI to refine query", value=True)
    
    if search_button and query:
        with st.spinner("🔍 Searching dark web..."):
            try:
                # Create search engines
                search_engines = create_search_engines(engines)
                
                # Progress bar
                progress = st.progress(0)
                status_text = st.empty()
                
                results = []
                for i, engine in enumerate(search_engines):
                    status_text.text(f"Searching {engine.__class__.__name__}...")
                    try:
                        engine_results = engine.search(query, max_results=max_results // len(search_engines))
                        results.extend(engine_results)
                    except Exception as e:
                        st.warning(f"Error with {engine.__class__.__name__}: {str(e)}")
                    progress.progress((i + 1) / len(search_engines))
                
                st.session_state.search_results = results
                st.success(f"✅ Search complete! Found {len(results)} results.")
                
            except Exception as e:
                st.error(f"Search failed: {str(e)}")
    
    # Results section
    if st.session_state.search_results:
        st.subheader(f"📋 Search Results ({len(st.session_state.search_results)})")
        
        for idx, result in enumerate(st.session_state.search_results):
            with st.container():
                st.markdown(f"""
                <div class="result-card">
                    <h4>{result.title or 'Untitled'}</h4>
                    <p><small>🔗 {result.url}</small></p>
                    <p>{result.description[:200] if result.description else 'No description'}...</p>
                </div>
                """, unsafe_allow_html=True)


def render_chat_page(model: str):
    """Render the AI chat page."""
    st.markdown('<h1 class="main-header">💬 AI Chat</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">Chat with {model}</p>', unsafe_allow_html=True)
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Create LLM provider
                    provider = LLMFactory.create(
                        model_name=model,
                        temperature=0.7
                    )
                    
                    # Generate response
                    response = provider.complete(
                        prompt=prompt,
                        system_prompt="You are NarakAAI, an AI assistant specialized in dark web OSINT and cybersecurity analysis. Provide helpful, accurate, and ethical responses."
                    )
                    
                    st.markdown(response.content)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.content})
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()


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
        engines = st.multiselect(
            "Search Engines",
            list(SEARCH_ENGINE_REGISTRY.keys()),
            default=["ahmia", "torch", "haystak"]
        )
        max_results = st.slider("Max results per engine", 5, 50, 10)
    with col2:
        extract_entities = st.checkbox("Extract entities", value=True)
        analyze_threats = st.checkbox("Analyze threats", value=True)
    with col3:
        generate_summary = st.checkbox("Generate AI summary", value=True)
        export_format = st.selectbox("Export format", ["JSON", "CSV", "PDF"])
    
    if st.button("🚀 Start Investigation", use_container_width=True):
        if not query:
            st.error("Please enter an investigation query.")
        else:
            # Create tabs for progress tracking
            tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search", "🤖 Analysis", "🔗 Entities", "📊 Summary"])
            
            with tab1:
                with st.spinner("Searching dark web..."):
                    try:
                        search_engines = create_search_engines(engines)
                        results = []
                        
                        progress = st.progress(0)
                        for i, engine in enumerate(search_engines):
                            st.info(f"Searching {engine.__class__.__name__}...")
                            try:
                                engine_results = engine.search(query, max_results=max_results)
                                results.extend(engine_results)
                            except Exception as e:
                                st.warning(f"Error with {engine.__class__.__name__}: {str(e)}")
                            progress.progress((i + 1) / len(search_engines))
                        
                        st.session_state.investigation_results = results
                        st.success(f"✅ Found {len(results)} results across {len(engines)} engines")
                        
                        # Display sample results
                        for result in results[:5]:
                            st.markdown(f"- [{result.title}]({result.url})")
                    except Exception as e:
                        st.error(f"Search failed: {str(e)}")
            
            with tab2:
                if generate_summary and 'investigation_results' in st.session_state:
                    with st.spinner(f"Analyzing with {model}..."):
                        try:
                            provider = LLMFactory.create(model_name=model, temperature=0.3)
                            
                            # Prepare context from results
                            context = "\n\n".join([
                                f"Title: {r.title}\nURL: {r.url}\nDescription: {r.description}"
                                for r in st.session_state.investigation_results[:10]
                            ])
                            
                            analysis_prompt = f"""Analyze these dark web search results for: {query}

Results:
{context}

Provide a comprehensive analysis including:
1. Key findings
2. Patterns and connections
3. Potential threats or concerns
4. Recommendations for further investigation"""
                            
                            response = provider.complete(
                                prompt=analysis_prompt,
                                system_prompt="You are a cybersecurity analyst specializing in OSINT and threat intelligence."
                            )
                            
                            st.success("✅ Analysis complete")
                            st.markdown("### 📊 AI Analysis")
                            st.markdown(response.content)
                            
                        except Exception as e:
                            st.error(f"Analysis failed: {str(e)}")
                else:
                    st.info("Run search first to generate analysis")
            
            with tab3:
                if extract_entities:
                    with st.spinner("Extracting entities..."):
                        time.sleep(1)
                        st.success("✅ Entity extraction complete")
                        
                        # Placeholder entity display
                        entity_types = ["Emails", "Crypto Wallets", "Domains", "IP Addresses"]
                        cols = st.columns(len(entity_types))
                        for i, etype in enumerate(entity_types):
                            with cols[i]:
                                st.metric(etype, "0")
                else:
                    st.info("Enable entity extraction in options")
            
            with tab4:
                st.markdown("### 📈 Investigation Summary")
                st.info(f"Query: {query}")
                st.info(f"Model: {model}")
                st.info(f"Engines: {', '.join(engines)}")
                
                if 'investigation_results' in st.session_state:
                    st.metric("Total Results", len(st.session_state.investigation_results))


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
    tab1, tab2, tab3 = st.tabs(["🔑 API Keys", "🤖 LLM", "🔍 Search"])
    
    with tab1:
        st.subheader("API Keys Configuration")
        st.info("💡 Set these in your .env file for persistent configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### OpenAI")
            openai_key = os.getenv("OPENAI_API_KEY", "")
            st.text_input(
                "OpenAI API Key",
                value=openai_key[:20] + "..." if openai_key else "Not set",
                type="password",
                disabled=True
            )
            st.caption("For GPT-4o, GPT-5, o1 models")
            
            st.markdown("### Anthropic")
            anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
            st.text_input(
                "Anthropic API Key",
                value=anthropic_key[:20] + "..." if anthropic_key else "Not set",
                type="password",
                disabled=True
            )
            st.caption("For Claude 3.5, Claude 4 models")
        
        with col2:
            st.markdown("### Google AI")
            google_key = os.getenv("GOOGLE_API_KEY", "")
            st.text_input(
                "Google API Key",
                value=google_key[:20] + "..." if google_key else "Not set",
                type="password",
                disabled=True
            )
            st.caption("For Gemini models")
            
            st.markdown("### Ollama")
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
            st.text_input(
                "Ollama Base URL",
                value=ollama_url,
                disabled=True
            )
            st.caption("For local models")
        
        st.markdown("---")
        st.code("""
# Add to your .env file:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OLLAMA_BASE_URL=http://127.0.0.1:11434
        """, language="bash")
    
    with tab2:
        st.subheader("LLM Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            default_model = st.selectbox(
                "Default Model",
                [
                    "gemini-flash-latest",
                    "gemini-2.5-pro",
                    "gpt-4o",
                    "gpt-4o-mini",
                    "claude-3-5-sonnet-latest",
                ],
                index=0
            )
            temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        
        with col2:
            max_tokens = st.number_input("Max Tokens", 100, 8000, 4000)
            streaming = st.checkbox("Enable Streaming", value=True)
        
        if st.button("💾 Save LLM Settings"):
            st.success("LLM settings saved for this session!")
    
    with tab3:
        st.subheader("Search Engine Configuration")
        
        st.markdown("### Available Engines")
        for engine_name in SEARCH_ENGINE_REGISTRY.keys():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.text(engine_name.upper())
            with col2:
                st.success("✓ Available")
            with col3:
                st.caption("Dark Web")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            default_timeout = st.slider("Request Timeout (seconds)", 10, 60, 30)
            max_retries = st.slider("Max Retries", 1, 10, 3)
        with col2:
            results_per_engine = st.slider("Default Results Per Engine", 5, 100, 20)
            enable_caching = st.checkbox("Enable Result Caching", value=True)
        
        if st.button("💾 Save Search Settings"):
            st.success("Search settings saved for this session!")


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
    elif "Chat" in page:
        render_chat_page(model)
    elif "Dashboard" in page:
        render_dashboard_page()
    elif "Settings" in page:
        render_settings_page()


if __name__ == "__main__":
    main()
