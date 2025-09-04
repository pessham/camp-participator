#!/usr/bin/env python3
import csv
import os
import shutil
from typing import List
import html as htmllib


IN_CSV = "data/participants_template.csv"
OUT_DIR = "data/public"
OUT_CSV = os.path.join(OUT_DIR, "participants_public.csv")
OUT_MD = "docs/名簿_公開版.md"
OUT_HTML = "docs/index.html"
DOCS_ASSETS_DIR = "docs/assets/icons"
OFFICIAL_URL = "https://kochi-vibecording-camp.netlify.app/"


def truthy(s: str) -> bool:
    if s is None:
        return False
    v = s.strip().lower()
    return v in {"true", "1", "yes", "y", "公開", "ok"}


def write_csv(rows: List[dict], fieldnames: List[str]):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def write_md(rows: List[dict], fieldnames: List[str]):
    # Exclude the publish flag from Markdown output
    md_fields = [fn for fn in fieldnames if fn != "公開可否"]
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# バイブコーディングキャンプ 参加者名簿\n\n")
        f.write("（注）Discordで自己紹介いただいた方のみ表示しています。\n\n")
        f.write(f"公式サイト: {OFFICIAL_URL}\n\n")
        # Header
        f.write("| " + " | ".join(md_fields) + " |\n")
        f.write("|" + "|".join(["---"] * len(md_fields)) + "|\n")
        for r in rows:
            vals = [str(r.get(k, "") or "").replace("\n", " ") for k in md_fields]
            f.write("| " + " | ".join(vals) + " |\n")


def ensure_docs_icons(icon_path: str) -> str:
    """Copy local icon into docs/assets/icons and return the path for HTML src.
    If icon_path is remote (http/https), return it as-is. Appends a cache-busting
    query string based on file mtime to avoid stale images on Pages.
    """
    if icon_path.startswith("http://") or icon_path.startswith("https://"):
        return icon_path
    if not icon_path:
        return ""
    os.makedirs(DOCS_ASSETS_DIR, exist_ok=True)
    basename = os.path.basename(icon_path)
    dst = os.path.join(DOCS_ASSETS_DIR, basename)
    try:
        shutil.copy2(icon_path, dst)
        mtime = int(os.path.getmtime(dst))
    except FileNotFoundError:
        return ""
    # Return path relative to docs root with cache buster
    return f"assets/icons/{basename}?v={mtime}"


def write_html(rows: List[dict]):
    def extract_x_handle(x_url: str) -> str:
        if not x_url:
            return ""
        x_url = x_url.strip()
        if x_url.startswith("@"):  # raw handle
            return x_url[1:]
        if x_url.startswith("http"):
            try:
                from urllib.parse import urlsplit

                parts = urlsplit(x_url)
                path = parts.path or ""
                handle = path.strip("/").split("/")[0]
                handle = handle.split("?")[0]
                return handle
            except Exception:
                return ""
        return x_url

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>バイブコーディングキャンプ 参加者名簿</title>
  <style>
    :root { --bg:#0f172a; --card:#111827; --text:#e5e7eb; --muted:#9ca3af; --accent:#22d3ee; }
    body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans JP, sans-serif; background:var(--bg); color:var(--text); }
    header { padding:24px 16px; text-align:center; }
    header h1 { margin:0 0 8px; font-size:28px; }
    header p { margin:0; color:var(--muted); }
    .cta { margin-top:12px; }
    .btn { display:inline-block; padding:8px 14px; border-radius:999px; border:1px solid rgba(255,255,255,0.12); color:#0b1220; background:#22d3ee; text-decoration:none; font-weight:600; }
    .btn:hover { filter: brightness(1.05); }
    .container { max-width:1100px; margin:0 auto; padding:16px; }
    .grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap:16px; }
    .card { background:linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02)); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:14px; }
    .avatar { width:72px; height:72px; border-radius:50%; object-fit:cover; border:2px solid rgba(255,255,255,0.1); background:#222; }
    .row { display:flex; gap:12px; align-items:center; }
    .name { font-size:18px; font-weight:700; }
    .feature { color:var(--accent); font-size:14px; margin-top:2px; }
    .meta { color:var(--muted); font-size:13px; margin-top:8px; word-break: break-word; overflow-wrap: anywhere; }
    .desc { font-size:14px; line-height:1.6; margin-top:8px; color:#d1d5db; word-break: break-word; overflow-wrap: anywhere; }
    .tags { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
    .tag { border:1px solid rgba(255,255,255,0.12); color:var(--muted); padding:2px 8px; border-radius:999px; font-size:12px; }
    .links { display:flex; gap:10px; margin-top:10px; flex-wrap: wrap; }
    .link { color:#93c5fd; text-decoration:none; font-size:13px; }
    footer { text-align:center; color:var(--muted); padding:24px; font-size:13px; }
    @media (max-width: 640px) {
      .container { padding: 12px; }
      .grid { grid-template-columns: 1fr; gap: 12px; }
      .card { padding: 12px; }
      .avatar { width: 64px; height: 64px; }
      .name { font-size: 17px; }
      .feature { font-size: 13px; }
    }
  </style>
  <meta name="robots" content="noindex" />
  <!-- 共有時のみ index へ変更 -->
</head>
<body>
  <header>
    <h1>バイブコーディングキャンプ 参加者名簿</h1>
    <p>Discordで自己紹介いただいた方のみ表示しています。</p>
    <div class="cta"><a class="btn" target="_blank" rel="noopener" href="https://kochi-vibecording-camp.netlify.app/">公式サイトへ</a></div>
  </header>
  <div class="container">
""")
        if not rows:
            f.write("<p style='color:#9ca3af;text-align:center'>公開可否を true に設定するとカードが表示されます。</p>")
        f.write("<div class=grid>\n")
        for r in rows:
            icon_src = ensure_docs_icons((r.get("アイコンURL") or "").strip())
            # Use priority: local -> live X -> unavatar
            x_handle = extract_x_handle(r.get("XアカウントURL") or "")
            x_live = f"https://x.com/{x_handle}/profile_image?size=original" if x_handle else ""
            unavatar = f"https://unavatar.io/x/{x_handle}" if x_handle else ""
            name = htmllib.escape(r.get("ハンドルネーム") or "")
            feat = htmllib.escape(r.get("特徴（ひとことで）") or "")
            loc = htmllib.escape(r.get("お住まい") or "")
            job = htmllib.escape(r.get("お仕事") or "")
            x_url = r.get("XアカウントURL") or ""
            sns = (r.get("SNSリンク") or "").split(",")
            sns = [s.strip() for s in sns if s.strip()]
            desc = htmllib.escape(r.get("リアル人物の特徴説明") or r.get("ひとこと") or "")
            f.write("  <div class=card>\n")
            f.write("    <div class=row>\n")
            # Build fallback chain
            sources = [s for s in [icon_src, x_live, unavatar] if s]
            if sources:
                src0 = sources[0]
                src1 = sources[1] if len(sources) > 1 else ""
                src2 = sources[2] if len(sources) > 2 else ""
                onerr_parts = []
                if src1:
                    onerr_parts.append(f"if(!this.dataset.step){{this.dataset.step='1';this.src='{src1}';return;}}")
                if src2:
                    onerr_parts.append(f"if(this.dataset.step==='1'){{this.dataset.step='2';this.src='{src2}';return;}}")
                onerr_parts.append("this.onerror=null")
                onerr = " ".join(onerr_parts)
                f.write(
                    f"      <img class=avatar src=\"{src0}\" alt=\"{name}\" loading=\"lazy\" decoding=\"async\" referrerpolicy=\"no-referrer\" onerror=\"{onerr}\" />\n"
                )
            f.write("      <div>\n")
            f.write(f"        <div class=name>{name}</div>\n")
            if feat:
                f.write(f"        <div class=feature>{feat}</div>\n")
            f.write("      </div>\n")
            f.write("    </div>\n")
            if desc:
                f.write(f"    <div class=desc>{desc}</div>\n")
            if loc or job:
                meta = " ・ ".join([t for t in [loc, job] if t])
                f.write(f"    <div class=meta>{meta}</div>\n")
            links_out = []
            if x_url:
                links_out.append(("X", x_url))
            for s in sns:
                label = s.split("//")[-1]
                links_out.append((label, s))
            if links_out:
                f.write("    <div class=links>\n")
                for label, url in links_out[:4]:
                    url_esc = htmllib.escape(url)
                    label_esc = htmllib.escape(label[:28])
                    f.write(f"      <a class=link target=_blank rel=noopener href=\"{url_esc}\">{label_esc}</a>\n")
                f.write("    </div>\n")
            f.write("  </div>\n")
        f.write("</div>\n</div>\n")
        f.write("<footer>Generated by export_public.py</footer>\n")
        f.write("</body></html>")


def main():
    if not os.path.exists(IN_CSV):
        raise SystemExit(f"not found: {IN_CSV}")
    with open(IN_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        fieldnames = reader.fieldnames or []
    if "公開可否" not in fieldnames:
        raise SystemExit("CSVに '公開可否' 列がありません")

    pub_rows = [r for r in all_rows if truthy(r.get("公開可否", ""))]
    write_csv(pub_rows, fieldnames)
    write_md(pub_rows, fieldnames)
    write_html(pub_rows)
    print(f"exported: {len(pub_rows)} rows -> {OUT_CSV}, {OUT_MD}, {OUT_HTML}")


if __name__ == "__main__":
    main()
