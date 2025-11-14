# Agent Architecture

> AI agent design, prompts, and orchestration

**Status**: 🚧 To be completed in Phase 3

## Overview

Quality Agent uses three specialized AI agents orchestrated by CrewAI:

1. **CodeAnalyzerAgent** - Analyzes code changes
2. **TestCoverageAgent** - Identifies test coverage gaps
3. **TestPlannerAgent** - Creates intelligent test execution plans

## Agent Pipeline

```
PR Event → CodeAnalyzerAgent → TestCoverageAgent → TestPlannerAgent → Report
```

## CodeAnalyzerAgent

### Role
Analyze git diffs and identify changed files, functions, and code patterns.

### Input
- `GitHubWebhookPayload` with PR information
- Git diff from GitHub API

### Output
- List of `CodeChange` models with impact scores

### Prompt
Details will be added in Phase 3.

## TestCoverageAgent

### Role
Identify existing tests and coverage gaps based on code changes.

### Input
- List of `CodeChange` models from CodeAnalyzerAgent

### Output
- List of `TestCoverageGap` models with severity ratings

### Prompt
Details will be added in Phase 3.

## TestPlannerAgent

### Role
Create prioritized, intelligent test execution plans.

### Input
- List of `TestCoverageGap` models from TestCoverageAgent

### Output
- `TestExecutionPlan` with prioritized tests and rationale

### Prompt
Details will be added in Phase 3.

## Agent Orchestration

CrewAI orchestration details will be added in Phase 3.

## Testing Agents

Guide to testing AI agents will be added in Phase 3.

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0 (Stub)
