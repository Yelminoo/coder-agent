"""
Pytest configuration file
"""
import os
import sys

# Add parent directory to path so tests can import from main package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set environment variables for testing
os.environ['LLM_MODE'] = 'LOCAL_ONLY'
os.environ['OLLAMA_HOST'] = 'http://localhost:11434'
os.environ['OLLAMA_MODEL'] = 'llama3.2:latest'
os.environ['CHAT_STORE_BACKEND'] = 'sqlite'
os.environ['ENABLE_URL_FETCH'] = 'false'
