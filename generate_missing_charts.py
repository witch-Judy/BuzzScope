#!/usr/bin/env python3
"""
为已收集但缺少图表的数据生成趋势图表
"""

import os
import json
import sys
from datetime import datetime
from collections import defaultdict
import plotly.graph_objects as go

def calculate_monthly_mentions(posts):
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

def generate_chart_for_keyword(keyword):
    """为指定关键词生成图表"""
    cache_dir = "data/cache"
    charts_dir = os.path.join(cache_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    platforms = ["hackernews", "reddit", "youtube"]
    
    for platform in platforms:
        data_file = os.path.join(cache_dir, platform, f"{keyword}.json")
        
        if not os.path.exists(data_file):
            print(f"⚠️ No data file for {platform}: {data_file}")
            continue
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            posts = data.get('posts', [])
            if not posts:
                print(f"⚠️ No posts in {platform} data")
                continue
            
            # 计算月度数据
            monthly_mentions = calculate_monthly_mentions(posts)
            
            if not monthly_mentions:
                print(f"⚠️ No monthly data for {platform}")
                continue
            
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
            chart_file = os.path.join(charts_dir, f"{platform}_{keyword}.json")
            with open(chart_file, 'w', encoding='utf-8') as f:
                json.dump(chart_cache, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Generated chart for {platform}: {chart_file}")
            print(f"   📊 {total_posts} posts across {total_months} months")
            print(f"   📈 Most active: {most_active_month} ({monthly_mentions[most_active_month]} posts)")
            
        except Exception as e:
            print(f"❌ Error generating chart for {platform}: {e}")

def main():
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
    else:
        keyword = "machine learning"
    
    print(f"🚀 Generating charts for keyword: '{keyword}'")
    generate_chart_for_keyword(keyword)
    print("✅ Chart generation completed!")

if __name__ == "__main__":
    main()
