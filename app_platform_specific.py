"""
BuzzScope - Platform-Specific Analysis Application
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
    page_title="BuzzScope - Platform-Specific Analysis",
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
    .platform-header {
        font-size: 2rem;
        font-weight: bold;
        margin: 2rem 0 1rem 0;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .hackernews-header { background: linear-gradient(90deg, #ff6600 0%, #ff9900 100%); color: white; }
    .reddit-header { background: linear-gradient(90deg, #ff4500 0%, #ff6b35 100%); color: white; }
    .youtube-header { background: linear-gradient(90deg, #ff0000 0%, #cc0000 100%); color: white; }
    .discord-header { background: linear-gradient(90deg, #5865f2 0%, #7289da 100%); color: white; }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Main header
    st.markdown('<div class="main-header">📊 BuzzScope - Platform-Specific Analysis</div>', unsafe_allow_html=True)
    st.markdown("""
    ### 🎯 Platform-Specific Analysis Architecture
    - **Keyword Input**: Enter technology keywords for analysis
    - **Platform Independent**: Each platform displays data and timeline independently
    - **Dynamic Collection**: Support real-time data collection for new keywords
    - **Historical Data**: Prioritize pre-collected historical data
    """)
    
    # Sidebar configuration
    st.sidebar.header("🔧 Analysis Configuration")
    
    # Keyword input
    keyword = st.sidebar.text_input(
        "🔍 Enter Keyword",
        value="IoT",
        help="Enter technology keyword to analyze"
    )
    
    # Exact match option
    exact_match = st.sidebar.checkbox(
        "🎯 Exact Match",
        value=False,
        help="Whether to use exact phrase matching"
    )
    
    # Platform selection
    st.sidebar.subheader("📱 Select Platforms")
    platforms = {
        'Hacker News': st.sidebar.checkbox("🔥 Hacker News", value=True),
        'Reddit': st.sidebar.checkbox("🔴 Reddit", value=True),
        'YouTube': st.sidebar.checkbox("📺 YouTube", value=True),
        'Discord': st.sidebar.checkbox("💬 Discord", value=True)
    }
    
    # Analysis button
    if st.sidebar.button("🚀 Start Analysis", type="primary"):
        if keyword.strip():
            analyze_keyword_platform_specific(keyword.strip(), platforms, exact_match)
        else:
            st.error("Please enter a keyword")
    
    # Display data collection status
    display_data_status()

def analyze_keyword_platform_specific(keyword: str, platforms: Dict[str, bool], exact_match: bool = False):
    """Analyze keyword with platform-specific views"""
    with st.spinner(f"Analyzing keyword '{keyword}'..."):
        try:
            # Use the new data collection service
            from data_collection_service import DataCollectionService
            service = DataCollectionService()
            
            # Check if we have historical data for this keyword
            status = service.get_keyword_status(keyword)
            
            if status['has_historical_data']:
                st.info(f"📚 Using cached historical data for analysis: {keyword}")
                analyze_with_historical_data(keyword, platforms, exact_match)
            else:
                st.info(f"🔄 Collecting new data for: {keyword}")
                analyze_with_dynamic_collection(keyword, platforms, exact_match)
            
        except Exception as e:
            st.error(f"Error occurred during analysis: {str(e)}")
            logger.error(f"Analysis error: {e}", exc_info=True)

def analyze_with_historical_data(keyword: str, platforms: Dict[str, bool], exact_match: bool = False):
    """Analyze using historical data"""
    from src.analyzers.historical_analyzer import HistoricalAnalyzer
    
    historical_analyzer = HistoricalAnalyzer()
    analysis = historical_analyzer.analyze_keyword_from_historical(keyword)
    
    if 'error' in analysis:
        st.error(f"Historical data analysis failed: {analysis['error']}")
        return
    
    # Display platform-specific results
    st.header(f"📊 {keyword} - Historical Data Analysis")
    
    for platform, data in analysis['platforms'].items():
        if 'error' in data:
            continue
            
        if platform == 'hackernews' and platforms.get('Hacker News', False):
            display_hackernews_analysis(keyword, data)
        elif platform == 'reddit' and platforms.get('Reddit', False):
            display_reddit_analysis(keyword, data)
        elif platform == 'youtube' and platforms.get('YouTube', False):
            display_youtube_analysis(keyword, data)

def analyze_with_dynamic_collection(keyword: str, platforms: Dict[str, bool], exact_match: bool = False):
    """Analyze with dynamic data collection using the new service"""
    st.info(f"🔄 Collecting new data for '{keyword}'...")
    
    try:
        # Use the new data collection service
        from data_collection_service import DataCollectionService
        service = DataCollectionService()
        
        # Convert platform selection to service format
        platform_list = []
        if platforms.get('Hacker News', False):
            platform_list.append('hackernews')
        if platforms.get('Reddit', False):
            platform_list.append('reddit')
        if platforms.get('YouTube', False):
            platform_list.append('youtube')
        if platforms.get('Discord', False):
            platform_list.append('discord')
        
        # Collect data using the service
        collection_results = service.collect_keyword_data(
            keyword=keyword,
            days_back=30,
            platforms=platform_list,
            exact_match=exact_match,
            use_historical=False
        )
        
        # Display collection results
        st.success(f"✅ Data collection completed for '{keyword}'")
        
        # Show collection summary
        with st.expander("📊 Collection Summary"):
            st.write(f"**Total Posts**: {collection_results['summary']['total_posts']}")
            st.write(f"**Successful Platforms**: {collection_results['summary']['successful_platforms']}")
            st.write(f"**Failed Platforms**: {collection_results['summary']['failed_platforms']}")
            
            for platform, data in collection_results['platforms'].items():
                if data['status'] == 'success':
                    st.write(f"✅ **{platform.title()}**: {data['posts_collected']} posts")
                elif data['status'] == 'no_data':
                    st.write(f"⚠️ **{platform.title()}**: No posts found")
                else:
                    st.write(f"❌ **{platform.title()}**: {data.get('error', 'Unknown error')}")
        
        # Now analyze the collected data
        from src.analyzers.historical_analyzer import HistoricalAnalyzer
        analyzer = HistoricalAnalyzer()
        analysis = analyzer.analyze_keyword_from_historical(keyword)
        
        if 'error' not in analysis:
            # Display platform-specific results
            st.header(f"📊 {keyword} - Real-time Data Analysis")
            
            for platform, data in analysis['platforms'].items():
                if 'error' not in data:
                    if platform == 'hackernews' and platforms.get('Hacker News', False):
                        display_hackernews_analysis(keyword, data)
                    elif platform == 'reddit' and platforms.get('Reddit', False):
                        display_reddit_analysis(keyword, data)
                    elif platform == 'youtube' and platforms.get('YouTube', False):
                        display_youtube_analysis(keyword, data)
                    elif platform == 'discord' and platforms.get('Discord', False):
                        display_discord_analysis(keyword, data)
        else:
            st.error(f"Analysis failed: {analysis['error']}")
            
    except Exception as e:
        st.error(f"Dynamic collection failed: {str(e)}")
        logger.error(f"Dynamic collection error: {e}", exc_info=True)

def display_hackernews_analysis(keyword: str, data: Dict[str, Any]):
    """Display Hacker News specific analysis"""
    st.markdown('<div class="platform-header hackernews-header">🔥 Hacker News Analysis</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Posts", data.get('total_posts', 0))
    with col2:
        st.metric("Unique Authors", data.get('unique_authors', 0))
    with col3:
        st.metric("Total Score", data.get('total_score', 0))
    with col4:
        st.metric("Average Score", f"{data.get('avg_score', 0):.1f}")
    
    # Content type distribution
    if 'content_types' in data:
        st.subheader("📝 Content Type Distribution")
        type_df = pd.DataFrame(list(data['content_types'].items()), columns=['Type', 'Count'])
        fig = px.pie(type_df, values='Count', names='Type', title="Content Type Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    # Daily activity
    if 'daily_activity' in data:
        st.subheader("📈 Daily Activity Trend")
        daily_df = pd.DataFrame(list(data['daily_activity'].items()), columns=['Date', 'Posts'])
        daily_df['Date'] = pd.to_datetime(daily_df['Date'])
        fig = px.line(daily_df, x='Date', y='Posts', title="Daily Posts Trend")
        st.plotly_chart(fig, use_container_width=True)
    
    # Top posts
    if 'top_posts' in data:
        st.subheader("🏆 Top Posts")
        for i, post in enumerate(data['top_posts'][:5], 1):
            with st.expander(f"{i}. {post.get('title', 'N/A')[:60]}..."):
                st.write(f"**Author**: {post.get('author', 'N/A')}")
                st.write(f"**Score**: {post.get('score', 0)}")
                st.write(f"**Time**: {post.get('time', 'N/A')}")

def display_reddit_analysis(keyword: str, data: Dict[str, Any]):
    """Display Reddit specific analysis"""
    st.markdown('<div class="platform-header reddit-header">🔴 Reddit Analysis</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Posts", data.get('total_posts', 0))
    with col2:
        st.metric("Unique Authors", data.get('unique_authors', 0))
    with col3:
        st.metric("Total Score", data.get('total_score', 0))
    with col4:
        st.metric("Total Comments", data.get('total_comments', 0))
    
    # Subreddit distribution
    if 'subreddits' in data:
        st.subheader("🏘️ Subreddit Distribution")
        subreddit_df = pd.DataFrame(list(data['subreddits'].items()), columns=['Subreddit', 'Posts'])
        fig = px.bar(subreddit_df, x='Subreddit', y='Posts', title="Posts by Subreddit")
        st.plotly_chart(fig, use_container_width=True)
    
    # Daily activity
    if 'daily_activity' in data:
        st.subheader("📈 Daily Activity Trend")
        daily_df = pd.DataFrame(list(data['daily_activity'].items()), columns=['Date', 'Posts'])
        daily_df['Date'] = pd.to_datetime(daily_df['Date'])
        fig = px.line(daily_df, x='Date', y='Posts', title="Daily Posts Trend")
        st.plotly_chart(fig, use_container_width=True)
    
    # Top posts
    if 'top_posts' in data:
        st.subheader("🏆 Top Posts")
        for i, post in enumerate(data['top_posts'][:5], 1):
            with st.expander(f"{i}. r/{post.get('subreddit', 'N/A')}: {post.get('title', 'N/A')[:50]}..."):
                st.write(f"**Author**: {post.get('author', 'N/A')}")
                st.write(f"**Score**: {post.get('score', 0)}")
                st.write(f"**Comments**: {post.get('num_comments', 0)}")

def display_youtube_analysis(keyword: str, data: Dict[str, Any]):
    """Display YouTube specific analysis"""
    st.markdown('<div class="platform-header youtube-header">📺 YouTube Analysis</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Videos", data.get('total_videos', 0))
    with col2:
        st.metric("Unique Channels", data.get('unique_channels', 0))
    with col3:
        st.metric("Total Views", f"{data.get('total_views', 0):,}")
    with col4:
        st.metric("Total Likes", f"{data.get('total_likes', 0):,}")
    
    # Top channels
    if 'top_channels' in data:
        st.subheader("📺 Top Channels")
        channel_df = pd.DataFrame(list(data['top_channels'].items()), columns=['Channel', 'Videos'])
        fig = px.bar(channel_df.head(10), x='Channel', y='Videos', title="Videos by Channel")
        st.plotly_chart(fig, use_container_width=True)
    
    # Daily activity
    if 'daily_activity' in data:
        st.subheader("📈 Daily Activity Trend")
        daily_df = pd.DataFrame(list(data['daily_activity'].items()), columns=['Date', 'Videos'])
        daily_df['Date'] = pd.to_datetime(daily_df['Date'])
        fig = px.line(daily_df, x='Date', y='Videos', title="Daily Video Upload Trend")
        st.plotly_chart(fig, use_container_width=True)
    
    # Top videos
    if 'top_videos' in data:
        st.subheader("🏆 Top Videos")
        for i, video in enumerate(data['top_videos'][:5], 1):
            with st.expander(f"{i}. {video.get('title', 'N/A')[:60]}..."):
                st.write(f"**Channel**: {video.get('channel_title', 'N/A')}")
                st.write(f"**Views**: {video.get('view_count', 0):,}")
                st.write(f"**Likes**: {video.get('like_count', 0):,}")

def display_discord_analysis(keyword: str, data: Dict[str, Any]):
    """Display Discord specific analysis"""
    st.markdown('<div class="platform-header discord-header">💬 Discord Analysis</div>', unsafe_allow_html=True)
    
    # This would be implemented based on Discord data structure
    st.info("Discord analysis functionality is under development...")

def collect_data(keyword: str, platforms: Dict[str, bool], days_back: int, exact_match: bool = False) -> Dict[str, Any]:
    """Collect data from selected platforms"""
    try:
        storage = BuzzScopeStorage()
        collected_data = {}
        
        # Hacker News
        if platforms.get('Hacker News', False):
            try:
                hn_collector = HackerNewsCollector()
                hn_posts = hn_collector.search_keyword(keyword, days_back, exact_match)
                if hn_posts:
                    storage.save_posts(hn_posts, 'hackernews')
                    collected_data['hackernews'] = len(hn_posts)
            except Exception as e:
                logger.error(f"Hacker News collection error: {e}")
        
        # Reddit
        if platforms.get('Reddit', False):
            try:
                reddit_collector = RedditCollector()
                reddit_posts = reddit_collector.search_keyword(keyword, days_back, exact_match, use_global=True)
                if reddit_posts:
                    storage.save_posts(reddit_posts, 'reddit')
                    collected_data['reddit'] = len(reddit_posts)
            except Exception as e:
                logger.error(f"Reddit collection error: {e}")
        
        # YouTube
        if platforms.get('YouTube', False):
            try:
                youtube_collector = YouTubeCollector()
                youtube_posts = youtube_collector.search_keyword(keyword, days_back, exact_match)
                if youtube_posts:
                    storage.save_posts(youtube_posts, 'youtube')
                    collected_data['youtube'] = len(youtube_posts)
            except Exception as e:
                logger.error(f"YouTube collection error: {e}")
        
        # Discord
        if platforms.get('Discord', False):
            try:
                discord_collector = DiscordCollector()
                discord_posts = discord_collector.search_keyword(keyword, days_back, exact_match)
                if discord_posts:
                    storage.save_posts(discord_posts, 'discord')
                    collected_data['discord'] = len(discord_posts)
            except Exception as e:
                logger.error(f"Discord collection error: {e}")
        
        return {
            'success': True,
            'data': collected_data,
            'total_posts': sum(collected_data.values())
        }
        
    except Exception as e:
        logger.error(f"Data collection error: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def display_data_status():
    """Display current data collection status"""
    st.sidebar.subheader("📊 Data Status")
    
    try:
        storage = BuzzScopeStorage()
        stats = storage.get_storage_stats()
        
        for platform, data in stats.items():
            if isinstance(data, dict):
                # Extract total_posts from the dictionary
                total_posts = data.get('total_posts', 0)
                st.sidebar.metric(platform.title(), total_posts)
            else:
                # If it's already a number, use it directly
                st.sidebar.metric(platform.title(), data)
            
    except Exception as e:
        st.sidebar.error(f"Unable to get data status: {e}")

if __name__ == "__main__":
    main()
