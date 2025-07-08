# WhatsApp Image Stylization Bot - Development Guide

## Overview
This guide outlines the step-by-step development process for building a WhatsApp bot that receives images via webhook, applies Simpsons-style processing through external APIs, and returns the stylized image.

## Prerequisites
- Python 3.8+
- Flask framework knowledge
- Access to image processing API (fal.ai or Replicate)
- Cloud storage service (Cloudinary or AWS S3)
- WhatsApp Business API or Twilio integration

## Recommended layout

```text
whatsapp-image-bot/
├── README.md
├── DEVELOPMENT_GUIDE.md
├── pyproject.toml
├── uv.lock                # Created after adding dependencies with uv
├── .python-version        # Python version pin (created by uv)
├── .env.example
├── .gitignore
├── src/
│   └── whatsapp_image_bot/
│       ├── __init__.py
│       ├── app.py                # Flask application factory
│       ├── config.py             # Configuration management
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py         # Flask routes/endpoints
│       │   └── webhooks.py       # Webhook handlers
│       ├── services/
│       │   ├── __init__.py
│       │   ├── image_processor.py # API calls to fal.ai/Replicate
│       │   ├── cloud_storage.py   # Cloudinary/S3 upload
│       │   └── whatsapp_client.py # WhatsApp API integration
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── helpers.py         # General utility functions
│       │   └── validators.py      # Input validation
│       └── clients/               # External API clients
│           ├── __init__.py
│           ├── fal_client.py      # fal.ai API client
│           └── replicate_client.py # Replicate API client
├── tests/
│   ├── __init__.py
│   ├── test_routes.py
│   ├── test_image_processor.py
│   ├── test_cloud_storage.py
│   └── test_api_clients.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── scripts/
    ├── setup.py
    └── deploy.sh
```

_Note: `.venv/` is auto-managed by uv and should be included in `.gitignore`._

## Development Phases

### Phase 1: Project Setup & Configuration
**Goal**: Establish project foundation and environment

**Tasks**:
- Set up virtual environment and dependencies
- Configure project structure according to recommended layout
- Create configuration management system
- Set up environment variables (.env)
- Initialize git repository with proper .gitignore

**Completion Criteria**:
- [ ] Project structure matches recommended layout
- [ ] Flask app runs successfully with basic "Hello World" endpoint
- [ ] Configuration loads environment variables correctly
- [ ] All dependencies install without errors

### Phase 2: Core Flask Application
**Goal**: Create basic web server with webhook endpoint

**Tasks**:
- Implement Flask application factory pattern
- Create webhook endpoint for receiving WhatsApp messages
- Add request validation and error handling
- Set up logging system
- Create health check endpoint

**Completion Criteria**:
- [ ] Flask app starts without errors
- [ ] Webhook endpoint responds to POST requests
- [ ] Request validation works for required fields
- [ ] Logs are properly formatted and saved
- [ ] Health check endpoint returns 200 OK

### Phase 3: WhatsApp Integration
**Goal**: Handle incoming WhatsApp messages and extract image URLs

**Tasks**:
- Implement WhatsApp webhook request parsing
- Extract image URLs from incoming messages
- Validate image URL accessibility
- Handle different message types gracefully
- Implement response formatting for WhatsApp

**Completion Criteria**:
- [ ] Successfully parses WhatsApp webhook payloads
- [ ] Extracts image URLs from messages
- [ ] Validates image URLs are accessible
- [ ] Handles non-image messages appropriately
- [ ] Sends properly formatted responses back to WhatsApp

### Phase 4: Image Download & Validation
**Goal**: Download images from URLs and validate them

**Tasks**:
- Implement image download functionality
- Add image format validation (JPEG, PNG, etc.)
- Implement file size limits
- Add image corruption detection
- Handle download timeouts and errors

**Completion Criteria**:
- [ ] Downloads images from URLs successfully
- [ ] Validates supported image formats
- [ ] Rejects oversized images
- [ ] Handles corrupted or invalid images
- [ ] Manages download timeouts gracefully

### Phase 5: External API Integration
**Goal**: Connect to image processing APIs (fal.ai/Replicate)

**Tasks**:
- Implement API client for chosen service (fal.ai or Replicate)
- Add authentication handling
- Implement image upload to processing service
- Handle API rate limits and errors
- Add retry logic for failed requests

**Completion Criteria**:
- [ ] Successfully authenticates with chosen API
- [ ] Uploads images to processing service
- [ ] Receives processed image URLs
- [ ] Handles API errors and rate limits
- [ ] Implements exponential backoff for retries

### Phase 6: Cloud Storage Integration
**Goal**: Upload processed images to cloud storage

**Tasks**:
- Implement cloud storage client (Cloudinary or AWS S3)
- Add file upload functionality
- Generate public URLs for uploaded images
- Implement file cleanup/lifecycle management
- Add error handling for upload failures

**Completion Criteria**:
- [ ] Uploads images to cloud storage successfully
- [ ] Generates accessible public URLs
- [ ] Handles upload failures gracefully
- [ ] Implements file cleanup policies
- [ ] Manages storage quotas/limits

### Phase 7: End-to-End Workflow
**Goal**: Integrate all components into complete workflow

**Tasks**:
- Chain all services together (webhook → download → process → upload → respond)
- Add comprehensive error handling
- Implement status tracking for long-running processes
- Add request timeout handling
- Create workflow logging

**Completion Criteria**:
- [ ] Complete image processing workflow works end-to-end
- [ ] Handles errors at each step appropriately
- [ ] Provides meaningful error messages to users
- [ ] Processes requests within acceptable timeframes
- [ ] Logs workflow progress accurately

### Phase 8: Testing & Quality Assurance
**Goal**: Ensure reliability and robustness

**Tasks**:
- Write unit tests for all services
- Create integration tests for workflows
- Add mock testing for external APIs
- Implement load testing
- Add error scenario testing

**Completion Criteria**:
- [ ] Unit tests achieve >80% code coverage
- [ ] Integration tests pass consistently
- [ ] Mock tests simulate API failures
- [ ] Load tests handle expected traffic
- [ ] Error scenarios are properly tested

### Phase 9: Security & Performance
**Goal**: Harden application for production use

**Tasks**:
- Implement input sanitization
- Add rate limiting to endpoints
- Secure API keys and credentials
- Optimize image processing performance
- Add monitoring and alerting

**Completion Criteria**:
- [ ] Input validation prevents injection attacks
- [ ] Rate limiting prevents abuse
- [ ] Credentials are securely stored
- [ ] Performance meets response time requirements
- [ ] Monitoring alerts on failures

### Phase 10: Deployment & Documentation
**Goal**: Deploy application and create operational documentation

**Tasks**:
- Create Docker configuration
- Set up deployment pipeline
- Create operational runbooks
- Document API endpoints
- Create troubleshooting guide

**Completion Criteria**:
- [ ] Application deploys successfully via Docker
- [ ] Deployment pipeline works reliably
- [ ] Documentation is complete and accurate
- [ ] API endpoints are properly documented
- [ ] Troubleshooting guide covers common issues

## Testing Strategy

### Unit Tests
- Test individual service functions
- Mock external API calls
- Validate input/output handling

### Integration Tests
- Test complete workflows
- Use test instances of external services
- Validate error propagation

### Load Tests
- Simulate concurrent users
- Test API rate limit handling
- Validate performance under load

## Monitoring & Maintenance

### Key Metrics
- Request processing time
- Error rates by service
- External API response times
- Storage usage
- User engagement

### Alerts
- High error rates
- API failures
- Storage quota exceeded
- Performance degradation

## Success Criteria
The application is considered complete when:
- All phase completion criteria are met
- End-to-end workflow processes images successfully
- Error handling provides meaningful user feedback
- Performance meets defined SLAs
- Security requirements are satisfied
- Documentation is comprehensive and accurate