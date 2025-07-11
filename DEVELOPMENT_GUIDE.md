# WhatsApp Image Stylization Bot - Development Guide

## Overview

This guide outlines the step-by-step development process for building a WhatsApp bot that receives images via webhook, applies Simpsons-style processing through external APIs, and returns the stylized image.

## Prerequisites

- Python 3.8+
- FastAPI framework knowledge
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
│       ├── app.py                # FastAPI application factory
│       ├── config.py             # Configuration management
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py         # FastAPI routes/endpoints
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

### Phase 1: Foundation & Core API

**Goal**: Establish the project, configure it, and create a functional webhook that validates incoming data. This phase combines initial setup with the creation of the main API endpoint.

**Tasks**:

- Set up the project structure and initialize the `git` repository.
- Use `uv` to set up the virtual environment and manage dependencies in `pyproject.toml`.
- Implement `config.py` to load all necessary environment variables from a `.env` file.
- Create the main FastAPI application in `app.py`.
- Define a Pydantic model to represent the expected data from a Twilio webhook.
- Implement the primary webhook endpoint in the `api` module, using the Pydantic model for automatic request validation.
- Create a `/health` endpoint for monitoring.

**Completion Criteria**:

- [x] Project structure is in place.
- [x] All initial dependencies (`fastapi`, `uvicorn`, `python-dotenv`, `twilio`) install correctly using `uv`.
- [x] The FastAPI server runs successfully via `uvicorn`.
- [x] The `/health` endpoint returns a `200 OK` status.
- [x] The webhook endpoint correctly receives and validates test data from Twilio, automatically rejecting invalid requests.

---

### Phase 2: External Service Integration

**Goal**: Build the clients that communicate with all external APIs, keeping each one modular and independent.

**Tasks**:

- In `clients/fal_client.py`, implement the functions to communicate with the `fal.ai` API (handle authentication, send requests, and parse responses).
- In `services/cloud_storage.py`, implement functions to upload image data to your chosen provider (e.g., S3 or Cloudinary) and return a public URL.
- In `services/whatsapp_client.py`, create a simple wrapper around the Twilio library. This should provide clean methods like `send_reply(to, body, media_url)` to hide Twilio-specific logic.

**Completion Criteria**:

- [x] The external AI API client (`fal_client.py`) can successfully authenticate and get a response from the service.
- [ ] The cloud storage service (`cloud_storage.py`) can successfully upload a test file and return a valid public URL.
- [ ] The WhatsApp client (`whatsapp_client.py`) can successfully send a test message to your phone number via the Twilio API.

---

### Phase 3: End-to-End Workflow & Business Logic

**Goal**: Connect all the independent components together to create the complete, functioning application workflow.

**Tasks**:

- Implement the main orchestrator logic in `services/image_processor.py`. This function will be the "brain" of the application.
- The `image_processor` will:
  1.  Be called by the webhook with an incoming image URL.
  2.  Use the `fal_client` to get the stylized image data.
  3.  Use the `cloud_storage` service to upload that new image and get a permanent URL.
  4.  Return the final, permanent URL.
- Update the webhook handler in `api/webhooks.py` to call the `image_processor` service.
- Use the `whatsapp_client` within the webhook handler to send the final image URL back to the user.
- Implement comprehensive error handling for the entire workflow (e.g., what happens if the AI API fails?).

**Completion Criteria**:

- [ ] Sending an image to the WhatsApp number successfully triggers the full workflow.
- [ ] The stylized image is correctly uploaded to cloud storage.
- [ ] The user receives a WhatsApp message back containing the new image.
- [ ] The application handles and logs errors from external services gracefully.

---

### Phase 4: Production Readiness

**Goal**: Ensure the application is tested, secure, documented, and ready for deployment.

**Tasks**:

- Write unit and integration tests in the `tests/` directory, mocking external API calls to ensure logic is correct and reliable.
- Implement security best practices (e.g., validating Twilio's request signature in your webhook).
- Add rate limiting to the API endpoints to prevent abuse.
- Create the `Dockerfile` and `docker-compose.yml` to containerize the application.
- Finalize the API documentation that FastAPI auto-generates at `/docs` by adding clear descriptions and examples to your endpoint functions and Pydantic models.

**Completion Criteria**:

- [ ] Unit tests provide adequate coverage of the core logic.
- [ ] The application can be successfully built and run using Docker.
- [ ] Security checks (like signature validation) are implemented and working.
- [ ] The automatically generated API documentation at `/docs` is clear and complete.
