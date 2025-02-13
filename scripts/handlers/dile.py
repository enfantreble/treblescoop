from . import BaseHandler
from typing import Dict

class DiveHandler(BaseHandler):
    def generate(self) -> Dict:
        clean_version = self.version.lstrip('v')
        current_url = f"https://github.com/{self.owner}/{self.repo}/releases/download/v{clean_version}/dive_{clean_version}_windows_amd64.zip"
        
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
                "github": f"https://github.com/{self.owner}/{self.repo}",
                "regex": "(?i)releases/tag/v?([\\d.]+)"
            },
            "autoupdate": {
                "architecture": {
                    "64bit": {
                        "url": f"https://github.com/{self.owner}/{self.repo}/releases/download/v$version/dive_$version_windows_amd64.zip"
                    }
                }
            }
        }