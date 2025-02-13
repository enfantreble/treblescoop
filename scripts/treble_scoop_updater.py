from pathlib import Path
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import tempfile
import subprocess
import yaml
import os
class TrebleScoopUpdater:
    def __init__(self, repo_path: Path, github_token: str):
        self.repo_path = repo_path
        self.bucket_path = repo_path / "bucket"
        self.headers = {"Authorization": f"token {github_token}"}
        self.config_path = repo_path / "scripts" / "tracked_apps.yml"
        self._ensure_config()
    def _ensure_config(self) -> None:
        if not self.config_path.parent.exists():
            self.config_path.parent.mkdir(parents=True)
        if not self.config_path.exists():
            self.config_path.write_text(yaml.dump({"apps": {}}))
    def track_app(self, owner: str, repo: str, patterns: Dict[str, str]) -> None:
        config = yaml.safe_load(self.config_path.read_text())
        config["apps"] = config.get("apps", {})
        config["apps"][f"{owner}/{repo}"] = {
            "patterns": patterns,
            "last_checked": None
        }
        self.config_path.write_text(yaml.dump(config))
    def _get_latest_release(self, owner: str, repo: str) -> Optional[Dict]:
        resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}/releases/latest", headers=self.headers)
        return resp.json() if resp.status_code == 200 else None
    def _get_file_hash(self, url: str) -> str:
        print(f"Downloading and hashing: {url}")
        response = requests.get(url, stream=True)
        sha256_hash = hashlib.sha256()
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    def _find_matching_asset(self, assets: List[Dict], pattern: str) -> Optional[Dict]:
        for asset in assets:
            if pattern.lower() in asset["name"].lower():
                return asset
        return None
    def update_manifests(self) -> None:
        if not self.config_path.exists():
            print(f"No config file found at {self.config_path}")
            return
        config = yaml.safe_load(self.config_path.read_text())
        if not config or "apps" not in config:
            print("No apps configured in tracking file")
            return
        for repo_full_name, info in config["apps"].items():
            print(f"Checking {repo_full_name}")
            owner, repo = repo_full_name.split("/")
            release = self._get_latest_release(owner, repo)
            if not release:
                print(f"No release found for {repo_full_name}")
                continue
            manifest = {
                "version": release["tag_name"].lstrip("v"),
                "description": f"Automatic update from {repo_full_name}",
                "homepage": f"https://github.com/{repo_full_name}",
                "license": "Unknown",
                "architecture": {}
            }
            for arch, pattern in info["patterns"].items():
                asset = self._find_matching_asset(release["assets"], pattern)
                if asset:
                    print(f"Found matching asset for {arch}: {asset['name']}")
                    manifest["architecture"][arch] = {
                        "url": asset["browser_download_url"],
                        "hash": self._get_file_hash(asset["browser_download_url"])
                    }
            if manifest["architecture"]:
                manifest_path = self.bucket_path / f"{repo}.json"
                manifest_path.write_text(json.dumps(manifest, indent=4))
                info["last_checked"] = release["published_at"]
                print(f"Updated manifest for {repo}")
            else:
                print(f"No matching assets found for {repo}")
        self.config_path.write_text(yaml.dump(config))
        self._commit_changes()
    def _get_current_branch(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "master"  # fallback to master if command fails
    def _commit_changes(self) -> None:
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if status.stdout.strip():
                # Add files
                subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True)
                
                # Commit changes
                subprocess.run(
                    ["git", "commit", "-m", f"Updated manifests {datetime.now().isoformat()}"],
                    cwd=self.repo_path,
                    check=True
                )
                
                # Get current branch
                branch = self._get_current_branch()
                print(f"Pushing to branch: {branch}")
                
                # Push to the current branch
                subprocess.run(
                    ["git", "push", "origin", branch],
                    cwd=self.repo_path,
                    check=True
                )
                print("Changes committed and pushed successfully")
            else:
                print("No changes to commit")
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            print(f"Command output: {e.output if hasattr(e, 'output') else 'No output'}")
        except Exception as e:
            print(f"Error during git operations: {e}")