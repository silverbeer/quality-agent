"""Lambda handler for GitHub webhook receiver.

Receives GitHub webhooks, verifies signatures, stores events to S3,
and sends processing messages to SQS.
"""

import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client("s3")
sqs_client = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
ssm_client = boto3.client("ssm")

# Environment variables
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
EVENTS_BUCKET = os.environ["EVENTS_BUCKET"]
PROCESSING_QUEUE_URL = os.environ["PROCESSING_QUEUE_URL"]
IDEMPOTENCY_TABLE = os.environ["IDEMPOTENCY_TABLE"]
WEBHOOK_SECRET_PARAM = os.environ["GITHUB_WEBHOOK_SECRET_PARAMETER"]

# Cache for webhook secret
_webhook_secret = None


def get_webhook_secret() -> str:
    """Retrieve webhook secret from Parameter Store with caching."""
    global _webhook_secret
    if _webhook_secret is None:
        response = ssm_client.get_parameter(
            Name=WEBHOOK_SECRET_PARAM,
            WithDecryption=True
        )
        _webhook_secret = response["Parameter"]["Value"]
    return _webhook_secret


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature using HMAC SHA-256.

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not signature.startswith("sha256="):
        return False

    secret = get_webhook_secret()
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    provided = signature.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)


def check_idempotency(delivery_id: str) -> bool:
    """Check if this delivery has already been processed.

    Args:
        delivery_id: GitHub delivery ID

    Returns:
        True if already processed, False if new
    """
    table = dynamodb.Table(IDEMPOTENCY_TABLE)

    try:
        response = table.get_item(Key={"delivery_id": delivery_id})
        return "Item" in response
    except ClientError as e:
        logger.error(f"DynamoDB error checking idempotency: {e}")
        return False


def record_delivery(delivery_id: str, event_type: str) -> None:
    """Record delivery ID to prevent duplicate processing.

    Args:
        delivery_id: GitHub delivery ID
        event_type: GitHub event type
    """
    table = dynamodb.Table(IDEMPOTENCY_TABLE)

    # TTL: 7 days from now
    ttl = int(time.time()) + (7 * 24 * 60 * 60)

    try:
        table.put_item(Item={
            "delivery_id": delivery_id,
            "event_type": event_type,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "ttl": ttl
        })
    except ClientError as e:
        logger.error(f"DynamoDB error recording delivery: {e}")


def store_event_to_s3(delivery_id: str, event_type: str, payload: dict) -> str:
    """Store webhook event to S3.

    Args:
        delivery_id: GitHub delivery ID
        event_type: GitHub event type
        payload: Webhook payload

    Returns:
        S3 key where event was stored
    """
    now = datetime.now(timezone.utc)
    s3_key = f"webhooks/{now.year}/{now.month:02d}/{now.day:02d}/{delivery_id}.json"

    event_data = {
        "delivery_id": delivery_id,
        "event_type": event_type,
        "received_at": now.isoformat(),
        "payload": payload
    }

    s3_client.put_object(
        Bucket=EVENTS_BUCKET,
        Key=s3_key,
        Body=json.dumps(event_data, default=str),
        ContentType="application/json"
    )

    logger.info(f"Stored event to s3://{EVENTS_BUCKET}/{s3_key}")
    return s3_key


def send_to_queue(delivery_id: str, event_type: str, payload: dict, s3_key: str) -> None:
    """Send processing message to SQS.

    Args:
        delivery_id: GitHub delivery ID
        event_type: GitHub event type
        payload: Webhook payload
        s3_key: S3 key where full event is stored
    """
    # Extract relevant info based on event type
    message = {
        "delivery_id": delivery_id,
        "event_type": event_type,
        "s3_key": s3_key,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if event_type == "pull_request":
        pr = payload.get("pull_request", {})
        message.update({
            "action": payload.get("action"),
            "repository": payload.get("repository", {}).get("full_name"),
            "pr_number": payload.get("number"),
            "pr_title": pr.get("title"),
            "head_sha": pr.get("head", {}).get("sha"),
            "base_ref": pr.get("base", {}).get("ref")
        })
    elif event_type == "push":
        message.update({
            "repository": payload.get("repository", {}).get("full_name"),
            "ref": payload.get("ref"),
            "before": payload.get("before"),
            "after": payload.get("after"),
            "commits_count": len(payload.get("commits", []))
        })
    elif event_type == "workflow_run":
        workflow = payload.get("workflow_run", {})
        message.update({
            "action": payload.get("action"),
            "repository": payload.get("repository", {}).get("full_name"),
            "workflow_name": workflow.get("name"),
            "workflow_id": workflow.get("id"),
            "conclusion": workflow.get("conclusion"),
            "head_sha": workflow.get("head_sha")
        })

    sqs_client.send_message(
        QueueUrl=PROCESSING_QUEUE_URL,
        MessageBody=json.dumps(message),
        MessageAttributes={
            "event_type": {
                "DataType": "String",
                "StringValue": event_type
            },
            "delivery_id": {
                "DataType": "String",
                "StringValue": delivery_id
            }
        }
    )

    logger.info(f"Sent message to SQS for delivery {delivery_id}")


def lambda_handler(event: dict, context) -> dict:
    """Main Lambda handler for GitHub webhooks.

    Args:
        event: Lambda event (from Function URL)
        context: Lambda context

    Returns:
        HTTP response dict
    """
    # Extract headers (case-insensitive)
    headers = {k.lower(): v for k, v in event.get("headers", {}).items()}

    # Get GitHub-specific headers
    signature = headers.get("x-hub-signature-256", "")
    event_type = headers.get("x-github-event", "")
    delivery_id = headers.get("x-github-delivery", "")

    # Validate required headers
    if not event_type or not delivery_id:
        logger.warning("Missing required GitHub headers")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing required GitHub headers"})
        }

    # Get request body
    body = event.get("body", "")
    if event.get("isBase64Encoded", False):
        import base64
        body = base64.b64decode(body).decode("utf-8")

    body_bytes = body.encode("utf-8") if isinstance(body, str) else body

    # Verify signature
    if not verify_signature(body_bytes, signature):
        logger.warning(f"Invalid signature for delivery {delivery_id}")
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Invalid signature"})
        }

    # Check idempotency
    if check_idempotency(delivery_id):
        logger.info(f"Duplicate delivery {delivery_id}, skipping")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "duplicate",
                "delivery_id": delivery_id,
                "message": "Event already processed"
            })
        }

    # Parse payload
    try:
        payload = json.loads(body) if isinstance(body, str) else body
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON payload"})
        }

    # Log event info
    logger.info(f"Received {event_type} event, delivery: {delivery_id}")

    # Store event to S3
    s3_key = store_event_to_s3(delivery_id, event_type, payload)

    # Send to processing queue
    send_to_queue(delivery_id, event_type, payload, s3_key)

    # Record delivery for idempotency
    record_delivery(delivery_id, event_type)

    # Build response based on event type
    response_data = {
        "status": "accepted",
        "delivery_id": delivery_id,
        "event_type": event_type,
        "s3_key": s3_key
    }

    if event_type == "pull_request":
        response_data.update({
            "action": payload.get("action"),
            "pr_number": payload.get("number"),
            "repository": payload.get("repository", {}).get("full_name")
        })
    elif event_type == "push":
        ref = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
        response_data.update({
            "branch": branch,
            "commits": len(payload.get("commits", [])),
            "repository": payload.get("repository", {}).get("full_name")
        })
    elif event_type == "workflow_run":
        workflow = payload.get("workflow_run", {})
        response_data.update({
            "action": payload.get("action"),
            "workflow": workflow.get("name"),
            "conclusion": workflow.get("conclusion"),
            "repository": payload.get("repository", {}).get("full_name")
        })

    return {
        "statusCode": 200,
        "body": json.dumps(response_data)
    }
