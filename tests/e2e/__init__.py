"""End-to-end tests for quality-agent webhook receiver.

These tests simulate complete webhook flows from GitHub to verify:
- Webhook signature verification
- Payload parsing and validation
- Audit log creation
- Metrics recording
- Background task queueing
- Complete state consistency

All test data uses obviously fake repository names and humorous commit messages
to make it clear these are test scenarios, not real repositories.
"""
