from pathlib import Path

workflow = Path('.github/workflows/engineering-continuation.yml').read_text()
required = (
    'shell: bash',
    'set -euo pipefail',
    'git fetch origin main',
    'git rebase origin/main',
    'for attempt in 1 2 3; do',
    'git push origin HEAD:main',
    'git rebase --abort',
    'State push failed after bounded retries.',
)
for fragment in required:
    if fragment not in workflow:
        raise SystemExit(f'missing workflow fragment: {fragment}')
if 'git push\n' in workflow:
    raise SystemExit('unbounded direct git push remains')
credential_markers = ('github' + '_pat_', 'gh' + 'p_', 'BEGIN RSA ' + 'PRIVATE KEY')
if any(marker in workflow for marker in credential_markers):
    raise SystemExit('credential-like material found')
print('engineering_continuation_workflow=valid')
print('bounded_retries=3')
print('conflict_behavior=fail_safe')
print('secret_scan=passed')
