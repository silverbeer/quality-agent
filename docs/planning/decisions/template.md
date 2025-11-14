# ADR-XXX: Title of Decision

**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Date**: YYYY-MM-DD
**Deciders**: [List of people involved in the decision]

## Context

Describe the context and problem statement. What is the issue that we're addressing?

Include:
- What forces are at play (technical, political, social, project-related)?
- What are the constraints?
- What are the assumptions?

## Decision

State the decision that was made.

Example: "We will use FastAPI for the web framework."

## Rationale

Explain why this decision was made. What were the key factors that led to this choice?

Include:
- Pros and cons of the chosen option
- Pros and cons of alternatives considered
- Why this option is best given the context

## Consequences

Describe the resulting context after applying the decision.

Include:
- Positive consequences (benefits)
- Negative consequences (drawbacks, technical debt)
- Neutral consequences (changes that are neither clearly positive nor negative)

## Alternatives Considered

### Alternative 1: [Name]
**Pros**:
- Pro 1
- Pro 2

**Cons**:
- Con 1
- Con 2

**Why rejected**: Brief explanation

### Alternative 2: [Name]
**Pros**:
- Pro 1

**Cons**:
- Con 1

**Why rejected**: Brief explanation

## Implementation Notes

- Implementation detail 1
- Implementation detail 2
- Migration path (if applicable)

## References

- Link to relevant documentation
- Link to discussions
- Link to related ADRs

---

## Example ADR

# ADR-001: Use CrewAI for Agent Orchestration

**Status**: Accepted
**Date**: 2025-11-14
**Deciders**: Development Team

## Context

We need an AI agent orchestration framework to coordinate multiple specialized agents (code analysis, test coverage, test planning). The framework should:
- Support sequential agent execution with data passing
- Work with Claude (Anthropic) LLMs
- Be actively maintained and production-ready
- Have a reasonable learning curve

## Decision

We will use CrewAI for agent orchestration.

## Rationale

CrewAI provides:
- Native support for Anthropic Claude
- Built-in agent-to-agent communication with structured outputs
- Pydantic model support for type-safe data passing
- Active development and community
- Good documentation

## Consequences

**Positive**:
- Faster development with built-in agent patterns
- Type-safe agent communication
- Good Claude integration

**Negative**:
- New dependency to learn and maintain
- Potential vendor lock-in to CrewAI patterns
- May need workarounds for advanced use cases

**Neutral**:
- Need to learn CrewAI API and patterns

## Alternatives Considered

### LangChain
**Pros**: Mature, well-documented, large ecosystem
**Cons**: More complex, heavier dependency, less focused on agent orchestration
**Why rejected**: Overkill for our use case, steeper learning curve

### Custom Solution
**Pros**: Full control, no dependencies
**Cons**: Significant development effort, need to solve solved problems
**Why rejected**: Would delay MVP significantly

## Implementation Notes

- Start with basic CrewAI patterns in Phase 3
- Evaluate advanced features as needed
- Keep agent logic loosely coupled to allow framework migration if needed

## References

- [CrewAI Documentation](https://docs.crewai.com/)
- [CrewAI GitHub](https://github.com/joaomdmoura/crewAI)
