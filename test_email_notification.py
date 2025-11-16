#!/usr/bin/env python3
"""
Test Email Notification System
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.append('src')

from services.hot_post_monitor import HotPostMonitor, HotPost


def test_email_configuration():
    """Test email configuration and send a test email"""
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file with your email configuration.")
        print("See email_config_template.txt for reference.")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required email variables
    required_vars = [
        'EMAIL_USERNAME',
        'EMAIL_PASSWORD', 
        'FROM_EMAIL',
        'TO_EMAIL'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please add these to your .env file.")
        return False
    
    # Configuration
    keywords = ['ai', 'iot', 'mqtt', 'unified_namespace']
    
    email_config = {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'username': os.getenv('EMAIL_USERNAME'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'from_email': os.getenv('FROM_EMAIL'),
        'to_email': os.getenv('TO_EMAIL')
    }
    
    print("📧 Email Configuration:")
    print(f"   SMTP Server: {email_config['smtp_server']}:{email_config['smtp_port']}")
    print(f"   From: {email_config['from_email']}")
    print(f"   To: {email_config['to_email']}")
    print(f"   Username: {email_config['username']}")
    print(f"   Password: {'*' * len(email_config['password'])}")
    
    # Create test hot posts
    test_posts = [
        HotPost(
            platform='hackernews',
            title='🔥 Test Hot Post: AI Breakthrough in Machine Learning',
            url='https://news.ycombinator.com/item?id=123456',
            author='testuser',
            score=150,
            comments=75,
            timestamp=datetime.now(),
            keyword='ai',
            heat_score=250.5
        ),
        HotPost(
            platform='reddit',
            title='🚀 Test Hot Post: IoT Security Best Practices Discussion',
            url='https://reddit.com/r/technology/comments/test',
            author='techguru',
            score=500,
            comments=120,
            timestamp=datetime.now(),
            keyword='iot',
            heat_score=1200.0
        ),
        HotPost(
            platform='youtube',
            title='📺 Test Hot Post: MQTT Protocol Deep Dive Tutorial',
            url='https://youtube.com/watch?v=test123',
            author='TechChannel',
            score=1000,
            comments=50,
            timestamp=datetime.now(),
            keyword='mqtt',
            heat_score=2500.0
        )
    ]
    
    print(f"\n🧪 Creating test hot posts: {len(test_posts)} posts")
    
    # Create monitor and send test email
    try:
        monitor = HotPostMonitor(keywords, email_config)
        print("✅ HotPostMonitor created successfully")
        
        print("📤 Sending test email...")
        monitor._send_email(test_posts)
        print("✅ Test email sent successfully!")
        
        print(f"\n🎉 Email notification system is working!")
        print(f"Check your inbox at {email_config['to_email']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your Gmail app password")
        print("2. Ensure 2-factor authentication is enabled")
        print("3. Verify SMTP settings")
        print("4. Check firewall/network settings")
        return False


def main():
    print("🔥 BuzzScope Hot Post Monitor - Email Test")
    print("=" * 50)
    
    success = test_email_configuration()
    
    if success:
        print("\n✅ Email system is ready!")
        print("You can now run the monitoring system:")
        print("  python monitor_hot_posts.py once")
        print("  python monitor_hot_posts.py continuous --interval 30")
    else:
        print("\n❌ Email system needs configuration.")
        print("Please check the error messages above and fix the configuration.")


if __name__ == "__main__":
    main()


