"""Tests for webhook audit logging functionality."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.webhook_audit import WebhookAuditor, cleanup_old_audit_logs, get_auditor, log_webhook


class TestWebhookAuditor:
    """Test suite for WebhookAuditor class."""

    @pytest.fixture
    def temp_audit_dir(self) -> Path:
        """Create a temporary directory for audit logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def auditor(self, temp_audit_dir: Path) -> WebhookAuditor:
        """Create a WebhookAuditor instance for testing."""
        return WebhookAuditor(audit_dir=str(temp_audit_dir), retention_days=7)

    def test_auditor_initializes_directory(self, temp_audit_dir: Path) -> None:
        """Test that auditor creates the audit directory on initialization."""
        # Arrange
        audit_dir = temp_audit_dir / "webhooks"
        assert not audit_dir.exists()

        # Act
        WebhookAuditor(audit_dir=str(audit_dir))

        # Assert
        assert audit_dir.exists()
        assert audit_dir.is_dir()

    def test_log_webhook_request_creates_file(self, auditor: WebhookAuditor) -> None:
        """Test that logging a webhook creates a log file."""
        # Arrange
        delivery_id = "test-delivery-123"
        event_type = "pull_request"
        headers = {"X-GitHub-Event": "pull_request"}
        payload = {"action": "opened", "number": 123}

        # Act
        auditor.log_webhook_request(delivery_id, event_type, headers, payload)

        # Assert
        log_files = list(auditor.audit_dir.glob("webhooks-*.jsonl"))
        assert len(log_files) == 1

    def test_log_webhook_request_writes_valid_json(self, auditor: WebhookAuditor) -> None:
        """Test that logged webhook data is valid JSON."""
        # Arrange
        delivery_id = "test-delivery-456"
        event_type = "push"
        headers = {"X-GitHub-Event": "push", "X-GitHub-Delivery": delivery_id}
        payload = {"ref": "refs/heads/main", "commits": []}
        metadata = {"repository": "owner/repo"}

        # Act
        auditor.log_webhook_request(delivery_id, event_type, headers, payload, metadata)

        # Assert
        log_file = auditor._get_log_file()
        with log_file.open() as f:
            line = f.readline()
            data = json.loads(line)  # Should not raise
            assert data["delivery_id"] == delivery_id
            assert data["event_type"] == event_type
            assert data["headers"] == headers
            assert data["payload"] == payload
            assert data["metadata"] == metadata
            assert "timestamp" in data

    def test_log_webhook_request_appends_to_existing_file(
        self, auditor: WebhookAuditor
    ) -> None:
        """Test that multiple webhooks are appended to the same daily file."""
        # Arrange & Act
        for i in range(3):
            auditor.log_webhook_request(
                delivery_id=f"delivery-{i}",
                event_type="pull_request",
                headers={"X-GitHub-Event": "pull_request"},
                payload={"number": i},
            )

        # Assert
        log_file = auditor._get_log_file()
        with log_file.open() as f:
            lines = f.readlines()
        assert len(lines) == 3

        # Verify all entries are valid JSON
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data["delivery_id"] == f"delivery-{i}"
            assert data["payload"]["number"] == i

    def test_read_audit_logs(self, auditor: WebhookAuditor) -> None:
        """Test reading audit logs for a specific date."""
        # Arrange
        auditor.log_webhook_request(
            delivery_id="test-1",
            event_type="pull_request",
            headers={},
            payload={"number": 1},
        )
        auditor.log_webhook_request(
            delivery_id="test-2",
            event_type="pull_request",
            headers={},
            payload={"number": 2},
        )

        # Act
        entries = auditor.read_audit_logs()

        # Assert
        assert len(entries) == 2
        assert entries[0]["delivery_id"] == "test-1"
        assert entries[1]["delivery_id"] == "test-2"

    def test_read_audit_logs_for_missing_date(self, auditor: WebhookAuditor) -> None:
        """Test reading audit logs for a date with no logs."""
        # Arrange
        past_date = datetime.utcnow().date() - timedelta(days=10)

        # Act
        entries = auditor.read_audit_logs(target_date=past_date)

        # Assert
        assert entries == []

    def test_cleanup_old_logs(self, auditor: WebhookAuditor, temp_audit_dir: Path) -> None:
        """Test that old audit logs are deleted."""
        # Arrange
        today = datetime.utcnow().date()
        old_date = today - timedelta(days=10)
        recent_date = today - timedelta(days=3)

        # Create old log file
        old_file = temp_audit_dir / f"webhooks-{old_date.isoformat()}.jsonl"
        old_file.write_text('{"test": "old"}\n')

        # Create recent log file
        recent_file = temp_audit_dir / f"webhooks-{recent_date.isoformat()}.jsonl"
        recent_file.write_text('{"test": "recent"}\n')

        # Create today's log file
        today_file = temp_audit_dir / f"webhooks-{today.isoformat()}.jsonl"
        today_file.write_text('{"test": "today"}\n')

        # Act
        deleted_count = auditor.cleanup_old_logs()

        # Assert
        assert deleted_count == 1  # Only the 10-day-old file should be deleted
        assert not old_file.exists()
        assert recent_file.exists()
        assert today_file.exists()

    def test_cleanup_old_logs_with_no_old_files(self, auditor: WebhookAuditor) -> None:
        """Test cleanup when there are no old files to delete."""
        # Arrange
        auditor.log_webhook_request(
            delivery_id="test",
            event_type="pull_request",
            headers={},
            payload={},
        )

        # Act
        deleted_count = auditor.cleanup_old_logs()

        # Assert
        assert deleted_count == 0

    def test_get_all_log_files(
        self, auditor: WebhookAuditor, temp_audit_dir: Path
    ) -> None:
        """Test getting all audit log files."""
        # Arrange
        dates = [
            datetime.utcnow().date() - timedelta(days=i)
            for i in range(3)
        ]
        for date in dates:
            file = temp_audit_dir / f"webhooks-{date.isoformat()}.jsonl"
            file.write_text('{"test": "data"}\n')

        # Act
        log_files = auditor.get_all_log_files()

        # Assert
        assert len(log_files) == 3
        # Should be sorted newest first
        assert log_files[0].name > log_files[1].name
        assert log_files[1].name > log_files[2].name

    def test_auditor_disabled_does_not_log(self, temp_audit_dir: Path) -> None:
        """Test that auditor does not log when disabled."""
        # Arrange
        auditor = WebhookAuditor(audit_dir=str(temp_audit_dir), retention_days=7)
        auditor.enabled = False

        # Act
        auditor.log_webhook_request(
            delivery_id="test",
            event_type="pull_request",
            headers={},
            payload={},
        )

        # Assert
        log_files = list(temp_audit_dir.glob("*.jsonl"))
        assert len(log_files) == 0

    def test_log_webhook_request_handles_errors_gracefully(
        self, auditor: WebhookAuditor
    ) -> None:
        """Test that logging errors don't crash the application."""
        # Arrange
        # Make audit_dir invalid by setting it to a file instead of directory
        auditor.audit_dir = auditor._get_log_file()
        auditor.audit_dir.write_text("invalid")

        # Act - should not raise exception
        auditor.log_webhook_request(
            delivery_id="test",
            event_type="pull_request",
            headers={},
            payload={},
        )

        # Assert - test passes if no exception is raised


class TestConvenienceFunctions:
    """Test suite for module-level convenience functions."""

    def test_get_auditor_returns_singleton(self) -> None:
        """Test that get_auditor returns the same instance."""
        # Act
        auditor1 = get_auditor()
        auditor2 = get_auditor()

        # Assert
        assert auditor1 is auditor2

    def test_log_webhook_uses_global_auditor(self, tmp_path: Path) -> None:
        """Test that log_webhook uses the global auditor instance."""
        # Arrange
        import app.webhook_audit

        # Create and set a test auditor
        test_auditor = WebhookAuditor(audit_dir=str(tmp_path), retention_days=7)
        app.webhook_audit._auditor = test_auditor

        # Act
        log_webhook(
            delivery_id="test-123",
            event_type="pull_request",
            headers={"X-GitHub-Event": "pull_request"},
            payload={"number": 123},
            metadata={"test": "data"},
        )

        # Assert
        log_files = list(tmp_path.glob("webhooks-*.jsonl"))
        assert len(log_files) == 1

    def test_cleanup_old_audit_logs_uses_global_auditor(
        self, tmp_path: Path
    ) -> None:
        """Test that cleanup_old_audit_logs uses the global auditor."""
        # Arrange
        import app.webhook_audit

        # Create and set a test auditor
        test_auditor = WebhookAuditor(audit_dir=str(tmp_path), retention_days=7)
        app.webhook_audit._auditor = test_auditor

        # Create an old log file
        old_date = datetime.utcnow().date() - timedelta(days=10)
        old_file = tmp_path / f"webhooks-{old_date.isoformat()}.jsonl"
        old_file.write_text('{"test": "old"}\n')

        # Act
        deleted_count = cleanup_old_audit_logs()

        # Assert
        assert deleted_count == 1
        assert not old_file.exists()


class TestIntegration:
    """Integration tests for webhook audit logging."""

    def test_full_webhook_audit_flow(self, tmp_path: Path) -> None:
        """Test complete flow: log webhook, read it back, cleanup old logs."""
        # Arrange
        auditor = WebhookAuditor(audit_dir=str(tmp_path), retention_days=3)

        # Act - Log webhook
        auditor.log_webhook_request(
            delivery_id="integration-test-123",
            event_type="pull_request",
            headers={
                "X-GitHub-Event": "pull_request",
                "X-GitHub-Delivery": "integration-test-123",
                "X-Hub-Signature-256": "sha256=test",
            },
            payload={
                "action": "opened",
                "number": 456,
                "pull_request": {"title": "Test PR"},
            },
            metadata={
                "pr_number": 456,
                "repository": "owner/repo",
            },
        )

        # Act - Read it back
        entries = auditor.read_audit_logs()

        # Assert
        assert len(entries) == 1
        entry = entries[0]
        assert entry["delivery_id"] == "integration-test-123"
        assert entry["event_type"] == "pull_request"
        assert entry["payload"]["number"] == 456
        assert entry["metadata"]["pr_number"] == 456

        # Act - Cleanup (should not delete today's log)
        deleted = auditor.cleanup_old_logs()
        assert deleted == 0

        # Verify log still exists
        entries_after_cleanup = auditor.read_audit_logs()
        assert len(entries_after_cleanup) == 1
