import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.treble_scoop_updater import TrebleScoopUpdater

repo_path = Path(__file__).parent.parent.parent
token = Path.home().joinpath(".github_token").read_text().strip()
updater = TrebleScoopUpdater(repo_path, token)

# Track SVGO
updater.track_app("svg", "svgo", {
    "64bit": "npm"
})

print("Starting manifest update...")
updater.update_manifests()
