"""
Simple Historical Analysis App
简化版历史数据分析应用，避免复杂导入问题
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional, Tuple

# 页面配置
st.set_page_config(
    page_title="BuzzScope - Historical Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

class SimpleHistoricalAnalyzer:
    """简化的历史数据分析器"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self.platforms = ["hackernews", "reddit", "youtube", "discord"]
        self.default_keywords = ["ai", "iot", "mqtt", "unified_namespace"]
        
        # Hacker News parquet分析器已移除，使用缓存数据
    
    def load_platform_data(self, platform: str, keyword: str) -> Dict[str, Any]:
        """加载平台数据"""
        file_path = os.path.join(self.cache_dir, platform, f"{keyword}.json")
        if not os.path.exists(file_path):
            return {"status": "error", "posts": []}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")
            return {"status": "error", "posts": []}
    
    def calculate_platform_metrics(self, platform: str, keyword: str) -> Dict[str, Any]:
        """计算单个平台的指标"""
        # 优先使用缓存数据
        data = self.load_platform_data(platform, keyword)
        
        # 如果缓存数据存在且包含metrics，直接返回
        if data.get("metrics"):
            return data["metrics"]
        
        # 如果缓存数据存在但没有metrics，从posts计算
        posts = data.get("posts", [])
        
        if not posts:
            return {
                "platform": platform,
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
        total_interactions = sum(self._get_interaction_count(post) for post in posts)
        unique_authors = len(set(self._get_author(post) for post in posts if self._get_author(post)))
        
        # 计算Top贡献者
        author_counts = Counter(self._get_author(post) for post in posts if self._get_author(post))
        top_contributors = [
            {
                "author": author,
                "post_count": count,
                "platform": platform,
                "profile_url": self._get_author_url(platform, author)
            }
            for author, count in author_counts.most_common(10)
        ]
        
        # 计算Top帖子
        top_posts = sorted(posts, key=lambda x: self._get_interaction_count(x), reverse=True)[:10]
        top_posts = [
            {
                "title": post.get('title', 'No title'),
                "interactions": self._get_interaction_count(post),
                "author": self._get_author(post),
                "created_at": post.get('created_at', ''),
                "url": self._get_post_url(platform, post),
                "platform": platform
            }
            for post in top_posts
        ]
        
        # 计算月度趋势数据
        monthly_mentions = self._calculate_monthly_mentions(posts)
        
        return {
            "platform": platform,
            "keyword": keyword,
            "total_posts": total_posts,
            "total_interactions": total_interactions,
            "unique_authors": unique_authors,
            "top_contributors": top_contributors,
            "top_posts": top_posts,
            "monthly_mentions": monthly_mentions
        }
    
    def _get_interaction_count(self, post: Dict[str, Any]) -> int:
        """获取帖子的互动数"""
        platform = post.get('platform', '')
        
        if platform == 'reddit':
            return post.get('score', 0) + post.get('num_comments', 0)
        elif platform == 'youtube':
            # YouTube互动数计算：观看数/100 + 点赞数 + 评论数
            # 这样既考虑了观看数，又不会让观看数完全主导排名
            view_count = (post.get('view_count', 0) or 0)
            like_count = (post.get('like_count', 0) or 0)
            comment_count = (post.get('comment_count', 0) or 0)
            return (view_count // 100) + like_count + comment_count
        elif platform == 'hackernews':
            return post.get('score', 0) + post.get('descendants', 0)
        elif platform == 'discord':
            # Discord互动数计算：如果有reactions数据就使用，否则默认为1（表示有内容）
            reactions = post.get('reactions', 0)
            if reactions == 0 or reactions == "No reactions":
                return 1  # 至少表示有内容被发布
            return int(reactions) if isinstance(reactions, (int, str)) and str(reactions).isdigit() else 1
        else:
            return 0
    
    def _get_author(self, post: Dict[str, Any]) -> Optional[str]:
        """获取帖子作者"""
        platform = post.get('platform', '')
        
        if platform == 'reddit':
            return post.get('author', '')
        elif platform == 'youtube':
            return post.get('author', '') or post.get('channel_title', '')
        elif platform == 'hackernews':
            return post.get('by', '')
        elif platform == 'discord':
            return post.get('author', '')
        else:
            return None
    
    def _get_author_url(self, platform: str, author: str) -> str:
        """获取作者链接"""
        if platform == 'reddit':
            return f"https://reddit.com/u/{author}"
        elif platform == 'youtube':
            return f"https://youtube.com/@{author.replace(' ', '')}"
        elif platform == 'hackernews':
            return f"https://news.ycombinator.com/user?id={author}"
        elif platform == 'discord':
            return f"https://discord.com/users/{author}"
        else:
            return ""
    
    def _get_post_url(self, platform: str, post: Dict[str, Any]) -> str:
        """获取帖子链接"""
        if platform == 'reddit':
            return f"https://reddit.com{post.get('permalink', '')}"
        elif platform == 'youtube':
            return f"https://youtube.com/watch?v={post.get('video_id', '')}"
        elif platform == 'hackernews':
            return f"https://news.ycombinator.com/item?id={post.get('id', '')}"
        elif platform == 'discord':
            return post.get('jump_url', '')
        else:
            return ""
    
    def _calculate_monthly_mentions(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算每月提及数"""
        monthly_counts = defaultdict(int)
        
        for post in posts:
            # 尝试多个时间戳字段
            timestamp_fields = ['created_at', 'timestamp', 'published_at', 'upload_date']
            date_obj = None
            
            for field in timestamp_fields:
                timestamp = post.get(field, '')
                if timestamp:
                    try:
                        # 处理不同的时间戳格式
                        if 'T' in timestamp:
                            date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        elif ' ' in timestamp and '+' in timestamp:
                            date_obj = datetime.fromisoformat(timestamp)
                        elif ' ' in timestamp:
                            date_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        else:
                            date_obj = datetime.fromisoformat(timestamp)
                        break
                    except:
                        continue
            
            if date_obj:
                month_str = date_obj.strftime('%Y-%m')
                monthly_counts[month_str] += 1
        
        return dict(monthly_counts)

def display_platform_overview(metrics: Dict[str, Any]):
    """显示平台概览"""
    st.subheader("Platform Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Posts",
            value=metrics.get('total_posts', 0),
            help="该平台的总帖子数"
        )
    
    with col2:
        st.metric(
            label="Total Interactions", 
            value=metrics.get('total_interactions', 0),
            help="该平台的总互动数"
        )
    
    with col3:
        st.metric(
            label="Unique Authors",
            value=metrics.get('unique_authors', 0),
            help="该平台的独特作者数"
        )

def display_top_contributors(contributors: List[Dict[str, Any]], platform: str):
    """显示Top贡献者"""
    if not contributors:
        st.info("No contributors found")
        return
    
    st.subheader(f"Top Contributors - {platform.title()}")
    
    for i, contributor in enumerate(contributors[:10]):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            if contributor.get('profile_url'):
                st.markdown(f"[{contributor['author']}]({contributor['profile_url']})")
            else:
                st.write(contributor['author'])
        
        with col2:
            st.write(f"{contributor['post_count']} posts")
        
        with col3:
            st.write(platform.title())

def display_discord_special(keyword: str):
    """显示Discord特殊内容：图片和Top Contributors"""
    st.subheader("Industry 4.0 Discord Community Analysis")
    
    # 1. 显示预处理好的图片
    image_path = "data/cache/charts/discord4.0solutions.png"
    if os.path.exists(image_path):
        st.write("**Channel Distribution by Keywords**")
        st.image(image_path, caption="Industry 4.0 Discord Community - Channel Distribution", width='stretch')
    else:
        st.warning("Discord channel distribution image not found")
    
    # 2. 显示Top Contributors表格
    st.write("**Top Contributors by Keyword**")
    
    # 根据关键词选择对应的CSV文件
    csv_files = {
        "ai": "data/discord/industry40/Industry 4.0 Community Discord - 🏭 Industry 4.0 Topics - ai-and-ml [742458296400740472].csv",
        "iot": "data/discord/industry40/Industry 4.0 Community Discord - 🚀 Automation Stack - iiot-edge [742458745031884921].csv",
        "mqtt": "data/discord/industry40/Industry 4.0 Community Discord - 🏭 Industry 4.0 Topics - mqtt [1166016853991235594].csv",
        "unified_namespace": "data/discord/industry40/Industry 4.0 Community Discord - 🏭 Industry 4.0 Topics - unified-namespace [740564843710382080].csv"
    }
    
    csv_file = csv_files.get(keyword)
    if csv_file and os.path.exists(csv_file):
        try:
            # 读取CSV文件并分析Top Contributors
            df = pd.read_csv(csv_file)
            
            # 统计每个作者的贡献
            if 'Author' in df.columns:
                author_counts = df['Author'].value_counts().head(10)
                
                # 显示Top Contributors表格
                contributors_data = []
                for author, count in author_counts.items():
                    contributors_data.append({
                        'Author': author,
                        'Messages': count,
                        'Platform': 'Discord'
                    })
                
                if contributors_data:
                    contributors_df = pd.DataFrame(contributors_data)
                    st.dataframe(contributors_df, width='stretch')
                else:
                    st.info("No contributors found in Discord data")
            else:
                st.warning(f"CSV file {csv_file} does not have 'Author' column")
                
        except Exception as e:
            st.error(f"Error reading Discord CSV file: {e}")
    else:
        st.warning(f"Discord CSV file for keyword '{keyword}' not found")

def display_top_posts(posts: List[Dict[str, Any]], platform: str):
    """显示Top帖子"""
    if not posts:
        st.info("No posts found")
        return
    
    st.subheader(f"Top Posts - {platform.title()}")
    
    for i, post in enumerate(posts[:10]):
        with st.expander(f"#{i+1} {post['title'][:50]}..."):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Title:** {post['title']}")
                st.write(f"**Author:** {post['author']}")
                st.write(f"**Date:** {post['created_at']}")
            
            with col2:
                st.write(f"**Interactions:** {post['interactions']}")
                if post.get('url'):
                    st.markdown(f"[View Post]({post['url']})")

def load_cached_chart(platform: str, keyword: str) -> Dict[str, Any]:
    """加载缓存的图表数据"""
    chart_file = f"data/cache/charts/{platform}_{keyword}_trend.json"
    if os.path.exists(chart_file):
        try:
            with open(chart_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading chart {chart_file}: {e}")
    return None

def display_trend_analysis(metrics: Dict[str, Any], platform: str, keyword: str):
    """显示月度趋势分析"""
    st.subheader(f"Monthly Trend Analysis - {platform.title()}")
    
    # 尝试加载缓存的图表
    cached_chart = load_cached_chart(platform, keyword)
    
    if cached_chart:
        # 使用缓存的图表HTML，添加Plotly.js库
        chart_html = cached_chart['chart_html']
        # 在HTML头部添加Plotly.js库
        if 'plotly.js' not in chart_html.lower():
            plotly_js = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
            chart_html = chart_html.replace('<head>', f'<head>{plotly_js}')
        
        st.components.v1.html(chart_html, height=450)
        
        # 显示缓存的统计信息
        stats = cached_chart.get('statistics', {})
        st.markdown("**Monthly Statistics**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if stats.get('most_active_month'):
                st.metric("Most Active Month", stats['most_active_month'])
        
        with col2:
            if stats.get('average_posts_per_month'):
                st.metric("Average Posts/Month", f"{stats['average_posts_per_month']}")
    else:
        # 回退到实时计算
        monthly_mentions = metrics.get('monthly_mentions', {})
        
        if not monthly_mentions:
            st.info("No monthly trend data available")
            return
        
        # 创建月度趋势图
        months = sorted(monthly_mentions.keys())
        counts = [monthly_mentions[month] for month in months]
        
        fig = go.Figure(data=go.Scatter(
            x=months,
            y=counts,
            mode='lines+markers',
            name='Monthly Mentions',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8, color='#1f77b4')
        ))
        
        fig.update_layout(
            title=f"Monthly Mentions Trend for {platform.title()}",
            xaxis_title="Month",
            yaxis_title="Number of Posts",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 显示月度统计信息
        st.write("### Monthly Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if monthly_mentions:
                max_month = max(monthly_mentions.items(), key=lambda x: x[1])
                st.metric("Most Active Month", f"{max_month[0]} ({max_month[1]} posts)")
        
        with col2:
            if monthly_mentions:
                total_months = len(monthly_mentions)
                total_posts = sum(monthly_mentions.values())
                avg_posts = total_posts / total_months if total_months > 0 else 0
                st.metric("Average Posts/Month", f"{avg_posts:.1f}")

def main():
    st.title("BuzzScope - Historical Analysis")
    st.markdown("---")
    
    # 初始化分析器
    analyzer = SimpleHistoricalAnalyzer()
    
    # 侧边栏配置
    st.sidebar.header("Analysis Configuration")
    
    # 关键词选择
    selected_keywords = st.sidebar.multiselect(
        "Select Keywords:",
        analyzer.default_keywords,
        default=analyzer.default_keywords
    )
    
    # 平台选择
    selected_platforms = st.sidebar.multiselect(
        "Select Platforms:",
        analyzer.platforms,
        default=analyzer.platforms
    )
    
    # 分析类型选择
    analysis_type = st.sidebar.selectbox(
        "Analysis Type:",
        ["Single Keyword Analysis", "Cross-Platform Comparison"]
    )
    
    if not selected_keywords:
        st.warning("Please select at least one keyword")
        return
    
    if not selected_platforms:
        st.warning("Please select at least one platform")
        return
    
    # 主内容区域
    if analysis_type == "Single Keyword Analysis":
        display_single_keyword_analysis(analyzer, selected_keywords, selected_platforms)
    elif analysis_type == "Cross-Platform Comparison":
        display_cross_platform_comparison(analyzer, selected_keywords, selected_platforms)

def display_single_keyword_analysis(analyzer, keywords, platforms):
    """显示单关键词分析"""
    # 使用侧边栏已选择的关键词
    if len(keywords) == 1:
        selected_keyword = keywords[0]
    else:
        st.warning("Please select exactly one keyword from the sidebar")
        return
    
    # 显示加载状态
    with st.spinner(f"Analyzing {selected_keyword}..."):
        # 分析关键词
        results = {}
        for platform in platforms:
            results[platform] = analyzer.calculate_platform_metrics(platform, selected_keyword)
    
    # 显示总体统计
    st.subheader(f"Overall Statistics for '{selected_keyword}'")
    
    total_posts = sum(metrics['total_posts'] for metrics in results.values())
    total_interactions = sum(metrics['total_interactions'] for metrics in results.values())
    # 统计各平台作者总数（可能包含跨平台重复）
    total_authors = sum(metrics['unique_authors'] for metrics in results.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Posts", total_posts)
    with col2:
        st.metric("Total Interactions", total_interactions)
    with col3:
        st.metric("Unique Authors", total_authors)
    
    # 显示各平台分析
    for i, (platform, metrics) in enumerate(results.items()):
        if metrics['total_posts'] > 0:
            # 平台分隔线（除了第一个平台）
            if i > 0:
                st.markdown("---")
            
            # 平台标题
            st.header(f"{platform.title()} Analysis")
            
            # Discord特殊处理
            if platform == "discord":
                display_discord_special(selected_keyword)
            else:
                # 其他平台的常规处理
                # 平台概览
                display_platform_overview(metrics)
                
                # Top贡献者
                display_top_contributors(metrics['top_contributors'], platform)
                
                # Top帖子
                display_top_posts(metrics['top_posts'], platform)
                
                # 趋势分析
                display_trend_analysis(metrics, platform, selected_keyword)
            
        else:
            # 无数据时的分隔线
            if i > 0:
                st.markdown("---")
            st.info(f"{platform.title()}: No data available")

def display_cross_platform_comparison(analyzer, keywords, platforms):
    """显示跨平台对比分析"""
    st.header("Cross-Platform Comparison")
    
    # 显示加载状态
    with st.spinner("Analyzing keywords..."):
        # 收集所有关键词的数据
        all_results = {}
        for keyword in keywords:
            all_results[keyword] = {}
            for platform in platforms:
                all_results[keyword][platform] = analyzer.calculate_platform_metrics(platform, keyword)
    
    # 创建对比数据
    comparison_data = []
    for keyword in keywords:
        for platform in platforms:
            metrics = all_results[keyword][platform]
            comparison_data.append({
                'keyword': keyword,
                'platform': platform,
                'posts': metrics['total_posts'],
                'interactions': metrics['total_interactions'],
                'authors': metrics['unique_authors']
            })
    
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        
        # 创建对比图
        fig = px.bar(
            df, 
            x='platform', 
            y='posts', 
            color='keyword',
            title='Cross-Platform Comparison: Posts by Platform and Keyword',
            barmode='group'
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 显示详细数据表
        st.write("### Detailed Comparison")
        st.dataframe(df, width='stretch')

if __name__ == "__main__":
    main()
