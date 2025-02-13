from typing import Dict, Optional

class BaseHandler:
    def __init__(self, owner: str, repo: str, version: str, release: Dict):
        self.owner = owner
        self.repo = repo
        self.version = version
        self.release = release

    def generate(self) -> Dict:
        raise NotImplementedError("Handlers must implement generate()")
