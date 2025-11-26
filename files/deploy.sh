#!/bin/bash

set -e

echo "🚀 Deploying FinTech K8s System"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if namespace exists
if kubectl get namespace fintech &> /dev/null; then
    echo -e "${YELLOW}Namespace 'fintech' already exists${NC}"
else
    echo -e "${YELLOW}Creating namespace 'fintech'...${NC}"
    kubectl create namespace fintech
    echo -e "${GREEN}✓ Namespace created${NC}"
fi

# Apply configurations in order
echo -e "\n${YELLOW}1. Applying ConfigMaps and Secrets...${NC}"
kubectl apply -f k8s/config/

echo -e "\n${YELLOW}2. Deploying PostgreSQL StatefulSet...${NC}"
kubectl apply -f k8s/database/

echo -e "\n${YELLOW}3. Waiting for PostgreSQL to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres -n fintech --timeout=180s

echo -e "\n${YELLOW}4. Deploying microservices...${NC}"
kubectl apply -f k8s/services/

echo -e "\n${YELLOW}5. Deploying CronJob...${NC}"
kubectl apply -f k8s/jobs/

echo -e "\n${YELLOW}6. Setting up HorizontalPodAutoscaler...${NC}"
kubectl apply -f k8s/autoscaling/

echo -e "\n${YELLOW}7. Waiting for all pods to be ready...${NC}"
kubectl wait --for=condition=ready pod --all -n fintech --timeout=300s || echo "Some pods may still be starting..."

echo -e "\n${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}Deployment Status:${NC}"
kubectl get pods -n fintech

echo -e "\n${YELLOW}Services:${NC}"
kubectl get svc -n fintech

echo -e "\n${YELLOW}HPA Status:${NC}"
kubectl get hpa -n fintech

echo -e "\n${YELLOW}CronJobs:${NC}"
kubectl get cronjobs -n fintech

echo -e "\n${GREEN}Access the application:${NC}"
echo "1. Port forward to frontend:"
echo "   kubectl port-forward -n fintech svc/frontend-service 3000:80"
echo ""
echo "2. Open http://localhost:3000 in your browser"
echo ""
echo "3. Monitor logs:"
echo "   kubectl logs -f deployment/scraper-service -n fintech"
echo "   kubectl logs -f deployment/analyzer-service -n fintech"
echo "   kubectl logs -f deployment/alert-service -n fintech"
echo ""
echo "4. Trigger manual scrape:"
echo "   kubectl exec -it deployment/scraper-service -n fintech -- curl -X POST http://localhost:5000/scrape"
echo ""
echo "5. Check database:"
echo "   kubectl exec -it postgres-0 -n fintech -- psql -U fintech_user -d fintech_db"
