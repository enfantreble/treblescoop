import sys
from pathlib import Path
# Add scripts directory to Python path
sys.path.append(str(Path.cwd() / "scripts"))
from treble_scoop_updater import TrebleScoopUpdater
# Get current directory
repo_path = Path.cwd()
# Read token
token = Path.home().joinpath(".github_token").read_text().strip()
# Initialize updater
updater = TrebleScoopUpdater(repo_path, token)
# Test with a specific app - let's try something smaller first
updater.track_app("OpenVPN", "openvpn-build", {
    "64bit": "win10-amd64",
})
# Run the update
print("Starting manifest update...")
updater.update_manifests()