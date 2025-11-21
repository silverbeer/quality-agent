"""CrewAI processor for analyzing pull requests.

This runs as a Fargate task, triggered by SQS messages.
It reads the full event from S3 and runs the CrewAI analysis pipeline.
"""

import json
import logging
import os
import sys

import boto3
import structlog

# Add parent directory to path to import agents and models
sys.path.insert(0, "/app")

from agents.crew import QualityAnalysisCrew
from models.github import PullRequestWebhookPayload

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Environment variables
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
EVENTS_BUCKET = os.environ["EVENTS_BUCKET"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

# Initialize AWS clients
s3_client = boto3.client("s3", region_name=AWS_REGION)


def get_event_from_s3(s3_key: str) -> dict:
    """Retrieve full event payload from S3.

    Args:
        s3_key: S3 object key

    Returns:
        Event data dictionary
    """
    response = s3_client.get_object(Bucket=EVENTS_BUCKET, Key=s3_key)
    return json.loads(response["Body"].read().decode("utf-8"))


def process_pull_request(message: dict) -> None:
    """Process a pull request event with CrewAI.

    Args:
        message: SQS message with event metadata
    """
    delivery_id = message.get("delivery_id")
    s3_key = message.get("s3_key")
    action = message.get("action")

    logger.info(
        "processing_pull_request",
        delivery_id=delivery_id,
        action=action,
        pr_number=message.get("pr_number"),
        repository=message.get("repository")
    )

    # Only process opened and synchronized actions
    if action not in ["opened", "synchronize"]:
        logger.info(
            "skipping_action",
            action=action,
            reason="Only processing opened/synchronize actions"
        )
        return

    # Get full event from S3
    event_data = get_event_from_s3(s3_key)
    payload = event_data.get("payload", {})

    # Parse into Pydantic model
    try:
        webhook_payload = PullRequestWebhookPayload(**payload)
    except Exception as e:
        logger.error(
            "payload_parse_error",
            error=str(e),
            delivery_id=delivery_id
        )
        return

    # Run CrewAI analysis
    try:
        crew = QualityAnalysisCrew()
        result = crew.analyze(webhook_payload)

        logger.info(
            "analysis_complete",
            delivery_id=delivery_id,
            pr_number=message.get("pr_number"),
            repository=message.get("repository"),
            code_changes=len(result.code_changes) if result.code_changes else 0,
            coverage_gaps=len(result.coverage_gaps) if result.coverage_gaps else 0,
            recommendations=len(result.test_plan.recommendations) if result.test_plan else 0
        )

        # Log the full analysis result
        logger.info(
            "analysis_result",
            delivery_id=delivery_id,
            result=result.model_dump() if hasattr(result, "model_dump") else str(result)
        )

    except Exception as e:
        logger.error(
            "analysis_error",
            error=str(e),
            delivery_id=delivery_id,
            pr_number=message.get("pr_number")
        )
        raise


def main():
    """Main entry point for the processor."""
    # Get message from environment (passed by Fargate task override)
    message_body = os.environ.get("MESSAGE_BODY")

    if not message_body:
        logger.error("no_message", error="MESSAGE_BODY environment variable not set")
        sys.exit(1)

    try:
        message = json.loads(message_body)
    except json.JSONDecodeError as e:
        logger.error("invalid_message", error=str(e))
        sys.exit(1)

    event_type = message.get("event_type")
    delivery_id = message.get("delivery_id")

    logger.info(
        "processor_started",
        event_type=event_type,
        delivery_id=delivery_id,
        environment=ENVIRONMENT
    )

    if event_type == "pull_request":
        process_pull_request(message)
    else:
        logger.info(
            "skipping_event",
            event_type=event_type,
            reason="Only processing pull_request events"
        )

    logger.info("processor_complete", delivery_id=delivery_id)


if __name__ == "__main__":
    main()
