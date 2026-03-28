import time
class MockGitHubClient:
    def __init__(self): self.authenticated = False
    def login(self):
        print("🌐 Simulating OAuth..."); time.sleep(1); self.authenticated = True; return True
    def push_file(self, path, content, msg):
        if not self.authenticated: raise Exception("Not Authenticated")
        print(f"📤 Pushing {path}..."); time.sleep(1); return True
