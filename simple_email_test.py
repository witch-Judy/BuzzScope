#!/usr/bin/env python3
"""
Simple Email Test - Test Gmail SMTP connection
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_gmail_connection():
    """Test Gmail SMTP connection and send a test email"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get email configuration
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')
    to_email = os.getenv('TO_EMAIL')
    
    print("📧 Testing Gmail SMTP Connection")
    print("=" * 40)
    print(f"SMTP Server: {smtp_server}:{smtp_port}")
    print(f"Username: {username}")
    print(f"From: {from_email}")
    print(f"To: {to_email}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    
    if not all([username, password, from_email, to_email]):
        print("❌ Missing email configuration!")
        print("Please check your .env file.")
        return False
    
    # Create test email
    subject = "🔥 BuzzScope Hot Post Monitor - Test Email"
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
            .test-info {{ margin: 20px 0; }}
            .success {{ color: #28a745; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🔥 BuzzScope Hot Post Monitor</h2>
            <p class="success">✅ Email system is working correctly!</p>
        </div>
        
        <div class="test-info">
            <h3>Test Information:</h3>
            <ul>
                <li><strong>Test Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                <li><strong>From:</strong> {from_email}</li>
                <li><strong>To:</strong> {to_email}</li>
                <li><strong>Status:</strong> <span class="success">SUCCESS</span></li>
            </ul>
        </div>
        
        <div class="test-info">
            <h3>What's Next?</h3>
            <p>Your email notification system is now ready! You can:</p>
            <ul>
                <li>Run hot post monitoring: <code>python3 monitor_hot_posts.py once</code></li>
                <li>Start continuous monitoring: <code>python3 monitor_hot_posts.py continuous --interval 30</code></li>
            </ul>
        </div>
        
        <div class="test-info">
            <h3>Monitoring Keywords:</h3>
            <p>ai, iot, mqtt, unified_namespace</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
🔥 BuzzScope Hot Post Monitor - Test Email

✅ Email system is working correctly!

Test Information:
- Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- From: {from_email}
- To: {to_email}
- Status: SUCCESS

What's Next?
Your email notification system is now ready! You can:
- Run hot post monitoring: python3 monitor_hot_posts.py once
- Start continuous monitoring: python3 monitor_hot_posts.py continuous --interval 30

Monitoring Keywords: ai, iot, mqtt, unified_namespace
    """
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    
    # Add both text and HTML versions
    text_part = MIMEText(text_content, 'plain')
    html_part = MIMEText(html_content, 'html')
    
    msg.attach(text_part)
    msg.attach(html_part)
    
    # Send email
    try:
        print("\n📤 Connecting to Gmail SMTP server...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("🔐 Starting TLS encryption...")
            server.starttls()
            
            print("🔑 Authenticating with Gmail...")
            server.login(username, password)
            
            print("📧 Sending test email...")
            server.send_message(msg)
            
        print("✅ Test email sent successfully!")
        print(f"📬 Check your inbox at {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("🔧 Troubleshooting:")
        print("1. Check your Gmail app password")
        print("2. Ensure 2-factor authentication is enabled")
        print("3. Make sure you're using the app password, not your regular password")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    print("🔥 BuzzScope Hot Post Monitor - Email Test")
    print("=" * 50)
    
    success = test_gmail_connection()
    
    if success:
        print("\n🎉 Email system is ready!")
        print("You can now run the monitoring system:")
        print("  python3 monitor_hot_posts.py once")
        print("  python3 monitor_hot_posts.py continuous --interval 30")
    else:
        print("\n❌ Email system needs configuration.")
        print("Please check the error messages above and fix the configuration.")


if __name__ == "__main__":
    main()


