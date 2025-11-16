"""
Dashboard components for BuzzScope
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
from .chart_factory import ChartFactory
from ..models import KeywordMetrics, ComparisonMetrics

class DashboardComponents:
    """Reusable dashboard components"""
    
    @staticmethod
    def create_overview_metrics(results: Dict[str, KeywordMetrics]) -> None:
        """Create overview metrics across all platforms"""
        if not results:
            st.warning("No data available for overview metrics")
            return
        
        st.subheader("📈 Overall Metrics")
        
        total_mentions = sum(metrics.total_mentions for metrics in results.values())
        total_authors = sum(metrics.unique_authors for metrics in results.values())
        total_interactions = sum(metrics.total_interactions for metrics in results.values())
        active_platforms = len(results)
        
        overview_metrics = {
            "Total Mentions": total_mentions,
            "Unique Authors": total_authors,
            "Total Interactions": f"{total_interactions:,}",
            "Active Platforms": active_platforms
        }
        
        ChartFactory.create_metric_cards(overview_metrics)
    
    @staticmethod
    def create_platform_comparison_chart(results: Dict[str, KeywordMetrics], 
                                       metric: str = "total_mentions") -> go.Figure:
        """Create platform comparison chart"""
        if not results:
            return go.Figure()
        
        platform_data = []
        for platform, metrics in results.items():
            platform_data.append({
                'Platform': platform.title(),
                'Mentions': metrics.total_mentions,
                'Authors': metrics.unique_authors,
                'Interactions': metrics.total_interactions
            })
        
        df = pd.DataFrame(platform_data)
        
        fig = ChartFactory.create_platform_comparison_chart(
            platform_data,
            metric=metric.title(),
            title=f"Platform Comparison - {metric.title()}"
        )
        
        return fig
    
    @staticmethod
    def create_platform_distribution_pie(results: Dict[str, KeywordMetrics]) -> go.Figure:
        """Create platform distribution pie chart"""
        if not results:
            return go.Figure()
        
        platform_data = []
        for platform, metrics in results.items():
            platform_data.append({
                'Platform': platform.title(),
                'Mentions': metrics.total_mentions
            })
        
        df = pd.DataFrame(platform_data)
        
        fig = ChartFactory.create_pie_chart(
            df,
            names='Platform',
            values='Mentions',
            title="Platform Distribution"
        )
        
        return fig
    
    @staticmethod
    def create_cross_platform_trends(results: Dict[str, KeywordMetrics]) -> go.Figure:
        """Create cross-platform trends chart"""
        if not results:
            return go.Figure()
        
        # Combine daily metrics from all platforms
        combined_data = []
        for platform, metrics in results.items():
            if metrics.daily_metrics is not None and not metrics.daily_metrics.empty:
                daily_df = metrics.daily_metrics.copy()
                daily_df['platform'] = platform.title()
                combined_data.append(daily_df)
        
        if not combined_data:
            return go.Figure()
        
        combined_df = pd.concat(combined_data, ignore_index=True)
        
        fig = ChartFactory.create_line_chart(
            combined_df,
            x='date',
            y='mentions',
            title="Cross-Platform Trends",
            color='platform'
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Mentions",
            title="📈 Cross-Platform Trends"
        )
        
        return fig
    
    @staticmethod
    def create_insights_section(insights: List[str], title: str = "💡 Insights") -> None:
        """Create insights section"""
        if not insights:
            return
        
        st.subheader(title)
        
        for insight in insights:
            st.info(insight)
    
    @staticmethod
    def create_sample_posts_display(metrics: KeywordMetrics) -> None:
        """Create sample posts display"""
        if not metrics.sample_posts:
            return
        
        st.subheader("📄 Sample Posts")
        
        for i, post in enumerate(metrics.sample_posts[:5]):
            with st.expander(f"Post {i+1} by {post.get('author', 'Unknown')}"):
                if 'title' in post and post['title']:
                    st.write(f"**Title:** {post['title']}")
                
                if 'content' in post and post['content']:
                    content = post['content']
                    if len(content) > 500:
                        content = content[:500] + "..."
                    st.write(f"**Content:** {content}")
                
                if 'timestamp' in post:
                    st.write(f"**Date:** {post['timestamp']}")
                
                if 'url' in post and post['url']:
                    st.write(f"**Link:** [View Post]({post['url']})")

