#!/usr/bin/env python3
"""Local-only static preview with uncached assets and video Range requests."""
import argparse
import functools
import http.server
import re
from pathlib import Path


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def send_head(self):
        self.byte_range = None
        path = Path(self.translate_path(self.path))
        request = self.headers.get('Range', '')
        if not request or not path.is_file():
            return super().send_head()
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', request)
        if not match:
            self.send_error(416, 'Unsupported byte range')
            return None
        size = path.stat().st_size
        a, b = match.groups()
        start = int(a) if a else max(0, size-int(b or 0))
        end = min(size-1, int(b)) if a and b else size-1
        if start > end or start >= size:
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{size}')
            self.end_headers()
            return None
        source = path.open('rb')
        source.seek(start)
        self.byte_range = (start, end)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end-start+1))
        self.end_headers()
        return source

    def copyfile(self, source, output):
        if self.byte_range is None:
            return super().copyfile(source, output)
        remaining = self.byte_range[1]-self.byte_range[0]+1
        while remaining:
            chunk = source.read(min(65536, remaining))
            if not chunk:
                break
            output.write(chunk)
            remaining -= len(chunk)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8853)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1]/'www')
    args = parser.parse_args()
    server = http.server.ThreadingHTTPServer(('127.0.0.1', args.port), functools.partial(Handler, directory=str(args.root)))
    print(f'Preview: http://127.0.0.1:{args.port}/', flush=True)
    server.serve_forever()
