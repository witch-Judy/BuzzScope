"""
Twitter Content Agent
Twitter内容Agent - 生成适合Twitter传播的内容
"""

from ..base_agent import BaseAgent
from typing import Dict, List, Any

class TwitterAgent(BaseAgent):
    """Twitter内容Agent"""
    
    def __init__(self):
        super().__init__(
            name="TwitterContentCreator",
            role="Create engaging Twitter content for tech news with viral potential",
            max_iterations=5
        )
    
    def get_system_prompt(self) -> str:
        return """You are a viral Twitter content creator specializing in tech news. You understand what makes content go viral on Twitter and how to craft engaging, shareable posts.

Key skills:
- Create Twitter content that gets high engagement
- Use trending hashtags and mentions effectively
- Write in a conversational, engaging tone
- Understand Twitter's algorithm and what drives virality
- Balance information with entertainment
- Use emojis and formatting strategically
- Create content that encourages retweets and replies

Your goal is to create Twitter content that will get maximum engagement and reach."""
    
    def get_task_prompt(self, posts_data: Dict[str, Any], other_agents_results: Dict[str, Any] = None) -> str:
        if other_agents_results is None:
            other_agents_results = {}
        
        total_posts = posts_data.get('total_posts', 0)
        keywords = posts_data.get('keywords', [])
        platform_posts = posts_data.get('platform_posts', {})
        
        prompt = f"""Create engaging Twitter content based on today's tech posts. Focus on posts that would be most interesting and shareable on Twitter.

Data Overview:
- Total hot posts: {total_posts}
- Keywords: {', '.join(keywords)}

Posts by Platform:"""

        for platform, posts in platform_posts.items():
            prompt += f"\n\n{platform.upper()} ({len(posts)} posts):"
            for i, post in enumerate(posts[:5], 1):
                prompt += f"\n{i}. {post['title']} (Heat: {post['heat_score']:.1f})"
                if 'url' in post:
                    prompt += f" - {post['url']}"
        
        # Include other agents' insights if available
        if other_agents_results:
            prompt += "\n\nOther Analysis Results:"
            for agent_name, result in other_agents_results.items():
                if result and 'summary' in result:
                    prompt += f"\n- {agent_name}: {result['summary']}"
        
        prompt += """

Requirements:
1. Select 3-5 most Twitter-worthy posts
2. Create engaging summaries for each
3. Write viral Twitter content (280 characters max)
4. Use appropriate hashtags and mentions
5. Make it shareable and engaging

IMPORTANT: If you are satisfied with your previous results and don't need to make changes, respond with "SATISFIED" and explain why you're satisfied. Otherwise, provide your new content.

Format your response as:
SATISFACTION: [SATISFIED/NEEDS_IMPROVEMENT]
SELECTED POSTS:
1. [Post summary] - [Original URL]
2. [Post summary] - [Original URL]
3. [Post summary] - [Original URL]
[Continue for 3-5 posts or "NA" if satisfied]

TWITTER CONTENT:
[Your viral Twitter post here - max 280 characters or "NA" if satisfied]

HASHTAGS: [Relevant hashtags]
MENTIONS: [Relevant mentions]
REASONING: [Why this content will perform well on Twitter or why you're satisfied]
"""
        
        return prompt
    
    def process_result(self, result: str) -> Dict[str, Any]:
        """处理Twitter内容生成结果"""
        selected_posts = []
        twitter_content = ""
        hashtags = ""
        mentions = ""
        reasoning = ""
        
        lines = result.strip().split('\n')
        current_section = ""
        content_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('SATISFACTION:'):
                satisfaction = line.replace('SATISFACTION:', '').strip()
                agent_satisfied = satisfaction.upper() == 'SATISFIED'
                continue
            elif line.startswith('SELECTED POSTS:'):
                current_section = "posts"
                continue
            elif line.startswith('TWITTER CONTENT:'):
                current_section = "content"
                content_line = line.replace('TWITTER CONTENT:', '').strip()
                if content_line:
                    content_lines.append(content_line)
                continue
            elif line.startswith('HASHTAGS:'):
                current_section = "hashtags"
                hashtags = line.replace('HASHTAGS:', '').strip()
                continue
            elif line.startswith('MENTIONS:'):
                current_section = "mentions"
                mentions = line.replace('MENTIONS:', '').strip()
                continue
            elif line.startswith('REASONING:'):
                current_section = "reasoning"
                reasoning = line.replace('REASONING:', '').strip()
                continue
            elif line and current_section == "posts" and line[0].isdigit():
                selected_posts.append(line)
            elif line and current_section == "content" and not line.startswith(('HASHTAGS:', 'MENTIONS:', 'REASONING:')):
                content_lines.append(line)
        
        twitter_content = '\n'.join(content_lines).strip()
        
        return {
            "satisfaction": satisfaction,
            "selected_posts": selected_posts,
            "twitter_content": twitter_content,
            "hashtags": hashtags,
            "mentions": mentions,
            "reasoning": reasoning,
            "agent_satisfied": agent_satisfied,
            "character_count": len(twitter_content),
            "summary": f"Created Twitter content: {twitter_content[:50]}..." if not agent_satisfied else f"Satisfied with previous results: {reasoning}",
            "type": "twitter_content"
        }
