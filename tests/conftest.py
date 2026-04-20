"""Pytest configuration for Cy language tests."""

import sys
from pathlib import Path

import dotenv

# Add src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env from project root (OPENAI_API_KEY, etc.)
dotenv.load_dotenv(Path(__file__).parent.parent / ".env")
