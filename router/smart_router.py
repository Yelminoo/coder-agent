class SmartRouter:
    @staticmethod
    def should_use_cloud(prompt):
        # Simple logic: Long prompts or complex keywords go to cloud
        complex_keywords = ["refactor", "architecture", "optimize", "security"]
        if any(k in prompt.lower() for k in complex_keywords): return True
        return len(prompt) > 50
