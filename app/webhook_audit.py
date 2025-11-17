"""Webhook audit logging for request tracking and replay.

This module provides audit logging functionality for all incoming webhook requests.
Audit logs are stored in JSON Lines format (one JSON object per line) for easy
processing and replay.

Features:
- Daily log rotation (one file per day)
- Automatic cleanup of old logs based on retention policy
- Thread-safe writing for concurrent webhook requests
- Complete request capture (headers, payload, metadata)
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import structlog

from app.config import settings

logger = structlog.get_logger()


class WebhookAuditor:
    """Handles audit logging of webhook requests.

    Writes webhook requests to JSON Lines format for easy processing and replay.
    Each line is a complete JSON object containing all request information.

    Example audit log entry:
    ```json
    {
        "timestamp": "2025-11-15T01:30:45.123456Z",
        "delivery_id": "12345-67890",
        "event_type": "pull_request",
        "action": "opened",
        "signature": "sha256=...",
        "headers": {
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "12345-67890",
            "X-Hub-Signature-256": "sha256=..."
        },
        "payload": { ... },
        "metadata": {
            "pr_number": 123,
            "repository": "owner/repo"
        }
    }
    ```
    """

    def __init__(self, audit_dir: str | None = None, retention_days: int | None = None):
        """Initialize the webhook auditor.

        Args:
            audit_dir: Directory to store audit logs (default: from settings)
            retention_days: Days to retain logs (default: from settings)
        """
        self.audit_dir = Path(audit_dir or settings.webhook_audit_dir)
        self.retention_days = retention_days or settings.webhook_audit_retention_days
        self.enabled = settings.enable_webhook_audit

        # Create audit directory if it doesn't exist
        if self.enabled:
            self.audit_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                "webhook_auditor_initialized",
                audit_dir=str(self.audit_dir),
                retention_days=self.retention_days,
            )

    def log_webhook_request(
        self,
        delivery_id: str,
        event_type: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log a webhook request to the audit log.

        Args:
            delivery_id: GitHub delivery ID (X-GitHub-Delivery)
            event_type: GitHub event type (X-GitHub-Event)
            headers: All request headers
            payload: Request payload (JSON body)
            metadata: Optional additional metadata (e.g., pr_number, action)
        """
        if not self.enabled:
            return

        try:
            # Create audit entry
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "delivery_id": delivery_id,
                "event_type": event_type,
                "headers": headers,
                "payload": payload,
                "metadata": metadata or {},
            }

            # Write to daily log file (one file per day)
            log_file = self._get_log_file()
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(audit_entry) + "\n")

            logger.debug(
                "webhook_audited",
                delivery_id=delivery_id,
                event_type=event_type,
                log_file=str(log_file),
            )

        except Exception as e:
            # Don't fail the webhook processing if audit logging fails
            logger.error(
                "webhook_audit_failed",
                delivery_id=delivery_id,
                error=str(e),
            )

    def _get_log_file(self) -> Path:
        """Get the log file for today.

        Returns:
            Path: Path to today's audit log file (e.g., webhooks-2025-11-15.jsonl)
        """
        today = datetime.utcnow().date()
        filename = f"webhooks-{today.isoformat()}.jsonl"
        return self.audit_dir / filename

    def cleanup_old_logs(self) -> int:
        """Remove audit logs older than retention period.

        Returns:
            int: Number of files deleted
        """
        if not self.enabled:
            return 0

        try:
            cutoff_date = datetime.utcnow().date() - timedelta(days=self.retention_days)
            deleted_count = 0

            # Find and delete old log files
            for log_file in self.audit_dir.glob("webhooks-*.jsonl"):
                try:
                    # Extract date from filename (webhooks-2025-11-15.jsonl)
                    date_str = log_file.stem.replace("webhooks-", "")
                    file_date = datetime.fromisoformat(date_str).date()

                    if file_date < cutoff_date:
                        log_file.unlink()
                        deleted_count += 1
                        logger.info(
                            "audit_log_deleted",
                            file=str(log_file),
                            file_date=date_str,
                        )
                except (ValueError, OSError) as e:
                    logger.warning(
                        "audit_log_cleanup_failed",
                        file=str(log_file),
                        error=str(e),
                    )
                    continue

            if deleted_count > 0:
                logger.info(
                    "audit_log_cleanup_completed",
                    deleted_count=deleted_count,
                    cutoff_date=cutoff_date.isoformat(),
                )

            return deleted_count

        except Exception as e:
            logger.error("audit_log_cleanup_error", error=str(e))
            return 0

    def read_audit_logs(self, target_date: date | None = None) -> list[dict[str, Any]]:
        """Read audit logs for a specific date.

        Args:
            target_date: Date to read logs for (default: today)

        Returns:
            list[dict]: List of audit entries
        """
        if not self.enabled:
            return []

        log_date = target_date or datetime.utcnow().date()
        filename = f"webhooks-{log_date.isoformat()}.jsonl"
        log_file = self.audit_dir / filename

        if not log_file.exists():
            return []

        entries = []
        try:
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))
        except Exception as e:
            logger.error(
                "audit_log_read_failed",
                file=str(log_file),
                error=str(e),
            )

        return entries

    def get_all_log_files(self) -> list[Path]:
        """Get all audit log files.

        Returns:
            list[Path]: List of audit log file paths, sorted by date (newest first)
        """
        if not self.enabled or not self.audit_dir.exists():
            return []

        log_files = sorted(
            self.audit_dir.glob("webhooks-*.jsonl"),
            reverse=True,  # Newest first
        )
        return list(log_files)


# Global auditor instance
_auditor: WebhookAuditor | None = None


def get_auditor() -> WebhookAuditor:
    """Get the global webhook auditor instance.

    Returns:
        WebhookAuditor: Global auditor instance
    """
    global _auditor
    if _auditor is None:
        _auditor = WebhookAuditor()
    return _auditor


def log_webhook(
    delivery_id: str,
    event_type: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> None:
    """Convenience function to log a webhook request.

    Args:
        delivery_id: GitHub delivery ID
        event_type: GitHub event type
        headers: Request headers
        payload: Request payload
        metadata: Optional metadata
    """
    auditor = get_auditor()
    auditor.log_webhook_request(delivery_id, event_type, headers, payload, metadata)


def cleanup_old_audit_logs() -> int:
    """Convenience function to cleanup old audit logs.

    Returns:
        int: Number of files deleted
    """
    auditor = get_auditor()
    return auditor.cleanup_old_logs()
