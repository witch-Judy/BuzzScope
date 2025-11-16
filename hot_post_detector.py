"""
Hot Post Detector
独立的热门帖子检测器，不依赖Streamlit
"""

import os
import json
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

class HotPostDetector:
    """热门帖子检测器"""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
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
            print(f"Error fetching Hacker News posts: {e}")
            return []
    
    def get_reddit_posts(self, keyword: str, hours_back: int = 24) -> List[Dict]:
        """获取Reddit最近的热门帖子"""
        try:
            # 使用Reddit JSON API - 固定获取一天内的热门帖子
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
            print(f"Error fetching Reddit posts: {e}")
            return []
    
    def get_youtube_videos(self, keyword: str, hours_back: int = 24) -> List[Dict]:
        """获取YouTube最近的热门视频"""
        try:
            api_key = os.getenv('YOUTUBE_API_KEY')
            if not api_key or api_key == 'your_youtube_api_key_here':
                print("    ⚠️ YouTube API key not configured - skipping YouTube")
                return []
            
            # Check if API key is valid format
            if not api_key.startswith('AIza') or len(api_key) != 39:
                print("    ⚠️ YouTube API key format invalid - skipping YouTube")
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
            print(f"Error fetching YouTube videos: {e}")
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
    
    def send_email_notification(self, hot_posts: List[Dict], keywords: List[str] = None) -> bool:
        """发送邮件通知"""
        if not hot_posts:
            return False
        
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
            print(f"Error sending email: {e}")
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
