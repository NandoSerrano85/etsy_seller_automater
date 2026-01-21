# Email System Setup Guide

This guide walks you through setting up the complete email system for CraftFlow Commerce, including SendGrid configuration, environment variables, and webhook setup.

## Table of Contents

1. [Overview](#overview)
2. [SendGrid Account Setup](#sendgrid-account-setup)
3. [Environment Variables](#environment-variables)
4. [Webhook Configuration](#webhook-configuration)
5. [Testing the System](#testing-the-system)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The CraftFlow email system provides:

- **Transactional Emails**: Order confirmations, shipping notifications
- **Marketing Campaigns**: Scheduled email campaigns to subscriber lists
- **Email Analytics**: Open rates, click rates, delivery tracking
- **Template Management**: Block-based email template editor
- **Subscriber Management**: Segmentation with tags, CSV import/export
- **Webhook Integration**: Real-time status updates from SendGrid

All emails are sent via SendGrid's reliable API, with webhook events tracked in the database for analytics.

---

## SendGrid Account Setup

### 1. Create SendGrid Account

1. Go to [SendGrid.com](https://sendgrid.com/)
2. Sign up for a free account (includes 100 emails/day)
3. For production, upgrade to a paid plan based on your volume needs

### 2. Verify Sender Identity

SendGrid requires sender verification before sending emails:

#### Option A: Single Sender Verification (Quick Setup)

1. Navigate to **Settings → Sender Authentication**
2. Click **Verify a Single Sender**
3. Fill in your email information:
   - **From Name**: Your store name (e.g., "CraftFlow Store")
   - **From Email Address**: noreply@yourdomain.com
   - **Reply To**: support@yourdomain.com (optional)
4. Check your email and click the verification link

#### Option B: Domain Authentication (Recommended for Production)

1. Navigate to **Settings → Sender Authentication**
2. Click **Authenticate Your Domain**
3. Select your DNS host provider
4. Add the provided DNS records (CNAME) to your domain
5. Wait for DNS propagation (can take up to 48 hours)
6. Return to SendGrid and click **Verify**

**Benefits of Domain Authentication**:

- Higher deliverability rates
- Removes "via sendgrid.net" from email headers
- Better brand reputation

### 3. Create API Key

1. Navigate to **Settings → API Keys**
2. Click **Create API Key**
3. Name: "CraftFlow Production API Key"
4. Permissions: Select **Full Access** (or Restricted Access with Mail Send enabled)
5. Copy the API key immediately - it won't be shown again
6. Save it securely (you'll need it for environment variables)

**Security Note**: Never commit API keys to version control. Use environment variables or secrets management.

---

## Environment Variables

Add these variables to your environment configuration:

### Backend (.env or Railway Variables)

```bash
# SendGrid Configuration
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME="Your Store Name"

# Enable Email Service
ENABLE_EMAIL_SERVICE=true

# Webhook Security (optional but recommended)
SENDGRID_WEBHOOK_SECRET=your_random_secret_string_here
```

### Variable Descriptions

| Variable                  | Required | Description                                             |
| ------------------------- | -------- | ------------------------------------------------------- |
| `SENDGRID_API_KEY`        | Yes      | Your SendGrid API key (starts with "SG.")               |
| `SENDGRID_FROM_EMAIL`     | Yes      | Verified sender email address                           |
| `SENDGRID_FROM_NAME`      | Yes      | Display name for sent emails                            |
| `ENABLE_EMAIL_SERVICE`    | No       | Set to "true" to enable email sending (default: true)   |
| `SENDGRID_WEBHOOK_SECRET` | No       | Secret for webhook signature verification (recommended) |

### Setting Environment Variables

#### Local Development

Create a `.env` file in your project root:

```bash
cp .env.example .env
# Edit .env and add your SendGrid credentials
```

#### Railway Deployment

1. Go to your Railway project
2. Navigate to **Variables** tab
3. Add each variable:
   - Click **New Variable**
   - Enter variable name and value
   - Click **Add**
4. Deploy your application to apply changes

---

## Webhook Configuration

Webhooks allow SendGrid to notify your application of email events in real-time (delivered, opened, clicked, bounced, etc.).

### 1. Get Your Webhook URL

Your webhook URL follows this pattern:

```
https://yourdomain.com/api/ecommerce/webhooks/sendgrid
```

For Railway deployments:

```
https://your-app-name.up.railway.app/api/ecommerce/webhooks/sendgrid
```

### 2. Configure Webhook in SendGrid

1. Navigate to **Settings → Mail Settings → Event Webhook**
2. Enable the Event Webhook
3. Set **HTTP Post URL**: `https://yourdomain.com/api/ecommerce/webhooks/sendgrid`
4. Set **Authorization Method**: None (we use custom verification)
5. Select events to track:
   - ☑ Delivered
   - ☑ Opened
   - ☑ Clicked
   - ☑ Bounced
   - ☑ Dropped
   - ☑ Spam Report
   - ☑ Unsubscribe
6. Click **Save**

### 3. Test Webhook Connection

Send a test event from SendGrid:

1. In the Event Webhook settings, click **Test Your Integration**
2. SendGrid will send a test POST request to your webhook URL
3. Check your server logs for "Received SendGrid webhook event"
4. Verify the response status is `200 OK`

### 4. Enable Webhook Signature Verification (Optional but Recommended)

For added security, verify webhook requests come from SendGrid:

1. In SendGrid Event Webhook settings, enable **Event Webhook Signature**
2. Copy the **Verification Key**
3. Add to your environment variables:
   ```bash
   SENDGRID_WEBHOOK_SECRET=your_verification_key_here
   ```
4. Restart your application

The webhook handler will now verify the `X-Twilio-Email-Event-Webhook-Signature` header.

---

## Testing the System

### 1. Initialize Default Templates

Default email templates are created automatically when you first save your storefront settings:

1. Navigate to **CraftFlow → Storefront Settings**
2. Configure your branding (logo, colors)
3. Click **Save**
4. Check the backend logs for: "✅ Default email templates created"
5. Navigate to **CraftFlow → Email Management → Templates** to verify

### 2. Test Transactional Emails

#### Test Order Confirmation Email

1. Create a test order in your storefront
2. Complete the checkout process
3. Check the **Email Logs** page for the sent email
4. Verify the email was received in the customer's inbox
5. Check the **Analytics** page for delivery metrics

#### Test Email Sending Directly

```python
# Use the admin API to send a test email
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}
data = {
    "template_id": 1,  # Order confirmation template
    "recipient_emails": ["test@example.com"],
    "scheduled_for": None  # Send immediately
}

response = requests.post(
    "http://localhost:3003/api/ecommerce/admin/emails/send-marketing",
    headers=headers,
    json=data
)

print(response.json())
```

### 3. Test Marketing Campaigns

1. Navigate to **Email Management → Subscribers**
2. Add a test subscriber with your email
3. Go to **Email Management → Campaigns**
4. Click **Create Campaign**
5. Select a marketing template
6. Choose "Manual Email List" and enter your email
7. Select "Send Now"
8. Check your inbox for the email
9. Click links in the email to test click tracking

### 4. Verify Webhook Events

1. Send a test email using the steps above
2. Open the email in your inbox
3. Click a link in the email
4. Navigate to **Email Logs** in the admin panel
5. Verify the status changed from "sent" → "delivered" → "opened" → "clicked"
6. Check backend logs for webhook event processing

### 5. Test Scheduled Campaigns

1. Create a campaign scheduled for 2 minutes in the future
2. Wait for the scheduler to execute (polls every 60 seconds)
3. Check backend logs for: "Executing scheduled campaign..."
4. Verify the email was sent and the campaign status is "completed"

---

## Troubleshooting

### Emails Not Sending

**Problem**: No emails appearing in logs or inbox

**Solutions**:

1. Verify `ENABLE_EMAIL_SERVICE=true` in environment variables
2. Check SendGrid API key is valid: Test in SendGrid dashboard → API Keys
3. Verify sender email is authenticated in SendGrid
4. Check backend logs for errors: `grep "email" server.log`
5. Ensure SendGrid account is not suspended (check SendGrid dashboard)

### Webhook Events Not Updating

**Problem**: Email status stuck on "sent", not updating to "delivered"

**Solutions**:

1. Verify webhook URL is accessible publicly (not localhost)
2. Test webhook URL returns 200: `curl -X POST https://yourdomain.com/api/ecommerce/webhooks/sendgrid`
3. Check SendGrid Event Webhook settings are enabled
4. Verify webhook URL in SendGrid matches your deployment
5. Check server logs for webhook errors: `grep "webhook" server.log`
6. Disable signature verification temporarily to test

### Scheduled Campaigns Not Executing

**Problem**: Campaigns stuck in "pending" status

**Solutions**:

1. Check backend logs for: "✅ Email campaign scheduler started"
2. Verify scheduler is running: Look for logs every 60 seconds
3. Ensure campaign `scheduled_for` time has passed
4. Check database: `SELECT * FROM scheduled_emails WHERE status='pending'`
5. Manually trigger scheduler in Python console:
   ```python
   from server.src.services.email_campaign_scheduler import process_scheduled_campaigns
   process_scheduled_campaigns()
   ```

### Template Variables Not Rendering

**Problem**: Email shows `{{variable_name}}` instead of values

**Solutions**:

1. Verify template uses correct variable names (e.g., `{{customer_name}}`)
2. Check context data passed to `render_email_template()` includes the variable
3. Use the preview endpoint to test rendering:
   ```bash
   curl -X POST http://localhost:3003/api/ecommerce/admin/emails/templates/1/preview \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"context": {"customer_name": "Test User"}}'
   ```

### High Bounce Rate

**Problem**: Many emails bouncing

**Solutions**:

1. Verify email addresses are valid before sending
2. Implement double opt-in for subscribers
3. Use domain authentication (not single sender verification)
4. Check SendGrid Sender Reputation score
5. Review bounce reasons in SendGrid dashboard
6. Remove hard-bounced emails from subscriber list

### Webhook Signature Verification Failing

**Problem**: Webhooks returning 401 Unauthorized

**Solutions**:

1. Verify `SENDGRID_WEBHOOK_SECRET` matches SendGrid's Verification Key
2. Check signature is being sent: Look for `X-Twilio-Email-Event-Webhook-Signature` header
3. Temporarily disable verification for testing:
   - Comment out signature verification in `webhooks.py`
   - Test webhook
   - Re-enable verification
4. Ensure timestamp is within 10 minutes (SendGrid requirement)

---

## Additional Resources

- [SendGrid Documentation](https://docs.sendgrid.com/)
- [SendGrid Event Webhook Reference](https://docs.sendgrid.com/for-developers/tracking-events/event)
- [Email Best Practices](https://sendgrid.com/blog/email-best-practices/)
- [Deliverability Guide](https://sendgrid.com/blog/deliverability-guide/)

---

## Next Steps

1. **Review [Email Architecture Documentation](./email-architecture.md)** to understand the system design
2. **Read [Admin User Guide](./email-admin-guide.md)** to learn how to use the email management UI
3. **Follow [Deployment Guide](./deployment-email-system.md)** for production deployment checklist

---

**Last Updated**: 2026-01-10
