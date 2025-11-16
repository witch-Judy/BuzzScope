#!/usr/bin/env python3
"""
Hot Posts Monitor CLI
Command-line interface for managing hot post monitoring
"""

import os
import sys
import argparse
import time
from datetime import datetime

# Add src to path
sys.path.append('src')

from services.hot_post_monitor import HotPostMonitor
from services.monitoring_scheduler import MonitoringScheduler


def load_email_config():
    """Load email configuration from environment variables"""
    required_vars = [
        'EMAIL_USERNAME',
        'EMAIL_PASSWORD', 
        'FROM_EMAIL',
        'TO_EMAIL'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        sys.exit(1)
    
    return {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'username': os.getenv('EMAIL_USERNAME'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'from_email': os.getenv('FROM_EMAIL'),
        'to_email': os.getenv('TO_EMAIL')
    }


def run_once(keywords, email_config):
    """Run monitoring once"""
    print("Running hot post monitoring once...")
    monitor = HotPostMonitor(keywords, email_config)
    monitor.run_monitoring_cycle()


def run_continuous(keywords, email_config, interval_minutes):
    """Run monitoring continuously"""
    print(f"Starting continuous monitoring every {interval_minutes} minutes...")
    scheduler = MonitoringScheduler(keywords, email_config)
    
    try:
        scheduler.start_monitoring(interval_minutes)
        
        print("Monitoring started. Press Ctrl+C to stop.")
        while True:
            time.sleep(60)
            status = scheduler.get_status()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {status['jobs_count']} jobs scheduled")
            
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        scheduler.stop_monitoring()
        print("Monitoring stopped.")


def test_email(keywords, email_config):
    """Test email functionality"""
    print("Testing email functionality...")
    
    # Create a test hot post
    from services.hot_post_monitor import HotPost
    
    test_post = HotPost(
        platform='test',
        title='Test Hot Post - This is a test notification',
        url='https://example.com',
        author='TestUser',
        score=999,
        comments=99,
        timestamp=datetime.now(),
        keyword='test',
        heat_score=999.9
    )
    
    monitor = HotPostMonitor(keywords, email_config)
    monitor._send_email([test_post])
    print("Test email sent!")


def main():
    parser = argparse.ArgumentParser(description='Hot Posts Monitor')
    parser.add_argument('command', choices=['once', 'continuous', 'test-email'], 
                       help='Command to run')
    parser.add_argument('--keywords', nargs='+', 
                       default=['ai', 'iot', 'mqtt', 'unified_namespace'],
                       help='Keywords to monitor')
    parser.add_argument('--interval', type=int, default=30,
                       help='Monitoring interval in minutes (for continuous mode)')
    
    args = parser.parse_args()
    
    # Load email configuration
    email_config = load_email_config()
    
    print(f"Monitoring keywords: {', '.join(args.keywords)}")
    print(f"Email notifications to: {email_config['to_email']}")
    
    if args.command == 'once':
        run_once(args.keywords, email_config)
    elif args.command == 'continuous':
        run_continuous(args.keywords, email_config, args.interval)
    elif args.command == 'test-email':
        test_email(args.keywords, email_config)


if __name__ == "__main__":
    main()


