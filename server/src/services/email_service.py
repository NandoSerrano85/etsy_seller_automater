"""
Email Service for sending transactional and marketing emails via SendGrid.

This service handles:
- Order confirmation emails (automatic on checkout)
- Shipping notification emails (automatic when tracking is added)
- Marketing emails (manual or scheduled)
- Template rendering with Jinja2
- Email logging for audit and analytics
- SendGrid API integration with error handling
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
import json

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Substitution
from jinja2 import Template
from sqlalchemy.orm import Session

from server.src.entities.ecommerce.email_template import EmailTemplate
from server.src.entities.ecommerce.email_log import EmailLog
from server.src.entities.ecommerce.email_subscriber import EmailSubscriber
from server.src.entities.ecommerce.order import Order

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SendGrid with template rendering."""

    def __init__(self, api_key: Optional[str] = None, db: Optional[Session] = None):
        """
        Initialize EmailService.

        Args:
            api_key: SendGrid API key (defaults to SENDGRID_API_KEY env var)
            db: Database session for logging emails
        """
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@yourdomain.com")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "Your Store")
        self.enabled = os.getenv("ENABLE_EMAIL_SERVICE", "false").lower() == "true"
        self.db = db

        if not self.api_key and self.enabled:
            logger.warning("SENDGRID_API_KEY not set but email service is enabled")

        self.sg = SendGridAPIClient(self.api_key) if self.api_key else None

    def _render_template(self, template: EmailTemplate, context: Dict[str, Any]) -> str:
        """
        Render email template blocks to HTML.

        Args:
            template: EmailTemplate instance with blocks
            context: Template variables (e.g., order_number, customer_name)

        Returns:
            Rendered HTML string
        """
        try:
            html_parts = []

            # Add basic HTML structure
            html_parts.append('<!DOCTYPE html>')
            html_parts.append('<html>')
            html_parts.append('<head><meta charset="UTF-8"><style>')
            html_parts.append('body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }')
            html_parts.append('h1 { font-size: 24px; margin-bottom: 20px; }')
            html_parts.append('.button { display: inline-block; padding: 12px 24px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }')
            html_parts.append('.footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }')
            html_parts.append('</style></head>')
            html_parts.append('<body>')

            # Render each block
            for block in template.blocks:
                block_type = block.get('type')

                if block_type == 'logo' and block.get('src'):
                    src = self._substitute_vars(block['src'], context)
                    align = block.get('align', 'left')
                    html_parts.append(f'<div style="text-align: {align}; margin-bottom: 20px;">')
                    html_parts.append(f'<img src="{src}" alt="Logo" style="max-width: 200px; height: auto;" />')
                    html_parts.append('</div>')

                elif block_type == 'header':
                    text = self._substitute_vars(block.get('text', ''), context)
                    color = block.get('color', template.primary_color)
                    html_parts.append(f'<h1 style="color: {color};">{text}</h1>')

                elif block_type == 'text':
                    content = self._substitute_vars(block.get('content', ''), context)
                    html_parts.append(f'<p>{content}</p>')

                elif block_type == 'button':
                    text = self._substitute_vars(block.get('text', ''), context)
                    url = self._substitute_vars(block.get('url', '#'), context)
                    bg_color = block.get('bg_color', template.primary_color)
                    html_parts.append(f'<a href="{url}" class="button" style="background-color: {bg_color};">{text}</a>')

                elif block_type == 'order_summary' and 'order' in context:
                    html_parts.append(self._render_order_summary(context['order'], block))

                elif block_type == 'tracking_info':
                    tracking_number = self._substitute_vars(block.get('tracking_number', ''), context)
                    html_parts.append('<div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">')
                    html_parts.append(f'<p><strong>Tracking Number:</strong> {tracking_number}</p>')
                    html_parts.append('</div>')

                elif block_type == 'shipping_address' and 'order' in context:
                    html_parts.append(self._render_shipping_address(context['order']))

                elif block_type == 'footer':
                    content = self._substitute_vars(block.get('content', ''), context)
                    html_parts.append(f'<div class="footer">{content}</div>')

            # Close HTML
            html_parts.append('</body></html>')

            return '\n'.join(html_parts)

        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return "<html><body>Error rendering email template</body></html>"

    def _substitute_vars(self, text: str, context: Dict[str, Any]) -> str:
        """Replace {{variable}} placeholders with context values."""
        try:
            template = Template(text)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error substituting variables: {e}")
            return text

    def _render_order_summary(self, order: Order, block: Dict) -> str:
        """Render order summary block."""
        html = []
        html.append('<div style="background-color: #f9fafb; padding: 20px; border-radius: 5px; margin: 20px 0;">')
        html.append('<h2 style="font-size: 18px; margin-top: 0;">Order Summary</h2>')

        if block.get('show_items', True):
            html.append('<table style="width: 100%; margin-bottom: 15px;">')
            for item in order.items:
                item_data = item if isinstance(item, dict) else {
                    'product_name': getattr(item, 'product_name', ''),
                    'quantity': getattr(item, 'quantity', 1),
                    'price': getattr(item, 'price', 0),
                    'total': getattr(item, 'total', 0)
                }
                html.append('<tr>')
                html.append(f'<td>{item_data["product_name"]}</td>')
                html.append(f'<td>Qty: {item_data["quantity"]}</td>')
                html.append(f'<td style="text-align: right;">${item_data["total"]:.2f}</td>')
                html.append('</tr>')
            html.append('</table>')

        if block.get('show_totals', True):
            html.append('<table style="width: 100%; border-top: 1px solid #ddd; padding-top: 10px;">')
            html.append(f'<tr><td>Subtotal:</td><td style="text-align: right;">${order.subtotal:.2f}</td></tr>')
            html.append(f'<tr><td>Tax:</td><td style="text-align: right;">${order.tax:.2f}</td></tr>')
            html.append(f'<tr><td>Shipping:</td><td style="text-align: right;">${order.shipping:.2f}</td></tr>')
            html.append(f'<tr><td><strong>Total:</strong></td><td style="text-align: right;"><strong>${order.total:.2f}</strong></td></tr>')
            html.append('</table>')

        html.append('</div>')
        return '\n'.join(html)

    def _render_shipping_address(self, order: Order) -> str:
        """Render shipping address block."""
        addr = order.shipping_address if isinstance(order.shipping_address, dict) else {}
        html = []
        html.append('<div style="margin: 20px 0;">')
        html.append('<h3 style="font-size: 16px;">Shipping Address</h3>')
        html.append(f'<p>{addr.get("first_name", "")} {addr.get("last_name", "")}<br>')
        if addr.get("company"):
            html.append(f'{addr["company"]}<br>')
        html.append(f'{addr.get("address1", "")}<br>')
        if addr.get("address2"):
            html.append(f'{addr["address2"]}<br>')
        html.append(f'{addr.get("city", "")}, {addr.get("state", "")} {addr.get("zip_code", "")}<br>')
        html.append(f'{addr.get("country", "USA")}</p>')
        html.append('</div>')
        return '\n'.join(html)

    def send_order_confirmation(
        self,
        user_id: UUID,
        order: Order,
        recipient_email: str
    ) -> Optional[EmailLog]:
        """
        Send order confirmation email.

        Args:
            user_id: Store owner user ID
            order: Order instance
            recipient_email: Customer email address

        Returns:
            EmailLog instance if successful, None if disabled or failed
        """
        if not self.enabled or not self.sg:
            logger.info("Email service disabled, skipping order confirmation")
            return None

        try:
            # Get active order confirmation template
            template = self.db.query(EmailTemplate).filter(
                EmailTemplate.user_id == user_id,
                EmailTemplate.email_type == "order_confirmation",
                EmailTemplate.is_active == True
            ).first()

            if not template:
                logger.warning(f"No active order confirmation template found for user {user_id}")
                return None

            # Build template context
            context = {
                'order_number': order.order_number,
                'customer_name': f"{order.shipping_address.get('first_name', '')} {order.shipping_address.get('last_name', '')}",
                'order': order,
                'order_url': f"https://yourdomain.com/orders/{order.id}",
                'support_email': self.from_email,
                'logo_url': template.logo_url or '',
                'primary_color': template.primary_color,
                'secondary_color': template.secondary_color
            }

            # Render template
            html_content = self._render_template(template, context)
            subject = self._substitute_vars(template.subject, context)

            # Send via SendGrid
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(recipient_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            response = self.sg.send(message)

            # Log email
            email_log = EmailLog(
                user_id=user_id,
                template_id=template.id,
                email_type="order_confirmation",
                recipient_email=recipient_email,
                subject=subject,
                order_id=order.id,
                customer_id=order.customer_id,
                sendgrid_message_id=response.headers.get('X-Message-Id'),
                sendgrid_status="sent"
            )
            self.db.add(email_log)
            self.db.commit()

            logger.info(f"Order confirmation email sent to {recipient_email} for order {order.order_number}")
            return email_log

        except Exception as e:
            logger.error(f"Failed to send order confirmation email: {e}")
            # Log failure
            if self.db:
                email_log = EmailLog(
                    user_id=user_id,
                    email_type="order_confirmation",
                    recipient_email=recipient_email,
                    subject=f"Order Confirmation - {order.order_number}",
                    order_id=order.id,
                    sendgrid_status="failed",
                    error_message=str(e)
                )
                self.db.add(email_log)
                try:
                    self.db.commit()
                except:
                    pass
            return None

    def send_shipping_notification(
        self,
        user_id: UUID,
        order: Order,
        tracking_number: str,
        tracking_url: str,
        recipient_email: str
    ) -> Optional[EmailLog]:
        """
        Send shipping notification email.

        Args:
            user_id: Store owner user ID
            order: Order instance
            tracking_number: Shipment tracking number
            tracking_url: Tracking URL
            recipient_email: Customer email address

        Returns:
            EmailLog instance if successful, None if disabled or failed
        """
        if not self.enabled or not self.sg:
            logger.info("Email service disabled, skipping shipping notification")
            return None

        try:
            # Get active shipping notification template
            template = self.db.query(EmailTemplate).filter(
                EmailTemplate.user_id == user_id,
                EmailTemplate.email_type == "shipping_notification",
                EmailTemplate.is_active == True
            ).first()

            if not template:
                logger.warning(f"No active shipping notification template found for user {user_id}")
                return None

            # Build template context
            context = {
                'order_number': order.order_number,
                'customer_name': f"{order.shipping_address.get('first_name', '')} {order.shipping_address.get('last_name', '')}",
                'order': order,
                'tracking_number': tracking_number,
                'tracking_url': tracking_url,
                'support_email': self.from_email,
                'logo_url': template.logo_url or '',
                'primary_color': template.primary_color,
                'secondary_color': template.secondary_color
            }

            # Render template
            html_content = self._render_template(template, context)
            subject = self._substitute_vars(template.subject, context)

            # Send via SendGrid
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(recipient_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            response = self.sg.send(message)

            # Log email
            email_log = EmailLog(
                user_id=user_id,
                template_id=template.id,
                email_type="shipping_notification",
                recipient_email=recipient_email,
                subject=subject,
                order_id=order.id,
                customer_id=order.customer_id,
                sendgrid_message_id=response.headers.get('X-Message-Id'),
                sendgrid_status="sent"
            )
            self.db.add(email_log)
            self.db.commit()

            logger.info(f"Shipping notification sent to {recipient_email} for order {order.order_number}")
            return email_log

        except Exception as e:
            logger.error(f"Failed to send shipping notification: {e}")
            # Log failure
            if self.db:
                email_log = EmailLog(
                    user_id=user_id,
                    email_type="shipping_notification",
                    recipient_email=recipient_email,
                    subject=f"Shipping Notification - {order.order_number}",
                    order_id=order.id,
                    sendgrid_status="failed",
                    error_message=str(e)
                )
                self.db.add(email_log)
                try:
                    self.db.commit()
                except:
                    pass
            return None

    def send_marketing_email(
        self,
        user_id: UUID,
        template_id: UUID,
        recipients: List[str],
        scheduled_email_id: Optional[UUID] = None
    ) -> List[EmailLog]:
        """
        Send marketing email to multiple recipients.

        Args:
            user_id: Store owner user ID
            template_id: Marketing email template ID
            recipients: List of recipient email addresses
            scheduled_email_id: Optional scheduled email ID for tracking

        Returns:
            List of EmailLog instances
        """
        if not self.enabled or not self.sg:
            logger.info("Email service disabled, skipping marketing email")
            return []

        logs = []

        try:
            # Get template
            template = self.db.query(EmailTemplate).filter(
                EmailTemplate.id == template_id,
                EmailTemplate.user_id == user_id
            ).first()

            if not template:
                logger.error(f"Template {template_id} not found")
                return []

            for recipient in recipients:
                try:
                    # Build basic context for marketing emails
                    context = {
                        'logo_url': template.logo_url or '',
                        'primary_color': template.primary_color,
                        'secondary_color': template.secondary_color,
                        'support_email': self.from_email,
                        'unsubscribe_url': f"https://yourdomain.com/api/ecommerce/emails/unsubscribe/{user_id}/{recipient}"
                    }

                    # Render template
                    html_content = self._render_template(template, context)
                    subject = self._substitute_vars(template.subject, context)

                    # Send via SendGrid
                    message = Mail(
                        from_email=Email(self.from_email, self.from_name),
                        to_emails=To(recipient),
                        subject=subject,
                        html_content=Content("text/html", html_content)
                    )

                    response = self.sg.send(message)

                    # Log email
                    email_log = EmailLog(
                        user_id=user_id,
                        template_id=template.id,
                        email_type="marketing",
                        recipient_email=recipient,
                        subject=subject,
                        sendgrid_message_id=response.headers.get('X-Message-Id'),
                        sendgrid_status="sent"
                    )
                    self.db.add(email_log)
                    logs.append(email_log)

                    # Update subscriber stats
                    subscriber = self.db.query(EmailSubscriber).filter(
                        EmailSubscriber.user_id == user_id,
                        EmailSubscriber.email == recipient
                    ).first()
                    if subscriber:
                        subscriber.total_sent += 1
                        subscriber.last_sent_at = datetime.utcnow()

                except Exception as e:
                    logger.error(f"Failed to send marketing email to {recipient}: {e}")
                    # Log individual failure
                    email_log = EmailLog(
                        user_id=user_id,
                        template_id=template.id,
                        email_type="marketing",
                        recipient_email=recipient,
                        subject=template.subject,
                        sendgrid_status="failed",
                        error_message=str(e)
                    )
                    self.db.add(email_log)
                    logs.append(email_log)

            self.db.commit()
            logger.info(f"Sent {len(logs)} marketing emails for template {template_id}")
            return logs

        except Exception as e:
            logger.error(f"Failed to send marketing emails: {e}")
            return logs


# Default email template definitions
DEFAULT_EMAIL_TEMPLATES = [
    {
        "name": "Order Confirmation",
        "template_type": "transactional",
        "email_type": "order_confirmation",
        "subject": "Order Confirmation - #{{order_number}}",
        "blocks": [
            {"type": "logo", "src": "{{logo_url}}", "align": "center"},
            {"type": "header", "text": "Thank you for your order!", "color": "{{primary_color}}"},
            {"type": "text", "content": "Hi {{customer_name}},"},
            {"type": "text", "content": "We've received your order and are processing it now."},
            {"type": "order_summary", "show_items": True, "show_totals": True},
            {"type": "button", "text": "View Order", "url": "{{order_url}}", "bg_color": "{{primary_color}}"},
            {"type": "text", "content": "Order Number: {{order_number}}"},
            {"type": "shipping_address"},
            {"type": "footer", "content": "Questions? Contact us at {{support_email}}"}
        ]
    },
    {
        "name": "Shipping Notification",
        "template_type": "transactional",
        "email_type": "shipping_notification",
        "subject": "Your order has shipped!",
        "blocks": [
            {"type": "logo", "src": "{{logo_url}}", "align": "center"},
            {"type": "header", "text": "Your order is on the way!", "color": "{{primary_color}}"},
            {"type": "text", "content": "Hi {{customer_name}},"},
            {"type": "text", "content": "Great news! Your order #{{order_number}} has shipped."},
            {"type": "tracking_info", "tracking_number": "{{tracking_number}}"},
            {"type": "button", "text": "Track Your Package", "url": "{{tracking_url}}", "bg_color": "{{primary_color}}"},
            {"type": "order_summary", "show_items": True},
            {"type": "footer", "content": "Questions? Contact us at {{support_email}}"}
        ]
    }
]


def create_default_templates(db: Session, user_id: UUID, storefront_settings) -> List[EmailTemplate]:
    """
    Create default email templates for a new user.

    Args:
        db: Database session
        user_id: User ID
        storefront_settings: StorefrontSettings instance for branding

    Returns:
        List of created EmailTemplate instances
    """
    templates = []

    for template_data in DEFAULT_EMAIL_TEMPLATES:
        # Check if template already exists
        existing = db.query(EmailTemplate).filter(
            EmailTemplate.user_id == user_id,
            EmailTemplate.email_type == template_data["email_type"]
        ).first()

        if not existing:
            template = EmailTemplate(
                user_id=user_id,
                name=template_data["name"],
                template_type=template_data["template_type"],
                email_type=template_data["email_type"],
                subject=template_data["subject"],
                blocks=template_data["blocks"],
                primary_color=storefront_settings.primary_color if storefront_settings else "#10b981",
                secondary_color=storefront_settings.secondary_color if storefront_settings else "#059669",
                logo_url=storefront_settings.logo_url if storefront_settings else None,
                is_active=True,
                is_default=True
            )
            db.add(template)
            templates.append(template)
            logger.info(f"Created default template: {template_data['name']}")

    if templates:
        db.commit()
        logger.info(f"Created {len(templates)} default email templates for user {user_id}")

    return templates
