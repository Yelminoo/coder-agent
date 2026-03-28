import os
import time
from dotenv import load_dotenv
from llm.metrics import record_ollama_response_time
load_dotenv()

class MultiProviderLLM:
    def __init__(self):
        self.mode = os.getenv("LLM_MODE", "AUTO")
        self.provider = self._detect_provider()
        
    def _detect_provider(self):
        if self.mode == "LOCAL_ONLY": return "ollama"
        if os.getenv("OPENAI_API_KEY"): return "openai"
        if os.getenv("ANTHROPIC_API_KEY"): return "anthropic"
        if os.getenv("GOOGLE_API_KEY"): return "google"
        if os.getenv("GROQ_API_KEY"): return "groq"
        return "ollama" # Fallback

    def _generate_ollama(self, prompt, system_prompt):
        import requests
        import json
        start_time = time.time()
        try:
            resp = requests.post(
                f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/generate",
                json={"model": os.getenv("OLLAMA_MODEL", "llama3"), "prompt": prompt, "system": system_prompt},
                timeout=120
            )
            resp.raise_for_status()
            lines = resp.text.split('\n')
            full_response = ""
            for line in lines:
                if line.strip():
                    data = json.loads(line)
                    full_response += data.get("response", "")
            
            # Record response time
            elapsed = time.time() - start_time
            record_ollama_response_time(elapsed)
            print(f"\u23f1\ufe0f Ollama response time: {elapsed:.2f}s")
            
            return full_response
        except Exception as e:
            return f"# Error connecting to Ollama: {str(e)}\n# Make sure 'ollama serve' is running."

    def generate(self, prompt, system_prompt="You are an expert Python developer."):
        print(f"🤖 Using Provider: {self.provider.upper()}")
        
        if self.provider == "openai":
            try:
                from openai import OpenAI
                client = OpenAI()
                resp = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
                )
                return resp.choices[0].message.content
            except Exception as e:
                print(f"⚠️ OpenAI failed, falling back to Ollama: {e}")
                return self._generate_ollama(prompt, system_prompt)
            
        elif self.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic()
            resp = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620"),
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.content[0].text
            
        elif self.provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel(os.getenv("GOOGLE_MODEL", "gemini-pro"))
            resp = model.generate_content(system_prompt + "\n\n" + prompt)
            return resp.text
            
        elif self.provider == "groq":
            from openai import OpenAI # Groq uses OpenAI compatible client
            client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
            resp = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
            )
            return resp.choices[0].message.content
            
        else: # Ollama (Local)
            return self._generate_ollama(prompt, system_prompt)

# Simple Router Logic
def should_use_local(prompt):
    # Short prompts or specific keywords go local
    if len(prompt) < 15: return True
    if "simple" in prompt.lower() or "hello" in prompt.lower(): return True
    return False
