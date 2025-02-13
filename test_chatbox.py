import sys
from pathlib import Path
sys.path.append(str(Path.cwd() / "scripts"))
from treble_scoop_updater import TrebleScoopUpdater

repo_path = Path.cwd()
token = Path.home().joinpath(".github_token").read_text().strip()
updater = TrebleScoopUpdater(repo_path, token)

# Let's use their exact release pattern for Windows
updater.track_app("Bin-Huang", "chatbox", {
    "64bit": "-windows-x64.exe"  # More general pattern to match any version
})

print("Starting manifest update...")
updater.update_manifests()