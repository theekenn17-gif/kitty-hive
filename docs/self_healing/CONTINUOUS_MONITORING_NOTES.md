# Continuous Health Monitoring

The self-healing scanner now supports optional continuous monitoring without changing the existing scan and report flow.

## New capability
- `SelfHealingScanner.monitor_repository(report, previous_report=None)` returns subsystem scores, historical comparison data, regression detections, and ChromaDB/local persistence status.
- Monitoring snapshots are stored in ChromaDB when available and fall back to a local JSON file in `memory/database/self_healing_history.json`.
- Regression detection compares the current health score against the previous snapshot and flags subsystem drops larger than 3 points.
