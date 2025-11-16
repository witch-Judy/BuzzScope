"""
Historical Data Analysis Service V2
专门用于分析历史数据的声量统计、趋势分析和横向对比
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import os
from dataclasses import dataclass

@dataclass
class PlatformMetrics:
    """平台指标数据类"""
    platform: str
    keyword: str
    total_posts: int
    total_interactions: int
    unique_authors: int
    date_range: Tuple[datetime, datetime]
    top_contributors: List[Dict[str, Any]]
    top_posts: List[Dict[str, Any]]
    daily_mentions: Dict[str, int]
    weekly_mentions: Dict[str, int]

@dataclass
class ComparisonMetrics:
    """对比指标数据类"""
    keywords: List[str]
    platform_totals: Dict[str, Dict[str, int]]
    cross_platform_insights: List[str]
    top_keywords: List[Tuple[str, int]]

class HistoricalAnalysisV2:
    """历史数据分析服务V2"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self.platforms = ["hackernews", "reddit", "youtube", "discord"]
        self.default_keywords = ["ai", "iot", "mqtt", "unified_namespace"]
    
    def load_platform_data(self, platform: str, keyword: str) -> Dict[str, Any]:
        """加载平台数据"""
        file_path = os.path.join(self.cache_dir, platform, f"{keyword}.json")
        if not os.path.exists(file_path):
            return {"status": "error", "posts": []}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {"status": "error", "posts": []}
    
    def calculate_platform_metrics(self, platform: str, keyword: str) -> PlatformMetrics:
        """计算单个平台的指标"""
        data = self.load_platform_data(platform, keyword)
        posts = data.get("posts", [])
        
        if not posts:
            return PlatformMetrics(
                platform=platform,
                keyword=keyword,
                total_posts=0,
                total_interactions=0,
                unique_authors=0,
                date_range=(datetime.now(), datetime.now()),
                top_contributors=[],
                top_posts=[],
                daily_mentions={},
                weekly_mentions={}
            )
        
        # 计算基础指标
        total_posts = len(posts)
        total_interactions = sum(self._get_interaction_count(post) for post in posts)
        unique_authors = len(set(self._get_author(post) for post in posts if self._get_author(post)))
        
        # 计算时间范围
        dates = [self._parse_date(post.get('created_at', '')) for post in posts]
        dates = [d for d in dates if d is not None]
        date_range = (min(dates), max(dates)) if dates else (datetime.now(), datetime.now())
        
        # 计算Top贡献者
        author_counts = Counter(self._get_author(post) for post in posts if self._get_author(post))
        top_contributors = [
            {
                "author": author,
                "post_count": count,
                "platform": platform,
                "profile_url": self._get_author_url(platform, author)
            }
            for author, count in author_counts.most_common(10)
        ]
        
        # 计算Top帖子
        top_posts = sorted(posts, key=lambda x: self._get_interaction_count(x), reverse=True)[:10]
        top_posts = [
            {
                "title": post.get('title', 'No title'),
                "interactions": self._get_interaction_count(post),
                "author": self._get_author(post),
                "created_at": post.get('created_at', ''),
                "url": self._get_post_url(platform, post),
                "platform": platform
            }
            for post in top_posts
        ]
        
        # 计算每日提及
        daily_mentions = self._calculate_daily_mentions(posts)
        
        # 计算每周提及
        weekly_mentions = self._calculate_weekly_mentions(posts)
        
        return PlatformMetrics(
            platform=platform,
            keyword=keyword,
            total_posts=total_posts,
            total_interactions=total_interactions,
            unique_authors=unique_authors,
            date_range=date_range,
            top_contributors=top_contributors,
            top_posts=top_posts,
            daily_mentions=daily_mentions,
            weekly_mentions=weekly_mentions
        )
    
    def analyze_keyword(self, keyword: str) -> Dict[str, PlatformMetrics]:
        """分析单个关键词在所有平台的指标"""
        results = {}
        for platform in self.platforms:
            results[platform] = self.calculate_platform_metrics(platform, keyword)
        return results
    
    def compare_keywords(self, keywords: Optional[List[str]] = None) -> ComparisonMetrics:
        """对比多个关键词"""
        if keywords is None:
            keywords = self.default_keywords
        
        platform_totals = {}
        all_metrics = {}
        
        # 收集所有关键词的指标
        for keyword in keywords:
            all_metrics[keyword] = self.analyze_keyword(keyword)
        
        # 计算平台总计
        for platform in self.platforms:
            platform_totals[platform] = {
                "total_posts": sum(metrics[platform].total_posts for metrics in all_metrics.values()),
                "total_interactions": sum(metrics[platform].total_interactions for metrics in all_metrics.values()),
                "unique_authors": len(set(
                    author["author"] 
                    for metrics in all_metrics.values() 
                    for author in metrics[platform].top_contributors
                ))
            }
        
        # 计算关键词排名
        keyword_totals = {}
        for keyword in keywords:
            keyword_totals[keyword] = sum(
                all_metrics[keyword][platform].total_posts 
                for platform in self.platforms
            )
        
        top_keywords = sorted(keyword_totals.items(), key=lambda x: x[1], reverse=True)
        
        # 生成跨平台洞察
        cross_platform_insights = self._generate_insights(all_metrics, platform_totals)
        
        return ComparisonMetrics(
            keywords=keywords,
            platform_totals=platform_totals,
            cross_platform_insights=cross_platform_insights,
            top_keywords=top_keywords
        )
    
    def _get_interaction_count(self, post: Dict[str, Any]) -> int:
        """获取帖子的互动数"""
        platform = post.get('platform', '')
        
        if platform == 'reddit':
            return post.get('score', 0) + post.get('num_comments', 0)
        elif platform == 'youtube':
            return (post.get('view_count', 0) or 0) + (post.get('like_count', 0) or 0) + (post.get('comment_count', 0) or 0)
        elif platform == 'hackernews':
            return post.get('score', 0) + post.get('descendants', 0)
        elif platform == 'discord':
            return post.get('reactions', 0) or 0
        else:
            return 0
    
    def _get_author(self, post: Dict[str, Any]) -> Optional[str]:
        """获取帖子作者"""
        platform = post.get('platform', '')
        
        if platform == 'reddit':
            return post.get('author', '')
        elif platform == 'youtube':
            return post.get('channel_title', '')
        elif platform == 'hackernews':
            return post.get('by', '')
        elif platform == 'discord':
            return post.get('author', '')
        else:
            return None
    
    def _get_author_url(self, platform: str, author: str) -> str:
        """获取作者链接"""
        if platform == 'reddit':
            return f"https://reddit.com/u/{author}"
        elif platform == 'youtube':
            return f"https://youtube.com/@{author.replace(' ', '')}"
        elif platform == 'hackernews':
            return f"https://news.ycombinator.com/user?id={author}"
        elif platform == 'discord':
            return f"https://discord.com/users/{author}"
        else:
            return ""
    
    def _get_post_url(self, platform: str, post: Dict[str, Any]) -> str:
        """获取帖子链接"""
        if platform == 'reddit':
            return f"https://reddit.com{post.get('permalink', '')}"
        elif platform == 'youtube':
            return f"https://youtube.com/watch?v={post.get('video_id', '')}"
        elif platform == 'hackernews':
            return f"https://news.ycombinator.com/item?id={post.get('id', '')}"
        elif platform == 'discord':
            return post.get('jump_url', '')
        else:
            return ""
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            # 尝试多种日期格式
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d %H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.replace('Z', ''), fmt)
                except ValueError:
                    continue
            
            # 如果都失败，尝试ISO格式
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None
    
    def _calculate_daily_mentions(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算每日提及数"""
        daily_counts = defaultdict(int)
        
        for post in posts:
            date = self._parse_date(post.get('created_at', ''))
            if date:
                date_str = date.strftime('%Y-%m-%d')
                daily_counts[date_str] += 1
        
        return dict(daily_counts)
    
    def _calculate_weekly_mentions(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算每周提及数"""
        weekly_counts = defaultdict(int)
        
        for post in posts:
            date = self._parse_date(post.get('created_at', ''))
            if date:
                # 获取该周的周一
                monday = date - timedelta(days=date.weekday())
                week_str = monday.strftime('%Y-W%U')
                weekly_counts[week_str] += 1
        
        return dict(weekly_counts)
    
    def _generate_insights(self, all_metrics: Dict[str, Dict[str, PlatformMetrics]], 
                          platform_totals: Dict[str, Dict[str, int]]) -> List[str]:
        """生成跨平台洞察"""
        insights = []
        
        # 找出最活跃的平台
        most_active_platform = max(platform_totals.keys(), 
                                 key=lambda p: platform_totals[p]['total_posts'])
        insights.append(f"最活跃的平台是 {most_active_platform}，共有 {platform_totals[most_active_platform]['total_posts']} 个帖子")
        
        # 找出互动最多的平台
        most_engaging_platform = max(platform_totals.keys(),
                                   key=lambda p: platform_totals[p]['total_interactions'])
        insights.append(f"互动最多的平台是 {most_engaging_platform}，共有 {platform_totals[most_engaging_platform]['total_interactions']} 次互动")
        
        # 找出作者最多的平台
        most_diverse_platform = max(platform_totals.keys(),
                                  key=lambda p: platform_totals[p]['unique_authors'])
        insights.append(f"作者最丰富的平台是 {most_diverse_platform}，共有 {platform_totals[most_diverse_platform]['unique_authors']} 位独特作者")
        
        return insights
