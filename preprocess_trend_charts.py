#!/usr/bin/env python3
"""
预处理月度趋势图表
为4个关键词×4个平台生成16张月度趋势图并缓存
"""

import json
import os
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any

def load_platform_data(platform: str, keyword: str, cache_dir: str = "data/cache") -> Dict[str, Any]:
    """加载平台数据"""
    file_path = os.path.join(cache_dir, platform, f"{keyword}.json")
    if not os.path.exists(file_path):
        return {"posts": []}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {"posts": []}

def calculate_monthly_mentions(posts: List[Dict[str, Any]]) -> Dict[str, int]:
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
                    if isinstance(timestamp, str):
                        if 'T' in timestamp:
                            # ISO格式: 2022-10-18T17:00:10+00:00
                            date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        elif ' ' in timestamp and '+' in timestamp:
                            # 格式: 2022-10-18 17:00:10+00:00
                            date_obj = datetime.fromisoformat(timestamp)
                        elif ' ' in timestamp and 'UTC' in timestamp:
                            # 格式: 2025-10-04 09:02:33 UTC
                            date_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S UTC')
                        elif ' ' in timestamp:
                            # 格式: 2022-10-18 17:00:10
                            date_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        else:
                            # 尝试其他格式
                            date_obj = datetime.fromisoformat(timestamp)
                    else:
                        # 如果已经是datetime对象
                        date_obj = timestamp
                    break
                except Exception as e:
                    continue
        
        if date_obj:
            month_str = date_obj.strftime('%Y-%m')
            monthly_counts[month_str] += 1
    
    return dict(monthly_counts)

def create_monthly_trend_chart(monthly_mentions: Dict[str, int], platform: str, keyword: str) -> str:
    """创建月度趋势图表并返回HTML"""
    if not monthly_mentions:
        # 创建空图表
        fig = go.Figure()
        fig.add_annotation(
            text="No monthly trend data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title=f"Monthly Mentions Trend - {platform.title()}",
            xaxis_title="Month",
            yaxis_title="Number of Posts",
            height=400,
            showlegend=False
        )
    else:
        # 创建趋势图
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
            title=f"Monthly Mentions Trend - {platform.title()}",
            xaxis_title="Month",
            yaxis_title="Number of Posts",
            height=400,
            showlegend=False
        )
    
    # 转换为HTML
    html = pio.to_html(fig, include_plotlyjs=False, div_id=f"chart_{platform}_{keyword}", config={'displayModeBar': False})
    return html

def generate_trend_statistics(monthly_mentions: Dict[str, int]) -> Dict[str, Any]:
    """生成趋势统计信息"""
    if not monthly_mentions:
        return {
            "most_active_month": None,
            "average_posts_per_month": 0,
            "total_months": 0,
            "total_posts": 0
        }
    
    total_months = len(monthly_mentions)
    total_posts = sum(monthly_mentions.values())
    avg_posts = total_posts / total_months if total_months > 0 else 0
    max_month = max(monthly_mentions.items(), key=lambda x: x[1]) if monthly_mentions else None
    
    return {
        "most_active_month": f"{max_month[0]} ({max_month[1]} posts)" if max_month else None,
        "average_posts_per_month": round(avg_posts, 1),
        "total_months": total_months,
        "total_posts": total_posts
    }

def main():
    """主函数"""
    print("🚀 开始预处理月度趋势图表...")
    
    # 配置
    platforms = ["hackernews", "reddit", "youtube", "discord"]
    keywords = ["ai", "iot", "mqtt", "unified_namespace"]
    cache_dir = "data/cache"
    charts_cache_dir = "data/cache/charts"
    
    # 确保图表缓存目录存在
    os.makedirs(charts_cache_dir, exist_ok=True)
    
    total_charts = len(platforms) * len(keywords)
    processed_charts = 0
    
    print(f"📊 将生成 {total_charts} 张图表 ({len(platforms)} 平台 × {len(keywords)} 关键词)")
    
    for platform in platforms:
        print(f"\n🔍 处理平台: {platform}")
        
        for keyword in keywords:
            print(f"  📈 生成图表: {keyword}")
            
            # 加载数据
            data = load_platform_data(platform, keyword, cache_dir)
            
            # 获取posts数据
            posts = data.get("posts", [])
            
            # 计算月度提及
            monthly_mentions = calculate_monthly_mentions(posts)
            
            # 生成趋势统计
            stats = generate_trend_statistics(monthly_mentions)
            
            # 创建图表
            chart_html = create_monthly_trend_chart(monthly_mentions, platform, keyword)
            
            # 保存图表数据
            chart_data = {
                "platform": platform,
                "keyword": keyword,
                "monthly_mentions": monthly_mentions,
                "statistics": stats,
                "chart_html": chart_html,
                "generated_at": datetime.now().isoformat()
            }
            
            # 保存到文件
            chart_file = os.path.join(charts_cache_dir, f"{platform}_{keyword}_trend.json")
            with open(chart_file, 'w', encoding='utf-8') as f:
                json.dump(chart_data, f, ensure_ascii=False, indent=2)
            
            processed_charts += 1
            print(f"    ✅ 已保存: {chart_file}")
            print(f"    📊 统计: {stats['total_posts']} 帖子, {stats['total_months']} 个月")
            if stats['most_active_month']:
                print(f"    🏆 最活跃月份: {stats['most_active_month']}")
    
    print(f"\n✅ 预处理完成！")
    print(f"📊 成功生成 {processed_charts}/{total_charts} 张图表")
    print(f"📁 图表缓存目录: {charts_cache_dir}")
    print("现在Streamlit前端可以直接调用预生成的图表，无需实时计算！")

if __name__ == "__main__":
    main()
