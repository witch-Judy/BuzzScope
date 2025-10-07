"""
Refactored analysis engine using platform-specific analyzers
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
import logging
from .models import KeywordMetrics, ComparisonMetrics
from .storage import BuzzScopeStorage
from .config import Config
from .analyzers import PLATFORM_ANALYZERS

logger = logging.getLogger(__name__)

class BuzzScopeAnalyzerV2:
    """Refactored analysis engine using platform-specific analyzers"""
    
    def __init__(self, storage: Optional[BuzzScopeStorage] = None):
        self.storage = storage or BuzzScopeStorage()
        self.config = Config.ANALYSIS
        self.analyzers = {}
        
        # Initialize platform-specific analyzers
        for platform, analyzer_class in PLATFORM_ANALYZERS.items():
            self.analyzers[platform] = analyzer_class()
    
    def analyze_keyword(self, keyword: str, platforms: Optional[List[str]] = None,
                       days_back: int = 30, exact_match: bool = False, 
                       start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, KeywordMetrics]:
        """
        Analyze keyword across platforms using platform-specific analyzers
        
        Args:
            keyword: Keyword to analyze
            platforms: List of platforms to analyze (defaults to all)
            days_back: Number of days to look back
            exact_match: If True, use exact phrase matching. If False, use substring matching.
            start_date: Start date for analysis (overrides days_back if provided)
            end_date: End date for analysis (overrides days_back if provided)
            
        Returns:
            Dictionary mapping platform names to KeywordMetrics
        """
        if platforms is None:
            platforms = list(Config.PLATFORMS.keys())
        
        results = {}
        
        # Use provided dates or calculate from days_back
        if start_date and end_date:
            analysis_start_date = start_date
            analysis_end_date = end_date
        else:
            analysis_end_date = date.today()
            analysis_start_date = analysis_end_date - timedelta(days=days_back)
        
        for platform in platforms:
            try:
                # Get platform-specific analyzer
                analyzer = self.analyzers.get(platform)
                if not analyzer:
                    logger.warning(f"No analyzer found for platform {platform}")
                    continue
                
                # Load posts for the platform
                df = self.storage.load_posts(platform, analysis_start_date, analysis_end_date)
                
                if df.empty:
                    logger.warning(f"No data found for platform {platform}")
                    continue
                
                # Filter posts containing the keyword
                keyword_posts = self._filter_keyword_posts(df, keyword, exact_match)
                
                if keyword_posts.empty:
                    logger.info(f"No posts found for keyword '{keyword}' in {platform}")
                    continue
                
                # Use platform-specific analyzer to calculate metrics
                metrics = analyzer.calculate_metrics(
                    keyword_posts, keyword, start_date, end_date
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
        
        # Get platform-specific analyzer
        analyzer = self.analyzers.get(platform)
        if not analyzer:
            logger.warning(f"No analyzer found for platform {platform}")
            return ComparisonMetrics(
                keywords=keywords,
                platform=platform,
                comparison_data=pd.DataFrame(),
                date_range=(start_date, end_date)
            )
        
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
            keyword_posts = self._filter_keyword_posts(df, keyword, exact_match=False)
            
            if keyword_posts.empty:
                continue
            
            # Calculate daily metrics using platform-specific analyzer
            daily_metrics = analyzer.calculate_daily_metrics(keyword_posts, keyword)
            
            # Add keyword column for comparison
            if not daily_metrics.empty:
                daily_metrics['keyword'] = keyword
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
    
    def get_cross_platform_insights(self, keyword: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Get cross-platform insights for a keyword
        
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
                'total_mentions': 0,
                'platform_summary': {},
                'insights': ['No data found for this keyword across any platform']
            }
        
        # Calculate cross-platform summary
        total_mentions = sum(metrics.total_mentions for metrics in platform_metrics.values())
        total_authors = sum(metrics.unique_authors for metrics in platform_metrics.values())
        total_interactions = sum(metrics.total_interactions for metrics in platform_metrics.values())
        
        # Platform summary
        platform_summary = {}
        for platform, metrics in platform_metrics.items():
            platform_summary[platform] = {
                'mentions': metrics.total_mentions,
                'authors': metrics.unique_authors,
                'interactions': metrics.total_interactions,
                'share': (metrics.total_mentions / total_mentions * 100) if total_mentions > 0 else 0
            }
        
        # Generate insights
        insights = self._generate_cross_platform_insights(platform_summary, keyword)
        
        return {
            'keyword': keyword,
            'total_mentions': total_mentions,
            'total_authors': total_authors,
            'total_interactions': total_interactions,
            'platform_summary': platform_summary,
            'insights': insights
        }
    
    def _filter_keyword_posts(self, df: pd.DataFrame, keyword: str, exact_match: bool = False) -> pd.DataFrame:
        """Filter posts containing the keyword"""
        if df.empty:
            return df
        
        keyword_lower = keyword.lower()
        
        if exact_match:
            # Use regex for exact phrase matching
            import re
            escaped_keyword = re.escape(keyword_lower)
            pattern = r'\b' + escaped_keyword + r'\b'
            mask = (
                df['title'].str.lower().str.contains(pattern, regex=True, na=False) |
                df['content'].str.lower().str.contains(pattern, regex=True, na=False)
            )
        else:
            # Use substring matching
            mask = (
                df['title'].str.lower().str.contains(keyword_lower, na=False) |
                df['content'].str.lower().str.contains(keyword_lower, na=False)
            )
        
        return df[mask]
    
    def _generate_comparison_insights(self, combined_df: pd.DataFrame, keywords: List[str]) -> List[str]:
        """Generate comparison insights"""
        insights = []
        
        if combined_df.empty:
            return insights
        
        # Find top performing keyword
        keyword_totals = combined_df.groupby('keyword')['mentions'].sum()
        if not keyword_totals.empty:
            top_keyword = keyword_totals.idxmax()
            top_count = keyword_totals.max()
            insights.append(f"🏆 '{top_keyword}' has the most mentions ({top_count})")
        
        # Find most engaging keyword
        keyword_engagement = combined_df.groupby('keyword')['interactions'].sum()
        if not keyword_engagement.empty:
            top_engagement_keyword = keyword_engagement.idxmax()
            top_engagement = keyword_engagement.max()
            insights.append(f"🔥 '{top_engagement_keyword}' has the highest engagement ({top_engagement})")
        
        return insights
    
    def _generate_cross_platform_insights(self, platform_summary: Dict[str, Any], keyword: str) -> List[str]:
        """Generate cross-platform insights"""
        insights = []
        
        if not platform_summary:
            return insights
        
        # Find dominant platform
        platform_mentions = {platform: data['mentions'] for platform, data in platform_summary.items()}
        dominant_platform = max(platform_mentions, key=platform_mentions.get)
        dominant_share = platform_summary[dominant_platform]['share']
        
        insights.append(f"🏆 {dominant_platform.title()} dominates with {dominant_share:.1f}% of mentions")
        
        # Find most engaging platform
        platform_engagement = {platform: data['interactions'] for platform, data in platform_summary.items()}
        most_engaging = max(platform_engagement, key=platform_engagement.get)
        insights.append(f"🔥 {most_engaging.title()} has the highest engagement")
        
        # Platform diversity
        active_platforms = len([p for p in platform_summary.values() if p['mentions'] > 0])
        insights.append(f"📊 Active on {active_platforms} platforms")
        
        return insights

