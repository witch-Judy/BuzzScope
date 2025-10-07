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
    page_title="BuzzScope - New Keyword Test",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

class SimpleHistoricalAnalyzer:
    """简化的历史数据分析器"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self.platforms = ["hackernews", "reddit", "youtube"]  # Discord removed for new keyword analysis
        self.default_keywords = ["ai", "iot", "mqtt", "unified_namespace"]
        
        # Hacker News parquet分析器已移除，使用缓存数据
        
        # 导入收集器（延迟导入，避免Streamlit启动时的依赖问题）
        self._collectors = None
    
    
    def _get_collectors(self):
        """延迟初始化收集器"""
        if self._collectors is None:
            try:
                # 动态导入收集器
                from src.collectors.reddit_collector import RedditCollector
                from src.collectors.youtube_collector import YouTubeCollector
                from src.analyzers.hackernews_parquet_analyzer import HackerNewsParquetAnalyzer
                
                self._collectors = {
                    "hackernews": HackerNewsParquetAnalyzer(),  # 使用parquet数据而不是实时API
                    "reddit": RedditCollector(),
                    "youtube": YouTubeCollector()
                    # 注意：不包含Discord，因为Discord只有历史数据
                }
            except ImportError as e:
                st.error(f"Failed to import collectors: {e}")
                self._collectors = {}
        return self._collectors
    
    def collect_real_data(self, keyword: str) -> Dict[str, Any]:
        """收集新关键词的真实数据"""
        collectors = self._get_collectors()
        
        if not collectors:
            return {
                "status": "error",
                "message": "Failed to initialize data collectors"
            }
        
        results = {
            "keyword": keyword,
            "status": "collecting",
            "platforms": {},
            "start_time": datetime.now().isoformat()
        }
        
        # 只收集有API的平台数据（排除Discord）
        platforms_to_collect = ["hackernews", "reddit", "youtube"]
        
        for platform in platforms_to_collect:
            try:
                st.info(f"🔍 Collecting {platform} data for '{keyword}'...")
                
                collector = collectors[platform]
                
                if platform == "hackernews":
                    # Hacker News使用parquet数据，调用calculate_metrics方法
                    with st.spinner(f"Searching Hacker News parquet data for '{keyword}'... This may take 1-2 minutes"):
                        metrics = collector.calculate_metrics(keyword, exact_match=True)
                    
                    if not metrics or metrics.get('total_posts', 0) == 0:
                        st.warning(f"⚠️ No posts found for '{keyword}' on {platform}")
                        results["platforms"][platform] = {
                            "status": "no_data",
                            "posts_collected": 0,
                            "message": f"No posts found for '{keyword}' on {platform}"
                        }
                        continue
                    
                    # 保存Hacker News数据到缓存
                    try:
                        self._save_hackernews_to_cache(platform, keyword, metrics)
                        
                        results["platforms"][platform] = {
                            "status": "success",
                            "posts_collected": metrics.get('total_posts', 0),
                            "cache_file": f"{keyword}.json",
                            "message": f"Successfully collected {metrics.get('total_posts', 0)} posts from parquet data"
                        }
                        
                        st.success(f"✅ Collected {metrics.get('total_posts', 0)} posts from {platform} parquet data")
                        
                    except Exception as save_error:
                        st.error(f"❌ Error saving {platform} data: {save_error}")
                        results["platforms"][platform] = {
                            "status": "save_error",
                            "error": str(save_error),
                            "posts_collected": metrics.get('total_posts', 0) if metrics else 0
                        }
                        
                else:
                    # Reddit和YouTube使用实时API
                    with st.spinner(f"Searching {platform} for '{keyword}'... This may take 1-3 minutes"):
                        if platform == "reddit":
                            # Reddit使用全局搜索，时间范围设为所有时间
                            posts = collector.search_keyword(keyword, days_back=365*5, exact_match=True, use_global=True)
                        else:
                            # YouTube使用所有时间搜索
                            posts = collector.search_keyword(keyword, days_back=365*5, exact_match=True)
                    
                    if not posts:
                        st.warning(f"⚠️ No posts found for '{keyword}' on {platform}")
                        results["platforms"][platform] = {
                            "status": "no_data",
                            "posts_collected": 0,
                            "message": f"No posts found for '{keyword}' on {platform}"
                        }
                        continue
                    
                    # 保存到缓存
                    try:
                        self._save_real_data_to_cache(platform, keyword, posts)
                        
                        results["platforms"][platform] = {
                            "status": "success",
                            "posts_collected": len(posts),
                            "cache_file": f"{keyword}.json"
                        }
                        
                        st.success(f"✅ Collected {len(posts)} posts from {platform}")
                        
                    except Exception as save_error:
                        st.error(f"❌ Error saving {platform} data: {save_error}")
                        results["platforms"][platform] = {
                            "status": "save_error",
                            "error": str(save_error),
                            "posts_collected": len(posts) if posts else 0
                        }
                
            except Exception as e:
                st.error(f"❌ Error collecting data for {platform}: {e}")
                results["platforms"][platform] = {
                    "status": "error",
                    "error": str(e)
                }
        
        results["end_time"] = datetime.now().isoformat()
        results["status"] = "completed"
        
        return results
    
    def _save_real_data_to_cache(self, platform: str, keyword: str, posts: List[Any]):
        """保存真实数据到缓存文件"""
        cache_dir = os.path.join(self.cache_dir, platform)
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, f"{keyword}.json")
        
        # 将对象转换为字典（如果是对象的话）
        serializable_posts = []
        for post in posts:
            if hasattr(post, '__dict__'):
                # 如果是对象，转换为字典
                post_dict = post.__dict__.copy()
                # 处理datetime对象
                for key, value in post_dict.items():
                    if hasattr(value, 'isoformat'):
                        post_dict[key] = value.isoformat()
                serializable_posts.append(post_dict)
            else:
                # 如果已经是字典，直接使用
                serializable_posts.append(post)
        
        # 创建缓存数据结构
        cache_data = {
            "keyword": keyword,
            "platform": platform,
            "data_source": "time_all" if platform in ["reddit", "youtube"] else "cache",
            "collection_time": datetime.now().isoformat(),
            "posts": serializable_posts,
            "total_posts": len(serializable_posts)
        }
        
        # 保存到文件
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        st.success(f"💾 Cached {len(serializable_posts)} posts to {cache_file}")
        
        # 为新数据生成趋势图表
        self._generate_trend_chart(platform, keyword, serializable_posts)
    
    def _save_hackernews_to_cache(self, platform: str, keyword: str, metrics: Dict[str, Any]) -> None:
        """保存Hacker News parquet数据到缓存"""
        try:
            # 确保目录存在
            platform_dir = os.path.join(self.cache_dir, platform)
            os.makedirs(platform_dir, exist_ok=True)
            
            # 创建缓存数据结构
            cache_data = {
                "keyword": keyword,
                "platform": platform,
                "data_source": "parquet",
                "collected_at": datetime.now().isoformat(),
                "metrics": metrics,
                "total_posts": metrics.get('total_posts', 0)
            }
            
            # 保存到文件
            file_path = os.path.join(platform_dir, f"{keyword}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            st.info(f"💾 Saved Hacker News metrics to cache: {file_path}")
            
        except Exception as e:
            st.error(f"❌ Error saving Hacker News to cache: {e}")
            raise
    
    def _generate_trend_chart(self, platform: str, keyword: str, posts: List[Dict[str, Any]]):
        """为新收集的数据生成趋势图表"""
        try:
            # 计算月度数据
            monthly_mentions = self._calculate_monthly_mentions(posts)
            
            if not monthly_mentions:
                return
            
            # 创建图表
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
            
            # 生成HTML
            chart_html = fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})
            
            # 计算统计信息
            total_months = len(monthly_mentions)
            total_posts = sum(monthly_mentions.values())
            avg_posts = total_posts / total_months if total_months > 0 else 0
            most_active_month = max(monthly_mentions.items(), key=lambda x: x[1])[0] if monthly_mentions else None
            
            # 保存图表缓存
            chart_cache = {
                "chart_html": chart_html,
                "statistics": {
                    "most_active_month": most_active_month,
                    "average_posts_per_month": f"{avg_posts:.1f}",
                    "total_months": total_months,
                    "total_posts": total_posts
                }
            }
            
            # 保存到缓存目录
            charts_dir = os.path.join(self.cache_dir, "charts")
            os.makedirs(charts_dir, exist_ok=True)
            
            chart_file = os.path.join(charts_dir, f"{platform}_{keyword}.json")
            with open(chart_file, 'w', encoding='utf-8') as f:
                json.dump(chart_cache, f, ensure_ascii=False, indent=2)
            
            st.success(f"📊 Generated trend chart for {platform}")
            
        except Exception as e:
            st.warning(f"⚠️ Could not generate trend chart for {platform}: {e}")
    
    def load_platform_data(self, platform: str, keyword: str) -> Dict[str, Any]:
        """加载平台数据"""
        file_path = os.path.join(self.cache_dir, platform, f"{keyword}.json")
        if not os.path.exists(file_path):
            return {"status": "no_data", "posts": []}
        
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
        # 优先使用缓存中已存储的URL
        if post.get('url'):
            return post.get('url')
        
        # 如果没有URL，则构建URL
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
                        # 处理不同的时间戳格式，按优先级排序
                        if ' ' in timestamp and 'UTC' in timestamp:
                            # 格式: 2025-10-04 09:02:33 UTC (最高优先级)
                            date_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S UTC')
                        elif 'T' in timestamp:
                            # ISO格式: 2022-10-18T17:00:10+00:00
                            date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        elif ' ' in timestamp and '+' in timestamp:
                            # 格式: 2022-10-18 17:00:10+00:00
                            date_obj = datetime.fromisoformat(timestamp)
                        elif ' ' in timestamp:
                            # 格式: 2022-10-18 17:00:10
                            date_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        elif timestamp.isdigit() and len(timestamp) > 10:
                            # Discord snowflake ID格式: 长数字字符串
                            # Discord snowflake ID包含时间信息，需要转换
                            snowflake_id = int(timestamp)
                            # Discord snowflake ID的时间戳是毫秒，需要除以1000
                            # 并且需要加上Discord的epoch时间 (2015-01-01)
                            discord_epoch = 1420070400000  # 2015-01-01 00:00:00 UTC in milliseconds
                            timestamp_ms = (snowflake_id >> 22) + discord_epoch
                            date_obj = datetime.fromtimestamp(timestamp_ms / 1000)
                        else:
                            # 尝试其他格式
                            date_obj = datetime.fromisoformat(timestamp)
                        break
                    except Exception as e:
                        print(f"Error parsing timestamp '{timestamp}': {e}")
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

# Discord special display function removed - not needed for new keyword analysis

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
    # 尝试两种文件名格式
    chart_files = [
        f"data/cache/charts/{platform}_{keyword}.json",
        f"data/cache/charts/{platform}_{keyword}_trend.json"
    ]
    
    for chart_file in chart_files:
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
    
    # 首先显示原始数据表格
    monthly_mentions = metrics.get('monthly_mentions', {})
    if monthly_mentions:
        st.markdown("**Raw Monthly Data**")
        
        # 准备表格数据
        months = sorted(monthly_mentions.keys())
        table_data = []
        for month in months:
            table_data.append({
                "Month": month,
                "Posts": monthly_mentions[month]
            })
        
        # 显示表格
        df = pd.DataFrame(table_data)
        st.dataframe(df, width='stretch')
        
        # 显示统计信息
        total_posts = sum(monthly_mentions.values())
        avg_posts = total_posts / len(months) if months else 0
        most_active_month = max(monthly_mentions.items(), key=lambda x: x[1])[0] if monthly_mentions else None
        
        st.markdown("**Monthly Statistics**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Posts", total_posts)
        with col2:
            st.metric("Average/Month", f"{avg_posts:.1f}")
        with col3:
            st.metric("Most Active Month", most_active_month or 'N/A')
        
        st.markdown("**Trend Chart**")
    
    # 尝试加载缓存的图表
    cached_chart = load_cached_chart(platform, keyword)
    
    if cached_chart:
        # 尝试从缓存的HTML中提取Plotly数据并重新创建图表
        try:
            # 从HTML中提取数据并重新创建Plotly图表
            monthly_mentions = metrics.get('monthly_mentions', {})
            if monthly_mentions:
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
                
                st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
            else:
                # 回退到HTML显示
                chart_html = cached_chart['chart_html']
                if 'plotly.js' not in chart_html.lower():
                    plotly_js = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
                    chart_html = chart_html.replace('<head>', f'<head>{plotly_js}')
                st.components.v1.html(chart_html, height=450)
        except Exception as e:
            st.error(f"Error displaying chart: {e}")
            # 回退到HTML显示
            chart_html = cached_chart['chart_html']
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
        
        # 确保有数据才创建图表
        if not months or not counts:
            st.info("No monthly trend data available")
            return
        
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
        
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        
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
    st.title("BuzzScope: Where technology speaks, and you feel the echo")
    st.markdown("---")
    
    # 初始化分析器
    analyzer = SimpleHistoricalAnalyzer()
    
    # 侧边栏配置
    st.sidebar.header("Analysis Configuration")
    
    # 关键词选择
    st.sidebar.subheader("Keywords")
    
    # 统一的关键词输入
    keyword_input = st.sidebar.text_input(
        "Enter keywords (comma-separated):",
        value="ai, iot, mqtt, unified_namespace",
        placeholder="e.g., ai, blockchain, python, machine learning",
        help="Enter keywords separated by commas. Default keywords are pre-filled."
    )
    
    # 解析关键词
    if keyword_input:
        selected_keywords = [kw.strip() for kw in keyword_input.split(',') if kw.strip()]
    else:
        selected_keywords = []
    
    # 数据收集按钮
    collect_data = False
    if selected_keywords:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Data Status**")
        
        # 检查每个关键词的数据状态
        keywords_to_collect = []
        for keyword in selected_keywords:
            # 检查是否已有缓存数据
            has_cached_data = any(
                analyzer.load_platform_data(platform, keyword).get("posts") or 
                analyzer.load_platform_data(platform, keyword).get("metrics")
                for platform in ["hackernews", "reddit", "youtube"]
            )
            
            if has_cached_data:
                st.sidebar.success(f"✅ '{keyword}' - cached")
            else:
                st.sidebar.warning(f"⚠️ '{keyword}' - needs collection")
                keywords_to_collect.append(keyword)
        
        # 如果有需要收集的关键词，显示收集按钮
        if keywords_to_collect:
            st.sidebar.info(f"Need to collect data for: {', '.join(keywords_to_collect)}")
            if st.sidebar.button("🚀 Collect Missing Data", type="primary"):
                collect_data = True
    
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
    
    # 处理数据收集
    if collect_data and keywords_to_collect:
        st.markdown("---")
        st.subheader(f"🚀 Collecting Data for: {', '.join(keywords_to_collect)}")
        st.info("⏱️ Data collection may take 2-7 minutes per keyword. Please be patient...")
        
        all_success = True
        for keyword in keywords_to_collect:
            st.write(f"📊 Collecting data for '{keyword}'...")
            results = analyzer.collect_real_data(keyword)
            
            if results["status"] == "completed":
                st.success(f"✅ Data collection completed for '{keyword}'!")
            else:
                st.error(f"❌ Data collection failed for '{keyword}'")
                all_success = False
        
        if all_success:
            st.success("🎉 All data collection completed!")
            st.info("🔄 Refreshing page to show new data...")
            st.rerun()
        else:
            st.error("❌ Some data collection failed. Please check the error messages above.")
    
    # 主内容区域
    if analysis_type == "Single Keyword Analysis":
        display_single_keyword_analysis(analyzer, selected_keywords, selected_platforms)
    elif analysis_type == "Cross-Platform Comparison":
        display_cross_platform_comparison(analyzer, selected_keywords, selected_platforms)

def display_single_keyword_analysis(analyzer, keywords, platforms):
    """显示单关键词分析"""
    # 如果只有一个关键词，直接分析
    if len(keywords) == 1:
        selected_keyword = keywords[0]
    else:
        # 如果有多个关键词，让用户选择一个
        selected_keyword = st.selectbox(
            "Select a keyword to analyze:",
            keywords,
            help="Choose one keyword from the list to perform detailed analysis"
        )
        if not selected_keyword:
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
            
            # 平台常规处理
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
        
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        
        # 显示详细数据表
        st.write("### Detailed Comparison")
        st.dataframe(df, width='stretch')

if __name__ == "__main__":
    main()
