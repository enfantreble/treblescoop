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

    def _find_matching_asset(self, assets: List[Dict], pattern: str) -> Optional[Dict]:
        for asset in assets:
            if pattern.lower() in asset["name"].lower():
                return asset
        return None

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

    def _generate_manifest(self, repo_full_name: str, release: Dict, patterns: Dict) -> Dict:
        owner, repo = repo_full_name.split("/")
        version = release["tag_name"].lstrip("v")
        
        # Get first line of description and clean it
        description = release.get("body", "").split("\n")[0]
        if description.startswith(">"):
            description = description[1:].strip()

        # Base manifest structure
        manifest = {
            "version": version,
            "description": description or f"{repo} - A GitHub release",
            "homepage": f"https://github.com/{repo_full_name}",
            "license": self._get_repo_license(owner, repo) or "Unknown",
            "notes": "",
            "architecture": {},
            "pre_install": "",
            "installer": {
                "script": ""
            },
            "post_install": [""],
            "uninstaller": {
                "script": ""
            },
            "bin": ["chatbox.exe"],
            "env_add_path": [""],
            "persist": [""],
            "checkver": {
                "github": f"https://github.com/{repo_full_name}",
                "regex": "(?i)releases/tag/v?([\\d.]+)"
            },
            "autoupdate": {
                "architecture": {
                    "64bit": {
                        "url": f"https://github.com/{repo_full_name}/releases/download/v$version/{repo.lower()}-$version-windows-x64.exe"
                    }
                }
            }
        }

        # Current version URL and hash
        exe_name = f"{repo.lower()}-{version}-windows-x64.exe"
        current_url = f"https://github.com/{repo_full_name}/releases/download/v{version}/{exe_name}"
        
        manifest["architecture"]["64bit"] = {
            "url": current_url,
            "hash": self._get_file_hash(current_url)
        }

        return manifest

        version = release["tag_name"].lstrip("v")
        
        # Get first line of description and clean it
        description = release.get("body", "").split("\n")[0]
        if description.startswith(">"):
            description = description[1:].strip()

        # Base manifest structure
        manifest = {
            "version": version,
            "description": description or f"{repo} - A GitHub release",
            "homepage": f"https://github.com/{repo_full_name}",
            "license": self._get_repo_license(owner, repo) or "Unknown",
            "notes": "",
            "architecture": {},
            "pre_install": "",
            "installer": {
                "script": ""
            },
            "post_install": [""],
            "uninstaller": {
                "script": ""
            },
            "bin": ["chatbox.exe"],
            "env_add_path": [""],
            "persist": [""],
            "checkver": {
                "github": f"https://github.com/{repo_full_name}",
                "regex": "(?i)releases/tag/v?([\\d.]+)"
            },
            "autoupdate": {
                "architecture": {
                    "64bit": {
                        "url": f"https://github.com/{repo_full_name}/releases/download/v$version/{repo.lower()}-$version-windows-x64.exe"
                    }
                }
            }
        }

        # Current version URL and hash
        exe_name = f"{repo.lower()}-{version}-windows-x64.exe"
        current_url = f"https://github.com/{repo_full_name}/releases/download/v{version}/{exe_name}"
        
        manifest["architecture"]["64bit"] = {
            "url": current_url,
            "hash": self._get_file_hash(current_url)
        }

        return manifest
        
        owner, repo = repo_full_name.split("/")
        
        # Get first line of description without '>'
        description = release.get("body", "").split("\n")[0]
        if description.startswith(">"):
            description = description[1:].strip()

        manifest = {
            "version": release["tag_name"].lstrip("v"),
            "description": description or f"{repo} - A GitHub release",
            "homepage": f"https://github.com/{repo_full_name}",
            "license": self._get_repo_license(owner, repo) or "Unknown",
            "notes": "",
            "architecture": {},
            "pre_install": "",
            "installer": {
                "script": ""
            },
            "post_install": [""],
            "uninstaller": {
                "script": ""
            },
            "bin": "",
            "env_add_path": [""],
            "persist": [""],
            "checkver": {
                "github": f"https://github.com/{repo_full_name}",
                "regex": "(?i)releases/tag/v?([\\d.]+)"
            },
            "autoupdate": {
                "architecture": {
                    "64bit": {
                        "url": f"https://github.com/{repo_full_name}/releases/download/v$version/{repo.lower()}-$version-windows-x64.exe"
                    }
                }
            }
        }
        for arch, pattern in patterns.items():
            print(f"Looking for {pattern} in release assets")
            asset = self._find_matching_asset(release["assets"], pattern)
            if asset:
                print(f"Found asset: {asset['name']}")
                url = asset["browser_download_url"]
                manifest["architecture"][arch] = {
                    "url": url,
                    "hash": self._get_file_hash(url)
                }
            else:
                print(f"No matching asset found for pattern: {pattern}")

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