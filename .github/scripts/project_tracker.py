"""Refresh dates on existing, explicitly selected project lines only.

Remove a line or the marker block to stop tracking it. Neither is recreated.
Descriptions remain hand-written in README.md. Dates are UTC last-push dates,
not inferred completion status. API failures leave the README untouched.
"""

import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

START = "<!--START_SECTION:projects-->"
END = "<!--END_SECTION:projects-->"
TRACKED = {"Qawwai/Skin-Lesion-Diagnosis-Classifier", "Qawwai/pca-image-compression"}
LINK = re.compile(r"\]\(https://github\.com/(Qawwai/[A-Za-z0-9_.-]+)\)")
DATE = re.compile(r" · Updated \d{4}-\d{2}-\d{2}\.$")


def fetch_date(repo):
    request = urllib.request.Request(
        "https://api.github.com/repos/" + repo,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-project-tracker"},
    )
    # Public metadata only; no personal access token or additional secrets.
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("private") is not False or data.get("full_name", "").lower() != repo.lower():
        raise ValueError("Unexpected repository metadata")
    stamp = data.get("pushed_at")
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").date().isoformat() if stamp else None


def refresh(content, fetch=fetch_date):
    if START not in content and END not in content:
        return content
    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError("Expected exactly one complete projects block")
    begin = content.index(START) + len(START)
    end = content.index(END)
    if end < begin:
        raise ValueError("Project markers are reversed")
    lines = content[begin:end].splitlines(keepends=True)
    for index, line in enumerate(lines):
        match = LINK.search(line)
        if not line.startswith("- ") or not match or match[1] not in TRACKED:
            continue
        date = fetch(match[1])
        if date:
            datetime.strptime(date, "%Y-%m-%d")
            ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
            body = DATE.sub("", line.rstrip("\r\n"))
            lines[index] = body + " · Updated " + date + "." + ending
    return content[:begin] + "".join(lines) + content[end:]


def main():
    path = Path("README.md")
    content = path.read_bytes().decode("utf-8")
    updated = refresh(content)
    if content != updated:
        path.write_bytes(updated.encode("utf-8"))
        print("Project dates updated.")
    else:
        print("No project changes.")


if __name__ == "__main__":
    main()
