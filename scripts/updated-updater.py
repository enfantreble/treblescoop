from pathlib import Path
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import yaml
import subprocess
from handlers.svgo import SVGOHandler
# Import other handlers as needed

class TrebleScoopUpdater:
    def __init__(self, repo_path: Path, github_token: str):
        self.repo_path = repo_path
        self.bucket_path = repo_path / "bucket"
        self.headers = {"Authorization": f"token {github_token}"}
        self.config_path = repo_path / "scripts" / "tracked_apps.yml"
        self._ensure_config()
        self.handlers = {
            "svgo": SVGOHandler,
            # Add other handlers here
        }

    def _generate_manifest(self, repo_full_name: str, release: Dict, patterns: Dict) -> Dict:
        owner, repo = repo_full_name.split("/")
        version = release["tag_name"].lstrip("v")
        
        # Get handler for this repo
        handler_class = self.handlers.get(repo.lower())
        if handler_class:
            handler = handler_class(owner, repo, version, release)
            return handler.generate()
            
        # Default manifest for unknown repos
        return {
            "version": version,
            "description": "",
            "homepage": f"https://github.com/{repo_full_name}",
            "license": self._get_repo_license(owner, repo) or "Unknown",
            "architecture": {}
        }

    # ... rest of the methods remain the same ...
