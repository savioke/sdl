#!/usr/bin/env python3
"""Serve a browsable HTML view of a repo's docs/sdl over localhost.

The viewer assets (index.html, marked.min.js) live once in this governance
install's viewer/ dir; the markdown is read live from the target repo's
docs/sdl/. Nothing is copied into the target repo.

    python3 sdl-serve.py [repo-path] [--port N]

repo-path defaults to the current directory. Binds 127.0.0.1 only.
"""

import argparse
import hashlib
import http.server
import json
import posixpath
import sys
import urllib.parse
from pathlib import Path

GOV = Path(__file__).resolve().parent.parent
VIEWER = GOV / "viewer"

# Pinned integrity of the vendored renderer (marked v12.0.2). A mismatch means
# the file was changed outside git; we warn rather than fail.
MARKED_SHA256 = "15fabce5b65898b32b03f5ed25e9f891a729ad4c0d6d877110a7744aa847a894"

META_FIELDS = ("slug", "branch", "pr", "status", "created")


def safe_join(root: Path, url_path: str):
    """Map a URL path under root to a real file, or None on traversal."""
    rel = urllib.parse.unquote(url_path).lstrip("/")
    rel = posixpath.normpath(rel) if rel else ""
    target = (root / rel).resolve()
    root = root.resolve()
    if target != root and root not in target.parents:
        return None  # escaped the root (../, absolute, or symlink out)
    return target


def read_meta(meta_path: Path) -> dict:
    """Minimal scalar parse of .sdl-meta.yml — avoids a YAML dependency."""
    out = {}
    for line in meta_path.read_text(encoding="utf-8").splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        if key in META_FIELDS:
            out[key] = val.strip()
    return out


def build_manifest(docs: Path) -> dict:
    top = [
        {"name": p.name, "path": "/" + p.name}
        for p in sorted(docs.glob("*.md"))
    ]
    cycles = []
    for d in sorted(p for p in docs.iterdir() if p.is_dir()):
        meta_file = d / ".sdl-meta.yml"
        if not meta_file.is_file():
            continue
        files = [
            {"name": f.name, "path": f"/{d.name}/{f.name}"}
            for f in sorted(d.glob("*.md"))
        ]
        files.append({"name": ".sdl-meta.yml", "path": f"/{d.name}/.sdl-meta.yml"})
        cycles.append({"dir": d.name, "meta": read_meta(meta_file), "files": files})
    return {"repo": str(docs.parent.parent), "topLevel": top, "cycles": cycles}


def make_handler(docs: Path):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _send(self, status, body: bytes, ctype: str):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _send_file(self, path: Path):
            ctype = {
                ".html": "text/html; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
                ".md": "text/plain; charset=utf-8",
                ".yml": "text/plain; charset=utf-8",
            }.get(path.suffix, "application/octet-stream")
            self._send(200, path.read_bytes(), ctype)

        def do_GET(self):
            url = urllib.parse.urlparse(self.path).path
            if url in ("/", ""):
                return self._send_file(VIEWER / "index.html")
            if url == "/_manifest":
                body = json.dumps(build_manifest(docs)).encode("utf-8")
                return self._send(200, body, "application/json; charset=utf-8")
            root = VIEWER if url.startswith("/_viewer/") else docs
            sub = url[len("/_viewer"):] if url.startswith("/_viewer/") else url
            target = safe_join(root, sub)
            if target is None or not target.is_file():
                return self._send(404, b"not found", "text/plain; charset=utf-8")
            self._send_file(target)

        do_HEAD = do_GET

    return Handler


def main():
    ap = argparse.ArgumentParser(description="Serve docs/sdl as a browsable HTML report.")
    ap.add_argument("repo", nargs="?", default=".", help="repo path (default: cwd)")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    docs = (Path(args.repo).resolve() / "docs" / "sdl")
    if not docs.is_dir():
        sys.exit(f"no docs/sdl under {Path(args.repo).resolve()}")
    if not (VIEWER / "index.html").is_file():
        sys.exit(f"viewer assets missing at {VIEWER}")

    marked = VIEWER / "marked.min.js"
    if marked.is_file():
        got = hashlib.sha256(marked.read_bytes()).hexdigest()
        if got != MARKED_SHA256:
            print(f"warning: {marked} sha256 {got} != pinned {MARKED_SHA256}", file=sys.stderr)

    httpd = http.server.HTTPServer(("127.0.0.1", args.port), make_handler(docs))
    print(f"SDL report: http://127.0.0.1:{args.port}/  (serving {docs})")
    print("Ctrl-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
