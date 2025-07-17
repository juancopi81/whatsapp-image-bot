# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On macOS/Linux
uv sync

# Install development dependencies
uv sync --group dev
```

### Running the Application

```bash
# Run the FastAPI development server
uvicorn src.whatsapp_image_bot.app:app --reload

# Alternative: Run directly with Python
python -m src.whatsapp_image_bot.app

# Server runs on http://127.0.0.1:8000
# API docs available at http://127.0.0.1:8000/docs
```

### Code Quality and Testing

```bash
# Run linting and formatting
ruff check .
ruff format .
black .

# Run tests
pytest

# Run specific test file
pytest tests/test_image_processor.py
```

### Development Workflow

```bash
# Expose local server for Twilio webhooks
ngrok http 8000
```

## Project Architecture

### Core Components

**FastAPI Application Structure:**

- `src/whatsapp_image_bot/app.py` - Main FastAPI application with health check and root endpoints
- `src/whatsapp_image_bot/config.py` - Configuration management using environment variables
- `src/whatsapp_image_bot/api/` - API routes and webhook handlers
- `src/whatsapp_image_bot/services/` - Business logic and orchestration
- `src/whatsapp_image_bot/clients/` - External API integrations
- `src/whatsapp_image_bot/utils/` - Utility functions and helpers

### Key Services

**Image Processing Pipeline:**

1. **Webhook Handler** (`api/webhooks.py`) - Receives Twilio webhook with image
2. **Image Processor** (`services/image_processor.py`) - Orchestrates the full workflow:
   - Calls FalClient to stylize image using fal.ai API
   - Downloads stylized image bytes
   - Uploads to S3 via S3StorageService
   - Returns public S3 URL
3. **WhatsApp Client** (`services/whatsapp_client.py`) - Sends reply messages via Twilio

**External Integrations:**

- **FalClient** (`clients/fal_client.py`) - Integrates with fal.ai API for AI image stylization using "flux-pro/kontext/max" model with Simpson style prompt
- **S3StorageService** (`services/cloud_storage.py`) - Handles file uploads to AWS S3 bucket
- **WhatsAppClient** (`services/whatsapp_client.py`) - Twilio API wrapper for sending WhatsApp messages

### Data Flow

1. User sends image to WhatsApp → Twilio webhook → `/api/` endpoint
2. Webhook extracts image URL and message metadata
3. `process_image()` function:
   - Stylizes image via fal.ai (converts to Simpson style)
   - Downloads stylized image bytes
   - Uploads to S3 with unique filename: `processed/{message_sid}_{timestamp}.jpg`
   - Returns public S3 URL
4. WhatsApp client sends stylized image back to user

### Configuration

**Required Environment Variables:**

- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` - Twilio integration
- `FAL_KEY` - fal.ai API authentication
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET_NAME` - S3 storage

### Development Status

The project is in active development with core infrastructure complete:

- ✅ FastAPI application structure
- ✅ Twilio webhook integration
- ✅ fal.ai client implementation
- ✅ S3 storage service
- ✅ WhatsApp client wrapper
- ✅ Image processing orchestrator
- ⚠️ Full end-to-end workflow integration in progress

### Testing

Tests are organized by component:

- `tests/test_routes.py` - API endpoint tests
- `tests/test_image_processor.py` - Image processing workflow tests
- `tests/test_cloud_storage.py` - S3 storage service tests
- `tests/test_api_clients.py` - External API client tests

Use `pytest` to run all tests or target specific test files for focused testing.

## Commit Message Guidelines

- Commit messages should follow a structured format:
  - **Type**: Describes the kind of change (e.g., feat, fix, docs, style, refactor, test, chore)
  - **Scope**: Indicates the part of the project affected (e.g., api, services, clients)
  - **Description**: A clear, concise explanation of the change
  - Example format:

```
feat(services): Implement core image processing orchestrator

Adds the main image processing service, which acts as the brain of the application, handling the end-to-end image stylization workflow.

The new 'process_image' function orchestrates the following steps:
- Calls the FalClient to stylize the user's image.
- Downloads the resulting image bytes from the temporary URL.
- Generates a unique object name for S3 using the message SID and a timestamp.
- Uploads the image to the S3 bucket, running the synchronous boto3 call in a non-blocking thread using asyncio.to_thread.
- Returns the permanent public URL of the final image.

This service connects the AI client, the downloader utility, and the cloud storage service. It includes comprehensive logging and error handling to ensure the process is resilient and traceable.
```
