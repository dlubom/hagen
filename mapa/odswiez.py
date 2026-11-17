"""Odśwież osadzone dane GPX i Survex w index.html. Wymaga dump3d i cs2cs."""

import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GPX = HERE / "zrodla" / "Hagengebirge-2025-8.gpx"
HTML = HERE / "index.html"


def location(node):
    return [float(node.attrib["lat"]), float(node.attrib["lon"])]


def gpx_data():
    root = ET.parse(GPX).getroot()
    waypoints = []
    for node in root.findall("{*}wpt"):
        item = {"ll": location(node)}
        for field in ("name", "desc", "cmt", "ele", "time", "sym"):
            value = node.findtext("{*}" + field)
            if value and not (field == "cmt" and value == item.get("desc")):
                item[field] = value
        waypoints.append(item)
    paths = []
    for kind, groups in (
        ("Ślad GPX", [(e, e.findall("{*}trkseg"), "trkpt") for e in root.findall("{*}trk")]),
        ("Trasa GPX", [(e, [e], "rtept") for e in root.findall("{*}rte")]),
    ):
        for node, segments, point_tag in groups:
            paths.append({
                "name": node.findtext("{*}name") or kind,
                "kind": kind,
                "segments": [[location(pt) for pt in seg.findall("{*}" + point_tag)] for seg in segments],
            })
    return waypoints, paths


def cave_data():
    dump = subprocess.check_output(["dump3d", "-l", ROOT / "hagen.3d"], text=True)
    nodes = {}
    edges = []
    for line in dump.splitlines():
        v = line.split()
        if v[:1] == ["CS"]:
            crs = v[1]
        if v[:1] == ["NODE"]:
            nodes[tuple(v[1:4])] = v[4].strip("[]")
        if v[:1] == ["LEG"]:
            edges.append((tuple(v[1:4]), tuple(v[4:7]), "SURFACE" in v[7:]))
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
    legs = [[nodes[a], nodes[b], surface] for a, b, surface in edges]
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
    points, tracks = gpx_data()
    stations, legs, controls = cave_data()
    data = dict(points=points, tracks=tracks, stations=stations, legs=legs, controls=controls)
    encoded = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("<", "\\u003c")
    before, marker, tail = HTML.read_text(encoding="utf-8").partition('<script id="map-data" type="application/json">')
    if not marker or "</script>" not in tail:
        raise ValueError("Nie znaleziono miejsca na dane w pliku mapy.")
    after = tail.split("</script>", 1)[1]
    HTML.write_text(before + marker + encoded + "</script>" + after, encoding="utf-8")


if __name__ == "__main__":
    main()
