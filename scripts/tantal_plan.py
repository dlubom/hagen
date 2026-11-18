"""Georeference the 1979 Tantalhöhle plan using its printed grid and the GPX entrance."""

from pathlib import Path

import cv2
import numpy as np


PHOTO = Path(__file__).resolve().parents[1] / "1335-30/zrodla/plan-1979.jpg"
# East, north (500 m squares), x, y (pixel centres in the cropped photograph).
# The N arrow follows the north grid lines. The origin is the labelled Eingang.
# fmt: off
GRID = np.array([
    (0, 0, 126, 1197), (0, 1, 345, 761), (1, 1, 788, 1008), (2, 1, 1234, 1248),
    (0, 2, 588, 324), (1, 2, 1031, 570), (2, 2, 1467, 815), (3, 2, 1904, 1054),
    (4, 2, 2327, 1293), (1, 3, 1272, 126), (2, 3, 1711, 381), (3, 3, 2145, 626),
    (4, 3, 2570, 867), (5, 3, 3001, 1107), (6, 3, 3419, 1344), (3, 4, 2386, 180),
    (4, 4, 2819, 431), (5, 4, 3249, 675), (6, 4, 3667, 917), (5, 5, 3496, 238),
    (6, 5, 3915, 484),
], dtype=float)
# fmt: on


def radial_basis(locations):
    delta = locations[:, None] - GRID[None, :, :2]
    squared = np.sum(delta * delta, axis=2)
    return squared * np.log(np.maximum(squared, 1e-12))


def photo_pixels(locations):
    """Thin plate spline through the photographed intersections of the folded sheet."""
    axis = np.column_stack((np.ones(len(GRID)), GRID[:, :2]))
    system = np.block([[radial_basis(GRID[:, :2]), axis], [axis.T, np.zeros((3, 3))]])
    weights = np.linalg.solve(system, np.vstack((GRID[:, 2:], np.zeros((3, 2)))))
    basis = np.column_stack(
        (radial_basis(locations), np.ones(len(locations)), locations)
    )
    return basis @ weights


def drawing():
    photo = cv2.imread(str(PHOTO))
    if photo is None or photo.shape[:2] != (1390, 4032):
        raise ValueError(f"Nieoczekiwane wymiary fotografii {PHOTO}")
    # Cut around the plan view and its labels. Coordinates refer to a half-size photo.
    # fmt: off
    outline = [
        (45, 577), (57, 567), (60, 499), (93, 496), (99, 475), (48, 463),
        (55, 415), (108, 405), (110, 370), (121, 327), (165, 329), (170, 303),
        (251, 303), (266, 272), (311, 265), (327, 244), (360, 241),
        (321, 228), (240, 236), (244, 208), (280, 201), (299, 168), (319, 169),
        (325, 194), (390, 199), (401, 175), (492, 175), (509, 187), (521, 183),
        (515, 157), (560, 155), (568, 141), (547, 126), (506, 127), (502, 103),
        (578, 105), (589, 89), (581, 80), (510, 84), (507, 61), (553, 60),
        (547, 34), (562, 27), (623, 56), (704, 68), (709, 90), (631, 91),
        (614, 114), (666, 121), (699, 138), (695, 159), (602, 162),
        (602, 174), (651, 175), (680, 233), (753, 235), (809, 258), (837, 254),
        (954, 252), (947, 285), (995, 291), (999, 320), (951, 324), (964, 331),
        (1044, 336), (1088, 331), (1117, 343), (1129, 367), (1199, 375),
        (1208, 337), (1259, 324), (1265, 345), (1244, 357), (1258, 380),
        (1302, 398), (1353, 381), (1351, 348), (1434, 352), (1471, 360),
        (1488, 322), (1588, 318), (1644, 326), (1781, 320), (1784, 350),
        (1840, 366), (1859, 385), (1871, 366), (1952, 366), (1958, 402),
        (1977, 413), (1977, 455), (1881, 457), (1825, 424), (1776, 426),
        (1745, 410), (1727, 437), (1591, 438), (1581, 416), (1558, 422),
        (1517, 420), (1513, 449), (1411, 448), (1373, 443), (1341, 440),
        (1312, 427), (1293, 442), (1251, 444), (1217, 451), (1176, 455),
        (1136, 459), (1131, 485), (1064, 485), (1052, 503), (962, 502),
        (952, 528), (926, 530), (919, 552), (833, 550), (837, 531), (813, 530),
        (783, 520), (759, 534), (674, 537), (675, 510), (707, 506),
        (701, 457), (696, 421), (649, 419), (648, 391), (700, 389),
        (708, 359), (674, 345), (650, 324), (578, 321), (564, 343),
        (599, 354), (581, 390), (553, 423), (520, 427), (477, 371), (415, 356),
        (406, 388), (345, 401), (327, 430), (330, 444), (352, 447),
        (346, 463), (306, 462), (289, 500), (324, 514), (335, 540),
        (292, 548), (284, 567), (407, 574), (409, 597), (311, 601),
        (348, 634), (346, 662), (308, 662), (303, 678), (270, 679),
        (270, 663), (224, 662), (223, 635), (275, 630), (263, 602),
        (247, 591), (245, 574), (224, 576), (206, 585), (133, 587),
        (125, 609), (52, 614),
    ]
    # fmt: on
    mask = np.zeros(photo.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [2 * np.array(outline, dtype=np.int32)], 255)
    # Normalize each channel against nearby paper to recover the coloured print,
    # including the lightly printed passages under the reflection on the middle fold.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (39, 39))
    paper = cv2.morphologyEx(photo, cv2.MORPH_CLOSE, kernel)
    density = np.maximum(paper.astype(np.float32) - photo, 0) / np.maximum(paper, 1)
    strength = np.max(density, axis=2)
    alpha = np.clip((strength - 0.07) * 1.85, 0, 1)
    alpha *= mask / 255
    colour = 1 - density / np.maximum(strength[:, :, None], 0.001)
    return np.dstack((colour * 255, alpha * 255)).astype(np.uint8)


def tantal_plan(output, points, transform_coords):
    (entrance,) = [p for p in points if p.get("name") == "Tantalhohle_30"]
    lat, lon = entrance["ll"]
    # Ground metres with true north at the entrance, no UTM grid convergence.
    local_crs = (
        f"+proj=tmerc +lat_0={lat} +lon_0={lon} +k=1 +ellps=WGS84 +units=m +type=crs"
    )
    # Source coordinates and the identified marks on both sheets are recorded
    # in 1335-30/georeferencja.md. Only the direction to point 302 sets rotation.
    survey_entrance, survey_302, survey_231 = transform_coords(
        "EPSG:32633",
        local_crs,
        [355462.73 + 5262084.82j, 357235.13 + 5263317.77j, 356477.23 + 5263110.86j],
    )
    paper_302 = 1650.92 + 1371.02j
    paper_231 = 876.33 + 1095.52j
    map_to_paper = paper_302 / (survey_302 - survey_entrance)
    map_to_paper /= abs(map_to_paper)
    angle = f"{np.angle(map_to_paper, deg=True):.2f}".replace(".", ",")
    residual_302 = abs(paper_302 / map_to_paper - survey_302)
    residual_231 = abs(paper_231 / map_to_paper - survey_231)
    corners = np.array([-550 - 150j, -550 + 2650j, 3500 - 150j, 3500 + 2650j])
    web = transform_coords(local_crs, "EPSG:3857", corners / map_to_paper)
    left, right = web.real.min(), web.real.max()
    bottom, top = web.imag.min(), web.imag.max()
    # A ~16 m mesh resolves the smooth photograph warp. Include both end pixel
    # centres explicitly so interpolation preserves the placement of the entrance.
    width, height = 4050, 2800
    coarse_x = np.linspace(0, width - 1, 256)
    coarse_y = np.linspace(0, height - 1, 182)
    x, y = np.meshgrid(coarse_x, coarse_y)
    mercator = left + (x + 0.5) / width * (right - left)
    mercator = mercator + 1j * (top - (y + 0.5) / height * (top - bottom))
    local = transform_coords("EPSG:3857", local_crs, mercator.ravel()) / 500
    grid = local * map_to_paper
    px = photo_pixels(np.column_stack((grid.real, grid.imag))).reshape(*x.shape, 2)
    # Interpolate premultiplied colour to keep paper out of the edges of the ink.
    source = drawing()
    source[:, :, :3] = (
        source[:, :, :3].astype(np.float32)
        * (source[:, :, 3:].astype(np.float32) / 255)
    ).astype("uint8")
    xx, yy = np.meshgrid(
        np.arange(width, dtype=np.float32) * (len(coarse_x) - 1) / (width - 1),
        np.arange(height, dtype=np.float32) * (len(coarse_y) - 1) / (height - 1),
    )
    lookup = cv2.remap(
        px.astype(np.float32), xx, yy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    )
    overlay = cv2.remap(source, lookup, None, cv2.INTER_LINEAR)
    del xx, yy, lookup
    sx, sy, w, h = cv2.boundingRect(overlay[:, :, 3])
    if min(sx, sy, width - sx - w, height - sy - h) < 2:
        raise ValueError("Ramka nakładki przycina rysunek Tantalhöhle.")
    overlay = overlay[sy : sy + h, sx : sx + w].copy()
    overlay[:, :, :3] = np.clip(
        overlay[:, :, :3].astype(np.float32) * 255 / np.maximum(overlay[:, :, 3:], 1),
        0,
        255,
    )
    filename = "plan-tantal-1979.webp"
    if not cv2.imwrite(
        str(output / filename), overlay, [cv2.IMWRITE_WEBP_QUALITY, 101]
    ):
        raise OSError(f"Nie można zapisać {filename}")
    scale_x, scale_y = (right - left) / width, (top - bottom) / height
    sw, ne = transform_coords(
        "EPSG:3857",
        "OGC:CRS84",
        [
            complex(left + sx * scale_x, top - (sy + h) * scale_y),
            complex(left + (sx + w) * scale_x, top - sy * scale_y),
        ],
    )
    return {
        "id": "plan-tantal-1979",
        "title": "Tantalhöhle 1335/30 · 1979",
        "image": filename,
        "bounds": [[sw.imag, sw.real], [ne.imag, ne.real]],
        "note": (
            "Otwór Eingang (1710 m) dowiązano do punktu GPX Tantalhohle_30. "
            "Siatka 500 m wyznacza skalę. Kierunek do punktu 302 w Riesenhalle "
            f"(stacja 282 pomiaru z 1986 r.) obraca plan o {angle}° w prawo "
            "względem wariantu z drukowaną strzałką N skierowaną na północ geograficzną. "
            f"Różnica położenia w punkcie 302 wynosi {residual_302:.0f} m, "
            f"a w niezależnym punkcie 231 przy Seufzertreppe (stacja 190) {residual_231:.0f} m."
        ),
        "attribution": "W. Waagner, 1979, według planów G. Abla, F. Koppenwallnera i W. Klappachera.",
    }
