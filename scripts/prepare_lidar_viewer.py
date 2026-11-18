"""Install the pinned Potree-Next renderer and its local patches."""

import argparse
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

SOURCE = Path(__file__).resolve().parent / "vendor"
PATCHES = {}

PATCHES["src/potree/octree/PointCloudOctree.js"] = [
    (
        "\t\t\tlet {node, weight} = element;\n",
        "\t\t\tlet {node, weight} = element;\n\n\t\t\t// Local prototype: enforce the budget assigned by the upstream renderer.\n\t\t\tif (numPoints + node.numPoints > this.pointBudget) continue;\n",
    ),
]
PATCHES["src/potree/octree/loader/PotreeLoader.js"] = [
    (
        "\t\t\t\tlet geometry = new Geometry();\n",
        "\t\t\t\tnode.loadAttempts = 0;\n\t\t\t\tlet geometry = new Geometry();\n",
    ),
    (
        "\t\t\t\t'content-type': 'multipart/byteranges',\n",
        "",
    ),
    (
        "\t\tlet buffer = await response.arrayBuffer();\n\n\t\tthis.parseHierarchy(node, buffer);",
        "\t\tif (response.status !== 206) throw new Error(`Hierarchy Range HTTP ${response.status}`);\n\t\tlet buffer = await response.arrayBuffer();\n\t\tif (buffer.byteLength !== Number(node.hierarchyByteSize)) throw new Error('Incomplete hierarchy Range');\n\n\t\tthis.parseHierarchy(node, buffer);",
    ),
    (
        '\t\t\t\tif(data === "failed"){\n',
        '\t\t\t\tif(data === "failed"){\n\t\t\t\t\tnode.loadAttempts = (node.loadAttempts || 0) + 1;\n\t\t\t\t\tif (node.loadAttempts > 5) this.error = `Nie udało się odczytać fragmentu chmury ${node.name}. Sprawdź HTTP Range i odśwież stronę.`;\n',
    ),
    (
        "\t\t}catch(e){\n\t\t\tdebugger;",
        "\t\t}catch(e){\n\t\t\tnode.loadAttempts = (node.loadAttempts || 0) + 1;\n\t\t\tif (node.loadAttempts > 5) this.error = `Nie udało się odczytać hierarchii ${node.name}: ${e.message || e}`;",
    ),
    (
        "\t\tlet response = await fetch(url);\n\t\tlet metadata = await response.json();",
        "\t\tlet response = await fetch(url);\n\t\tif (!response.ok) throw new Error(`Metadane chmury: HTTP ${response.status}`);\n\t\tlet metadata = await response.json();",
    ),
    (
        'workerPath = "./src/potree/octree/loader/DecoderWorker_default.js";',
        'workerPath = new URL("./DecoderWorker_default.js", import.meta.url).href;',
    ),
    (
        'workerPath = "./src/potree/octree/loader/DecoderWorker_brotli.js";',
        'workerPath = new URL("./DecoderWorker_brotli.js", import.meta.url).href;',
    ),
]
PATCHES["src/potree/octree/loader/DecoderWorker_default.js"] = [
    (
        "\t\t\t\t'content-type': 'multipart/byteranges',\n",
        "",
    ),
    (
        "\t\tbuffer = await response.arrayBuffer();",
        "\t\tif (response.status !== 206) throw new Error(`Point Range HTTP ${response.status}`);\n\t\tbuffer = await response.arrayBuffer();\n\t\tif (buffer.byteLength !== Number(byteSize)) throw new Error('Incomplete point Range');",
    ),
]
PATCHES["src/renderer/Renderer.js"] = [
    (
        "\t\tx = Math.max(x, 0);\n\t\ty = Math.max(y, 0);",
        "\t\t// A resize can leave the pointer outside the new picking texture.\n\t\tif (x >= texture.width || y >= texture.height || width > texture.width || height > texture.height) {\n\t\t\treturn new ArrayBuffer(width * height * 4);\n\t\t}\n\t\tx = Math.max(0, Math.min(Math.floor(x), texture.width - width));\n\t\ty = Math.max(0, Math.min(Math.floor(y), texture.height - height));",
    ),
]
PATCHES["src/modules/drawCommands/renderLines.js"] = [
    (
        "\tvout.color = color;",
        "\tvout.color = vec4<f32>(color.rgb / 255.0, color.a);",
    ),
]
PATCHES["src/init.js"] = [
    (
        'import * as ProgressiveLoader from "./modules/progressive_loader/ProgressiveLoader.js";\n',
        "// This viewer loads prepared octrees.\n",
    ),
    (
        '\t// progressive loader\n\tlet element = document.getElementById("canvas");\n\tProgressiveLoader.install(element, {\n\t\tonSetup: (node) => {\n\t\t\tscene.root.children.push(node)\n\t\t\tconsole.log("setup done");\n\t\t},\n\t\tonProgress: (e) => {\n\t\t\tconsole.log("progress", e);\n\t\t}\n\t});\n',
        "",
    ),
]


def install(output):
    manifest = SOURCE / "potree-next.json"
    pin = json.loads(manifest.read_text(encoding="utf-8"))
    archive_path = SOURCE / "potree-next.zip"
    if (
        archive_path.stat().st_size != pin["archive_bytes"]
        or hashlib.sha256(archive_path.read_bytes()).hexdigest()
        != pin["archive_sha256"]
    ):
        raise ValueError("Potree-Next archive checksum mismatch")

    root = f"Potree-Next-{pin['sha']}"
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            path = PurePosixPath(member.filename)
            if path.parts[0] != root or ".." in path.parts or "\\" in str(path):
                raise ValueError(f"Unexpected archive path: {member.filename}")
            relative = path.relative_to(root)
            if relative.parts[0] not in {
                "src",
                "libs",
                "resources",
                "LICENSE",
                "README.md",
            }:
                continue
            destination = output.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(member))

    diff = []
    for filename, substitutions in PATCHES.items():
        path = output / filename
        original = path.read_text(encoding="utf-8")
        changed = original
        for before, after in substitutions:
            if changed.count(before) != 1:
                raise ValueError(f"Unexpected pinned source: {filename}")
            changed = changed.replace(before, after, 1)
        path.write_bytes(changed.replace("\n", "\r\n").encode("utf-8"))
        diff.extend(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                changed.splitlines(keepends=True),
                fromfile=f"a/{filename}",
                tofile=f"b/{filename}",
            )
        )

    (output / "potree-next-local.patch").write_text("".join(diff), encoding="utf-8")
    shutil.copyfile(manifest, output / manifest.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    install(parser.parse_args().output)
