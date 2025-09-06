#!/usr/bin/env python3
import csv
import os
import re
import sys
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


CSV_PATH = "data/participants_template.csv"
OUT_DIR = "assets/icons"


def extract_handle(x_url: str) -> str:
    if not x_url:
        return ""
    x_url = x_url.strip()
    # Accept forms: https://x.com/handle, https://twitter.com/handle, @handle
    if x_url.startswith("@"):  # raw handle
        return x_url[1:]
    if x_url.startswith("http"):
        try:
            parts = urlsplit(x_url)
            # path like /handle or /handle/
            path = parts.path or ""
            if not path:
                return ""
            handle = path.strip("/").split("/")[0]
            # strip query artifacts like ?s=21&...
            handle = handle.split("?")[0]
            return handle
        except Exception:
            return ""
    # fallback: return as-is if it's a likely handle
    return re.sub(r"[^A-Za-z0-9_]+", "", x_url)


def download_first(candidates, out_path: str) -> bool:
    """Try a list of URLs and save the first that returns image/* content."""
    headers = {"User-Agent": "Mozilla/5.0 (Codex CLI)"}
    for url in candidates:
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=20) as resp:
                ctype = resp.headers.get("Content-Type", "")
                data = resp.read()
                if not data or not ctype.startswith("image/"):
                    continue
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(data)
                return True
        except Exception:
            continue
    return False


def fetch_x_icon(handle: str, out_path: str) -> bool:
    # Try unavatar variants first, then twitter redirect endpoint
    candidates = [
        f"https://unavatar.io/x/{handle}",
        f"https://unavatar.io/twitter/{handle}",
        f"https://unavatar.io/https://twitter.com/{handle}",
        f"https://twitter.com/{handle}/profile_image?size=original",
    ]
    return download_first(candidates, out_path)


def extract_youtube_handle(url: str) -> str:
    if not url:
        return ""
    m = re.search(r"youtube\.com/@([A-Za-z0-9_\-\.]+)", url)
    if m:
        return m.group(1)
    return ""


def fetch_youtube_icon(handle: str, out_path: str) -> bool:
    # Try multiple unavatar variants
    candidates = [
        f"https://unavatar.io/youtube/{handle}",
        f"https://unavatar.io/youtube/@{handle}",
        f"https://unavatar.io/https://www.youtube.com/@{handle}",
    ]
    return download_first(candidates, out_path)


def extract_instagram_handle(url: str) -> str:
    if not url:
        return ""
    m = re.search(r"instagram\.com/([^/?#]+)", url)
    if m:
        return m.group(1)
    return ""


def fetch_instagram_icon(handle: str, out_path: str) -> bool:
    candidates = [
        f"https://unavatar.io/instagram/{handle}",
        f"https://unavatar.io/https://instagram.com/{handle}",
    ]
    return download_first(candidates, out_path)


def main():
    csv_path = CSV_PATH
    force = False
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == "--force":
                force = True
            else:
                csv_path = arg
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    ok, ng = 0, 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Prefer X handle
            x_url = (row.get("XアカウントURL") or "").strip()
            x_handle = extract_handle(x_url)
            out_path = None
            fetched = False

            if x_handle:
                out_path = os.path.join(OUT_DIR, f"{x_handle}.jpg")
                if os.path.exists(out_path) and not force:
                    ok += 1
                    continue
                fetched = fetch_x_icon(x_handle, out_path)
                if fetched:
                    ok += 1
                    print(f"fetched: {x_handle} -> {out_path}")
                else:
                    print(f"failed: {x_handle}", file=sys.stderr)
            else:
                # Try Instagram (from SNSリンク) if X is missing; then YouTube
                sns_links = (row.get("SNSリンク") or "").strip()
                ig_handle = extract_instagram_handle(sns_links)
                if ig_handle:
                    out_path = os.path.join(OUT_DIR, f"{ig_handle}.jpg")
                    if os.path.exists(out_path) and not force:
                        ok += 1
                    else:
                        fetched = fetch_instagram_icon(ig_handle, out_path)
                        if fetched:
                            ok += 1
                            print(f"fetched: instagram:{ig_handle} -> {out_path}")
                        else:
                            print(f"failed: instagram:{ig_handle}", file=sys.stderr)

                if not fetched:
                    yt_handle = extract_youtube_handle(sns_links)
                    if yt_handle:
                        out_path = os.path.join(OUT_DIR, f"{yt_handle}.jpg")
                        if os.path.exists(out_path) and not force:
                            ok += 1
                        else:
                            fetched = fetch_youtube_icon(yt_handle, out_path)
                            if fetched:
                                ok += 1
                                print(f"fetched: youtube:{yt_handle} -> {out_path}")
                            else:
                                print(f"failed: youtube:{yt_handle}", file=sys.stderr)
            if not fetched and not out_path:
                ng += 1
                continue

    print(f"done. success={ok}, failed={ng}")


if __name__ == "__main__":
    main()
