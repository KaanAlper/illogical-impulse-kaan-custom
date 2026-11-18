#!/usr/bin/env python3
"""Parallel HTTP Range image downloader (IDM-style multi-connection chunking)."""

import concurrent.futures
import hashlib
import os
import sys
import urllib.parse
import urllib.request

CACHE_DIR = "/tmp/qs-anime-cache"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)
CHUNK_MIN_SIZE = 256 * 1024  # Only split files >= 256 KiB
DEFAULT_WORKERS = 8


def guess_ext(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".bmp"}:
        return ext
    return ".img"


def probe(url: str) -> tuple[int | None, bool]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            length_hdr = resp.headers.get("Content-Length")
            ranges_hdr = (resp.headers.get("Accept-Ranges") or "").lower()
            total = int(length_hdr) if length_hdr and length_hdr.isdigit() else None
            return total, ("bytes" in ranges_hdr)
    except Exception:
        return None, False


def download_range(url: str, fd: int, start: int, end: int) -> None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Range": f"bytes={start}-{end}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        offset = start
        while True:
            buf = resp.read(65536)
            if not buf:
                break
            written = 0
            while written < len(buf):
                n = os.pwrite(fd, buf[written:], offset + written)
                written += n
            offset += len(buf)


def download_single(url: str, part_path: str) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp, open(part_path, "wb") as f:
        while True:
            buf = resp.read(65536)
            if not buf:
                break
            f.write(buf)


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1]:
        return 1
    url = sys.argv[1]
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_WORKERS

    os.makedirs(CACHE_DIR, exist_ok=True)
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    dest = os.path.join(CACHE_DIR, f"{digest}{guess_ext(url)}")

    if os.path.isfile(dest) and os.path.getsize(dest) > 0:
        print(f"file://{dest}", flush=True)
        return 0

    part = f"{dest}.{os.getpid()}.part"
    try:
        total, supports_ranges = probe(url)
        if supports_ranges and total and total >= CHUNK_MIN_SIZE:
            fd = os.open(part, os.O_CREAT | os.O_RDWR | os.O_TRUNC, 0o644)
            try:
                os.ftruncate(fd, total)
                step = (total + workers - 1) // workers
                ranges = [
                    (i * step, min(total - 1, (i + 1) * step - 1))
                    for i in range(workers)
                    if i * step < total
                ]
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(ranges)) as ex:
                    futs = [ex.submit(download_range, url, fd, s, e) for s, e in ranges]
                    for fut in concurrent.futures.as_completed(futs):
                        fut.result()
            finally:
                os.close(fd)
        else:
            download_single(url, part)

        os.replace(part, dest)
        print(f"file://{dest}", flush=True)
        return 0
    except Exception as exc:
        print(f"ERR:{exc}", file=sys.stderr)
        try:
            if os.path.exists(part):
                os.unlink(part)
        except OSError:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
