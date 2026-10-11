# Ticket orchestration — sonos-network contract

The user-level `k-ticket-coordinator` skill runs multi-ticket builds here. This file holds the repo-specific values it reads; where it and the skill differ, **this file wins**.

## Who does what

- **Coordinator** = the session Kenneth is talking to. Only it edits `PROJECT_STATE.json`, the tracking issue, and runs audits.
- **Implementer** = one fresh subagent per ticket, driving `/tdd` (red-green-refactor) against deep modules (`/codebase-design`).
- **Gate auditor** = one fresh independent subagent per audit round, applying `bmad-review-adversarial-general` and `/code-review` (Standards + Spec).

## Units

- **Phase** (a `phases[]` entry in `PROJECT_STATE.json`) = the claim, the branch, the **audit target**, the round counter.
- **Ticket** (a GitHub child issue created via `/to-tickets`) = one vertical tracer-bullet slice = one build unit. Tickets are never audit targets.
- One tracking issue per phase.

## Commands

| What | Command |
|---|---|
| Backend tests | `cd backend && pytest` |
| Frontend typecheck | `cd frontend && npm run typecheck` |
| Frontend tests | `cd frontend && npm run test` |

## Audit (`audit_rule`)

- Plan stage: a clean plan/spec round before tickets are cut.
- Code stage: one target, the integrated diff `origin/main..<branch>`, after every build ticket in the phase is closed.
- Cap: three rounds **per stage**. Round $N > 1$ reviews only round $N-1$'s fixes and their interactions.
- Gate: a finding blocks only if it can **display inaccurate RF/telemetry/topology metrics (dBm, ANI, PHY err/s, STP cost, BSSID/AP attribution)**, **corrupt persisted PostgreSQL data**, **violate domain invariants in `AGENTS.md` / `GLOSSARY.md` (e.g., wiring Keller without STP override, burst-scanning VLAN 10 above safe concurrency)**, or **misstate mechanism in a comment**.
- Never merge to `main` without Kenneth's explicit go.
