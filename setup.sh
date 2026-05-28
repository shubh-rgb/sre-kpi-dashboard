#!/bin/bash
# Quick setup script for enhanced dashboard system

set -e

echo "================================"
echo "SRE KPI Dashboard Setup"
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create directories
echo "📁 Creating directories..."
mkdir -p pipeline/documents
mkdir -p grafana/provisioning/dashboards

# Check if documents folder exists
if [ ! -d "pipeline/documents" ]; then
    echo "❌ Failed to create documents folder"
    exit 1
fi

echo "✅ Directories created"

# Show instructions
echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Add CSV files to: pipeline/documents/"
echo "   Example:"
echo "   cp my_data.csv pipeline/documents/"
echo ""
echo "2. Start the stack:"
echo "   docker-compose up --build"
echo ""
echo "3. Open Grafana:"
echo "   http://localhost:3000"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "4. (Optional) Enable Freshservice:"
echo "   Edit docker-compose.yml and set:"
echo "   - LOAD_FRESHSERVICE_DATA: \"true\""
echo "   - FRESHSERVICE_API_KEY: \"your-key\""
echo "   - FRESHSERVICE_DOMAIN: \"your-domain\""
echo ""
echo "================================"
echo ""
