# Architecture Overview

> System architecture, components, and design decisions

**Status**: 🚧 To be completed in Phase 1

## High-Level Architecture

```
GitHub → ngrok → Quality Agent → CrewAI → Claude → Analysis Report
```

## Components

### 1. Webhook Receiver
- FastAPI application
- Receives GitHub webhook events
- Verifies HMAC signatures
- Triggers agent orchestration

### 2. AI Agents
- CodeAnalyzerAgent
- TestCoverageAgent
- TestPlannerAgent

### 3. GitHub Integration
- Fetches PR diffs
- Accesses repository metadata

### 4. Data Models
- Pydantic models for type safety
- Inter-agent communication
- Report generation

## Technology Stack

- **Web Framework**: FastAPI
- **AI Orchestration**: CrewAI
- **LLM**: Claude (Anthropic)
- **Data Validation**: Pydantic
- **Deployment**: Docker + k3s
- **Package Management**: uv

## Data Flow

Detailed data flow diagrams will be added in Phase 1.

## Design Decisions

See [Architecture Decision Records](../planning/decisions/) for documented decisions.

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0 (Stub)
