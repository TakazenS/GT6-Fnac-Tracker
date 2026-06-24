"""Build a distributable zip of GTA 6 Tracker.

Creates GTA6-Tracker.zip containing only the files an end user needs.
Used both locally and by the GitHub Actions release workflow.

    py build_zip.py
"""

import zipfile
from pathlib import Path

# Files shipped to end users (everything else stays out of the zip).
FILES = [
    "gta6_tracker.py",
    "requirements.txt",
    "README.md",
    ".env.example",
    "Installer.bat",
    "Start.bat",
    "Uninstaller.bat",
    "LICENSE",
]

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "GTA6-Tracker.zip"


def main() -> None:
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            path = ROOT / name
            if not path.exists():
                print(f"[!] Missing, skipped: {name}")
                continue
            # Store everything inside a top-level "GTA6-Tracker/" folder so it
            # extracts cleanly.
            archive.write(path, f"GTA6-Tracker/{name}")
            print(f"  + {name}")
    print(f"\nCreated {OUTPUT}")


if __name__ == "__main__":
    main()
