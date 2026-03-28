# Ollama Fine-Tuning Guide 🎯

Learn how to create a custom Ollama model trained on your conversation history.

## Understanding the Difference

### 1. **Context Feeding** (Already Working ✅)
Your app **already does this automatically**! Every time you chat:
- Previous conversation turns are loaded from the database
- They're fed as context to the model via `build_contextual_prompt()`
- The model "remembers" your conversation within that chat session

**Location in code:** `web_server.py` line 57-68

```python
def build_contextual_prompt(current_prompt: str, turns: list[dict[str, str]]) -> str:
    if not turns:
        return current_prompt

    transcript = []
    for turn in turns:
        transcript.append(f"User: {turn.get('user', '')}")
        transcript.append(f"Assistant: {turn.get('assistant', '')}")

    history_block = "\n".join(transcript)
    return f"Conversation so far:\n{history_block}\n\nCurrent user message:\n{current_prompt}"
```

### 2. **Fine-Tuning** (Custom Model Training 🚀)
This creates a **new model** permanently trained on your conversations:
- Creates a model that inherently "knows" your patterns
- Doesn't need context fed each time
- Better for domain-specific knowledge
- Requires more setup

---

## How to Export & Fine-Tune

### Step 1: Export Your Conversations 📥

1. Open your AI Coding Assistant at http://localhost:8000
2. Look for the **"🗄️ DB Status & Export"** section
3. Click the **"📥 Export for Training"** button
4. Download the `ollama-training-XXXXX.jsonl` file

**Alternative:** Use API directly:
```bash
curl http://localhost:8000/api/chats/export/jsonl -o training_data.jsonl
```

---

### Step 2: Create a Modelfile 📝

Create a file named `Modelfile` in your project directory:

```dockerfile
# Base model to fine-tune from
FROM llama3.2:latest

# System prompt for your custom model
SYSTEM """
You are an AI coding assistant trained on specific user conversations.
You help with Python development, code generation, and technical questions.
"""

# Training parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

# Optional: Add your training data
# Note: Ollama uses adapters, not full retraining
ADAPTER ./training_data.jsonl
```

---

### Step 3: Create Your Custom Model 🤖

Run this command in your terminal:

```bash
# Create a new model from your Modelfile
ollama create my-custom-assistant -f Modelfile

# Verify it was created
ollama list
```

You should see your new model: `my-custom-assistant:latest`

---

### Step 4: Use Your Custom Model ⚙️

**Option A: Update your `.env` file**
```env
OLLAMA_MODEL=my-custom-assistant:latest
```

**Option B: Test it directly**
```bash
ollama run my-custom-assistant
```

**Option C: Use Ollama's create command with training**
```bash
# For more advanced fine-tuning with LoRA adapters
ollama create my-assistant --from llama3.2 --training training_data.jsonl
```

---

## Advanced: True Fine-Tuning with LoRA

For actual model weight updates (requires more resources):

### 1. Convert JSONL to Training Format

Create a Python script `prepare_training.py`:

```python
import json

def convert_to_ollama_format(input_file, output_file):
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            data = json.loads(line)
            formatted = {
                "instruction": data["prompt"],
                "output": data["response"]
            }
            f_out.write(json.dumps(formatted) + '\\n')

convert_to_ollama_format('training_data.jsonl', 'formatted_training.jsonl')
```

### 2. Fine-Tune with Ollama

```bash
# Fine-tune with LoRA (Low-Rank Adaptation)
ollama create my-fine-tuned-model \\
  --from llama3.2:latest \\
  --training formatted_training.jsonl \\
  --epochs 3 \\
  --batch-size 4
```

---

## Best Practices 📚

### Data Quality
- ✅ **Export regularly** - More data = better training
- ✅ **Clean data** - Remove test/gibberish conversations
- ✅ **Diverse topics** - Cover various use cases
- ❌ **Avoid sensitive data** - Don't include passwords/keys

### Model Selection
- `llama3.2:latest` (2GB) - Fast, good for most tasks
- `llama3:8b` (4.7GB) - Better reasoning
- `codellama:latest` (7B) - Specialized for coding

### Training Parameters
```dockerfile
PARAMETER temperature 0.7      # Creativity (0.1-1.0)
PARAMETER top_p 0.9           # Diversity
PARAMETER num_ctx 4096        # Context window size
PARAMETER repeat_penalty 1.1  # Avoid repetition
```

---

## Monitoring Your Training

Check if your custom model is working:

```bash
# Ask a question that was in your training data
ollama run my-custom-assistant "What patterns do I usually ask about?"

# Compare with base model
ollama run llama3.2 "What patterns do I usually ask about?"
```

---

## Current App Configuration 🔧

Your app automatically:
1. ✅ Stores all conversations in SQLite (`data/chat_sessions.db`)
2. ✅ Feeds recent conversation history as context (last 200 turns)
3. ✅ Tracks which agent was used per chat
4. ✅ Timestamps every message

**To check your data:**
```bash
# View your SQLite database
sqlite3 data/chat_sessions.db "SELECT COUNT(*) FROM messages;"
sqlite3 data/chat_sessions.db "SELECT * FROM messages LIMIT 5;"
```

---

## Troubleshooting 🔧

### "Export failed"
- Ensure you're using SQLite backend (not JSON)
- Check `.env`: `CHAT_STORE_BACKEND=sqlite`

### "Model creation failed"
- Verify Ollama is running: `ollama list`
- Check Modelfile syntax
- Ensure training file exists and is valid JSONL

### "Model doesn't use my training"
- Ollama's ADAPTER directive is for model extensions
- For true fine-tuning, use external tools like `llama.cpp` or `Unsloth`
- Consider context feeding (already working!) for most use cases

---

## When to Use Each Approach

### Use Context Feeding (Current) When:
- ✅ You want immediate conversation memory
- ✅ You're testing/iterating quickly
- ✅ Your use case changes frequently
- ✅ You have < 1000 conversations

### Use Fine-Tuning When:
- 🚀 You have 10,000+ quality conversations
- 🚀 Your domain is highly specialized
- 🚀 You need consistent behavior across all new chats
- 🚀 You want lower latency (no context overhead)

---

## Resources 📖

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)
- [Modelfile Reference](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)
- [Fine-tuning LLMs Guide](https://github.com/ollama/ollama/blob/main/docs/faq.md#how-can-i-fine-tune-a-model)

---

**Your conversation memory is already working!** 🎉  
The export feature is for creating custom models if you need advanced training.
