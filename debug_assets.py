import sys
from pathlib import Path
import requests

token = Path.home().joinpath(".github_token").read_text().strip()
headers = {"Authorization": f"token {token}"}

print("Fetching latest release info...")
response = requests.get(
    "https://api.github.com/repos/Bin-Huang/chatbox/releases/latest",
    headers=headers
)

if response.status_code == 200:
    release = response.json()
    print(f"\nLatest version: {release['tag_name']}")
    print("\nAvailable assets:")
    for asset in release['assets']:
        print(f"- {asset['name']}")
        print(f"  URL: {asset['browser_download_url']}")
else:
    print(f"Error fetching release: {response.status_code}")
    print(response.text)