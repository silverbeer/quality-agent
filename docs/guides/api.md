# API Reference

> Complete API documentation for Quality Agent

**Status**: 🚧 To be completed in Phase 2

## Base URL

```
Local: http://localhost:8000
Production: https://your-domain.com
```

## Endpoints

### Health Check

```http
GET /health
```

Returns the health status of the service.

**Response**: `200 OK`
```json
{
  "status": "healthy"
}
```

### GitHub Webhook

```http
POST /webhook/github
```

Receives GitHub webhook events for pull requests.

**Headers**:
- `X-Hub-Signature-256`: HMAC SHA-256 signature of the payload

**Request Body**: GitHub webhook payload (PR events)

**Response**: `200 OK`
```json
{
  "status": "accepted"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid signature
- `422 Unprocessable Entity`: Invalid payload format

Detailed API documentation will be added in Phase 2.

## Data Models

### GitHubWebhookPayload

Details will be added in Phase 2.

### AnalysisReport

Details will be added in Phase 3.

## Interactive Documentation

When the service is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0 (Stub)
