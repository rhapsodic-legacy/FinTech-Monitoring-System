# FinTech K8s System - Quick Start Guide

## 🎯 5-Minute Setup

### Prerequisites Check
```bash
# Verify installations
docker --version
kubectl version --client
python3 --version
node --version
```

### Step 1: Initial Setup
```bash
# Make scripts executable
chmod +x setup.sh build.sh deploy.sh scripts/*.sh

# Run setup (checks dependencies, creates directories)
./setup.sh
```

### Step 2: Configure API Keys
Edit the `.env` file or update the secret directly:

```bash
# Edit the file
nano .env

# Or update Kubernetes secret
kubectl create secret generic api-keys-secret -n fintech \
  --from-literal=ALPHA_VANTAGE_KEY=your_key \
  --from-literal=NEWS_API_KEY=your_key \
  --from-literal=GEMINI_API_KEY=your_key \
  --dry-run=client -o yaml | kubectl apply -f -
```

**Get Free API Keys:**
- Alpha Vantage: https://www.alphavantage.co/support/#api-key
- NewsAPI: https://newsapi.org/register
- Google Gemini: https://ai.google.dev/

### Step 3: Build Docker Images
```bash
./build.sh
```

This builds:
- `fintech-scraper:latest` (Market data scraper)
- `fintech-analyzer:latest` (AI sentiment analyzer)
- `fintech-alert:latest` (Alert service)
- `fintech-frontend:latest` (React dashboard)

### Step 4: Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace fintech

# Deploy everything
./deploy.sh

# Or manually:
kubectl apply -f k8s/
```

### Step 5: Access the Application
```bash
# Forward frontend port
kubectl port-forward -n fintech svc/frontend-service 3000:80

# Open browser
open http://localhost:3000
```

## 🔍 Verify Deployment

### Check Pods
```bash
kubectl get pods -n fintech

# Expected output:
# NAME                              READY   STATUS    RESTARTS   AGE
# analyzer-service-xxx              1/1     Running   0          2m
# alert-service-xxx                 1/1     Running   0          2m
# frontend-xxx                      1/1     Running   0          2m
# postgres-0                        1/1     Running   0          3m
# scraper-service-xxx               1/1     Running   0          2m
```

### Check Services
```bash
kubectl get svc -n fintech

# Expected services:
# - postgres-service (ClusterIP)
# - scraper-service (ClusterIP)
# - analyzer-service (ClusterIP)
# - alert-service (ClusterIP)
# - frontend-service (LoadBalancer)
```

### Check HPA
```bash
kubectl get hpa -n fintech

# Should show analyzer-hpa with 2/2 replicas
```

### Check CronJob
```bash
kubectl get cronjobs -n fintech

# Should show scraper-cronjob with schedule */30 * * * *
```

## 🧪 Test the System

### 1. Trigger Manual Scrape
```bash
kubectl exec -it deployment/scraper-service -n fintech -- \
  curl -X POST http://localhost:5000/scrape
```

### 2. View Logs
```bash
# Scraper logs
kubectl logs -f deployment/scraper-service -n fintech

# Analyzer logs (with Gemini AI)
kubectl logs -f deployment/analyzer-service -n fintech

# Alert logs
kubectl logs -f deployment/alert-service -n fintech
```

### 3. Query Database
```bash
kubectl exec -it postgres-0 -n fintech -- \
  psql -U fintech_user -d fintech_db

# SQL commands:
# SELECT * FROM market_data ORDER BY timestamp DESC LIMIT 5;
# SELECT * FROM sentiment_analysis ORDER BY analyzed_at DESC LIMIT 5;
# SELECT * FROM alerts WHERE triggered = true LIMIT 5;
# \q to exit
```

### 4. Test Auto-Scaling
```bash
# Run load test
./scripts/load-test.sh

# Watch pods scale
kubectl get hpa -n fintech -w
```

## 📊 Access Individual Services

### Scraper Service
```bash
kubectl port-forward -n fintech svc/scraper-service 5000:5000
curl http://localhost:5000/api/latest-data
```

### Analyzer Service
```bash
kubectl port-forward -n fintech svc/analyzer-service 5001:5001
curl http://localhost:5001/api/sentiment-summary
```

### Alert Service
```bash
kubectl port-forward -n fintech svc/alert-service 5002:5002
curl http://localhost:5002/api/alerts/recent
```

## 🔧 Troubleshooting

### Pods Not Starting
```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n fintech

# Check logs
kubectl logs <pod-name> -n fintech

# Check if images exist
docker images | grep fintech
```

### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it postgres-0 -n fintech -- pg_isready

# Check service
kubectl get svc postgres-service -n fintech

# Restart dependent services
kubectl rollout restart deployment/scraper-service -n fintech
```

### HPA Not Working
```bash
# Check if metrics-server is running
kubectl get deployment metrics-server -n kube-system

# Install if missing
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For Docker Desktop, patch for insecure TLS
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
```

### Out of Memory (8GB Mac)
```bash
# Reduce replicas
kubectl scale deployment analyzer-service --replicas=1 -n fintech
kubectl scale deployment frontend --replicas=1 -n fintech

# Or update resource limits in k8s/services/*.yaml
```

## 🧹 Cleanup

### Delete Everything
```bash
kubectl delete namespace fintech

# Or selectively:
kubectl delete -f k8s/ -n fintech
```

### Remove Docker Images
```bash
docker rmi fintech-scraper:latest
docker rmi fintech-analyzer:latest
docker rmi fintech-alert:latest
docker rmi fintech-frontend:latest
```

## 📚 Learning Path

1. **Understand the Architecture** - Review README.md
2. **Explore StatefulSets** - Look at `k8s/database/postgres-statefulset.yaml`
3. **Study CronJobs** - Check `k8s/jobs/scraper-cronjob.yaml`
4. **Analyze HPA** - Review `k8s/autoscaling/analyzer-hpa.yaml`
5. **Service Networking** - Examine all `*-service.yaml` files
6. **Review Code** - Read through `services/*/app.py`

## 🎓 Key Concepts Demonstrated

✅ StatefulSets with Persistent Volumes (PostgreSQL)
✅ Deployments with ReplicaSets (Microservices)
✅ CronJobs for Scheduled Tasks
✅ Horizontal Pod Autoscaling (CPU-based)
✅ Service Discovery & Networking
✅ ConfigMaps & Secrets Management
✅ Health Checks (Liveness & Readiness Probes)
✅ Resource Requests & Limits
✅ Init Containers
✅ Multi-container Pods

## 🚀 Next Steps

- Add Ingress controller for better routing
- Implement Prometheus/Grafana monitoring
- Add CI/CD pipeline
- Implement service mesh (Istio/Linkerd)
- Add more sophisticated ML models
- Implement WebSocket for real-time updates

## 💡 Tips for M2 Mac

- Docker Desktop needs ~4GB RAM minimum
- Keep resource requests low (shown in configs)
- Use `imagePullPolicy: Never` for local images
- Stop other apps to free memory if needed

---

**Questions?** Check the full README.md or logs for detailed information.
