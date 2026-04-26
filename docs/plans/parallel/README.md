# Parallel Execution Plans

This directory contains work packages that can be assigned to multiple Codex
agents at the same time. A parallel package must include:

- a shared tracker
- one task file per agent
- explicit owned files for each agent
- shared interfaces that all agents must preserve
- merge order and integration rules

Agents should read the shared tracker first, then their own task file. Agents
should not edit files outside their owned file list unless the coordinator
updates the tracker and assigns that ownership explicitly.

The current parallel package is
[macos-live-capture](macos-live-capture/TRACKER.md).
