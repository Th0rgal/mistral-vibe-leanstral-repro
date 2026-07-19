#!/usr/bin/env python3
"""Create three isolated public benchmark worktrees pinned to the captured SHA."""
from __future__ import annotations

import json
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = ROOT / "workspaces"
BASE = WORKSPACES / "benchmark-base"
META = json.loads((ROOT / "examples" / "tasks.json").read_text())


def run(*args: str, cwd: Path | None = None) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=cwd, check=True)


def main() -> int:
    WORKSPACES.mkdir(parents=True, exist_ok=True)
    if not BASE.exists():
        run("git", "clone", "--filter=blob:none", META["benchmark_repo"], str(BASE))
    run("git", "fetch", "origin", META["benchmark_sha"], cwd=BASE)
    run("git", "checkout", "--detach", META["benchmark_sha"], cwd=BASE)
    for task in META["tasks"]:
        slug = task["slug"]
        dest = WORKSPACES / slug
        if dest.exists():
            print(f"= {dest} already exists; leaving it untouched")
            continue
        run("git", "worktree", "add", "--detach", str(dest), META["benchmark_sha"], cwd=BASE)
        harness = dest / "harness"
        harness.mkdir(exist_ok=True)
        shutil.copyfile(ROOT / task["task_summary"], harness / "TASK_SUMMARY.md")
        check = harness / "check.sh"
        check.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\n"
            f"lake env lean {task['editable_file']}\n"
        )
        check.chmod(check.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"prepared {slug}: {dest}")
    print("Optional dependency cache: cd workspaces/<slug> && lake exe cache get")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
