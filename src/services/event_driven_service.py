"""
Event-Driven Notification Service
Monitors daily hot posts for keyword mentions and sends notifications
"""
import os
import json
import smtplib
import paho.mqtt.client as mqtt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..collectors import HackerNewsCollector, RedditCollector, YouTubeCollector
from ..config import Config
from .realtime_collection_service import RealtimeCollectionService

class EventDrivenService:
    """Service for monitoring hot posts and sending notifications"""
    
    def __init__(self, mqtt_broker: str = None, mqtt_port: int = 1883, 
                 mqtt_username: str = None, mqtt_password: str = None,
                 mqtt_use_tls: bool = False):
        self.mqtt_broker = mqtt_broker or os.getenv('MQTT_BROKER', 'localhost')
        self.mqtt_port = mqtt_port
        self.mqtt_username = mqtt_username or os.getenv('MQTT_USERNAME')
        self.mqtt_password = mqtt_password or os.getenv('MQTT_PASSWORD')
        self.mqtt_use_tls = mqtt_use_tls or os.getenv('MQTT_USE_TLS', 'false').lower() == 'true'
        self.mqtt_client = None
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL')
        
        # Initialize real-time collection service
        self.realtime_service = RealtimeCollectionService()
        
        # Track last check time
        self.last_check_file = "data/last_hot_posts_check.json"
        self.last_check_time = self._load_last_check_time()
    
    def monitor_keywords(self, keywords: List[str], exact_match: bool = True):
        """
        Monitor hot posts for keyword mentions
        
        Args:
            keywords: List of keywords to monitor
            exact_match: Whether to use exact phrase matching
        """
        print(f"🔍 Monitoring hot posts for keywords: {keywords}")
        
        # Get today's hot posts from all platforms
        hot_posts = self.realtime_service.collect_hot_posts()
        
        # Check for keyword mentions
        notifications = self.realtime_service.search_keywords_in_hot_posts(
            keywords, hot_posts, exact_match
        )
        
        # Send notifications if any mentions found
        if notifications:
            self._send_notifications(notifications)
            self._publish_mqtt_notifications(notifications)
        
        # Update last check time
        self._update_last_check_time()
        
        return notifications
    
    
    def _send_notifications(self, notifications: List[Dict]):
        """Send email notifications"""
        if not self.email_user or not self.email_password or not self.notification_email:
            print("⚠️ Email configuration not set, skipping email notifications")
            return
        
        print(f"📧 Sending email notifications for {len(notifications)} mentions...")
        
        try:
            # Create email content
            subject = f"BuzzScope Alert: {len(notifications)} keyword mentions found"
            body = self._create_email_body(notifications)
            
            # Send email
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.notification_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            print("✅ Email notification sent successfully")
            
        except Exception as e:
            print(f"❌ Failed to send email notification: {e}")
    
    def _create_email_body(self, notifications: List[Dict]) -> str:
        """Create HTML email body"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .mention { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
                .platform { font-weight: bold; color: #333; }
                .keyword { background-color: #ffffcc; padding: 2px 4px; border-radius: 3px; }
                .post-title { font-size: 16px; margin: 5px 0; }
                .post-meta { color: #666; font-size: 12px; }
                .post-url { color: #0066cc; text-decoration: none; }
            </style>
        </head>
        <body>
            <h2>🔍 BuzzScope Keyword Alert</h2>
            <p>Found <strong>{count}</strong> keyword mentions in today's hot posts:</p>
        """.format(count=len(notifications))
        
        for notification in notifications:
            post = notification['post']
            platform = notification['platform']
            keyword = notification['keyword']
            
            html += f"""
            <div class="mention">
                <div class="platform">📱 {platform.upper()}</div>
                <div class="keyword">Keyword: {keyword}</div>
                <div class="post-title">{post.get('title', 'No title')}</div>
                <div class="post-meta">
                    Author: {post.get('author', 'Unknown')} | 
                    Score: {post.get('score', 0)} | 
                    Time: {post.get('timestamp', 'Unknown')}
                </div>
                <div>
                    <a href="{post.get('url', '#')}" class="post-url">View Post</a>
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _publish_mqtt_notifications(self, notifications: List[Dict]):
        """Publish notifications to MQTT broker"""
        if not self.mqtt_broker:
            print("⚠️ MQTT broker not configured, skipping MQTT notifications")
            return
        
        print(f"📡 Publishing {len(notifications)} notifications to MQTT...")
        
        try:
            if not self.mqtt_client:
                self.mqtt_client = mqtt.Client()
                
                # Configure authentication if provided
                if self.mqtt_username and self.mqtt_password:
                    self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
                
                # Configure TLS if enabled
                if self.mqtt_use_tls:
                    self.mqtt_client.tls_set()
                
                # Connect to broker
                self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
                self.mqtt_client.loop_start()  # Start background loop
            
            for notification in notifications:
                topic = f"buzzscope/alerts/{notification['keyword']}"
                payload = json.dumps(notification, default=str)
                
                # Publish with QoS 1 for reliability
                result = self.mqtt_client.publish(topic, payload, qos=1)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"  ✅ Published to {topic}")
                else:
                    print(f"  ❌ Failed to publish to {topic}: {result.rc}")
            
            print("✅ MQTT notifications published successfully")
            
        except Exception as e:
            print(f"❌ Failed to publish MQTT notifications: {e}")
            # Reset client to force reconnection on next attempt
            if self.mqtt_client:
                self.mqtt_client.disconnect()
                self.mqtt_client = None
    
    def _load_last_check_time(self) -> datetime:
        """Load last check time from file"""
        if os.path.exists(self.last_check_file):
            try:
                with open(self.last_check_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data['last_check'])
            except:
                pass
        
        # Default to yesterday
        return datetime.now() - timedelta(days=1)
    
    def _update_last_check_time(self):
        """Update last check time"""
        os.makedirs(os.path.dirname(self.last_check_file), exist_ok=True)
        
        with open(self.last_check_file, 'w') as f:
            json.dump({
                'last_check': datetime.now().isoformat()
            }, f, indent=2)
    
    def start_monitoring(self, keywords: List[str], interval_hours: int = 6):
        """
        Start continuous monitoring
        
        Args:
            keywords: List of keywords to monitor
            interval_hours: Check interval in hours
        """
        import time
        
        print(f"🚀 Starting continuous monitoring...")
        print(f"   Keywords: {keywords}")
        print(f"   Interval: {interval_hours} hours")
        
        while True:
            try:
                notifications = self.monitor_keywords(keywords)
                if notifications:
                    print(f"📢 Found {len(notifications)} mentions!")
                else:
                    print("✅ No mentions found in current check")
                
                # Wait for next check
                time.sleep(interval_hours * 3600)
                
            except KeyboardInterrupt:
                print("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
