import time
class MockCloudLLM:
    def generate(self, prompt, context=""):
        time.sleep(1.5)
        return f"# Cloud Generated (GPT-4)\nprint('Hello from Cloud!')\n# Prompt: {prompt}"

class MockLocalLLM:
    def generate(self, prompt, context=""):
        time.sleep(0.8)
        return f"# Local Generated (Llama3)\nprint('Hello from Local!')\n# Prompt: {prompt}"
