#!/usr/bin/env python3
"""Collect a bounded, factual GitHub engineering-continuation snapshot.

This script intentionally never changes target repositories, reruns workflows, changes
secrets, or publishes content. It records evidence so a later reviewed engineering pass
can inspect completed failures before a remediation is applied.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "continuation-targets.json"
STATE_PATH = ROOT / "state" / "continuation-state.json"
HISTORY_PATH = ROOT / "state" / "execution-history.jsonl"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def gh_json(arguments: list[str]) -> tuple[Any | None, str | None]:
    environment = os.environ.copy()
    environment.update({"NO_COLOR": "1", "CLICOLOR": "0", "GH_FORCE_TTY": "0"})
    result = subprocess.run(
        ["gh", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if result.returncode != 0:
        return None, (result.stderr or result.stdout).strip()[-1000:]
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"Invalid GitHub CLI JSON: {exc}"


def find_unresolved_failures(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_success: dict[str, str] = {}
    for run in runs:
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        workflow_name = run.get("workflowName")
        updated_at = run.get("updatedAt", "")
        if workflow_name and updated_at > latest_success.get(workflow_name, ""):
            latest_success[workflow_name] = updated_at

    return [
        run
        for run in runs
        if run.get("status") == "completed"
        and run.get("conclusion") in {"failure", "startup_failure", "timed_out", "action_required"}
        and latest_success.get(run.get("workflowName"), "") <= run.get("updatedAt", "")
    ]


def collect_repository(repo: dict[str, Any]) -> dict[str, Any]:
    name = repo["name"]
    metadata, metadata_error = gh_json(
        ["repo", "view", name, "--json", "defaultBranchRef,updatedAt,isPrivate,url"]
    )
    runs, runs_error = gh_json(
        [
            "run",
            "list",
            "--repo",
            name,
            "--limit",
            "20",
            "--json",
            "databaseId,workflowName,status,conclusion,headSha,createdAt,updatedAt,url",
        ]
    )
    workflow_focus = set(repo.get("workflows", []))
    focused_runs = [
        run for run in (runs or []) if not workflow_focus or run.get("workflowName") in workflow_focus
    ][:10]
    unresolved_failures = find_unresolved_failures(focused_runs)
    return {
        "repository": name,
        "workflowFocus": sorted(workflow_focus),
        "metadata": metadata,
        "metadataError": metadata_error,
        "recentRuns": focused_runs,
        "unresolvedFailures": unresolved_failures,
        "runsError": runs_error,
    }


def run_summary(repositories: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"success": 0, "failure": 0, "queued": 0, "in_progress": 0, "other": 0}
    failure_conclusions = {"failure", "startup_failure", "timed_out", "action_required"}
    for repository in repositories:
        for run in repository["recentRuns"]:
            if run.get("status") != "completed":
                status = run.get("status", "other")
                summary[status if status in summary else "other"] += 1
            elif run.get("conclusion") == "success":
                summary["success"] += 1
            elif run.get("conclusion") not in failure_conclusions:
                summary["other"] += 1
        summary["failure"] += len(repository.get("unresolvedFailures", []))
    return summary


def write_summary(snapshot: dict[str, Any]) -> None:
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return
    totals = snapshot["summary"]
    lines = [
        "## Engineering Continuation Cycle",
        "",
        f"- Cycle: **{snapshot['cycle']}** of **{snapshot['cycleLimit']}**",
        f"- Captured: `{snapshot['capturedAt']}`",
        f"- Recent focused runs: {totals['success']} successful, {totals['failure']} failed, {totals['queued']} queued, {totals['in_progress']} in progress.",
        f"- Collection status: **{snapshot.get('status', 'unknown')}**.",
        "- Safety: target-repository mutation and automatic reruns are disabled; completed failures require log review.",
    ]
    Path(summary_file).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    config = load_json(CONFIG_PATH, {})
    state = load_json(STATE_PATH, {"cycle": 0, "history": []})
    cycle_limit = int(config.get("cycleLimit", 2400))
    current_cycle = int(state.get("cycle", 0))

    if current_cycle >= cycle_limit:
        terminal_state = {
            "cycle": current_cycle,
            "cycleLimit": cycle_limit,
            "capturedAt": now_utc(),
            "status": "cycle_limit_reached",
            "message": "No target repositories were inspected because the configured cycle limit has been reached.",
        }
        write_summary({**terminal_state, "summary": {"success": 0, "failure": 0, "queued": 0, "in_progress": 0, "other": 0}})
        print(json.dumps(terminal_state, indent=2))
        return 0

    repositories = [collect_repository(repo) for repo in config.get("repositories", [])]
    access_errors = [
        repository["repository"]
        for repository in repositories
        if repository["metadataError"] or repository["runsError"]
    ]
    snapshot = {
        "schemaVersion": 1,
        "mission": config.get("mission", "GitHub-centered engineering continuation"),
        "cycle": current_cycle + 1,
        "cycleLimit": cycle_limit,
        "capturedAt": now_utc(),
        "status": "degraded" if access_errors else "healthy",
        "repositoriesWithAccessErrors": access_errors,
        "safety": config.get("safety", {}),
        "repositories": repositories,
        "summary": run_summary(repositories),
    }

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with HISTORY_PATH.open("a", encoding="utf-8") as history:
        history.write(json.dumps(snapshot, sort_keys=True) + "\n")
    write_summary(snapshot)
    print(json.dumps({"cycle": snapshot["cycle"], "summary": snapshot["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
