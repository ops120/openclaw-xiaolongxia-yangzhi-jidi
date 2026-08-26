#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert .md to HTML, then take full-page screenshot via playwright."""

import sys
from pathlib import Path
import markdown
from playwright.sync_api import sync_playwright


def md_to_html(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "codehilite",
            "sane_lists",
            "nl2br",
        ]
    )
    body_html = md.convert(text)

    css = """
    * { box-sizing: border-box; }
    body {
        font-family: "Microsoft YaHei", "Segoe UI", "PingFang SC", sans-serif;
        font-size: 14px;
        line-height: 1.65;
        color: #1e293b;
        background: #ffffff;
        max-width: 1200px;
        margin: 0 auto;
        padding: 30px 40px;
    }
    h1 {
        font-size: 26px;
        color: #0f172a;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 10px;
        margin: 30px 0 20px;
    }
    h2 {
        font-size: 21px;
        color: #1e293b;
        margin: 30px 0 15px;
        border-left: 4px solid #3b82f6;
        padding-left: 12px;
    }
    h3 { font-size: 17px; color: #334155; margin: 25px 0 12px; }
    h4 { font-size: 15px; color: #475569; margin: 20px 0 10px; }
    p { margin: 10px 0; }
    table {
        border-collapse: collapse;
        margin: 15px 0;
        width: 100%;
        font-size: 13px;
    }
    th, td {
        border: 1px solid #cbd5e1;
        padding: 8px 12px;
        text-align: left;
        vertical-align: top;
    }
    th { background: #f1f5f9; font-weight: 600; color: #0f172a; }
    tr:nth-child(even) td { background: #f8fafc; }
    code {
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: Consolas, monospace;
        font-size: 13px;
        color: #be185d;
    }
    pre {
        background: #0f172a;
        color: #e2e8f0;
        padding: 15px 18px;
        border-radius: 6px;
        overflow-x: auto;
        font-size: 12px;
        line-height: 1.5;
        margin: 15px 0;
    }
    pre code { background: transparent; color: inherit; padding: 0; }
    blockquote {
        border-left: 4px solid #94a3b8;
        padding: 10px 15px;
        margin: 15px 0;
        color: #475569;
        background: #f8fafc;
    }
    img {
        max-width: 100%;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        margin: 10px 0;
    }
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 25px 0; }
    ul, ol { margin: 10px 0; padding-left: 30px; }
    li { margin: 4px 0; }
    strong { color: #0f172a; font-weight: 700; }
    em { color: #475569; font-style: italic; }
    a { color: #2563eb; text-decoration: none; }
    """

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{md_path.stem}</title>
<style>{css}</style>
</head>
<body>
{body_html}
</body>
</html>
"""


def screenshot_html(html_path: Path, png_path: Path):
    url = f"file:///{str(html_path).replace(chr(92), '/')}"
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--no-sandbox", "--disable-gpu"]
        )
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()


def main():
    md_path = Path(r"D:\ai_project_all\openclaw-xiaolongxia-yangzhi-jidi-main\自买自测\RTX5070-32G\花巨资测试_Qwen3.8-27B_RTX5070-32G_vLLM_投机解码对比.md")
    html_path = md_path.with_suffix(".html")
    png_path = Path(r"D:\ai_project_all\openclaw-xiaolongxia-yangzhi-jidi-main\自买自测\RTX5070-32G\花巨资测试_Qwen3.8-27B_RTX5070-32G_vLLM_投机解码对比_文档截图.png")

    if not md_path.exists():
        print(f"ERROR: 找不到 {md_path}")
        sys.exit(1)

    print(f"[1/3] Read: {md_path.name}")
    html = md_to_html(md_path)

    print(f"[2/3] Write HTML: {html_path.name}")
    html_path.write_text(html, encoding="utf-8")
    print(f"      HTML bytes: {len(html)}")

    print(f"[3/3] Screenshot: {png_path.name}")
    screenshot_html(html_path, png_path)
    print(f"      PNG bytes: {png_path.stat().st_size}")


if __name__ == "__main__":
    main()
