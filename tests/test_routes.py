"""Tests for API routes and webhook handlers."""

import pytest
from fastapi.testclient import TestClient

from src.whatsapp_image_bot.app import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestHealthAndRootEndpoints:
    """Tests for basic app endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to the Image Styler API!"}

    def test_health_endpoint(self, client):
        """Test health endpoint returns OK status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestWebhookHelpers:
    """Tests for webhook helper functions."""

    def test_is_allowed_media_url_valid(self):
        """Test _is_allowed_media_url with valid URLs."""
        from src.whatsapp_image_bot.api.webhooks import _is_allowed_media_url

        valid_urls = [
            "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test",
            "https://example.twilio.com/media/file.jpg",
            "https://s3.amazonaws.com/bucket/image.jpg",
            "http://api.twilio.com/media.jpg",  # HTTP also allowed
        ]

        for url in valid_urls:
            assert _is_allowed_media_url(url), f"URL should be allowed: {url}"

    def test_is_allowed_media_url_invalid(self):
        """Test _is_allowed_media_url with invalid URLs."""
        from src.whatsapp_image_bot.api.webhooks import _is_allowed_media_url

        invalid_urls = [
            "https://malicious.com/image.jpg",
            "ftp://api.twilio.com/file.jpg",  # Wrong scheme
            "https://api.twilio.co.uk/file.jpg",  # Wrong domain
            "not-a-url",
            "",
        ]

        for url in invalid_urls:
            assert not _is_allowed_media_url(url), f"URL should be rejected: {url}"


class TestTwilioWebhookRequest:
    """Tests for TwilioWebhookRequest model."""

    def test_valid_webhook_request(self):
        """Test TwilioWebhookRequest with valid data."""
        from src.whatsapp_image_bot.api.webhooks import TwilioWebhookRequest

        data = {
            "From": "whatsapp:+1234567890",
            "MessageSid": "SM12345678901234567890123456789012",
            "NumMedia": 1,
            "MediaUrl0": "https://api.twilio.com/media/test.jpg",
        }

        request = TwilioWebhookRequest(**data)
        assert request.sender_number == "whatsapp:+1234567890"
        assert request.message_sid == "SM12345678901234567890123456789012"
        assert request.num_media == 1
        assert request.media_url == "https://api.twilio.com/media/test.jpg"

    def test_webhook_request_no_media(self):
        """Test TwilioWebhookRequest with no media."""
        from src.whatsapp_image_bot.api.webhooks import TwilioWebhookRequest

        data = {
            "From": "whatsapp:+1234567890",
            "MessageSid": "SM12345678901234567890123456789012",
            "NumMedia": 0,
        }

        request = TwilioWebhookRequest(**data)
        assert request.sender_number == "whatsapp:+1234567890"
        assert request.message_sid == "SM12345678901234567890123456789012"
        assert request.num_media == 0
        assert request.media_url is None

    def test_to_signature_dict(self):
        """Test to_signature_dict method."""
        from src.whatsapp_image_bot.api.webhooks import TwilioWebhookRequest

        data = {
            "From": "whatsapp:+1234567890",
            "MessageSid": "SM12345678901234567890123456789012",
            "NumMedia": 1,
            "MediaUrl0": "https://api.twilio.com/media/test.jpg",
        }

        request = TwilioWebhookRequest(**data)
        sig_dict = request.to_signature_dict()

        expected = {
            "From": "whatsapp:+1234567890",
            "MessageSid": "SM12345678901234567890123456789012",
            "NumMedia": "1",  # Should be string for signature
            "MediaUrl0": "https://api.twilio.com/media/test.jpg",
        }

        assert sig_dict == expected
