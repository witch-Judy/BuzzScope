"""
Historical Data Visualization Components
专门用于历史数据分析的可视化组件
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
import json

class HistoricalVisualizer:
    """历史数据可视化器"""
    
    def __init__(self):
        self.color_palette = {
            'hackernews': '#FF6600',
            'reddit': '#FF4500', 
            'youtube': '#FF0000',
            'discord': '#5865F2'
        }
    
    def display_platform_overview(self, metrics: Dict[str, Any]):
        """显示平台概览"""
        st.subheader("📊 Platform Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
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
                help="该平台的总互动数（点赞、评论、分享等）"
            )
        
        with col3:
            st.metric(
                label="Unique Authors",
                value=metrics.get('unique_authors', 0),
                help="该平台的独特作者数"
            )
        
        with col4:
            date_range = metrics.get('date_range', {})
            if date_range:
                start_date = date_range.get('start', '')
                end_date = date_range.get('end', '')
                st.metric(
                    label="Date Range",
                    value=f"{start_date} to {end_date}",
                    help="数据的时间范围"
                )
    
    def display_top_contributors(self, contributors: List[Dict[str, Any]], platform: str):
        """显示Top贡献者"""
        if not contributors:
            st.info("No contributors found")
            return
        
        st.subheader(f"🏆 Top Contributors - {platform.title()}")
        
        # 创建DataFrame
        df = pd.DataFrame(contributors)
        
        # 显示表格，包含链接
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
    
    def display_top_posts(self, posts: List[Dict[str, Any]], platform: str):
        """显示Top帖子"""
        if not posts:
            st.info("No posts found")
            return
        
        st.subheader(f"🔥 Top Posts - {platform.title()}")
        
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
    
    def display_trend_analysis(self, daily_mentions: Dict[str, int], weekly_mentions: Dict[str, int], platform: str):
        """显示趋势分析"""
        st.subheader(f"📈 Trend Analysis - {platform.title()}")
        
        if not daily_mentions and not weekly_mentions:
            st.info("No trend data available")
            return
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Daily Mentions', 'Weekly Mentions'),
            vertical_spacing=0.1
        )
        
        # 每日提及图
        if daily_mentions:
            dates = sorted(daily_mentions.keys())
            counts = [daily_mentions[date] for date in dates]
            
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=counts,
                    mode='lines+markers',
                    name='Daily',
                    line=dict(color=self.color_palette.get(platform, '#000000'))
                ),
                row=1, col=1
            )
        
        # 每周提及图
        if weekly_mentions:
            weeks = sorted(weekly_mentions.keys())
            counts = [weekly_mentions[week] for week in weeks]
            
            fig.add_trace(
                go.Scatter(
                    x=weeks,
                    y=counts,
                    mode='lines+markers',
                    name='Weekly',
                    line=dict(color=self.color_palette.get(platform, '#000000'))
                ),
                row=2, col=1
            )
        
        fig.update_layout(
            height=600,
            showlegend=False,
            title=f"Trend Analysis for {platform.title()}"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def display_keyword_comparison(self, comparison_metrics: Dict[str, Any]):
        """显示关键词对比"""
        st.subheader("🔄 Keyword Comparison")
        
        # 平台总计对比
        st.write("### Platform Totals")
        
        platform_data = comparison_metrics.get('platform_totals', {})
        if platform_data:
            # 创建对比图
            platforms = list(platform_data.keys())
            posts = [platform_data[p]['total_posts'] for p in platforms]
            interactions = [platform_data[p]['total_interactions'] for p in platforms]
            authors = [platform_data[p]['unique_authors'] for p in platforms]
            
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=('Total Posts', 'Total Interactions', 'Unique Authors'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]]
            )
            
            colors = [self.color_palette.get(p, '#000000') for p in platforms]
            
            fig.add_trace(
                go.Bar(x=platforms, y=posts, name='Posts', marker_color=colors),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(x=platforms, y=interactions, name='Interactions', marker_color=colors),
                row=1, col=2
            )
            
            fig.add_trace(
                go.Bar(x=platforms, y=authors, name='Authors', marker_color=colors),
                row=1, col=3
            )
            
            fig.update_layout(
                height=400,
                showlegend=False,
                title="Cross-Platform Comparison"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 关键词排名
        st.write("### Keyword Rankings")
        top_keywords = comparison_metrics.get('top_keywords', [])
        if top_keywords:
            keywords, counts = zip(*top_keywords)
            
            fig = go.Figure(data=[
                go.Bar(x=list(keywords), y=list(counts), marker_color='lightblue')
            ])
            
            fig.update_layout(
                title="Total Mentions by Keyword",
                xaxis_title="Keywords",
                yaxis_title="Total Posts"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 跨平台洞察
        insights = comparison_metrics.get('cross_platform_insights', [])
        if insights:
            st.write("### Cross-Platform Insights")
            for insight in insights:
                st.info(insight)
    
    def display_platform_specific_analysis(self, platform_metrics: Dict[str, Any], platform: str):
        """显示平台特定分析"""
        st.header(f"📱 {platform.title()} Analysis")
        
        # 平台概览
        self.display_platform_overview(platform_metrics)
        
        # Top贡献者
        self.display_top_contributors(platform_metrics.get('top_contributors', []), platform)
        
        # Top帖子
        self.display_top_posts(platform_metrics.get('top_posts', []), platform)
        
        # 趋势分析
        self.display_trend_analysis(
            platform_metrics.get('daily_mentions', {}),
            platform_metrics.get('weekly_mentions', {}),
            platform
        )
    
    def display_multi_keyword_analysis(self, keyword_results: Dict[str, Dict[str, Any]]):
        """显示多关键词分析"""
        st.header("🔍 Multi-Keyword Analysis")
        
        # 选择要显示的关键词
        available_keywords = list(keyword_results.keys())
        selected_keywords = st.multiselect(
            "Select keywords to compare:",
            available_keywords,
            default=available_keywords[:2] if len(available_keywords) >= 2 else available_keywords
        )
        
        if not selected_keywords:
            st.warning("Please select at least one keyword")
            return
        
        # 创建对比数据
        comparison_data = []
        for keyword in selected_keywords:
            for platform, metrics in keyword_results[keyword].items():
                comparison_data.append({
                    'keyword': keyword,
                    'platform': platform,
                    'posts': metrics.get('total_posts', 0),
                    'interactions': metrics.get('total_interactions', 0),
                    'authors': metrics.get('unique_authors', 0)
                })
        
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            
            # 创建对比图
            fig = px.bar(
                df, 
                x='platform', 
                y='posts', 
                color='keyword',
                title='Posts by Platform and Keyword',
                barmode='group'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示详细数据表
            st.write("### Detailed Comparison")
            st.dataframe(df, use_container_width=True)
