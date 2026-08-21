# Engineering Continuation Control Plane

This private repository records a bounded, factual continuation history for the connected engineering environment. It preserves evidence; it does not independently change target repositories, modify secrets, publish content, or rerun failed workflows.

## Cycle Behavior

The scheduled workflow executes once per hour. Each cycle reads `state/continuation-state.json`, collects recent workflow metadata from the configured GitHub repositories, writes the latest snapshot to `state/continuation-state.json`, appends the complete record to `state/execution-history.jsonl`, and commits the state update back to this private repository.

The configured maximum is **2,400 cycles**. Once reached, the script records that the limit is reached and performs no target-repository inspection or mutation.

## Failure Handling

A completed failure is preserved as evidence only. A repair is deliberately not automated because safe remediation requires inspection of the failing log, source context, repository policy, and likely regression surface. The remediation procedure is:

1. Inspect the actual GitHub Actions failure and job logs.
2. Classify it as code, workflow, credential, runner, policy, or external-service related.
3. Apply the smallest safe fix only when the cause is reproducible and available permissions allow it.
4. Run the affected validation and record its actual conclusion.
5. Preserve the resulting state in this repository and the engineering log.

## Configuration

`config/continuation-targets.json` holds target repositories, workflow focus, the cycle limit, and safety switches. The current configuration performs read-only data collection from target repositories.

## Local Validation

```bash
python3 scripts/run_continuation_cycle.py
```

The script requires a logged-in GitHub CLI for repository metadata and Actions run inspection. It has no third-party Python dependencies.
