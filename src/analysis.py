"""
Analysis engine for BuzzScope keyword tracking
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
import logging
from .models import KeywordMetrics, ComparisonMetrics
from .storage import BuzzScopeStorage
from .config import Config

logger = logging.getLogger(__name__)

class BuzzScopeAnalyzer:
    """Main analysis engine for keyword tracking"""
    
    def __init__(self, storage: Optional[BuzzScopeStorage] = None):
        self.storage = storage or BuzzScopeStorage()
        self.config = Config.ANALYSIS
    
    def analyze_keyword(self, keyword: str, platforms: Optional[List[str]] = None,
                       days_back: int = 30, exact_match: bool = False) -> Dict[str, KeywordMetrics]:
        """
        Analyze keyword across platforms
        
        Args:
            keyword: Keyword to analyze
            platforms: List of platforms to analyze (defaults to all)
            days_back: Number of days to look back
            exact_match: If True, use exact phrase matching. If False, use substring matching.
            
        Returns:
            Dictionary mapping platform names to KeywordMetrics
        """
        if platforms is None:
            platforms = list(Config.PLATFORMS.keys())
        
        results = {}
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        for platform in platforms:
            try:
                # Load posts for the platform
                df = self.storage.load_posts(platform, start_date, end_date)
                
                if df.empty:
                    logger.warning(f"No data found for platform {platform}")
                    continue
                
                # Filter posts containing the keyword
                keyword_posts = self._filter_keyword_posts(df, keyword)
                
                if keyword_posts.empty:
                    logger.info(f"No posts found for keyword '{keyword}' in {platform}")
                    continue
                
                # Calculate metrics
                metrics = self._calculate_platform_metrics(
                    keyword_posts, keyword, platform, start_date, end_date
                )
                
                results[platform] = metrics
                
            except Exception as e:
                logger.error(f"Error analyzing {platform} for '{keyword}': {e}")
                continue
        
        return results
    
    def compare_keywords(self, keywords: List[str], platform: str,
                        days_back: int = 30) -> ComparisonMetrics:
        """
        Compare multiple keywords on a single platform
        
        Args:
            keywords: List of keywords to compare
            platform: Platform to analyze
            days_back: Number of days to look back
            
        Returns:
            ComparisonMetrics object
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        # Load platform data
        df = self.storage.load_posts(platform, start_date, end_date)
        
        if df.empty:
            logger.warning(f"No data found for platform {platform}")
            return ComparisonMetrics(
                keywords=keywords,
                platform=platform,
                comparison_data=pd.DataFrame(),
                date_range=(start_date, end_date)
            )
        
        # Create comparison data
        comparison_data = []
        
        for keyword in keywords:
            keyword_posts = self._filter_keyword_posts(df, keyword)
            
            if keyword_posts.empty:
                continue
            
            # Calculate daily metrics
            daily_metrics = self._calculate_daily_metrics(keyword_posts, keyword)
            comparison_data.append(daily_metrics)
        
        if not comparison_data:
            return ComparisonMetrics(
                keywords=keywords,
                platform=platform,
                comparison_data=pd.DataFrame(),
                date_range=(start_date, end_date)
            )
        
        # Combine comparison data
        combined_df = pd.concat(comparison_data, ignore_index=True)
        
        # Generate insights
        insights = self._generate_comparison_insights(combined_df, keywords)
        
        return ComparisonMetrics(
            keywords=keywords,
            platform=platform,
            comparison_data=combined_df,
            date_range=(start_date, end_date),
            insights=insights
        )
    
    def get_trend_analysis(self, keyword: str, platform: str,
                          days_back: int = 30) -> Dict[str, Any]:
        """
        Get detailed trend analysis for a keyword
        
        Args:
            keyword: Keyword to analyze
            platform: Platform to analyze
            days_back: Number of days to look back
            
        Returns:
            Dictionary with trend analysis results
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        # Load and filter data
        df = self.storage.load_posts(platform, start_date, end_date)
        keyword_posts = self._filter_keyword_posts(df, keyword)
        
        if keyword_posts.empty:
            return {
                'keyword': keyword,
                'platform': platform,
                'trend_data': pd.DataFrame(),
                'insights': ['No data found for this keyword']
            }
        
        # Calculate trend metrics
        daily_metrics = self._calculate_daily_metrics(keyword_posts, keyword)
        
        # Calculate moving averages
        window = self.config['moving_average_window']
        daily_metrics['moving_avg_mentions'] = daily_metrics['mentions'].rolling(
            window=window, min_periods=1
        ).mean()
        
        # Calculate growth rates
        daily_metrics['mentions_growth'] = daily_metrics['mentions'].pct_change()
        daily_metrics['interactions_growth'] = daily_metrics['interactions'].pct_change()
        
        # Generate insights
        insights = self._generate_trend_insights(daily_metrics, keyword, platform)
        
        return {
            'keyword': keyword,
            'platform': platform,
            'trend_data': daily_metrics,
            'insights': insights,
            'summary_stats': {
                'total_mentions': daily_metrics['mentions'].sum(),
                'avg_daily_mentions': daily_metrics['mentions'].mean(),
                'peak_day': daily_metrics.loc[daily_metrics['mentions'].idxmax(), 'date'],
                'peak_mentions': daily_metrics['mentions'].max(),
                'growth_rate': daily_metrics['mentions_growth'].mean()
            }
        }
    
    def get_cross_platform_insights(self, keyword: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Get insights across all platforms for a keyword
        
        Args:
            keyword: Keyword to analyze
            days_back: Number of days to look back
            
        Returns:
            Dictionary with cross-platform insights
        """
        # Analyze keyword across all platforms
        platform_metrics = self.analyze_keyword(keyword, days_back=days_back)
        
        if not platform_metrics:
            return {
                'keyword': keyword,
                'platform_summary': {},
                'insights': ['No data found for this keyword across any platform']
            }
        
        # Create platform summary
        platform_summary = {}
        total_mentions = 0
        total_authors = 0
        total_interactions = 0
        
        for platform, metrics in platform_metrics.items():
            platform_summary[platform] = {
                'mentions': metrics.total_mentions,
                'unique_authors': metrics.unique_authors,
                'interactions': metrics.total_interactions,
                'date_range': metrics.date_range
            }
            
            total_mentions += metrics.total_mentions
            total_authors += metrics.unique_authors
            total_interactions += metrics.total_interactions
        
        # Find common authors across platforms
        common_authors = self._find_common_authors(platform_metrics)
        
        # Generate insights
        insights = self._generate_cross_platform_insights(
            platform_summary, common_authors, keyword
        )
        
        return {
            'keyword': keyword,
            'platform_summary': platform_summary,
            'totals': {
                'mentions': total_mentions,
                'unique_authors': total_authors,
                'interactions': total_interactions
            },
            'common_authors': common_authors,
            'insights': insights
        }
    
    def _filter_keyword_posts(self, df: pd.DataFrame, keyword: str) -> pd.DataFrame:
        """Filter DataFrame for posts containing keyword"""
        keyword_lower = keyword.lower()
        mask = (
            df['title'].str.lower().str.contains(keyword_lower, na=False) |
            df['content'].str.lower().str.contains(keyword_lower, na=False)
        )
        return df[mask].copy()
    
    def _calculate_platform_metrics(self, df: pd.DataFrame, keyword: str,
                                   platform: str, start_date: date, end_date: date) -> KeywordMetrics:
        """Calculate metrics for a platform"""
        # Basic metrics
        total_mentions = len(df)
        unique_authors = df['author'].nunique()
        
        # Calculate total interactions based on platform
        total_interactions = self._calculate_total_interactions(df, platform)
        
        # Time series data
        time_series = self._calculate_daily_metrics(df, keyword)
        
        # Top contributors
        top_contributors = self._get_top_contributors(df, platform)
        
        # Sample posts
        sample_posts = self._get_sample_posts(df, platform)
        
        return KeywordMetrics(
            keyword=keyword,
            platform=platform,
            total_mentions=total_mentions,
            unique_authors=unique_authors,
            total_interactions=total_interactions,
            date_range=(start_date, end_date),
            time_series=time_series,
            top_contributors=top_contributors,
            sample_posts=sample_posts
        )
    
    def _calculate_total_interactions(self, df: pd.DataFrame, platform: str) -> int:
        """Calculate total interactions based on platform"""
        if platform == 'hackernews':
            return df.get('score', pd.Series([0] * len(df))).sum() + df.get('descendants', pd.Series([0] * len(df))).sum()
        elif platform == 'reddit':
            return df.get('score', pd.Series([0] * len(df))).sum() + df.get('num_comments', pd.Series([0] * len(df))).sum()
        elif platform == 'youtube':
            return df.get('view_count', pd.Series([0] * len(df))).sum() + df.get('like_count', pd.Series([0] * len(df))).sum() + df.get('comment_count', pd.Series([0] * len(df))).sum()
        elif platform == 'discord':
            # For Discord, we could count reactions if available
            return len(df)  # Simple count for now
        else:
            return len(df)
    
    def _calculate_daily_metrics(self, df: pd.DataFrame, keyword: str) -> pd.DataFrame:
        """Calculate daily metrics for time series"""
        if df.empty:
            return pd.DataFrame()
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # Group by date and calculate metrics
        daily_metrics = df.groupby('date').agg({
            'post_id': 'count',  # mentions
            'author': 'nunique',  # unique authors
        }).rename(columns={'post_id': 'mentions', 'author': 'unique_authors'})
        
        # Add interactions
        daily_metrics['interactions'] = self._calculate_daily_interactions(df)
        
        # Reset index to make date a column
        daily_metrics = daily_metrics.reset_index()
        
        return daily_metrics
    
    def _calculate_daily_interactions(self, df: pd.DataFrame) -> pd.Series:
        """Calculate daily interactions"""
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # This is a simplified version - in practice, you'd sum platform-specific interaction columns
        return df.groupby('date').size()
    
    def _get_top_contributors(self, df: pd.DataFrame, platform: str) -> List[Dict[str, Any]]:
        """Get top contributors for a platform"""
        limit = self.config['top_contributors_limit']
        
        # Count posts per author
        author_counts = df['author'].value_counts().head(limit)
        
        contributors = []
        for author, count in author_counts.items():
            contributors.append({
                'author': author,
                'post_count': count,
                'platform': platform
            })
        
        return contributors
    
    def _get_sample_posts(self, df: pd.DataFrame, platform: str) -> List[Dict[str, Any]]:
        """Get sample posts for display"""
        limit = self.config['sample_posts_limit']
        
        # Get most recent posts
        sample_df = df.nlargest(limit, 'timestamp')
        
        posts = []
        for _, row in sample_df.iterrows():
            posts.append({
                'post_id': row['post_id'],
                'title': row['title'],
                'content': row['content'][:200] + '...' if len(row['content']) > 200 else row['content'],
                'author': row['author'],
                'timestamp': row['timestamp'],
                'url': row.get('url', ''),
                'platform': platform
            })
        
        return posts
    
    def _find_common_authors(self, platform_metrics: Dict[str, KeywordMetrics]) -> Dict[str, List[str]]:
        """Find authors who appear across multiple platforms"""
        author_platforms = {}
        
        for platform, metrics in platform_metrics.items():
            if metrics.top_contributors:
                for contributor in metrics.top_contributors:
                    author = contributor['author']
                    if author not in author_platforms:
                        author_platforms[author] = []
                    author_platforms[author].append(platform)
        
        # Find authors on multiple platforms
        common_authors = {
            author: platforms for author, platforms in author_platforms.items()
            if len(platforms) > 1
        }
        
        return common_authors
    
    def _generate_trend_insights(self, daily_metrics: pd.DataFrame, keyword: str, platform: str) -> List[str]:
        """Generate insights from trend data"""
        insights = []
        
        if daily_metrics.empty:
            return insights
        
        # Growth trend
        recent_avg = daily_metrics['mentions'].tail(7).mean()
        earlier_avg = daily_metrics['mentions'].head(7).mean()
        
        if recent_avg > earlier_avg * 1.2:
            insights.append(f"📈 Growing trend: {keyword} mentions increased by {((recent_avg/earlier_avg-1)*100):.1f}% recently")
        elif recent_avg < earlier_avg * 0.8:
            insights.append(f"📉 Declining trend: {keyword} mentions decreased by {((1-recent_avg/earlier_avg)*100):.1f}% recently")
        
        # Peak activity
        peak_day = daily_metrics.loc[daily_metrics['mentions'].idxmax()]
        insights.append(f"🔥 Peak activity: {peak_day['mentions']} mentions on {peak_day['date']}")
        
        # Consistency
        cv = daily_metrics['mentions'].std() / daily_metrics['mentions'].mean()
        if cv < 0.3:
            insights.append("📊 Consistent activity: Low variation in daily mentions")
        elif cv > 0.8:
            insights.append("📊 Variable activity: High variation in daily mentions")
        
        return insights
    
    def _generate_comparison_insights(self, comparison_df: pd.DataFrame, keywords: List[str]) -> List[str]:
        """Generate insights from keyword comparison"""
        insights = []
        
        if comparison_df.empty:
            return insights
        
        # Find top performing keyword
        total_mentions = comparison_df.groupby('keyword')['mentions'].sum()
        top_keyword = total_mentions.idxmax()
        top_mentions = total_mentions.max()
        
        insights.append(f"🏆 Top performer: '{top_keyword}' with {top_mentions} total mentions")
        
        # Calculate relative performance
        for keyword in keywords:
            if keyword in total_mentions.index:
                mentions = total_mentions[keyword]
                percentage = (mentions / top_mentions) * 100
                insights.append(f"📊 '{keyword}': {mentions} mentions ({percentage:.1f}% of top performer)")
        
        return insights
    
    def _generate_cross_platform_insights(self, platform_summary: Dict[str, Any], 
                                        common_authors: Dict[str, List[str]], 
                                        keyword: str) -> List[str]:
        """Generate cross-platform insights"""
        insights = []
        
        # Platform dominance
        platform_mentions = {platform: data['mentions'] for platform, data in platform_summary.items()}
        top_platform = max(platform_mentions, key=platform_mentions.get)
        top_mentions = platform_mentions[top_platform]
        
        insights.append(f"🏆 Most active platform: {top_platform} with {top_mentions} mentions")
        
        # Cross-platform engagement
        if common_authors:
            insights.append(f"👥 Cross-platform users: {len(common_authors)} users active on multiple platforms")
            for author, platforms in list(common_authors.items())[:3]:  # Show top 3
                insights.append(f"   • {author}: {', '.join(platforms)}")
        
        # Platform diversity
        active_platforms = len([p for p in platform_mentions.values() if p > 0])
        insights.append(f"🌐 Platform diversity: Active on {active_platforms} platforms")
        
        return insights

