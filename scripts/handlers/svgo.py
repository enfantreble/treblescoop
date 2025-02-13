from . import BaseHandler
from typing import Dict

class SVGOHandler(BaseHandler):
    def generate(self) -> Dict:
        return {
            "version": self.version,
            "description": "Node.js tool for optimizing SVG files",
            "homepage": f"https://github.com/{self.owner}/{self.repo}",
            "license": "MIT",
            "depends": "nodejs",
            "bin": "svgo.cmd",
            "installer": {
                "script": [
                    "New-Item -ItemType Directory -Force -Path \"$dir\\svgo\" | Out-Null",
                    "Set-Location -Path \"$dir\\svgo\"",
                    "npm install svgo@$version",
                    "$content = @'",
                    "@echo off",
                    "node \"%~dp0svgo\\node_modules\\svgo\\bin\\svgo\" %*",
                    "'@",
                    "$content | Out-File \"$dir\\svgo.cmd\" -Encoding ASCII"
                ]
            },
            "checkver": {
                "github": f"https://github.com/{self.owner}/{self.repo}",
                "regex": "(?i)releases/tag/v?([\\d.]+)"
            },
            "autoupdate": {
                "version": "$version"
            }
        }
