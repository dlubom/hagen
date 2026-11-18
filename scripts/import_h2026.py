"""Export the cave centrelines from a local checkout of dlubom/test2, branch h2026."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def survey_names(source):
    names = {}
    for master in source.glob("*/*-master.svx"):
        code = master.name.removesuffix("-master.svx")
        main = next(
            (
                path
                for path in master.parent.glob("*.svx")
                if path.stem.lower() == code.lower()
            ),
            None,
        )
        if main is None:
            continue  # The joint 495–581 master contains the two individual surveys.
        # The 495 project has its catalogue entry in the entrance survey. The 570
        # wrapper repeats the metadata of cave 569, but the field survey identifies FK-13.
        metadata = {
            "495": main.parent / "20080801-Ciag_wejsciowy1/C_WEJ_1.svx",
            "570": main.parent / "20200801-FK13/fk13.svx",
        }.get(code, main)
        header = metadata.read_bytes().partition(b"*")[0]
        try:
            header = header.decode("utf-8")
        except UnicodeDecodeError:
            header = header.decode("cp1250")
        key = re.search(rb"^\*begin[ \t]+(\S+)", main.read_bytes(), re.I | re.M)[
            1
        ].decode()
        labels = re.findall(r'^;cavern name (?:pl|de)\s+"([^"]+)"', header, re.M | re.I)
        labels = list(dict.fromkeys(label.replace("_", " ") for label in labels))
        if not labels and key != code:
            labels = [key.removeprefix(code + "-").replace("_", " ")]
        if code.isdecimal():
            labels.insert(0, f"1335/{int(code)}")
        names[key] = " · ".join(labels) or key.replace("_", " ")
    return names


def centrelines(model):
    surveys = defaultdict(list)
    current = None
    previous = None
    dump = subprocess.check_output(["dump3d", model], text=True)
    if "CS EPSG:32633" not in dump.splitlines()[:8]:
        raise ValueError("Expected a model in WGS 84 / UTM zone 33N.")
    for row in dump.splitlines():
        fields = row.split()
        if fields[:1] == ["MOVE"]:
            current = None
            previous = tuple(fields[1:3])
        elif fields[:1] == ["LINE"]:
            survey = fields[4].strip("[]").split(".")[0]
            point = tuple(fields[1:3])
            # 484N.svx calls its only shot fictitious. _BAZA draws a camp symbol.
            if survey in {"484-Neuhauserschacht", "_BAZA"} or {
                "SPLAY",
                "DUPLICATE",
                "SURFACE",
                "STYLE=NOSURVEY",
            }.intersection(fields[5:]):
                current = None
            else:
                if current != survey:
                    surveys[survey].append([previous])
                surveys[survey][-1].append(point)
                current = survey
            previous = point
    return surveys


def export(source, output):
    revision = subprocess.check_output(
        ["git", "-C", source, "rev-parse", "HEAD"], text=True
    ).strip()
    subprocess.run(
        ["git", "-C", source, "diff", "--quiet", "HEAD", "--", "*.svx"], check=True
    )
    with tempfile.TemporaryDirectory() as tmp:
        model = Path(tmp) / "hagen.3d"
        subprocess.run(["cavern", "-o", model, source / "Hagengebirge.svx"], check=True)
        surveys = centrelines(model)
    names = survey_names(source)
    points = dict.fromkeys(
        p for paths in surveys.values() for path in paths for p in path
    )
    rows = subprocess.check_output(
        ["cs2cs", "EPSG:32633", "OGC:CRS84", "-f", "%.8f"],
        input="".join(" ".join(p) + "\n" for p in points),
        text=True,
    ).splitlines()
    if len(points) != len(rows):
        raise ValueError("Incomplete coordinate transformation.")
    wgs84 = {p: list(map(float, row.split()[:2])) for p, row in zip(points, rows)}
    features = []
    for survey, paths in sorted(surveys.items()):
        features.append(
            {
                "type": "Feature",
                "id": survey,
                "properties": {
                    "name": names[survey],
                    "legs": sum(len(path) - 1 for path in paths),
                },
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [[wgs84[p] for p in path] for path in paths],
                },
            }
        )
    collection = {
        "type": "FeatureCollection",
        "source": "https://github.com/dlubom/test2/tree/" + revision,
        "features": features,
    }
    output.write_text(
        json.dumps(
            collection, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source", type=Path, help="Local checkout containing Hagengebirge.svx"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "mapa/zrodla/h2026.geojson"
    )
    args = parser.parse_args()
    export(args.source.resolve(), args.output)
