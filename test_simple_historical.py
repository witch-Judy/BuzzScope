"""
简单测试历史数据分析功能
"""

import json
import os
from datetime import datetime
from collections import Counter

def test_data_loading():
    """测试数据加载"""
    print("🧪 测试数据加载...")
    
    cache_dir = "data/cache"
    platforms = ["reddit", "youtube", "discord"]
    keywords = ["ai", "iot", "mqtt", "unified_namespace"]
    
    total_posts = 0
    for platform in platforms:
        platform_posts = 0
        for keyword in keywords:
            file_path = os.path.join(cache_dir, platform, f"{keyword}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        posts = data.get('total_posts', 0)
                        platform_posts += posts
                        total_posts += posts
                        print(f"  {platform}/{keyword}: {posts} posts")
                except Exception as e:
                    print(f"  Error loading {file_path}: {e}")
        
        print(f"  {platform} total: {platform_posts} posts")
    
    print(f"\n📊 总计: {total_posts} posts")
    return total_posts > 0

def test_metrics_calculation():
    """测试指标计算"""
    print("\n📈 测试指标计算...")
    
    # 加载一个样本文件
    file_path = "data/cache/reddit/ai.json"
    if not os.path.exists(file_path):
        print("  ❌ 样本文件不存在")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        posts = data.get('posts', [])
        print(f"  📊 加载了 {len(posts)} 个帖子")
        
        if posts:
            # 计算基础指标
            total_posts = len(posts)
            total_interactions = 0
            authors = []
            
            for post in posts:
                # 计算互动数
                score = post.get('score', 0)
                comments = post.get('num_comments', 0)
                total_interactions += score + comments
                
                # 收集作者
                author = post.get('author', '')
                if author:
                    authors.append(author)
            
            unique_authors = len(set(authors))
            
            print(f"    - 总帖子数: {total_posts}")
            print(f"    - 总互动数: {total_interactions}")
            print(f"    - 独特作者数: {unique_authors}")
            
            # 计算Top贡献者
            author_counts = Counter(authors)
            top_contributors = author_counts.most_common(5)
            print(f"    - Top贡献者: {top_contributors}")
            
            return True
        else:
            print("  ❌ 没有帖子数据")
            return False
            
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False

def test_trend_analysis():
    """测试趋势分析"""
    print("\n📈 测试趋势分析...")
    
    file_path = "data/cache/reddit/ai.json"
    if not os.path.exists(file_path):
        print("  ❌ 样本文件不存在")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        posts = data.get('posts', [])
        if not posts:
            print("  ❌ 没有帖子数据")
            return False
        
        # 计算每日提及
        daily_mentions = {}
        for post in posts:
            created_at = post.get('created_at', '')
            if created_at:
                try:
                    # 解析日期
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%Y-%m-%d')
                    daily_mentions[date_str] = daily_mentions.get(date_str, 0) + 1
                except:
                    pass
        
        print(f"  📅 每日提及数: {len(daily_mentions)} 天")
        if daily_mentions:
            max_day = max(daily_mentions.items(), key=lambda x: x[1])
            print(f"  🔥 最活跃的一天: {max_day[0]} ({max_day[1]} 个帖子)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试历史数据分析功能...")
    
    # 测试数据加载
    data_ok = test_data_loading()
    
    # 测试指标计算
    metrics_ok = test_metrics_calculation()
    
    # 测试趋势分析
    trend_ok = test_trend_analysis()
    
    print("\n📋 测试结果:")
    print(f"  📊 数据加载: {'✅' if data_ok else '❌'}")
    print(f"  📈 指标计算: {'✅' if metrics_ok else '❌'}")
    print(f"  📅 趋势分析: {'✅' if trend_ok else '❌'}")
    
    if data_ok and metrics_ok and trend_ok:
        print("\n🎉 所有测试通过！历史数据分析功能正常")
    else:
        print("\n⚠️ 部分测试失败，需要检查")

if __name__ == "__main__":
    main()
