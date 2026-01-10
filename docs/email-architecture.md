# Email System Architecture Documentation

This document describes the technical architecture, data flow, and design decisions for the CraftFlow Commerce email system.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Core Components](#core-components)
4. [Data Models](#data-models)
5. [Email Template System](#email-template-system)
6. [Data Flows](#data-flows)
7. [Security Considerations](#security-considerations)
8. [Performance & Scalability](#performance--scalability)

---

## System Overview

The email system is designed to handle both transactional and marketing emails for CraftFlow Commerce users. It integrates with SendGrid for reliable email delivery and provides real-time tracking through webhooks.

### Key Features

- **Multi-tenant**: Complete isolation between users
- **Template-based**: Block editor for customizable email designs
- **Real-time tracking**: Webhook-based status updates
- **Scheduled campaigns**: Background scheduler for marketing emails
- **Analytics**: Comprehensive metrics (delivery, open, click rates)
- **Pro plan gating**: Email management requires Pro subscription

### Technology Stack

- **Backend**: FastAPI (Python), SQLAlchemy ORM, PostgreSQL
- **Email Provider**: SendGrid API
- **Template Engine**: Jinja2 with custom block rendering
- **Background Tasks**: AsyncIO with 60-second polling
- **Frontend**: React, Axios, React Router
- **Authentication**: JWT Bearer tokens

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Admin Frontend                          │
│  (React - /frontend/src/pages/CraftFlow/Emails/)              │
│                                                                 │
│  Components:                                                    │
│  • EmailTemplates.js       - Template list & management        │
│  • EmailTemplateEditor.js  - Block-based template editor       │
│  • EmailLogs.js            - Email delivery logs               │
│  • EmailAnalytics.js       - Metrics dashboard                 │
│  • EmailSubscribers.js     - Subscriber management             │
│  • EmailCampaigns.js       - Campaign scheduler                │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP/REST API (JWT Auth)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  (Python - /server/src/)                                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Routes (/api/ecommerce/admin/emails/)               │  │
│  │  - templates: CRUD operations                            │  │
│  │  - logs: Query email logs with filtering                 │  │
│  │  - analytics: Aggregate metrics                          │  │
│  │  - subscribers: Subscriber management                    │  │
│  │  - scheduled: Campaign management                        │  │
│  │  - webhooks: SendGrid event receiver                     │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │  EmailService (Business Logic)                          │  │
│  │  - send_transactional_email()                          │  │
│  │  - send_marketing_email()                              │  │
│  │  - render_email_template()                             │  │
│  │  - create_default_templates()                          │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │  Background Scheduler (AsyncIO)                         │  │
│  │  - Polls every 60 seconds                              │  │
│  │  - Executes pending campaigns                          │  │
│  │  - Updates campaign status                             │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────┬────────────────────────┬──────────────────────────────┘
          │                        │
          │ SendGrid API           │ PostgreSQL
          ▼                        ▼
┌──────────────────────┐  ┌──────────────────────────────────┐
│    SendGrid          │  │  Database Tables                 │
│                      │  │  • email_templates               │
│  • Send emails       │  │  • email_logs                    │
│  • Track events      │  │  • email_subscribers             │
│  • Webhooks          │  │  • scheduled_emails              │
│  • Analytics         │  │  • users (multi-tenant)          │
└──────────┬───────────┘  └──────────────────────────────────┘
           │
           │ Webhook Events
           │ (delivered, opened, clicked, etc.)
           │
           └─────────────────────────────────────────────────┐
                                                             │
                         ┌───────────────────────────────────▼┐
                         │  Webhook Handler                   │
                         │  - Validates signature             │
                         │  - Updates email_logs status       │
                         │  - Updates subscriber metrics      │
                         └────────────────────────────────────┘
```

---

## Core Components

### 1. Admin Frontend Pages

**Location**: `/frontend/src/pages/CraftFlow/Emails/`

**Pattern**: React functional components with hooks

- `useAuth()` for JWT token
- `useNotifications()` for toast messages
- `axios` for API requests
- `react-router` for navigation

**Key Pages**:

- **EmailTemplates.js**: List all templates, filter by type/status, delete
- **EmailTemplateEditor.js**: Create/edit templates with block editor, preview
- **EmailLogs.js**: View email delivery logs with pagination
- **EmailAnalytics.js**: Dashboard with metrics (open rate, click rate)
- **EmailSubscribers.js**: Manage subscribers, add/edit/delete, CSV export
- **EmailCampaigns.js**: Schedule and manage marketing campaigns

### 2. API Routes

**Location**: `/server/src/routes/ecommerce/admin_emails/`

**Authentication**: Requires Pro plan (`@require_pro_plan` decorator)

**Endpoints**:

```
GET    /api/ecommerce/admin/emails/templates              - List templates
POST   /api/ecommerce/admin/emails/templates              - Create template
GET    /api/ecommerce/admin/emails/templates/{id}         - Get template
PUT    /api/ecommerce/admin/emails/templates/{id}         - Update template
DELETE /api/ecommerce/admin/emails/templates/{id}         - Delete template
POST   /api/ecommerce/admin/emails/templates/{id}/preview - Preview template

GET    /api/ecommerce/admin/emails/logs                   - List email logs
GET    /api/ecommerce/admin/emails/analytics/summary      - Get analytics

GET    /api/ecommerce/admin/emails/subscribers            - List subscribers
POST   /api/ecommerce/admin/emails/subscribers            - Add subscriber
PUT    /api/ecommerce/admin/emails/subscribers/{id}       - Update subscriber
DELETE /api/ecommerce/admin/emails/subscribers/{id}       - Delete subscriber

GET    /api/ecommerce/admin/emails/scheduled              - List campaigns
POST   /api/ecommerce/admin/emails/send-marketing         - Create campaign
DELETE /api/ecommerce/admin/emails/scheduled/{id}         - Cancel campaign

POST   /api/ecommerce/webhooks/sendgrid                   - Webhook receiver
```

### 3. EmailService

**Location**: `/server/src/services/email_service.py`

**Responsibilities**:

- Render email templates with Jinja2
- Send emails via SendGrid API
- Log all email sends to database
- Create default templates on initialization

**Key Methods**:

```python
class EmailService:
    def send_transactional_email(
        user_id: int,
        email_type: str,
        recipient_email: str,
        context: dict
    ) -> EmailLog

    def send_marketing_email(
        user_id: int,
        template_id: int,
        recipient_emails: List[str],
        scheduled_email_id: Optional[int] = None
    ) -> List[EmailLog]

    def render_email_template(
        template: EmailTemplate,
        context: dict
    ) -> Tuple[str, str]  # (html, text)

def create_default_templates(
    db: Session,
    user_id: int,
    settings: StorefrontSettings
) -> None
```

### 4. Background Campaign Scheduler

**Location**: `/server/src/services/email_campaign_scheduler.py`

**Design**: AsyncIO-based polling loop (not separate worker process)

**Flow**:

1. `start_email_campaign_scheduler()` runs in FastAPI lifespan
2. Polls database every 60 seconds
3. Finds campaigns with `status='pending'` and `scheduled_for <= now`
4. Executes each campaign:
   - Updates status to "processing"
   - Resolves recipients (filter or manual list)
   - Sends emails via EmailService
   - Updates sent/failed counts
   - Sets status to "completed" or "failed"

**Integration**: Started in `main.py` lifespan event:

```python
asyncio.create_task(start_email_campaign_scheduler())
```

### 5. Webhook Handler

**Location**: `/server/src/routes/ecommerce/webhooks.py`

**Purpose**: Receives SendGrid event notifications in real-time

**Events Tracked**:

- `delivered`: Email reached inbox
- `open`: Email was opened
- `click`: Link in email was clicked
- `bounce`: Email bounced
- `dropped`: SendGrid rejected email
- `spam_report`: Marked as spam
- `unsubscribe`: User unsubscribed

**Processing**:

1. Validate webhook signature (optional)
2. Extract email and event type from payload
3. Find EmailLog by recipient email and user
4. Update status and metrics
5. Update EmailSubscriber metrics (total_sent, total_opened)
6. Return 200 OK to acknowledge receipt

---

## Data Models

### EmailTemplate

**Location**: `/server/src/entities/ecommerce/email_template.py`

```python
class EmailTemplate(Base):
    id: int
    user_id: int                    # Multi-tenant isolation
    name: str                       # Display name
    email_type: str                 # order_confirmation, shipping_notification, marketing
    template_type: str              # transactional, marketing
    subject: str                    # Supports {{variables}}
    blocks: List[dict]              # JSON array of block objects
    branding: dict                  # Colors, logo URL
    is_active: bool                 # Enable/disable template
    is_default: bool                # Prevent deletion
    created_at: datetime
    updated_at: datetime
```

**Block Structure**:

```json
[
  {
    "type": "logo",
    "src": "{{logo_url}}",
    "align": "center"
  },
  {
    "type": "header",
    "text": "Order Confirmation",
    "color": "#333333"
  },
  {
    "type": "text",
    "content": "Hi {{customer_name}}, thanks for your order!"
  },
  {
    "type": "button",
    "text": "View Order",
    "url": "{{order_url}}",
    "bg_color": "#4F46E5"
  }
]
```

### EmailLog

**Location**: `/server/src/entities/ecommerce/email_log.py`

```python
class EmailLog(Base):
    id: int
    user_id: int                    # Owner of the email
    email_type: str                 # Type of email sent
    template_id: int                # Template used (nullable)
    recipient_email: str            # Recipient
    subject: str                    # Email subject
    sendgrid_message_id: str        # For webhook matching
    sendgrid_status: str            # sent, delivered, opened, clicked, bounced, failed
    error_message: str              # Error details if failed
    sent_at: datetime               # When email was sent
    delivered_at: datetime          # When delivered (from webhook)
    opened_at: datetime             # When opened (from webhook)
    clicked_at: datetime            # When clicked (from webhook)
```

### EmailSubscriber

**Location**: `/server/src/entities/ecommerce/email_subscriber.py`

```python
class EmailSubscriber(Base):
    id: int
    user_id: int                    # Store owner
    email: str                      # Subscriber email
    customer_id: str                # Link to Customer (nullable)
    is_subscribed: bool             # Subscription status
    tags: List[str]                 # Segmentation tags
    total_sent: int                 # Total emails sent
    total_opened: int               # Total emails opened
    total_clicked: int              # Total links clicked
    last_sent_at: datetime          # Last email sent
    subscribed_at: datetime
    unsubscribed_at: datetime
```

### ScheduledEmail

**Location**: `/server/src/entities/ecommerce/scheduled_email.py`

```python
class ScheduledEmail(Base):
    id: int
    user_id: int                    # Campaign owner
    template_id: int                # Marketing template
    scheduled_for: datetime         # When to send
    status: str                     # pending, processing, completed, failed, cancelled
    recipient_emails: List[str]     # Manual recipient list (nullable)
    recipient_filter: dict          # Filter criteria (e.g., tags)
    sent_count: int                 # Successfully sent
    failed_count: int               # Failed sends
    error_message: str              # Error details if failed
    created_at: datetime
    started_at: datetime            # When execution started
    completed_at: datetime          # When execution finished
```

---

## Email Template System

### Block Types

The template system uses a block-based architecture with 8 block types:

1. **Logo**: Display branding logo
   - `src`: Image URL (supports variables)
   - `align`: left | center | right

2. **Header**: Section heading
   - `text`: Header text (supports variables)
   - `color`: Hex color

3. **Text**: Paragraph content
   - `content`: Text content (supports variables, HTML allowed)

4. **Button**: Call-to-action button
   - `text`: Button label
   - `url`: Button link
   - `bg_color`: Background color

5. **Order Summary**: Display order details
   - `show_items`: Boolean - show line items
   - `show_totals`: Boolean - show subtotal, tax, shipping, total

6. **Tracking Info**: Shipping tracking section
   - `tracking_number`: Variable placeholder
   - `carrier`: Variable placeholder

7. **Shipping Address**: Customer shipping address
   - No configuration (uses {{shipping_address}} object)

8. **Footer**: Email footer
   - `content`: Footer text (HTML allowed)

### Variable Substitution

Templates support Jinja2 variable syntax:

**Common Variables**:

- `{{customer_name}}`: Customer's name
- `{{customer_email}}`: Customer's email
- `{{order_id}}`: Order identifier
- `{{order_url}}`: Link to order details
- `{{order_number}}`: Human-friendly order number
- `{{tracking_number}}`: Shipping tracking number
- `{{tracking_url}}`: Tracking link
- `{{logo_url}}`: Store logo
- `{{store_name}}`: Store name
- `{{store_url}}`: Store homepage URL

**Context Objects**:

```python
context = {
    "customer_name": "John Doe",
    "order": {
        "id": 123,
        "number": "CF-1001",
        "items": [...],
        "subtotal": 29.99,
        "tax": 2.40,
        "shipping": 5.00,
        "total": 37.39
    },
    "shipping_address": {
        "line1": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94102",
        "country": "US"
    }
}
```

### Template Rendering Flow

```
1. Load EmailTemplate from database
   ↓
2. Extract blocks array and branding config
   ↓
3. For each block:
   - Render block HTML based on type
   - Substitute {{variables}} with context values
   ↓
4. Wrap blocks in base HTML template:
   - Add DOCTYPE, head, body tags
   - Apply branding colors
   - Add responsive CSS
   ↓
5. Generate plain text version (strip HTML)
   ↓
6. Return (html, text) tuple
```

---

## Data Flows

### 1. Transactional Email Flow

```
Order Placed (Checkout API)
  ↓
Call EmailService.send_transactional_email()
  user_id=current_user.id
  email_type="order_confirmation"
  recipient_email=customer.email
  context={order data}
  ↓
Find active template for email_type
  ↓
Render template with context
  ↓
Send via SendGrid API
  ↓
Create EmailLog record (status="sent")
  ↓
Return success
  ↓
SendGrid delivers email
  ↓
SendGrid sends webhook event (delivered)
  ↓
Webhook handler updates EmailLog (status="delivered")
  ↓
Customer opens email
  ↓
SendGrid sends webhook event (opened)
  ↓
Webhook handler updates EmailLog (status="opened", opened_at=now)
```

### 2. Marketing Campaign Flow

```
Admin creates campaign (EmailCampaigns.js)
  • Select template
  • Choose recipients (all/tags/manual)
  • Schedule time
  ↓
POST /api/ecommerce/admin/emails/send-marketing
  ↓
Create ScheduledEmail record (status="pending")
  ↓
Return success to admin
  ↓
[Wait for scheduled_for time]
  ↓
Background scheduler polls database (every 60s)
  ↓
Find ScheduledEmail with status="pending" and scheduled_for <= now
  ↓
Update status to "processing"
  ↓
Resolve recipients:
  - If recipient_filter: Query EmailSubscribers with matching tags
  - If recipient_emails: Use manual list
  ↓
For each recipient:
  - Call EmailService.send_marketing_email()
  - Create EmailLog
  - Send via SendGrid
  ↓
Update ScheduledEmail:
  - sent_count = successful sends
  - failed_count = failed sends
  - status = "completed"
  ↓
Admin views campaign in list (status updated to "completed")
```

### 3. Webhook Event Processing Flow

```
Customer action (opens email, clicks link)
  ↓
SendGrid detects event
  ↓
SendGrid sends POST to /api/ecommerce/webhooks/sendgrid
  Headers:
    X-Twilio-Email-Event-Webhook-Signature (optional)
    X-Twilio-Email-Event-Webhook-Timestamp
  Body: [{event, email, sg_message_id, timestamp, ...}]
  ↓
Webhook handler validates signature (if enabled)
  ↓
For each event in batch:
  - Parse event type (delivered, open, click, etc.)
  - Extract recipient email and sg_message_id
  - Find EmailLog by sg_message_id or recipient_email
  - Update EmailLog status and timestamp fields
  - If subscriber exists: Update metrics (total_opened++, etc.)
  ↓
Return 200 OK to SendGrid
  ↓
Admin views updated stats in Analytics/Logs pages
```

---

## Security Considerations

### 1. Multi-Tenant Isolation

All database queries filter by `user_id` to prevent cross-user data access:

```python
templates = db.query(EmailTemplate).filter(
    EmailTemplate.user_id == current_user.id
).all()
```

### 2. Pro Plan Requirement

Email management requires Pro subscription:

```python
@router.get("/templates")
@require_pro_plan
async def list_templates(...):
    ...
```

### 3. Webhook Signature Verification

Optional but recommended for production:

```python
def verify_webhook_signature(body, signature, timestamp):
    if not SENDGRID_WEBHOOK_SECRET:
        return True  # Skip verification if not configured

    expected = generate_signature(body, timestamp, SENDGRID_WEBHOOK_SECRET)
    return hmac.compare_digest(signature, expected)
```

### 4. Template Variable Sanitization

Jinja2 auto-escapes HTML to prevent XSS:

```python
from jinja2 import Environment, select_autoescape

env = Environment(autoescape=select_autoescape(['html', 'xml']))
```

### 5. Rate Limiting

SendGrid enforces rate limits based on plan. Consider implementing:

- Per-user daily send limits
- Campaign recipient count limits
- API endpoint rate limiting

### 6. Data Privacy

- Emails stored in logs for analytics
- Consider GDPR compliance: Allow users to request log deletion
- Unsubscribe links required for marketing emails
- Honor unsubscribe requests immediately

---

## Performance & Scalability

### 1. Database Indexing

Critical indexes for performance:

```sql
-- Email logs
CREATE INDEX idx_email_logs_user_id ON email_logs(user_id);
CREATE INDEX idx_email_logs_sg_message_id ON email_logs(sendgrid_message_id);
CREATE INDEX idx_email_logs_recipient_email ON email_logs(recipient_email);

-- Scheduled emails
CREATE INDEX idx_scheduled_emails_status_time ON scheduled_emails(status, scheduled_for);

-- Subscribers
CREATE INDEX idx_email_subscribers_user_id ON email_subscribers(user_id);
CREATE INDEX idx_email_subscribers_email ON email_subscribers(email);
```

### 2. Scheduler Polling Frequency

Current: 60 seconds

**Trade-offs**:

- Lower frequency (2-5 min): Less DB load, less precise timing
- Higher frequency (10-30 sec): More precise, higher DB load

**Optimization**: Use database-level job queue (pg_cron) or dedicated task queue (Celery, RQ)

### 3. Webhook Batch Processing

SendGrid sends events in batches. Handler processes all in single transaction:

```python
for event in events:
    process_event(event)
db.commit()  # Single commit for all updates
```

### 4. Email Rendering Cache

For high-volume transactional emails, consider caching rendered templates:

```python
@lru_cache(maxsize=100)
def get_rendered_template(template_id: int, context_hash: str):
    ...
```

### 5. Horizontal Scaling

The system is stateless and can scale horizontally:

- Multiple FastAPI instances behind load balancer
- Scheduler uses database row-level locking to prevent duplicate execution
- Webhooks are idempotent (can process same event multiple times safely)

### 6. Monitoring

Key metrics to monitor:

- Email send volume (per user, per day)
- SendGrid API latency
- Webhook processing time
- Scheduler execution time
- Database query performance
- Email bounce/failure rates

---

## Future Enhancements

1. **A/B Testing**: Split test subject lines and content
2. **Automation Rules**: Trigger emails based on customer behavior
3. **Dynamic Segments**: Auto-update subscriber segments based on activity
4. **Email Previews**: Render templates in multiple email clients
5. **Attachment Support**: Allow file attachments in emails
6. **Internationalization**: Multi-language template support
7. **Advanced Analytics**: Funnel tracking, cohort analysis
8. **Template Library**: Pre-built templates for common use cases

---

**Last Updated**: 2026-01-10
