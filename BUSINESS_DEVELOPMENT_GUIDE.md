# Background Removal Bot - Business Development Guide

## Overview

This guide outlines the development plan to transition the "AI Image Styler" project into a commercial **Background & Object Removal Service** on WhatsApp. The primary goal is to build a Minimum Viable Product (MVP) capable of acquiring its first paying customers, and then to scale it into a profitable, automated business.

This plan prioritizes features that directly support the business model: user management, payments, and a seamless user experience designed for online sellers.

## The Core User Interaction Flow

Before diving into phases, it's essential to define the target user experience. The entire application should be built to support this conversational flow:

1.  **First Contact**: A new user sends a message or image to the bot for the first time.

    - **Bot's Action**: The system creates a new user record in the database, associated with their WhatsApp number, and grants them a set of free credits (e.g., 3).
    - **Bot's Reply**: "Welcome! I can remove the background from your product photos. You have 3 free edits to start. Just send me an image!"

2.  **Image Submission**: The user sends an image.

    - **Bot's Action**: The system checks the user's credit balance.
    - **If credits > 0**: The bot proceeds to the next step.
    - **If credits <= 0**: The bot replies, "You're out of credits! To buy more and continue, just type **'buy'**." The process stops here until the user buys more credits.

3.  **Action Prompt**: After receiving an image from a user with credits, the bot needs to know what to do.

    - **Bot's Reply**:
      ✅ Image received!  
       What should I erase?  
       • Reply **background** to remove the entire background, or  
       • Describe the object you want removed (e.g., “the red car”).

    Please be specific so I can locate it in the image.
    Tip: JUST describe the object — no need to say “remove.”

4.  **User Command**: The user replies with text.

    - **Example 1**: "background"
    - **Example 2**: "the man in the blue shirt"

5.  **Processing & Delivery**:
    - **Bot's Action**: The system debits 1 credit from the user's account. It sends the image and the user's text command to the AI removal service.
    - **Bot's Interim Reply**: "Got it! Working on it now... ✨"
    - **Bot's Final Reply**: Once the processed image is ready, the bot sends it back to the user with a message like, "Here you go! You have x credits remaining."

## Development Phases

### Phase 1: Minimum Viable Product (MVP) - The First Sale

**Goal**: To build the absolute essential features required to process an image, manage a user's credits, and accept a payment. The aim is to validate the business idea with the first paying customer.

**Tasks**:

1.  **Pivot the AI Service**:

    - Replace the current "Simpsons style" AI client with a client for a **background and object removal API** (we could use the same endpoint, but we need to change the prompt).
    - The new client must be able to accept both an image and a text prompt.

2.  **Implement User Database**:

    - Set up a simple database (SQLite is perfect for the start).
    - Create a `User` table to store `whatsapp_number` and `credits_remaining`.

3.  **Integrate Core Credit Logic**:

    - In the main webhook handler, implement the logic from the user flow:
      - On first contact, create a user with free credits.
      - Before processing an image, check if the user has credits.
      - After successful processing, decrement the user's credit count.

4.  **Establish Manual Payment Process**:
    - Do **not** build a payment webhook yet.
    - Create a **Stripe Payment Link** (or equivalent) for the `$1.99` (4 credits) and `$4.99` (12 credits) credit packs.
    - For now, you will be notified of a sale by email. You will then **manually update the user's credits in the database**. This is temporary but is the fastest way to validate that people will pay.

**Completion Criteria**:

- [ ] The bot can successfully remove a background from a user's image.
- [ ] A new user is automatically created in the database with free credits.
- [ ] The system correctly checks and debits credits for each job.
- [ ] You can send a user a payment link and, upon their purchase, manually add credits to their account.

### Phase 2: The SaaS Engine - Automation & User Experience

**Goal**: To eliminate manual work and create a smooth, self-service experience for the user. This turns the MVP into a real, automated business.

**Tasks**:

1.  **Automate Payments**:

    - Build a new webhook endpoint (`/api/webhooks/stripe`) to listen for successful payment events from your payment provider.
    - This endpoint must securely validate the incoming request and automatically add the correct number of credits to the corresponding user's account in the database.

2.  **Develop Conversational Commands**:

    - Implement the text-based command handler within the main webhook.
    - The bot must be able to recognize and respond to commands like:
      - `balance`: "You have X credits remaining."
      - `buy`: "Here are our credit packs: [Payment Link 1], [Payment Link 2]"
      - `help`: Provides a summary of how the bot works.

3.  **Refine the Interactive Prompt**:
    - Implement the "What would you like to do?" prompt after an image is received.
    - Ensure the system can correctly parse the user's text reply and pass it to the AI service.

**Completion Criteria**:

- [ ] A user can purchase a credit pack and have their account updated automatically, with zero manual intervention.
- [ ] The bot responds correctly to non-image text commands (`balance`, `buy`).
- [ ] The full user interaction flow, from image submission to action prompt to delivery, is smooth and reliable.

### Phase 3: Growth & Scaling

**Goal**: To add features that encourage organic growth, improve retention, and prepare the business for a larger, international audience.

**Tasks**:

1.  **Build the Referral Engine**:

    - Create a system that generates a unique referral link for each user.
    - Implement the logic for the referral offer (e.g., "Share this link with a friend. When they buy their first pack, you both get 5 free edits!").
    - The system must automatically track successful referrals and award the bonus credits.

2.  **Internationalization (i18n)**:

    - Refactor the bot's reply strings into a language management system.
    - The bot should detect the user's language (or allow them to set it) and reply in either English, Spanish, or Portuguese.
    - This includes localizing the payment links to show local currencies (e.g., BRL for Brazil).

3.  **Basic Analytics**:
    - Implement logging or database tracking for key business metrics:
      - Daily new users.
      - Daily active users.
      - Number of images processed per day.
      - Daily sales (number of packs sold).
      - Conversion rate from free user to paid user.

**Completion Criteria**:

- [ ] Users can successfully refer friends and receive bonus credits automatically.
- [ ] The bot can communicate with users in the primary languages of your target markets.
- [ ] You have a simple dashboard or report to monitor the health and growth of the business.
