#!/bin/bash

# WhatsApp Image Bot Deployment Script

set -e  # Exit on any error

echo "=� Starting WhatsApp Image Bot deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "L Error: .env file not found!"
    echo "Please create a .env file with the required environment variables:"
    echo "  - TWILIO_ACCOUNT_SID"
    echo "  - TWILIO_AUTH_TOKEN"
    echo "  - TWILIO_PHONE_NUMBER"
    echo "  - FAL_KEY"
    echo "  - AWS_ACCESS_KEY_ID"
    echo "  - AWS_SECRET_ACCESS_KEY"
    echo "  - AWS_REGION"
    echo "  - S3_BUCKET_NAME"
    exit 1
fi

# Load environment variables
source .env

# Navigate to project root
cd "$(dirname "$0")/.."

echo "=� Building Docker image..."
docker-compose -f docker/docker-compose.yml build

echo "<� Starting services..."
docker-compose -f docker/docker-compose.yml up -d

echo "� Waiting for services to be ready..."
sleep 10

# Check if the service is healthy
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo " WhatsApp Image Bot is running successfully!"
    echo "< API available at: http://localhost:8000"
    echo "=� API docs at: http://localhost:8000/docs"
    echo ""
    echo "To view logs: docker-compose -f docker/docker-compose.yml logs -f"
    echo "To stop: docker-compose -f docker/docker-compose.yml down"
else
    echo "L Health check failed. Check logs with:"
    echo "docker-compose -f docker/docker-compose.yml logs"
    exit 1
fi