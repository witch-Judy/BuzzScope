"""
Hacker News Parquet Data Analyzer
专门用于分析Hacker News parquet文件的分析器
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
import re

class HackerNewsParquetAnalyzer:
    """Hacker News Parquet数据分析器"""
    
    def __init__(self, parquet_path: str = "data/Hackernews_raw/hackernews_2years.parquet"):
        self.parquet_path = parquet_path
        self.df = None
        self._load_data()
    
    def _load_data(self):
        """加载parquet数据"""
        if os.path.exists(self.parquet_path):
            print(f"Loading Hacker News data from {self.parquet_path}...")
            self.df = pd.read_parquet(self.parquet_path)
            print(f"Loaded {len(self.df):,} records")
        else:
            print(f"Parquet file not found: {self.parquet_path}")
            self.df = pd.DataFrame()
    
    def search_keyword(self, keyword: str, exact_match: bool = True) -> List[Dict[str, Any]]:
        """搜索关键词"""
        if self.df is None or self.df.empty:
            return []
        
        print(f"Searching for '{keyword}' in Hacker News data...")
        
        # 创建搜索条件
        if exact_match:
            # 精确匹配
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        else:
            # 模糊匹配
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        
        # 搜索标题和文本
        title_matches = self.df['title'].fillna('').str.contains(pattern, na=False)
        text_matches = self.df['text'].fillna('').str.contains(pattern, na=False)
        
        # 合并匹配结果
        matches = title_matches | text_matches
        
        # 获取匹配的记录
        matched_df = self.df[matches].copy()
        
        print(f"Found {len(matched_df)} matches")
        
        # 转换为字典列表
        results = []
        for _, row in matched_df.iterrows():
            result = {
                'platform': 'hackernews',
                'post_id': str(row['id']),
                'title': row['title'] if pd.notna(row['title']) else '',
                'content': row['text'] if pd.notna(row['text']) else '',
                'author': row['by'] if pd.notna(row['by']) else '',
                'score': int(row['score']) if pd.notna(row['score']) else 0,
                'descendants': int(row['descendants']) if pd.notna(row['descendants']) else 0,
                'type': row['type'] if pd.notna(row['type']) else '',
                'url': row['url'] if pd.notna(row['url']) else '',
                'created_at': row['timestamp'] if pd.notna(row['timestamp']) else '',
                'timestamp': row['timestamp'] if pd.notna(row['timestamp']) else ''
            }
            results.append(result)
        
        return results
    
    def calculate_metrics(self, keyword: str, exact_match: bool = True) -> Dict[str, Any]:
        """计算指标"""
        posts = self.search_keyword(keyword, exact_match)
        
        if not posts:
            return {
                "platform": "hackernews",
                "keyword": keyword,
                "total_posts": 0,
                "total_interactions": 0,
                "unique_authors": 0,
                "top_contributors": [],
                "top_posts": [],
                "monthly_mentions": {}
            }
        
        # 计算基础指标
        total_posts = len(posts)
        total_interactions = sum(post['score'] + post['descendants'] for post in posts)
        unique_authors = len(set(post['author'] for post in posts if post['author']))
        
        # 计算Top贡献者
        author_counts = Counter(post['author'] for post in posts if post['author'])
        top_contributors = [
            {
                "author": author,
                "post_count": count,
                "platform": "hackernews",
                "profile_url": f"https://news.ycombinator.com/user?id={author}"
            }
            for author, count in author_counts.most_common(10)
        ]
        
        # 计算Top帖子
        top_posts = sorted(posts, key=lambda x: x['score'] + x['descendants'], reverse=True)[:10]
        top_posts = [
            {
                "title": post['title'] or 'No title',
                "interactions": post['score'] + post['descendants'],
                "author": post['author'],
                "created_at": post['created_at'],
                "url": f"https://news.ycombinator.com/item?id={post['post_id']}",
                "platform": "hackernews"
            }
            for post in top_posts
        ]
        
        # 计算月度提及
        monthly_mentions = self._calculate_monthly_mentions(posts)
        
        return {
            "platform": "hackernews",
            "keyword": keyword,
            "total_posts": total_posts,
            "total_interactions": total_interactions,
            "unique_authors": unique_authors,
            "top_contributors": top_contributors,
            "top_posts": top_posts,
            "monthly_mentions": monthly_mentions
        }
    
    def _calculate_monthly_mentions(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算每月提及数"""
        monthly_counts = defaultdict(int)
        
        for post in posts:
            timestamp = post.get('timestamp', '')
            if timestamp:
                try:
                    # 解析时间戳
                    if isinstance(timestamp, str):
                        # 处理不同的时间戳格式，按优先级排序
                        if ' ' in timestamp and 'UTC' in timestamp:
                            # 格式: 2025-10-04 09:02:33 UTC (最高优先级)
                            date_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S UTC')
                        elif 'T' in timestamp:
                            # ISO格式: 2022-10-18T17:00:10+00:00
                            date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        elif ' ' in timestamp and '+' in timestamp:
                            # 格式: 2022-10-18 17:00:10+00:00
                            date_obj = datetime.fromisoformat(timestamp)
                        elif ' ' in timestamp:
                            # 格式: 2022-10-18 17:00:10
                            date_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        else:
                            # 尝试其他格式
                            date_obj = datetime.fromisoformat(timestamp)
                    else:
                        # 如果已经是datetime对象
                        date_obj = timestamp
                    
                    month_str = date_obj.strftime('%Y-%m')
                    monthly_counts[month_str] += 1
                except Exception as e:
                    print(f"Error parsing timestamp '{timestamp}': {e}")
                    pass
        
        return dict(monthly_counts)
    
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要"""
        if self.df is None or self.df.empty:
            return {"error": "No data loaded"}
        
        # 基本统计
        total_records = len(self.df)
        unique_authors = self.df['by'].nunique()
        
        # 内容类型统计
        type_counts = self.df['type'].value_counts().to_dict()
        
        # 时间范围
        if 'timestamp' in self.df.columns:
            timestamps = pd.to_datetime(self.df['timestamp'], errors='coerce')
            min_date = timestamps.min()
            max_date = timestamps.max()
        else:
            min_date = max_date = None
        
        return {
            "total_records": total_records,
            "unique_authors": unique_authors,
            "content_types": type_counts,
            "date_range": {
                "start": str(min_date) if min_date else None,
                "end": str(max_date) if max_date else None
            }
        }
