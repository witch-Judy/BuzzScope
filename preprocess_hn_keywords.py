#!/usr/bin/env python3
"""
预处理Hacker News关键词数据
将4个关键词的搜索结果预先计算并保存到cache目录
"""

import pandas as pd
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Any

def search_keyword_in_hn(keyword: str, df: pd.DataFrame, exact_match: bool = True) -> List[Dict[str, Any]]:
    """在Hacker News数据中搜索关键词"""
    print(f"🔍 搜索关键词: '{keyword}'")
    
    # 创建搜索条件
    if exact_match:
        # 精确匹配
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
    else:
        # 模糊匹配
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    
    # 搜索标题和文本
    title_matches = df['title'].fillna('').str.contains(pattern, na=False)
    text_matches = df['text'].fillna('').str.contains(pattern, na=False)
    
    # 合并匹配结果
    matches = title_matches | text_matches
    
    # 获取匹配的记录
    matched_df = df[matches].copy()
    
    print(f"  找到 {len(matched_df)} 个匹配")
    
    # 转换为字典列表
    results = []
    for _, row in matched_df.iterrows():
        result = {
            'platform': 'hackernews',
            'post_id': str(row['id']),
            'title': row['title'] if pd.notna(row['title']) else '',
            'content': row['text'] if pd.notna(row['text']) else '',
            'author': row['by'] if pd.notna(row['by']) else '',
            'score': int(row['score']) if pd.notna(row['score']) else 0,
            'descendants': int(row['descendants']) if pd.notna(row['descendants']) else 0,
            'type': row['type'] if pd.notna(row['type']) else '',
            'url': row['url'] if pd.notna(row['url']) else '',
            'created_at': row['timestamp'] if pd.notna(row['timestamp']) else '',
            'timestamp': row['timestamp'] if pd.notna(row['timestamp']) else ''
        }
        results.append(result)
    
    return results

def calculate_monthly_mentions(posts: List[Dict[str, Any]]) -> Dict[str, int]:
    """计算每月提及数"""
    monthly_counts = defaultdict(int)
    
    for post in posts:
        timestamp = post.get('timestamp', '')
        if timestamp:
            try:
                # 解析时间戳
                if isinstance(timestamp, str):
                    date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    date_obj = timestamp
                
                month_str = date_obj.strftime('%Y-%m')
                monthly_counts[month_str] += 1
            except:
                pass
    
    return dict(monthly_counts)

def calculate_metrics(posts: List[Dict[str, Any]], keyword: str) -> Dict[str, Any]:
    """计算指标"""
    if not posts:
        return {
            "platform": "hackernews",
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
    total_interactions = sum(post['score'] + post['descendants'] for post in posts)
    unique_authors = len(set(post['author'] for post in posts if post['author']))
    
    # 计算Top贡献者
    author_counts = Counter(post['author'] for post in posts if post['author'])
    top_contributors = [
        {
            "author": author,
            "post_count": count,
            "platform": "hackernews",
            "profile_url": f"https://news.ycombinator.com/user?id={author}"
        }
        for author, count in author_counts.most_common(10)
    ]
    
    # 计算Top帖子
    top_posts = sorted(posts, key=lambda x: x['score'] + x['descendants'], reverse=True)[:10]
    top_posts = [
        {
            "title": post['title'] or 'No title',
            "interactions": post['score'] + post['descendants'],
            "author": post['author'],
            "created_at": post['created_at'],
            "url": f"https://news.ycombinator.com/item?id={post['post_id']}",
            "platform": "hackernews"
        }
        for post in top_posts
    ]
    
    # 计算月度提及
    monthly_mentions = calculate_monthly_mentions(posts)
    
    return {
        "platform": "hackernews",
        "keyword": keyword,
        "total_posts": total_posts,
        "total_interactions": total_interactions,
        "unique_authors": unique_authors,
        "top_contributors": top_contributors,
        "top_posts": top_posts,
        "monthly_mentions": monthly_mentions
    }

def main():
    """主函数"""
    print("🚀 开始预处理Hacker News关键词数据...")
    
    # 检查parquet文件
    parquet_path = "data/Hackernews_raw/hackernews_2years.parquet"
    if not os.path.exists(parquet_path):
        print(f"❌ Parquet文件不存在: {parquet_path}")
        return
    
    # 加载数据
    print(f"📊 加载Hacker News数据: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    print(f"   总记录数: {len(df):,}")
    
    # 确保cache目录存在
    cache_dir = "data/cache/hackernews"
    os.makedirs(cache_dir, exist_ok=True)
    
    # 要处理的关键词
    keywords = ["ai", "iot", "mqtt", "unified_namespace"]
    
    for keyword in keywords:
        print(f"\n🔍 处理关键词: '{keyword}'")
        
        # 搜索关键词
        posts = search_keyword_in_hn(keyword, df, exact_match=True)
        
        # 计算指标
        metrics = calculate_metrics(posts, keyword)
        
        # 保存到cache
        cache_file = os.path.join(cache_dir, f"{keyword}.json")
        
        cache_data = {
            "keyword": keyword,
            "platform": "hackernews",
            "data_source": "parquet",
            "collection_date": datetime.now().isoformat(),
            "total_posts": len(posts),
            "posts": posts,
            "metrics": metrics
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 已保存到: {cache_file}")
        print(f"   📊 统计: {metrics['total_posts']} 帖子, {metrics['total_interactions']} 互动, {metrics['unique_authors']} 作者")
        
        # 显示月度分布
        if metrics['monthly_mentions']:
            print(f"   📅 月度分布: {len(metrics['monthly_mentions'])} 个月")
            top_months = sorted(metrics['monthly_mentions'].items(), key=lambda x: x[1], reverse=True)[:3]
            for month, count in top_months:
                print(f"      {month}: {count} 帖子")
    
    print(f"\n✅ 预处理完成！所有关键词数据已保存到 {cache_dir}")
    print("现在Streamlit应用可以直接使用缓存数据，无需实时搜索parquet文件。")

if __name__ == "__main__":
    main()
