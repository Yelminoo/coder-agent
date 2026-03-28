# Basic tests for AI Coding Assistant
import pytest
from fastapi.testclient import TestClient


def test_imports():
    """Test that main modules can be imported"""
    try:
        from web_server import app
        from llm.engine import MultiProviderLLM
        from router.agent_registry import AgentRegistry
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_app_exists():
    """Test that FastAPI app is created"""
    from web_server import app
    assert app is not None


def test_health_endpoint():
    """Test the root endpoint returns 200"""
    from web_server import app
    
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_agents_endpoint():
    """Test that agents API endpoint works"""
    from web_server import app
    
    client = TestClient(app)
    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert isinstance(data["agents"], list)


def test_agent_registry():
    """Test agent registry loads correctly"""
    from router.agent_registry import AgentRegistry
    
    registry = AgentRegistry()
    agents = registry.list_agents()
    assert len(agents) > 0
    assert registry.get_default_agent_id() is not None


def test_llm_engine_initialization():
    """Test that LLM engine can be initialized"""
    from llm.engine import MultiProviderLLM
    
    engine = MultiProviderLLM()
    assert engine is not None
    assert engine.provider in ["openai", "anthropic", "google", "ollama"]


def test_chat_store_initialization():
    """Test that chat store can be initialized"""
    from data.chat_sessions_sqlite import ChatSessionStore
    import tempfile
    import os
    
    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        store = ChatSessionStore(tmp_path)
        assert store is not None
        
        # Test basic operations
        chat_id = "test_chat"
        store.append_turn(chat_id, "Hello", "Hi there!")
        turns = store.get_recent_turns(chat_id)
        assert len(turns) == 1
        assert turns[0]["user"] == "Hello"
        assert turns[0]["assistant"] == "Hi there!"
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_sanitize_input():
    """Test input sanitization function"""
    from web_server import sanitize_input
    
    # Test normal input
    assert sanitize_input("Hello World") == "Hello World"
    
    # Test null byte removal
    assert sanitize_input("Hello\x00World") == "HelloWorld"
    
    # Test control character removal
    result = sanitize_input("Hello\x01\x02World")
    assert "\x01" not in result
    assert "\x02" not in result
    
    # Test newlines are preserved
    assert sanitize_input("Hello\nWorld") == "Hello\nWorld"
    
    # Test length limit
    long_text = "a" * 60000
    result = sanitize_input(long_text, max_length=1000)
    assert len(result) == 1000


def test_sanitize_identifier():
    """Test identifier sanitization function"""
    from web_server import sanitize_identifier
    
    # Test valid identifier
    assert sanitize_identifier("my_agent_123") == "my_agent_123"
    
    # Test removes invalid characters
    assert sanitize_identifier("my agent!@#") == "myagent"
    
    # Test prevents path traversal
    assert sanitize_identifier("../../../etc/passwd") == "etcpasswd"
    
    # Test length limit
    long_id = "a" * 200
    result = sanitize_identifier(long_id, max_length=50)
    assert len(result) == 50


def test_ollama_status_endpoint():
    """Test Ollama status endpoint structure"""
    from web_server import app
    
    client = TestClient(app)
    response = client.get("/api/ollama/status")
    assert response.status_code == 200
    data = response.json()
    
    # Check expected fields exist
    assert "connected" in data
    assert "model" in data
    assert "host" in data


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_basic.py -v
    pytest.main([__file__, "-v"])
