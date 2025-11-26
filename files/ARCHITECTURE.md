# FinTech K8s System - Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  👤 User Browser  →  http://localhost:3000                              │
│                                                                           │
│  📡 External APIs:                                                       │
│     • Alpha Vantage (Market Data)                                        │
│     • NewsAPI (Financial News)                                           │
│     • Google Gemini (AI Sentiment Analysis)                             │
│     • Twilio (SMS Alerts - Optional)                                    │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         KUBERNETES CLUSTER                               │
│                         (Docker Desktop)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              FRONTEND (React + Nginx)                           │   │
│  │  • Type: Deployment                                             │   │
│  │  • Replicas: 2                                                  │   │
│  │  • Service: LoadBalancer on port 80                            │   │
│  │  • Features: Real-time dashboard, Charts, Alerts display       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                ↓                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    SERVICE MESH / API GATEWAY                     │  │
│  │  • ClusterIP Services                                             │  │
│  │  • Service Discovery via DNS                                      │  │
│  │  • Internal Load Balancing                                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│          ↓                    ↓                    ↓                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │
│  │    SCRAPER     │  │    ANALYZER    │  │     ALERT      │           │
│  │    SERVICE     │  │    SERVICE     │  │    SERVICE     │           │
│  │                │  │                │  │                │           │
│  │ • Deployment   │  │ • Deployment   │  │ • Deployment   │           │
│  │ • Replicas: 1  │  │ • Replicas: 2+ │  │ • Replicas: 1  │           │
│  │ • Port: 5000   │  │ • Port: 5001   │  │ • Port: 5002   │           │
│  │                │  │ • HPA Enabled  │  │                │           │
│  │ Pulls data:    │  │ AI Analysis:   │  │ Notifications: │           │
│  │ • Market data  │  │ • Gemini API   │  │ • Email/SMS    │           │
│  │ • News feeds   │  │ • Sentiment    │  │ • Conditions   │           │
│  │                │  │ • Signals      │  │ • Triggers     │           │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘           │
│           │                   │                   │                     │
│           └───────────────────┴───────────────────┘                     │
│                               ↓                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    POSTGRESQL DATABASE                            │  │
│  │  • Type: StatefulSet                                              │  │
│  │  • Replicas: 1                                                    │  │
│  │  • Persistent Volume: 2Gi                                         │  │
│  │  • Service: Headless (ClusterIP None)                            │  │
│  │  • Stable hostname: postgres-0.postgres-service                  │  │
│  │                                                                    │  │
│  │  Tables:                                                          │  │
│  │    • market_data          (Real-time prices)                     │  │
│  │    • news_articles        (Financial news)                       │  │
│  │    • sentiment_analysis   (AI-generated sentiment)               │  │
│  │    • trading_signals      (Composite signals)                    │  │
│  │    • alerts               (Triggered alerts)                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    SCHEDULED JOBS                                 │  │
│  │  ┌────────────────────────────────────────────────────────────┐ │  │
│  │  │  SCRAPER CRONJOB                                           │ │  │
│  │  │  • Schedule: Every 30 minutes (*/30 * * * *)              │ │  │
│  │  │  • Concurrency: Forbid                                     │ │  │
│  │  │  • Success History: 3                                      │ │  │
│  │  │  • Failed History: 1                                       │ │  │
│  │  │  • Action: Fetch market data & news                       │ │  │
│  │  └────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    AUTO-SCALING                                   │  │
│  │  ┌────────────────────────────────────────────────────────────┐ │  │
│  │  │  ANALYZER HPA (Horizontal Pod Autoscaler)                 │ │  │
│  │  │  • Min Replicas: 2                                         │ │  │
│  │  │  • Max Replicas: 5                                         │ │  │
│  │  │  • Target CPU: 70%                                         │ │  │
│  │  │  • Target Memory: 80%                                      │ │  │
│  │  │  • Scale Up: Fast (100% or 2 pods per 15s)               │ │  │
│  │  │  • Scale Down: Gradual (50% per 15s, 5min stabilization) │ │  │
│  │  └────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React + Nginx)
**File:** `services/frontend/`
**K8s Config:** `k8s/services/frontend-deployment.yaml`

- **Technology:** React 18, Recharts for visualization
- **Container:** Multi-stage build (Node → Nginx)
- **Networking:** LoadBalancer service, proxies API calls to backend
- **Features:**
  - Real-time market data display
  - AI sentiment analysis charts
  - Alert notifications
  - System status monitoring

### 2. Scraper Service
**File:** `services/scraper/app.py`
**K8s Config:** `k8s/services/scraper-deployment.yaml`

- **Technology:** Python Flask, psycopg2, requests
- **External APIs:**
  - Alpha Vantage (market data)
  - NewsAPI (financial news)
- **Features:**
  - REST API for manual triggers
  - Database persistence
  - Rate limiting compliance
- **Endpoints:**
  - `GET /health` - Health check
  - `POST /scrape` - Trigger manual scrape
  - `GET /api/latest-data` - Get latest market data
  - `GET /api/news/<symbol>` - Get news for symbol

### 3. Analyzer Service
**File:** `services/analyzer/app.py`
**K8s Config:** `k8s/services/analyzer-deployment.yaml`

- **Technology:** Python Flask, Google Gemini AI
- **AI Capabilities:**
  - Sentiment analysis using Gemini Pro
  - JSON-structured responses
  - Confidence scoring
- **Signal Aggregation:**
  - Price-based signals
  - Sentiment-based signals
  - Composite scoring algorithm
- **Endpoints:**
  - `GET /health` - Health check
  - `POST /analyze` - Trigger analysis
  - `GET /api/sentiment-summary` - Get sentiment summary
  - `GET /api/signals/<symbol>` - Get trading signals

### 4. Alert Service
**File:** `services/alert/app.py`
**K8s Config:** `k8s/services/alert-deployment.yaml`

- **Technology:** Python Flask, Twilio (optional)
- **Alert Conditions:**
  - Price change > threshold
  - Negative sentiment trends
  - Strong buy/sell signals
- **Notification Channels:**
  - Email (logged to console in demo)
  - SMS via Twilio (optional)
- **Endpoints:**
  - `GET /health` - Health check
  - `POST /check-alerts` - Trigger alert check
  - `GET /api/alerts/recent` - Get recent alerts
  - `GET /api/alerts/<symbol>` - Get alerts for symbol

### 5. PostgreSQL Database
**K8s Config:** `k8s/database/postgres-statefulset.yaml`

- **Type:** StatefulSet (not Deployment)
- **Why StatefulSet?**
  - Stable network identity
  - Persistent storage
  - Ordered deployment/scaling
- **Persistent Volume:** 2Gi dynamically provisioned
- **Service:** Headless (clusterIP: None)
- **Hostname:** `postgres-0.postgres-service`

### 6. Scraper CronJob
**K8s Config:** `k8s/jobs/scraper-cronjob.yaml`

- **Schedule:** Every 30 minutes
- **Concurrency Policy:** Forbid (no overlapping runs)
- **Success History:** Keep last 3 successful jobs
- **Failed History:** Keep last 1 failed job
- **Init Container:** Waits for PostgreSQL

### 7. Analyzer HPA
**K8s Config:** `k8s/autoscaling/analyzer-hpa.yaml`

- **Metrics:** CPU (70%) and Memory (80%)
- **Scale Up Behavior:**
  - Immediate (0s stabilization)
  - Max 100% increase or 2 pods per 15s
- **Scale Down Behavior:**
  - 5 minute stabilization window
  - Max 50% decrease per 15s
- **Why Analyzer?** Most CPU-intensive (AI processing)

## Data Flow

### 1. Scraping Flow
```
External APIs → Scraper Service → PostgreSQL
     ↑              ↓
CronJob      market_data table
            news_articles table
```

### 2. Analysis Flow
```
PostgreSQL → Analyzer Service → Google Gemini API
news_articles   ↓                      ↓
          sentiment_analysis      AI Results
          trading_signals
```

### 3. Alert Flow
```
PostgreSQL → Alert Service → Email/SMS
trading_signals  ↓              ↓
sentiment     Check          Notifications
market_data  Conditions
              ↓
         alerts table
```

### 4. Display Flow
```
PostgreSQL → Backend Services → Frontend → User Browser
  All Tables    API Responses    React UI    Dashboard
```

## Kubernetes Concepts Demonstrated

### StatefulSets
- **File:** `k8s/database/postgres-statefulset.yaml`
- **Features:**
  - Ordered pod names (postgres-0, postgres-1...)
  - Stable network identities
  - Persistent volume per pod
  - Ordered deployment and scaling
- **Use Case:** Databases, distributed systems

### Deployments
- **Files:** `k8s/services/*-deployment.yaml`
- **Features:**
  - Replica management
  - Rolling updates
  - Self-healing
- **Use Case:** Stateless applications

### CronJobs
- **File:** `k8s/jobs/scraper-cronjob.yaml`
- **Features:**
  - Scheduled execution
  - Job history management
  - Concurrency control
- **Use Case:** Periodic tasks

### HorizontalPodAutoscaler
- **File:** `k8s/autoscaling/analyzer-hpa.yaml`
- **Features:**
  - Automatic scaling based on metrics
  - CPU and memory targets
  - Scale up/down policies
- **Use Case:** Variable load handling

### Services
- **Types Used:**
  - **ClusterIP:** Internal service communication
  - **Headless:** StatefulSet (postgres)
  - **LoadBalancer:** External access (frontend)
- **Features:**
  - Service discovery
  - Load balancing
  - DNS resolution

### ConfigMaps & Secrets
- **Files:** `k8s/config/*.yaml`
- **ConfigMaps:** Non-sensitive configuration
- **Secrets:** API keys, passwords
- **Usage:** Environment variables in pods

### Persistent Volumes
- **Volume Claim Templates** in StatefulSet
- **Dynamic Provisioning** by Kubernetes
- **Use Case:** Database data persistence

### Init Containers
- **Used in:** All service deployments
- **Purpose:** Wait for PostgreSQL before starting
- **Command:** `nc -z postgres-0.postgres-service 5432`

### Health Checks
- **Liveness Probes:** Container is alive
- **Readiness Probes:** Container ready for traffic
- **Used in:** All deployments

### Resource Management
- **Requests:** Guaranteed resources
- **Limits:** Maximum resources
- **Purpose:** Efficient scheduling, prevent resource exhaustion

## Network Architecture

```
External Traffic
     ↓
LoadBalancer (frontend-service)
     ↓
Frontend Pods (80)
     ↓
Internal ClusterIP Services
     ↓
┌──────────────┬──────────────┬──────────────┐
│   Scraper    │   Analyzer   │    Alert     │
│   (5000)     │   (5001)     │   (5002)     │
└──────┬───────┴──────┬───────┴──────┬───────┘
       └──────────────┴──────────────┘
                      ↓
              PostgreSQL
            postgres-0.postgres-service
                   (5432)
```

## Security Considerations

### Implemented
- Non-root containers
- Secret management for sensitive data
- Resource limits to prevent DoS
- Health checks for stability

### Production Recommendations
- Add Network Policies
- Implement RBAC
- Use TLS for inter-service communication
- Rotate secrets regularly
- Implement Pod Security Policies
- Add image scanning

## Scaling Strategy

### Current Configuration
- **Frontend:** 2 replicas (can scale manually)
- **Scraper:** 1 replica (data consistency)
- **Analyzer:** 2-5 replicas (HPA enabled)
- **Alert:** 1 replica (event-driven)
- **Database:** 1 replica (StatefulSet)

### Scaling Recommendations
- **Read Replicas:** Add PostgreSQL read replicas
- **Cache Layer:** Redis for frequently accessed data
- **Message Queue:** RabbitMQ/Kafka for async processing
- **More HPA:** Enable for scraper and alert services

## Monitoring & Observability

### Current Approach
- Health check endpoints on all services
- Kubernetes pod status monitoring
- Resource usage via kubectl top

### Production Recommendations
- **Metrics:** Prometheus for metrics collection
- **Visualization:** Grafana dashboards
- **Logging:** EFK stack (Elasticsearch, Fluentd, Kibana)
- **Tracing:** Jaeger for distributed tracing
- **Alerting:** Alertmanager for notifications

## Technology Stack

### Backend Services
- **Language:** Python 3.11
- **Framework:** Flask
- **Database Driver:** psycopg2
- **AI/ML:** Google Generative AI (Gemini)
- **HTTP Client:** requests
- **WSGI Server:** Gunicorn

### Frontend
- **Framework:** React 18
- **Build Tool:** react-scripts (Create React App)
- **Charting:** Recharts
- **HTTP Client:** axios
- **Web Server:** Nginx

### Database
- **RDBMS:** PostgreSQL 15
- **Storage:** Persistent Volumes

### Infrastructure
- **Orchestration:** Kubernetes (Docker Desktop)
- **Containerization:** Docker
- **Base Images:** 
  - python:3.11-slim
  - node:18-alpine
  - postgres:15
  - nginx:alpine

## File Structure

```
fintech-k8s-system/
├── README.md                      # Comprehensive documentation
├── QUICKSTART.md                  # Quick start guide
├── setup.sh                       # Environment setup script
├── build.sh                       # Docker build script
├── deploy.sh                      # Kubernetes deployment script
├── .env                           # Environment variables (gitignored)
│
├── services/                      # Microservices source code
│   ├── scraper/
│   │   ├── app.py                # Market data scraper
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── analyzer/
│   │   ├── app.py                # AI sentiment analyzer
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── alert/
│   │   ├── app.py                # Alert notification service
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/
│       ├── src/
│       │   ├── App.js            # React main component
│       │   ├── App.css           # Styles
│       │   ├── index.js
│       │   └── index.css
│       ├── public/
│       │   └── index.html
│       ├── package.json
│       ├── nginx.conf
│       └── Dockerfile
│
├── k8s/                          # Kubernetes configurations
│   ├── database/
│   │   ├── postgres-statefulset.yaml    # StatefulSet demo
│   │   └── postgres-service.yaml
│   ├── services/
│   │   ├── scraper-deployment.yaml
│   │   ├── analyzer-deployment.yaml
│   │   ├── alert-deployment.yaml
│   │   └── frontend-deployment.yaml
│   ├── jobs/
│   │   └── scraper-cronjob.yaml         # CronJob demo
│   ├── autoscaling/
│   │   └── analyzer-hpa.yaml            # HPA demo
│   └── config/
│       ├── postgres-config.yaml
│       ├── postgres-secret.yaml
│       ├── app-config.yaml
│       └── api-keys-secret.yaml
│
└── scripts/
    ├── init-db.sql               # Database schema
    └── load-test.sh              # HPA testing script
```

## Resource Requirements

### Minimum (for 8GB M2 Mac)
- **Docker Desktop:** 4GB RAM
- **Kubernetes:** 2GB RAM
- **Total System:** 8GB RAM

### Per Pod (as configured)
- **Frontend:** 64Mi-128Mi
- **Scraper:** 128Mi-256Mi
- **Analyzer:** 256Mi-512Mi (×2-5 pods)
- **Alert:** 128Mi-256Mi
- **PostgreSQL:** 256Mi-512Mi
- **Total:** ~1.5GB-3GB (scales with HPA)

## API Rate Limits

### External APIs (Free Tiers)
- **Alpha Vantage:** 25 requests/day (demo key)
- **NewsAPI:** 100 requests/day
- **Google Gemini:** 60 requests/minute

### Mitigation Strategies
- CronJob runs every 30 minutes (48 times/day)
- Adjust schedule in `k8s/jobs/scraper-cronjob.yaml`
- Implement caching layer
- Upgrade to paid tiers

## Future Enhancements

### Short Term
- [ ] Add Ingress controller
- [ ] Implement WebSocket for real-time updates
- [ ] Add more stock symbols
- [ ] Implement data visualization improvements

### Medium Term
- [ ] PostgreSQL read replicas
- [ ] Redis caching layer
- [ ] Prometheus + Grafana monitoring
- [ ] CI/CD pipeline (GitHub Actions)

### Long Term
- [ ] Service mesh (Istio/Linkerd)
- [ ] Multi-region deployment
- [ ] Machine learning model improvements
- [ ] Kafka for event streaming
- [ ] Custom CRDs and operators

---

**This architecture demonstrates production-grade Kubernetes patterns while remaining accessible for learning and development on an M2 Mac.**
