"""Refresh the 'Recent activity' block in README.md from my public GitHub events."""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

USER = "Qawwai"
MAX_LINES = 5
README = "README.md"
START = "<!--START_SECTION:activity-->"
END = "<!--END_SECTION:activity-->"


def fetch_events():
    req = urllib.request.Request(
        "https://api.github.com/users/%s/events/public?per_page=100" % USER,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "readme-activity",
        },
    )
    token = os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def ago(stamp):
    moment = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    seconds = (datetime.now(timezone.utc) - moment).total_seconds()
    for size, unit in ((86400, "d"), (3600, "h"), (60, "m")):
        if seconds >= size:
            return "%d%s ago" % (seconds // size, unit)
    return "just now"


def describe(event):
    repo = event["repo"]["name"]
    link = "[%s](https://github.com/%s)" % (repo, repo)
    payload = event.get("payload") or {}
    kind = event["type"]

    if kind == "PushEvent":
        count = payload.get("size", 0)
        return "Pushed %d commit%s to %s" % (count, "" if count == 1 else "s", link)
    if kind == "CreateEvent":
        ref_type = payload.get("ref_type")
        if ref_type == "repository":
            return "Started %s" % link
        if ref_type == "branch":
            return "Opened branch `%s` on %s" % (payload.get("ref"), link)
        return None
    if kind == "PullRequestEvent":
        number = payload.get("number")
        url = (payload.get("pull_request") or {}).get("html_url", "")
        return "%s pull request [#%s](%s) in %s" % (
            (payload.get("action") or "updated").capitalize(),
            number,
            url,
            link,
        )
    if kind == "IssuesEvent":
        issue = payload.get("issue") or {}
        return "%s issue [#%s](%s) in %s" % (
            (payload.get("action") or "updated").capitalize(),
            issue.get("number"),
            issue.get("html_url", ""),
            link,
        )
    if kind == "ReleaseEvent":
        release = payload.get("release") or {}
        return "Released [%s](%s) in %s" % (
            release.get("tag_name"),
            release.get("html_url", ""),
            link,
        )
    if kind == "WatchEvent":
        return "Starred %s" % link
    if kind == "ForkEvent":
        return "Forked %s" % link
    return None


def build_lines(events):
    lines = []
    seen = set()
    for event in events:
        text = describe(event)
        if not text:
            continue
        key = (event["type"], event["repo"]["name"])
        if key in seen:
            continue
        seen.add(key)
        lines.append("- %s &nbsp;&middot;&nbsp; %s" % (text, ago(event["created_at"])))
        if len(lines) == MAX_LINES:
            break
    return lines


def main():
    lines = build_lines(fetch_events())
    if not lines:
        lines = ["- Nothing public in the last little while."]

    with open(README, encoding="utf-8") as handle:
        content = handle.read()

    block = "%s\n\n%s\n\n%s" % (START, "\n".join(lines), END)
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        lambda _: block,
        content,
        flags=re.DOTALL,
    )

    if updated != content:
        with open(README, "w", encoding="utf-8") as handle:
            handle.write(updated)
        print("README updated.")
    else:
        print("No change.")


if __name__ == "__main__":
    main()
