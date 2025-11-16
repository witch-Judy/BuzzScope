"""
Multi-Agent Analytics App - Port 8506
多Agent分析应用 - 8506端口
"""

import streamlit as st
import json
import os
import time
import threading
import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Import the scheduler
from aiAnalytics.agent_scheduler import AgentScheduler

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="BuzzScope Multi-Agent Analytics",
    page_icon="🤖",
    layout="wide"
)

# Initialize scheduler
@st.cache_resource
def get_scheduler():
    return AgentScheduler()

class DataCollector:
    """数据收集器 - 从8503复制过来的逻辑"""
    
    def __init__(self):
        self.platforms = ["hackernews", "reddit", "youtube"]
    
    def _calculate_heat_score(self, post: Dict, platform: str) -> float:
        """计算热度分数"""
        if platform == 'reddit':
            return post.get('score', 0) + post.get('num_comments', 0)
        elif platform == 'youtube':
            view_count = (post.get('view_count', 0) or 0)
            like_count = (post.get('like_count', 0) or 0)
            comment_count = (post.get('comment_count', 0) or 0)
            return (view_count // 100) + like_count + comment_count
        elif platform == 'hackernews':
            return post.get('score', 0) + post.get('descendants', 0)
        else:
            return 0
    
    def get_hackernews_posts(self, keyword: str, hours_back: int = 24) -> List[Dict]:
        """获取Hacker News最近的热门帖子"""
        try:
            response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json')
            if response.status_code != 200:
                return []
            
            story_ids = response.json()[:100]
            posts = []
            
            for story_id in story_ids:
                try:
                    story_response = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json')
                    if story_response.status_code == 200:
                        story = story_response.json()
                        
                        # 精准匹配关键词
                        title = story.get('title', '').lower()
                        text = story.get('text', '').lower() if story.get('text') else ''
                        keyword_lower = keyword.lower()
                        
                        keyword_pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                        
                        if re.search(keyword_pattern, title) or re.search(keyword_pattern, text):
                            story_time = datetime.fromtimestamp(story.get('time', 0))
                            if story_time >= datetime.now() - timedelta(hours=24):
                                posts.append({
                                    'platform': 'hackernews',
                                    'title': story.get('title', ''),
                                    'url': story.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                                    'author': story.get('by', ''),
                                    'score': story.get('score', 0),
                                    'comments': story.get('descendants', 0),
                                    'timestamp': story_time.isoformat(),
                                    'keyword': keyword,
                                    'heat_score': self._calculate_heat_score(story, 'hackernews')
                                })
                except Exception:
                    continue
            
            return posts
        except Exception as e:
            st.error(f"Error fetching Hacker News posts: {e}")
            return []
    
    def get_reddit_posts(self, keyword: str, hours_back: int = 24) -> List[Dict]:
        """获取Reddit最近的热门帖子"""
        try:
            url = f"https://www.reddit.com/search.json?q={keyword}&sort=hot&limit=100&t=day"
            headers = {'User-Agent': 'BuzzScope Multi-Agent Analytics 1.0'}
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return []
            
            data = response.json()
            posts = []
            
            for post_data in data.get('data', {}).get('children', []):
                post = post_data.get('data', {})
                
                # 精准匹配关键词
                title = post.get('title', '').lower()
                selftext = post.get('selftext', '').lower() if post.get('selftext') else ''
                keyword_lower = keyword.lower()
                
                keyword_pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                
                if re.search(keyword_pattern, title) or re.search(keyword_pattern, selftext):
                    post_time = datetime.fromtimestamp(post.get('created_utc', 0))
                    if post_time >= datetime.now() - timedelta(hours=24):
                        posts.append({
                            'platform': 'reddit',
                            'title': post.get('title', ''),
                            'url': f"https://reddit.com{post.get('permalink', '')}",
                            'author': post.get('author', ''),
                            'score': post.get('score', 0),
                            'comments': post.get('num_comments', 0),
                            'timestamp': post_time.isoformat(),
                            'keyword': keyword,
                            'heat_score': self._calculate_heat_score(post, 'reddit')
                        })
            
            return posts
        except Exception as e:
            st.error(f"Error fetching Reddit posts: {e}")
            return []
    
    def get_youtube_videos(self, keyword: str, hours_back: int = 24) -> List[Dict]:
        """获取YouTube最近的热门视频"""
        try:
            api_key = os.getenv('YOUTUBE_API_KEY')
            if not api_key:
                st.warning("YouTube API key not configured")
                return []
            
            # 搜索视频
            search_url = "https://www.googleapis.com/youtube/v3/search"
            search_params = {
                'part': 'snippet',
                'q': keyword,
                'type': 'video',
                'order': 'relevance',
                'maxResults': 50,
                'publishedAfter': (datetime.now() - timedelta(hours=24)).isoformat() + 'Z',
                'key': api_key
            }
            
            response = requests.get(search_url, params=search_params)
            if response.status_code != 200:
                return []
            
            search_data = response.json()
            video_ids = [item['id']['videoId'] for item in search_data.get('items', [])]
            
            if not video_ids:
                return []
            
            # 获取视频详情
            videos_url = "https://www.googleapis.com/youtube/v3/videos"
            videos_params = {
                'part': 'snippet,statistics',
                'id': ','.join(video_ids),
                'key': api_key
            }
            
            videos_response = requests.get(videos_url, params=videos_params)
            if videos_response.status_code != 200:
                return []
            
            videos_data = videos_response.json()
            posts = []
            
            for video in videos_data.get('items', []):
                snippet = video.get('snippet', {})
                stats = video.get('statistics', {})
                
                # 精准匹配关键词
                title = snippet.get('title', '').lower()
                description = snippet.get('description', '').lower()
                keyword_lower = keyword.lower()
                
                keyword_pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                
                if re.search(keyword_pattern, title) or re.search(keyword_pattern, description):
                    posts.append({
                        'platform': 'youtube',
                        'title': snippet.get('title', ''),
                        'url': f"https://youtube.com/watch?v={video['id']}",
                        'author': snippet.get('channelTitle', ''),
                        'score': int(stats.get('viewCount', 0)),
                        'comments': int(stats.get('commentCount', 0)),
                        'timestamp': snippet.get('publishedAt', ''),
                        'keyword': keyword,
                        'heat_score': self._calculate_heat_score({
                            'view_count': int(stats.get('viewCount', 0)),
                            'like_count': int(stats.get('likeCount', 0)),
                            'comment_count': int(stats.get('commentCount', 0))
                        }, 'youtube')
                    })
            
            return posts
        except Exception as e:
            st.error(f"Error fetching YouTube videos: {e}")
            return []
    
    def collect_hot_posts(self, keywords: List[str], platforms: List[str]) -> Dict[str, Any]:
        """收集热门帖子数据"""
        all_hot_posts = []
        platform_posts = {}
        
        for keyword in keywords:
            for platform in platforms:
                if platform == 'hackernews':
                    posts = self.get_hackernews_posts(keyword, 24)
                elif platform == 'reddit':
                    posts = self.get_reddit_posts(keyword, 24)
                elif platform == 'youtube':
                    posts = self.get_youtube_videos(keyword, 24)
                else:
                    posts = []
                
                # 过滤热门帖子（热度分数 > 10）
                hot_posts = [post for post in posts if post.get('heat_score', 0) > 10]
                all_hot_posts.extend(hot_posts)
                
                if platform not in platform_posts:
                    platform_posts[platform] = []
                platform_posts[platform].extend(hot_posts)
        
        # 按热度分数排序
        all_hot_posts.sort(key=lambda x: x['heat_score'], reverse=True)
        for platform in platform_posts:
            platform_posts[platform].sort(key=lambda x: x['heat_score'], reverse=True)
        
        return {
            'total_posts': len(all_hot_posts),
            'keywords': keywords,
            'platform_posts': platform_posts,
            'all_posts': all_hot_posts,
            'timestamp': datetime.now().isoformat()
        }

def load_hot_posts_data() -> Optional[Dict[str, Any]]:
    """加载热帖数据"""
    ai_data_dir = "data/ai_analysis"
    if not os.path.exists(ai_data_dir):
        return None
    
    # 查找最新的热帖数据文件
    files = [f for f in os.listdir(ai_data_dir) if f.startswith("hot_posts_") and f.endswith(".json")]
    if not files:
        return None
    
    # 按修改时间排序，取最新的
    latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(ai_data_dir, x)))
    filepath = os.path.join(ai_data_dir, latest_file)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading hot posts data: {e}")
        return None

def display_agent_result(agent_name: str, result: Dict[str, Any]):
    """显示Agent结果"""
    if not result:
        st.info(f"No results for {agent_name}")
        return
    
    if "error" in result:
        st.error(f"Error in {agent_name}: {result['error']}")
        return
    
    st.subheader(f"🤖 {agent_name.replace('_', ' ').title()}")
    
    # 根据Agent类型显示不同内容
    if agent_name == "title":
        if "headline" in result:
            st.markdown(f"**📰 Headline:** {result['headline']}")
        if "reasoning" in result:
            st.markdown(f"**💭 Reasoning:** {result['reasoning']}")
        if "keywords" in result:
            st.markdown(f"**🏷️ Keywords:** {result['keywords']}")
    
    elif agent_name == "trends":
        if "trends" in result:
            for i, trend in enumerate(result["trends"], 1):
                with st.expander(f"Trend {i}: {trend.get('name', 'Unknown')}"):
                    if "description" in trend:
                        st.write(f"**Description:** {trend['description']}")
                    if "evidence" in trend:
                        st.write(f"**Evidence:** {trend['evidence']}")
                    if "impact" in trend:
                        st.write(f"**Impact:** {trend['impact']}")
        if "summary" in result:
            st.markdown(f"**📊 Summary:** {result['summary']}")
    
    elif agent_name == "twitter":
        if "twitter_content" in result:
            st.markdown("**🐦 Twitter Content:**")
            st.code(result["twitter_content"], language="text")
            st.caption(f"Character count: {result.get('character_count', 0)}")
        if "selected_posts" in result:
            st.markdown("**📋 Selected Posts:**")
            for post in result["selected_posts"]:
                st.write(f"• {post}")
        if "hashtags" in result:
            st.markdown(f"**#️⃣ Hashtags:** {result['hashtags']}")
    
    elif agent_name == "linkedin":
        if "linkedin_content" in result:
            st.markdown("**💼 LinkedIn Content:**")
            st.code(result["linkedin_content"], language="text")
            st.caption(f"Character count: {result.get('character_count', 0)}")
        if "selected_posts" in result:
            st.markdown("**📋 Selected Posts:**")
            for post in result["selected_posts"]:
                st.write(f"• {post}")
        if "key_insights" in result:
            st.markdown(f"**💡 Key Insights:** {result['key_insights']}")
    
    elif agent_name == "xiaohongshu":
        if "xiaohongshu_content" in result:
            st.markdown("**📱 Xiaohongshu Content:**")
            st.code(result["xiaohongshu_content"], language="text")
            st.caption(f"Character count: {result.get('character_count', 0)}")
        if "selected_posts" in result:
            st.markdown("**📋 Selected Posts:**")
            for post in result["selected_posts"]:
                st.write(f"• {post}")
        if "lifestyle_benefits" in result:
            st.markdown(f"**✨ Lifestyle Benefits:** {result['lifestyle_benefits']}")

def main():
    st.title("🤖 BuzzScope Multi-Agent Analytics")
    st.markdown("**Intelligent content generation using collaborative AI agents**")
    st.markdown("---")
    
    scheduler = get_scheduler()
    data_collector = DataCollector()
    
    # Sidebar for controls
    st.sidebar.header("🎛️ Controls")
    
    # Data collection section
    st.sidebar.subheader("📊 Data Collection")
    
    # Keywords input
    keywords_input = st.sidebar.text_input(
        "Keywords (comma-separated):",
        value="ai,iot,mqtt",
        help="Enter keywords separated by commas"
    )
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
    
    # Platform selection
    platforms = st.sidebar.multiselect(
        "Platforms:",
        ["hackernews", "reddit", "youtube"],
        default=["hackernews", "reddit", "youtube"]
    )
    
    # Collect data button
    if st.sidebar.button("📡 Collect Hot Posts Data", type="primary", use_container_width=True):
        if not keywords:
            st.sidebar.error("Please enter at least one keyword")
        elif not platforms:
            st.sidebar.error("Please select at least one platform")
        else:
            with st.spinner("Collecting hot posts data..."):
                posts_data = data_collector.collect_hot_posts(keywords, platforms)
                
                # Save data for later use
                ai_data_dir = "data/ai_analysis"
                os.makedirs(ai_data_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                keyword_str = "_".join(keywords)
                filename = f"hot_posts_{keyword_str}_{timestamp}.json"
                filepath = os.path.join(ai_data_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(posts_data, f, indent=2, ensure_ascii=False)
                
                st.sidebar.success(f"✅ Collected {posts_data['total_posts']} hot posts!")
                st.rerun()
    
    # Load hot posts data
    posts_data = load_hot_posts_data()
    
    if posts_data:
        st.sidebar.success("✅ Hot posts data loaded")
        st.sidebar.write(f"📊 Total posts: {posts_data.get('total_posts', 0)}")
        st.sidebar.write(f"🏷️ Keywords: {', '.join(posts_data.get('keywords', []))}")
        st.sidebar.write(f"📅 Date: {posts_data.get('timestamp', 'Unknown')}")
    else:
        st.sidebar.warning("⚠️ No hot posts data found")
        st.sidebar.write("Click 'Collect Hot Posts Data' to gather fresh data")
        return
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚀 Multi-Agent Analysis")
        
        # One-click collect and analyze button
        if st.button("🎯 Collect Data + Start Analysis", type="primary", use_container_width=True):
            if not keywords:
                st.error("Please enter keywords in the sidebar first")
            elif not platforms:
                st.error("Please select platforms in the sidebar first")
            elif not scheduler.is_running:
                def collect_and_analyze():
                    # Collect fresh data
                    fresh_posts_data = data_collector.collect_hot_posts(keywords, platforms)
                    
                    # Save data
                    ai_data_dir = "data/ai_analysis"
                    os.makedirs(ai_data_dir, exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    keyword_str = "_".join(keywords)
                    filename = f"hot_posts_{keyword_str}_{timestamp}.json"
                    filepath = os.path.join(ai_data_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(fresh_posts_data, f, indent=2, ensure_ascii=False)
                    
                    # Start analysis
                    scheduler.execute_multi_agent_analysis(fresh_posts_data)
                
                analysis_thread = threading.Thread(target=collect_and_analyze)
                analysis_thread.start()
                
                st.success("🚀 Data collection and multi-agent analysis started!")
                st.info("Collecting fresh data and starting agent collaboration...")
            else:
                st.warning("⚠️ Analysis is already running!")
        
        # Separate analysis button for existing data
        if st.button("🤖 Start Analysis (Use Existing Data)", use_container_width=True):
            if not scheduler.is_running:
                def run_analysis():
                    scheduler.execute_multi_agent_analysis(posts_data)
                
                analysis_thread = threading.Thread(target=run_analysis)
                analysis_thread.start()
                
                st.success("🚀 Multi-agent analysis started!")
                st.info("The agents are now collaborating to analyze your data...")
            else:
                st.warning("⚠️ Analysis is already running!")
    
    with col2:
        st.subheader("📊 Status")
        
        # Display current status
        status = scheduler.get_execution_status()
        
        if status["is_running"]:
            st.info("🔄 Analysis in progress...")
            st.write(f"Round: {status['current_round']}")
            
            # Show agent status
            for agent_name, agent_status in status["agents_status"].items():
                if agent_status["is_satisfied"]:
                    st.success(f"✅ {agent_name}")
                else:
                    st.info(f"🔄 {agent_name} (iter: {agent_status['iterations']})")
        else:
            st.info("⏸️ Ready to start")
    
    # Display results
    st.markdown("---")
    st.subheader("📋 Analysis Results")
    
    # Get latest results
    latest_results = scheduler.get_latest_results()
    
    if latest_results and latest_results.get("agent_results"):
        # Create tabs for each agent
        agent_names = list(latest_results["agent_results"].keys())
        tabs = st.tabs([name.replace('_', ' ').title() for name in agent_names])
        
        for i, (agent_name, result) in enumerate(latest_results["agent_results"].items()):
            with tabs[i]:
                display_agent_result(agent_name, result)
    else:
        st.info("No analysis results yet. Click 'Start Multi-Agent Analysis' to begin.")
    
    # Execution log
    if scheduler.execution_log:
        st.markdown("---")
        st.subheader("📝 Execution Log")
        
        with st.expander("View execution log", expanded=False):
            for log_entry in scheduler.execution_log[-20:]:  # Show last 20 entries
                timestamp = log_entry.get("timestamp", "")
                message = log_entry.get("message", "")
                agent_name = log_entry.get("agent_name", "")
                
                if agent_name:
                    st.write(f"`{timestamp}` **{agent_name}**: {message}")
                else:
                    st.write(f"`{timestamp}` {message}")
    
    # Auto-refresh when running
    if scheduler.is_running:
        time.sleep(3)
        st.rerun()

if __name__ == "__main__":
    main()
