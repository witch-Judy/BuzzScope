"""
YouTube specific analyzer
"""
import pandas as pd
from datetime import date
from typing import List, Dict, Any
from .base_analyzer import BaseAnalyzer
from ..models import KeywordMetrics

class YouTubeAnalyzer(BaseAnalyzer):
    """Analyzer for YouTube data"""
    
    def __init__(self):
        super().__init__("youtube")
    
    def calculate_metrics(self, df: pd.DataFrame, keyword: str, 
                         start_date: date, end_date: date) -> KeywordMetrics:
        """Calculate YouTube specific metrics"""
        if df.empty:
            return KeywordMetrics(
                keyword=keyword,
                platform=self.platform,
                total_mentions=0,
                unique_authors=0,
                total_interactions=0,
                date_range=(start_date, end_date),
                daily_metrics=pd.DataFrame(),
                top_contributors=[],
                sample_posts=[],
                insights=[]
            )
        
        # Calculate basic metrics
        total_mentions = len(df)
        unique_authors = df['author'].nunique()
        total_interactions = self.calculate_interactions(df)
        
        # Calculate daily metrics
        daily_metrics = self.calculate_daily_metrics(df, keyword)
        
        # Get top contributors
        top_contributors = self.get_top_contributors(df)
        
        # Get sample posts
        sample_posts = self.get_sample_posts(df)
        
        # Generate insights
        insights = self.generate_trend_insights(daily_metrics, keyword)
        insights.extend(self._generate_youtube_insights(df, keyword))
        
        return KeywordMetrics(
            keyword=keyword,
            platform=self.platform,
            total_mentions=total_mentions,
            unique_authors=unique_authors,
            total_interactions=total_interactions,
            date_range=(start_date, end_date),
            daily_metrics=daily_metrics,
            top_contributors=top_contributors,
            sample_posts=sample_posts,
            insights=insights
        )
    
    def calculate_interactions(self, df: pd.DataFrame) -> int:
        """Calculate YouTube interactions (views + likes + comments)"""
        views_sum = df.get('view_count', pd.Series([0] * len(df))).sum()
        likes_sum = df.get('like_count', pd.Series([0] * len(df))).sum()
        comments_sum = df.get('comment_count', pd.Series([0] * len(df))).sum()
        return int(views_sum + likes_sum + comments_sum)
    
    def get_top_contributors(self, df: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top YouTube contributors by engagement"""
        if df.empty:
            return []
        
        # Group by author and calculate metrics
        author_stats = df.groupby('author').agg({
            'post_id': 'count',
            'view_count': 'sum',
            'like_count': 'sum',
            'comment_count': 'sum'
        }).rename(columns={'post_id': 'videos'})
        
        # Calculate total engagement
        author_stats['total_engagement'] = (
            author_stats['view_count'] + 
            author_stats['like_count'] + 
            author_stats['comment_count']
        )
        
        # Sort by total engagement
        top_authors = author_stats.sort_values('total_engagement', ascending=False).head(limit)
        
        contributors = []
        for author, stats in top_authors.iterrows():
            contributors.append({
                'author': author,
                'videos': int(stats['videos']),
                'total_views': int(stats['view_count']),
                'total_likes': int(stats['like_count']),
                'total_comments': int(stats['comment_count']),
                'total_engagement': int(stats['total_engagement'])
            })
        
        return contributors
    
    def get_sample_posts(self, df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample YouTube posts"""
        if df.empty:
            return []
        
        # Sort by view count and get top posts
        top_posts = df.nlargest(limit, 'view_count')
        
        posts = []
        for _, post in top_posts.iterrows():
            posts.append({
                'post_id': post['post_id'],
                'title': post.get('title', ''),
                'author': post['author'],
                'view_count': int(post.get('view_count', 0)),
                'like_count': int(post.get('like_count', 0)),
                'comment_count': int(post.get('comment_count', 0)),
                'timestamp': post['timestamp'],
                'url': post.get('url', '')
            })
        
        return posts
    
    def _generate_youtube_insights(self, df: pd.DataFrame, keyword: str) -> List[str]:
        """Generate YouTube specific insights"""
        insights = []
        
        if df.empty:
            return insights
        
        # High view videos
        high_view_videos = df[df.get('view_count', 0) > 10000]
        if not high_view_videos.empty:
            insights.append(f"📺 {len(high_view_videos)} videos with 10K+ views")
        
        # Popular videos
        high_like_videos = df[df.get('like_count', 0) > 1000]
        if not high_like_videos.empty:
            insights.append(f"👍 {len(high_like_videos)} videos with 1K+ likes")
        
        # Engaging content
        high_comment_videos = df[df.get('comment_count', 0) > 100]
        if not high_comment_videos.empty:
            insights.append(f"💬 {len(high_comment_videos)} videos with 100+ comments")
        
        # Top performing video
        if 'view_count' in df.columns and not df.empty:
            top_video = df.loc[df['view_count'].idxmax()]
            insights.append(f"🏆 Top video: {top_video.get('view_count', 0):,} views by {top_video['author']}")
        
        # Total reach
        total_views = df.get('view_count', pd.Series([0] * len(df))).sum()
        if total_views > 0:
            insights.append(f"📊 Total reach: {total_views:,} views across all videos")
        
        return insights

