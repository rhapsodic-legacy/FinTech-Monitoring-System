# FinTech Monitoring System - Kubernetes Project

A production-ready financial monitoring system demonstrating advanced Kubernetes concepts including StatefulSets, CronJobs, auto-scaling, and microservices architecture.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                    Deployment + LoadBalancer                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                        API Gateway                               │
│                      (Service Mesh)                              │
└─────┬──────────────┬─────────────────┬──────────────────┬───────┘
      │              │                 │                  │
┌─────▼─────┐ ┌─────▼─────┐    ┌─────▼─────┐    ┌──────▼──────┐
│  Scraper  │ │ Analyzer  │    │   Alert   │    │  PostgreSQL │
│  Service  │ │  Service  │    │  Service  │    │ StatefulSet │
│Deployment │ │Deployment │    │Deployment │    │    + PVC    │
│+ CronJob  │ │  + HPA    │    │           │    │             │
└───────────┘ └───────────┘    └───────────┘    └─────────────┘
```

## 🚀 Features

- **Scraper Service**: Fetches real-time market data from Alpha Vantage & news from NewsAPI
- **Analyzer Service**: Uses Google Gemini AI for sentiment analysis and signal aggregation
- **Alert Service**: Email/SMS notifications via Twilio when conditions trigger
- **PostgreSQL Database**: Persistent storage with StatefulSet
- **React Frontend**: Real-time dashboard with WebSocket updates
- **Horizontal Auto-Scaling**: Automatically scales based on load
- **CronJobs**: Scheduled data collection

## 📋 Prerequisites (M2 Mac)

1. **Docker Desktop for Mac (Apple Silicon)**
   ```bash
   # Install via Homebrew
   brew install --cask docker
   
   # Start Docker Desktop and enable Kubernetes in settings
   # Settings → Kubernetes → Enable Kubernetes
   ```

2. **kubectl**
   ```bash
   brew install kubectl
   ```

3. **Python 3.10+**
   ```bash
   brew install python@3.11
   ```

4. **Node.js 18+**
   ```bash
   brew install node@18
   ```

5. **API Keys** (Free tiers available):
   - Alpha Vantage: https://www.alphavantage.co/support/#api-key
   - NewsAPI: https://newsapi.org/register
   - Google Gemini: https://ai.google.dev/
   - Twilio (optional): https://www.twilio.com/try-twilio

## 🔧 Installation & Setup

### Step 1: Clone and Setup Environment

```bash
# Navigate to project directory
cd fintech-k8s-system

# Run the automated setup script
chmod +x setup.sh
./setup.sh
```

### Step 2: Configure API Keys

Edit the `.env` file created by the setup script:

```bash
# Database
POSTGRES_USER=fintech_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=fintech_db

# API Keys
ALPHA_VANTAGE_KEY=your_alpha_vantage_key
NEWS_API_KEY=your_news_api_key
GEMINI_API_KEY=your_gemini_api_key

# Twilio (optional for SMS alerts)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890

# Alert Settings
ALERT_EMAIL=your_email@example.com
ALERT_PHONE=+1234567890
```

### Step 3: Build Docker Images

```bash
# Build all service images
./build.sh
```

### Step 4: Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace fintech

# Apply all configurations
kubectl apply -f k8s/

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod --all -n fintech --timeout=300s
```

### Step 5: Access the Application

```bash
# Get the frontend URL
kubectl get svc frontend-service -n fintech

# Forward port to access locally
kubectl port-forward svc/frontend-service 3000:80 -n fintech

# Access at http://localhost:3000
```

## 📊 Kubernetes Concepts Demonstrated

### 1. StatefulSets (PostgreSQL)
- **File**: `k8s/database/postgres-statefulset.yaml`
- Persistent storage with PVCs
- Stable network identities
- Ordered deployment and scaling

### 2. Deployments (Microservices)
- **Files**: `k8s/services/*-deployment.yaml`
- Replica management
- Rolling updates
- Health checks (liveness/readiness probes)

### 3. CronJobs (Scheduled Scraping)
- **File**: `k8s/jobs/scraper-cronjob.yaml`
- Scheduled market data collection
- Job history limits
- Concurrent execution policies

### 4. Horizontal Pod Autoscaler (HPA)
- **File**: `k8s/autoscaling/analyzer-hpa.yaml`
- CPU-based auto-scaling
- Min/max replica configuration
- Target utilization metrics

### 5. Persistent Volume Claims
- **File**: `k8s/database/postgres-pvc.yaml`
- Dynamic volume provisioning
- Data persistence across pod restarts

### 6. Services & Networking
- **Files**: `k8s/services/*-service.yaml`
- ClusterIP for internal communication
- LoadBalancer for external access
- Service discovery via DNS

### 7. ConfigMaps & Secrets
- **Files**: `k8s/config/*`
- Environment configuration
- Sensitive data management

## 🎯 Usage Examples

### Monitor Logs

```bash
# Scraper logs
kubectl logs -f deployment/scraper-service -n fintech

# Analyzer logs (with Gemini AI)
kubectl logs -f deployment/analyzer-service -n fintech

# Alert logs
kubectl logs -f deployment/alert-service -n fintech

# Database logs
kubectl logs -f statefulset/postgres -n fintech
```

### Scale Services Manually

```bash
# Scale analyzer service
kubectl scale deployment analyzer-service --replicas=3 -n fintech

# Scale scraper service
kubectl scale deployment scraper-service --replicas=2 -n fintech
```

### Check Auto-Scaling Status

```bash
# View HPA status
kubectl get hpa -n fintech

# Describe HPA
kubectl describe hpa analyzer-hpa -n fintech
```

### Execute Database Queries

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n fintech -- psql -U fintech_user -d fintech_db

# Example queries:
# SELECT * FROM market_data ORDER BY timestamp DESC LIMIT 10;
# SELECT * FROM sentiment_analysis ORDER BY created_at DESC LIMIT 10;
# SELECT * FROM alerts WHERE triggered = true;
```

### View CronJob Schedule

```bash
# List CronJobs
kubectl get cronjobs -n fintech

# View CronJob details
kubectl describe cronjob scraper-cronjob -n fintech

# Manually trigger a job
kubectl create job --from=cronjob/scraper-cronjob manual-scrape-$(date +%s) -n fintech
```

## 🧪 Testing the System

### Generate Load for Auto-Scaling

```bash
# Run load test (requires Apache Bench)
./scripts/load-test.sh

# Or manually
kubectl run -it --rm load-generator --image=busybox --restart=Never -n fintech -- \
  /bin/sh -c "while true; do wget -q -O- http://analyzer-service:5001/health; done"
```

### Verify Data Flow

```bash
# Check if data is being scraped
curl http://localhost:5000/api/latest-data

# Check analyzer results
curl http://localhost:5001/api/sentiment-summary

# Check alerts
curl http://localhost:5002/api/alerts/recent
```

## 📁 Project Structure

```
fintech-k8s-system/
├── services/
│   ├── scraper/              # Market data scraper service
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── analyzer/             # ML/AI sentiment analyzer
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── alert/                # Alert notification service
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/             # React dashboard
│       ├── src/
│       ├── package.json
│       └── Dockerfile
├── k8s/
│   ├── database/             # StatefulSet & PVC configs
│   ├── services/             # Deployment configs
│   ├── jobs/                 # CronJob configs
│   ├── autoscaling/          # HPA configs
│   └── config/               # ConfigMaps & Secrets
├── scripts/
│   ├── init-db.sql           # Database schema
│   └── load-test.sh          # Load testing script
├── setup.sh                  # Automated setup
├── build.sh                  # Docker build script
└── README.md                 # This file
```

## 🛠️ Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n fintech

# Describe problematic pod
kubectl describe pod <pod-name> -n fintech

# Check events
kubectl get events -n fintech --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
kubectl get statefulset postgres -n fintech

# Check service
kubectl get svc postgres-service -n fintech

# Test connection
kubectl run -it --rm psql-test --image=postgres:15 --restart=Never -n fintech -- \
  psql -h postgres-service -U fintech_user -d fintech_db
```

### API Rate Limits

The system respects API rate limits:
- Alpha Vantage: 25 requests/day (free tier)
- NewsAPI: 100 requests/day (free tier)
- Gemini: 60 requests/minute (free tier)

Adjust CronJob schedules in `k8s/jobs/scraper-cronjob.yaml` if needed.

## 🚀 Advanced Features

### Enable Metrics Server (for HPA)

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For Docker Desktop on Mac, patch for insecure TLS
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
```

### Set Up Ingress (Optional)

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Apply ingress configuration
kubectl apply -f k8s/ingress/ingress.yaml
```

## 📈 Monitoring & Observability

The system includes health check endpoints:
- Scraper: `http://scraper-service:5000/health`
- Analyzer: `http://analyzer-service:5001/health`
- Alert: `http://alert-service:5002/health`

## 🧹 Cleanup

```bash
# Delete all resources
kubectl delete namespace fintech

# Or delete specific resources
kubectl delete -f k8s/ -n fintech

# Stop Docker Desktop Kubernetes if needed
```

## 📚 Learning Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [StatefulSets Guide](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)

## 🤝 Contributing

This is an educational project. Feel free to fork and extend with:
- Additional data sources
- More sophisticated ML models
- Real-time streaming with Kafka
- Prometheus/Grafana monitoring
- CI/CD pipelines

## 📄 License

MIT License - Educational purposes

---

**Ready to deploy your FinTech system?** Run `./setup.sh` to get started! 🚀
