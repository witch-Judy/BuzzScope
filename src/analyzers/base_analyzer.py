"""
Base analyzer class for platform-specific analysis
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
import logging
from abc import ABC, abstractmethod
from ..models import KeywordMetrics, ComparisonMetrics

logger = logging.getLogger(__name__)

class BaseAnalyzer(ABC):
    """Base class for platform-specific analyzers"""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.logger = logging.getLogger(f"{__name__}.{platform}")
    
    @abstractmethod
    def calculate_metrics(self, df: pd.DataFrame, keyword: str, 
                         start_date: date, end_date: date) -> KeywordMetrics:
        """Calculate platform-specific metrics"""
        pass
    
    @abstractmethod
    def calculate_interactions(self, df: pd.DataFrame) -> int:
        """Calculate total interactions for the platform"""
        pass
    
    @abstractmethod
    def get_top_contributors(self, df: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top contributors for the platform"""
        pass
    
    @abstractmethod
    def get_sample_posts(self, df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample posts for the platform"""
        pass
    
    def calculate_daily_metrics(self, df: pd.DataFrame, keyword: str) -> pd.DataFrame:
        """Calculate daily metrics for time series (common implementation)"""
        if df.empty:
            return pd.DataFrame()
        
        # Create a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
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
        """Calculate daily interactions (common implementation)"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # This is a simplified version - platform-specific analyzers can override
        return df.groupby('date').size()
    
    def generate_trend_insights(self, daily_metrics: pd.DataFrame, keyword: str) -> List[str]:
        """Generate trend insights (common implementation)"""
        insights = []
        
        if daily_metrics.empty:
            return insights
        
        # Calculate trend
        if len(daily_metrics) >= 2:
            recent_avg = daily_metrics['mentions'].tail(7).mean()
            earlier_avg = daily_metrics['mentions'].head(7).mean()
            
            if recent_avg > earlier_avg * 1.2:
                insights.append(f"📈 {keyword} mentions are trending up (+{((recent_avg/earlier_avg-1)*100):.1f}%)")
            elif recent_avg < earlier_avg * 0.8:
                insights.append(f"📉 {keyword} mentions are trending down ({((recent_avg/earlier_avg-1)*100):.1f}%)")
            else:
                insights.append(f"📊 {keyword} mentions are stable")
        
        # Peak activity
        peak_date = daily_metrics.loc[daily_metrics['mentions'].idxmax(), 'date']
        peak_mentions = daily_metrics['mentions'].max()
        insights.append(f"🔥 Peak activity: {peak_mentions} mentions on {peak_date}")
        
        return insights

