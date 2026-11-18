"""Assemble the static GitHub Pages site in build/pages."""

from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "site"
OUTPUT = ROOT / "build" / "pages"


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=OUTPUT.parent) as staging:
        public = Path(staging) / "pages"
        # The map generator supplies data/ and CaveView installs its own translation.
        ignore = shutil.ignore_patterns(
            "data", "lang-pl.json", "*.py", "__pycache__", ".DS_Store"
        )
        shutil.copytree(SOURCE, public, ignore=ignore)
        model = public / "model" / "hagen.3d"
        subprocess.run(["cavern", "-w", "-o", model, ROOT / "hagen.svx"], check=True)
        model.with_suffix(".err").unlink(missing_ok=True)
        subprocess.run(
            [
                sys.executable,
                "-B",
                ROOT / "scripts" / "build_map_data.py",
                "--model",
                model,
                "--output",
                public / "map" / "data",
            ],
            check=True,
        )
        subprocess.run(
            [sys.executable, SOURCE / "model" / "prepare.py", public / "model"],
            check=True,
        )
        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        public.rename(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
