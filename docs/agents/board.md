# GitHub Board Contract — sonos-network

Used by `k-board-worker` and `k-ticket-coordinator`.

## Status labels on `board-item` issues

| Label | Meaning | Set by | Cleared by |
|---|---|---|---|
| _(none)_ | Ready if no open blocker | — | — |
| `agent-in-progress` | An agent holds the claim and works it | Agent after take | Agent when moving to another status |
| `needs-kenneth` | Waiting for a decision; numbered questions in a comment | Agent | **Kenneth only** |
| `blocked` | Stopped on an unresolvable failure (reason in a comment) | Agent | **Kenneth only** |
| `waiting-merge` | Code audit clean, PR open | Agent | Kenneth (merge closes the item) |

## Hard limits

Without Kenneth's explicit instruction in the active chat, never:
- Merge a PR (`gh pr merge`) or push directly to `main` during a ticket/board build.
- Force-push or rebase an already-pushed branch.
- Delete branches, issues, comments, or labels.
- Self-certify an adversarial audit without spawning an independent auditor subagent.

## Loop per `board-item`

1. Cut branch `board/<phase-kebab>-<hex4>` from `origin/main` (or resume existing branch).
2. Run `/to-spec` (if not yet spec'd) and `/to-tickets` to create vertical tracer-bullet sub-issues with native `blocked_by` edges.
3. For each unblocked frontier ticket: spawn a fresh implementer subagent driving `/tdd`, verify tests pass, push, and close the sub-issue.
4. Merge `origin/main`, run full test suites, and run independent `/code-review` + `bmad-review-adversarial-general` gate audit (max 3 rounds).
5. Open PR (`Closes #<item>`) and swap label `agent-in-progress` -> `waiting-merge`.
