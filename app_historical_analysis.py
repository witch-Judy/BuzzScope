"""
BuzzScope Historical Analysis App
专门用于历史数据分析的Streamlit应用
"""

import streamlit as st
import sys
import os
from datetime import datetime

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.historical_analysis_v2 import HistoricalAnalysisV2
from src.visualization.historical_visualizer import HistoricalVisualizer

# 页面配置
st.set_page_config(
    page_title="BuzzScope - Historical Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化服务
@st.cache_resource
def get_analysis_service():
    return HistoricalAnalysisV2()

@st.cache_resource
def get_visualizer():
    return HistoricalVisualizer()

def main():
    st.title("📊 BuzzScope - Historical Analysis")
    st.markdown("---")
    
    # 获取服务实例
    analysis_service = get_analysis_service()
    visualizer = get_visualizer()
    
    # 侧边栏配置
    st.sidebar.header("🔧 Analysis Configuration")
    
    # 关键词选择
    default_keywords = ["ai", "iot", "mqtt", "unified_namespace"]
    selected_keywords = st.sidebar.multiselect(
        "Select Keywords:",
        default_keywords,
        default=default_keywords
    )
    
    # 平台选择
    available_platforms = ["hackernews", "reddit", "youtube", "discord"]
    selected_platforms = st.sidebar.multiselect(
        "Select Platforms:",
        available_platforms,
        default=available_platforms
    )
    
    # 分析类型选择
    analysis_type = st.sidebar.selectbox(
        "Analysis Type:",
        ["Single Keyword Analysis", "Multi-Keyword Comparison", "Platform-Specific Analysis"]
    )
    
    if not selected_keywords:
        st.warning("Please select at least one keyword")
        return
    
    if not selected_platforms:
        st.warning("Please select at least one platform")
        return
    
    # 主内容区域
    if analysis_type == "Single Keyword Analysis":
        display_single_keyword_analysis(analysis_service, visualizer, selected_keywords, selected_platforms)
    elif analysis_type == "Multi-Keyword Comparison":
        display_multi_keyword_comparison(analysis_service, visualizer, selected_keywords, selected_platforms)
    elif analysis_type == "Platform-Specific Analysis":
        display_platform_specific_analysis(analysis_service, visualizer, selected_keywords, selected_platforms)

def display_single_keyword_analysis(analysis_service, visualizer, keywords, platforms):
    """显示单关键词分析"""
    st.header("🔍 Single Keyword Analysis")
    
    # 选择关键词
    selected_keyword = st.selectbox("Select a keyword:", keywords)
    
    if not selected_keyword:
        return
    
    # 显示加载状态
    with st.spinner(f"Analyzing {selected_keyword}..."):
        # 分析关键词
        results = analysis_service.analyze_keyword(selected_keyword)
    
    # 过滤选中的平台
    filtered_results = {platform: results[platform] for platform in platforms if platform in results}
    
    if not filtered_results:
        st.error("No data found for the selected platforms")
        return
    
    # 显示总体统计
    st.subheader(f"📈 Overall Statistics for '{selected_keyword}'")
    
    total_posts = sum(metrics.total_posts for metrics in filtered_results.values())
    total_interactions = sum(metrics.total_interactions for metrics in filtered_results.values())
    total_authors = len(set(
        author.author for metrics in filtered_results.values() 
        for author in metrics.top_contributors
    ))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Posts", total_posts)
    with col2:
        st.metric("Total Interactions", total_interactions)
    with col3:
        st.metric("Unique Authors", total_authors)
    
    # 显示各平台分析
    for platform, metrics in filtered_results.items():
        if metrics.total_posts > 0:
            visualizer.display_platform_specific_analysis(metrics.__dict__, platform)
        else:
            st.info(f"No data available for {platform}")

def display_multi_keyword_comparison(analysis_service, visualizer, keywords, platforms):
    """显示多关键词对比"""
    st.header("🔄 Multi-Keyword Comparison")
    
    # 显示加载状态
    with st.spinner("Analyzing keywords..."):
        # 进行对比分析
        comparison_metrics = analysis_service.compare_keywords(keywords)
    
    # 显示对比结果
    visualizer.display_keyword_comparison(comparison_metrics.__dict__)
    
    # 显示详细的多关键词分析
    st.subheader("📊 Detailed Multi-Keyword Analysis")
    
    # 收集所有关键词的数据
    all_results = {}
    for keyword in keywords:
        all_results[keyword] = analysis_service.analyze_keyword(keyword)
    
    # 过滤选中的平台
    filtered_results = {}
    for keyword, results in all_results.items():
        filtered_results[keyword] = {platform: results[platform] for platform in platforms if platform in results}
    
    visualizer.display_multi_keyword_analysis(filtered_results)

def display_platform_specific_analysis(analysis_service, visualizer, keywords, platforms):
    """显示平台特定分析"""
    st.header("📱 Platform-Specific Analysis")
    
    # 选择平台
    selected_platform = st.selectbox("Select a platform:", platforms)
    
    if not selected_platform:
        return
    
    # 显示加载状态
    with st.spinner(f"Analyzing {selected_platform}..."):
        # 收集该平台所有关键词的数据
        platform_results = {}
        for keyword in keywords:
            results = analysis_service.analyze_keyword(keyword)
            if selected_platform in results:
                platform_results[keyword] = results[selected_platform]
    
    if not platform_results:
        st.error(f"No data found for {selected_platform}")
        return
    
    # 显示平台概览
    st.subheader(f"📊 {selected_platform.title()} Overview")
    
    total_posts = sum(metrics.total_posts for metrics in platform_results.values())
    total_interactions = sum(metrics.total_interactions for metrics in platform_results.values())
    total_authors = len(set(
        author.author for metrics in platform_results.values() 
        for author in metrics.top_contributors
    ))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Posts", total_posts)
    with col2:
        st.metric("Total Interactions", total_interactions)
    with col3:
        st.metric("Unique Authors", total_authors)
    
    # 显示各关键词在该平台的表现
    st.subheader(f"🔍 Keywords Performance on {selected_platform.title()}")
    
    keyword_data = []
    for keyword, metrics in platform_results.items():
        keyword_data.append({
            'Keyword': keyword,
            'Posts': metrics.total_posts,
            'Interactions': metrics.total_interactions,
            'Authors': metrics.unique_authors
        })
    
    if keyword_data:
        import pandas as pd
        df = pd.DataFrame(keyword_data)
        st.dataframe(df, use_container_width=True)
        
        # 创建可视化
        import plotly.express as px
        
        fig = px.bar(
            df, 
            x='Keyword', 
            y='Posts',
            title=f'Posts by Keyword on {selected_platform.title()}',
            color='Posts',
            color_continuous_scale='viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 显示详细分析
    selected_keyword = st.selectbox("Select keyword for detailed analysis:", keywords)
    
    if selected_keyword and selected_keyword in platform_results:
        metrics = platform_results[selected_keyword]
        if metrics.total_posts > 0:
            visualizer.display_platform_specific_analysis(metrics.__dict__, selected_platform)

def display_data_status():
    """显示数据状态"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Data Status")
    
    # 检查数据文件
    cache_dir = "data/cache"
    platforms = ["hackernews", "reddit", "youtube", "discord"]
    keywords = ["ai", "iot", "mqtt", "unified_namespace"]
    
    for platform in platforms:
        platform_posts = 0
        for keyword in keywords:
            file_path = os.path.join(cache_dir, platform, f"{keyword}.json")
            if os.path.exists(file_path):
                try:
                    import json
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        platform_posts += data.get('total_posts', 0)
                except:
                    pass
        
        st.sidebar.metric(
            label=platform.title(),
            value=platform_posts,
            help=f"Total posts in {platform}"
        )

if __name__ == "__main__":
    # 显示数据状态
    display_data_status()
    
    # 运行主应用
    main()
