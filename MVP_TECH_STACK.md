# MVP Tech Stack - 1-Day Build

## 🎯 Goal
Build a functional MVP in **one day** that:
1. Connects to a local git repo
2. Accepts natural language requests
3. Routes to Cloud LLM (fallback) or Local LLM
4. Generates code changes
5. Applies changes to the repo (with approval)
6. Logs Cloud responses for future local training

---

## 🛠️ Minimal Tech Stack

### Core Language
- **Python 3.10+** (single language for everything)

### LLM Integration
- **Cloud**: `openai` package (GPT-4) or `anthropic` (Claude) - *pick one for MVP*
- **Local**: `ollama` Python client + `llama3.2` or `codellama` model
- **Unified Interface**: Simple wrapper class (no LangChain for MVP - too heavy)

### Repository Access
- **GitPython** - for repo operations
- Built-in `pathlib` and `difflib` for file handling

### CLI Interface
- **Typer** or **Click** - for command-line interaction
- **Rich** - for beautiful terminal output

### Data Storage (MVP Simple)
- **SQLite** - for logging prompts/responses (training data)
- **JSON files** - for config and cache

### Dependencies (requirements.txt)
```txt
# Core
python>=3.10
typer[all]>=0.9.0
rich>=13.0.0
pydantic>=2.0.0

# Git & File Ops
gitpython>=3.1.0

# LLM Clients
openai>=1.0.0          # OR anthropic>=0.18.0
ollama>=0.1.0

# Database
sqlite3                # Built-in
aiosqlite>=0.19.0      # Async support

# Utilities
python-dotenv>=1.0.0
httpx>=0.25.0          # Async HTTP
```

---

## 📁 Project Structure (MVP)

```
ai-coding-assistant/
├── main.py                 # CLI entry point
├── config.py               # Configuration management
├── requirements.txt        # Dependencies
├── .env                    # API keys (gitignored)
│
├── llm/
│   ├── __init__.py
│   ├── base.py             # Abstract LLM interface
│   ├── cloud_llm.py        # OpenAI/Claude implementation
│   └── local_llm.py        # Ollama implementation
│
├── repo/
│   ├── __init__.py
│   ├── manager.py          # GitPython wrapper
│   └── changer.py          # Apply code changes
│
├── router/
│   └── selector.py         # Cloud vs Local decision logic
│
├── storage/
│   ├── __init__.py
│   ├── database.py         # SQLite for training logs
│   └── models.py           # Pydantic models
│
└── utils/
    ├── logger.py           # Rich-based logging
    └── validators.py       # Input validation
```

---

## 🔄 MVP Workflow

```
User Request (CLI)
    ↓
Load Repo Context (git status, recent files)
    ↓
Router Decision (Local if available, else Cloud)
    ↓
LLM Generation (with repo context)
    ↓
Show Diff to User
    ↓
User Approval (y/n)
    ↓
Apply Changes (git patch)
    ↓
Log to SQLite (if Cloud used → training data)
```

---

## ⚡ Quick Start Commands

### 1. Setup (5 mins)
```bash
mkdir ai-coding-assistant && cd ai-coding-assistant
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install typer[all] rich gitpython openai ollama python-dotenv pydantic
```

### 2. Configure (2 mins)
```bash
# Create .env file
echo "OPENAI_API_KEY=your_key_here" > .env
echo "LOCAL_LLM_MODEL=llama3.2" >> .env
echo "REPO_PATH=/path/to/your/repo" >> .env
```

### 3. Run (instant)
```bash
python main.py "Add a function to calculate fibonacci" --repo ./my-project
```

---

## 🎨 Example CLI Usage

```bash
# Basic request
$ ai-code "Create a REST API endpoint for user login"

# With specific repo
$ ai-code "Refactor the database connection pool" --repo ~/projects/myapp

# Force cloud LLM
$ ai-code "Complex architecture question" --force-cloud

# Force local LLM
$ ai-code "Simple utility function" --force-local

# Review mode (show diff only)
$ ai-code "Add error handling" --review-only
```

---

## 🔧 Key Design Decisions for Speed

| Decision | Why |
|----------|-----|
| **No LangChain** | Too much overhead for MVP, build simple wrapper |
| **SQLite not PostgreSQL** | Zero setup, file-based, good enough for logging |
| **Ollama for Local** | Easiest local LLM setup (one command install) |
| **Typer over Click** | Better type hints, auto-generated help |
| **No Docker (yet)** | Direct Python execution faster for dev |
| **Single file config** | `.env` + `config.py`, no complex YAML/JSON |
| **Synchronous I/O** | Simpler than async for MVP, can refactor later |

---

## 📊 MVP Success Metrics

- ✅ Can read git repo structure
- ✅ Sends prompt to Cloud LLM successfully
- ✅ Sends prompt to Local LLM (Ollama) successfully
- ✅ Shows generated code with syntax highlighting
- ✅ Applies changes to files after approval
- ✅ Logs all Cloud interactions to SQLite
- ✅ Complete flow in < 30 seconds per request

---

## 🚀 Next Steps After MVP Day 1

1. **Day 2-3**: Add RAG (vector search with sentence-transformers)
2. **Day 4-5**: Build training script to fine-tune local model
3. **Week 2**: Add VSCode extension
4. **Week 3**: Add web dashboard

---

## 💡 Pro Tips for 1-Day Build

1. **Start with Cloud LLM only** - get end-to-end working first
2. **Add Local LLM as second priority** - same interface, different backend
3. **Hardcode router logic initially** - e.g., "always use cloud" then refine
4. **Skip tests initially** - add pytest after core works
5. **Use Rich for all output** - makes it feel polished instantly

Ready to start coding? I can generate the complete file structure with working code!
