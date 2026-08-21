#!/usr/bin/env python3
from __future__ import annotations

from run_continuation_cycle import find_unresolved_failures


def run() -> None:
    out_of_order_runs = [
        {
            "workflowName": "Verify application",
            "status": "completed",
            "conclusion": "success",
            "updatedAt": "2026-08-21T03:49:00Z",
        },
        {
            "workflowName": "Verify application",
            "status": "completed",
            "conclusion": "failure",
            "updatedAt": "2026-08-21T03:07:20Z",
        },
        {
            "workflowName": "Verify application",
            "status": "completed",
            "conclusion": "success",
            "updatedAt": "2026-08-21T03:00:00Z",
        },
    ]
    assert find_unresolved_failures(out_of_order_runs) == []

    unresolved_runs = [
        {
            "workflowName": "Daily repository maintenance",
            "status": "completed",
            "conclusion": "failure",
            "updatedAt": "2026-08-21T03:29:42Z",
        }
    ]
    assert len(find_unresolved_failures(unresolved_runs)) == 1

    print("continuation failure classification tests: PASS")


if __name__ == "__main__":
    run()
