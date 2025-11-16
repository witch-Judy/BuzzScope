"""
AI Analysis Service for Hot Posts
使用OpenAI GPT分析热门帖子，生成社交媒体内容
"""

import os
import json
import openai
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIAnalyzer:
    """AI分析器，用于分析热帖并生成社交媒体内容"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # 清除可能的代理设置
        for key in list(os.environ.keys()):
            if 'proxy' in key.lower():
                del os.environ[key]
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # 确保AI分析数据目录存在
        self.ai_data_dir = "data/ai_analysis"
        os.makedirs(self.ai_data_dir, exist_ok=True)
    
    def analyze_hot_posts(self, hot_posts: List[Dict], keywords: List[str]) -> Dict[str, Any]:
        """
        分析热门帖子并生成AI摘要
        
        Args:
            hot_posts: 热门帖子列表
            keywords: 关键词列表
            
        Returns:
            包含分析结果的字典
        """
        if not hot_posts:
            return {"error": "No hot posts to analyze"}
        
        # 准备分析数据
        analysis_data = self._prepare_analysis_data(hot_posts, keywords)
        
        # 生成AI分析
        ai_analysis = self._generate_ai_analysis(analysis_data)
        
        # 保存分析结果
        self._save_analysis_result(ai_analysis, keywords)
        
        return ai_analysis
    
    def _prepare_analysis_data(self, hot_posts: List[Dict], keywords: List[str]) -> Dict[str, Any]:
        """准备分析数据"""
        # 按平台分组
        platform_posts = {}
        for post in hot_posts:
            platform = post.get('platform', 'unknown')
            if platform not in platform_posts:
                platform_posts[platform] = []
            platform_posts[platform].append({
                'title': post.get('title', ''),
                'url': post.get('url', ''),
                'heat_score': post.get('heat_score', 0),
                'score': post.get('score', 0),
                'comments': post.get('comments', 0),
                'keyword': post.get('keyword', '')
            })
        
        return {
            'keywords': keywords,
            'total_posts': len(hot_posts),
            'platform_posts': platform_posts,
            'analysis_date': datetime.now().isoformat()
        }
    
    def _generate_ai_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用OpenAI GPT生成分析"""
        try:
            # 构建提示词
            prompt = self._build_analysis_prompt(analysis_data)
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的科技趋势分析师，擅长将热门技术帖子分析成简洁、有趣的社交媒体内容。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            ai_content = response.choices[0].message.content
            
            # 解析AI回复
            return self._parse_ai_response(ai_content, analysis_data)
            
        except Exception as e:
            return {
                "error": f"AI analysis failed: {str(e)}",
                "analysis_data": analysis_data
            }
    
    def _build_analysis_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """构建分析提示词"""
        keywords = ", ".join(analysis_data['keywords'])
        total_posts = analysis_data['total_posts']
        
        prompt = f"""
请分析以下关于"{keywords}"的热门帖子数据，生成今日科技大事的社交媒体内容。

数据概览：
- 总热门帖子数：{total_posts}
- 关键词：{keywords}

各平台热门帖子：

"""
        
        for platform, posts in analysis_data['platform_posts'].items():
            prompt += f"\n{platform.upper()}平台 ({len(posts)}个热门帖子)：\n"
            for i, post in enumerate(posts[:5], 1):  # 只取前5个最热门的
                prompt += f"{i}. {post['title']} (热度: {post['heat_score']:.1f})\n"
        
        prompt += """

请生成以下格式的内容：

1. 【今日AI大事】标题（吸引眼球，不超过20字）

2. 【核心趋势】3-5个关键趋势点

3. 【社交媒体文案】
   - Twitter版本（280字符以内）
   - LinkedIn版本（专业版，可稍长）
   - 微博版本（140字符以内）

4. 【数据洞察】基于热度的数据分析

5. 【推荐阅读】3-5个最值得关注的帖子链接

要求：
- 内容要专业但易懂
- 突出技术趋势和商业价值
- 适合不同社交媒体平台的特点
- 包含具体的数据和链接
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_content: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析AI回复"""
        return {
            "ai_analysis": ai_content,
            "analysis_data": analysis_data,
            "generated_at": datetime.now().isoformat(),
            "model": "gpt-4"
        }
    
    def _save_analysis_result(self, analysis_result: Dict[str, Any], keywords: List[str]) -> str:
        """保存分析结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        keyword_str = "_".join(keywords)
        filename = f"ai_analysis_{keyword_str}_{timestamp}.json"
        filepath = os.path.join(self.ai_data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def get_latest_analysis(self, keywords: List[str]) -> Optional[Dict[str, Any]]:
        """获取最新的分析结果"""
        keyword_str = "_".join(keywords)
        pattern = f"ai_analysis_{keyword_str}_"
        
        # 查找匹配的文件
        matching_files = []
        if os.path.exists(self.ai_data_dir):
            for filename in os.listdir(self.ai_data_dir):
                if filename.startswith(pattern) and filename.endswith('.json'):
                    filepath = os.path.join(self.ai_data_dir, filename)
                    matching_files.append((filepath, os.path.getmtime(filepath)))
        
        if not matching_files:
            return None
        
        # 返回最新的文件
        latest_file = max(matching_files, key=lambda x: x[1])[0]
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading analysis file: {e}")
            return None
    
    def format_for_social_media(self, analysis_result: Dict[str, Any], platform: str = "twitter") -> str:
        """格式化分析结果为特定社交媒体平台"""
        if "error" in analysis_result:
            return f"分析失败: {analysis_result['error']}"
        
        ai_content = analysis_result.get("ai_analysis", "")
        
        # 根据平台提取相应内容
        if platform.lower() == "twitter":
            return self._extract_twitter_content(ai_content)
        elif platform.lower() == "linkedin":
            return self._extract_linkedin_content(ai_content)
        elif platform.lower() == "weibo":
            return self._extract_weibo_content(ai_content)
        else:
            return ai_content
    
    def _extract_twitter_content(self, content: str) -> str:
        """提取Twitter版本内容"""
        lines = content.split('\n')
        twitter_content = ""
        
        for line in lines:
            if "Twitter版本" in line or "twitter" in line.lower():
                # 找到Twitter版本后的内容
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    twitter_content = lines[idx + 1].strip()
                    break
        
        return twitter_content if twitter_content else content[:280]
    
    def _extract_linkedin_content(self, content: str) -> str:
        """提取LinkedIn版本内容"""
        lines = content.split('\n')
        linkedin_content = ""
        
        for line in lines:
            if "LinkedIn版本" in line or "linkedin" in line.lower():
                # 找到LinkedIn版本后的内容
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    linkedin_content = lines[idx + 1].strip()
                    break
        
        return linkedin_content if linkedin_content else content
    
    def _extract_weibo_content(self, content: str) -> str:
        """提取微博版本内容"""
        lines = content.split('\n')
        weibo_content = ""
        
        for line in lines:
            if "微博版本" in line or "weibo" in line.lower():
                # 找到微博版本后的内容
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    weibo_content = lines[idx + 1].strip()
                    break
        
        return weibo_content if weibo_content else content[:140]
