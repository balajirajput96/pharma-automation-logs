from pathlib import Path

workflow = Path('.github/workflows/engineering-continuation.yml').read_text()
required = (
    'shell: bash',
    'set -euo pipefail',
    'for attempt in 1 2 3; do',
    'git fetch origin main',
    'git reset --hard origin/main',
    'python3 scripts/run_continuation_cycle.py',
    'git push origin HEAD:main',
    'State push failed after bounded retries.',
)
for fragment in required:
    if fragment not in workflow:
        raise SystemExit(f'missing workflow fragment: {fragment}')
commit_block = workflow.split('      - name: Commit state record', 1)[1]
if 'git rebase' in commit_block:
    raise SystemExit('state writer must not rebase generated state')
if commit_block.index('git fetch origin main') > commit_block.index('git reset --hard origin/main'):
    raise SystemExit('latest main must be checked out before regeneration')
if commit_block.index('git reset --hard origin/main') > commit_block.index('python3 scripts/run_continuation_cycle.py'):
    raise SystemExit('state must be regenerated after resetting to latest main')
if commit_block.index('python3 scripts/run_continuation_cycle.py') > commit_block.index('git add state/'):
    raise SystemExit('generated state must be created before staging')
if 'git push\n' in workflow:
    raise SystemExit('unbounded direct git push remains')
credential_markers = ('github' + '_pat_', 'gh' + 'p_', 'BEGIN RSA ' + 'PRIVATE KEY')
if any(marker in workflow for marker in credential_markers):
    raise SystemExit('credential-like material found')
print('engineering_continuation_workflow=valid')
print('bounded_retries=3')
print('conflict_behavior=regenerate_after_refetch')
print('secret_scan=passed')
