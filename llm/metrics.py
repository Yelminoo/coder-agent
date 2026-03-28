"""Shared metrics for LLM performance tracking."""

# Ollama metrics tracking
OLLAMA_METRICS = {
    "response_times": [],
    "last_response_time": None,
    "connection_status": None,
    "last_check": None
}


def record_ollama_response_time(duration: float):
    """Record Ollama response time in seconds."""
    OLLAMA_METRICS["last_response_time"] = duration
    OLLAMA_METRICS["response_times"].append(duration)
    
    # Keep only last 10 response times
    if len(OLLAMA_METRICS["response_times"]) > 10:
        OLLAMA_METRICS["response_times"] = OLLAMA_METRICS["response_times"][-10:]


def get_ollama_metrics() -> dict:
    """Get current Ollama metrics."""
    return OLLAMA_METRICS.copy()
