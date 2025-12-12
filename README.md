# FinTech Kubernetes Monitoring System           

A production grade financial monitoring system built to demonstrate advanced Kubernetes orchestration patterns and microservices architecture. The system aggregates real time market data, performs AI-powered sentiment analysis on financial news, and generates automated trading signals with configurable alert thresholds.
    
## System Overview  

This application implements a complete data pipeline using event-driven microservices architecture. Market data flows from external APIs through a scraper service into a PostgreSQL database. An analyzer service processes this data alongside news articles using Google's Gemini AI to generate sentiment scores and composite trading signals. An alert service monitors these signals and triggers notifications when specified thresholds are exceeded. A React based dashboard provides real-time visualization of market movements, sentiment trends, and system status.
  
## Learning Objectives 

This project was developed as a practical learning exercise to gain hands on experience with Kubernetes orchestration, container deployment patterns, and cloud native application architecture. The implementation focuses on demonstrating production ready patterns including StatefulSets for stateful workloads, CronJobs for scheduled tasks, Horizontal Pod Autoscaling for dynamic resource management, and proper configuration management through ConfigMaps and Secrets.
 
## Architecture Components
 
### Backend Services

The **Scraper Service** is a Python Flask application that interfaces with Alpha Vantage for market data and NewsAPI for financial news. It implements retry logic, rate limiting compliance, and stores normalized data in PostgreSQL with appropriate indexing for query performance.

The **Analyzer Service** leverages Google Gemini AI to perform sentiment analysis on news articles. It aggregates multiple data sources to generate composite trading signals based on both technical price movements and sentiment trends. The service is designed to handle variable load through horizontal pod autoscaling.

The **Alert Service** monitors trading signals and market conditions against configurable thresholds. It implements a notification system supporting both email and SMS delivery (via Twilio), with alert deduplication and history tracking.

### Data Layer

PostgreSQL runs as a StatefulSet with persistent volume claims to ensure data durability across pod restarts. The database schema includes proper indexing strategies for time-series queries and implements referential integrity for relational data.

### Frontend

A React-based dashboard provides real time visualization using Recharts. The application displays market data cards, sentiment analysis charts, alert feeds, and Kubernetes resource status. The frontend is containerized using multi stage Docker builds with Nginx serving the production bundle.

### Kubernetes Infrastructure

The deployment demonstrates several key Kubernetes concepts:

**StatefulSets** manage the PostgreSQL database with ordered deployment, stable network identities, and persistent storage through dynamically provisioned volumes.

**Deployments** handle the stateless microservices with replica management, rolling update strategies, and health check configurations using liveness and readiness probes.

**CronJobs** execute scheduled data collection every 30 minutes with concurrency controls and job history limits.

**HorizontalPodAutoscaler** dynamically scales the analyzer service based on CPU utilization with configurable scale-up and scale-down policies.

**Services** provide stable networking with ClusterIP for internal communication, a headless service for StatefulSet DNS, and LoadBalancer for external frontend access.

**ConfigMaps and Secrets** manage application configuration and sensitive credentials with proper separation of concerns.

## Technical Stack

Backend services are written in Python 3.11 using Flask with psycopg2 for database connectivity. The frontend uses React 18 with Recharts for data visualization. PostgreSQL 15 provides persistent storage. All services are containerized using Docker with multi-stage builds for optimized image sizes. Kubernetes orchestrates the entire system with configurations optimized for local development on Docker Desktop.

## Potential Improvements

The system could be enhanced by implementing a message queue such as RabbitMQ or Apache Kafka to decouple service communication and enable event streaming. Adding Prometheus for metrics collection and Grafana for monitoring dashboards would provide better observability. Implementing an Istio service mesh would enable advanced traffic management and security policies. The analyzer service could be extended with more sophisticated machine learning models, potentially using TensorFlow or PyTorch for predictive analytics. A CI/CD pipeline using GitHub Actions or ArgoCD would automate testing and deployment. Adding WebSocket support would enable real-time data streaming to the frontend without polling. The database could be configured with read replicas to improve query performance under load. Implementing Helm charts would simplify deployment configuration and environment management.

---

## Getting Started

See (QUICKSTART.md) for setup instructions or (README.md) for comprehensive documentation.
