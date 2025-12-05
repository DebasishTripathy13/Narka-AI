# Configuration Guide

Robin uses a layered configuration system that supports:
- Environment variables
- `.env` files
- YAML configuration files

## Environment Variables

All configuration options can be set via environment variables.

### LLM Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GOOGLE_API_KEY` | Google AI API key | - |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://127.0.0.1:11434` |
| `LLM_DEFAULT_MODEL` | Default LLM model | `gpt-4o` |
| `LLM_TEMPERATURE` | Model temperature | `0.0` |

### Tor Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TOR_HOST` | Tor SOCKS proxy host | `127.0.0.1` |
| `TOR_PORT` | Tor SOCKS proxy port | `9050` |
| `TOR_CONTROL_PORT` | Tor control port | `9051` |
| `TOR_CONTROL_PASSWORD` | Tor control password | - |

### Search Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARCH_MAX_RESULTS_PER_ENGINE` | Max results per engine | `50` |
| `SEARCH_TIMEOUT` | Search timeout (seconds) | `30` |
| `SEARCH_MAX_WORKERS` | Parallel search workers | `5` |

### API Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | API server host | `127.0.0.1` |
| `API_PORT` | API server port | `8080` |
| `API_DEBUG` | Enable debug mode | `false` |
| `API_RATE_LIMIT` | Requests per minute | `60` |

## YAML Configuration

Create a `config.yaml` file in the project root:

```yaml
app_name: Robin
version: "2.0.0"
debug: false

tor:
  host: "127.0.0.1"
  port: 9050

llm:
  default_model: gpt-4o
  temperature: 0.0

search:
  default_engines:
    - ahmia
    - torch
  max_results_per_engine: 50
```

## Configuration Priority

1. Environment variables (highest priority)
2. `.env` file
3. `config.yaml` file
4. Default values (lowest priority)
