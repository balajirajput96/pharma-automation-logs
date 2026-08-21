#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
for relative in [
    "config/continuation-targets.json",
    "state/continuation-state.json",
]:
    json.loads((ROOT / relative).read_text(encoding="utf-8"))
    print(f"VALID JSON\t{relative}")

workflow = ROOT / ".github/workflows/engineering-continuation.yml"
yaml.safe_load(workflow.read_text(encoding="utf-8"))
print("VALID YAML\t.github/workflows/engineering-continuation.yml")

for relative in [
    "scripts/run_continuation_cycle.py",
    "scripts/validate_continuation_artifacts.py",
]:
    py_compile.compile(str(ROOT / relative), doraise=True)
    print(f"VALID PYTHON\t{relative}")
