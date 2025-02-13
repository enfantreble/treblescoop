import sys
from pathlib import Path
sys.path.append(str(Path.cwd() / "scripts"))
from treble_scoop_updater import TrebleScoopUpdater

repo_path = Path.cwd()
token = Path.home().joinpath(".github_token").read_text().strip()
updater = TrebleScoopUpdater(repo_path, token)

# Dive uses patterns like: dive_0.9.2_windows_amd64.zip
updater.track_app("wagoodman", "dive", {
    "64bit": "windows_amd64.zip"
})

print("Starting manifest update...")
updater.update_manifests()