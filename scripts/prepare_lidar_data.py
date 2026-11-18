"""Prepare the Kälbergruben-Windloch Potree cloud with colours from basemap.at.

Requires Python 3.11+, laspy[lazrs], NumPy, Pillow, pyproj and PotreeConverter
2.1.5 (c2cb61843bf2b901e8e257874b1a6dcf67792fb2). Pass the official
4427453_dgm_op_1_m.laz source as the first argument.
"""

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from urllib.request import urlopen

import laspy
import numpy as np
from PIL import Image
from pyproj import CRS, Transformer


ROOT = Path(__file__).resolve().parents[1]
SAGIS_SOURCE = (
    "https://service.salzburg.gv.at/sagisogd/archiv/raster/hoehen/laserscan/"
    "Originalpunkte/ungefiltert/DGM/4427453_dgm_op_1_m.laz"
)
SAGIS_SHA256 = "313ca9eec63989d1f7cb2e73f52b70ba8cbf7ce57015023b43d2ef895bd1fec8"
SAGIS_CRS = "EPSG:31258"
OUTPUT_CRS = "EPSG:32633"
CONVERTER_COMMIT = "c2cb61843bf2b901e8e257874b1a6dcf67792fb2"
WMTS = "https://mapsneu.wien.gv.at/basemap/bmaporthofoto30cm/normal/google3857"
WMTS_ZOOM = 19
TILE_SIZE = 256
MERCATOR_HALF_WIDTH = 20037508.342789244
OUTPUT_FILES = ("metadata.json", "hierarchy.bin", "octree.bin")


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def sample_orthophoto(east, north, cache):
    """Read the pixel containing each XY point in the Web Mercator tile grid."""
    matrix_width = 1 << WMTS_ZOOM
    pixels = TILE_SIZE * matrix_width
    pixels_per_metre = pixels / (2 * MERCATOR_HALF_WIDTH)
    column = np.floor((east + MERCATOR_HALF_WIDTH) * pixels_per_metre).astype(np.int64)
    row = np.floor((MERCATOR_HALF_WIDTH - north) * pixels_per_metre).astype(np.int64)
    tile_x, pixel_x = np.divmod(column, TILE_SIZE)
    tile_y, pixel_y = np.divmod(row, TILE_SIZE)
    tile_ids = tile_y * matrix_width + tile_x
    point_order = np.argsort(tile_ids)
    used_tiles, starts = np.unique(tile_ids[point_order], return_index=True)
    colours = np.empty((len(east), 3), dtype=np.uint8)
    checksums = {}
    cache.mkdir(parents=True, exist_ok=True)
    for tile_id, indices in zip(used_tiles, np.split(point_order, starts[1:])):
        y, x = divmod(int(tile_id), matrix_width)
        path = cache / f"{x}-{y}.jpeg"
        cached = path.is_file()
        if cached:
            data = path.read_bytes()
        else:
            with urlopen(f"{WMTS}/{WMTS_ZOOM}/{y}/{x}.jpeg", timeout=30) as response:
                data = response.read()
        with Image.open(BytesIO(data)) as image:
            if image.size != (TILE_SIZE, TILE_SIZE):
                raise ValueError(f"Unexpected orthophoto tile size for {x}/{y}")
            colours[indices] = np.asarray(image.convert("RGB"))[
                pixel_y[indices], pixel_x[indices]
            ]
        if not cached:
            with TemporaryDirectory(prefix=".tile-", dir=cache) as directory:
                pending = Path(directory) / path.name
                pending.write_bytes(data)
                pending.replace(path)
        checksums[f"{WMTS_ZOOM}/{y}/{x}"] = hashlib.sha256(data).hexdigest()
    return colours, checksums


def prepare(source, cache, converter, output):
    if sha256(source) != SAGIS_SHA256:
        raise ValueError(
            "The input checksum does not match the SAGIS tile 4427453, epoch 1 DGM"
        )
    ground = laspy.read(source)
    if ground.header.parse_crs().to_epsg() != 31258 or not np.all(
        ground.classification == 2
    ):
        raise ValueError("Expected SAGIS ground returns in EPSG:31258")
    web = Transformer.from_crs(SAGIS_CRS, "EPSG:3857", always_xy=True)
    utm = Transformer.from_crs(SAGIS_CRS, OUTPUT_CRS, always_xy=True)
    e, n = web.transform(ground.x, ground.y, errcheck=True)
    colours, ortho_checksums = sample_orthophoto(e, n, cache)
    east, north = utm.transform(ground.x, ground.y, errcheck=True)
    elevation = np.asarray(ground.z)
    scale = 0.001
    header = laspy.LasHeader(point_format=2, version="1.2")
    header.scales = np.full(3, scale)
    header.offsets = np.floor(np.array([east.min(), north.min(), elevation.min()]))
    header.add_crs(CRS.from_user_input(OUTPUT_CRS))
    cloud = laspy.LasData(header)
    cloud.x, cloud.y, cloud.z = east, north, elevation
    cloud.classification = np.asarray(ground.classification)
    rgb = colours.astype(np.uint16) * 257
    cloud.red, cloud.green, cloud.blue = rgb.T

    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".prepare-lidar-", dir=output.parent) as temp:
        staging = Path(temp)
        las = staging / "kalbergruben-windloch.las"
        cloud.write(las)
        octree = staging / "cloud"
        subprocess.run(
            [
                str(converter.resolve()),
                str(las),
                "-o",
                str(octree),
                "--encoding",
                "DEFAULT",
                "--method",
                "poisson",
                "--projection",
                OUTPUT_CRS,
                "--attributes",
                "rgb",
            ],
            check=True,
        )
        metadata_path = octree / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            metadata["points"] != len(ground)
            or metadata["projection"] != OUTPUT_CRS
            or metadata["scale"] != [scale] * 3
            or metadata["offset"] != metadata["boundingBox"]["min"]
            or metadata["encoding"] != "DEFAULT"
            or {attr["name"] for attr in metadata["attributes"]} != {"position", "rgb"}
        ):
            raise ValueError("Potree metadata does not match the prepared ground cloud")
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        provenance = {
            "als": {
                "url": SAGIS_SOURCE,
                "sha256": SAGIS_SHA256,
                "crs": SAGIS_CRS,
                "class": 2,
                "attribution": "Datenquelle: Land Salzburg – data.salzburg.gv.at",
            },
            "orthophoto": {
                "url": WMTS + "/{z}/{y}/{x}.jpeg",
                "zoom": WMTS_ZOOM,
                "attribution": "Datenquelle: basemap.at",
                "licence": "CC BY 4.0",
                "tile_sha256": ortho_checksums,
            },
            "projection": OUTPUT_CRS,
            "vertical": "Z retained in metres from SAGIS. Vertical datum unknown.",
            "converter_commit": CONVERTER_COMMIT,
            "points": len(ground),
            "files": {
                name: {
                    "bytes": (octree / name).stat().st_size,
                    "sha256": sha256(octree / name),
                }
                for name in OUTPUT_FILES
            },
        }
        (octree / "provenance.json").write_text(
            json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        output.mkdir(exist_ok=True)
        for name in (*OUTPUT_FILES, "provenance.json"):
            (octree / name).replace(output / name)
    print(
        f"{len(ground):,} points coloured using {len(ortho_checksums)} orthophoto tiles"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--converter", type=Path, required=True)
    parser.add_argument(
        "--orthophoto-cache", type=Path, default=ROOT / "build" / "lidar-orthophoto"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "site" / "lidar" / "cloud"
    )
    arguments = parser.parse_args()
    prepare(
        arguments.source,
        arguments.orthophoto_cache,
        arguments.converter,
        arguments.output,
    )
