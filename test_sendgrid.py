#!/usr/bin/env python3
"""
SendGrid API Key Test Script

This script sends a test email to verify your SendGrid API key is working correctly.
Run this BEFORE deploying to Railway to ensure your SendGrid setup is complete.

Usage:
    python test_sendgrid.py

Required environment variables:
    SENDGRID_API_KEY - Your SendGrid API key
    SENDGRID_FROM_EMAIL - Your verified sender email
    SENDGRID_FROM_NAME - Your sender name (optional)
"""

import os
import sys

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError:
    print("ERROR: sendgrid package not installed")
    print("Install it with: pip install sendgrid")
    sys.exit(1)


def send_test_email():
    """Send a test email using SendGrid"""

    # Get environment variables
    api_key = os.environ.get('SENDGRID_API_KEY')
    from_email = os.environ.get('SENDGRID_FROM_EMAIL')
    from_name = os.environ.get('SENDGRID_FROM_NAME', 'Test Sender')

    # Validate required variables
    if not api_key:
        print("❌ ERROR: SENDGRID_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export SENDGRID_API_KEY='SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'")
        sys.exit(1)

    if not from_email:
        print("❌ ERROR: SENDGRID_FROM_EMAIL environment variable not set")
        print("\nSet it with:")
        print("  export SENDGRID_FROM_EMAIL='noreply@yourdomain.com'")
        sys.exit(1)

    # Validate API key format
    if not api_key.startswith('SG.'):
        print("⚠️  WARNING: API key doesn't start with 'SG.' - is this correct?")
        print(f"   Key starts with: {api_key[:10]}...")

    print("\n🔄 Testing SendGrid Configuration...")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"   From Email: {from_email}")
    print(f"   From Name: {from_name}")

    # Ask for test recipient email
    print("\n📧 Enter the email address to send the test email to:")
    print("   (This should be YOUR email so you can verify receipt)")
    to_email = input("   Recipient email: ").strip()

    if not to_email or '@' not in to_email:
        print("❌ ERROR: Invalid email address")
        sys.exit(1)

    print(f"\n✉️  Sending test email to {to_email}...")

    # Create email message
    message = Mail(
        from_email=(from_email, from_name),
        to_emails=to_email,
        subject='CraftFlow Email System Test',
        html_content=f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #4F46E5;">✅ SendGrid Test Successful!</h2>
            <p>Your SendGrid API key is working correctly.</p>
            <p><strong>Configuration:</strong></p>
            <ul>
                <li>From Email: {from_email}</li>
                <li>From Name: {from_name}</li>
                <li>API Key: {api_key[:10]}...{api_key[-4:]}</li>
            </ul>
            <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ccc; color: #666; font-size: 12px;">
                This is a test email from the CraftFlow Commerce email system.<br>
                You can now safely deploy your application to Railway.
            </p>
        </body>
        </html>
        """
    )

    try:
        # Initialize SendGrid client
        sg = SendGridAPIClient(api_key)

        # Send email
        response = sg.send(message)

        # Check response
        if response.status_code == 202:
            print(f"\n✅ SUCCESS! Email sent successfully")
            print(f"   Status Code: {response.status_code}")
            print(f"   Message ID: {response.headers.get('X-Message-Id', 'N/A')}")
            print(f"\n📬 Check your inbox at {to_email}")
            print("   The email should arrive within a few seconds.")
            print("\n✨ Your SendGrid setup is complete!")
            print("   You can now deploy to Railway with confidence.")
            return True
        else:
            print(f"\n⚠️  WARNING: Unexpected status code: {response.status_code}")
            print(f"   Response body: {response.body}")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: Failed to send email")
        print(f"   Error: {str(e)}")

        # Provide specific error guidance
        error_str = str(e).lower()
        if 'unauthorized' in error_str or '401' in error_str:
            print("\n💡 This error usually means:")
            print("   • Your API key is invalid or expired")
            print("   • Check your API key in SendGrid dashboard")
        elif 'forbidden' in error_str or '403' in error_str:
            print("\n💡 This error usually means:")
            print("   • Your sender email is not verified in SendGrid")
            print("   • Go to SendGrid → Settings → Sender Authentication")
        elif 'not found' in error_str or '404' in error_str:
            print("\n💡 This error usually means:")
            print("   • The API endpoint is incorrect (shouldn't happen)")
        else:
            print("\n💡 Check the error message above for details")

        return False


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 CraftFlow SendGrid API Key Test")
    print("=" * 60)

    success = send_test_email()

    sys.exit(0 if success else 1)
