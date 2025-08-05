# WhatsApp Background & Object Removal Bot

A commercial FastAPI-powered bot that removes backgrounds and objects from images sent via WhatsApp, designed for online sellers and content creators.

## Overview

This project is a commercial web service that connects to WhatsApp through Twilio. Users can send product photos or images to remove backgrounds or specific objects. The bot processes images using AI services and operates on a credit-based system with automated payments.

The application is built with modern Python tools, including the high-performance **FastAPI** framework and the **uv** package manager.

---

## ⚠️ Project Status

**This project is transitioning from a technical proof-of-concept to a commercial MVP.** The core image processing infrastructure is complete, and we're now implementing user management, credit systems, and payment processing for the first paying customers.

---

## Key Features

### Current (Technical Foundation)
- **WhatsApp Integration**: Receive and send images directly through WhatsApp using the Twilio API.
- **AI Background/Object Removal**: Connect to external APIs like `fal.ai` to remove backgrounds or specific objects from images.
- **Asynchronous Processing**: Built with FastAPI to handle multiple user requests efficiently without blocking.
- **Modular Architecture**: Code is separated into distinct services and clients for easy maintenance and scalability.
- **Cloud Storage**: Automatic upload and hosting of processed images via AWS S3.

### Planned (Business Features)
- **Credit-Based System**: Users receive 3 free credits, then purchase credit packs to continue using the service.
- **Automated Payments**: Stripe integration for seamless credit purchases.
- **User Database**: Track users, credits, and usage patterns.
- **Conversational Commands**: Support for `balance`, `buy`, and `help` commands.
- **Referral Program**: Users can refer friends for bonus credits.
- **Multi-language Support**: English, Spanish, and Portuguese localization.

---

## Project Structure

```text
whatsapp-image-bot/
├── README.md
├── DEVELOPMENT_GUIDE.md
├── pyproject.toml
├── .env.example
├── .dockerignore                    # Docker build context exclusions
├── docker/
│   ├── Dockerfile                   # Multi-stage, security-hardened
│   └── docker-compose.yml           # With secrets & resource limits
├── scripts/
│   └── deploy.sh                    # Intelligent health checking
├── tests/
│   ├── test_routes.py
│   ├── test_image_processor.py
│   ├── test_cloud_storage.py
│   ├── test_api_clients.py
│   └── test_docker_container.py     # Container security & config tests
└── src/
    └── whatsapp_image_bot/
        ├── app.py
        ├── config.py                # Docker secrets integration
        ├── api/
        │   ├── routes.py
        │   └── webhooks.py
        ├── services/
        │   ├── image_processor.py
        │   ├── cloud_storage.py
        │   └── whatsapp_client.py
        └── clients/
            ├── base.py
            └── fal_client.py
```

---

## Development Setup

To get this project running locally, follow these steps.

1.  **Prerequisites**

    **For Docker deployment:**
    - Docker and Docker Compose
    - `ngrok` for exposing the local server
    
    **For local development:**
    - Python 3.11+
    - [uv](https://astral.sh/docs/uv#installation) package manager
    - `ngrok` for exposing the local server

2.  **Clone the Repository**

    ```bash
    git clone <your-repository-url>
    cd whatsapp-image-bot
    ```

3.  **Create Environment & Install Dependencies**

    ```bash
    # Create the virtual environment
    uv venv

    # Activate the environment
    source .venv/bin/activate

    # Install dependencies from pyproject.toml
    uv sync
    ```

4.  **Configure Environment Variables**

    - Create a `.env` file by copying the example file.
      ```bash
      cp .env.example .env
      ```
    - Edit the `.env` file and add your secret keys:
      ```bash
      # Twilio Configuration
      TWILIO_ACCOUNT_SID=your_twilio_account_sid
      TWILIO_AUTH_TOKEN=your_twilio_auth_token
      TWILIO_PHONE_NUMBER=your_twilio_phone_number
      
      # fal.ai Configuration
      FAL_KEY=your_fal_api_key
      
      # AWS S3 Configuration
      AWS_ACCESS_KEY_ID=your_aws_access_key
      AWS_SECRET_ACCESS_KEY=your_aws_secret_key
      AWS_REGION=your_aws_region
      S3_BUCKET_NAME=your_s3_bucket_name
      ```

---

## Running the Application

### Option 1: Docker Deployment (Recommended)

1.  **Quick Start with Docker**
    
    Use the automated deployment script with intelligent health checking:
    ```bash
    ./scripts/deploy.sh
    ```
    
    Or manually with docker-compose:
    ```bash
    docker-compose -f docker/docker-compose.yml up -d
    ```

2.  **Security Features**
    - **Non-root container**: Runs as `appuser` for enhanced security
    - **Docker secrets**: Sensitive environment variables are managed as Docker secrets
    - **Resource limits**: Memory and CPU limits prevent resource exhaustion
    - **Multi-stage builds**: Optimized image size with minimal attack surface

3.  **Check Status**
    ```bash
    # View logs
    docker-compose -f docker/docker-compose.yml logs -f
    
    # Check container health
    docker-compose -f docker/docker-compose.yml ps
    
    # Stop services
    docker-compose -f docker/docker-compose.yml down
    ```

### Option 2: Local Development

1.  **Start the Server**
    With your virtual environment activated, run the Uvicorn server:

    ```bash
    uvicorn src.whatsapp_image_bot.app:app --reload
    ```

    The server will be available at `http://127.0.0.1:8000`.

2.  **Expose with `ngrok`**
    To connect with Twilio, you'll need to expose your local server to the internet:

    ```bash
    ngrok http 8000
    ```

    Use the public `https://...` URL provided by `ngrok` for your Twilio webhook configuration.

---

## Testing

The project includes comprehensive tests for both application logic and Docker container functionality.

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_docker_container.py  # Docker-specific tests
pytest tests/test_routes.py           # API endpoint tests
pytest tests/test_image_processor.py  # Image processing tests

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=src/whatsapp_image_bot
```

### Test Categories

- **Unit Tests**: Core application logic and services
- **Integration Tests**: API endpoints and external service integration
- **Docker Tests**: Container security, configuration, and deployment validation
- **Configuration Tests**: Environment variable and secrets management
