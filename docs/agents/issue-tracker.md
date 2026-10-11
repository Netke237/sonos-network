# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues on `Netke237/sonos-network`. Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc or `--body-file` for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

The repo is `Netke237/sonos-network` (public); `gh` infers it inside a clone.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Coordinated builds (`k-ticket-coordinator` & `k-board-worker`)

Multi-ticket builds are coordinated by the user-level `k-ticket-coordinator` and `k-board-worker` skills under one **tracking issue**. Repo-specific rules: `docs/agents/ticket-orchestration.md` and `docs/agents/board.md`.

Labels:

| Label | Meaning |
|---|---|
| `board-item` | Phase-level work item on the GitHub Board Queue. |
| `tracking` | The coordination issue for a phase. Kenneth reads this; only the coordinator edits it. |
| `ready-for-agent` | Child ticket with every blocker closed, waiting for an implementer. |
| `agent-in-progress` | An implementer or board worker is working it. |
| `needs-kenneth` | Waiting for a decision from Kenneth. |
| `waiting-merge` | Code audit clean, PR open. |
| `blocked` | Stopped; the reason is in a comment and under "Needs Kenneth" in the tracking issue. |
| `<phase-id-kebab>` | Groups every issue of one phase, e.g. `phase-1-core-telemetry`. |

- **Sub-issue link** (child under the tracking issue): `gh api --method POST repos/Netke237/sonos-network/issues/<tracker>/sub_issues -F sub_issue_id=<child-db-id>`.
- **Blocked-by edge**: `gh api --method POST repos/Netke237/sonos-network/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`.
- `<…-db-id>` is the numeric database id: `gh api repos/Netke237/sonos-network/issues/<n> --jq .id` (not the `#number`, not `node_id`).
- If either endpoint is refused, the `Part of #<tracker>` / `Blocked by: #…` lines at the top of each child body are the record; note the fallback in the tracking issue.

## When a skill says "publish to the issue tracker"

Create a GitHub issue on `Netke237/sonos-network`.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue labelled `wayfinder:map`, with **child** issues as tickets linked via GitHub sub-issues and native `blocked_by` dependencies.
