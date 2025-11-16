"""
Monitoring Scheduler
Schedules and manages hot post monitoring tasks
"""

import time
import schedule
import threading
from datetime import datetime
from typing import Dict, List

from .hot_post_monitor import HotPostMonitor


class MonitoringScheduler:
    """Schedules and manages monitoring tasks"""
    
    def __init__(self, keywords: List[str], email_config: Dict):
        self.keywords = keywords
        self.email_config = email_config
        self.monitor = HotPostMonitor(keywords, email_config)
        self.running = False
        self.scheduler_thread = None
    
    def start_monitoring(self, interval_minutes: int = 30):
        """Start monitoring with specified interval"""
        print(f"Starting hot post monitoring every {interval_minutes} minutes")
        
        # Schedule the monitoring task
        schedule.every(interval_minutes).minutes.do(self._run_monitoring_task)
        
        # Start scheduler in a separate thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        print("Monitoring scheduler started successfully")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        print("Stopping hot post monitoring...")
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        print("Monitoring scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in scheduler: {e}")
                time.sleep(60)
    
    def _run_monitoring_task(self):
        """Run the monitoring task"""
        try:
            print(f"Running scheduled monitoring task at {datetime.now()}")
            self.monitor.run_monitoring_cycle()
        except Exception as e:
            print(f"Error in monitoring task: {e}")
    
    def run_once(self):
        """Run monitoring once (for testing)"""
        print("Running monitoring task once...")
        self.monitor.run_monitoring_cycle()
    
    def get_status(self) -> Dict:
        """Get monitoring status"""
        return {
            'running': self.running,
            'keywords': self.keywords,
            'next_run': str(schedule.next_run()) if schedule.jobs else None,
            'jobs_count': len(schedule.jobs)
        }


def main():
    """Main function for testing"""
    import os
    
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
    
    # Create scheduler
    scheduler = MonitoringScheduler(keywords, email_config)
    
    try:
        # Start monitoring every 30 minutes
        scheduler.start_monitoring(interval_minutes=30)
        
        # Keep running
        while True:
            time.sleep(60)
            status = scheduler.get_status()
            print(f"Status: {status}")
            
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        scheduler.stop_monitoring()


if __name__ == "__main__":
    main()
