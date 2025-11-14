"""GitHub webhook receiver with signature verification.

This module handles incoming GitHub webhooks, verifies their authenticity using
HMAC SHA-256 signatures, and processes pull request events.

Security:
    - All webhooks MUST have valid GitHub signatures
    - Constant-time comparison prevents timing attacks
    - Invalid signatures are rejected with 401 Unauthorized

Reference: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
"""

import hmac
import hashlib

from fastapi import BackgroundTasks, HTTPException, Request, status
import structlog

from agents import analyze_pull_request
from app.config import settings
from models.github import PullRequestWebhookPayload, PushWebhookPayload, WebhookDeliveryInfo

logger = structlog.get_logger(__name__)


class WebhookVerificationError(Exception):
    """Raised when webhook signature verification fails."""

    pass


def verify_github_signature(
    payload_body: bytes,
    signature_header: str,
    secret: str,
) -> bool:
    """Verify GitHub webhook signature using HMAC SHA-256.

    GitHub signs webhook payloads with HMAC SHA-256 using the webhook secret.
    The signature is sent in the X-Hub-Signature-256 header as "sha256=<hash>".

    Args:
        payload_body: Raw request body bytes
        signature_header: Value of X-Hub-Signature-256 header
        secret: Webhook secret (from configuration)

    Returns:
        bool: True if signature is valid, False otherwise

    Example:
        ```python
        is_valid = verify_github_signature(
            payload_body=await request.body(),
            signature_header=request.headers["X-Hub-Signature-256"],
            secret=settings.github_webhook_secret,
        )
        ```

    Security:
        Uses constant-time comparison (hmac.compare_digest) to prevent timing attacks.
    """
    if not signature_header.startswith("sha256="):
        logger.warning("invalid_signature_format", header=signature_header)
        return False

    # Extract hash from header (remove "sha256=" prefix)
    received_signature = signature_header[7:]

    # Compute expected signature
    expected_signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(received_signature, expected_signature)

    if not is_valid:
        logger.warning(
            "signature_verification_failed",
            received=received_signature[:16] + "...",  # Log partial hash
            expected=expected_signature[:16] + "...",
        )

    return is_valid


async def run_pr_analysis(
    payload: PullRequestWebhookPayload,
    delivery_id: str,
) -> None:
    """Run PR analysis in background.

    This function runs the CrewAI agent pipeline asynchronously.

    Args:
        payload: Validated webhook payload
        delivery_id: Webhook delivery ID for tracking
    """
    try:
        logger.info(
            "analysis_starting",
            pr_number=payload.number,
            repository=payload.repo_full_name,
            delivery_id=delivery_id,
        )

        # Run the analysis pipeline
        report = analyze_pull_request(
            webhook_payload=payload,
            github_token=settings.github_token,
        )

        # Log results
        logger.info(
            "analysis_completed",
            pr_number=payload.number,
            repository=payload.repo_full_name,
            status=report.status,
            code_changes=len(report.code_changes),
            coverage_gaps=len(report.coverage_gaps),
            test_recommendations=report.test_plan.total_tests,
            critical_tests=len(report.test_plan.critical_tests),
            risk_score=report.risk_score,
            duration_seconds=report.duration_seconds,
        )

        # Log summary for easy viewing
        summary = report.to_summary_dict()
        logger.info("analysis_summary", **summary)

        # TODO: Phase 4 - Store results in database
        # TODO: Phase 5 - Post results as PR comment or webhook callback

    except Exception as e:
        logger.error(
            "analysis_failed",
            pr_number=payload.number,
            repository=payload.repo_full_name,
            error=str(e),
            delivery_id=delivery_id,
        )


async def process_pull_request_webhook(
    payload: PullRequestWebhookPayload,
    delivery_info: WebhookDeliveryInfo,
    background_tasks: BackgroundTasks,
) -> dict[str, str | int]:
    """Process a validated pull request webhook.

    This function is called after signature verification succeeds.
    It determines if the PR event requires analysis and triggers
    the CrewAI agent pipeline in the background.

    Args:
        payload: Validated webhook payload
        delivery_info: Webhook delivery metadata
        background_tasks: FastAPI background tasks for async processing

    Returns:
        dict: Response data including status and message

    Example:
        ```python
        response = await process_pull_request_webhook(payload, delivery_info, bg_tasks)
        # {"status": "processing", "message": "Analysis started", "pr_number": 123}
        ```
    """
    logger.info(
        "webhook_received",
        event_type="pull_request",
        action=payload.action,
        pr_number=payload.number,
        repo=payload.repo_full_name,
        delivery_id=delivery_info.delivery_id,
    )

    # Check if this event requires analysis
    if not payload.is_actionable:
        logger.info(
            "webhook_ignored",
            action=payload.action,
            pr_number=payload.number,
            reason="Action does not require analysis",
        )
        return {
            "status": "ignored",
            "message": f"Action '{payload.action}' does not require analysis",
            "pr_number": payload.number,
        }

    # Log PR details for analysis
    logger.info(
        "pr_analysis_requested",
        pr_number=payload.number,
        pr_title=payload.pull_request.title,
        pr_url=payload.pr_url,
        head_branch=payload.pull_request.head.ref,
        base_branch=payload.pull_request.base.ref,
        head_sha=payload.pull_request.head.sha,
        files_changed=payload.pull_request.changed_files,
        additions=payload.pull_request.additions,
        deletions=payload.pull_request.deletions,
    )

    # Trigger CrewAI analysis in background
    background_tasks.add_task(
        run_pr_analysis,
        payload=payload,
        delivery_id=delivery_info.delivery_id,
    )

    logger.info(
        "analysis_queued",
        pr_number=payload.number,
        delivery_id=delivery_info.delivery_id,
    )

    return {
        "status": "processing",
        "message": "Pull request analysis started",
        "pr_number": payload.number,
        "action": payload.action,
        "delivery_id": delivery_info.delivery_id,
    }


async def process_push_webhook(
    payload: PushWebhookPayload,
    delivery_info: WebhookDeliveryInfo,
) -> dict[str, str | int]:
    """Process a validated push webhook.

    This function is called after signature verification succeeds for push events.
    It logs the push details and (in future phases) can trigger analysis.

    Args:
        payload: Validated webhook payload
        delivery_info: Webhook delivery metadata

    Returns:
        dict: Response data including status and message

    Example:
        ```python
        response = await process_push_webhook(payload, delivery_info)
        # {"status": "accepted", "message": "Push received", "commits": 3}
        ```
    """
    logger.info(
        "webhook_received",
        event_type="push",
        branch=payload.branch_name,
        repo=payload.repo_full_name,
        delivery_id=delivery_info.delivery_id,
        commits=payload.commit_count,
        before=payload.before[:8],
        after=payload.after[:8],
    )

    # Only process branch pushes (not tags)
    if not payload.is_branch_push:
        logger.info(
            "webhook_ignored",
            ref=payload.ref,
            reason="Not a branch push (possibly a tag)",
        )
        return {
            "status": "ignored",
            "message": f"Ref '{payload.ref}' is not a branch",
        }

    # Log commit details
    logger.info(
        "push_details",
        branch=payload.branch_name,
        commit_count=payload.commit_count,
        compare_url=str(payload.compare),
    )

    # Phase 3: This is where we'll trigger analysis
    # For now, just log and return acceptance
    logger.info(
        "push_acknowledged",
        branch=payload.branch_name,
        commits=payload.commit_count,
        note="Analysis not yet implemented (Phase 3)",
    )

    return {
        "status": "accepted",
        "message": "Push received",
        "branch": payload.branch_name,
        "commits": payload.commit_count,
    }


async def handle_github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str,
    x_github_event: str,
    x_github_delivery: str,
) -> dict[str, str | int]:
    """Handle incoming GitHub webhook requests.

    This is the main entry point for GitHub webhooks. It:
    1. Validates required headers are present
    2. Verifies the HMAC signature
    3. Parses and validates the payload
    4. Processes the webhook event

    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks for async processing
        x_hub_signature_256: GitHub signature header
        x_github_event: GitHub event type (e.g., "pull_request")
        x_github_delivery: Unique delivery ID for this webhook

    Returns:
        dict: Response data with status and message

    Raises:
        HTTPException: 400 for missing headers/invalid payload, 401 for invalid signature

    Example:
        This function is called by FastAPI when POST /webhook/github is hit.
        It should not be called directly in application code.
    """
    # Only handle pull_request and push events
    if x_github_event not in ("pull_request", "push"):
        logger.info(
            "webhook_ignored",
            event_type=x_github_event,
            delivery_id=x_github_delivery,
            reason="Event type not handled",
        )
        return {
            "status": "ignored",
            "message": f"Event type '{x_github_event}' is not handled",
        }

    # Read raw body for signature verification
    payload_body = await request.body()

    # Verify signature
    is_valid = verify_github_signature(
        payload_body=payload_body,
        signature_header=x_hub_signature_256,
        secret=settings.github_webhook_secret,
    )

    if not is_valid:
        logger.warning(
            "webhook_rejected",
            reason="Invalid signature",
            delivery_id=x_github_delivery,
            event_type=x_github_event,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # Parse JSON payload
    try:
        payload_json = await request.json()
    except Exception as e:
        logger.error("webhook_rejected", reason="Invalid JSON", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Create delivery info for tracking
    delivery_info = WebhookDeliveryInfo(
        delivery_id=x_github_delivery,
        event_type=x_github_event,
        signature=x_hub_signature_256,
        payload_size=len(payload_body),
    )

    # Route to appropriate handler based on event type
    if x_github_event == "pull_request":
        # Validate payload structure with Pydantic
        try:
            payload = PullRequestWebhookPayload.model_validate(payload_json)
        except Exception as e:
            logger.error(
                "webhook_rejected",
                reason="Invalid pull_request payload structure",
                error=str(e),
                delivery_id=x_github_delivery,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payload structure: {str(e)}",
            )

        return await process_pull_request_webhook(payload, delivery_info, background_tasks)

    elif x_github_event == "push":
        # Validate payload structure with Pydantic
        try:
            payload = PushWebhookPayload.model_validate(payload_json)
        except Exception as e:
            logger.error(
                "webhook_rejected",
                reason="Invalid push payload structure",
                error=str(e),
                delivery_id=x_github_delivery,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payload structure: {str(e)}",
            )

        return await process_push_webhook(payload, delivery_info)

    else:
        # Should never reach here due to earlier check, but for safety
        return {
            "status": "ignored",
            "message": f"Event type '{x_github_event}' is not handled",
        }
