from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, validator
import asyncio
import json
import os
import requests
import secrets
import re
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from llm.engine import MultiProviderLLM
from llm.metrics import get_ollama_metrics
from router.agent_registry import AgentRegistry
from data.chat_sessions import ChatSessionStore as JsonChatSessionStore
from data.chat_sessions_sqlite import ChatSessionStore as SqliteChatSessionStore
from data.app_context import load_app_context

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
agent_registry = AgentRegistry()
chat_backend = os.getenv("CHAT_STORE_BACKEND", "sqlite").lower()
if chat_backend == "json":
    chat_store = JsonChatSessionStore(os.getenv("CHAT_SESSIONS_FILE", "data/chat_sessions_store.json"))
else:
    chat_store = SqliteChatSessionStore(os.getenv("CHAT_DB_PATH", "data/chat_sessions.db"))
APP_CONTEXT_PDF = os.getenv("APP_CONTEXT_PDF", "docs/app_overview.pdf")
APP_CONTEXT_TEXT = load_app_context(APP_CONTEXT_PDF)
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")
SESSION_COOKIE_NAME = "ai_session"
OAUTH_STATES: dict[str, str] = {}
USER_SESSIONS: dict[str, dict] = {}

def sanitize_input(text: str, max_length: int = 50000) -> str:
    """Sanitize user input to prevent XSS and other attacks."""
    if not text:
        return ""
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Limit length to prevent DoS
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if char in '\n\t\r' or ord(char) >= 32)
    
    return text


def sanitize_identifier(text: str, max_length: int = 100) -> str:
    """Sanitize identifiers like chat_id, agent_id to prevent path traversal."""
    if not text:
        return ""
    
    # Remove dangerous characters
    text = re.sub(r'[^a-zA-Z0-9_-]', '', text)
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Prevent path traversal
    text = text.replace('..', '').replace('/', '').replace('\\', '')
    
    return text


class PromptRequest(BaseModel):
    prompt: str
    include_test: bool = True
    agent_id: str | None = None
    chat_id: str | None = None
    search_mode: bool = False
    
    @validator('prompt')
    def sanitize_prompt(cls, v):
        return sanitize_input(v, max_length=50000)
    
    @validator('agent_id', 'chat_id')
    def sanitize_ids(cls, v):
        if v is None:
            return v
        return sanitize_identifier(v, max_length=100)


def is_code_intent(prompt: str) -> bool:
    text = (prompt or "").lower()
    code_keywords = [
        "code", "function", "class", "script", "implement", "write a", "create a",
        "build", "refactor", "debug", "fix bug", "pytest", "unit test", "api endpoint"
    ]
    return any(keyword in text for keyword in code_keywords)


def build_contextual_prompt(current_prompt: str, turns: list[dict[str, str]]) -> str:
    if not turns:
        return current_prompt

    transcript = []
    for turn in turns:
        transcript.append(f"User: {turn.get('user', '')}")
        transcript.append(f"Assistant: {turn.get('assistant', '')}")

    history_block = "\n".join(transcript)
    return f"Conversation so far:\n{history_block}\n\nCurrent user message:\n{current_prompt}"


def detect_urls(text: str) -> list[str]:
    """Extract all URLs from text."""
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    urls = re.findall(url_pattern, text)
    return urls


def fetch_url_content(url: str, max_chars: int = 5000) -> dict:
    """Fetch and extract readable content from a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        # Try to use BeautifulSoup for better content extraction
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Get title
            title = soup.title.string if soup.title else url
            
        except ImportError:
            # Fallback to simple text extraction
            text = response.text
            title = url
        
        # Truncate if too long
        if len(text) > max_chars:
            text = text[:max_chars] + "... (truncated)"
        
        return {
            "url": url,
            "title": str(title).strip(),
            "content": text.strip(),
            "success": True
        }
    
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }


def process_urls_in_prompt(prompt: str) -> tuple[str, list[dict]]:
    """Detect URLs in prompt, fetch their content, and return enriched prompt."""
    urls = detect_urls(prompt)
    
    if not urls:
        return prompt, []
    
    print(f"\n{'='*60}")
    print(f"🔗 URL DETECTION: Found {len(urls)} URL(s) in prompt")
    for i, url in enumerate(urls[:3], 1):
        print(f"   {i}. {url}")
    print(f"{'='*60}\n")
    
    fetched_contents = []
    for i, url in enumerate(urls[:3], 1):  # Limit to 3 URLs to avoid overload
        print(f"📥 Fetching URL {i}/{min(len(urls), 3)}: {url}")
        content = fetch_url_content(url)
        if content.get('success'):
            print(f"   ✅ Success! Title: {content.get('title', 'N/A')[:60]}...")
            print(f"   📄 Extracted {len(content.get('content', ''))} characters")
        else:
            print(f"   ❌ Failed: {content.get('error', 'Unknown error')}")
        fetched_contents.append(content)
    
    # Build enriched prompt with URL contents
    if fetched_contents:
        url_context = []
        for item in fetched_contents:
            if item.get("success"):
                url_context.append(
                    f"Content from {item['url']}:\n"
                    f"Title: {item['title']}\n"
                    f"{item['content'][:2000]}\n"  # Limit per URL
                )
            else:
                url_context.append(f"Failed to fetch {item['url']}: {item.get('error', 'Unknown error')}")
        
        enriched_prompt = (
            f"{prompt}\n\n"
            f"--- Fetched URL Content ---\n"
            f"{chr(10).join(url_context)}\n"
            f"--- End of URL Content ---\n\n"
            f"Please analyze and summarize the content from the URL(s) above in relation to the user's request."
        )
        
        print(f"\n\u2705 Successfully enriched prompt with {len([f for f in fetched_contents if f.get('success')])} URL content(s)")
        print(f"{'='*60}\n")
        
        return enriched_prompt, fetched_contents
    
    return prompt, []


def global_web_search(query: str, max_results: int = 5) -> list[str]:
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    snippets: list[str] = []
    abstract = (payload.get("AbstractText") or "").strip()
    if abstract:
        snippets.append(abstract)

    def collect_related(items: list):
        for item in items:
            if isinstance(item, dict):
                if "Text" in item and item["Text"]:
                    snippets.append(str(item["Text"]).strip())
                nested = item.get("Topics")
                if isinstance(nested, list):
                    collect_related(nested)

    related = payload.get("RelatedTopics")
    if isinstance(related, list):
        collect_related(related)

    deduped = []
    seen = set()
    for text in snippets:
        if text and text not in seen:
            seen.add(text)
            deduped.append(text)
    return deduped[:max_results]


def should_use_global_search(prompt: str, answer: str) -> bool:
    prompt_text = (prompt or "").lower()
    answer_text = (answer or "").lower().strip()
    if not answer_text:
        return True

    realtime_keywords = ["latest", "today", "current", "real-time", "news", "updated", "recent"]
    if any(keyword in prompt_text for keyword in realtime_keywords):
        return True

    low_confidence_markers = [
        "i don't know",
        "i do not know",
        "not sure",
        "cannot browse",
        "can't browse",
        "do not have access",
        "no access to",
        "unable to find",
        "error connecting",
        "insufficient information",
    ]
    return any(marker in answer_text for marker in low_confidence_markers)


def is_news_query(prompt: str) -> bool:
    text = (prompt or "").lower()
    keywords = ["news", "latest", "today", "headline", "breaking", "recent", "current events", "what happened"]
    return any(keyword in text for keyword in keywords)


def fetch_news_rss(topic: str = "", max_results: int = 5) -> list[str]:
    """Fetch headlines from Google News RSS. No API key required."""
    try:
        query = topic.strip() if topic.strip() else "world"
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        headlines = []
        for item in items[:max_results]:
            title_el = item.find("title")
            pub_el = item.find("pubDate")
            if title_el is not None and title_el.text:
                title = title_el.text.strip()
                pub = pub_el.text.strip() if pub_el is not None and pub_el.text else ""
                headlines.append(f"{title} ({pub})" if pub else title)
        return headlines
    except Exception as e:
        print(f"⚠️ RSS fetch failed: {e}")
        return []


def is_weather_query(prompt: str) -> bool:
    text = (prompt or "").lower()
    keywords = ["weather", "temperature", "forecast", "rain", "humidity", "wind"]
    return any(keyword in text for keyword in keywords)


def extract_location(prompt: str) -> str:
    text = (prompt or "").strip()
    match = re.search(r"(?:weather|forecast|temperature)\s+(?:in|for)\s+([A-Za-z0-9\s,.-]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip(" .,")

    fallback = os.getenv("DEFAULT_LOCATION", "New York")
    return fallback


def fetch_live_weather(location: str) -> dict | None:
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        geo.raise_for_status()
        geo_data = geo.json()
        results = geo_data.get("results") or []
        if not results:
            return None

        place = results[0]
        lat = place.get("latitude")
        lon = place.get("longitude")
        if lat is None or lon is None:
            return None

        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            },
            timeout=10,
        )
        weather.raise_for_status()
        weather_data = weather.json()
        current = weather_data.get("current") or {}
        if not current:
            return None

        return {
            "location": f"{place.get('name')}, {place.get('country')}",
            "time": current.get("time"),
            "temperature_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_kmh": current.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
        }
    except Exception:
        return None


def get_session_id(request: Request) -> str | None:
    sid = request.cookies.get(SESSION_COOKIE_NAME)
    if sid and isinstance(sid, str):
        return sid
    return None


def ensure_session_id(request: Request) -> tuple[str, bool]:
    sid = get_session_id(request)
    if sid:
        return sid, False
    return secrets.token_urlsafe(24), True


def current_user_from_session(request: Request) -> dict | None:
    sid = get_session_id(request)
    user = USER_SESSIONS.get(sid or "")
    if isinstance(user, dict):
        return user
    return None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    engine = MultiProviderLLM()
    agent_registry.reload()
    agents = agent_registry.list_agents()
    default_agent_id = agent_registry.get_default_agent_id()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "current_provider": engine.provider.upper(),
        "is_local": engine.provider == "ollama",
        "agents": agents,
        "default_agent_id": default_agent_id,
        "current_user": current_user_from_session(request),
    })


@app.get("/api/db/status")
async def db_status():
    if hasattr(chat_store, "get_stats"):
        return JSONResponse(chat_store.get_stats())
    return JSONResponse({"error": "DB stats unavailable"}, status_code=500)


def check_ollama_connection() -> dict:
    """Check Ollama connection and return status metrics."""
    import time
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    
    # Get metrics from shared module
    metrics = get_ollama_metrics()
    
    try:
        start_time = time.time()
        response = requests.get(f"{ollama_host}/api/tags", timeout=3)
        elapsed = time.time() - start_time
        
        if response.ok:
            # Calculate average response time
            avg_time = None
            if metrics["response_times"]:
                avg_time = sum(metrics["response_times"]) / len(metrics["response_times"])
            
            return {
                "connected": True,
                "host": ollama_host,
                "model": ollama_model,
                "last_response_time": metrics["last_response_time"],
                "avg_response_time": avg_time,
                "ping_time": round(elapsed, 3)
            }
        else:
            return {"connected": False, "host": ollama_host, "model": ollama_model}
            
    except Exception as e:
        return {
            "connected": False,
            "host": ollama_host,
            "model": ollama_model,
            "error": str(e)
        }


@app.get("/api/ollama/status")
async def ollama_status():
    """Get real-time Ollama model status and metrics."""
    status = check_ollama_connection()
    
    # Check GPU availability
    try:
        import subprocess
        gpu_check = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if gpu_check.returncode == 0 and gpu_check.stdout.strip():
            gpu_info = gpu_check.stdout.strip().split(", ")
            status["gpu"] = {
                "available": True,
                "name": gpu_info[0] if len(gpu_info) > 0 else "Unknown",
                "memory_total": gpu_info[1] if len(gpu_info) > 1 else "Unknown",
                "memory_used": gpu_info[2] if len(gpu_info) > 2 else "Unknown"
            }
        else:
            status["gpu"] = {"available": False, "message": "No NVIDIA GPU detected"}
    except (FileNotFoundError, Exception):
        status["gpu"] = {"available": False, "message": "nvidia-smi not found (CPU only)"}
    
    return JSONResponse(status)


@app.get("/api/ollama/models")
async def list_ollama_models():
    """List all available Ollama models."""
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if response.ok:
            data = response.json()
            models = data.get("models", [])
            model_list = []
            for model in models:
                model_list.append({
                    "name": model.get("name"),
                    "size": model.get("size"),
                    "modified": model.get("modified_at"),
                })
            return JSONResponse({
                "success": True,
                "models": model_list,
                "current": os.getenv("OLLAMA_MODEL", "llama3.2:latest")
            })
        else:
            return JSONResponse({"success": False, "error": "Failed to connect to Ollama"}, status_code=500)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/ollama/switch-model")
async def switch_ollama_model(request: Request):
    """Switch the active Ollama model."""
    try:
        body = await request.json()
        model_name = body.get("model")
        if not model_name:
            return JSONResponse({"success": False, "error": "Model name required"}, status_code=400)
        
        # Update environment variable for current session
        os.environ["OLLAMA_MODEL"] = model_name
        
        return JSONResponse({
            "success": True,
            "model": model_name,
            "message": f"Switched to {model_name}"
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/api/me")
async def api_me(request: Request):
    user = current_user_from_session(request)
    if not user:
        return JSONResponse({"authenticated": False})
    return JSONResponse({"authenticated": True, "user": user})


@app.get("/auth/github/login")
async def github_login(request: Request):
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return JSONResponse({"error": "GitHub OAuth is not configured."}, status_code=500)

    sid, created = ensure_session_id(request)
    state = secrets.token_urlsafe(24)
    OAUTH_STATES[sid] = state
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": state,
    }
    query = "&".join(f"{k}={requests.utils.quote(str(v), safe='')}" for k, v in params.items())
    response = RedirectResponse(url=f"https://github.com/login/oauth/authorize?{query}", status_code=302)
    if created:
        response.set_cookie(SESSION_COOKIE_NAME, sid, httponly=True, samesite="lax")
    return response


@app.get("/auth/github/callback")
async def github_callback(request: Request, code: str = "", state: str = ""):
    sid = get_session_id(request)
    session_state = OAUTH_STATES.get(sid or "")
    if not code or not state or not session_state or state != session_state:
        return RedirectResponse(url="/?auth=failed", status_code=302)

    token_resp = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_REDIRECT_URI,
            "state": state,
        },
        timeout=15,
    )
    token_payload = token_resp.json() if token_resp.ok else {}
    access_token = token_payload.get("access_token")
    if not access_token:
        return RedirectResponse(url="/?auth=failed", status_code=302)

    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github+json",
    }
    user_resp = requests.get("https://api.github.com/user", headers=headers, timeout=15)
    if not user_resp.ok:
        return RedirectResponse(url="/?auth=failed", status_code=302)

    user_payload = user_resp.json()
    email_value = user_payload.get("email")
    if not email_value:
        emails_resp = requests.get("https://api.github.com/user/emails", headers=headers, timeout=15)
        if emails_resp.ok:
            emails = emails_resp.json()
            if isinstance(emails, list):
                primary = next((item for item in emails if item.get("primary")), None)
                if primary:
                    email_value = primary.get("email")
                elif emails:
                    email_value = emails[0].get("email")

    USER_SESSIONS[sid] = {
        "id": user_payload.get("id"),
        "login": user_payload.get("login"),
        "name": user_payload.get("name") or user_payload.get("login"),
        "avatar_url": user_payload.get("avatar_url"),
        "email": email_value,
    }
    OAUTH_STATES.pop(sid, None)
    return RedirectResponse(url="/?auth=ok", status_code=302)


@app.get("/auth/logout")
async def logout(request: Request):
    sid = get_session_id(request)
    if sid:
        USER_SESSIONS.pop(sid, None)
        OAUTH_STATES.pop(sid, None)
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@app.get("/api/agents")
async def list_agents():
    agent_registry.reload()
    return JSONResponse({
        "default_agent": agent_registry.get_default_agent_id(),
        "agents": agent_registry.list_agents()
    })


@app.post("/api/agents/{agent_id}")
async def update_agent(agent_id: str, request: Request):
    """Update an agent's configuration."""
    try:
        body = await request.json()
        
        # Validate and sanitize inputs
        updates = {}
        if "name" in body:
            updates["name"] = sanitize_input(body["name"], max_length=100)
        if "system_prompt" in body:
            updates["system_prompt"] = sanitize_input(body["system_prompt"], max_length=5000)
        if "description" in body:
            updates["description"] = sanitize_input(body["description"], max_length=500)
        
        if not updates:
            return JSONResponse({"success": False, "error": "No valid fields to update"}, status_code=400)
        
        success = agent_registry.update_agent(agent_id, updates)
        
        if success:
            return JSONResponse({"success": True, "message": f"Agent {agent_id} updated successfully"})
        else:
            return JSONResponse({"success": False, "error": "Agent not found"}, status_code=404)
    
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/agents")
async def create_agent(request: Request):
    """Create a new agent."""
    try:
        body = await request.json()
        
        # Validate and sanitize inputs
        agent_data = {
            "id": sanitize_identifier(body.get("id", ""), max_length=50),
            "name": sanitize_input(body.get("name", ""), max_length=100),
            "mode": body.get("mode", "contextual"),
            "description": sanitize_input(body.get("description", ""), max_length=500),
            "system_prompt": sanitize_input(body.get("system_prompt", ""), max_length=5000)
        }
        
        if not agent_data["id"] or not agent_data["name"]:
            return JSONResponse({"success": False, "error": "Agent ID and name are required"}, status_code=400)
        
        result = agent_registry.create_agent(agent_data)
        
        if result.get("success"):
            return JSONResponse(result)
        else:
            return JSONResponse(result, status_code=400)
    
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent."""
    try:
        result = agent_registry.delete_agent(agent_id)
        
        if result.get("success"):
            return JSONResponse(result)
        else:
            return JSONResponse(result, status_code=400)
    
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/api/chats/{chat_id}/history")
async def chat_history(chat_id: str):
    turns = chat_store.get_recent_turns(chat_id, limit=200)
    return JSONResponse({
        "chat_id": chat_id,
        "agent_id": chat_store.get_agent_id(chat_id),
        "turns": turns
    })


@app.get("/api/chats/export/all")
async def export_all_chats():
    """Export all conversations for fine-tuning."""
    if not hasattr(chat_store, '_connect'):
        return JSONResponse({"error": "Export only available with SQLite backend"}, status_code=400)
    
    all_conversations = []
    with chat_store._connect() as conn:
        cursor = conn.execute(
            "SELECT chat_id, user_prompt, assistant_reply, created_at FROM messages ORDER BY chat_id, created_at"
        )
        for row in cursor:
            all_conversations.append({
                "chat_id": row["chat_id"],
                "user": row["user_prompt"],
                "assistant": row["assistant_reply"],
                "timestamp": row["created_at"]
            })
    
    return JSONResponse({
        "total_messages": len(all_conversations),
        "conversations": all_conversations
    })


@app.get("/api/chats/export/jsonl")
async def export_jsonl():
    """Export conversations in JSONL format for Ollama fine-tuning."""
    from fastapi.responses import StreamingResponse
    import io
    
    if not hasattr(chat_store, '_connect'):
        return JSONResponse({"error": "Export only available with SQLite backend"}, status_code=400)
    
    def generate_jsonl():
        with chat_store._connect() as conn:
            cursor = conn.execute(
                "SELECT user_prompt, assistant_reply FROM messages ORDER BY created_at"
            )
            for row in cursor:
                line = json.dumps({
                    "prompt": row["user_prompt"],
                    "response": row["assistant_reply"]
                }) + "\n"
                yield line
    
    return StreamingResponse(
        generate_jsonl(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=training_data.jsonl"}
    )


def run_generation(req: PromptRequest) -> dict:
    if not (req.prompt or "").strip():
        return {"error": "Prompt cannot be empty.", "status_code": 400}

    agent_registry.reload()
    chat_id = req.chat_id or "default"
    persisted_agent_id = chat_store.get_agent_id(chat_id)
    resolved_agent_id = req.agent_id or persisted_agent_id
    selected_agent = agent_registry.get_agent(resolved_agent_id)
    chat_store.set_agent_id(chat_id, selected_agent.get("id"))
    engine = MultiProviderLLM()
    requested_test = req.include_test
    mode = selected_agent.get("mode", "contextual")
    code_requested = is_code_intent(req.prompt)
    allow_code_output = mode == "code-first" or (mode == "contextual" and code_requested)
    include_test = requested_test and allow_code_output
    system_prompt = selected_agent.get("system_prompt", "You are a helpful assistant.")
    if not allow_code_output:
        system_prompt = (
            f"{system_prompt}\n"
            "Respond in plain conversational text. Do not output code blocks or source code unless the user explicitly asks for code."
        )

    if APP_CONTEXT_TEXT:
        system_prompt = (
            f"{system_prompt}\n\n"
            "Application context (source-of-truth):\n"
            f"{APP_CONTEXT_TEXT}\n\n"
            "Use this context to keep responses aligned with what this application is built to do."
        )
    # URL processing disabled by user request
    # To re-enable, set ENABLE_URL_FETCH=true in .env
    enable_url_fetch = os.getenv("ENABLE_URL_FETCH", "false").lower() == "true"
    
    if enable_url_fetch:
        current_prompt_enriched, fetched_urls = process_urls_in_prompt(req.prompt)
        prompt_with_context = build_contextual_prompt(current_prompt_enriched, chat_store.get_recent_turns(chat_id))
        if fetched_urls:
            print(f"📎 Processed {len(fetched_urls)} URL(s) from current message and enriched prompt")
    else:
        prompt_with_context = build_contextual_prompt(req.prompt, chat_store.get_recent_turns(chat_id))
        fetched_urls = []
    
    search_used = False
    search_results: list[str] = []
    search_source = None
    urls_processed = fetched_urls  # Track processed URLs for response metadata

    print(f"🔍 search_mode={'ON' if req.search_mode else 'OFF'} | prompt={req.prompt!r}")

    if req.search_mode and not allow_code_output:
        if is_weather_query(req.prompt):
            # Live weather via Open-Meteo — bypass LLM entirely
            weather_location = extract_location(req.prompt)
            weather = fetch_live_weather(weather_location)
            if weather:
                search_used = True
                search_source = "open-meteo"
                code = (
                    f"Current weather for {weather['location']} (as of {weather['time']}):\n"
                    f"- Temperature: {weather['temperature_c']}°C\n"
                    f"- Feels like: {weather['feels_like_c']}°C\n"
                    f"- Humidity: {weather['humidity']}%\n"
                    f"- Wind: {weather['wind_kmh']} km/h\n"
                    f"- Weather code: {weather['weather_code']}"
                )
                search_results = [
                    f"location={weather['location']}",
                    f"temperature_c={weather['temperature_c']}",
                    f"humidity={weather['humidity']}",
                    f"wind_kmh={weather['wind_kmh']}",
                ]
            else:
                code = engine.generate(prompt_with_context, system_prompt=system_prompt)
        elif is_news_query(req.prompt):
            # News query — fetch from Google News RSS first
            topic = re.sub(r"(find|today|latest|recent|breaking|news|headlines?)\s*", "", req.prompt, flags=re.IGNORECASE).strip()
            rss_results = fetch_news_rss(topic or "top stories", max_results=5)
            print(f"📰 Google News RSS returned {len(rss_results)} headline(s)")
            if rss_results:
                search_used = True
                search_source = "google-news-rss"
                search_results = rss_results
                findings = "\n".join(f"- {item}" for item in rss_results)
                enriched_prompt = (
                    f"{prompt_with_context}\n\n"
                    f"Live news headlines (as of today):\n{findings}\n\n"
                    "Summarise these headlines for the user in a helpful way."
                )
                code = engine.generate(enriched_prompt, system_prompt=system_prompt)
            else:
                code = engine.generate(prompt_with_context, system_prompt=system_prompt)
        else:
            # For all other queries, fetch global search results FIRST and inject into prompt
            web_results = global_web_search(req.prompt)
            print(f"🌐 DuckDuckGo returned {len(web_results)} result(s)")
            if web_results:
                search_used = True
                search_source = "duckduckgo"
                search_results = web_results
                findings = "\n".join(f"- {item}" for item in web_results)
                enriched_prompt = (
                    f"{prompt_with_context}\n\n"
                    f"Global search results (use these to answer accurately):\n{findings}"
                )
                code = engine.generate(enriched_prompt, system_prompt=system_prompt)
            else:
                # No search results — fall back to plain LLM
                code = engine.generate(prompt_with_context, system_prompt=system_prompt)
    else:
        code = engine.generate(prompt_with_context, system_prompt=system_prompt)

    # Sanitize before storing in database
    safe_prompt = sanitize_input(req.prompt)
    safe_code = sanitize_input(code)
    created_at = chat_store.append_turn(chat_id, safe_prompt, safe_code)

    result = {
        "code": code,
        "provider": engine.provider,
        "test_code": None,
        "agent_id": selected_agent.get("id"),
        "agent_name": selected_agent.get("name"),
        "mode": mode,
        "chat_id": chat_id,
        "allow_code_output": allow_code_output,
        "search_mode": req.search_mode,
        "search_used": search_used,
        "search_source": search_source,
        "search_results": search_results,
        "urls_processed": urls_processed if 'urls_processed' in locals() else [],
        "turn": {
            "user": req.prompt,
            "assistant": code,
            "created_at": created_at
        }
    }

    if include_test:
        test_prompt = f"Write a pytest unit test for this code:\n\n{code}"
        result["test_code"] = engine.generate(test_prompt, system_prompt="Write only pytest code.")

    return result

@app.post("/api/generate")
async def generate(req: PromptRequest):
    result = run_generation(req)
    if result.get("status_code"):
        return JSONResponse({"error": result.get("error", "Request failed")}, status_code=result["status_code"])
    return JSONResponse(result)


@app.post("/api/generate/stream")
async def generate_stream(req: PromptRequest):
    result = run_generation(req)
    if result.get("status_code"):
        return JSONResponse({"error": result.get("error", "Request failed")}, status_code=result["status_code"])

    async def event_stream():
        yield f"data: {json.dumps({'type': 'meta', 'payload': {'allow_code_output': result.get('allow_code_output', False), 'search_used': result.get('search_used', False), 'search_source': result.get('search_source'), 'urls_processed': result.get('urls_processed', [])}})}\n\n"
        text = result.get("code", "")
        step = int(os.getenv("STREAM_CHUNK_SIZE", "14"))
        for index in range(0, len(text), step):
            chunk = text[index:index + step]
            yield f"data: {json.dumps({'type': 'chunk', 'delta': chunk})}\n\n"
            await asyncio.sleep(0.01)
        yield f"data: {json.dumps({'type': 'done', 'payload': result})}\n\n"
        yield "data: {\"type\":\"end\"}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    import uvicorn
    engine = MultiProviderLLM()
    print(f"🚀 Server Starting... Mode: {engine.provider.upper()}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
