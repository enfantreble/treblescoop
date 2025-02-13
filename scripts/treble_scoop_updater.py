from pathlib import Path
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import yaml
import subprocess

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

    def _get_repo_license(self, owner: str, repo: str) -> Optional[str]:
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=self.headers
            )
            if resp.status_code == 200:
                return resp.json().get("license", {}).get("spdx_id")
        except:
            pass
        return None

    def _handle_dive(self, owner: str, repo: str, version: str, release: Dict) -> Dict:
        clean_version = version.lstrip('v')
        current_url = f"https://github.com/{owner}/{repo}/releases/download/v{clean_version}/dive_{clean_version}_windows_amd64.zip"
        
        return {
            "description": "A tool for exploring a docker image, layer contents, and discovering ways to shrink the size of your Docker/OCI image",
            "bin": "dive.exe",
            "architecture": {
                "64bit": {
                    "url": current_url,
                    "hash": self._get_file_hash(current_url)
                }
            },
            "checkver": {
                "github": f"https://github.com/{owner}/{repo}",
                "regex": "(?i)releases/tag/v?([\\d.]+)"
            },
            "autoupdate": {
                "architecture": {
                    "64bit": {
                        "url": f"https://github.com/{owner}/{repo}/releases/download/v$version/dive_$version_windows_amd64.zip"
                    }
                }
            }
        }

    def _handle_chatbox(self, owner: str, repo: str, version: str, release: Dict) -> Dict:
        current_url = f"https://github.com/{owner}/{repo}/releases/download/v{version}/Chatbox.CE-{version}-Setup.exe#/dl.exe"
        
        return {
            "description": release.get("body", "").split("\n")[0].lstrip("> ").strip(),
            "bin": [["Chatbox CE\\Chatbox CE.exe", "chatbox"]],
            "shortcuts": [["Chatbox CE\\Chatbox CE.exe", "Chatbox CE"]],
            "architecture": {
                "64bit": {
                    "url": current_url,
                    "hash": self._get_file_hash(current_url.split('#')[0]),
                    "installer": {
                        "script": "Start-Process -Wait \"$dir\\dl.exe\" -ArgumentList \"/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /DIR=`\"$dir\\Chatbox CE`\"\"" 
                    }
                }
            },
            "checkver": {
                "github": f"https://github.com/{owner}/{repo}",
                "regex": "(?i)releases/tag/v?([\\d.]+)"
            },
            "autoupdate": {
                "architecture": {
                    "64bit": {
                        "url": f"https://github.com/{owner}/{repo}/releases/download/v$version/Chatbox.CE-$version-Setup.exe#/dl.exe"
                    }
                }
            }
        }

    def _generate_manifest(self, repo_full_name: str, release: Dict, patterns: Dict) -> Dict:
        owner, repo = repo_full_name.split("/")
        version = release["tag_name"].lstrip("v")
        
        manifest = {
            "version": version,
            "description": "",
            "homepage": f"https://github.com/{repo_full_name}",
            "license": self._get_repo_license(owner, repo) or "Unknown",
            "architecture": {}
        }

        if repo.lower() == "dive":
            manifest.update(self._handle_dive(owner, repo, version, release))
        elif repo.lower() == "chatbox":
            manifest.update(self._handle_chatbox(owner, repo, version, release))
        
        return manifest

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
                
            manifest = self._generate_manifest(repo_full_name, release, info["patterns"])
            manifest_path = self.bucket_path / f"{repo}.json"
            manifest_path.write_text(json.dumps(manifest, indent=4))
            info["last_checked"] = release["published_at"]
            print(f"Updated manifest for {repo}")

        self.config_path.write_text(yaml.dump(config))
        self._commit_changes()

    def _commit_changes(self) -> None:
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if status.stdout.strip():
                subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True)
                subprocess.run(
                    ["git", "commit", "-m", f"Updated manifests {datetime.now().isoformat()}"],
                    cwd=self.repo_path,
                    check=True
                )
                branch = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                ).stdout.strip()
                print(f"Pushing to branch: {branch}")
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