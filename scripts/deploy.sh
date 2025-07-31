#!/bin/bash

# WhatsApp Image Bot Deployment Script

set -e  # Exit on any error

echo "🚀 Starting WhatsApp Image Bot deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
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

echo "🔨 Building Docker image..."
docker-compose -f docker/docker-compose.yml build

echo "🚀 Starting services..."
docker-compose -f docker/docker-compose.yml up -d

echo "⏳ Waiting for services to be ready..."

# Health check with retry logic
MAX_ATTEMPTS=30
ATTEMPT=1
SLEEP_DURATION=2

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "  Attempt $ATTEMPT/$MAX_ATTEMPTS: Checking health..."
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ WhatsApp Image Bot is running successfully!"
        echo "🌐 API available at: http://localhost:8000"
        echo "📖 API docs at: http://localhost:8000/docs"
        echo ""
        echo "To view logs: docker-compose -f docker/docker-compose.yml logs -f"
        echo "To stop: docker-compose -f docker/docker-compose.yml down"
        exit 0
    fi
    
    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        sleep $SLEEP_DURATION
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
done

# Health check failed
echo "❌ Health check failed after $MAX_ATTEMPTS attempts. Recent logs:"
docker-compose -f docker/docker-compose.yml logs --tail=20
echo ""
echo "Full logs available with: docker-compose -f docker/docker-compose.yml logs"
exit 1