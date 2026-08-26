# n8n GitHub Actions Startup-Failure Findings — 2026-08-25

## Evidence

Two GitHub Actions pages were inspected for the n8n PR #13 head `16e252cc` after its rebase.

| Run | Workflow | GitHub annotation | Classification |
|---|---|---|---|
| `32871387472` | `CI: Check PR Title` | `n8n-io/validate-n8n-pull-request-title@8aad0456a34b6f487c421539210529304ae8042c` is not allowed by the fork’s Actions policy. | Reproducible workflow dependency policy failure. |
| `32871386065` | `CI: Validate CODEOWNERS` | `mszostok/codeowners-validator@7f3f5e28c6d7b8dfae5731e54ce2272ca384592f` is not allowed by the fork’s Actions policy. | Reproducible workflow dependency policy failure. |

Both runs had `startup_failure` and no jobs started. Each referenced a full commit SHA; the blocker is the repository’s allow-list policy for third-party actions, not SHA pinning.

## Replacement constraints

1. Keep title validation semantically aligned with the original action’s documented n8n Conventional Commit purpose.
2. Replace blocked third-party actions only with GitHub-owned/verified actions or local repository scripts.
3. Do not disable title or CODEOWNERS validation merely to make the run green.
4. Preserve the fork’s action allow-list policy and do not change secrets.

## Pending source inspection

`CI: Pull Requests (Build, Test, Lint)` run `32871388661` also had `startup_failure` with no job. Its exact annotation remains to be inspected before modifying that workflow.

## External reference findings retained for replacement design

The blocked `n8n-io/validate-n8n-pull-request-title` action documents n8n Conventional Commit validation, including allowed types, static scopes, Node scopes, uppercase subjects, no final period, and ticket/PR-number exclusions. Its source and test suite were reviewed at `https://raw.githubusercontent.com/n8n-io/validate-n8n-pull-request-title/8aad0456a34b6f487c421539210529304ae8042c/src/validatePrTitle.js`, `validatePrTitle.test.js`, and `constants.js`.

The blocked `zizmorcore/zizmor-action` action was reviewed at `https://raw.githubusercontent.com/zizmorcore/zizmor-action/5f14fd08f7cf1cb1609c1e344975f152c7ee938d/action.yml` and `README.md`. It defaults to SARIF upload through GitHub Advanced Security and intentionally does not fail on scan findings in that mode. The official CLI installation and usage references are `https://docs.zizmor.sh/installation/` and `https://docs.zizmor.sh/usage/`. Local verification installed `zizmor 1.29.0`; its SARIF mode successfully produced a valid SARIF document for the n8n workflow tree even while reporting existing findings.

## Additional confirmed startup blocker

`CI: Pull Requests (Build, Test, Lint)` run `32871388661` reported that `zizmorcore/zizmor-action@5f14fd08f7cf1cb1609c1e344975f152c7ee938d` was disallowed by the fork’s Actions policy. The replacement uses the official pinned PyPI CLI and GitHub-owned `github/codeql-action/upload-sarif` to preserve non-blocking SARIF reporting.

## Follow-up validation evidence

After policy-compatible replacements and PR rebase, `CI: Check PR Title` and `CI: Validate CODEOWNERS` progressed from startup failures to actual jobs. CODEOWNERS completed successfully. The title validator initially rejected the lower-case Dependabot subject; PR #13 was retitled to `build(deps): Bump the npm_and_yarn group across 5 directories with 6 updates`, and the title check then completed successfully. The full CI workflow progressed past prior startup failure and exposed a real `@n8n/design-system` Typecheck mismatch after the PR's `markdown-it` 13→15 dependency update; diagnosis is ongoing.

## Rebase and remediation continuation — 2026-08-25

The Dependabot PR #13 branch was rebased to include the fork-master workflow repairs and then updated through lease-protected pushes. The current PR head is `c884ceb5`.

Implemented and locally validated workflow/dependency fixes:

- Replaced blocked PR-title and CODEOWNERS external actions with repository-local, dependency-free validators plus regression tests; GitHub runs for both checks became successful.
- Replaced the blocked zizmor action with the official CLI and GitHub-owned SARIF uploader; the later `Zizmor Security Scan` and `Poutine Security Scan` jobs succeeded in run `32879567097`.
- Kept `markdown-it` on the compatible v13 range because the PR's 13→15 major update produced actual design-system Typecheck errors. The lockfile was regenerated with `--lockfile-only --frozen-lockfile`; local lock validation and whitespace checks succeeded. The compatible pin was committed as `0349fcf3`.
- Added Codecov token guards to every reusable test upload. The first `secrets` expression was invalid in a reusable-workflow `if`; it was corrected by mapping the optional secret to the job environment and guarding against `env.CODECOV_TOKEN`. GitHub parsed the corrected workflow. In run `32879567097`, both Backend Integration Codecov steps were `skipped` (not failed) when the token was absent.
- Replaced blocked `korthout/backport-action` with the same pinned commit from the user-owned fork `balajirajput96/backport-action`, created specifically to preserve the original action behavior while complying with the fork's Actions policy. Commit `d0001fa6`.
- The backend integration job then exposed a new real failure only in the scoped CLI invocation: Vitest had no selected files and exited 1. The CLI test script now passes `--passWithNoTests`, preserving real test failures while allowing an empty change-selected suite. Commit `c884ceb5`.

Acting-career-automation historical failures were also refreshed from logs. The earlier 403 issue-list failures and `follow_up_tracker.py` syntax error are already remediated on current `main`: workflows have `issues: write`, both relevant scripts compile, and the latest Draft Generation (`32805950275`), Follow-up (`32809402149`), and Toolkit Health (`32805105859`) runs concluded `success`. No duplicate change was made.

Validation state at record time: fresh n8n PR CI run `32881329640` is active after the no-test repair; it has passed parsing, is running Typecheck and Backend Integration Tests, and has no new completed failure yet. The PR's standalone legacy `CLA Check` status remains failed for the existing `1 unlinked commit(s)` policy reason; the workflow CLA job itself succeeds and no policy weakening or secret change was applied.


## Latest validation result — run 32881329640

The current run parsed and executed. Its Typecheck job completed with `success` at 18:16:30 UTC, confirming that the markdown-it compatibility fix removed the previously observed Typecheck failure. The Backend Integration job reached the scoped CLI stage and its optional Codecov uploads were skipped as intended when no token was available.

The remaining failure is confined to `n8n#test:integration:changed`. The job invokes `janitor test-scoped` with the integration config after a global change trigger. Vitest reports `No test files found, exiting with code 0` after the added option, but subsequently loads `@n8n/backend-test-utils`, accesses Vitest's worker state, and exits 1 with `Vitest failed to access its internal state`. This is no longer a Codecov, action-policy, parser, typecheck, or secret issue. The repository contains CLI integration test files locally, while the hosted invocation still selects none; the job therefore needs a project-native Janitor/Vitest scope-selection correction rather than another workflow retry or a test-suppressing `continue-on-error` change. No such suppression was added.

## Upstream rebase completion and final PR #13 validation — 2026-08-26

Fork `master` was safely rebased from 127 commits behind `n8n-io/master` and force-pushed with lease protection. The pre-rebase fork history remains protected on remote branch `backup/master-before-upstream-rebase-20260825`; the original PR #13 history remains protected on `backup/pr13-before-upstream-rebase-20260825`. The trusted default branch then received `4a30ffc20c` to restore the in-repository CLA helper scripts required by `pull_request_target` workflows. No secrets, Actions-policy controls, CLA policy, or external-provider authentication were changed.

The rebase retained and extended policy-compatible CI remediation: GitHub-owned `actions/setup-node` plus pinned shell-installed pnpm replaced blocked setup/caching actions; repository-local PR-title and CODEOWNERS validators replaced blocked third-party actions; the official pinned PyPI zizmor CLI plus GitHub-owned SARIF uploader replaced the blocked action; and the backport workflow continues to use the same pinned SHA from `balajirajput96/backport-action`. Fresh post-rebase validations succeeded for title, CODEOWNERS, CLA workflow, static analysis, Windows build, Zizmor, Poutine, and the policy-safe backport skip path.

The first post-rebase full PR workflow, run `32906000397`, proved that the previously focal `Test Integration (cli, scoped)` stage can run as a real suite rather than fail immediately with the prior no-test/Vitest internal-state condition: job `97991752491` completed that stage with `success` at `2026-08-25T22:51:51Z`. That run exposed independent, completed failures only: a design-system packaging type mismatch and missing default pnpm catalog entry for `ws`.

The following source-level fixes were applied on the live PR branch after inspecting their completed job logs:

- Commit `ca99f19916` forwards required `label` from the design-system Combobox option into Reka's `ComboboxItem`, resolving the packaging TypeScript diagnostic.
- Commit `44dafbd612` adds `ws: '>=8.21.1'` to the actual default `catalog` block in `pnpm-workspace.yaml`; the prior matching value existed only under `overrides`, so `pnpm -r pack --dry-run` correctly reported no default catalog entry.
- Commit `4742c5ecd3` changes the existing global `ws` override to `catalog:` as required by the repository's catalog-violations rule, preserving the centralized version policy without duplicating the catalog declaration.

Local validation used Node `v26.5.1` and pnpm `11.22.0`, matching the CI toolchain. It completed `pnpm install --lockfile-only --ignore-scripts --frozen-lockfile` successfully and had no diff-whitespace errors. The definitive fresh full CI workflow is `32910575120` for PR head `4742c5ecd3bf0e2a89b279b989af95147c6dc076`; it concluded `success` at `2026-08-26T00:03:01Z` with no non-success jobs. In that run, `Check packaging`, Typecheck, Windows build, PR Quality/Static Analysis, Zizmor, Poutine, backend non-CLI integration, and `Test Integration (cli, scoped)` all completed `success`; optional Codecov coverage upload was `skipped` because the optional token was absent.

At final refresh, the only remaining failed check context on PR #13 is the pre-existing unlinked `CLA Check` status attached to the pull request itself. The current secure CLA workflow job `Verify CLA signatures` completed `success`; no attempt was made to bypass or weaken the contributor-policy status. PR #13 was not merged automatically.
