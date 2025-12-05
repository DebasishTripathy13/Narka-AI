#!/usr/bin/env python3
"""
🦅 NarakAAI - Advanced AI-Powered Dark Web Intelligence Platform

Main entry point for the application.

Usage:
    python narakaai.py --help
    python narakaai.py search "query" --model gpt-5.1
    python narakaai.py investigate "query" --output report.json
    python narakaai.py api --port 8000
    python narakaai.py webui --port 8501
"""

import sys
import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.presentation.cli import main

if __name__ == "__main__":
    main()
