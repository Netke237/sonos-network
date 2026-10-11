# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`GLOSSARY.md`** at the repo root: canonical definitions for spatial topology (`Floor`, `Room`, `SwitchPort`, `NetworkDevice`), Wi-Fi spectrum (`AccessPointRadio`, `BssidReading`, `WiFiRoomSurvey`, `SurveyComparisonDelta`), Sonos RF/STP (`ConnectionMode`, `OfdmAniLevel`, `PhyErrorRate`, `SonosMeshLink`, `StpPathCost`, `GhostGroup`, `DpcDucking`, `SonosTelemetrySnapshot`), and diagnostics (`DeviceConnectionEdge`, `HealthGrade`, `RoomDiagnostic`, `SolutionProposal`).
- **`docs/adr/`**: read ADRs that touch the area you're about to work in (`0001` through `0004`).

## File structure

Single-context repo:

```
/
├── GLOSSARY.md
├── AGENTS.md
├── docs/
│   ├── adr/
│   │   ├── 0001-always-on-minipc-fastapi-postgres-stack.md
│   │   ├── 0002-multi-source-network-telemetry-adapters.md
│   │   ├── 0003-room-wifi-survey-and-before-after-delta-model.md
│   │   └── 0004-dual-topology-graph-and-rule-based-diagnostic-engine.md
│   ├── agents/
│   ├── sonos/
│   └── wifi/
├── backend/
└── frontend/
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a spec, a ticket, a schema table, an API model, or a test name), use the term as defined in `GLOSSARY.md`. Don't drift to synonyms the glossary explicitly avoids.

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0001 (always-on Mini PC FastAPI + Postgres stack), but worth reopening because…_
