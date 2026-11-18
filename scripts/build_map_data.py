"""Build the Web Mercator overlays and GeoJSON. Requires NumPy, OpenCV, Survex and PROJ."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import cv2
import numpy as np

from tantal_plan import tantal_plan

ROOT = Path(__file__).resolve().parents[1]
CAVE = ROOT / "1335-70"
sys.path.insert(0, str(ROOT / "mapa"))
from odswiez import REGIONAL, cave_data, gpx_points  # noqa: E402 — shared with the offline map


def write_json(path, data, indent=None):
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=indent,
            separators=None if indent else (",", ":"),
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def feature(geometry, coordinates, **properties):
    return {
        "type": "Feature",
        "geometry": {"type": geometry, "coordinates": coordinates},
        "properties": properties,
    }


def vectors(output, model_path, points):
    stations, legs, controls = cave_data(model_path)
    gps, surveys, entrances = [], [], []
    names = {"Kalbergrube_70-d": "kgw.e1", "Kalbergrube_70-g": "kgw.e2"}
    for point in points:
        lat, lon = point["ll"]
        props = {k: v for k, v in point.items() if k != "ll"}
        if "ele" in props:
            props["ele"] = float(props["ele"])
        if props.get("name") in names:
            props["station"] = names[props["name"]]
        gps.append(feature("Point", [lon, lat], **props))
    for start, end, surface in legs:
        coords = [[stations[s][1], stations[s][0]] for s in (start, end)]
        surveys.append(
            feature(
                "LineString", coords, **{"from": start, "to": end, "surface": surface}
            )
        )
    for station, label in (("kgw.e1", "Otwór dolny"), ("kgw.e2", "Otwór górny")):
        for kind, source in (("control", controls), ("model", stations)):
            lat, lon, ele = source[station]
            entrances.append(
                feature(
                    "Point", [lon, lat], kind=kind, station=station, name=label, ele=ele
                )
            )
    datasets = {"gps": gps, "surveys": surveys, "controls": entrances}
    manifest = {}
    for key, features in datasets.items():
        filename = ("entrances" if key == "controls" else key) + ".geojson"
        write_json(
            output / filename, {"type": "FeatureCollection", "features": features}
        )
        manifest[key] = filename
    shutil.copyfile(REGIONAL, output / REGIONAL.name)
    manifest["regional"] = REGIONAL.name
    return manifest


def node_locations(path):
    rows = subprocess.check_output(["dump3d", "-l", path], text=True).splitlines()
    return {
        r[4].strip("[]"): complex(float(r[1]), float(r[2]))
        for row in rows
        if (r := row.split())[:1] == ["NODE"]
    }


def transform_coords(source, target, coords):
    rows = subprocess.check_output(
        ["cs2cs", source, "+to", target, "-f", "%.10f"],
        input="".join(f"{p.real:.10f} {p.imag:.10f}\n" for p in coords),
        text=True,
    ).splitlines()
    return np.array([complex(*map(float, row.split()[:2])) for row in rows])


def model_alignment(model_path):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "local.3d"
        subprocess.run(
            ["cavern", "-w", "-o", path, CAVE / "kontrola/uklad-planu.svx"], check=True
        )
        local = node_locations(path)
    utm = node_locations(model_path)
    a, b = local["kgw.e1"], utm["kgw.e1"]
    # Use the computed upper station for orientation; its independent GPS reading is a check.
    rotation = (utm["kgw.e2"] - b) / (local["kgw.e2"] - a)
    rotation /= abs(rotation)
    offset = b - rotation * a
    error = max(
        abs(rotation * point + offset - utm[name]) for name, point in local.items()
    )
    print(f"Maksymalna różnica przeniesienia stacji układu planu do UTM: {error:.3f} m")
    return rotation, offset


def paper_pixels(grid, en):
    # Same measured intersections and bilinear interpolation as sprawdz_obrys.py.
    u, v = (en.real + 350) / 50, (100 - en.imag) / 50
    i, j = (
        np.clip(np.floor(u).astype(int), 0, 6),
        np.clip(np.floor(v).astype(int), 0, 3),
    )
    a, b = u - i, v - j
    top = grid[j, i] * (1 - a) + grid[j, i + 1] * a
    bottom = grid[j + 1, i] * (1 - a) + grid[j + 1, i + 1] * a
    return top * (1 - b) + bottom * b


def old_plan_pixels(plan_xy):
    # Six surveyed drawing correspondences transcribed in kontrola/dowiazanie.md.
    plan = [
        [1210, 400],
        [1265, 333],
        [1368, 265],
        [1319, 343],
        [1172, 478],
        [1421, 285],
    ]
    book = [[540, 634], [634, 524], [849, 385], [745, 529], [489, 789], [934, 425]]
    design = np.column_stack((plan, np.ones(len(plan))))
    affine = np.linalg.lstsq(design, book, rcond=None)[0]
    coeffs = affine[:, 0] + 1j * affine[:, 1]
    return coeffs[0] * plan_xy.real + coeffs[1] * plan_xy.imag + coeffs[2]


def selected_ink(gray, outline, reference_width, historical):
    # Extract dark ink against the photographed paper, retaining thin, faint strokes.
    paper = cv2.morphologyEx(
        gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    )
    threshold, contrast = (18, 3.3) if historical else (6, 5.5)
    ink = np.clip((paper.astype(float) - gray - threshold) * contrast, 0, 255).astype(
        "uint8"
    )
    mask = np.zeros_like(gray)
    polygon = np.rint(np.array(outline) * gray.shape[1] / reference_width).astype(
        "int32"
    )
    cv2.fillPoly(mask, [polygon], 255)
    return cv2.bitwise_and(ink, mask)


def draw_plan(gray, outline, reference_width, box, grid, alignment, historical, path):
    rotation, offset = alignment
    xmin, ymin, xmax, ymax = box
    local_corners = np.array(
        [complex(x, y) for x in (xmin, xmax) for y in (ymin, ymax)]
    )
    projected = transform_coords(
        "EPSG:32633", "EPSG:3857", local_corners * rotation + offset
    )
    left, right = projected.real.min(), projected.real.max()
    bottom, top = projected.imag.min(), projected.imag.max()
    corners = [complex(x, y) for y in (top, bottom) for x in (left, right)]
    local = (transform_coords("EPSG:3857", "EPSG:32633", corners) - offset) / rotation
    width = round((xmax - xmin) * (8 if historical else 4))
    height = round(width * (top - bottom) / (right - left))
    u = (np.arange(width) + 0.5) / width
    v = (np.arange(height)[:, None] + 0.5) / height
    # Project the map pixel centers. Bilinear interpolation over this sub-km extent.
    en = (1 - v) * ((1 - u) * local[0] + u * local[1]) + v * (
        (1 - u) * local[2] + u * local[3]
    )
    xy = paper_pixels(grid, en)
    if historical:
        xy = old_plan_pixels(xy)
    ink = cv2.remap(
        selected_ink(gray, outline, reference_width, historical),
        xy.real.astype("float32"),
        xy.imag.astype("float32"),
        cv2.INTER_LINEAR,
    )
    # Thin ivory halo keeps original ink visible on light and dark basemaps.
    halo = cv2.GaussianBlur(cv2.dilate(ink, np.ones((3, 3), np.uint8)), (5, 5), 1.0)
    alpha = ink + halo.astype(float) * (1 - ink / 255)
    color = (ink * 0.10 + (alpha - ink) * 0.98) / np.maximum(alpha, 1) * 255
    rgba = np.stack((color, color, color, alpha), axis=-1).astype("uint8")
    if not cv2.imwrite(str(path), rgba, [cv2.IMWRITE_PNG_COMPRESSION, 9]):
        raise OSError(f"Nie można zapisać {path}")
    sw, ne = transform_coords(
        "EPSG:3857", "OGC:CRS84", [complex(left, bottom), complex(right, top)]
    )
    return [[sw.imag, sw.real], [ne.imag, ne.real]]


def plan_layers(output, model_path):
    raw = (CAVE / "kontrola/lokalny-na-planie.html").read_text()
    registration = json.loads(
        re.search(r'<script id="data" type="application/json">(.*?)</script>', raw)[1]
    )
    grid_xy = np.asarray(registration["grid"])
    grid = grid_xy[..., 0] + 1j * grid_xy[..., 1]
    alignment = model_alignment(model_path)
    # Paper cut lines traced in 1400- and 720-pixel-wide previews. They exclude the
    # unrelated marginal sketch, page text, compass, legend and title block.
    outline = [
        (182, 48),
        (268, 49),
        (268, 113),
        (299, 159),
        (312, 237),
        (309, 289),
        (339, 331),
        (375, 389),
        (491, 438),
        (552, 427),
        (597, 445),
        (645, 481),
        (673, 485),
        (690, 465),
        (679, 407),
        (706, 379),
        (728, 323),
        (752, 309),
        (750, 244),
        (785, 231),
        (755, 174),
        (739, 110),
        (704, 107),
        (704, 34),
        (784, 30),
        (813, 118),
        (857, 160),
        (888, 184),
        (960, 163),
        (1044, 180),
        (1051, 198),
        (1101, 199),
        (1101, 335),
        (986, 335),
        (960, 282),
        (929, 279),
        (885, 320),
        (850, 344),
        (896, 399),
        (872, 425),
        (834, 421),
        (775, 370),
        (745, 367),
        (728, 390),
        (781, 408),
        (788, 451),
        (751, 470),
        (788, 514),
        (749, 550),
        (712, 566),
        (664, 619),
        (628, 634),
        (603, 624),
        (619, 558),
        (585, 529),
        (555, 493),
        (525, 479),
        (485, 487),
        (414, 456),
        (384, 475),
        (317, 450),
        (245, 413),
        (190, 378),
        (117, 362),
        (117, 315),
        (175, 312),
        (230, 365),
        (324, 382),
        (310, 355),
        (270, 320),
        (258, 241),
        (231, 189),
        (205, 167),
        (180, 115),
    ]
    book_outline = [
        (174, 58),
        (245, 62),
        (260, 133),
        (331, 139),
        (337, 174),
        (275, 188),
        (270, 201),
        (337, 238),
        (349, 305),
        (381, 309),
        (429, 295),
        (426, 227),
        (512, 216),
        (565, 240),
        (609, 242),
        (630, 320),
        (668, 334),
        (668, 407),
        (597, 409),
        (552, 354),
        (527, 376),
        (511, 376),
        (509, 416),
        (378, 416),
        (362, 450),
        (330, 475),
        (299, 514),
        (262, 506),
        (243, 491),
        (247, 432),
        (207, 430),
        (214, 395),
        (265, 389),
        (254, 351),
        (243, 307),
        (241, 254),
        (211, 223),
        (207, 187),
        (198, 139),
        (171, 89),
    ]
    main = cv2.rotate(
        cv2.imread(str(CAVE / "zrodla/plan-1-500.jpg"), cv2.IMREAD_GRAYSCALE),
        cv2.ROTATE_90_COUNTERCLOCKWISE,
    )
    book = cv2.imread(str(CAVE / "zrodla/hoehlenbuch/s-304.jpg"), cv2.IMREAD_GRAYSCALE)
    if main.shape != (924, 2000) or book.shape != (1600, 1200):
        raise ValueError("Zmieniła się geometria fotografii źródłowej.")
    main_bounds = draw_plan(
        main,
        outline,
        1400,
        (-395, -150, 22, 109),
        grid,
        alignment,
        False,
        output / "plan-1985.png",
    )
    book_bounds = draw_plan(
        book,
        book_outline,
        720,
        (-153, -56, 22, 106),
        grid,
        alignment,
        True,
        output / "plan-1963.png",
    )
    return [
        {
            "id": "plan-1985",
            "title": "Kälbergruben-Windloch · 1963/1985",
            "image": "plan-1985.png",
            "bounds": main_bounds,
            "note": "Dopasowanie do 40 przecięć siatki 50 m i głównego poligonu Survex. Dolny otwór ustala położenie. Fałdy papieru i perspektywa zdjęcia ograniczają dokładność.",
            "attribution": "Archiwum Landesverein für Höhlenkunde in Salzburg, plan 1335/70.",
        },
        {
            "id": "plan-1963",
            "title": "Kälbergruben-Windloch · stare partie 1963",
            "image": "plan-1963.png",
            "bounds": book_bounds,
            "note": "Ryc. 276 przeniesiono na plan zbiorczy według sześciu szczegółów ścian. Przy bocznej odnodze Große Halle różnica wynosi około 6 m.",
            "attribution": "F. Koppenwallner, 1963. Salzburger Höhlenbuch, t. 3 (1979), s. 304, ryc. 276.",
        },
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "site/map/data",
        help="Directory for the manifest, rasters and vectors",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=ROOT / "hagen.3d",
        help="Compiled georeferenced main Survex model",
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    points = gpx_points()
    manifest = vectors(args.output, args.model, points)
    manifest["plans"] = plan_layers(args.output, args.model)
    manifest["plans"].append(tantal_plan(args.output, points, transform_coords))
    write_json(args.output / "map.json", manifest, 2)


if __name__ == "__main__":
    main()
