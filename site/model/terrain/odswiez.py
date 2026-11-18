"""Resample the BEV 1 m source at the vertices of the four CaveView z16 tiles."""

import argparse
from array import array
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


SOURCE = (
    "/vsicurl/https://data.bev.gv.at/download/ALS/DTM/20240915/"
    "ALS_DTM_CRS3035RES50000mN2700000E4550000.tif"
)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "raster", nargs="?", default=SOURCE, help="Local BEV GeoTIFF or GDAL URL"
)
args = parser.parse_args()

z, x0, y0 = 16, 35158, 22911
divisions = 256
span = math.pi * 6378137
width = 2 * span / (2**z)
step = width / divisions
west = x0 * width - span
north = span - y0 * width
size = 2 * divisions + 1
# GDAL extents describe pixel edges. The first and last samples must fall
# exactly on tile vertices so adjacent CaveView meshes share their edges.
extent = (
    west - step / 2,
    north - 2 * width - step / 2,
    west + 2 * width + step / 2,
    north + step / 2,
)
with tempfile.TemporaryDirectory() as tmp:
    raw = Path(tmp) / "samples.bin"
    subprocess.run(
        [
            "gdalwarp",
            "-q",
            "-s_srs",
            "EPSG:3035",
            "-t_srs",
            "EPSG:3857",
            "-novshift",
            "-r",
            "bilinear",
            "-ovr",
            "NONE",
            "-et",
            "0",
            "-dstnodata",
            "-9999",
            "-te",
            *map(str, extent),
            "-ts",
            str(size),
            str(size),
            "-of",
            "ENVI",
            "-ot",
            "Float32",
            args.raster,
            str(raw),
        ],
        check=True,
    )
    values = array("f")
    values.frombytes(raw.read_bytes())
    header = raw.with_suffix(".hdr").read_text()
    file_little_endian = "byte order = 0" in header
    if file_little_endian != (sys.byteorder == "little"):
        values.byteswap()

if len(values) != size * size or not all(0 <= h < 4096 for h in values):
    raise ValueError("Incomplete elevation coverage or height out of uint16/16 range")

out = Path(__file__).parent / "dtm" / str(z)
out.mkdir(exist_ok=True, parents=True)
for dy in range(2):
    for dx in range(2):
        tile = bytearray()
        for row in range(divisions + 1):
            start = (dy * divisions + row) * size + dx * divisions
            samples = values[start : start + divisions + 1]
            tile.extend(struct.pack("<257H", *(round(h * 16) for h in samples)))
        (out / f"DTM-{x0 + dx}-{y0 + dy}.bin").write_bytes(tile)
