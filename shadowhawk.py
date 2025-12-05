#!/usr/bin/env python3
"""
🦅 NarakAI - Advanced AI-Powered Dark Web Intelligence Platform

Main entry point for the application.

Usage:
    python narakai.py --help
    python narakai.py search "query" --model gpt-5.1
    python narakai.py investigate "query" --output report.json
    python narakai.py api --port 8000
    python narakai.py webui --port 8501
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.presentation.cli import main

if __name__ == "__main__":
    main()
