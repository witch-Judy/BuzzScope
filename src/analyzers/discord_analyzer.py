"""
Discord specific analyzer
"""
import pandas as pd
from datetime import date
from typing import List, Dict, Any
from .base_analyzer import BaseAnalyzer
from ..models import KeywordMetrics

class DiscordAnalyzer(BaseAnalyzer):
    """Analyzer for Discord data"""
    
    def __init__(self):
        super().__init__("discord")
    
    def calculate_metrics(self, df: pd.DataFrame, keyword: str, 
                         start_date: date, end_date: date) -> KeywordMetrics:
        """Calculate Discord specific metrics"""
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
        insights.extend(self._generate_discord_insights(df, keyword))
        
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
        """Calculate Discord interactions (reactions + message count)"""
        total_interactions = len(df)  # Base message count
        
        # Add reactions if available
        if 'reactions' in df.columns:
            for reactions in df['reactions']:
                if reactions and isinstance(reactions, dict):
                    total_interactions += sum(reactions.values())
        
        return total_interactions
    
    def get_top_contributors(self, df: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top Discord contributors by message count and reactions"""
        if df.empty:
            return []
        
        # Group by author and calculate metrics
        author_stats = df.groupby('author').agg({
            'post_id': 'count',
            'reactions': lambda x: self._sum_reactions(x)
        }).rename(columns={'post_id': 'messages'})
        
        # Calculate total engagement
        author_stats['total_reactions'] = author_stats['reactions']
        author_stats['total_engagement'] = author_stats['messages'] + author_stats['reactions']
        
        # Sort by total engagement
        top_authors = author_stats.sort_values('total_engagement', ascending=False).head(limit)
        
        contributors = []
        for author, stats in top_authors.iterrows():
            contributors.append({
                'author': author,
                'messages': int(stats['messages']),
                'total_reactions': int(stats['total_reactions']),
                'total_engagement': int(stats['total_engagement'])
            })
        
        return contributors
    
    def get_sample_posts(self, df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample Discord posts"""
        if df.empty:
            return []
        
        # Sort by reactions and get top posts
        df_with_reactions = df.copy()
        df_with_reactions['reaction_count'] = df_with_reactions['reactions'].apply(
            lambda x: sum(x.values()) if x and isinstance(x, dict) else 0
        )
        
        top_posts = df_with_reactions.nlargest(limit, 'reaction_count')
        
        posts = []
        for _, post in top_posts.iterrows():
            # Extract server and channel info from metadata
            server_name = post.get('metadata', {}).get('server_name', 'Unknown Server')
            channel_name = post.get('metadata', {}).get('channel_name', 'Unknown Channel')
            
            posts.append({
                'post_id': post['post_id'],
                'content': post.get('content', '')[:200] + '...' if len(post.get('content', '')) > 200 else post.get('content', ''),
                'author': post['author'],
                'reactions': post.get('reactions', {}),
                'reaction_count': post['reaction_count'],
                'timestamp': post['timestamp'],
                'server': server_name,
                'channel': channel_name
            })
        
        return posts
    
    def _sum_reactions(self, reactions_series) -> int:
        """Sum up reactions from a series of reaction dictionaries"""
        total = 0
        for reactions in reactions_series:
            if reactions and isinstance(reactions, dict):
                total += sum(reactions.values())
        return total
    
    def _generate_discord_insights(self, df: pd.DataFrame, keyword: str) -> List[str]:
        """Generate Discord specific insights"""
        insights = []
        
        if df.empty:
            return insights
        
        # Server distribution
        if 'metadata' in df.columns:
            server_counts = df['metadata'].apply(
                lambda x: x.get('server_name', 'Unknown') if isinstance(x, dict) else 'Unknown'
            ).value_counts()
            
            if not server_counts.empty:
                top_server = server_counts.index[0]
                insights.append(f"🏢 Most active server: {top_server} ({server_counts.iloc[0]} messages)")
        
        # Channel distribution
        if 'metadata' in df.columns:
            channel_counts = df['metadata'].apply(
                lambda x: x.get('channel_name', 'Unknown') if isinstance(x, dict) else 'Unknown'
            ).value_counts()
            
            if not channel_counts.empty:
                top_channel = channel_counts.index[0]
                insights.append(f"📢 Most active channel: #{top_channel} ({channel_counts.iloc[0]} messages)")
        
        # High engagement messages
        if 'reactions' in df.columns:
            high_reaction_posts = df[df['reactions'].apply(
                lambda x: sum(x.values()) if x and isinstance(x, dict) else 0
            ) > 5]
            
            if not high_reaction_posts.empty:
                insights.append(f"🔥 {len(high_reaction_posts)} messages with 5+ reactions")
        
        # Active discussion periods
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            peak_hour = df['hour'].mode().iloc[0] if not df['hour'].mode().empty else None
            if peak_hour is not None:
                insights.append(f"⏰ Peak discussion time: {peak_hour}:00")
        
        return insights

