# Email System Deployment Guide

This guide covers deploying the CraftFlow Commerce email system to production, with specific instructions for Railway deployment.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [SendGrid Production Setup](#sendgrid-production-setup)
3. [Railway Deployment Steps](#railway-deployment-steps)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Troubleshooting Production Issues](#troubleshooting-production-issues)
7. [Rollback Procedure](#rollback-procedure)

---

## Pre-Deployment Checklist

Before deploying the email system to production, ensure the following requirements are met:

### Code Readiness

- [ ] All backend files committed to repository:
  - `server/src/services/email_campaign_scheduler.py`
  - `server/main.py` (lifespan integration)
  - `server/src/routes/ecommerce/storefront_settings.py` (default templates)
  - `server/src/services/email_service.py` (existing)
  - `server/src/routes/ecommerce/admin_emails/` (existing)
  - `server/src/routes/ecommerce/webhooks.py` (existing)
  - All entity models (email_template, email_log, etc.)

- [ ] All frontend files committed to repository:
  - `frontend/src/pages/CraftFlow/Emails/*.js` (6 pages)
  - `frontend/src/App.js` (routes added)
  - `frontend/src/components/SidebarNavigation.js` (link added)

- [ ] Database migrations created and tested locally
- [ ] No pending schema changes
- [ ] All tests passing (if applicable)

### SendGrid Account

- [ ] Production SendGrid account created
- [ ] Sender email verified (single sender or domain authentication)
- [ ] API key created with Full Access or Mail Send permission
- [ ] Webhook endpoint configured
- [ ] Webhook signature verification enabled (recommended)

### Environment Variables

Required variables ready to deploy:

```bash
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME="Your Store Name"
ENABLE_EMAIL_SERVICE=true
SENDGRID_WEBHOOK_SECRET=your_random_secret_here  # Optional but recommended
```

### Database

- [ ] Production database has sufficient storage for email logs
- [ ] Indexes created on email tables (see Architecture docs)
- [ ] Backups configured

### Dependencies

- [ ] `requirements.txt` includes all email-related packages:
  - `sendgrid>=6.9.7`
  - `jinja2>=3.1.2`
  - No additional packages needed (asyncio is built-in)

---

## SendGrid Production Setup

### 1. Create Production SendGrid Account

1. Go to [SendGrid.com](https://sendgrid.com/pricing/)
2. Choose appropriate plan:
   - **Free**: 100 emails/day (testing only)
   - **Essentials**: 50k-100k emails/month ($19.95+)
   - **Pro**: 1.5M+ emails/month ($89.95+)

### 2. Domain Authentication (Recommended)

Domain authentication improves deliverability and removes "via sendgrid.net" from emails.

**Steps**:

1. Navigate to **Settings → Sender Authentication → Authenticate Your Domain**
2. Select your DNS provider
3. Add the provided DNS records to your domain:

   ```
   Type: CNAME
   Name: em1234.yourdomain.com
   Value: u1234567.wl134.sendgrid.net

   Type: CNAME
   Name: s1._domainkey.yourdomain.com
   Value: s1.domainkey.u1234567.wl134.sendgrid.net

   Type: CNAME
   Name: s2._domainkey.yourdomain.com
   Value: s2.domainkey.u1234567.wl134.sendgrid.net
   ```

4. Wait for DNS propagation (up to 48 hours)
5. Return to SendGrid and click **Verify**

**Verification**:

```bash
# Check DNS records
dig CNAME em1234.yourdomain.com
dig CNAME s1._domainkey.yourdomain.com
```

### 3. Create Production API Key

1. Navigate to **Settings → API Keys**
2. Click **Create API Key**
3. Name: "CraftFlow Production"
4. Permissions: **Full Access** (or Restricted with Mail Send enabled)
5. Copy key immediately (won't be shown again)
6. Store securely in password manager

**Security Best Practice**: Rotate API keys every 90 days.

### 4. Configure Webhook

1. Navigate to **Settings → Mail Settings → Event Webhook**
2. Enable the Event Webhook
3. Set HTTP Post URL:
   ```
   https://yourdomain.com/api/ecommerce/webhooks/sendgrid
   ```
4. Authorization Method: None (we use custom verification)
5. Select events:
   - ☑ Delivered
   - ☑ Opened
   - ☑ Clicked
   - ☑ Bounced
   - ☑ Dropped
   - ☑ Spam Report
   - ☑ Unsubscribe
6. Enable **Event Webhook Signature** (highly recommended)
7. Copy the Verification Key
8. Click **Save**

### 5. Configure Email Activity Feed (Optional)

Enables viewing sent emails in SendGrid dashboard:

1. Navigate to **Settings → Mail Settings → Email Activity**
2. Enable Email Activity
3. Retention: Choose appropriate duration (7-30 days)

---

## Railway Deployment Steps

### Step 1: Database Migration

Run database migrations to create email tables:

```bash
# SSH into Railway container or run locally with production DB
alembic upgrade head

# Or use your migration tool
python migration-service/run-migrations.py
```

**Verify Tables Created**:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('email_templates', 'email_logs', 'email_subscribers', 'scheduled_emails');
```

### Step 2: Set Environment Variables

In Railway dashboard:

1. Navigate to your project
2. Go to **Variables** tab
3. Add environment variables:

```
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=Your Store Name
ENABLE_EMAIL_SERVICE=true
SENDGRID_WEBHOOK_SECRET=your_verification_key_from_sendgrid
```

**Verify Variables**:

- Click **View Raw** to ensure no extra spaces or newlines
- Check that API key starts with "SG."

### Step 3: Deploy Code

#### Via GitHub Integration (Recommended)

1. Push code to GitHub:

   ```bash
   git add .
   git commit -m "Add email system with scheduler and admin UI"
   git push origin main
   ```

2. Railway will auto-deploy from the `main` branch

#### Via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

### Step 4: Verify Deployment

Check deployment logs in Railway dashboard:

**Expected Logs**:

```
✅ Database connected
✅ Email campaign scheduler started
✅ Server started on port 3003
```

**Error Logs to Watch For**:

```
⚠️ Warning: Failed to start email campaign scheduler
⚠️ Warning: ENABLE_EMAIL_SERVICE not set, email features disabled
```

### Step 5: Configure Webhook URL

Update SendGrid webhook with production URL:

1. Get your Railway app URL:

   ```
   https://your-app-name.up.railway.app
   ```

2. Update webhook in SendGrid:

   ```
   https://your-app-name.up.railway.app/api/ecommerce/webhooks/sendgrid
   ```

3. Test webhook:
   - Click **Test Your Integration** in SendGrid
   - Check Railway logs for: "Received SendGrid webhook event"

---

## Post-Deployment Verification

### 1. Health Checks

**Check Scheduler Status**:

```bash
# View Railway logs
railway logs

# Look for scheduler startup
grep "Email campaign scheduler started" logs.txt
```

**Check API Endpoints**:

```bash
# Test templates endpoint
curl -X GET https://yourdomain.com/api/ecommerce/admin/emails/templates \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should return 200 OK with templates array
```

### 2. Initialize Default Templates

Default templates are created when a user first saves storefront settings:

1. Login to admin panel
2. Navigate to **CraftFlow → Storefront Settings**
3. Configure branding (logo URL, colors)
4. Click **Save**
5. Check logs for: "✅ Default email templates created"
6. Navigate to **Email Management → Templates**
7. Verify 2 default templates exist:
   - Order Confirmation (transactional)
   - Shipping Notification (transactional)

### 3. Send Test Email

**Via Admin UI**:

1. Navigate to **Email Management → Campaigns**
2. Click **Create Campaign**
3. Select a template
4. Choose "Manual Email List"
5. Enter your test email
6. Select "Send Now"
7. Check inbox for email

**Via API**:

```bash
curl -X POST https://yourdomain.com/api/ecommerce/admin/emails/send-marketing \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "recipient_emails": ["test@example.com"],
    "scheduled_for": null
  }'
```

### 4. Verify Webhook Processing

1. Send test email (from step 3)
2. Open the email
3. Click a link in the email
4. Navigate to **Email Management → Logs**
5. Verify status progresses: sent → delivered → opened → clicked
6. Check Railway logs for webhook events:
   ```
   Received SendGrid webhook event: delivered for test@example.com
   Received SendGrid webhook event: open for test@example.com
   Received SendGrid webhook event: click for test@example.com
   ```

### 5. Verify Scheduled Campaigns

1. Create campaign scheduled for 2 minutes in future
2. Wait for scheduler to execute
3. Check logs for:
   ```
   Executing scheduled campaign 123
   Campaign 123 completed: 1 sent, 0 failed
   ```
4. Verify campaign status changed to "completed" in UI

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Email Send Volume**
   - Track daily send counts per user
   - Alert if exceeding SendGrid plan limits

2. **Scheduler Health**
   - Monitor scheduler loop logs
   - Alert if scheduler stops running

3. **SendGrid API Errors**
   - Track API error rates
   - Alert on high failure rates (>5%)

4. **Webhook Processing**
   - Monitor webhook receipt rate
   - Alert if webhooks stop arriving

5. **Database Performance**
   - Monitor query times for email tables
   - Alert on slow queries (>1s)

### Recommended Monitoring Tools

#### Railway Metrics (Built-in)

- CPU & Memory usage
- Request volume & latency
- Error rates

#### External Monitoring

**SendGrid Dashboard**:

- Navigate to **Activity** for email metrics
- Set up **Alerts** for bounce/spam rates

**Application Monitoring** (Optional):

- Sentry for error tracking
- DataDog/New Relic for performance monitoring
- Uptime Robot for endpoint availability

### Alert Configurations

**Critical Alerts** (immediate response):

- Scheduler stopped running
- Webhook endpoint returning 500 errors
- SendGrid API key invalid/expired
- Database connection failures

**Warning Alerts** (monitor):

- High bounce rate (>5%)
- High spam rate (>0.1%)
- Slow webhook processing (>5s)
- Campaign execution delays (>5 minutes)

### Log Retention

Configure log retention in Railway:

- Railway keeps logs for 7 days by default
- For longer retention, use external logging (Papertrail, Loggly, etc.)

---

## Troubleshooting Production Issues

### Issue: Scheduler Not Running

**Symptoms**:

- Campaigns stuck in "pending" status
- No scheduler logs in Railway

**Diagnosis**:

```bash
# Check logs for scheduler startup
railway logs | grep "Email campaign scheduler"

# Should see:
# ✅ Email campaign scheduler started
```

**Solutions**:

1. Verify scheduler integration in `main.py`:
   ```python
   asyncio.create_task(start_email_campaign_scheduler())
   ```
2. Check for exceptions in scheduler:
   ```bash
   railway logs | grep "Error in scheduler"
   ```
3. Restart Railway service:
   ```bash
   railway restart
   ```

### Issue: Emails Not Sending

**Symptoms**:

- Emails stuck in logs with "sent" status
- No emails received

**Diagnosis**:

```bash
# Check SendGrid API key validity
curl -X GET https://api.sendgrid.com/v3/scopes \
  -H "Authorization: Bearer $SENDGRID_API_KEY"

# Should return list of scopes
```

**Solutions**:

1. Verify `ENABLE_EMAIL_SERVICE=true` in Railway variables
2. Check SendGrid API key is correct (starts with "SG.")
3. Verify sender email is verified in SendGrid
4. Check SendGrid account status (not suspended)
5. Review Railway logs for API errors:
   ```bash
   railway logs | grep "SendGrid API error"
   ```

### Issue: Webhooks Not Updating Status

**Symptoms**:

- All emails stuck in "sent" status
- No "delivered" or "opened" events

**Diagnosis**:

```bash
# Test webhook endpoint
curl -X POST https://yourdomain.com/api/ecommerce/webhooks/sendgrid \
  -H "Content-Type: application/json" \
  -d '[{"event":"test"}]'

# Should return 200 OK
```

**Solutions**:

1. Verify webhook URL in SendGrid matches Railway URL
2. Check webhook endpoint is publicly accessible (not localhost)
3. Temporarily disable signature verification:
   - Remove `SENDGRID_WEBHOOK_SECRET` from Railway variables
   - Restart app
   - Test webhook
4. Check Railway logs for webhook errors:
   ```bash
   railway logs | grep "webhook"
   ```

### Issue: High Memory Usage

**Symptoms**:

- Railway app restarting frequently
- Memory usage at 100%

**Diagnosis**:

```bash
# Check Railway metrics for memory usage spike
# Review logs for OOM errors
```

**Solutions**:

1. Increase Railway memory limit (upgrade plan if needed)
2. Optimize email log query pagination
3. Add email log cleanup job (delete old logs)
4. Cache rendered templates to reduce rendering load

### Issue: Slow Campaign Execution

**Symptoms**:

- Campaigns take >10 minutes to complete
- High CPU usage during execution

**Diagnosis**:

- Check campaign recipient count
- Review SendGrid API latency in logs

**Solutions**:

1. Batch email sends (100 recipients per batch)
2. Add rate limiting between batches
3. Increase scheduler polling frequency (30s instead of 60s)
4. Consider using SendGrid's batch API endpoint

---

## Rollback Procedure

If critical issues arise after deployment, follow this rollback procedure:

### 1. Identify Rollback Target

Determine last stable deployment:

```bash
# View Railway deployment history
railway status

# Or check Git commits
git log --oneline
```

### 2. Rollback Code

**Via Railway Dashboard**:

1. Navigate to **Deployments** tab
2. Find last stable deployment
3. Click **Redeploy**

**Via Git**:

```bash
# Revert to previous commit
git revert HEAD
git push origin main

# Railway will auto-deploy
```

### 3. Rollback Database (if schema changed)

**If migrations were run**:

```bash
# Downgrade database
alembic downgrade -1

# Or restore from backup
pg_restore -d $DATABASE_URL backup.dump
```

### 4. Verify Rollback

1. Check Railway logs for clean startup
2. Test email sending via admin UI
3. Verify existing data intact (templates, logs, subscribers)
4. Monitor for error rates

### 5. Post-Rollback Actions

1. Investigate root cause of issues
2. Fix issues in development environment
3. Test thoroughly before redeploying
4. Document incident and lessons learned

---

## Production Best Practices

### 1. Staging Environment

Before production deployment, test in staging:

- Deploy to Railway staging project
- Use SendGrid sandbox mode
- Test all features end-to-end

### 2. Gradual Rollout

For large user bases:

1. Deploy email system with `ENABLE_EMAIL_SERVICE=false`
2. Enable for 10% of users (feature flag)
3. Monitor metrics for 24 hours
4. Gradually increase to 100%

### 3. Database Maintenance

Schedule regular maintenance:

- Clean up old email logs (>90 days)
- Vacuum PostgreSQL tables
- Review slow queries

```sql
-- Delete old logs
DELETE FROM email_logs WHERE sent_at < NOW() - INTERVAL '90 days';

-- Vacuum tables
VACUUM ANALYZE email_logs;
VACUUM ANALYZE scheduled_emails;
```

### 4. Backup Strategy

- Railway provides automatic database backups
- Export email templates before major updates
- Keep audit trail of template changes

### 5. Security Hardening

- Rotate SendGrid API keys every 90 days
- Enable SendGrid IP access restrictions
- Use webhook signature verification in production
- Implement rate limiting on admin endpoints

---

## Post-Deployment Checklist

After successful deployment, verify:

- [ ] Scheduler running and processing campaigns
- [ ] Test email sent and received successfully
- [ ] Webhooks updating email statuses
- [ ] Admin UI accessible and functional
- [ ] Default templates created for all users
- [ ] Monitoring alerts configured
- [ ] SendGrid account in good standing
- [ ] Documentation updated with production URLs
- [ ] Team trained on email system usage

---

## Support & Resources

- [Railway Documentation](https://docs.railway.app/)
- [SendGrid Documentation](https://docs.sendgrid.com/)
- [Email System Setup Guide](./email-system-setup.md)
- [Email Architecture Documentation](./email-architecture.md)
- [Admin User Guide](./email-admin-guide.md)

For deployment issues, check:

1. Railway logs: `railway logs`
2. SendGrid Activity Feed
3. Database query logs
4. Application error tracking (Sentry, etc.)

---

**Last Updated**: 2026-01-10
