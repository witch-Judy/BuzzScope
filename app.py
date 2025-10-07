"""
BuzzScope - Streamlit Application for Keyword Tracking
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import logging
from typing import Dict, List, Any

# Import BuzzScope modules
from src.config import Config
from src.storage import BuzzScopeStorage
from src.analysis_v2 import BuzzScopeAnalyzerV2
from src.visualization import ChartFactory, DashboardComponents
from src.collectors import (
    HackerNewsCollector, RedditCollector, 
    YouTubeCollector, DiscordCollector
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="BuzzScope - Refactored Architecture",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .platform-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_storage():
    """Load storage system with caching"""
    return BuzzScopeStorage()

@st.cache_data
def load_analyzer():
    """Load analyzer with caching"""
    return BuzzScopeAnalyzerV2(load_storage())

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🔍 BuzzScope</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Keyword Tracking Across Tech Communities</p>', unsafe_allow_html=True)
    
    # Architecture info
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #667eea; margin-bottom: 1rem;">
        <h4>🏗️ Refactored Architecture</h4>
        <p><strong>Analysis Layer:</strong> Platform-specific analyzers handle data processing</p>
        <p><strong>Visualization Layer:</strong> Reusable components handle chart creation</p>
        <p><strong>Separation of Concerns:</strong> Clean separation between data analysis and presentation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    storage = load_storage()
    analyzer = load_analyzer()
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Configuration")
        
        # Keyword input
        keyword = st.text_input(
            "🔍 Keyword to Track",
            value="",
            placeholder="Enter keyword (e.g., 'unified namespace', 'AI', 'IoT')",
            help="Enter the keyword or phrase you want to track across platforms"
        )
        
        # Exact match option
        exact_match = st.checkbox(
            "🎯 Exact Phrase Match",
            value=False,
            help="If checked, only matches the exact phrase. If unchecked, matches any text containing the keyword."
        )
        
        # Time range
        days_back = st.slider(
            "📅 Days to Look Back",
            min_value=1,
            max_value=90,
            value=30,
            help="Number of days to analyze"
        )
        
        # Platform selection
        st.subheader("🌐 Platforms")
        platforms = []
        for platform, config in Config.PLATFORMS.items():
            enabled = st.checkbox(
                platform.title(),
                value=config.get('enabled', False),
                disabled=not Config.is_platform_enabled(platform)
            )
            if enabled:
                platforms.append(platform)
        
        # Analysis type
        analysis_type = st.selectbox(
            "📊 Analysis Type",
            ["Single Keyword Analysis", "Keyword Comparison", "Cross-Platform Insights"]
        )
        
        # Data collection
        st.subheader("📥 Data Collection")
        if st.button("🔄 Collect Fresh Data"):
            collect_data(keyword, platforms, days_back, exact_match)
    
    # Main content area
    if not keyword:
        st.warning("Please enter a keyword to analyze")
        return
    
    if not platforms:
        st.warning("Please select at least one platform")
        return
    
    # Display analysis based on type
    if analysis_type == "Single Keyword Analysis":
        display_single_keyword_analysis(analyzer, keyword, platforms, days_back, exact_match)
    elif analysis_type == "Keyword Comparison":
        display_keyword_comparison(analyzer, platforms, days_back, exact_match)
    elif analysis_type == "Cross-Platform Insights":
        display_cross_platform_insights(analyzer, keyword, days_back, exact_match)
    
    # Storage statistics
    display_storage_stats(storage)

def collect_data(keyword: str, platforms: List[str], days_back: int, exact_match: bool = False):
    """Collect fresh data from platforms"""
    st.info(f"🔄 Collecting fresh data for '{keyword}' (exact_match={exact_match})...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    collectors = {
        'hackernews': HackerNewsCollector(),
        'reddit': RedditCollector(),
        'youtube': YouTubeCollector(),
        'discord': DiscordCollector()
    }
    
    storage = load_storage()
    total_platforms = len(platforms)
    
    for i, platform in enumerate(platforms):
        if platform not in collectors:
            continue
        
        status_text.text(f"Collecting from {platform.title()}...")
        
        try:
            collector = collectors[platform]
            posts = collector.search_keyword(keyword, days_back, exact_match)
            
            if posts:
                storage.save_posts(posts, platform)
                st.success(f"✅ Collected {len(posts)} posts from {platform.title()}")
            else:
                st.info(f"ℹ️ No posts found for '{keyword}' in {platform.title()}")
                
        except Exception as e:
            st.error(f"❌ Error collecting from {platform.title()}: {str(e)}")
        
        progress_bar.progress((i + 1) / total_platforms)
    
    status_text.text("✅ Data collection complete!")
    st.success("Data collection completed successfully!")

def display_single_keyword_analysis(analyzer: BuzzScopeAnalyzerV2, keyword: str, 
                                   platforms: List[str], days_back: int, exact_match: bool = False):
    """Display single keyword analysis"""
    match_type = "Exact Phrase" if exact_match else "Substring"
    st.header(f"📊 Analysis: '{keyword}' ({match_type} Match)")
    
    # Get analysis results
    with st.spinner("Analyzing data..."):
        results = analyzer.analyze_keyword(keyword, platforms, days_back, exact_match)
    
    if not results:
        st.warning(f"No data found for keyword '{keyword}' in the selected platforms")
        return
    
    # Overall metrics
    st.subheader("📈 Overall Metrics")
    
    total_mentions = sum(metrics.total_mentions for metrics in results.values())
    total_authors = sum(metrics.unique_authors for metrics in results.values())
    total_interactions = sum(metrics.total_interactions for metrics in results.values())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Mentions", total_mentions)
    with col2:
        st.metric("Unique Authors", total_authors)
    with col3:
        st.metric("Total Interactions", f"{total_interactions:,}")
    with col4:
        st.metric("Active Platforms", len(results))
    
    # Platform breakdown
    st.subheader("🌐 Platform Breakdown")
    
    platform_data = []
    for platform, metrics in results.items():
        platform_data.append({
            'Platform': platform.title(),
            'Mentions': metrics.total_mentions,
            'Authors': metrics.unique_authors,
            'Interactions': metrics.total_interactions
        })
    
    platform_df = pd.DataFrame(platform_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mentions by platform
        fig = px.bar(platform_df, x='Platform', y='Mentions', 
                     title=f"Mentions by Platform - '{keyword}'")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Authors by platform
        fig = px.bar(platform_df, x='Platform', y='Authors',
                     title=f"Unique Authors by Platform - '{keyword}'")
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed platform analysis
    for platform, metrics in results.items():
        st.markdown(f'<div class="platform-header">{platform.title()} Analysis</div>', 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Mentions", metrics.total_mentions)
            st.metric("Unique Authors", metrics.unique_authors)
            st.metric("Total Interactions", f"{metrics.total_interactions:,}")
        
        with col2:
            if metrics.time_series is not None and not metrics.time_series.empty:
                # Time series chart
                fig = px.line(metrics.time_series, x='date', y='mentions',
                             title=f"Daily Mentions Trend - {platform.title()}")
                st.plotly_chart(fig, use_container_width=True)
        
        # Top contributors
        if metrics.top_contributors:
            st.subheader(f"👥 Top Contributors - {platform.title()}")
            contributors_df = pd.DataFrame(metrics.top_contributors)
            st.dataframe(contributors_df, use_container_width=True)
        
        # Sample posts
        if metrics.sample_posts:
            st.subheader(f"📝 Sample Posts - {platform.title()}")
            for post in metrics.sample_posts[:5]:  # Show top 5
                with st.expander(f"{post['title'][:50]}... by {post['author']}"):
                    st.write(f"**Content:** {post['content']}")
                    st.write(f"**Author:** {post['author']}")
                    st.write(f"**Date:** {post['timestamp']}")
                    if post['url']:
                        st.write(f"**URL:** {post['url']}")

def display_keyword_comparison(analyzer: BuzzScopeAnalyzerV2, platforms: List[str], days_back: int, exact_match: bool = False):
    """Display keyword comparison analysis"""
    st.header("⚖️ Keyword Comparison")
    
    # Keyword input for comparison
    st.subheader("🔍 Keywords to Compare")
    
    col1, col2 = st.columns(2)
    with col1:
        keyword1 = st.text_input("Keyword 1", value="", placeholder="Enter first keyword")
    with col2:
        keyword2 = st.text_input("Keyword 2", value="", placeholder="Enter second keyword")
    
    # Add more keywords
    additional_keywords = st.text_input(
        "Additional Keywords (comma-separated)", 
        value="",
        placeholder="Enter additional keywords separated by commas",
        help="Enter additional keywords separated by commas"
    )
    
    # Parse keywords
    keywords = [keyword1, keyword2]
    if additional_keywords:
        keywords.extend([k.strip() for k in additional_keywords.split(',') if k.strip()])
    
    keywords = [k for k in keywords if k]  # Remove empty strings
    
    if len(keywords) < 2:
        st.warning("Please enter at least 2 keywords to compare")
        return
    
    # Platform selection for comparison
    comparison_platform = st.selectbox("Select Platform for Comparison", platforms)
    
    if st.button("🔄 Compare Keywords"):
        with st.spinner("Comparing keywords..."):
            comparison = analyzer.compare_keywords(keywords, comparison_platform, days_back)
        
        if comparison.comparison_data.empty:
            st.warning(f"No data found for comparison in {comparison_platform}")
            return
        
        # Comparison chart
        st.subheader(f"📊 Comparison Results - {comparison_platform.title()}")
        
        # Create comparison chart
        fig = px.line(comparison.comparison_data, x='date', y='mentions', 
                     color='keyword', title=f"Daily Mentions Comparison - {comparison_platform.title()}")
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary table
        summary_data = comparison.comparison_data.groupby('keyword').agg({
            'mentions': 'sum',
            'unique_authors': 'sum',
            'interactions': 'sum'
        }).reset_index()
        
        st.subheader("📋 Comparison Summary")
        st.dataframe(summary_data, use_container_width=True)
        
        # Insights
        if comparison.insights:
            st.subheader("💡 Insights")
            for insight in comparison.insights:
                st.info(insight)

def display_cross_platform_insights(analyzer: BuzzScopeAnalyzerV2, keyword: str, days_back: int, exact_match: bool = False):
    """Display cross-platform insights"""
    match_type = "Exact Phrase" if exact_match else "Substring"
    st.header(f"🌐 Cross-Platform Insights: '{keyword}' ({match_type} Match)")
    
    with st.spinner("Analyzing cross-platform data..."):
        insights = analyzer.get_cross_platform_insights(keyword, days_back)
    
    if not insights['platform_summary']:
        st.warning(f"No cross-platform data found for '{keyword}'")
        return
    
    # Summary metrics
    st.subheader("📊 Cross-Platform Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Mentions", insights['totals']['mentions'])
    with col2:
        st.metric("Unique Authors", insights['totals']['unique_authors'])
    with col3:
        st.metric("Total Interactions", f"{insights['totals']['interactions']:,}")
    
    # Platform comparison
    st.subheader("🌐 Platform Comparison")
    
    platform_data = []
    for platform, data in insights['platform_summary'].items():
        platform_data.append({
            'Platform': platform.title(),
            'Mentions': data['mentions'],
            'Authors': data['unique_authors'],
            'Interactions': data['interactions']
        })
    
    platform_df = pd.DataFrame(platform_data)
    
    # Platform comparison chart
    fig = px.bar(platform_df, x='Platform', y='Mentions',
                 title=f"Platform Comparison - '{keyword}'")
    st.plotly_chart(fig, use_container_width=True)
    
    # Common authors
    if insights['common_authors']:
        st.subheader("👥 Cross-Platform Users")
        st.write(f"Found {len(insights['common_authors'])} users active on multiple platforms:")
        
        for author, platforms in insights['common_authors'].items():
            st.write(f"• **{author}**: {', '.join(platforms)}")
    
    # Insights
    if insights['insights']:
        st.subheader("💡 Key Insights")
        for insight in insights['insights']:
            st.info(insight)

def display_storage_stats(storage: BuzzScopeStorage):
    """Display storage statistics"""
    with st.expander("📊 Storage Statistics"):
        stats = storage.get_storage_stats()
        
        st.write(f"**Total Platforms:** {stats['total_platforms']}")
        st.write(f"**Total Posts:** {stats['total_posts']:,}")
        
        if stats['date_range']:
            st.write(f"**Date Range:** {stats['date_range'][0]} to {stats['date_range'][1]}")
        
        if stats['platform_stats']:
            st.subheader("Platform Details")
            for platform, data in stats['platform_stats'].items():
                st.write(f"**{platform.title()}:** {data['total_posts']} posts, {data['files']} files")

if __name__ == "__main__":
    main()

