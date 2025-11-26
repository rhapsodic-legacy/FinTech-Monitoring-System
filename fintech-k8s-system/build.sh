#!/bin/bash

set -e

echo "🐳 Building Docker Images for FinTech K8s System"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Build scraper service
echo -e "\n${YELLOW}Building scraper service...${NC}"
cd services/scraper
docker build -t fintech-scraper:latest .
echo -e "${GREEN}✓ Scraper service built${NC}"
cd ../..

# Build analyzer service
echo -e "\n${YELLOW}Building analyzer service...${NC}"
cd services/analyzer
docker build -t fintech-analyzer:latest .
echo -e "${GREEN}✓ Analyzer service built${NC}"
cd ../..

# Build alert service
echo -e "\n${YELLOW}Building alert service...${NC}"
cd services/alert
docker build -t fintech-alert:latest .
echo -e "${GREEN}✓ Alert service built${NC}"
cd ../..

# Build frontend
echo -e "\n${YELLOW}Building frontend...${NC}"
cd services/frontend
docker build -t fintech-frontend:latest .
echo -e "${GREEN}✓ Frontend built${NC}"
cd ../..

echo -e "\n${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}All images built successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}Built images:${NC}"
docker images | grep fintech

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Create namespace: kubectl create namespace fintech"
echo "2. Deploy to Kubernetes: kubectl apply -f k8s/"
echo "3. Check status: kubectl get pods -n fintech"
