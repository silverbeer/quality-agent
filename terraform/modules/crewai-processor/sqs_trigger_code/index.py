"""Lambda function to trigger ECS Fargate tasks from SQS messages."""

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs_client = boto3.client("ecs")

ECS_CLUSTER = os.environ["ECS_CLUSTER"]
TASK_DEFINITION = os.environ["TASK_DEFINITION"]
SUBNETS = os.environ["SUBNETS"].split(",")
SECURITY_GROUPS = os.environ["SECURITY_GROUPS"].split(",")
CONTAINER_NAME = os.environ["CONTAINER_NAME"]


def handler(event, context):
    """Handle SQS messages and launch Fargate tasks."""
    for record in event.get("Records", []):
        message_body = record.get("body", "{}")
        message = json.loads(message_body)

        delivery_id = message.get("delivery_id", "unknown")
        event_type = message.get("event_type", "unknown")

        logger.info(f"Processing {event_type} event: {delivery_id}")

        # Only process pull_request events with CrewAI
        if event_type != "pull_request":
            logger.info(f"Skipping {event_type} event (not a PR)")
            continue

        # Launch Fargate task
        try:
            response = ecs_client.run_task(
                cluster=ECS_CLUSTER,
                taskDefinition=TASK_DEFINITION,
                launchType="FARGATE",
                capacityProviderStrategy=[
                    {
                        "capacityProvider": "FARGATE_SPOT",
                        "weight": 100,
                        "base": 0
                    }
                ],
                networkConfiguration={
                    "awsvpcConfiguration": {
                        "subnets": SUBNETS,
                        "securityGroups": SECURITY_GROUPS,
                        "assignPublicIp": "ENABLED"
                    }
                },
                overrides={
                    "containerOverrides": [
                        {
                            "name": CONTAINER_NAME,
                            "environment": [
                                {
                                    "name": "MESSAGE_BODY",
                                    "value": message_body
                                }
                            ]
                        }
                    ]
                }
            )

            task_arns = [task["taskArn"] for task in response.get("tasks", [])]
            failures = response.get("failures", [])

            if failures:
                logger.error(f"Task launch failures: {failures}")
            else:
                logger.info(f"Launched task(s): {task_arns}")

        except Exception as e:
            logger.error(f"Failed to launch Fargate task: {e}")
            raise

    return {"statusCode": 200}
