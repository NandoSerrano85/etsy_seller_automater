# Email Management Admin User Guide

This guide explains how to use the CraftFlow Commerce email management system for store owners and administrators.

## Table of Contents

1. [Overview](#overview)
2. [Accessing Email Management](#accessing-email-management)
3. [Managing Email Templates](#managing-email-templates)
4. [Viewing Email Logs](#viewing-email-logs)
5. [Understanding Analytics](#understanding-analytics)
6. [Managing Subscribers](#managing-subscribers)
7. [Creating Email Campaigns](#creating-email-campaigns)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The CraftFlow Commerce email system allows you to:

- **Customize Email Templates**: Design branded transactional and marketing emails
- **Track Email Performance**: View delivery, open, and click rates
- **Manage Subscribers**: Build and segment your email list
- **Send Campaigns**: Schedule marketing emails to your customers
- **Monitor Delivery**: Track every email sent from your store

### Email Types

**Transactional Emails** (automatic):

- Order confirmations
- Shipping notifications
- Password resets (future)

**Marketing Emails** (manual):

- Promotional campaigns
- Newsletters
- Product announcements

---

## Accessing Email Management

### Requirements

- **Pro Plan Subscription**: Email management is a Pro plan feature
- **Admin Access**: You must be a store owner or admin
- **Storefront Settings**: Complete your storefront settings before using email features

### Navigation

1. Login to your CraftFlow account
2. Navigate to **CraftFlow → Email Management**
3. You'll see the Email Templates page

**Email Management Sections**:

- **Templates**: Create and edit email designs
- **Analytics**: View email performance metrics
- **Email Logs**: Track individual email deliveries
- **Subscribers**: Manage your email list
- **Campaigns**: Schedule marketing emails

---

## Managing Email Templates

Templates define the design and content of your emails. CraftFlow uses a block-based editor for easy customization.

### Viewing Templates

1. Navigate to **Email Management → Templates**
2. View all templates in a card layout
3. Use filters to narrow results:
   - **Email Type**: Order Confirmation, Shipping Notification, Marketing
   - **Status**: Active, Inactive

**Template Card Information**:

- Template name
- Email subject line
- Email type and template type badges
- Active/Inactive status
- Default template indicator
- Block count
- Last updated date

### Creating a New Template

1. Click **Create Template** button
2. Fill in template metadata:
   - **Name**: Internal name (e.g., "Summer Sale Announcement")
   - **Email Type**: Choose from dropdown
     - Order Confirmation
     - Shipping Notification
     - Marketing
   - **Template Type**: Transactional or Marketing
   - **Subject**: Email subject line (supports variables like `{{customer_name}}`)
3. Configure branding:
   - **Primary Color**: Main brand color (e.g., #4F46E5)
   - **Secondary Color**: Accent color
   - **Logo URL**: Link to your logo image
4. Add email blocks (see [Building Email Content](#building-email-content))
5. Click **Save** or **Save & Activate**

### Editing an Existing Template

1. Find the template in the list
2. Click the **Edit** button
3. Make your changes
4. Click **Save** or **Save & Activate**

**Note**: Default templates (Order Confirmation, Shipping Notification) cannot be deleted but can be edited.

### Building Email Content

CraftFlow emails are built using blocks. Add blocks in order from top to bottom:

#### Available Block Types

**1. Logo Block**

- Displays your store logo
- **Settings**:
  - Image URL (use `{{logo_url}}` for storefront logo)
  - Alignment: Left, Center, or Right

**2. Header Block**

- Large heading text
- **Settings**:
  - Text content (supports variables)
  - Text color

**3. Text Block**

- Paragraph content
- **Settings**:
  - Text content (supports variables and HTML)

**4. Button Block**

- Call-to-action button
- **Settings**:
  - Button text
  - Link URL (supports variables)
  - Background color

**5. Order Summary Block**

- Displays order details (for transactional emails)
- **Settings**:
  - Show line items (checkbox)
  - Show totals (checkbox)

**6. Tracking Info Block**

- Shipping tracking details
- **Settings**:
  - Uses `{{tracking_number}}` and `{{tracking_url}}` variables
  - Automatically formatted

**7. Shipping Address Block**

- Customer shipping address
- **Settings**:
  - Uses `{{shipping_address}}` object
  - Automatically formatted

**8. Footer Block**

- Email footer content
- **Settings**:
  - Footer text (HTML allowed)
  - Good place for unsubscribe link, social media, contact info

#### Managing Blocks

- **Add Block**: Click "Add Block" dropdown, select type
- **Reorder Blocks**: Use ↑ and ↓ buttons
- **Delete Block**: Click trash icon
- **Edit Block**: Modify fields in each block's section

### Using Variables in Templates

Variables are replaced with actual data when emails are sent.

**Common Variables**:

- `{{customer_name}}`: Customer's name
- `{{customer_email}}`: Customer's email
- `{{order_number}}`: Human-readable order number (e.g., "CF-1001")
- `{{order_url}}`: Link to view order details
- `{{tracking_number}}`: Shipping tracking number
- `{{tracking_url}}`: Tracking link
- `{{logo_url}}`: Your store logo
- `{{store_name}}`: Your store name
- `{{store_url}}`: Your store homepage

**Example Subject Line**:

```
Order Confirmation - {{order_number}}
```

**Example Text Block**:

```
Hi {{customer_name}},

Thank you for your order! Your order #{{order_number}} has been confirmed and will be shipped soon.
```

### Previewing Templates

1. While editing a template, click **Preview** button
2. View how the email will look with sample data
3. Check that all variables are rendering correctly
4. Close preview and make adjustments if needed

### Activating/Deactivating Templates

**Active Templates**:

- Will be used when sending emails of that type
- Shows green "Active" badge

**Inactive Templates**:

- Will not be used automatically
- Shows red "Inactive" badge
- Useful for drafts or seasonal templates

**To Toggle Status**:

1. Edit the template
2. Check/uncheck the **Active** checkbox
3. Click **Save**

**Note**: Only one template per email type should be active at a time.

### Deleting Templates

1. Find the template in the list
2. Click the **Delete** button (trash icon)
3. Click again within 3 seconds to confirm

**Note**: Default templates cannot be deleted.

---

## Viewing Email Logs

Email logs show every email sent from your store with real-time status updates.

### Accessing Email Logs

1. Navigate to **Email Management → Email Logs**
2. View table of all sent emails

### Understanding Email Status

**Status Progression**:

1. **Sent**: Email handed off to SendGrid
2. **Delivered**: Email reached recipient's inbox
3. **Opened**: Recipient opened the email
4. **Clicked**: Recipient clicked a link in the email

**Error Statuses**:

- **Bounced**: Email address invalid or mailbox full
- **Failed**: Email could not be sent (configuration issue)

**Status Badge Colors**:

- Sent: Blue
- Delivered: Green
- Opened: Purple
- Clicked: Indigo
- Bounced/Failed: Red

### Filtering Email Logs

Use filters to find specific emails:

**Email Type Filter**:

- All Types
- Order Confirmation
- Shipping Notification
- Marketing

**Status Filter**:

- All Status
- Sent
- Delivered
- Opened
- Clicked
- Bounced
- Failed

**Date Range**:

- Start Date: Select start of date range
- End Date: Select end of date range

### Email Log Details

Each log entry shows:

- **Timestamp**: When email was sent
- **Recipient**: Customer email address
- **Type**: Email type badge
- **Subject**: Email subject line
- **Status**: Current status badge
- **Error Message**: If failed, reason for failure

### Pagination

- Logs display 20 per page
- Use **Previous** and **Next** buttons to navigate
- Page number shown at bottom

---

## Understanding Analytics

Analytics provide insights into your email performance.

### Accessing Analytics

1. Navigate to **Email Management → Analytics**
2. View dashboard with metrics and charts

### Date Range Selection

Choose time period for analytics:

- **Last 7 Days**
- **Last 30 Days**
- **Last 90 Days**
- **Custom Range**: Select specific start and end dates

### Summary Metrics

**Total Sent**:

- Number of emails sent in date range
- All email types combined

**Delivery Rate**:

- Percentage of emails successfully delivered
- Formula: (Delivered / Sent) × 100
- Industry average: ~95%

**Open Rate**:

- Percentage of delivered emails that were opened
- Formula: (Opened / Delivered) × 100
- Industry average for transactional: 20-25%

**Click Rate**:

- Percentage of delivered emails with link clicks
- Formula: (Clicked / Delivered) × 100
- Industry average: 5-10%

### Emails by Type

Breakdown showing send volume for each email type:

- Order Confirmation
- Shipping Notification
- Marketing

### Additional Metrics

**Total Bounced**:

- Number of emails that bounced
- Monitor for high bounce rate (>5% is concerning)

**Total Failed**:

- Number of emails that failed to send
- Investigate if this number is high

**Success Rate**:

- Percentage of emails sent without bounce or failure
- Formula: ((Sent - Bounced - Failed) / Sent) × 100

### Performance Table

Detailed metrics table showing:

- Metric name (Sent, Delivered, Opened, etc.)
- Count of emails
- Percentage of total

### Interpreting Analytics

**Good Performance**:

- Delivery rate >95%
- Open rate 20-30% (transactional), 15-25% (marketing)
- Click rate 5-15%
- Bounce rate <2%

**Poor Performance Indicators**:

- Low delivery rate (<90%): Check sender authentication
- Low open rate (<10%): Improve subject lines
- High bounce rate (>5%): Clean subscriber list
- High spam rate: Review email content

---

## Managing Subscribers

Subscribers are customers and contacts who can receive marketing emails.

### Accessing Subscribers

1. Navigate to **Email Management → Subscribers**
2. View table of all subscribers

### Adding Subscribers

**Manual Entry**:

1. Click **Add Subscriber** button
2. Fill in form:
   - **Email**: Required
   - **Tags**: Comma-separated (e.g., "vip, customer, newsletter")
   - **Customer ID**: Optional - link to existing customer
   - **Subscribed**: Check to enable emails
3. Click **Add Subscriber**

**CSV Import** (Future Feature):

1. Click **Import CSV** button
2. Upload CSV file with columns: email, tags, customer_id
3. Review import preview
4. Confirm import

### Editing Subscribers

1. Find subscriber in table
2. Click **Edit** button (pencil icon)
3. Modify fields in modal
4. Click **Update Subscriber**

### Deleting Subscribers

1. Find subscriber in table
2. Click **Delete** button (trash icon)
3. Click again within 3 seconds to confirm

### Subscriber Tags

Tags allow you to segment your audience for targeted campaigns.

**Example Tags**:

- `vip`: High-value customers
- `new_customer`: Recent purchases
- `newsletter`: Newsletter subscribers
- `abandoned_cart`: Users with abandoned carts
- `repeat_buyer`: Multiple purchases

**Using Tags**:

1. Add tags when creating/editing subscribers
2. Separate multiple tags with commas
3. Use tags when creating campaigns to target specific groups

### Subscriber Metrics

Each subscriber shows:

- **Email**: Email address
- **Tags**: Colored badges for each tag
- **Total Sent**: Number of emails sent to this subscriber
- **Total Opened**: Number of emails they opened
- **Last Sent**: Date of most recent email
- **Status**: Subscribed or Unsubscribed

### Filtering Subscribers

**Search**: Type email to search
**Status Filter**:

- All Status
- Subscribed
- Unsubscribed

**Tags Filter**: Enter tag name to filter by tag

### Exporting Subscribers

1. Click **Export CSV** button
2. CSV file downloads with all subscriber data
3. Open in Excel or Google Sheets

**CSV Columns**:

- email
- tags
- customer_id
- is_subscribed
- total_sent
- total_opened
- total_clicked
- last_sent_at
- subscribed_at

---

## Creating Email Campaigns

Campaigns allow you to send marketing emails to your subscribers on a schedule.

### Accessing Campaigns

1. Navigate to **Email Management → Campaigns**
2. View list of scheduled and completed campaigns

### Campaign List

**Campaign Information**:

- Template name
- Number of recipients
- Scheduled date/time
- Status (Pending, Processing, Completed, Failed, Cancelled)
- Sent/Failed counts

**Actions**:

- **Cancel**: Cancel pending campaigns (before they send)

### Creating a New Campaign

1. Click **Create Campaign** button
2. Follow the 4-step wizard:

#### Step 1: Select Template

- Choose a marketing template
- Only active marketing templates are shown
- Preview shows template name and subject

#### Step 2: Select Recipients

Choose how to select recipients:

**All Subscribers**:

- Sends to all subscribed contacts
- Shows total count

**Filter by Tags**:

- Enter comma-separated tags
- Sends to subscribers with ANY of the tags
- Example: `vip, newsletter` sends to anyone tagged "vip" OR "newsletter"
- Shows filtered count

**Manual Email List**:

- Enter email addresses (one per line)
- Useful for one-time sends or small lists
- Shows count of entered emails

#### Step 3: Schedule

Choose when to send:

**Send Now**:

- Campaign executes immediately
- May take a few minutes depending on recipient count

**Schedule for Later**:

- Choose specific date and time
- Campaign will execute at scheduled time (±1 minute)
- Timezone matches your server timezone

#### Step 4: Review & Confirm

Review campaign details:

- Template name and subject
- Recipient count and selection method
- Schedule (immediate or datetime)

**Actions**:

- **Back**: Return to previous step to make changes
- **Send Campaign** / **Schedule Campaign**: Confirm and create

### Campaign Execution

**Immediate Send**:

1. Campaign created with status "pending"
2. Scheduler picks it up within 60 seconds
3. Status changes to "processing"
4. Emails sent to all recipients
5. Status changes to "completed"

**Scheduled Send**:

1. Campaign created with status "pending"
2. Campaign waits until scheduled time
3. Scheduler executes within 60 seconds of scheduled time
4. Status changes to "processing" → "completed"

### Campaign Status

**Pending**:

- Campaign created, waiting to execute
- Can be cancelled

**Processing**:

- Campaign currently sending emails
- Cannot be cancelled

**Completed**:

- All emails sent successfully
- View sent/failed counts

**Failed**:

- Campaign encountered an error
- Check error message for details

**Cancelled**:

- Campaign was cancelled before execution
- No emails were sent

### Monitoring Campaign Progress

1. After creating campaign, stay on Campaigns page
2. Refresh page to see status updates
3. Status will progress: Pending → Processing → Completed
4. View sent/failed counts when completed

### Cancelling Campaigns

**Before Execution**:

1. Find campaign with "Pending" status
2. Click **Cancel** button
3. Campaign status changes to "Cancelled"

**After Execution Starts**:

- Cannot cancel campaigns in "Processing" or "Completed" status

---

## Best Practices

### Email Design

**Subject Lines**:

- Keep under 50 characters for mobile readability
- Use personalization: `{{customer_name}}`
- Create urgency: "24 Hour Sale" vs. "Sale"
- A/B test different subject lines

**Email Content**:

- Use clear, scannable layout
- Include prominent call-to-action button
- Keep text concise
- Use images sparingly (some email clients block images)
- Always include unsubscribe link in marketing emails

**Branding**:

- Use consistent colors matching your store
- Include logo in all emails
- Use professional imagery
- Maintain brand voice in copy

### Sender Reputation

**Maintain Good Practices**:

- Only email subscribers who opted in
- Honor unsubscribe requests immediately
- Remove hard-bounced emails from your list
- Monitor bounce and spam rates

**Avoid Spam Triggers**:

- Don't use ALL CAPS subject lines
- Avoid excessive exclamation points!!!
- Don't use misleading subject lines
- Include physical mailing address in footer

### Subscriber Management

**Growing Your List**:

- Add signup form on your website
- Offer incentive (discount, free shipping)
- Collect emails at checkout
- Promote newsletter on social media

**Keeping List Healthy**:

- Send regular emails (1-4 per month)
- Remove unengaged subscribers (no opens in 6 months)
- Segment by behavior and preferences
- Use double opt-in for new subscribers

### Campaign Strategy

**Email Frequency**:

- Transactional: As needed (automatic)
- Marketing: 1-4 emails per month
- Too frequent: Leads to unsubscribes
- Too infrequent: Subscribers forget you

**Segmentation**:

- Target campaigns to relevant audiences
- Use tags for behavior-based segments
- Personalize content for each segment
- Test different messages for different groups

**Timing**:

- Best days: Tuesday - Thursday
- Best times: 10am - 11am, 2pm - 3pm
- Avoid weekends and holidays
- Test different send times for your audience

### Testing

**Before Sending**:

- Preview template with real data
- Send test email to yourself
- Check on mobile and desktop
- Click all links to verify they work
- Review for typos and errors

**After Sending**:

- Monitor analytics for first 48 hours
- Review open and click rates
- Check for high bounce rates
- Read any customer feedback

---

## Troubleshooting

### Emails Not Sending

**Problem**: Created campaign but no emails arriving

**Check**:

1. Campaign status - is it still "Pending"?
   - Wait up to 60 seconds for scheduler to execute
2. Check Email Logs page - do entries exist?
   - If yes: Emails were sent, check spam folder
   - If no: Contact support
3. Verify recipient email is correct
4. Check SendGrid account status

### Low Open Rates

**Problem**: Emails sent but few opens (<10%)

**Possible Causes**:

- Subject line not compelling
- Emails going to spam folder
- Sent at wrong time
- Subscribers not engaged

**Solutions**:

- Test different subject lines
- Check spam score of emails
- Send at different times
- Clean unengaged subscribers from list

### High Bounce Rate

**Problem**: Many emails bouncing (>5%)

**Possible Causes**:

- Invalid email addresses
- Purchased email list (don't do this)
- Old subscriber list

**Solutions**:

- Remove hard-bounced emails immediately
- Use double opt-in for new subscribers
- Regularly clean your list
- Verify email addresses before adding

### Template Not Showing

**Problem**: Created template but not appearing in campaign wizard

**Check**:

1. Is template set to Active?
   - Edit template, check "Active" checkbox
2. Is template type "Marketing"?
   - Only marketing templates show in campaigns
   - Transactional templates are automatic

### Variables Not Rendering

**Problem**: Email shows `{{variable_name}}` instead of value

**Cause**: Variable not provided in email context

**Solution**:

- Use only documented variables
- Check variable spelling and case
- Contact support if variable should work

### Campaign Stuck in Pending

**Problem**: Campaign stays in "Pending" status for >5 minutes

**Possible Causes**:

- Scheduler not running
- Server error

**Solutions**:

1. Wait 5-10 minutes, refresh page
2. If still pending, try creating new campaign
3. Contact support if problem persists

---

## Getting Help

### Documentation

- [Email System Setup Guide](./email-system-setup.md) - Technical setup
- [Email Architecture Documentation](./email-architecture.md) - System design
- [Deployment Guide](./deployment-email-system.md) - Production deployment

### Support Channels

- **Help Center**: Access from admin panel
- **Email Support**: support@craftflow.com
- **Live Chat**: Available during business hours

### FAQs

**Q: Can I use custom HTML in emails?**
A: Text blocks support limited HTML. For full custom HTML, contact support.

**Q: How often are email logs updated?**
A: Logs update in real-time as webhook events arrive from SendGrid (usually within seconds).

**Q: Can I restore a deleted template?**
A: No, deleted templates cannot be restored. Default templates cannot be deleted.

**Q: What happens if a campaign fails?**
A: The campaign status will show "Failed" with an error message. No additional attempts are made automatically.

**Q: Can I edit a campaign after it's scheduled?**
A: No, campaigns cannot be edited after creation. You can cancel and create a new one.

**Q: How do I add an unsubscribe link?**
A: Add a footer block with HTML: `<a href="{{unsubscribe_url}}">Unsubscribe</a>`

---

## Terms & Compliance

### CAN-SPAM Compliance

All marketing emails must include:

- Accurate "From" and "Reply-To" addresses
- Accurate subject line
- Physical mailing address in footer
- Clear unsubscribe mechanism
- Honor unsubscribe requests within 10 days

### GDPR Compliance

For European customers:

- Obtain explicit consent before emailing
- Provide clear opt-in checkbox (not pre-checked)
- Allow easy unsubscribe
- Respect right to data deletion

### Best Practices

- Only email people who opted in
- Keep records of consent
- Honor unsubscribe requests immediately
- Provide privacy policy link

---

**Last Updated**: 2026-01-10

**Need Help?** Contact CraftFlow support at support@craftflow.com
