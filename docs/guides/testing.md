# Testing Guide

> Comprehensive guide to testing strategy, requirements, and execution

**Status**: 🚧 To be completed in Phase 1 & 4

## Testing Strategy

Quality Agent maintains high testing standards:
- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Security-Critical Code**: 100% coverage

## Running Tests

```bash
# Run all tests with coverage
pytest --cov=app --cov=agents --cov-report=html

# Run specific test categories
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest tests/security/       # Security tests only

# Run tests in parallel
pytest -n auto

# Run with verbose output
pytest -v
```

## Test Categories

### Unit Tests
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution (<1s per test)
- Located in `tests/unit/`

### Integration Tests
- Test component interactions
- May use real dependencies (with caution)
- Slower execution (1-10s per test)
- Located in `tests/integration/`

### Security Tests
- Test security-critical functionality
- Webhook signature verification
- Input validation
- Located in `tests/security/`

## Writing Tests

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestWebhookReceiver:
    """Test suite for GitHub webhook receiver."""

    async def test_valid_signature_accepted(self, client, valid_payload):
        """Test that webhooks with valid signatures are accepted."""
        # Arrange
        headers = {"X-Hub-Signature-256": "sha256=..."}

        # Act
        response = await client.post(
            "/webhook/github",
            json=valid_payload,
            headers=headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
```

### Fixtures

Common fixtures are defined in `tests/conftest.py`. See [conftest.py](../../tests/conftest.py).

## Coverage Requirements

- Overall: 80% minimum
- Security-critical modules: 100%
- New features: Must maintain or improve coverage

View coverage report:
```bash
open htmlcov/index.html
```

## Test Data

Test data and fixtures will be documented in Phase 1.

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0 (Stub)
