"""Odśwież osadzone dane GPX i Survex w index.html. Wymaga dump3d i cs2cs."""

import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GPX = HERE / "zrodla" / "Hagengebirge-2025-8.gpx"
REGIONAL = HERE / "zrodla" / "h2026.geojson"
HTML = HERE / "index.html"
LACZNIK_ROBOCZY = {"kgw.2", "local.4"}


def location(node):
    return [float(node.attrib["lat"]), float(node.attrib["lon"])]


def gpx_points():
    root = ET.parse(GPX).getroot()
    waypoints = []
    for node in root.findall("{*}wpt"):
        item = {"ll": location(node)}
        for field in ("name", "desc", "cmt", "ele", "time", "sym"):
            value = node.findtext("{*}" + field)
            if value and not (field == "cmt" and value == item.get("desc")):
                item[field] = value
        waypoints.append(item)
    return waypoints


def survey_records(model_path):
    dump = subprocess.check_output(["dump3d", "-l", model_path], text=True)
    crs = None
    nodes = {}
    edges = []
    for line in dump.splitlines():
        v = line.split()
        if v[:1] == ["CS"]:
            crs = v[1]
        if v[:1] == ["NODE"]:
            nodes[tuple(v[1:4])] = v[4].strip("[]")
        if v[:1] == ["LEG"]:
            edges.append((tuple(v[1:4]), tuple(v[4:7]), v[7:]))
    if crs is None:
        raise ValueError("Model Survex nie zawiera układu współrzędnych.")
    legs = []
    for a, b, flags in edges:
        start, end = nodes[a], nodes[b]
        synthetic = "DUPLICATE" in flags and {start, end} == LACZNIK_ROBOCZY
        legs.append([start, end, "SURFACE" in flags, synthetic])
    return crs, nodes, legs


def cave_data(model_path=ROOT / "hagen.3d"):
    crs, nodes, legs = survey_records(model_path)
    rows = subprocess.check_output(
        ["cs2cs", crs, "OGC:CRS84", "-f", "%.10f"],
        input="".join(" ".join(xyz) + "\n" for xyz in nodes), text=True,
    ).splitlines()
    stations = {}
    for xyz, row in zip(nodes, rows):
        lon, lat, height = map(float, row.split())
        stations[nodes[xyz]] = [lat, lon, height]
    if len(stations) != len(nodes):
        raise ValueError("Niepełna transformacja układu współrzędnych.")
    controls = {}
    for line in (ROOT / "hagen.svx").read_text().splitlines():
        v = line.lstrip("*; ").split()
        if v[:2] == ["fix", "kgw.e1"]:
            v = v[1:]
        if v[:1] in (["kgw.e1"], ["kgw.e2"]):
            lon, lat, z = map(float, v[1:])
            controls[v[0]] = [lat, lon, z]
    if set(controls) != {"kgw.e1", "kgw.e2"}:
        raise ValueError("Sprawdź zapis obu otworów w hagen.svx.")
    return stations, legs, controls


def main():
    stations, legs, controls = cave_data()
    data = dict(points=gpx_points(), regional=json.loads(REGIONAL.read_text()),
                stations=stations, legs=legs, controls=controls)
    encoded = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("<", "\\u003c")
    before, marker, tail = HTML.read_text(encoding="utf-8").partition('<script id="map-data" type="application/json">')
    if not marker or "</script>" not in tail:
        raise ValueError("Nie znaleziono miejsca na dane w pliku mapy.")
    after = tail.split("</script>", 1)[1]
    HTML.write_text(before + marker + encoded + "</script>" + after, encoding="utf-8")


if __name__ == "__main__":
    main()
