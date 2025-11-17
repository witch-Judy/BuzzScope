"""
Hot Post Monitor App - Port 8503
独立的热门帖子监控和邮件通知系统
"""

import streamlit as st
import os
import json
import time
import smtplib
import pandas as pd
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from collections import Counter
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="BuzzScope Hot Post Monitor",
    page_icon="🔥",
    layout="wide"
)

class HotPostDetector:
    """热门帖子检测器"""
    
    def __init__(self):
        # Get password and remove spaces (Gmail app passwords may have spaces)
        password = os.getenv('EMAIL_PASSWORD', '')
        if password:
            password = password.replace(' ', '')  # Remove spaces from app password
        
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': password,
            'from_email': os.getenv('FROM_EMAIL'),
            'to_email': os.getenv('TO_EMAIL')
        }
    
    def get_hackernews_posts(self, keyword: str, hours_back: int = 24) -> List[Dict]:
        """获取Hacker News最近的热门帖子"""
        try:
            # 使用Hacker News API获取最新帖子
            response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json')
            if response.status_code != 200:
                return []
            
            story_ids = response.json()[:100]  # 获取前100个热门帖子
            
            posts = []
            for story_id in story_ids:
                try:
                    story_response = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json')
                    if story_response.status_code == 200:
                        story = story_response.json()
                        
                        # 检查是否包含关键词（精准匹配）
                        title = story.get('title', '').lower()
                        text = story.get('text', '').lower() if story.get('text') else ''
                        keyword_lower = keyword.lower()
                        
                        # 使用正则表达式进行精准匹配
                        import re
                        keyword_pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                        
                        if re.search(keyword_pattern, title) or re.search(keyword_pattern, text):
                            # 检查时间（最近24小时）
                            story_time = datetime.fromtimestamp(story.get('time', 0))
                            if story_time >= datetime.now() - timedelta(hours=24):
                                posts.append({
                                    'platform': 'hackernews',
                                    'title': story.get('title', ''),
                                    'url': story.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                                    'author': story.get('by', ''),
                                    'score': story.get('score', 0),
                                    'comments': story.get('descendants', 0),
                                    'timestamp': story_time.isoformat(),
                                    'keyword': keyword,
                                    'heat_score': self._calculate_heat_score(story, 'hackernews')
                                })
                except Exception as e:
                    continue
            
            return posts
        except Exception as e:
            st.error(f"Error fetching Hacker News posts: {e}")
            return []
    
    def get_reddit_posts(self, keyword: str, hours_back: int = 24) -> List[Dict]:
        """获取Reddit最近的热门帖子"""
        try:
            # 使用Reddit JSON API
            url = f"https://www.reddit.com/search.json?q={keyword}&sort=hot&limit=100&t=day"
            headers = {'User-Agent': 'BuzzScope Hot Post Monitor 1.0'}
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return []
            
            data = response.json()
            posts = []
            
            for post_data in data.get('data', {}).get('children', []):
                post = post_data.get('data', {})
                
                # 检查是否包含关键词（精准匹配）
                title = post.get('title', '').lower()
                selftext = post.get('selftext', '').lower() if post.get('selftext') else ''
                keyword_lower = keyword.lower()
                
                # 使用正则表达式进行精准匹配
                import re
                keyword_pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                
                if re.search(keyword_pattern, title) or re.search(keyword_pattern, selftext):
                    # 检查时间（最近24小时）
                    post_time = datetime.fromtimestamp(post.get('created_utc', 0))
                    if post_time >= datetime.now() - timedelta(hours=24):
                        posts.append({
                            'platform': 'reddit',
                            'title': post.get('title', ''),
                            'url': f"https://reddit.com{post.get('permalink', '')}",
                            'author': post.get('author', ''),
                            'score': post.get('score', 0),
                            'comments': post.get('num_comments', 0),
                            'timestamp': post_time.isoformat(),
                            'keyword': keyword,
                            'heat_score': self._calculate_heat_score(post, 'reddit')
                        })
            
            return posts
        except Exception as e:
            st.error(f"Error fetching Reddit posts: {e}")
            return []
    
    def get_youtube_videos(self, keyword: str, hours_back: int = 24) -> List[Dict]:
        """获取YouTube最近的热门视频"""
        try:
            api_key = os.getenv('YOUTUBE_API_KEY')
            if not api_key:
                st.warning("YouTube API key not configured")
                return []
            
            # 使用YouTube Data API v3
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'q': keyword,
                'type': 'video',
                'order': 'relevance',
                'maxResults': 50,
                'publishedAfter': (datetime.now() - timedelta(hours=24)).isoformat() + 'Z',
                'key': api_key
            }
            
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return []
            
            data = response.json()
            posts = []
            
            for item in data.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                
                # 获取视频统计信息
                stats_url = "https://www.googleapis.com/youtube/v3/videos"
                stats_params = {
                    'part': 'statistics',
                    'id': video_id,
                    'key': api_key
                }
                
                stats_response = requests.get(stats_url, params=stats_params)
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    if stats_data.get('items'):
                        stats = stats_data['items'][0]['statistics']
                        
                        posts.append({
                            'platform': 'youtube',
                            'title': snippet.get('title', ''),
                            'url': f"https://youtube.com/watch?v={video_id}",
                            'author': snippet.get('channelTitle', ''),
                            'score': int(stats.get('likeCount', 0)),
                            'comments': int(stats.get('commentCount', 0)),
                            'views': int(stats.get('viewCount', 0)),
                            'timestamp': snippet.get('publishedAt', ''),
                            'keyword': keyword,
                            'heat_score': self._calculate_heat_score(stats, 'youtube')
                        })
            
            return posts
        except Exception as e:
            st.error(f"Error fetching YouTube videos: {e}")
            return []
    
    def _calculate_heat_score(self, post: Dict, platform: str) -> float:
        """计算热度分数"""
        if platform == 'hackernews':
            score = post.get('score', 0)
            comments = post.get('descendants', 0)
            return score + comments * 2
        
        elif platform == 'reddit':
            score = post.get('score', 0)
            comments = post.get('num_comments', 0)
            return score + comments * 1.5
        
        elif platform == 'youtube':
            views = int(post.get('viewCount', 0))
            likes = int(post.get('likeCount', 0))
            comments = int(post.get('commentCount', 0))
            return views / 100 + likes + comments * 2
        
        return 0
    
    def is_hot_post(self, post: Dict, platform: str) -> bool:
        """判断是否为热门帖子"""
        heat_score = post.get('heat_score', 0)
        
        if platform == 'hackernews':
            return (heat_score > 150 or 
                   post.get('score', 0) > 100 or 
                   post.get('comments', 0) > 50)
        
        elif platform == 'reddit':
            return (heat_score > 1000 or 
                   post.get('score', 0) > 500 or 
                   post.get('comments', 0) > 100)
        
        elif platform == 'youtube':
            return (heat_score > 100 or 
                   post.get('views', 0) > 1000 or 
                   post.get('score', 0) > 100 or 
                   post.get('comments', 0) > 10)
        
        return False
    
    def send_email_notification(self, hot_posts: List[Dict], keywords: List[str] = None):
        """发送邮件通知"""
        if not hot_posts:
            return
        
        # Sort hot posts by heat score (highest first)
        hot_posts_sorted = sorted(hot_posts, key=lambda x: x['heat_score'], reverse=True)
        
        # Create personalized subject with keywords
        if keywords:
            keywords_str = ", ".join(keywords)
            subject = f"🔥 Hot Posts for {keywords_str}!"
        else:
            subject = f"🔥 {len(hot_posts_sorted)} Hot Posts Detected!"
        
        html_content = self._create_email_html(hot_posts_sorted, keywords)
        text_content = self._create_email_text(hot_posts_sorted, keywords)
        
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
            return True
        except Exception as e:
            st.error(f"Error sending email: {e}")
            return False
    
    
    def _create_email_html(self, hot_posts: List[Dict], keywords: List[str] = None) -> str:
        """创建HTML邮件内容"""
        # Get unique platforms from hot posts
        platforms = list(set([post['platform'] for post in hot_posts]))
        platforms_str = ", ".join(platforms)
        
        # Create keywords display
        keywords_display = ""
        if keywords:
            keywords_str = ", ".join(keywords)
            keywords_display = f"<p><strong>Keywords monitored:</strong> {keywords_str}</p>"
        
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
                <p>Detected {len(hot_posts)} trending posts across {platforms_str} platforms.</p>
                {keywords_display}
            </div>
        """
        
        for post in hot_posts:
            html += f"""
            <div class="post">
                <div class="platform">{post['platform'].upper()}</div>
                <div class="title">
                    <a href="{post['url']}" target="_blank">{post['title']}</a>
                </div>
                <div class="metrics">
                    <span class="heat-score">Heat: {post['heat_score']:.1f}</span>
                    | Score: {post['score']} | Comments: {post['comments']} | Author: {post['author']}
                    <br>Keyword: {post['keyword']} | Time: {post['timestamp'][:19]}
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _create_email_text(self, hot_posts: List[Dict], keywords: List[str] = None) -> str:
        """创建文本邮件内容"""
        # Get unique platforms from hot posts
        platforms = list(set([post['platform'] for post in hot_posts]))
        platforms_str = ", ".join(platforms)
        
        text = f"🔥 HOT POSTS ALERT!\n\n"
        text += f"Detected {len(hot_posts)} trending posts across {platforms_str} platforms.\n"
        
        # Add keywords information
        if keywords:
            keywords_str = ", ".join(keywords)
            text += f"Keywords monitored: {keywords_str}\n"
        
        text += "\n"
        
        for post in hot_posts:
            text += f"Platform: {post['platform'].upper()}\n"
            text += f"Title: {post['title']}\n"
            text += f"URL: {post['url']}\n"
            text += f"Score: {post['score']} | Comments: {post['comments']} | Heat: {post['heat_score']:.1f}\n"
            text += f"Author: {post['author']} | Keyword: {post['keyword']}\n"
            text += f"Time: {post['timestamp'][:19]}\n"
            text += "-" * 50 + "\n\n"
        
        return text

def main():
    st.title("🔥 BuzzScope Hot Post Monitor")
    st.markdown("**Port 8503 - Real-time Hot Post Detection & Email Notifications**")
    
    # Initialize detector
    detector = HotPostDetector()
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Keywords to monitor
    keywords_input = st.sidebar.text_input(
        "Keywords to monitor (comma-separated):",
        value="ai, iot, mqtt, unified_namespace",
        help="Enter keywords separated by commas"
    )
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
    
    # Platforms to monitor
    platforms = st.sidebar.multiselect(
        "Platforms to monitor:",
        ["hackernews", "reddit", "youtube"],
        default=["hackernews", "reddit", "youtube"]
    )
    
    # Email configuration status
    st.sidebar.subheader("📧 Email Status")
    if detector.email_config['username'] and detector.email_config['password']:
        st.sidebar.success("✅ Email configured")
        st.sidebar.write(f"To: {detector.email_config['to_email']}")
    else:
        st.sidebar.error("❌ Email not configured")
        st.sidebar.write("Please set EMAIL_USERNAME and EMAIL_PASSWORD in .env")
    
    # Main content - Single column layout
    st.header("🔍 Hot Post Detection")
    
    # Large, prominent detection button
    if st.button("🚀 RUN HOT POST DETECTION & SEND EMAIL", type="primary", use_container_width=True):
        if not keywords:
            st.error("Please enter at least one keyword")
            return
        
        if not platforms:
            st.error("Please select at least one platform")
            return
        
        # Check email configuration
        if not detector.email_config['username'] or not detector.email_config['password']:
            st.error("❌ Email not configured. Please set EMAIL_USERNAME and EMAIL_PASSWORD in .env")
            return
        
        st.info(f"🔍 Checking {len(platforms)} platforms for {len(keywords)} keywords...")
        
        all_hot_posts = []
        
        # Progress bar
        progress_bar = st.progress(0)
        total_checks = len(keywords) * len(platforms)
        current_check = 0
        
        for keyword in keywords:
            st.write(f"**Checking keyword: {keyword}**")
            
            for platform in platforms:
                current_check += 1
                progress_bar.progress(current_check / total_checks)
                
                st.write(f"  📡 Fetching {platform} posts...")
                
                # Get posts based on platform (hardcoded to 24 hours)
                if platform == 'hackernews':
                    posts = detector.get_hackernews_posts(keyword, 24)
                elif platform == 'reddit':
                    posts = detector.get_reddit_posts(keyword, 24)
                elif platform == 'youtube':
                    posts = detector.get_youtube_videos(keyword, 24)
                else:
                    posts = []
                
                # Filter hot posts
                hot_posts = [post for post in posts if detector.is_hot_post(post, platform)]
                
                if hot_posts:
                    st.write(f"  🔥 Found {len(hot_posts)} hot posts!")
                    all_hot_posts.extend(hot_posts)
                else:
                    st.write(f"  ✅ No hot posts found")
        
        progress_bar.progress(1.0)
        
        # Display results and automatically send email
        if all_hot_posts:
            st.success(f"🎉 Found {len(all_hot_posts)} hot posts total!")
            
            # Automatically send email notification
            st.info("📧 Sending email notification...")
            if detector.send_email_notification(all_hot_posts, keywords):
                st.success("✅ Email notification sent successfully!")
                st.write(f"📬 Check your inbox at: {detector.email_config['to_email']}")
                
            else:
                st.error("❌ Failed to send email notification")
            
            # Sort hot posts by heat score (highest first)
            all_hot_posts.sort(key=lambda x: x['heat_score'], reverse=True)
            
            
            # Display hot posts (simplified)
            st.subheader("🔥 Hot Posts Found (Sorted by Heat Score)")
            for i, post in enumerate(all_hot_posts, 1):
                with st.expander(f"{i}. {post['title'][:60]}... (Heat: {post['heat_score']:.1f})"):
                    st.write(f"**Platform:** {post['platform'].upper()}")
                    st.write(f"**Title:** {post['title']}")
                    st.write(f"**URL:** {post['url']}")
                    st.write(f"**Heat Score:** {post['heat_score']:.1f}")
                    st.write(f"**Score:** {post['score']} | **Comments:** {post['comments']}")
                    st.write(f"**Keyword:** {post['keyword']}")
        else:
            st.info("ℹ️ No hot posts found in the last 24 hours")
            st.write("📧 No email sent (no hot posts to report)")
    
    # Simple status section
    st.markdown("---")
    st.subheader("📊 Current Configuration")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"**Keywords:** {', '.join(keywords)}")
    with col2:
        st.write(f"**Platforms:** {', '.join(platforms)}")
    with col3:
        st.write(f"**Email:** {detector.email_config['to_email']}")
    
    # Quick test email button
    if st.button("🧪 Test Email System", use_container_width=True):
        test_posts = [{
            'platform': 'test',
            'title': 'Test Hot Post - Email System Working',
            'url': 'https://example.com',
            'author': 'TestUser',
            'score': 999,
            'comments': 99,
            'timestamp': datetime.now().isoformat(),
            'keyword': 'test',
            'heat_score': 999.9
        }]
        
        if detector.send_email_notification(test_posts):
            st.success("✅ Test email sent!")
        else:
            st.error("❌ Failed to send test email")

if __name__ == "__main__":
    main()
