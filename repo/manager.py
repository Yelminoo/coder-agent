import os
from git import Repo
class RepoManager:
    def __init__(self, path="."):
        self.repo = Repo(path) if os.path.exists(".git") else None
    
    def commit_and_push(self, message):
        if not self.repo: return False
        self.repo.git.add(A=True)
        self.repo.index.commit(message)
        # self.repo.remote().push() # Optional
        return True
