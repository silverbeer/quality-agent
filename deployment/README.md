# Quality Agent - Deployment Guide

## Quick Start with Docker Compose

The fastest way to get Quality Agent running with Prometheus and Grafana:

```bash
# From the deployment directory
cd deployment

# Start all services (quality-agent, Prometheus, Grafana)
docker-compose up --build

# Access the services:
# - Quality Agent: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

## What Gets Deployed

### Quality Agent (Port 8000)
- FastAPI webhook receiver
- DORA metrics collection
- `/metrics` endpoint for Prometheus
- `/health` endpoint for monitoring

### Prometheus (Port 9090)
- Scrapes quality-agent every 15 seconds
- Stores metrics for 30 days
- Provides PromQL query interface

### Grafana (Port 3000)
- Pre-configured Prometheus datasource
- Default credentials: admin/admin
- Ready for dashboard creation

## DORA Metrics Available

Once webhooks start flowing, you'll collect:

- **pr_total**: Pull request events (opened, closed, merged)
- **pr_review_time_seconds**: Time from PR creation to merge (histogram)
- **deployments_total**: Deployment frequency (push-to-main proxy)
- **http_requests_total**: HTTP request metrics (automatic)
- **http_request_duration_seconds**: Request duration (histogram)

## Example Prometheus Queries

Access Prometheus at http://localhost:9090 and try:

```promql
# PR merge rate (PRs per hour)
rate(pr_total{action="closed",merged="true"}[1h]) * 3600

# Median PR review time
histogram_quantile(0.50, rate(pr_review_time_seconds_bucket[24h]))

# 95th percentile PR review time
histogram_quantile(0.95, rate(pr_review_time_seconds_bucket[24h]))

# Deployment frequency (per day)
rate(deployments_total{environment="production",status="success"}[24h]) * 86400

# HTTP request rate
rate(http_requests_total[5m])

# HTTP error rate
rate(http_requests_total{status=~"5.."}[5m])
```

## Kubernetes (k3s) Deployment

For k3s deployment (local or production):

```bash
# Deploy Prometheus
kubectl apply -f k8s/prometheus/

# Deploy Grafana
kubectl apply -f k8s/grafana/

# Verify deployments
kubectl get pods
kubectl get services

# Access services:
# - Prometheus: http://localhost:30090 (NodePort)
# - Grafana: http://localhost:30300 (NodePort)
```

## Configuration

### Enable Metrics in Quality Agent

In your `.env` file:

```bash
# Enable metrics endpoint
ENABLE_METRICS=true

# Include default HTTP metrics (optional)
METRICS_INCLUDE_DEFAULT=true
```

### Customize Prometheus Retention

Edit `prometheus/prometheus.yml` or `k8s/prometheus/prometheus-deployment.yaml`:

```yaml
args:
  - '--storage.tsdb.retention.time=30d'  # Change retention period
```

### Customize Grafana

1. Login to Grafana (admin/admin)
2. Change default password
3. Create new dashboards
4. Import community dashboards (optional)

## Troubleshooting

### Quality Agent not showing metrics

1. Check metrics are enabled:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/metrics
   ```

2. Verify env variable is set:
   ```bash
   docker-compose exec quality-agent env | grep ENABLE_METRICS
   ```

### Prometheus not scraping

1. Check Prometheus targets:
   - Go to http://localhost:9090/targets
   - Verify quality-agent target is UP

2. Check connectivity:
   ```bash
   docker-compose exec prometheus wget -O- http://quality-agent:8000/metrics
   ```

### Grafana can't connect to Prometheus

1. Check Grafana datasource config:
   - Settings > Data Sources > Prometheus
   - URL should be: http://prometheus:9090

2. Test connection in Grafana UI

## Next Steps

1. **Send test webhooks** to generate metrics
2. **Create Grafana dashboards** for DORA metrics
3. **Set up alerts** in Prometheus for SLO violations
4. **Configure GitHub webhooks** in your repository:
   - Go to Repository Settings > Webhooks
   - Add webhook: http://your-server:8000/webhook/github
   - Secret: (from GITHUB_WEBHOOK_SECRET env var)
   - Events: Pull requests, Pushes

## Architecture

```
GitHub Webhooks
      ↓
Quality Agent (:8000)
  ├─ /webhook/github  → Process webhooks, record metrics
  └─ /metrics         → Expose Prometheus metrics
      ↓
Prometheus (:9090)
  ├─ Scrape /metrics every 15s
  └─ Store time-series data
      ↓
Grafana (:3000)
  └─ Query & visualize metrics
```

## Files

```
deployment/
├── docker-compose.yml          # Docker Compose setup
├── Dockerfile                  # Quality Agent container
├── prometheus/
│   └── prometheus.yml          # Prometheus config (Docker)
├── grafana/
│   └── datasources/
│       └── prometheus.yaml     # Grafana datasource
└── k8s/
    ├── prometheus/             # Prometheus k8s manifests
    └── grafana/                # Grafana k8s manifests
```
