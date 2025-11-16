"""
Xiaohongshu (Little Red Book) Content Agent
小红书内容Agent - 生成适合小红书传播的内容
"""

from ..base_agent import BaseAgent
from typing import Dict, List, Any

class XiaohongshuAgent(BaseAgent):
    """小红书内容Agent"""
    
    def __init__(self):
        super().__init__(
            name="XiaohongshuContentCreator",
            role="Create engaging Xiaohongshu content for tech lifestyle and trends",
            max_iterations=5
        )
    
    def get_system_prompt(self) -> str:
        return """你是一个专业的小红书内容创作者，专门制作科技生活类内容，内容需要能调动起情绪。

核心技能：
- 用最地道的中文表达，朴实简洁真诚
- 了解小红书用户的真实需求和痛点
- 用生活化的语言解释晦涩的、高深的科技概念（但ai这种大家都知道的就不用解释了），让技术变得有趣易懂
- 创造有共鸣的内容，让用户想收藏和分享
- 用真实的体验和感受，避免过于官方或营销化的语言

你的目标是创作出真正接地气、有温度、让人愿意分享的科技生活内容。"""
    
    def get_task_prompt(self, posts_data: Dict[str, Any], other_agents_results: Dict[str, Any] = None) -> str:
        if other_agents_results is None:
            other_agents_results = {}
        
        total_posts = posts_data.get('total_posts', 0)
        keywords = posts_data.get('keywords', [])
        platform_posts = posts_data.get('platform_posts', {})
        
        prompt = f"""基于今天的科技热门帖子，创作小红书内容。要选择最贴近年轻人、最有实用价值或者最能调动大家情感的帖子，帖子需要朴实简洁真诚。

数据概览：
- 总热门帖子数：{total_posts}
- 关键词：{', '.join(keywords)}

各平台热门帖子："""

        for platform, posts in platform_posts.items():
            prompt += f"\n\n{platform.upper()} ({len(posts)}个帖子)："
            for i, post in enumerate(posts[:5], 1):
                prompt += f"\n{i}. {post['title']} (热度: {post['heat_score']:.1f})"
                if 'url' in post:
                    prompt += f" - {post['url']}"
        
        # Include other agents' insights if available
        if other_agents_results:
            prompt += "\n\n其他分析结果："
            for agent_name, result in other_agents_results.items():
                if result and 'summary' in result:
                    prompt += f"\n- {agent_name}: {result['summary']}"
        
        prompt += """

创作要求：
1. 选择3-5个最符合小红书调性的帖子（生活化、实用、有趣）
2. 用最地道的中文表达，朴实简洁真诚的中文重新包装这些内容
3. 写一篇完整的小红书帖
4. 语言要真实、有温度，避免官方腔调和营销化

重要提示：如果你对之前的结果满意，不需要修改，请回答"满意"并说明原因。否则，提供新的内容。

输出格式：
满意度：[满意/需要改进]
选择的帖子：
1. [用生活化语言重新包装的帖子内容] - [原链接]
2. [用生活化语言重新包装的帖子内容] - [原链接]
3. [用生活化语言重新包装的帖子内容] - [原链接]
[继续3-5个帖子，如果满意则写"无更新"]

小红书正文：
[你的完整小红书帖子内容，要像朋友分享一样自然真实，如果满意则写"无更新"]

生活价值：[这些内容如何改善日常生活]
目标用户：[谁会喜欢这些内容]
创作理由：[为什么这样写会受欢迎，如果满意则说明为什么满意]
"""
        
        return prompt
    
    def process_result(self, result: str) -> Dict[str, Any]:
        """处理小红书内容生成结果"""
        selected_posts = []
        xiaohongshu_content = ""
        lifestyle_benefits = ""
        target_audience = ""
        reasoning = ""
        
        lines = result.strip().split('\n')
        current_section = ""
        content_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('满意度：') or line.startswith('SATISFACTION:'):
                satisfaction = line.replace('满意度：', '').replace('SATISFACTION:', '').strip()
                agent_satisfied = satisfaction == '满意' or satisfaction.upper() == 'SATISFIED'
                continue
            elif line.startswith('选择的帖子：') or line.startswith('SELECTED POSTS:'):
                current_section = "posts"
                continue
            elif line.startswith('小红书正文：') or line.startswith('XIAOHONGSHU CONTENT:'):
                current_section = "content"
                # 获取标题行后的内容
                content_line = line.replace('小红书正文：', '').replace('XIAOHONGSHU CONTENT:', '').strip()
                if content_line:
                    content_lines.append(content_line)
                continue
            elif line.startswith('生活价值：') or line.startswith('LIFESTYLE BENEFITS:'):
                current_section = "benefits"
                lifestyle_benefits = line.replace('生活价值：', '').replace('LIFESTYLE BENEFITS:', '').strip()
                continue
            elif line.startswith('目标用户：') or line.startswith('TARGET AUDIENCE:'):
                current_section = "audience"
                target_audience = line.replace('目标用户：', '').replace('TARGET AUDIENCE:', '').strip()
                continue
            elif line.startswith('创作理由：') or line.startswith('REASONING:'):
                current_section = "reasoning"
                reasoning = line.replace('创作理由：', '').replace('REASONING:', '').strip()
                continue
            elif line and current_section == "posts" and line[0].isdigit():
                selected_posts.append(line)
            elif line and current_section == "content" and not line.startswith(('生活价值：', '目标用户：', '创作理由：', 'LIFESTYLE BENEFITS:', 'TARGET AUDIENCE:', 'REASONING:')):
                # 收集内容部分的所有行
                content_lines.append(line)
        
        # 合并所有内容行
        xiaohongshu_content = '\n'.join(content_lines).strip()
        
        return {
            "satisfaction": satisfaction,
            "selected_posts": selected_posts,
            "xiaohongshu_content": xiaohongshu_content,
            "lifestyle_benefits": lifestyle_benefits,
            "target_audience": target_audience,
            "reasoning": reasoning,
            "agent_satisfied": agent_satisfied,
            "character_count": len(xiaohongshu_content),
            "summary": f"Created Xiaohongshu content: {xiaohongshu_content[:50]}..." if not agent_satisfied else f"Satisfied with previous results: {reasoning}",
            "type": "xiaohongshu_content"
        }
