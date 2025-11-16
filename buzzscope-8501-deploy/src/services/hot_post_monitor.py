"""
Hot Post Monitor Service
Monitors platforms for trending posts and sends email notifications
"""

import os
import json
import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..collectors.hackernews_collector import HackerNewsCollector
from ..collectors.reddit_collector import RedditCollector
from ..collectors.youtube_collector import YouTubeCollector


@dataclass
class HotPost:
    """Represents a hot post with metrics"""
    platform: str
    title: str
    url: str
    author: str
    score: int
    comments: int
    timestamp: datetime
    keyword: str
    heat_score: float


class HotPostMonitor:
    """Monitors platforms for trending posts"""
    
    def __init__(self, keywords: List[str], email_config: Dict):
        self.keywords = keywords
        self.email_config = email_config
        self.collectors = {
            'hackernews': HackerNewsCollector(),
            'reddit': RedditCollector(),
            'youtube': YouTubeCollector()
        }
        self.last_check_file = 'data/monitoring/last_check.json'
        self.hot_posts_file = 'data/monitoring/hot_posts.json'
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure monitoring directories exist"""
        os.makedirs('data/monitoring', exist_ok=True)
    
    def _load_last_check(self) -> Dict:
        """Load last check timestamp"""
        if os.path.exists(self.last_check_file):
            with open(self.last_check_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_last_check(self, timestamps: Dict):
        """Save last check timestamp"""
        with open(self.last_check_file, 'w') as f:
            json.dump(timestamps, f, default=str)
    
    def _load_hot_posts(self) -> List[Dict]:
        """Load previously detected hot posts"""
        if os.path.exists(self.hot_posts_file):
            with open(self.hot_posts_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_hot_posts(self, hot_posts: List[Dict]):
        """Save hot posts to file"""
        with open(self.hot_posts_file, 'w') as f:
            json.dump(hot_posts, f, default=str)
    
    def _calculate_heat_score(self, post: Dict, platform: str) -> float:
        """Calculate heat score for a post"""
        base_score = 0
        
        if platform == 'hackernews':
            score = post.get('score', 0)
            comments = post.get('descendants', 0)
            # HN heat score: score + comments * 2
            base_score = score + comments * 2
            
        elif platform == 'reddit':
            score = post.get('score', 0)
            comments = post.get('num_comments', 0)
            # Reddit heat score: score + comments * 1.5
            base_score = score + comments * 1.5
            
        elif platform == 'youtube':
            view_count = post.get('view_count', 0)
            like_count = post.get('like_count', 0)
            comment_count = post.get('comment_count', 0)
            # YouTube heat score: views/100 + likes + comments * 2
            base_score = view_count / 100 + like_count + comment_count * 2
        
        # Time decay factor (newer posts get higher scores)
        post_time = datetime.fromisoformat(post.get('timestamp', datetime.now().isoformat()))
        hours_old = (datetime.now() - post_time).total_seconds() / 3600
        time_factor = max(0.1, 1 - (hours_old / 24))  # Decay over 24 hours
        
        return base_score * time_factor
    
    def _is_hot_post(self, post: Dict, platform: str) -> bool:
        """Check if a post meets hot criteria"""
        heat_score = self._calculate_heat_score(post, platform)
        
        if platform == 'hackernews':
            return (heat_score > 150 or 
                   post.get('score', 0) > 100 or 
                   post.get('descendants', 0) > 50)
        
        elif platform == 'reddit':
            return (heat_score > 1000 or 
                   post.get('score', 0) > 500 or 
                   post.get('num_comments', 0) > 100)
        
        elif platform == 'youtube':
            return (heat_score > 2000 or 
                   post.get('view_count', 0) > 10000 or 
                   post.get('like_count', 0) > 1000 or 
                   post.get('comment_count', 0) > 50)
        
        return False
    
    def _get_recent_posts(self, platform: str, keyword: str, hours_back: int = 6) -> List[Dict]:
        """Get recent posts from a platform"""
        try:
            collector = self.collectors[platform]
            posts = collector.search_keyword(keyword, days_back=1)  # Get last 24 hours
            
            # Filter to last 6 hours
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_posts = []
            
            for post in posts:
                post_time = datetime.fromisoformat(post.get('timestamp', datetime.now().isoformat()))
                if post_time >= cutoff_time:
                    recent_posts.append(post)
            
            return recent_posts
        except Exception as e:
            print(f"Error getting recent posts from {platform}: {e}")
            return []
    
    def check_for_hot_posts(self) -> List[HotPost]:
        """Check all platforms for hot posts"""
        hot_posts = []
        last_check = self._load_last_check()
        
        for keyword in self.keywords:
            for platform in ['hackernews', 'reddit', 'youtube']:
                print(f"Checking {platform} for hot posts with keyword: {keyword}")
                
                recent_posts = self._get_recent_posts(platform, keyword)
                
                for post in recent_posts:
                    if self._is_hot_post(post, platform):
                        hot_post = HotPost(
                            platform=platform,
                            title=post.get('title', 'No title'),
                            url=post.get('url', ''),
                            author=post.get('author', 'Unknown'),
                            score=post.get('score', 0),
                            comments=post.get('descendants', post.get('num_comments', post.get('comment_count', 0))),
                            timestamp=datetime.fromisoformat(post.get('timestamp', datetime.now().isoformat())),
                            keyword=keyword,
                            heat_score=self._calculate_heat_score(post, platform)
                        )
                        hot_posts.append(hot_post)
        
        return hot_posts
    
    def _send_email(self, hot_posts: List[HotPost]):
        """Send email notification for hot posts"""
        if not hot_posts:
            return
        
        # Create email content
        subject = f"🔥 {len(hot_posts)} Hot Posts Detected!"
        
        html_content = self._create_email_html(hot_posts)
        text_content = self._create_email_text(hot_posts)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email_config['from_email']
        msg['To'] = self.email_config['to_email']
        
        # Add both text and HTML versions
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        try:
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            print(f"Email sent successfully for {len(hot_posts)} hot posts")
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def _create_email_html(self, hot_posts: List[HotPost]) -> str:
        """Create HTML email content"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .post {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .platform {{ font-weight: bold; color: #333; }}
                .title {{ font-size: 16px; margin: 10px 0; }}
                .metrics {{ color: #666; font-size: 14px; }}
                .heat-score {{ background-color: #ff6b6b; color: white; padding: 2px 8px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🔥 Hot Posts Alert!</h2>
                <p>Detected {len(hot_posts)} trending posts across your monitored platforms.</p>
            </div>
        """
        
        for post in hot_posts:
            html += f"""
            <div class="post">
                <div class="platform">{post.platform.upper()}</div>
                <div class="title">
                    <a href="{post.url}" target="_blank">{post.title}</a>
                </div>
                <div class="metrics">
                    <span class="heat-score">Heat: {post.heat_score:.1f}</span>
                    | Score: {post.score} | Comments: {post.comments} | Author: {post.author}
                    <br>Keyword: {post.keyword} | Time: {post.timestamp.strftime('%Y-%m-%d %H:%M')}
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _create_email_text(self, hot_posts: List[HotPost]) -> str:
        """Create text email content"""
        text = f"🔥 HOT POSTS ALERT!\n\n"
        text += f"Detected {len(hot_posts)} trending posts:\n\n"
        
        for post in hot_posts:
            text += f"Platform: {post.platform.upper()}\n"
            text += f"Title: {post.title}\n"
            text += f"URL: {post.url}\n"
            text += f"Score: {post.score} | Comments: {post.comments} | Heat: {post.heat_score:.1f}\n"
            text += f"Author: {post.author} | Keyword: {post.keyword}\n"
            text += f"Time: {post.timestamp.strftime('%Y-%m-%d %H:%M')}\n"
            text += "-" * 50 + "\n\n"
        
        return text
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        print(f"Starting monitoring cycle at {datetime.now()}")
        
        # Check for hot posts
        hot_posts = self.check_for_hot_posts()
        
        if hot_posts:
            print(f"Found {len(hot_posts)} hot posts!")
            
            # Save hot posts
            existing_posts = self._load_hot_posts()
            new_posts_data = [post.__dict__ for post in hot_posts]
            all_posts = existing_posts + new_posts_data
            self._save_hot_posts(all_posts)
            
            # Send email notification
            self._send_email(hot_posts)
        else:
            print("No hot posts found in this cycle")
        
        # Update last check time
        self._save_last_check({
            'last_check': datetime.now().isoformat(),
            'hot_posts_found': len(hot_posts)
        })
        
        print(f"Monitoring cycle completed at {datetime.now()}")


def main():
    """Main function for testing"""
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
    
    # Create monitor and run
    monitor = HotPostMonitor(keywords, email_config)
    monitor.run_monitoring_cycle()


if __name__ == "__main__":
    main()
