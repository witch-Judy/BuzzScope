#!/usr/bin/env python3
"""
Hot Post Monitor Service
自动化热门帖子监控服务
"""

import os
import time
import schedule
import json
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Import the independent detector
from hot_post_detector import HotPostDetector

class HotPostMonitorService:
    """热门帖子监控服务"""
    
    def __init__(self):
        self.detector = HotPostDetector()
        self.keywords = ['ai', 'iot', 'mqtt', 'unified_namespace']
        self.platforms = ['hackernews', 'reddit', 'youtube']
        self.hours_back = 24
        self.log_file = 'data/monitoring/hot_post_log.json'
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保目录存在"""
        os.makedirs('data/monitoring', exist_ok=True)
    
    def _load_log(self) -> List[Dict]:
        """加载监控日志"""
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_log(self, log_data: List[Dict]):
        """保存监控日志"""
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
    
    def run_monitoring_cycle(self):
        """运行一次监控周期"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting hot post monitoring cycle...")
        
        all_hot_posts = []
        
        for keyword in self.keywords:
            print(f"  Checking keyword: {keyword}")
            
            for platform in self.platforms:
                print(f"    Fetching {platform} posts...")
                
                # Get posts based on platform
                if platform == 'hackernews':
                    posts = self.detector.get_hackernews_posts(keyword, self.hours_back)
                elif platform == 'reddit':
                    posts = self.detector.get_reddit_posts(keyword, self.hours_back)
                elif platform == 'youtube':
                    posts = self.detector.get_youtube_videos(keyword, self.hours_back)
                else:
                    posts = []
                
                # Filter hot posts
                hot_posts = [post for post in posts if self.detector.is_hot_post(post, platform)]
                
                if hot_posts:
                    print(f"    🔥 Found {len(hot_posts)} hot posts!")
                    all_hot_posts.extend(hot_posts)
                else:
                    print(f"    ✅ No hot posts found")
        
        # Send email notification if hot posts found
        if all_hot_posts:
            print(f"🎉 Found {len(all_hot_posts)} hot posts total!")
            
            # Send email
            if self.detector.send_email_notification(all_hot_posts):
                print("✅ Email notification sent!")
                
                # Log the notification
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'hot_posts_count': len(all_hot_posts),
                    'keywords': self.keywords,
                    'platforms': self.platforms,
                    'email_sent': True
                }
                
                log_data = self._load_log()
                log_data.append(log_entry)
                self._save_log(log_data)
            else:
                print("❌ Failed to send email")
        else:
            print("ℹ️ No hot posts found in this cycle")
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring cycle completed")
    
    def start_scheduled_monitoring(self, interval_minutes: int = 30):
        """启动定时监控"""
        print(f"Starting scheduled hot post monitoring every {interval_minutes} minutes...")
        
        # Schedule the monitoring task
        schedule.every(interval_minutes).minutes.do(self.run_monitoring_cycle)
        
        print("Monitoring scheduler started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            schedule.clear()
            print("Monitoring stopped.")
    
    def run_once(self):
        """运行一次监控"""
        print("Running hot post monitoring once...")
        self.run_monitoring_cycle()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Hot Post Monitor Service')
    parser.add_argument('command', choices=['once', 'schedule'], 
                       help='Command to run')
    parser.add_argument('--interval', type=int, default=30,
                       help='Monitoring interval in minutes (for schedule mode)')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Create service
    service = HotPostMonitorService()
    
    if args.command == 'once':
        service.run_once()
    elif args.command == 'schedule':
        service.start_scheduled_monitoring(args.interval)

if __name__ == "__main__":
    main()
