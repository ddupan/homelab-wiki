#!/usr/bin/env python3
"""列出 watch 路径在 last_reviewed 之后有新提交的页面；--issue 时同步到固定 issue。"""
from __future__ import annotations

import argparse
from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_docs import as_date, split_frontmatter  # noqa: E402

API = "https://git.ddupan.top/api/v1"
DEFAULT_OWNER = "panxiao81"
WIKI_REPO = "panxiao81/homelab-wiki"
ISSUE_TITLE = "文档待复核"
# Dependency bumps change versions, not how anything is used or operated.
NOISE = ("chore(deps)", "fix(deps)")


def api(path, token=None, method="GET", body=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"token {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    # The WAN drops at random; a weekly job should not fail on one blip.
    for attempt in range(3):
        try:
            with urlopen(Request(API + path, data, headers, method=method), timeout=30) as r:
                return json.load(r)
        except HTTPError:
            raise
        except OSError:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def parse_watch(entry):
    repo, path = entry.split(":", 1)
    if "/" not in repo:
        repo = f"{DEFAULT_OWNER}/{repo}"
    return repo, path.strip("/")


def path_exists(repo, path):
    try:
        api(f"/repos/{repo}/contents/{quote(path)}")
        return True
    except HTTPError as e:
        if e.code == 404:
            return False
        raise


def commits_since(repo, path, since):
    query = urlencode({"path": path, "since": f"{since.isoformat()}T00:00:00Z", "limit": 50,
                       "stat": "false", "verification": "false", "files": "false"})
    result = []
    for c in api(f"/repos/{repo}/commits?{query}"):
        subject = c["commit"]["message"].splitlines()[0]
        if len(c.get("parents") or []) > 1 or any(n in subject for n in NOISE):
            continue
        result.append((c["sha"][:7], subject, c["html_url"]))
    return result


def stale_pages(root):
    files = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z", "*.md"]).decode().split("\0")
    report = []
    for relative in sorted(f for f in files if f):
        meta, _ = split_frontmatter((root / relative).read_text(encoding="utf-8"))
        if not meta or not meta.get("watch") or not meta.get("last_reviewed"):
            continue
        # ponytail: day granularity; commits made later on the review day are skipped.
        since = as_date(meta["last_reviewed"]) + timedelta(days=1)
        findings = []
        for entry in meta["watch"]:
            repo, path = parse_watch(entry)
            if not path_exists(repo, path):
                findings.append(f"- `{entry}` 已不存在，代码可能搬了家")
                continue
            for sha, subject, url in commits_since(repo, path, since):
                findings.append(f"- `{entry}` [{sha}]({url}) {subject}")
        if findings:
            report.append((relative, meta["last_reviewed"], list(dict.fromkeys(findings))))
    return report


def render(report):
    lines = ["以下页面依赖的源码在上次复核后有变化。对照提交更新正文后修改 `last_reviewed`；",
             "内容不受影响也只需更新日期。本 issue 由每周的 stale 任务自动维护。", ""]
    for relative, reviewed, findings in report:
        lines += [f"### [{relative}](https://git.ddupan.top/{WIKI_REPO}/src/branch/main/{relative})",
                  f"上次复核：{reviewed}", "", *findings, ""]
    return "\n".join(lines)


def sync_issue(report, token):
    issues = api(f"/repos/{WIKI_REPO}/issues?" + urlencode({"state": "open", "type": "issues",
                                                           "q": ISSUE_TITLE}), token)
    issue = next((i for i in issues if i["title"] == ISSUE_TITLE), None)
    if not report:
        if issue:
            api(f"/repos/{WIKI_REPO}/issues/{issue['number']}", token, "PATCH", {"state": "closed"})
        return
    body = render(report)
    if issue:
        api(f"/repos/{WIKI_REPO}/issues/{issue['number']}", token, "PATCH", {"body": body})
    else:
        api(f"/repos/{WIKI_REPO}/issues", token, "POST", {"title": ISSUE_TITLE, "body": body})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--issue", action="store_true", help="用 GITEA_TOKEN 同步固定 issue")
    args = parser.parse_args()
    report = stale_pages(args.root)
    print(render(report) if report else "没有需要复核的页面。")
    if args.issue:
        sync_issue(report, os.environ["GITEA_TOKEN"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
