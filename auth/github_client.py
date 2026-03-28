import os
import requests
class GitHubClient:
    def __init__(self, token):
        self.token = token
        self.headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    def get_file(self, repo, path, branch="main"):
        url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
        r = requests.get(url, headers=self.headers)
        if r.status_code == 200: return r.json()["content"] # Base64
        return None

    def push_file(self, repo, path, content, message, branch="main"):
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        data = {"message": message, "content": content, "branch": branch}
        r = requests.put(url, json=data, headers=self.headers)
        return r.status_code == 201 or r.status_code == 200
