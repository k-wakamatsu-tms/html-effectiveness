#!/usr/bin/env python3
"""Detect which English HTML files need their ja/ translation created, updated, or deleted.

Stateless: for each ja/ file, the English content it was translated from is taken
to be the English file as of the last commit that touched that ja/ file. If the
current English file differs from that baseline, the translation needs updating.

Run from anywhere inside the repo. Requires the upstream merge to be committed
(only git-tracked files are considered).

Output: JSON with keys "add", "update", "delete", "ok".
"""
import json
import subprocess
import sys


def git(*args, check=True):
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8"
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result


def main():
    repo = git("rev-parse", "--show-toplevel").stdout.strip()
    files = git("-C", repo, "ls-files", "*.html").stdout.splitlines()
    en_files = [f for f in files if not f.startswith("ja/")]
    ja_files = set(f for f in files if f.startswith("ja/"))

    result = {"add": [], "update": [], "delete": [], "ok": []}

    for en in en_files:
        ja = "ja/" + en
        if ja not in ja_files:
            result["add"].append(en)
            continue
        base_commit = git("-C", repo, "log", "-1", "--format=%H", "--", ja).stdout.strip()
        shown = git("-C", repo, "show", f"{base_commit}:{en}", check=False)
        if shown.returncode != 0:
            # English file did not exist when the ja/ file was last touched —
            # translation predates the source somehow; treat as needing update.
            result["update"].append(en)
            continue
        current = git("-C", repo, "show", f"HEAD:{en}").stdout
        if shown.stdout != current:
            result["update"].append(en)
        else:
            result["ok"].append(en)

    for ja in sorted(ja_files):
        en = ja[len("ja/"):]
        if en not in en_files:
            result["delete"].append(ja)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    total_work = len(result["add"]) + len(result["update"]) + len(result["delete"])
    print(
        f"\n{total_work} file(s) need work "
        f"(add={len(result['add'])}, update={len(result['update'])}, "
        f"delete={len(result['delete'])}), {len(result['ok'])} up to date.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
