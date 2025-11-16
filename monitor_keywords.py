#!/usr/bin/env python3
"""
Keyword Monitoring Script
Monitors hot posts for keyword mentions and sends notifications
"""
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services import EventDrivenService

def main():
    parser = argparse.ArgumentParser(description='Monitor keywords in hot posts')
    parser.add_argument('keywords', nargs='+', help='Keywords to monitor')
    parser.add_argument('--exact-match', action='store_true', 
                       help='Use exact phrase matching')
    parser.add_argument('--interval', type=int, default=6,
                       help='Check interval in hours (default: 6)')
    parser.add_argument('--once', action='store_true',
                       help='Run once instead of continuous monitoring')
    
    args = parser.parse_args()
    
    print("🔍 BuzzScope Keyword Monitor")
    print("=" * 50)
    print(f"Keywords: {args.keywords}")
    print(f"Exact match: {args.exact_match}")
    
    # Initialize service
    service = EventDrivenService()
    
    if args.once:
        # Run once
        print("\\n🔄 Running single check...")
        notifications = service.monitor_keywords(args.keywords, args.exact_match)
        
        if notifications:
            print(f"\\n📢 Found {len(notifications)} mentions!")
            for notification in notifications:
                post = notification['post']
                print(f"  - {notification['platform']}: {post.get('title', 'No title')[:60]}...")
        else:
            print("\\n✅ No mentions found")
    else:
        # Continuous monitoring
        print(f"\\n🚀 Starting continuous monitoring (interval: {args.interval}h)...")
        service.start_monitoring(args.keywords, args.interval)

if __name__ == "__main__":
    main()
