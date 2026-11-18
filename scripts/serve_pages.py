"""Serve the local atlas with byte ranges for Potree's binary files."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1] / "build" / "pages"
BYTE_RANGE = re.compile(r"bytes=([0-9]{0,20})-([0-9]{0,20})")


class PagesHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def send_head(self):
        self.range_length = None
        path = Path(self.translate_path(self.path)).resolve()
        root = Path(self.directory).resolve()
        if not path.is_relative_to(root):
            self.send_error(404)
            return None
        if path.is_dir():
            for name in ("index.html", "index.htm"):
                index = path / name
                if index.is_file() and not index.resolve().is_relative_to(root):
                    self.send_error(404)
                    return None

        request = BYTE_RANGE.fullmatch(self.headers.get("Range", ""))
        if (
            self.command != "GET"
            or not path.is_file()
            or not request
            or not any(request.groups())
        ):
            return super().send_head()

        try:
            stream = path.open("rb")
        except OSError:
            self.send_error(404)
            return None

        stat = os.fstat(stream.fileno())
        size = stat.st_size
        first, last = request.groups()
        start = int(first) if first else max(0, size - int(last))
        end = min(int(last), size - 1) if first and last else size - 1
        if start > end:
            stream.close()
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None

        self.range_length = end - start + 1
        stream.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path.name))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(self.range_length))
        self.send_header("Last-Modified", self.date_time_string(stat.st_mtime))
        self.end_headers()
        return stream

    def copyfile(self, source, outputfile):
        remaining = self.range_length
        if remaining is None:
            super().copyfile(source, outputfile)
            return
        while remaining:
            block = source.read(min(remaining, 64 * 1024))
            if not block:
                break
            outputfile.write(block)
            remaining -= len(block)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if not (args.root / "index.html").is_file():
        parser.error(f"Build the atlas first: missing {args.root / 'index.html'}")

    handler = partial(PagesHandler, directory=args.root.resolve())
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
