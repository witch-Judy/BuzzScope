"""
Reddit specific analyzer
"""
import pandas as pd
from datetime import date
from typing import List, Dict, Any
from .base_analyzer import BaseAnalyzer
from ..models import KeywordMetrics

class RedditAnalyzer(BaseAnalyzer):
    """Analyzer for Reddit data"""
    
    def __init__(self):
        super().__init__("reddit")
    
    def calculate_metrics(self, df: pd.DataFrame, keyword: str, 
                         start_date: date, end_date: date) -> KeywordMetrics:
        """Calculate Reddit specific metrics"""
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
        insights.extend(self._generate_reddit_insights(df, keyword))
        
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
        """Calculate Reddit interactions (score + comments)"""
        score_sum = df.get('score', pd.Series([0] * len(df))).sum()
        comments_sum = df.get('num_comments', pd.Series([0] * len(df))).sum()
        return int(score_sum + comments_sum)
    
    def get_top_contributors(self, df: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top Reddit contributors by score and comments"""
        if df.empty:
            return []
        
        # Group by author and calculate metrics
        author_stats = df.groupby('author').agg({
            'post_id': 'count',
            'score': 'sum',
            'num_comments': 'sum'
        }).rename(columns={'post_id': 'posts'})
        
        # Calculate total engagement
        author_stats['total_engagement'] = author_stats['score'] + author_stats['num_comments']
        
        # Sort by total engagement
        top_authors = author_stats.sort_values('total_engagement', ascending=False).head(limit)
        
        contributors = []
        for author, stats in top_authors.iterrows():
            contributors.append({
                'author': author,
                'posts': int(stats['posts']),
                'total_score': int(stats['score']),
                'total_comments': int(stats['num_comments']),
                'total_engagement': int(stats['total_engagement'])
            })
        
        return contributors
    
    def get_sample_posts(self, df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample Reddit posts"""
        if df.empty:
            return []
        
        # Sort by score and get top posts
        top_posts = df.nlargest(limit, 'score')
        
        posts = []
        for _, post in top_posts.iterrows():
            posts.append({
                'post_id': post['post_id'],
                'title': post.get('title', ''),
                'content': post.get('content', '')[:200] + '...' if len(post.get('content', '')) > 200 else post.get('content', ''),
                'author': post['author'],
                'score': int(post.get('score', 0)),
                'comments': int(post.get('num_comments', 0)),
                'subreddit': post.get('subreddit', ''),
                'timestamp': post['timestamp'],
                'url': post.get('url', '')
            })
        
        return posts
    
    def _generate_reddit_insights(self, df: pd.DataFrame, keyword: str) -> List[str]:
        """Generate Reddit specific insights"""
        insights = []
        
        if df.empty:
            return insights
        
        # Subreddit distribution
        if 'subreddit' in df.columns:
            subreddit_counts = df['subreddit'].value_counts()
            if not subreddit_counts.empty:
                top_subreddit = subreddit_counts.index[0]
                insights.append(f"🏘️ Most active subreddit: r/{top_subreddit} ({subreddit_counts.iloc[0]} posts)")
        
        # High engagement posts
        high_score_posts = df[df.get('score', 0) > 100]
        if not high_score_posts.empty:
            insights.append(f"🔥 {len(high_score_posts)} posts with 100+ upvotes")
        
        # Popular discussions
        high_comment_posts = df[df.get('num_comments', 0) > 50]
        if not high_comment_posts.empty:
            insights.append(f"💬 {len(high_comment_posts)} posts with 50+ comments")
        
        # Top performing post
        if 'score' in df.columns and not df.empty:
            top_post = df.loc[df['score'].idxmax()]
            insights.append(f"🏆 Top post: {top_post.get('score', 0)} upvotes in r/{top_post.get('subreddit', 'unknown')}")
        
        return insights

