"""Install the verified CaveView browser runtime in the Pages build directory."""

import argparse
import hashlib
import io
from pathlib import Path
import shutil
import subprocess
import zipfile


RELEASE = (
    "https://github.com/aardgoose/CaveView.js/releases/download/2.9.0/CaveView.zip"
)
SHA256 = "63c2f45e875442c51215b156194eca7c2d55f17252286dc1ae1b31d2eea3f3fd"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("output", type=Path)
parser.add_argument("--archive", type=Path, help="Use a previously downloaded release")
args = parser.parse_args()
data = (
    args.archive.read_bytes()
    if args.archive
    else subprocess.check_output(
        [
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "--location",
            "--retry",
            "3",
            RELEASE,
        ]
    )
)
if hashlib.sha256(data).hexdigest() != SHA256:
    raise SystemExit("CaveView release checksum mismatch")

with zipfile.ZipFile(io.BytesIO(data)) as archive:
    for member in (
        "CaveView/js/CaveView2.js",
        "CaveView/js/workers/webTileWorker.js",
        "CaveView/css/caveview.css",
        "CaveView/js/assets/asset-21643d84",
    ):
        archive.extract(member, args.output)

# Resolve the survey's uppercase EPSG code locally. Upstream 2.9.0 handles
# lowercase codes by querying epsg.io, including when the viewer is self-hosted.
viewer = args.output / "CaveView/js/CaveView2.js"
source = viewer.read_text()
# GitHub Pages projects on the same domain share localStorage. Isolate the
# model from camera, layer and vertical datum settings saved by other viewers.
source = source.replace("'cv-state'", "'hagen-cv-state'")
lookup = "if ( init.toLowerCase() === 'epsg:27700' )"
if source.count(lookup) != 1:
    raise SystemExit("Unexpected CaveView CRS lookup")
viewer.write_text(
    source.replace(
        lookup,
        """if ( init.toLowerCase() === 'epsg:32633' ) {
                    sourceCRS = '+proj=utm +zone=33 +datum=WGS84 +units=m +no_defs';
                } else """
        + lookup,
    )
)
lang_directory = args.output / "CaveView/lib"
lang_directory.mkdir(exist_ok=True)
shutil.copyfile(
    Path(__file__).with_name("lang-pl.json"), lang_directory / "lang-pl.json"
)
