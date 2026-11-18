"""Assemble the static GitHub Pages site in build/pages."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "site"
OUTPUT = ROOT / "build" / "pages"


def check_lidar_cloud(cloud):
    metadata = json.loads((cloud / "metadata.json").read_text(encoding="utf-8"))
    attributes = {attribute["name"] for attribute in metadata["attributes"]}
    scale = metadata["scale"]
    # The pinned Potree-Next decoder expects equal scales and this origin.
    if (
        metadata["projection"] != "EPSG:32633"
        or metadata["points"] <= 0
        or not attributes.intersection({"rgb", "rgba"})
        or len(scale) != 3
        or scale[0] <= 0
        or len(set(scale)) != 1
        or metadata["offset"] != metadata["boundingBox"]["min"]
    ):
        raise ValueError("Chmura LiDAR ma niezgodne metadane Potree lub brak koloru RGB.")
    provenance = json.loads((cloud / "provenance.json").read_text(encoding="utf-8"))
    for name in ("metadata.json", "hierarchy.bin", "octree.bin"):
        data = (cloud / name).read_bytes()
        expected = provenance["files"][name]
        if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            raise ValueError(f"Plik chmury LiDAR {name} różni się od manifestu pochodzenia.")


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=OUTPUT.parent) as staging:
        public = Path(staging) / "pages"
        # The map generator supplies data/ and CaveView installs its own translation.
        ignore = shutil.ignore_patterns(
            "data", "lang-pl.json", "*.py", "__pycache__", ".DS_Store"
        )
        shutil.copytree(SOURCE, public, ignore=ignore)
        lidar = public / "lidar"
        check_lidar_cloud(lidar / "cloud")
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
                "--lidar-survey",
                lidar / "survey.json",
            ],
            check=True,
        )
        subprocess.run(
            [sys.executable, SOURCE / "model" / "prepare.py", public / "model"],
            check=True,
        )
        subprocess.run(
            [sys.executable, ROOT / "scripts" / "prepare_lidar_viewer.py", lidar / "vendor"],
            check=True,
        )
        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        public.rename(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
