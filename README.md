<div align="center">
   <img src=".github/assets/logo.png" alt="NarakAAI Logo" width="300">
   
   <h1>🦅 Naraka AI</h1>
   <h3>Advanced AI-Powered Dark Web Intelligence Platform</h3>

   <p>
      <strong>NarakAAI</strong> is a next-generation OSINT platform for dark web investigations. 
      Powered by multiple LLM providers, automated entity extraction, threat intelligence analysis, 
      and a modular plugin architecture.
   </p>

   <p>
      <a href="#-features">Features</a> •
      <a href="#-installation">Installation</a> •
      <a href="#-quick-start">Quick Start</a> •
      <a href="#-architecture">Architecture</a> •
      <a href="#-api-reference">API</a> •
      <a href="#-plugins">Plugins</a> •
      <a href="#-contributing">Contributing</a>
   </p>

   <p>
      <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
      <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
      <img src="https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg" alt="Platform">
      <img src="https://img.shields.io/badge/docker-ready-blue.svg" alt="Docker">
   </p>
</div>

---

## 🌟 What's New in v2.0

Naraka AI v2.0 is a complete rewrite with enterprise-grade features:

- 🏗️ **Clean Architecture** - Modular design with domain-driven structure
- 🔌 **Plugin System** - Extend functionality with custom plugins
- 🌐 **REST API** - Full-featured FastAPI backend for integrations
- 📊 **Threat Intelligence** - Automated IOC extraction and threat scoring
- 🔄 **Multiple LLM Providers** - OpenAI, Anthropic, Google, Ollama support
- 💾 **Advanced Caching** - Memory and SQLite-based caching with TTL
- 📤 **Export Formats** - JSON, CSV, STIX 2.1, PDF reports
- 🛡️ **Tor Circuit Rotation** - Enhanced anonymity with automatic circuit rotation
- 📈 **Investigation Dashboard** - Track and manage multiple investigations

---

## ✨ Features

### 🔍 **Intelligence Gathering**
| Feature | Description |
|---------|-------------|
| Multi-Engine Search | Query Ahmia, Torch, Haystak, Excavator simultaneously |
| Smart Query Refinement | LLM-powered query optimization for better results |
| Intelligent Filtering | AI-driven result relevance scoring |
| Deep Content Scraping | Extract and analyze .onion page content |

### 🧠 **AI-Powered Analysis**
| Feature | Description |
|---------|-------------|
| Entity Extraction | Auto-detect emails, crypto wallets, IPs, domains, credentials |
| Threat Scoring | Automated threat level assessment (1-10 scale) |
| Pattern Recognition | Identify trends and connections across data |
| Investigation Summaries | Generate comprehensive intelligence reports |

### 🤖 **LLM Provider Support**
| Provider | Models |
|----------|--------|
| OpenAI | **GPT-5.1** (best for coding/agentic), **GPT-5 mini**, **GPT-5 nano**, GPT-4o, GPT-4-Turbo, o1, o1-mini |
| Google | **Gemini 3 Pro** (most intelligent), Gemini 2.5 Pro, Gemini 2.5 Flash (1M context), Veo 3.1 (video), Nano Banana (images) |
| Anthropic | Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku, Claude 4 Sonnet |
| Ollama | Llama 3.2, Mistral, DeepSeek-R1, Qwen 2.5, any local model |

### 📊 **Export & Reporting**
| Format | Use Case |
|--------|----------|
| JSON | Data interchange and API integration |
| CSV | Spreadsheet analysis and data processing |
| STIX 2.1 | Threat intelligence platform integration |
| PDF | Professional investigation reports |

### 🏛️ **Enterprise Features**
- 🔐 API Authentication with JWT tokens
- 📝 Structured JSON logging with correlation IDs
- 🗄️ SQLite and PostgreSQL storage backends
- ⚡ Redis and in-memory caching
- 🔔 Webhook and email alert notifications
- 🔌 Extensible plugin architecture

---

## ⚠️ Disclaimer

> **IMPORTANT**: This tool is intended for **educational and lawful investigative purposes only**.
>
> - Accessing certain dark web content may be **illegal** depending on your jurisdiction
> - The authors are **not responsible** for any misuse of this tool
> - Ensure compliance with all relevant **laws and institutional policies**
> - Be cautious when sending queries to third-party LLM APIs
> - Use responsibly and **at your own risk**

---

## 📦 Installation

### Prerequisites

- **Python 3.10+**
- **Tor** service running locally
- **API Keys** for your preferred LLM provider

#### Installing Tor

```bash
# Linux (Debian/Ubuntu)
sudo apt install tor
sudo systemctl start tor

# macOS
brew install tor
brew services start tor

# Windows (WSL recommended)
sudo apt install tor
```

### Method 1: Docker (Recommended)

```bash
# Pull the latest image
docker pull narakaai/narakaai:latest

# Run Web UI
docker run --rm \
   -v "$(pwd)/.env:/app/.env" \
   --add-host=host.docker.internal:host-gateway \
   -p 8501:8501 \
   narakaai/narakaai:latest webui

# Run REST API
docker run --rm \
   -v "$(pwd)/.env:/app/.env" \
   --add-host=host.docker.internal:host-gateway \
   -p 8000:8000 \
   narakaai/narakaai:latest api
```

### Method 2: Python (pip)

```bash
# Clone the repository
git clone https://github.com/DebasishTripathy13/Narka-AI.git
cd Narka-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.sample .env
# Edit .env with your API keys
```

### Method 3: Development Install

```bash
# Install in editable mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### Configuration

Create a `.env` file with your API keys:

```env
# LLM Provider API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# Ollama (for local models)
OLLAMA_BASE_URL=http://localhost:11434

# Tor Configuration
TOR_SOCKS_HOST=127.0.0.1
TOR_SOCKS_PORT=9050

# Optional: Default LLM
DEFAULT_LLM_PROVIDER=google
DEFAULT_LLM_MODEL=gemini-flash-latest
```

### CLI Usage

```bash
# Basic search
python narakaai.py search "ransomware payments" --model gpt-5.1

# Full investigation
python narakaai.py investigate "credential leaks 2024" \
   --model claude-3-5-sonnet \
   --output report.json \
   --format json

# Interactive mode
python narakaai.py interactive

# Start REST API server
python narakaai.py api --host 0.0.0.0 --port 8000

# Start Web UI
python narakaai.py webui --port 8501

# Check system status
python narakaai.py status
```

### CLI Commands Reference

```
Usage: python narakaai.py [OPTIONS] COMMAND [ARGS]...

Commands:
  search       🔍 Perform a quick dark web search
  scrape       📄 Scrape content from a .onion URL
  investigate  🕵️ Run a full investigation with analysis
  interactive  💬 Start interactive investigation mode
  api          🌐 Start the REST API server
  webui        🖥️ Start the Streamlit web interface
  status       📊 Check system and service status

Options:
  --config PATH    Path to configuration file
  --verbose, -v    Enable verbose logging
  --debug          Enable debug mode
  --help           Show this message and exit
```

---

## 🏗️ Architecture

NarakAAI follows Clean Architecture principles with clear separation of concerns:

```
src/
├── core/                    # Domain Layer
│   ├── entities/            # Business entities (Investigation, SearchResult, etc.)
│   ├── interfaces/          # Abstract interfaces (ports)
│   └── services/            # Business logic services
│
├── adapters/                # Interface Adapters
│   ├── llm/                 # LLM provider implementations
│   ├── search_engines/      # Search engine adapters
│   ├── storage/             # Storage backends
│   └── export/              # Export format handlers
│
├── infrastructure/          # Frameworks & Drivers
│   ├── logging/             # Logging infrastructure
│   ├── tor/                 # Tor management
│   └── cache/               # Caching implementations
│
├── presentation/            # UI Layer
│   ├── api/                 # FastAPI REST API
│   ├── cli/                 # Click CLI application
│   └── web/                 # Streamlit web interface
│
└── plugins/                 # Plugin system
    ├── base.py              # Plugin base classes
    ├── loader.py            # Plugin discovery & loading
    └── examples/            # Example plugins
```

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CLI/API   │────▶│  Services   │────▶│  Adapters   │
│   Web UI    │◀────│  (Business  │◀────│  (External  │
│             │     │   Logic)    │     │  Systems)   │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │   Entities  │
                    │   (Domain   │
                    │   Models)   │
                    └─────────────┘
```

---

## 🌐 API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
```bash
# Get API token
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-api-key"}'

# Use token in requests
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/investigations
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/search` | Perform dark web search |
| `POST` | `/scrape` | Scrape .onion URL content |
| `POST` | `/investigations` | Create new investigation |
| `GET` | `/investigations` | List all investigations |
| `GET` | `/investigations/{id}` | Get investigation details |
| `POST` | `/investigations/{id}/analyze` | Analyze investigation data |
| `GET` | `/investigations/{id}/export` | Export investigation |
| `GET` | `/health` | Health check |
| `GET` | `/status` | System status |

### Example: Create Investigation

```bash
curl -X POST http://localhost:8000/api/v1/investigations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "query": "ransomware bitcoin wallets",
    "model": "gpt-4o",
    "search_engines": ["ahmia", "torch"],
    "options": {
      "extract_entities": true,
      "analyze_threats": true,
      "max_results": 50
    }
  }'
```

---

## 🔌 Plugins

NarakAAI supports a plugin architecture for extending functionality.

### Creating a Plugin

```python
# plugins/my_search_engine.py
from plugins.base import SearchEnginePlugin
from src.core.entities.search_result import SearchResult

class MySearchEngine(SearchEnginePlugin):
    name = "my_engine"
    version = "1.0.0"
    
    async def search(self, query: str, **kwargs) -> list[SearchResult]:
        # Implement your search logic
        results = await self._fetch_results(query)
        return [
            SearchResult(
                url=r["url"],
                title=r["title"],
                snippet=r["snippet"]
            )
            for r in results
        ]
```

### Plugin Types

| Type | Base Class | Purpose |
|------|------------|---------|
| Search Engine | `SearchEnginePlugin` | Add new search sources |
| LLM Provider | `LLMPlugin` | Add new AI models |
| Exporter | `ExporterPlugin` | Add new export formats |
| Analyzer | `AnalyzerPlugin` | Add custom analysis |

### Loading Plugins

```python
from plugins.loader import PluginManager

manager = PluginManager()
manager.discover_plugins("./plugins")
manager.load_all()

# Use loaded plugins
search_plugins = manager.get_plugins_by_type("search_engine")
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_entity_extractor.py

# Run with verbose output
pytest tests/ -v
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Configuration Guide](docs/configuration.md) | Detailed configuration options |
| [Architecture Overview](docs/architecture.md) | System design and patterns |
| [API Documentation](docs/api.md) | REST API reference |
| [Plugin Development](docs/plugins.md) | Creating custom plugins |
| [Deployment Guide](docs/deployment.md) | Production deployment |

---

## 🛠️ Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/DebasishTripathy13/Narka-AI.git
cd Narka-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black isort mypy

# Run linting
black src/ tests/
isort src/ tests/
mypy src/

# Run tests
pytest tests/ -v
```

### Project Structure

```
Narka-AI/
├── src/                     # Source code
├── tests/                   # Test suite
├── plugins/                 # Plugin directory
├── docs/                    # Documentation
├── .github/                 # GitHub workflows
├── docker/                  # Docker configurations
├── config.example.yaml      # Example config file
├── .env.sample              # Example environment file
├── requirements.txt         # Python dependencies
├── narakaai.py              # Main entry point
└── README.md                # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for public methods
- Add tests for new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Ahmia](https://ahmia.fi/) - Dark web search engine
- [Tor Project](https://www.torproject.org/) - Anonymous communication
- [LangChain](https://langchain.com/) - LLM framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Streamlit](https://streamlit.io/) - Data app framework

---

## 📬 Contact

- **Issues**: [GitHub Issues](https://github.com/DebasishTripathy13/Narka-AI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DebasishTripathy13/Narka-AI/discussions)

---

<div align="center">
   <p>
      <strong>🦅 Naraka AI</strong> - Illuminate the Dark Web
   </p>
   <p>
      Made with ❤️ for the security research community
   </p>
</div>

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

- Fork the repository
- Create your feature branch (git checkout -b feature/amazing-feature)
- Commit your changes (git commit -m 'Add some amazing feature')
- Push to the branch (git push origin feature/amazing-feature)
- Open a Pull Request

Open an Issue for any of these situations:
- If you spot a bug or bad code
- If you have a feature request idea
- If you have questions or doubts about usage

---

## Acknowledgements

- Idea inspiration from [Thomas Roccia](https://x.com/fr0gger_) and his demo of [Perplexity of the Dark Web](https://x.com/fr0gger_/status/1908051083068645558).
- Tools inspiration from my [OSINT Tools for the Dark Web](https://github.com/apurvsinghgautam/dark-web-osint-tools) repository.
- LLM Prompt inspiration from [OSINT-Assistant](https://github.com/AXRoux/OSINT-Assistant) repository.
- Logo Design by my friend [Tanishq Rupaal](https://github.com/Tanq16/)

