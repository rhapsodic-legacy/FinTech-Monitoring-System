#!/bin/bash

set -e

echo "🚀 FinTech K8s System - Setup Script for M2 Mac"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Warning: This script is optimized for macOS. Proceed with caution.${NC}"
fi

# Check Docker
echo -e "\n${YELLOW}Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker not found. Please install Docker Desktop for Mac.${NC}"
    echo "Visit: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Check kubectl
echo -e "\n${YELLOW}Checking kubectl...${NC}"
if ! command -v kubectl &> /dev/null; then
    echo -e "${YELLOW}kubectl not found. Installing...${NC}"
    if command -v brew &> /dev/null; then
        brew install kubectl
    else
        echo -e "${RED}Homebrew not found. Please install kubectl manually.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ kubectl installed${NC}"

# Check Kubernetes cluster
echo -e "\n${YELLOW}Checking Kubernetes cluster...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Kubernetes cluster not accessible.${NC}"
    echo "Please enable Kubernetes in Docker Desktop:"
    echo "  Docker Desktop → Settings → Kubernetes → Enable Kubernetes"
    exit 1
fi

echo -e "${GREEN}✓ Kubernetes cluster is accessible${NC}"

# Check Python
echo -e "\n${YELLOW}Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found. Installing...${NC}"
    if command -v brew &> /dev/null; then
        brew install python@3.11
    else
        echo -e "${RED}Please install Python 3.11+ manually.${NC}"
        exit 1
    fi
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} installed${NC}"

# Check Node.js
echo -e "\n${YELLOW}Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Node.js not found. Installing...${NC}"
    if command -v brew &> /dev/null; then
        brew install node@18
    else
        echo -e "${RED}Please install Node.js 18+ manually.${NC}"
        exit 1
    fi
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js ${NODE_VERSION} installed${NC}"

# Create directory structure
echo -e "\n${YELLOW}Creating directory structure...${NC}"
mkdir -p services/{scraper,analyzer,alert,frontend}
mkdir -p k8s/{database,services,jobs,autoscaling,config,ingress}
mkdir -p scripts

echo -e "${GREEN}✓ Directory structure created${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file...${NC}"
    cat > .env << 'EOF'
# Database Configuration
POSTGRES_USER=fintech_user
POSTGRES_PASSWORD=change_me_in_production_12345
POSTGRES_DB=fintech_db
POSTGRES_HOST=postgres-service
POSTGRES_PORT=5432

# API Keys (Get free keys from the respective services)
ALPHA_VANTAGE_KEY=demo
NEWS_API_KEY=your_newsapi_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Twilio Configuration (Optional - for SMS alerts)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Alert Configuration
ALERT_EMAIL=your_email@example.com
ALERT_PHONE=+1234567890

# Service Configuration
SCRAPER_PORT=5000
ANALYZER_PORT=5001
ALERT_PORT=5002
FRONTEND_PORT=3000

# Stock Symbols to Monitor
STOCK_SYMBOLS=AAPL,GOOGL,MSFT,TSLA,AMZN

# Alert Thresholds
PRICE_CHANGE_THRESHOLD=5.0
SENTIMENT_THRESHOLD=-0.3
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys!${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create Python virtual environments for services
echo -e "\n${YELLOW}Setting up Python virtual environments...${NC}"

for service in scraper analyzer alert; do
    if [ ! -d "services/${service}/venv" ]; then
        echo "Creating venv for ${service}..."
        cd services/${service}
        python3 -m venv venv
        cd ../..
    fi
done

echo -e "${GREEN}✓ Virtual environments created${NC}"

# Check metrics-server for HPA
echo -e "\n${YELLOW}Checking metrics-server for HPA...${NC}"
if ! kubectl get deployment metrics-server -n kube-system &> /dev/null; then
    echo -e "${YELLOW}metrics-server not found. Would you like to install it? (y/n)${NC}"
    read -r install_metrics
    if [[ "$install_metrics" == "y" ]]; then
        kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
        # Patch for Docker Desktop on Mac
        sleep 5
        kubectl patch deployment metrics-server -n kube-system --type='json' \
          -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]' || true
        echo -e "${GREEN}✓ metrics-server installed${NC}"
    fi
else
    echo -e "${GREEN}✓ metrics-server already installed${NC}"
fi

# Summary
echo -e "\n${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Edit .env file and add your API keys:"
echo "   - Alpha Vantage: https://www.alphavantage.co/support/#api-key"
echo "   - NewsAPI: https://newsapi.org/register"
echo "   - Google Gemini: https://ai.google.dev/"
echo ""
echo "2. Build Docker images:"
echo "   ./build.sh"
echo ""
echo "3. Deploy to Kubernetes:"
echo "   kubectl create namespace fintech"
echo "   kubectl apply -f k8s/"
echo ""
echo "4. Access the frontend:"
echo "   kubectl port-forward svc/frontend-service 3000:80 -n fintech"
echo "   Open http://localhost:3000"
echo ""
echo -e "${YELLOW}For detailed instructions, see README.md${NC}"
