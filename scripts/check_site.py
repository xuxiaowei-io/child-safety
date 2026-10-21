#!/usr/bin/env python3
"""Validate the static child-safety site before it is published to GitHub Pages.

Checks are deliberately dependency-free (stdlib only) so the same command works
locally and in CI:

    python3 scripts/check_site.py

It verifies structure (required files and anchors), that every local link
resolves, that the page loads no third-party resources, and that the canonical
/ Open Graph / sitemap / robots metadata stay consistent with the public URL.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
BASE_PATH = "/child-safety/"
ORIGIN = "https://xuxiaowei-io.github.io"
PAGE_URL = ORIGIN + BASE_PATH
OG_IMAGE = PAGE_URL + "assets/og.png"

REQUIRED_FILES = [
    "index.html",
    "404.html",
    "robots.txt",
    "sitemap.xml",
    ".nojekyll",
    "assets/app-icon-96.png",
    "assets/og.png",
    "assets/icon-192.png",
    "assets/apple-touch-icon.png",
    "assets/favicon-32.png",
]

REQUIRED_IDS = {
    "main",
    "doc-zh",
    "doc-en",
    "btn-zh",
    "btn-en",
    *{f"zh-{i}" for i in range(1, 12)},
    *{f"en-{i}" for i in range(1, 12)},
}

RESOURCE_TAGS = {"script", "link", "img", "iframe", "source", "video", "audio"}
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "#")


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []  # (tag, url) for href/src
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.metas: list[dict[str, str]] = []
        self.mailtos: list[str] = []
        self.title = ""
        self._in_title = False
        self._in_style = False
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k: (v or "") for k, v in attrs}
        self.tags.append((tag, attr))
        if attr.get("id"):
            self.ids.add(attr["id"])
        if tag == "meta":
            self.metas.append(attr)
        if tag == "title":
            self._in_title = True
        if tag == "style":
            self._in_style = True
        metadata_link = tag == "link" and attr.get("rel") in ("canonical", "alternate")
        for name in ("href", "src"):
            url = attr.get(name)
            if not url:
                continue
            if url.startswith("mailto:"):
                self.mailtos.append(url)
            if url.startswith(SKIP_SCHEMES) or metadata_link:
                continue
            self.links.append((tag, url))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if not self._in_style:
            self.text.append(data)

    def meta(self, key: str, value: str) -> str:
        for attrs in self.metas:
            if attrs.get(key) == value:
                return attrs.get("content", "")
        return ""


errors: list[str] = []
notes: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def check(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def resolve_local(url: str) -> Path | None:
    """Map a local URL from the page to a file under site/."""
    if url.startswith("http://") or url.startswith("https://"):
        return None
    path = urlparse(url).path
    if path.startswith(BASE_PATH):
        path = path[len(BASE_PATH) :]
    elif path.startswith("/"):
        path = path.lstrip("/")
    if path in ("", ".") or path.endswith("/"):
        path += "index.html"
    return SITE / path


def validate_page(path: Path) -> PageParser:
    raw = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(raw)
    parser.close()
    rel = path.relative_to(SITE)

    for tag, url in parser.links:
        target = resolve_local(url)
        if target is None:
            if tag in RESOURCE_TAGS:
                fail(f"{rel}: 引用了外部资源 <{tag}> {url}（页面必须自包含）")
            continue
        if url.startswith("#"):
            continue
        if not target.exists():
            fail(f"{rel}: 本地链接指向不存在的文件 {url}")

    for tag, attr in parser.tags:
        if tag == "a":
            href = attr.get("href", "")
            if href.startswith("#") and len(href) > 1 and href[1:] not in parser.ids:
                fail(f"{rel}: 锚点 {href} 没有对应的 id")

    check("TODO" not in raw, f"{rel}: 还有 TODO 占位符")
    check("example.com" not in raw, f"{rel}: 还有 example.com 占位符")

    if rel.name == "index.html":
        missing = REQUIRED_IDS - parser.ids
        check(not missing, f"{rel}: 缺少必需的 id: {', '.join(sorted(missing))}")
        check(parser.title.strip() != "", f"{rel}: 缺少 <title>")
        check(
            'name="viewport"' in raw or "name='viewport'" in raw,
            f"{rel}: 缺少 viewport meta",
        )
        check(len(parser.mailtos) >= 2, f"{rel}: mailto 链接少于 2 个")
        check(
            "xuxiaowei@xuxiaowei.com.cn" in "".join(parser.text),
            f"{rel}: 联系人邮箱没有出现在正文里",
        )
        canonical = next(
            (a.get("href", "") for t, a in parser.tags if t == "link" and a.get("rel") == "canonical"),
            "",
        )
        check(canonical == PAGE_URL, f"{rel}: canonical 应为 {PAGE_URL}，实际 {canonical!r}")
        check(
            parser.meta("property", "og:url") == PAGE_URL,
            f"{rel}: og:url 应为 {PAGE_URL}",
        )
        check(
            parser.meta("property", "og:image") == OG_IMAGE,
            f"{rel}: og:image 应为 {OG_IMAGE}",
        )
        check(
            parser.meta("property", "og:image:width") == "1200"
            and parser.meta("property", "og:image:height") == "630",
            f"{rel}: og:image 尺寸应为 1200x630",
        )
        check(len(parser.meta("name", "description")) >= 50, f"{rel}: description 太短")
        headings = [a for t, a in parser.tags if t == "h2"]
        check(len(headings) == 22, f"{rel}: 应为 11+11 个小节标题，实际 {len(headings)}")

    return parser


def main() -> int:
    for name in REQUIRED_FILES:
        check((SITE / name).exists(), f"缺少文件 site/{name}")

    if not (SITE / "index.html").exists():
        report()
        return 1

    parser = validate_page(SITE / "index.html")
    validate_page(SITE / "404.html")

    canonical = PAGE_URL
    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    check(f"<loc>{canonical}</loc>" in sitemap, "sitemap.xml: <loc> 与 canonical 不一致")
    robots = (SITE / "robots.txt").read_text(encoding="utf-8")
    check(f"{PAGE_URL}sitemap.xml" in robots, "robots.txt: 没有指向 sitemap.xml")

    check(parser.ids, "index.html: 没有解析到任何 id")
    notes.append(f"页面 URL: {PAGE_URL}")
    notes.append(f"正文小节: {sum(1 for t, _ in parser.tags if t == 'h2')} 个")
    notes.append(f"锚点: {len(parser.ids)} 个，内部链接均可解析")

    report()
    return 0 if not errors else 1


def report() -> None:
    for note in notes:
        print(f"  {note}")
    if errors:
        print("\n校验失败：")
        for err in errors:
            print(f"  ✗ {err}")
    else:
        print("\n✓ 站点校验通过")


if __name__ == "__main__":
    sys.exit(main())
