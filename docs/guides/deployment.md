# Deployment Guide

> Guide to deploying Quality Agent to various environments

**Status**: 🚧 To be completed in Phase 5

## Deployment Options

Quality Agent supports multiple deployment methods:
1. Local development (uvicorn)
2. Docker container
3. docker-compose
4. k3s/Kubernetes
5. Production (cloud platforms)

## Local Development

```bash
uvicorn app.main:app --reload --port 8000
```

## Docker Deployment

Details will be added in Phase 5.

```bash
# Build image
docker build -t quality-agent:latest .

# Run container
docker run -p 8000:8000 --env-file .env quality-agent:latest
```

## docker-compose Deployment

Details will be added in Phase 5.

```bash
docker-compose up --build
```

## k3s Deployment

Details will be added in Phase 5.

```bash
# Build and load image
docker build -t quality-agent:latest .
docker save quality-agent:latest | sudo k3s ctr images import -

# Deploy
kubectl apply -f deployment/k8s/
```

## Production Deployment

Production deployment guide will be added in Phase 5, covering:
- Environment configuration
- Secret management
- Scaling considerations
- Monitoring setup
- Backup procedures

## ngrok Setup for Webhooks

```bash
# Install ngrok
# macOS: brew install ngrok
# Linux: Download from https://ngrok.com/

# Start tunnel
ngrok http 8000

# Use the HTTPS URL in GitHub webhook settings
```

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0 (Stub)
