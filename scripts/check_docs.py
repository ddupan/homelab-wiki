#!/usr/bin/env python3
"""离线检查 wiki 的元数据、链接、标题锚点与服务索引。"""
from __future__ import annotations

import argparse
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
import yaml

LIFECYCLES = {"planned", "experimental", "active", "retired", "unknown"}
EVIDENCE = {"configuration", "documented", "live-verified"}
# These two pages are navigation/scope descriptions, not individual services.
SERVICE_INDEXES = {"services/index.md", "services/external-consumers.md"}
# A reader in the middle of an incident relies on every SOP having the same shape.
SOP_SECTIONS = ["什么时候用", "先确认", "操作步骤", "验证", "回滚 / 升级"]
# <repo>:<path> or <owner>/<repo>:<path>; parsed again by stale_pages.py.
WATCH = re.compile(r"(?:[\w.-]+/)?[\w.-]+:[^\s:]+")


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise ValueError("frontmatter 键必须是字符串")
        if key in result:
            raise ValueError(f"重复 frontmatter 键：{key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def split_frontmatter(text):
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            metadata = yaml.load("".join(lines[1:i]), Loader=UniqueLoader)
            if not isinstance(metadata, dict):
                raise ValueError("frontmatter 必须是映射")
            # Preserve line positions for diagnostics.
            return metadata, "\n" * (i + 1) + "".join(lines[i + 1:])
    raise ValueError("frontmatter 缺少结束分隔符")


def as_date(value):
    if type(value) is date:
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return date.fromisoformat(value)
    raise ValueError("必须是 YYYY-MM-DD 日期")


def metadata_errors(meta, required=False, template=False):
    if meta is None:
        return ["服务页缺少 frontmatter"] if required else []
    errors = []
    keys = {"title", "last_reviewed"}
    if required:
        keys |= {"lifecycle", "evidence", "last_verified"}
    for key in sorted(keys - meta.keys()):
        errors.append(f"缺少字段 {key}")
    if not isinstance(meta.get("title"), str) or not meta["title"].strip():
        errors.append("title 必须是非空字符串")
    for key, choices in [("lifecycle", LIFECYCLES), ("evidence", EVIDENCE)]:
        if key in meta and (not isinstance(meta[key], str) or meta[key] not in choices):
            errors.append(f"{key} 不在允许值中")
    dates = {}
    for key in ["last_reviewed", "last_verified"]:
        if key not in meta:
            continue
        if meta[key] is None:
            if key == "last_reviewed" and not template:
                errors.append("last_reviewed 不得为 null")
            continue
        try:
            dates[key] = as_date(meta[key])
        except (ValueError, TypeError):
            errors.append(f"{key} 必须是 YYYY-MM-DD 日期或允许的 null")
    if meta.get("evidence") == "live-verified" and "last_verified" not in dates:
        errors.append("live-verified 必须提供 last_verified 日期")
    if len(dates) == 2 and dates["last_verified"] > dates["last_reviewed"]:
        errors.append("last_verified 不能晚于 last_reviewed")
    if "sources" in meta and (not isinstance(meta["sources"], list) or
                             any(not isinstance(x, str) or not x.strip() for x in meta["sources"])):
        errors.append("sources 必须是非空字符串组成的列表（可为空列表）")
    if "watch" in meta and (not isinstance(meta["watch"], list) or
                           any(not isinstance(x, str) or not WATCH.fullmatch(x) for x in meta["watch"])):
        errors.append("watch 必须是 <仓库>:<路径> 或 <所有者>/<仓库>:<路径> 组成的列表")
    return errors


def slug(text):
    # Common Gitea/GitHub heading form; keep CJK, words, spaces and hyphens.
    return "".join(c for c in text.lower() if c in " -_" or
                   unicodedata.category(c)[0] in "LN").replace(" ", "-")


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.anchors = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ["href", "src"]:
            if attrs.get(key):
                self.links.append(attrs[key])
        if attrs.get("id"):
            self.anchors.add(attrs["id"])
        if tag == "a" and attrs.get("name"):
            self.anchors.add(attrs["name"])


def parse_body(body):
    tokens = MarkdownIt("commonmark").enable("table").parse(body)
    anchors, links, sections = set(), [], []
    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            inline = tokens[i + 1]
            text = "".join(t.content for t in inline.children or []
                           if t.type in {"text", "code_inline", "image"})
            if token.tag == "h2":
                sections.append(text.strip())
            base = slug(text)
            candidate, suffix = base, 0
            while candidate in anchors:
                suffix += 1
                candidate = f"{base}-{suffix}"
            anchors.add(candidate)

        def visit(t, line):
            line = t.map[0] + 1 if t.map else line
            if t.type in {"link_open", "image"}:
                url = t.attrGet("href" if t.type == "link_open" else "src")
                if url is not None:
                    links.append((line, url))
            if t.type in {"html_inline", "html_block"}:
                html = HTMLLinks()
                html.feed(t.content)
                anchors.update(html.anchors)
                links.extend((line, u) for u in html.links)
            for child in t.children or []:
                visit(child, line)
        visit(token, 1)
    return anchors, links, sections


def check(root, files):
    root = root.resolve()
    errors, documents = [], {}
    for relative in files:
        path = root / relative
        try:
            if not path.resolve().is_relative_to(root):
                raise ValueError("文件指向仓库外部")
            meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
            required = relative.startswith("services/") and relative not in SERVICE_INDEXES
            errors.extend(f"{relative}:1: {e}" for e in metadata_errors(
                meta, required=required, template=relative.startswith("templates/")))
            documents[relative] = parse_body(body)
            if is_sop(relative):
                missing = [h for h in SOP_SECTIONS if h not in documents[relative][2]]
                if missing:
                    errors.append(f"{relative}:1: SOP 缺少小节：{'、'.join(missing)}")
        except (ValueError, OSError, yaml.YAMLError) as exc:
            # Do not print YAML source lines: malformed frontmatter may contain secrets.
            errors.append(f"{relative}:1: 无法解析文件或 frontmatter（{type(exc).__name__}）")
    indexed = set()
    for relative, (_, links, _) in documents.items():
        for line, url in links:
            prefix = f"{relative}:{line}: "
            try:
                parsed = urlsplit(url)
            except ValueError:
                errors.append(prefix + "URL 格式无效")
                continue
            if parsed.scheme in {"http", "https", "mailto", "tel", "data"} or parsed.netloc:
                continue
            if parsed.scheme or parsed.path.startswith("/"):
                errors.append(prefix + "链接必须使用仓库内相对路径或网页 URL")
                continue
            target = ((root / relative).parent / unquote(parsed.path)).resolve() if parsed.path else root / relative
            if not target.is_relative_to(root):
                errors.append(prefix + "链接越出仓库")
                continue
            if not target.exists():
                errors.append(prefix + f"目标不存在：{unquote(parsed.path)}")
                continue
            dest = target.relative_to(root).as_posix()
            if relative in {"services/index.md", "sop/index.md"}:
                indexed.add(dest)
            anchor = unquote(parsed.fragment)
            if anchor and dest in documents and anchor not in documents[dest][0]:
                errors.append(prefix + f"标题锚点不存在：{dest}#{anchor}")
    for relative in documents:
        if relative.startswith("services/") and relative not in SERVICE_INDEXES and relative not in indexed:
            errors.append(f"{relative}:1: 服务页未被 services/index.md 链接")
        if is_sop(relative) and relative not in indexed:
            errors.append(f"{relative}:1: SOP 未被 sop/index.md 链接")
    return errors


def is_sop(relative):
    return relative.startswith("sop/") and relative != "sop/index.md"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    output = subprocess.check_output(
        ["git", "-C", str(args.root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"])
    files = sorted({p for p in output.decode().split("\0") if p.endswith(".md")})
    errors = check(args.root, files)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"文档检查通过：{len(files)} 个 Markdown 文件；未联网或执行文档示例。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
